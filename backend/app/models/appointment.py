import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .enums import AppointmentStatus
from .mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .master import Master
    from .notification import Notification
    from .review import Review
    from .service import Service
    from .user import User


class Appointment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Запись (приём) клиента к мастеру на конкретную услугу.

    Защита от двойного бронирования реализована через EXCLUDE USING gist
    на уровне БД — см. Alembic-миграцию (нельзя выразить через __table_args__).
    Разрешённые переходы статуса валидируются в AppointmentService, не в модели.
    """
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_appointments_end_after_start"),
        CheckConstraint("final_price >= 0", name="ck_appointments_price_non_negative"),
        Index("ix_appointments_client", "client_id"),
        Index("ix_appointments_master", "master_id"),
        Index("ix_appointments_time", "start_time", "end_time"),
        Index("ix_appointments_status", "status"),
    )

    client_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    master_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("masters.id", ondelete="RESTRICT"), nullable=False
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("services.id", ondelete="RESTRICT"), nullable=False
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Цена фиксируется в момент создания записи — не меняется при изменении прайса
    final_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        SAEnum(AppointmentStatus, name="appointment_status"),
        nullable=False, default=AppointmentStatus.pending,
    )

    client: Mapped["User"] = relationship(back_populates="appointments", foreign_keys=[client_id])
    master: Mapped["Master"] = relationship(back_populates="appointments", foreign_keys=[master_id])
    service: Mapped["Service"] = relationship(back_populates="appointments")
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="appointment", cascade="all, delete-orphan"
    )
    review: Mapped["Review | None"] = relationship(
        back_populates="appointment", uselist=False, cascade="all, delete-orphan"
    )

    # Удобство для AppointmentBriefResponse — отличить "можно оставить отзыв"
    # от "отзыв уже есть" без отдельного запроса.
    @property
    def review_id(self) -> uuid.UUID | None:
        return self.review.id if self.review else None

    # Денормализованные имена для списков — без них клиенту/мастеру пришлось бы
    # делать отдельный запрос на каждый client_id/master_id/service_id.
    @property
    def client_name(self) -> str:
        return f"{self.client.first_name} {self.client.last_name}"

    @property
    def master_name(self) -> str:
        return f"{self.master.first_name} {self.master.last_name}"

    @property
    def service_name(self) -> str:
        return self.service.name

    def __repr__(self) -> str:
        return (f"<Appointment(id={self.id}, master={self.master_id}, "
                f"client={self.client_id}, status='{self.status}')>")
