import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models.enums import UserRole
from ..models.user import User
from ..repositories.login_attempt_repository import LoginAttemptRepository
from ..repositories.password_reset_token_repository import PasswordResetTokenRepository
from ..repositories.user_repository import UserRepository
from ..schemas.auth import TokenResponse
from ..schemas.user import UserCreate, UserResponse, UserUpdate
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
bearer_scheme = HTTPBearer()
_bearer_scheme_optional = HTTPBearer(auto_error=False)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.login_attempt_repo = LoginAttemptRepository(db)
        self.reset_token_repo = PasswordResetTokenRepository(db)

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
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
        return build_token_response(user)

    def update_profile(self, user: User, data: UserUpdate) -> UserResponse:
        if (data.phone is not None and data.phone != user.phone
                and self.user_repo.phone_exists(data.phone)):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким номером телефона уже существует",
            )
        try:
            user = self.user_repo.update(user, data)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Пользователь с таким номером телефона уже существует",
            )
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
        # время ответа не раскрывает, зарегистрирован ли адрес.
        hashed = user.password_hash if user else _DUMMY_HASH
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
        Если email зарегистрирован — создаёт токен сброса и пишет ссылку в лог
        сервера (нет SMTP-провайдера для реальной отправки писем).
        Снаружи всегда ведёт себя одинаково, независимо от результата —
        чтобы не дать возможность перебором узнать, какие email зарегистрированы.
        """
        user = self.user_repo.get_by_email(email)
        if not user:
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

        logger.info(
            "Password reset requested for %s — link: /reset-password?token=%s (expires %s)",
            user.email, raw_token, expires_at.isoformat(),
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
        self.reset_token_repo.mark_used(token)


# ── JWT ──────────────────────────────────────────────────────────


def build_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=_create_access_token(user.id),
        user=UserResponse.model_validate(user),
    )


def _create_access_token(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def _decode_token(token: str) -> Optional[UUID]:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        user_id = payload.get("sub")
        return UUID(user_id) if user_id else None
    except (JWTError, ValueError):
        return None


# ── Dependencies ─────────────────────────────────────────────────


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = _decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    # Ранее выданный токен заблокированного пользователя недействителен —
    # JWT сам по себе не отзываем, поэтому режем на каждой проверке.
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован. Обратитесь к администратору.",
        )
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Пользователь, если запрос авторизован, иначе None — для публичных
    эндпоинтов, которые показывают админу больше (например, скрытые услуги)."""
    if not credentials:
        return None
    user_id = _decode_token(credentials.credentials)
    if not user_id:
        return None
    return UserRepository(db).get_by_id(user_id)


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
