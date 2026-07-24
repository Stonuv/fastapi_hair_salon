import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models.enums import UserRole
from ..models.user import User
from ..repositories.email_verification_token_repository import EmailVerificationTokenRepository
from ..repositories.login_attempt_repository import LoginAttemptRepository
from ..repositories.password_reset_token_repository import PasswordResetTokenRepository
from ..repositories.session_repository import SessionRepository
from ..repositories.user_repository import UserRepository
from ..schemas.auth import TokenResponse
from ..schemas.user import UserCreate, UserResponse, UserUpdate
from ..utils.email import send_email
from ._errors import constraint_name

logger = logging.getLogger(__name__)

# ── Утилиты для паролей ──────────────────────────────────────────


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    # bcrypt 5.x бросает ValueError на пароль длиннее 72 байт — такой пароль
    # заведомо неверен (валидные не проходят регистрацию), а не повод для 500.
    if len(password.encode("utf-8")) > 72:
        return False
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _hash_token(raw_token: str) -> str:
    """В БД хранится только хеш — сам токен живёт лишь в ссылке пользователю."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


# Хеш заведомо несуществующего пароля: когда пользователь не найден, bcrypt
# всё равно выполняется — иначе быстрый ответ выдаёт, что email не зарегистрирован.
_DUMMY_HASH = bcrypt.hashpw(secrets.token_bytes(32), bcrypt.gensalt()).decode()

# ── HTTPBearer схема — в Swagger появится поле "Value: <token>" ──
# auto_error=False: токен может прийти либо в httpOnly-cookie (SPA), либо в
# заголовке Authorization (Swagger "Authorize", внешние API-клиенты) — какой
# из двух источников обязателен, решает get_current_user, а не сама схема.
_bearer_scheme_optional = HTTPBearer(auto_error=False)

# Cookie с access-токеном для SPA (см. "Токен в localStorage" в README —
# заменяет чтение токена из localStorage на стороне фронтенда).
ACCESS_TOKEN_COOKIE = "access_token"


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=settings.access_token_expire_minutes * 60,
        path="/api",
        httponly=True,
        secure=settings.cookie_secure,
        # Lax, а не Strict: иначе переход по прямой ссылке (открыть письмо со
        # ссылкой сброса пароля в новой вкладке) на не-GET маршрутизацию не
        # повлияет, но проще для навигации; для CSRF на POST/PATCH/DELETE
        # Lax достаточен — куки не уходят при кросс-сайтовом non-GET запросе,
        # а простой JSON-эндпоинт без form-encoded submit не эксплуатируется
        # обычной CSRF-формой.
        samesite="lax",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/api")


# Cookie с refresh-токеном (см. models/session.py) — путь ограничен /api/auth,
# в отличие от access-токена: не должна уходить с каждым API-запросом,
# нужна только эндпоинтам refresh/logout.
REFRESH_TOKEN_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth"


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, path=REFRESH_COOKIE_PATH)


def create_session(db: Session, user_id: UUID) -> str:
    """Создаёт новую сессию (refresh-токен) для пользователя и возвращает
    «сырой» токен для cookie — в БД остаётся только его хеш (_hash_token)."""
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    SessionRepository(db).create(user_id, _hash_token(raw_token), expires_at)
    return raw_token


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.login_attempt_repo = LoginAttemptRepository(db)
        self.reset_token_repo = PasswordResetTokenRepository(db)
        self.verification_token_repo = EmailVerificationTokenRepository(db)
        self.session_repo = SessionRepository(db)

    def register(self, data: UserCreate) -> TokenResponse:
        if self.user_repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким email уже существует",
            )
        if data.phone and self.user_repo.phone_exists(data.phone):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким номером телефона уже существует",
            )
        password_hash = hash_password(data.password)
        try:
            user = self.user_repo.create(data, password_hash)
        except IntegrityError as exc:
            # Проигравший гонку с параллельной регистрацией — частичные
            # unique-индексы users надёжнее пред-проверок выше.
            self.db.rollback()
            detail = (
                "Пользователь с таким номером телефона уже существует"
                if constraint_name(exc) == "uq_users_phone_active"
                else "Пользователь с таким email уже существует"
            )
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
        self.send_verification_email(user)
        return build_token_response(user)

    def update_profile(self, user: User, data: UserUpdate) -> UserResponse:
        # email отдельно от остальных полей: он может ещё не быть задан у
        # VK-пользователя (см. vk_oauth_service) и требует проверки на
        # уникальность, как при регистрации/в админке (см. admin_service.update_user).
        if data.email is not None and data.email != user.email:
            if self.user_repo.email_exists(data.email):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Пользователь с таким email уже существует")
            try:
                user = self.user_repo.set_email(user, data.email)
            except IntegrityError as exc:
                self.db.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail="Пользователь с таким email уже существует") from exc
            # Новый email не доказан (в отличие от email, отданного VK OAuth
            # напрямую при создании аккаунта) — требует подтверждения так же,
            # как при обычной регистрации.
            self.send_verification_email(user)

        if (data.phone is not None and data.phone != user.phone
                and self.user_repo.phone_exists(data.phone)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким номером телефона уже существует",
            )

        other_fields = data.model_dump(exclude_unset=True, exclude={"email"})
        if other_fields:
            try:
                user = self.user_repo.update(user, UserUpdate(**other_fields))
            except IntegrityError as exc:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Пользователь с таким номером телефона уже существует",
                ) from exc
        return UserResponse.model_validate(user)

    def login(self, email: str, password: str, ip_address: str | None = None) -> TokenResponse:
        # Временная блокировка после N неудачных попыток (защита от перебора;
        # сам журнал login_attempts — требование 5.1).
        window_start = datetime.now(timezone.utc) - timedelta(
            minutes=settings.login_lockout_minutes
        )
        recent_failed = self.login_attempt_repo.count_recent_failed(email, window_start)
        if recent_failed >= settings.login_max_failed_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком много неудачных попыток входа. Попробуйте позже.",
            )

        user = self.user_repo.get_by_email(email)
        # bcrypt выполняется и для несуществующего email (сравнение с dummy-хешем) —
        # время ответа не раскрывает, зарегистрирован ли адрес. Аккаунт без
        # пароля (VK ID) тоже сравнивается с dummy-хешем — у него не может
        # быть верного пароля, но ответ ("неверный email или пароль") должен
        # быть неотличим от обычного случая.
        hashed = user.password_hash if user and user.password_hash else _DUMMY_HASH
        password_ok = _verify_password(password, hashed) and user is not None
        # Верный пароль заблокированного аккаунта — это тоже неуспешный вход
        success = password_ok and not user.is_blocked

        # Требование 5.1 — логируем каждую попытку входа, успешную и неуспешную.
        self.login_attempt_repo.create(
            email_attempted=email,
            user_id=user.id if user else None,
            ip_address=ip_address,
            success=success,
        )
        # Коммитим сразу: get_db откатывает транзакцию при HTTPException,
        # а запись о неудачной попытке обязана сохраниться — на ней держится
        # и аудит-лог, и блокировка перебора выше.
        self.db.commit()

        if not password_ok or user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
            )

        # Блокировка (ТЗ 4.2): пароль верный, но вход запрещён
        if user.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Аккаунт заблокирован. Обратитесь к администратору.",
            )

        return build_token_response(user)

    def request_password_reset(self, email: str) -> None:
        """
        Если email зарегистрирован — создаёт токен сброса и отправляет
        ссылку письмом (SMTP, см. settings.smtp_* / utils/email.py).
        Снаружи всегда ведёт себя одинаково, независимо от результата —
        чтобы не дать возможность перебором узнать, какие email зарегистрированы.
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            return
        if not user.password_hash:
            # OAuth-аккаунт (VK ID) — у него нет пароля, который можно сбросить.
            logger.info("Password reset requested for OAuth-only account %s — ignored", email)
            return

        # Rate limit: не даём бесконечно генерировать токены (и засорять лог).
        # Молча выходим — снаружи ответ обязан быть неотличим от успешного.
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        if (self.reset_token_repo.count_created_since(user.id, hour_ago)
                >= settings.password_reset_max_requests_per_hour):
            logger.warning("Password reset rate limit hit for %s", user.email)
            return

        self.reset_token_repo.invalidate_all_for_user(user.id)

        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.password_reset_token_expire_minutes
        )
        self.reset_token_repo.create(user.id, _hash_token(raw_token), expires_at)

        reset_link = f"{settings.frontend_base_url}/reset-password?token={raw_token}"
        # DEBUG, не INFO: с рабочим SMTP это только для локальной отладки —
        # на INFO (уровень по умолчанию в проде, см. main.py) сырой токен
        # утекал бы в логи контейнера и позволял сбросить пароль в обход письма.
        logger.debug(
            "Password reset requested for %s — link: %s (expires %s)",
            user.email, reset_link, expires_at.isoformat(),
        )
        send_email(
            to=user.email,
            subject="Восстановление пароля — Барбершоп «Сайтама»",
            text_body=(
                f"Здравствуйте, {user.first_name}!\n\n"
                f"Для сброса пароля перейдите по ссылке (действует "
                f"{settings.password_reset_token_expire_minutes} минут):\n{reset_link}\n\n"
                "Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо."
            ),
            html_body=(
                f"<p>Здравствуйте, {user.first_name}!</p>"
                f"<p>Для сброса пароля перейдите по ссылке (действует "
                f"{settings.password_reset_token_expire_minutes} минут):</p>"
                f'<p><a href="{reset_link}">{reset_link}</a></p>'
                "<p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>"
            ),
        )

    def confirm_password_reset(self, raw_token: str, new_password: str) -> None:
        token = self.reset_token_repo.get_valid_by_hash(_hash_token(raw_token))
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Токен сброса пароля недействителен или просрочен",
            )
        user = self.user_repo.get_by_id(token.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не найден",
            )
        self.user_repo.set_password(user, hash_password(new_password))
        # Токены, выданные до сброса, не должны пережить смену пароля — и
        # access (token_version), и все refresh-сессии на всех устройствах.
        self.user_repo.bump_token_version(user)
        self.session_repo.delete_all_for_user(user.id)
        self.reset_token_repo.mark_used(token)

    def send_verification_email(self, user: User) -> None:
        """Отправляет письмо со ссылкой подтверждения email — после
        регистрации и при смене email в профиле. "Мягкий" гейт (ISSUES):
        неподтверждённый email не мешает войти и пользоваться сайтом,
        поэтому в отличие от request_password_reset здесь нет смысла
        маскировать некоторые случаи под "успех" — вызывающая сторона уже
        знает, что у неё есть аккаунт с этим email (аноним так не вызывает
        этот метод). Тихо ничего не делает, если email не задан (VK-аккаунт
        без email) или лимит отправок исчерпан — не должно ронять
        register()/update_profile() из-за проблем с почтой."""
        if not user.email:
            return
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        if (self.verification_token_repo.count_created_since(user.id, hour_ago)
                >= settings.email_verification_max_requests_per_hour):
            logger.warning("Email verification rate limit hit for %s", user.email)
            return
        self._issue_verification_token_and_send(user)

    def resend_verification_email(self, user: User) -> None:
        """Повторная отправка по явному запросу пользователя (кнопка «отправить
        письмо ещё раз») — в отличие от send_verification_email, тут вызывающая
        сторона уже авторизована как этот самый пользователь, так что можно
        (и нужно) явно сказать, почему запрос отклонён, а не тихо промолчать."""
        if not user.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Сначала укажите email в профиле")
        if user.email_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Email уже подтверждён")
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        if (self.verification_token_repo.count_created_since(user.id, hour_ago)
                >= settings.email_verification_max_requests_per_hour):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                detail="Слишком много запросов. Попробуйте позже.")
        self._issue_verification_token_and_send(user)

    def _issue_verification_token_and_send(self, user: User) -> None:
        self.verification_token_repo.invalidate_all_for_user(user.id)

        raw_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.email_verification_token_expire_minutes
        )
        self.verification_token_repo.create(user.id, _hash_token(raw_token), expires_at)

        verify_link = f"{settings.frontend_base_url}/verify-email?token={raw_token}"
        logger.debug(
            "Email verification requested for %s — link: %s (expires %s)",
            user.email, verify_link, expires_at.isoformat(),
        )
        send_email(
            to=user.email,
            subject="Подтвердите email — Барбершоп «Сайтама»",
            text_body=(
                f"Здравствуйте, {user.first_name}!\n\n"
                f"Подтвердите свой email, перейдя по ссылке (действует "
                f"{settings.email_verification_token_expire_minutes // 60} ч):\n{verify_link}\n\n"
                "Если вы не регистрировались на этом сайте, просто проигнорируйте это письмо."
            ),
            html_body=(
                f"<p>Здравствуйте, {user.first_name}!</p>"
                f"<p>Подтвердите свой email, перейдя по ссылке (действует "
                f"{settings.email_verification_token_expire_minutes // 60} ч):</p>"
                f'<p><a href="{verify_link}">{verify_link}</a></p>'
                "<p>Если вы не регистрировались на этом сайте, просто проигнорируйте это письмо.</p>"
            ),
        )

    def confirm_email_verification(self, raw_token: str) -> None:
        token = self.verification_token_repo.get_valid_by_hash(_hash_token(raw_token))
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Токен подтверждения email недействителен или просрочен",
            )
        user = self.user_repo.get_by_id(token.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь не найден",
            )
        self.user_repo.set_email_verified_at(user, datetime.now(timezone.utc))
        self.verification_token_repo.mark_used(token)

    def logout(self, raw_refresh_token: str | None) -> None:
        """Удаляет ровно текущую сессию (устройство) — не трогает остальные.
        Access-токен этого устройства доживает своим коротким TTL (см.
        access_token_expire_minutes), но обновить его через /refresh уже
        нельзя: сессии больше нет. Полную инвалидацию всех устройств сразу
        делают только события безопасности — см. bump_token_version +
        session_repo.delete_all_for_user (смена/сброс пароля, блокировка)."""
        if raw_refresh_token:
            self.session_repo.delete_by_hash(_hash_token(raw_refresh_token))

    def refresh_session(self, raw_refresh_token: str) -> tuple[TokenResponse, str]:
        """Ротация refresh-токена: старая сессия удаляется, выдаётся новая —
        если старый токен всё же используют повторно (кража), следующий
        refresh легитимного клиента получит 401 вместо тихой утечки доступа."""
        session = self.session_repo.get_valid_by_hash(_hash_token(raw_refresh_token))
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Сессия недействительна или истекла, войдите заново",
            )
        user = self.user_repo.get_by_id(session.user_id)
        self.session_repo.delete(session)
        if not user or user.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Сессия недействительна или истекла, войдите заново",
            )
        new_raw_token = create_session(self.db, user.id)
        return build_token_response(user), new_raw_token


