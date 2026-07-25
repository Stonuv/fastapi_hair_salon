from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Index, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .appointment import Appointment
    from .master import Master


class Salon(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Точка сети (см. ROADMAP.md §4.2). Без SoftDeleteMixin — точка не
    удаляется физически (masters/appointments.salon_id ссылаются
    ondelete=RESTRICT), только is_active=false, как Service/Master."""

    __tablename__ = "salons"
    __table_args__ = (
        CheckConstraint("close_time > open_time", name="ck_salons_close_after_open"),
        Index("uq_salons_slug", "slug", unique=True),
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # Генерируется сервером из name (транслитерация + slugify + суффикс
    # при коллизии) — не редактируется вручную в v1, см. utils/slug.py.
    slug: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    open_time: Mapped[time] = mapped_column(Time, nullable=False)
    close_time: Mapped[time] = mapped_column(Time, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(500))
    # "Закрыть" точку без физического удаления — masters/appointments
    # ссылаются ondelete=RESTRICT, так что DELETE недостижим через API.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    masters: Mapped[list["Master"]] = relationship(back_populates="salon")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="salon")

    def __repr__(self) -> str:
        return f"<Salon(id={self.id}, name='{self.name}', slug='{self.slug}')>"
