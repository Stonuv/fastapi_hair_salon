import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.schedule import Schedule
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate


class ScheduleRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, schedule_id: uuid.UUID) -> Optional[Schedule]:
        return self.db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        ).scalar_one_or_none()

    def get_by_master(self, master_id: uuid.UUID) -> list[Schedule]:
        """Всё расписание мастера, отсортированное по дням недели."""
        stmt = (
            select(Schedule)
            .where(Schedule.master_id == master_id)
            .order_by(Schedule.day_of_week)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_master_and_day(self, master_id: uuid.UUID,
                              day_of_week: int) -> Optional[Schedule]:
        """Расписание мастера на конкретный день недели."""
        stmt = select(Schedule).where(
            Schedule.master_id == master_id,
            Schedule.day_of_week == day_of_week,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    # ── Создание ─────────────────────────────────────────────────

    def create(self, master_id: uuid.UUID, data: ScheduleCreate) -> Schedule:
        schedule = Schedule(master_id=master_id, **data.model_dump())
        self.db.add(schedule)
        self.db.flush()
        self.db.refresh(schedule)
        return schedule

    # ── Обновление ───────────────────────────────────────────────

    def update(self, schedule: Schedule, data: ScheduleUpdate) -> Schedule:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(schedule, field, value)
        self.db.flush()
        self.db.refresh(schedule)
        return schedule
