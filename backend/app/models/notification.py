import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Text, UniqueConstraint, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .enums import NotificationChannel, NotificationStatus, NotificationType
from .mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .appointment import Appointment


class Notification(Base, UUIDPrimaryKeyMixin):
    """Уведомления, порождённые записью (1:N к appointments)."""
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("appointment_id", "type", "channel",
                         name="uq_notifications_appointment_type_channel"),
        Index("ix_notifications_pending", "scheduled_at",
              postgresql_where=text("status = 'pending'")),
    )

    appointment_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, name="notification_type"), nullable=False
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        SAEnum(NotificationChannel, name="notification_channel"),
        nullable=False, default=NotificationChannel.email,
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(NotificationStatus, name="notification_status"),
        nullable=False, default=NotificationStatus.pending,
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    appointment: Mapped["Appointment"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:
        return (f"<Notification(appointment={self.appointment_id}, "
                f"type='{self.type}', status='{self.status}')>")
