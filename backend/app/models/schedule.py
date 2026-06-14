import uuid
from sqlalchemy import Column, Boolean, SmallInteger, Time, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Schedule(Base):
    """Рабочее расписание мастера по дням недели.
    day_of_week: 0 = пн … 6 = вс.
    """
    __tablename__ = "schedules"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    master_id   = Column(UUID(as_uuid=True),
                         ForeignKey("masters.id", ondelete="CASCADE"),
                         nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)  # 0–6
    start_time  = Column(Time, nullable=False)
    end_time    = Column(Time, nullable=False)
    is_working  = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_schedules_day_of_week"),
        CheckConstraint("end_time > start_time",        name="ck_schedules_end_after_start"),
        UniqueConstraint("master_id", "day_of_week",    name="uq_schedules_master_day"),
    )

    # Связи
    master = relationship("Master", back_populates="schedules")

    def __repr__(self):
        return (f"<Schedule(master_id={self.master_id}, "
                f"day={self.day_of_week}, {self.start_time}-{self.end_time})>")
