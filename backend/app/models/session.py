import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .user import User


class Session(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Сессия входа (refresh-токен). В БД хранится только SHA-256 хеш токена —
    сам токен живёт только в httpOnly-cookie на устройстве пользователя.

    Logout удаляет ровно одну сессию (текущее устройство). События
    безопасности (смена/сброс пароля, блокировка, мягкое удаление —
    см. AuthService/AdminService) вместо этого удаляют все сессии
    пользователя разом, синхронно с bump_token_version — иначе access-токен
    отзывался бы, а refresh тихо выдавал бы новый рабочий взамен.
    """
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_user", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session(user_id={self.user_id}, expires_at={self.expires_at})>"
