from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.appointment import Appointment
from ..models.enums import AppointmentStatus, UserRole
from ..models.master import Master
from ..models.service import Service
from ..models.user import User


class StatsRepository:
    """Агрегирующие запросы для счётчиков/графиков админ-панели (4.4)."""

    def __init__(self, db: Session):
        self.db = db

    def count_users_by_role(self) -> dict[UserRole, int]:
        stmt = (
            select(User.role, func.count())
            .where(User.deleted_at.is_(None))
            .group_by(User.role)
        )
        return dict(self.db.execute(stmt).all())

    def count_active_masters(self) -> int:
        stmt = select(func.count()).select_from(Master).where(
            Master.deleted_at.is_(None), Master.is_active.is_(True)
        )
        return self.db.execute(stmt).scalar_one()

    def count_active_services(self) -> int:
        stmt = select(func.count()).select_from(Service).where(
            Service.deleted_at.is_(None), Service.is_active.is_(True)
        )
        return self.db.execute(stmt).scalar_one()

    def appointments_and_revenue_since(self, since: datetime) -> tuple[int, Decimal]:
        """Количество и суммарная выручка завершённых визитов с указанной даты.

        Фильтр по start_time (дата визита), а не created_at: запись, сделанная
        в мае на июнь, относится к июню — дашборд показывает «выручку за месяц»,
        а не «выручку от записей, созданных в этом месяце»."""
        stmt = select(
            func.count(), func.coalesce(func.sum(Appointment.final_price), 0)
        ).where(
            Appointment.start_time >= since,
            Appointment.status == AppointmentStatus.done,
        )
        count, revenue = self.db.execute(stmt).one()
        return count, revenue

    def daily_registrations(self, since: datetime) -> list[tuple[datetime, int]]:
        # Сутки — по UTC независимо от таймзоны сессии БД (см. report_repository)
        day = func.date(func.timezone("UTC", User.created_at))
        stmt = (
            select(day.label("day"), func.count())
            .where(User.created_at >= since, User.deleted_at.is_(None))
            .group_by(day)
            .order_by(day)
        )
        return list(self.db.execute(stmt).all())
