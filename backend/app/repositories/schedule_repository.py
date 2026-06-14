from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ..models.schedule import Schedule
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate


class ScheduleRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, schedule_id: UUID) -> Optional[Schedule]:
        return self.db.query(Schedule).filter(Schedule.id == schedule_id).first()

    def get_by_master(self, master_id: UUID) -> list[Schedule]:
        """Всё расписание мастера, отсортированное по дням недели."""
        return (
            self.db.query(Schedule)
            .filter(Schedule.master_id == master_id)
            .order_by(Schedule.day_of_week)
            .all()
        )

    def get_by_master_and_day(self, master_id: UUID,
                              day_of_week: int) -> Optional[Schedule]:
        """Расписание мастера на конкретный день недели."""
        return (
            self.db.query(Schedule)
            .filter(
                Schedule.master_id   == master_id,
                Schedule.day_of_week == day_of_week,
            )
            .first()
        )

    # ── Создание ─────────────────────────────────────────────────

    def create(self, master_id: UUID, data: ScheduleCreate) -> Schedule:
        schedule = Schedule(master_id=master_id, **data.model_dump())
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    # ── Обновление ───────────────────────────────────────────────

    def update(self, schedule: Schedule, data: ScheduleUpdate) -> Schedule:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(schedule, field, value)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule
