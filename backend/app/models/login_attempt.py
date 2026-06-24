import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .user import User


class LoginAttempt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Аудит-лог попыток входа (требование 5.1 — логирование попыток авторизации)."""
    __tablename__ = "login_attempts"
    __table_args__ = (
        Index("ix_login_attempts_email_created", "email_attempted", "created_at"),
    )

    email_attempted: Mapped[str] = mapped_column(String(255), nullable=False)
    # NULL если email не принадлежит ни одному пользователю
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    ip_address: Mapped[str | None] = mapped_column(String(45))
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="login_attempts")

    def __repr__(self) -> str:
        return f"<LoginAttempt(email='{self.email_attempted}', success={self.success})>"
