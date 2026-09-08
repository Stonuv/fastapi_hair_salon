import uuid
from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, SmallInteger, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .master import Master


class Schedule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Рабочее расписание мастера по дням недели.
    day_of_week: 0 = пн … 6 = вс.
    """
    __tablename__ = "schedule"
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="chk_schedule_day_of_week"),
        CheckConstraint("end_time > start_time", name="chk_schedule_end_after_start"),
        UniqueConstraint("master_id", "day_of_week", name="uniq_schedule_master_id_day_of_week"),
    )

    master_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("master.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_working: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    master: Mapped["Master"] = relationship(back_populates="schedules")

    def __repr__(self) -> str:
        return (f"<Schedule(master_id={self.master_id}, "
                f"day={self.day_of_week}, {self.start_time}-{self.end_time})>")
