import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .appointment import Appointment
    from .review import Review
    from .salon import Salon
    from .schedule import Schedule
    from .service import Service
    from .user import User


class Master(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "master"
    __table_args__ = (
        CheckConstraint("coefficient > 0", name="chk_master_coefficient_positive"),
        Index("uniq_master_user_id", "user_id", unique=True,
              postgresql_where=text("deleted_at IS NULL")),
        Index("idx_master_salon_id", "salon_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False
    )
    # Мастер физически работает в одной точке (см. ROADMAP.md §4.1) —
    # мультилокационный мастер вне периметра v1.
    salon_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("salon.id", ondelete="RESTRICT"), nullable=False
    )
    specialization: Mapped[str | None] = mapped_column(String(200))
    photo_url: Mapped[str | None] = mapped_column(String(500))
    # Финальная цена = services.price * coefficient
    # (если не задан price_override в master_services)
    coefficient: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("1.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship(back_populates="master_profile")
    salon: Mapped["Salon"] = relationship(back_populates="masters")
    services: Mapped[list["MasterService"]] = relationship(
        back_populates="master", cascade="all, delete-orphan"
    )
    schedules: Mapped[list["Schedule"]] = relationship(
        back_populates="master", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        back_populates="master", foreign_keys="Appointment.master_id"
    )
    reviews: Mapped[list["Review"]] = relationship(back_populates="master")

    # Удобный доступ к имени для схем, валидирующих Master напрямую
    # (например AppointmentResponse.master: MasterBriefResponse) —
    # имя/фамилия физически хранятся на User, не на Master.
    @property
    def first_name(self) -> str:
        return self.user.first_name

    @property
    def last_name(self) -> str:
        return self.user.last_name

    # Аналогично first_name/last_name — MasterPublicResponse.salon_name
    # (ROADMAP.md §4.8) не раскрывает полный SalonBriefResponse наружу.
    @property
    def salon_name(self) -> str:
        return self.salon.name

    def __repr__(self) -> str:
        return f"<Master(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class MasterService(Base):
    """Связь N:M — какой мастер оказывает какую услугу."""
    __tablename__ = "master_service"
    __table_args__ = (
        CheckConstraint("price_override >= 0", name="chk_master_service_price_override_non_negative"),
        # Композитный PK (master_id, service_id) индексирует поиск по master_id,
        # но не по одному service_id — нужен отдельный индекс.
        Index("idx_master_service_service_id", "service_id"),
    )

    master_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("master.id", ondelete="CASCADE"), primary_key=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("service.id", ondelete="CASCADE"), primary_key=True
    )
    # NULL → итоговая цена = services.price * masters.coefficient
    price_override: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    master: Mapped["Master"] = relationship(back_populates="services")
    service: Mapped["Service"] = relationship(back_populates="masters")

    def __repr__(self) -> str:
        return (f"<MasterService(master_id={self.master_id}, "
                f"service_id={self.service_id}, override={self.price_override})>")