# ── JWT ──────────────────────────────────────────────────────────


def build_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=_create_access_token(user),
        user=UserResponse.model_validate(user),
    )


def _create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    # "ver" — снимок token_version на момент выдачи; get_current_user
    # сверяет его с текущим значением в БД, что и даёт отзыв токена.
    payload = {"sub": str(user.id), "ver": user.token_version, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def _decode_token(token: str) -> tuple[UUID, int] | None:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        user_id = payload.get("sub")
        token_version = payload.get("ver")
        if user_id is None or token_version is None:
            return None
        return UUID(user_id), int(token_version)
    except (JWTError, ValueError, TypeError):
        return None


def _token_from_request(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    # Cookie — основной путь для SPA (см. ACCESS_TOKEN_COOKIE); заголовок
    # Authorization остаётся рабочим для Swagger "Authorize" и внешних
    # API-клиентов, которым httpOnly-cookie недоступна.
    return request.cookies.get(ACCESS_TOKEN_COOKIE) or (
        credentials.credentials if credentials else None
    )


# ── Dependencies ─────────────────────────────────────────────────


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme_optional),
    db: Session = Depends(get_db),
) -> User:
    token = _token_from_request(request, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    decoded = _decode_token(token)
    if not decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id, token_version = decoded
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    # Токен пережил logout/смену пароля — token_version в payload устарел.
    if user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен отозван, войдите заново",
        )
    # Ранее выданный токен заблокированного пользователя недействителен.
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован. Обратитесь к администратору.",
        )
    return user


def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme_optional),
    db: Session = Depends(get_db),
) -> User | None:
    """Пользователь, если запрос авторизован, иначе None — для публичных
    эндпоинтов, которые показывают админу больше (например, скрытые услуги)."""
    token = _token_from_request(request, credentials)
    if not token:
        return None
    decoded = _decode_token(token)
    if not decoded:
        return None
    user_id, token_version = decoded
    user = UserRepository(db).get_by_id(user_id)
    if not user or user.token_version != token_version:
        return None
    return user


def require_role(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав",
            )
        return current_user
    return dependency


get_current_client = require_role(UserRole.client, UserRole.admin)
get_current_master = require_role(UserRole.master, UserRole.admin)
get_current_admin  = require_role(UserRole.admin)
