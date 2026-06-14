import uuid
from sqlalchemy import Column, Text, Enum, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base
from .enums import NotificationType, NotificationChannel, NotificationStatus


class Notification(Base):
    """Уведомления, порождённые записью (1:N к appointments)."""
    __tablename__ = "notifications"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True),
                            ForeignKey("appointments.id", ondelete="CASCADE"),
                            nullable=False)
    type           = Column(Enum(NotificationType),    nullable=False)
    channel        = Column(Enum(NotificationChannel), nullable=False,
                            default=NotificationChannel.email)
    scheduled_at   = Column(DateTime(timezone=True),   nullable=False)
    sent_at        = Column(DateTime(timezone=True))   # NULL до отправки
    status         = Column(Enum(NotificationStatus),  nullable=False,
                            default=NotificationStatus.pending)
    error_message  = Column(Text)   # заполняется при status = 'failed'

    __table_args__ = (
        # Одно уведомление каждого типа на запись + канал
        UniqueConstraint("appointment_id", "type", "channel",
                         name="uq_notifications_appointment_type_channel"),
    )

    # Связи
    appointment = relationship("Appointment", back_populates="notifications")

    def __repr__(self):
        return (f"<Notification(appointment={self.appointment_id}, "
                f"type='{self.type}', status='{self.status}')>")
