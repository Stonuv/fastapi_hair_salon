import uuid
from sqlalchemy import Column, Numeric, ForeignKey, Enum, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from ..database import Base
from .enums import AppointmentStatus


class Appointment(Base):
    """Запись (приём) клиента к мастеру на конкретную услугу.

    Защита от двойного бронирования реализована через EXCLUDE USING gist
    на уровне БД — см. Alembic-миграцию (нельзя выразить через __table_args__).
    """
    __tablename__ = "appointments"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id   = Column(UUID(as_uuid=True),
                         ForeignKey("users.id",    ondelete="RESTRICT"),
                         nullable=False)
    master_id   = Column(UUID(as_uuid=True),
                         ForeignKey("masters.id",  ondelete="RESTRICT"),
                         nullable=False)
    service_id  = Column(UUID(as_uuid=True),
                         ForeignKey("services.id", ondelete="RESTRICT"),
                         nullable=False)
    start_time  = Column(DateTime(timezone=True), nullable=False)
    end_time    = Column(DateTime(timezone=True), nullable=False)
    # Цена фиксируется в момент создания записи — не меняется при изменении прайса
    final_price = Column(Numeric(10, 2), nullable=False)
    status      = Column(Enum(AppointmentStatus), nullable=False,
                         default=AppointmentStatus.pending)
    created_at  = Column(DateTime(timezone=True), nullable=False,
                         default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("end_time > start_time",  name="ck_appointments_end_after_start"),
        CheckConstraint("final_price >= 0",        name="ck_appointments_price_non_negative"),
    )

    # Связи
    client        = relationship("User",    back_populates="appointments",
                                 foreign_keys=[client_id])
    master        = relationship("Master",  back_populates="appointments",
                                 foreign_keys=[master_id])
    service       = relationship("Service", back_populates="appointments")
    notifications = relationship("Notification", back_populates="appointment",
                                 cascade="all, delete-orphan")

    def __repr__(self):
        return (f"<Appointment(id={self.id}, master={self.master_id}, "
                f"client={self.client_id}, status='{self.status}')>")
