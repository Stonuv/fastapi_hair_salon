import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models.enums import UserRole
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from ._query_utils import LIKE_ESCAPE_CHAR, escape_like, paginated


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, user_id: uuid.UUID, *, include_deleted: bool = False) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_phone(self, phone: str) -> Optional[User]:
        stmt = select(User).where(User.phone == phone, User.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_vk_id(self, vk_user_id: str) -> Optional[User]:
        stmt = select(User).where(User.vk_user_id == vk_user_id, User.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def has_role(self, role: UserRole) -> bool:
        stmt = select(User.id).where(User.role == role, User.deleted_at.is_(None)).limit(1)
        return self.db.execute(stmt).scalar() is not None

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        role: UserRole | None = None,
        search: str | None = None,
        sort_by: Literal["created_at", "email"] = "created_at",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> tuple[list[User], int]:
        """Список пользователей для админ-панели: фильтр по роли + поиск по имени/email."""
        stmt = select(User).where(User.deleted_at.is_(None))
        if role is not None:
            stmt = stmt.where(User.role == role)
        if search:
            pattern = f"%{escape_like(search)}%"
            stmt = stmt.where(or_(
                User.email.ilike(pattern, escape=LIKE_ESCAPE_CHAR),
                User.first_name.ilike(pattern, escape=LIKE_ESCAPE_CHAR),
                User.last_name.ilike(pattern, escape=LIKE_ESCAPE_CHAR),
            ))

        sort_column = User.created_at if sort_by == "created_at" else User.email
        order = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        stmt = stmt.order_by(order)

        return paginated(self.db, stmt, page=page, page_size=page_size)

    # ── Создание ─────────────────────────────────────────────────

    def create(self, data: UserCreate, password_hash: str, role: UserRole = UserRole.client) -> User:
        """
        Принимает схему UserCreate и уже готовый хеш пароля.
        Хешировать пароль — задача сервиса, не репозитория.
        Саморегистрация всегда создаёт клиента (role не передаётся —
        используется дефолт); администратор может задать роль явно.
        """
        user = User(
            email=data.email,
            password_hash=password_hash,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            role=role,
        )
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def create_vk_oauth_user(self, *, email: str, first_name: str, last_name: str,
                             vk_user_id: str) -> User:
        """Первый вход через VK ID для email, не найденного среди существующих
        пользователей — регистрация без пароля (см. User.password_hash)."""
        user = User(
            email=email,
            password_hash=None,
            first_name=first_name,
            last_name=last_name,
            vk_user_id=vk_user_id,
            role=UserRole.client,
        )
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def link_vk_id(self, user: User, vk_user_id: str) -> User:
        """Привязывает VK-аккаунт к уже существующему пользователю (найденному
        по email из VK ID) — так повторный вход через VK находит его напрямую."""
        user.vk_user_id = vk_user_id
        self.db.flush()
        self.db.refresh(user)
        return user

    # ── Обновление ───────────────────────────────────────────────

    def update(self, user: User, data: UserUpdate) -> User:
        """
        Обновляет только те поля, которые переданы (не None).
        Паттерн model_dump(exclude_unset=True) — берём только явно
        переданные поля, не затираем остальные нулями.
        """
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        self.db.flush()
        self.db.refresh(user)
        return user

    def set_password(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        self.db.flush()

    def bump_token_version(self, user: User) -> None:
        """Отзывает все ранее выданные JWT пользователя (logout, смена/сброс
        пароля, блокировка) — старый token_version в payload перестаёт
        совпадать с текущим при проверке в get_current_user."""
        user.token_version += 1
        self.db.flush()

    def set_role(self, user: User, role: UserRole) -> User:
        user.role = role
        self.db.flush()
        self.db.refresh(user)
        return user

    def set_email(self, user: User, email: str) -> User:
        user.email = email
        self.db.flush()
        self.db.refresh(user)
        return user

    def set_blocked(self, user: User, is_blocked: bool) -> User:
        user.is_blocked = is_blocked
        self.db.flush()
        self.db.refresh(user)
        return user

    def soft_delete(self, user: User) -> None:
        user.deleted_at = datetime.now(timezone.utc)
        self.db.flush()

    # ── Вспомогательное ──────────────────────────────────────────

    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None

    def phone_exists(self, phone: str) -> bool:
        return self.get_by_phone(phone) is not None
