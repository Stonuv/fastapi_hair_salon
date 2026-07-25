import secrets

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..models.enums import UserRole
from ..repositories.user_repository import UserRepository
from ..schemas.auth import TokenResponse
from ..schemas.setup import SetupRequest
from ._errors import constraint_name
from .auth_service import build_token_response, hash_password
from .salon_service import SalonService
from .site_settings_service import SiteSettingsService


# Произвольный, но постоянный ключ для pg_advisory_xact_lock — сериализует
# конкурентные вызовы /api/setup, чтобы проверка is_completed() и создание
# админа были атомарны (иначе два одновременных запроса могут оба пройти
# проверку и оба создать "первого" админа).
_SETUP_LOCK_KEY = 727271


class SetupService:
    """Первичная настройка после развёртывания: создание владельца сети,
    первой точки (и опционально базовых полей контента сайта) одним запросом
    от визарда на фронтенде. Как только управляющий аккаунт существует,
    эндпоинт навсегда возвращает 404 — выглядит как несуществующий, а не
    просто запрещённый (ISSUES #28: 409 подтверждал бы факт установки
    анонимному пробующему запросу; GET /api/setup/status при этом остаётся
    200 как и был — на нём завязан общий router-guard фронтенда на каждой
    навигации).

    До появления владельца /api/setup неизбежно публичен — если задан
    SETUP_TOKEN (обязателен вне debug, см. config.py), запрос обязан
    предъявить его, иначе владельцем станет тот, кто быстрее найдёт
    /setup после деплоя, а не тот, у кого есть доступ к серверу."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.salon_service = SalonService(db)

    def is_completed(self) -> bool:
        # Штатный признак — наличие owner (его и создаёт complete() ниже).
        # UserRole.admin проверяется вдобавок сознательно, как страховка: это
        # вопрос "можно ли снова открыть /api/setup публично", и ошибиться тут
        # безопаснее в сторону "нельзя". Любой существующий управляющий
        # аккаунт — достаточная причина считать инсталляцию настроенной, даже
        # если owner когда-либо будет удалён/разжалован (ROADMAP.md §4.10
        # Фаза B отмечает разжалование как отдельный нерешённый вопрос).
        return self.user_repo.has_role(UserRole.owner) or self.user_repo.has_role(UserRole.admin)

    def requires_token(self) -> bool:
        return bool(settings.setup_token)

    def complete(self, data: SetupRequest) -> TokenResponse:
        # compare_digest — сравнение за постоянное время, не даёт угадывать
        # код побайтово по времени ответа.
        if settings.setup_token and (
            not data.setup_token
            or not secrets.compare_digest(data.setup_token, settings.setup_token)
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Неверный код настройки (SETUP_TOKEN)")
        self.db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _SETUP_LOCK_KEY})
        if self.is_completed():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Настройка уже выполнена")
        if self.user_repo.email_exists(data.owner.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Пользователь с таким email уже существует")
        if data.owner.phone and self.user_repo.phone_exists(data.owner.phone):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Пользователь с таким номером телефона уже существует")
        try:
            # Именно owner: роль admin с введением сети salon-scoped и требует
            # salon_id (ck_users_admin_requires_salon), которого на первом
            # запуске взять неоткуда — попытка создать здесь admin валила
            # /api/setup нарушением этого констрейнта.
            user = self.user_repo.create(data.owner, hash_password(data.owner.password),
                                         role=UserRole.owner)
        except IntegrityError as exc:
            self.db.rollback()
            # Раньше здесь безусловно возвращалось "email уже существует" — и
            # нарушение постороннего констрейнта выглядело как дубликат email
            # на заведомо пустой БД, что маскировало настоящую причину.
            # Сверяемся с именем констрейнта, как в остальных сервисах.
            name = constraint_name(exc)
            if name == "uq_users_phone_active":
                detail = "Пользователь с таким номером телефона уже существует"
            elif name == "uq_users_email_active":
                detail = "Пользователь с таким email уже существует"
            else:
                raise
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc

        # Первая точка сети — до записи контента сайта: masters/appointments
        # ссылаются на salons.id (NOT NULL), без неё инсталляция нерабочая.
        self.salon_service.ensure_primary(data.salon)

        if data.site_content is not None:
            SiteSettingsService(self.db).update(data.site_content)

        return build_token_response(user)
