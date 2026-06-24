import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .appointment import Appointment
    from .master import Master
    from .service import Service
    from .user import User


class Review(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Отзыв клиента о завершённой записи. Один отзыв на одну запись."""
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),
        UniqueConstraint("appointment_id", name="uq_reviews_appointment"),
        Index("ix_reviews_master", "master_id"),
        Index("ix_reviews_service", "service_id"),
    )

    appointment_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Денормализованы из appointment в момент создания — позволяют выбирать
    # отзывы мастера/услуги без join через appointments.
    master_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("masters.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    # Быстрое действие администратора «опубликовать / снять с публикации»
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    appointment: Mapped["Appointment"] = relationship(back_populates="review")
    client: Mapped["User"] = relationship(back_populates="reviews", foreign_keys=[client_id])
    master: Mapped["Master"] = relationship(back_populates="reviews")
    service: Mapped["Service"] = relationship(back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review(appointment={self.appointment_id}, master={self.master_id}, rating={self.rating})>"
