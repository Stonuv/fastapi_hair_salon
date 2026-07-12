from typing import TYPE_CHECKING

from sqlalchemy import Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .enums import UserRole
from .mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .login_attempt import LoginAttempt
    from .master import Master
    from .password_reset_token import PasswordResetToken
    from .session import Session
    from .appointment import Appointment
    from .review import Review


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    __table_args__ = (
        # Уникальность email/телефона действует только среди "живых" записей —
        # иначе мягко удалённый пользователь блокирует email от повторной регистрации.
        Index("uq_users_email_active", "email", unique=True,
              postgresql_where=text("deleted_at IS NULL")),
        Index("uq_users_phone_active", "phone", unique=True,
              postgresql_where=text("deleted_at IS NULL AND phone IS NOT NULL")),
        Index("uq_users_vk_user_id_active", "vk_user_id", unique=True,
              postgresql_where=text("deleted_at IS NULL AND vk_user_id IS NOT NULL")),
        Index("ix_users_role", "role"),
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    # NULL — аккаунт создан через VK ID (OAuth), пароля никогда не было;
    # такие аккаунты не проходят обычный login() по email/паролю (см. auth_service).
    password_hash: Mapped[str | None] = mapped_column(String(255))
    # ID пользователя VK ID (user_info.user_id) — привязка OAuth-аккаунта.
    vk_user_id: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.client
    )
    # Блокировка (ТЗ 4.2 MIN) — отличается от мягкого удаления: аккаунт и
    # история сохраняются и видны, но вход и действия по токену запрещены.
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Инкрементируется при logout, смене/сбросе пароля и блокировке — так
    # уже выданные JWT отзываются без хранения denylist'а (см. auth_service).
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Профиль мастера (только если role = 'master')
    master_profile: Mapped["Master | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    # Записи клиента (только если role = 'client')
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="client", foreign_keys="Appointment.client_id"
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="client", foreign_keys="Review.client_id"
    )
    login_attempts: Mapped[list["LoginAttempt"]] = relationship(back_populates="user")
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
