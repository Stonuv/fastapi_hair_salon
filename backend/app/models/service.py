from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .mixins import SoftDeleteMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .appointment import Appointment
    from .master import MasterService
    from .review import Review


class Service(Base, UUIDPrimaryKeyMixin, SoftDeleteMixin):
    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_services_price_non_negative"),
        CheckConstraint("duration_min > 0", name="ck_services_duration_positive"),
        Index("ix_services_name", "name"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    # Публикация/снятие с публикации в каталоге — отдельно от deleted_at
    # (мягкое удаление), который полностью убирает услугу из системы.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    masters: Mapped[list["MasterService"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="service")
    reviews: Mapped[list["Review"]] = relationship(back_populates="service")

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name='{self.name}', price={self.price})>"
