import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.appointment import Appointment
from ..models.enums import AppointmentStatus
from ..models.master import Master
from ..models.review import Review
from ..models.service import Service
from ..models.user import User


class ReportRepository:
    """salon_id (ROADMAP.md §4.8, Фаза C) — None означает всю сеть (owner);
    Appointment.salon_id денормализован (снимок на момент брони), поэтому
    фильтр не требует join'а на Master."""

    def __init__(self, db: Session):
        self.db = db

    def _done_in_range(self, date_from: date, date_to: date, salon_id: uuid.UUID | None = None):
        # Границы суток — явно в UTC: naive datetime сравнивался бы
        # с timestamptz по таймзоне сессии PostgreSQL.
        conditions = [
            Appointment.start_time >= datetime.combine(date_from, time.min, tzinfo=timezone.utc),
            Appointment.start_time <= datetime.combine(date_to, time.max, tzinfo=timezone.utc),
            Appointment.status == AppointmentStatus.done,
        ]
        if salon_id is not None:
            conditions.append(Appointment.salon_id == salon_id)
        return conditions

    def get_summary(self, date_from: date, date_to: date,
                    salon_id: uuid.UUID | None = None) -> tuple[int, Decimal, Decimal]:
        """(total_appointments, total_revenue, avg_check) for done appointments."""
        stmt = select(
            func.count(),
            func.coalesce(func.sum(Appointment.final_price), 0),
            func.coalesce(func.avg(Appointment.final_price), 0),
        ).where(*self._done_in_range(date_from, date_to, salon_id))
        count, revenue, avg = self.db.execute(stmt).one()
        return int(count), Decimal(revenue), Decimal(avg)

    def get_repeat_clients_pct(self, date_from: date, date_to: date,
                              salon_id: uuid.UUID | None = None) -> float:
        """% of clients who visited in the period AND had a prior visit before it."""
        period_start = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        period_end = datetime.combine(date_to, time.max, tzinfo=timezone.utc)

        period_conditions = [
            Appointment.start_time >= period_start,
            Appointment.start_time <= period_end,
            Appointment.status == AppointmentStatus.done,
        ]
        if salon_id is not None:
            period_conditions.append(Appointment.salon_id == salon_id)
        period_clients = (
            select(Appointment.client_id).where(*period_conditions).distinct().subquery()
        )
        total = self.db.execute(select(func.count()).select_from(period_clients)).scalar_one() or 0
        if total == 0:
            return 0.0

        prior_conditions = [
            Appointment.start_time < period_start,
            Appointment.status == AppointmentStatus.done,
        ]
        if salon_id is not None:
            # Точка, в которой клиент вернулся, а не точка первого визита —
            # "повторный клиент этого салона", даже если впервые он приходил
            # в другую точку сети.
            prior_conditions.append(Appointment.salon_id == salon_id)
        returning = (
            select(func.count(Appointment.client_id.distinct()))
            .join(period_clients, Appointment.client_id == period_clients.c.client_id)
            .where(*prior_conditions)
        )
        repeat = self.db.execute(returning).scalar_one() or 0
        return round(repeat / total * 100, 1)

    def get_revenue_by_day(self, date_from: date, date_to: date,
                           salon_id: uuid.UUID | None = None) -> list[tuple]:
        # func.date(timestamptz) режет сутки по таймзоне сессии БД —
        # фиксируем UTC, чтобы группировка совпадала с границами _done_in_range.
        day = func.date(func.timezone("UTC", Appointment.start_time))
        stmt = (
            select(day.label("date"), func.coalesce(func.sum(Appointment.final_price), 0).label("revenue"))
            .where(*self._done_in_range(date_from, date_to, salon_id))
            .group_by(day)
            .order_by(day)
        )
        return list(self.db.execute(stmt).all())

    def get_appointments_by_service(self, date_from: date, date_to: date,
                                    salon_id: uuid.UUID | None = None) -> list[tuple]:
        stmt = (
            select(Service.name.label("service_name"), func.count().label("appointments"))
            .join(Appointment, Appointment.service_id == Service.id)
            .where(*self._done_in_range(date_from, date_to, salon_id))
            .group_by(Service.id, Service.name)
            .order_by(func.count().desc())
        )
        return list(self.db.execute(stmt).all())

    def get_masters_breakdown(self, date_from: date, date_to: date,
                              salon_id: uuid.UUID | None = None) -> list[tuple]:
        stmt = (
            select(
                (User.first_name + " " + User.last_name).label("master_name"),
                func.count(Appointment.id).label("appointments"),
                func.coalesce(func.sum(Appointment.final_price), 0).label("revenue"),
                func.coalesce(func.avg(Appointment.final_price), 0).label("avg_check"),
                func.avg(Review.rating).label("avg_rating"),
            )
            .join(Master, Master.id == Appointment.master_id)
            .join(User, User.id == Master.user_id)
            .outerjoin(Review, Review.appointment_id == Appointment.id)
            .where(*self._done_in_range(date_from, date_to, salon_id))
            .group_by(Master.id, User.first_name, User.last_name)
            .order_by(func.sum(Appointment.final_price).desc())
        )
        return list(self.db.execute(stmt).all())
