import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..models.appointment import Appointment
from ..models.enums import AppointmentStatus
from ..models.master import Master
from ..schemas.appointment import AppointmentCreate
from ._query_utils import paginated


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, appointment_id: uuid.UUID) -> Appointment | None:
        """Загружает запись со всеми связями для детальной страницы."""
        stmt = (
            select(Appointment)
            .options(
                joinedload(Appointment.client),
                joinedload(Appointment.master).joinedload(Master.user),
                joinedload(Appointment.service),
            )
            .where(Appointment.id == appointment_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        client_id: uuid.UUID | None = None,
        master_id: uuid.UUID | None = None,
        status: AppointmentStatus | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> tuple[list[Appointment], int]:
        """Список записей с фильтром по клиенту/мастеру/статусу/диапазону дат (1.4)."""
        stmt = select(Appointment).options(
            joinedload(Appointment.review),
            joinedload(Appointment.client),
            joinedload(Appointment.master).joinedload(Master.user),
            joinedload(Appointment.service),
        )
        if client_id is not None:
            stmt = stmt.where(Appointment.client_id == client_id)
        if master_id is not None:
            stmt = stmt.where(Appointment.master_id == master_id)
        if status is not None:
            stmt = stmt.where(Appointment.status == status)
        if date_from is not None:
            stmt = stmt.where(Appointment.start_time >= date_from)
        if date_to is not None:
            stmt = stmt.where(Appointment.start_time <= date_to)

        order = Appointment.start_time.asc() if sort_order == "asc" else Appointment.start_time.desc()
        stmt = stmt.order_by(order)

        return paginated(self.db, stmt, page=page, page_size=page_size)

    def get_by_master_in_range(self, master_id: uuid.UUID,
                               date_from: datetime,
                               date_to: datetime) -> list[Appointment]:
        """Неотменённые записи мастера, пересекающие диапазон — для расчёта
        свободных слотов (без пагинации, нужен полный набор).

        Условие — пересечение интервалов, а не start_time внутри диапазона:
        запись, начавшаяся до date_from (например, созданная до изменения
        расписания), но заходящая в рабочее окно, тоже занимает слоты."""
        stmt = (
            select(Appointment)
            .where(
                Appointment.master_id == master_id,
                Appointment.status != AppointmentStatus.cancelled,
                Appointment.start_time < date_to,
                Appointment.end_time > date_from,
            )
            .order_by(Appointment.start_time)
        )
        return list(self.db.execute(stmt).scalars().all())

    def count_active_for_client(self, client_id: uuid.UUID) -> int:
        """Число незавершённых записей клиента (pending/confirmed) — для лимита
        на одновременные бронирования (см. settings.max_active_appointments_per_client)."""
        stmt = select(func.count()).where(
            Appointment.client_id == client_id,
            Appointment.status.in_((AppointmentStatus.pending, AppointmentStatus.confirmed)),
        )
        return self.db.execute(stmt).scalar_one()

    def get_overlapping(self, master_id: uuid.UUID,
                        start_time: datetime,
                        end_time: datetime,
                        exclude_id: uuid.UUID | None = None) -> Appointment | None:
        """
        Ищет пересекающиеся записи у мастера в заданном диапазоне времени.
        Нужно для проверки двойного бронирования на уровне сервиса —
        до того как PostgreSQL выбросит ошибку из EXCLUDE USING gist.

        Два интервала [A, B) и [C, D) пересекаются когда A < D и C < B.
        """
        stmt = select(Appointment).where(
            Appointment.master_id == master_id,
            Appointment.status != AppointmentStatus.cancelled,
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        )
        if exclude_id:
            stmt = stmt.where(Appointment.id != exclude_id)
        return self.db.execute(stmt).scalars().first()

    # ── Создание ─────────────────────────────────────────────────

    def create(self, client_id: uuid.UUID, data: AppointmentCreate,
               end_time: datetime, final_price: Decimal) -> Appointment:
        """
        end_time и final_price вычисляются в сервисе и передаются сюда готовыми.
        Репозиторий только сохраняет — без логики.
        """
        appointment = Appointment(
            client_id=client_id,
            master_id=data.master_id,
            service_id=data.service_id,
            start_time=data.start_time,
            end_time=end_time,
            final_price=final_price,
            status=AppointmentStatus.pending,
        )
        self.db.add(appointment)
        self.db.flush()
        self.db.refresh(appointment)
        return appointment

    # ── Обновление статуса ────────────────────────────────────────

    def update_status(self, appointment: Appointment,
                      status: AppointmentStatus) -> Appointment:
        appointment.status = status
        self.db.flush()
        self.db.refresh(appointment)
        return appointment

    def update_schedule(self, appointment: Appointment, start_time: datetime,
                        end_time: datetime) -> Appointment:
        """Перенос записи мастером. Сбрасывает уже отправленные напоминания
        (reminder_*_sent_at) — они считались под старое время; иначе для
        перенесённой записи напоминание на новое время просто не пришло бы
        (флаг "уже отправлено" остался бы true с прошлого раза)."""
        appointment.start_time = start_time
        appointment.end_time = end_time
        appointment.reminder_24h_sent_at = None
        appointment.reminder_2h_sent_at = None
        self.db.flush()
        self.db.refresh(appointment)
        return appointment

    # ── Напоминания (ReminderService) ───────────────────────────────

    def list_due_24h_reminders(self, now: datetime) -> list[Appointment]:
        """Записи, которым пора получить напоминание "за 24 часа": ещё не
        отправлено, до начала остался 24-часовой рубеж, но ещё больше 2
        часов — если опрос пропустил окно (бэкенд был недоступен), запись
        уже попавшая в 2-часовое окно получит только "за 2 часа", без
        задвоения писем."""
        stmt = (
            select(Appointment)
            .options(
                joinedload(Appointment.client),
                joinedload(Appointment.master).joinedload(Master.user),
                joinedload(Appointment.service),
            )
            .where(
                Appointment.status.in_((AppointmentStatus.pending, AppointmentStatus.confirmed)),
                Appointment.reminder_24h_sent_at.is_(None),
                Appointment.start_time > now + timedelta(hours=2),
                Appointment.start_time <= now + timedelta(hours=24),
            )
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def list_due_2h_reminders(self, now: datetime) -> list[Appointment]:
        """Записи, которым пора получить напоминание "за 2 часа"."""
        stmt = (
            select(Appointment)
            .options(
                joinedload(Appointment.client),
                joinedload(Appointment.master).joinedload(Master.user),
                joinedload(Appointment.service),
            )
            .where(
                Appointment.status.in_((AppointmentStatus.pending, AppointmentStatus.confirmed)),
                Appointment.reminder_2h_sent_at.is_(None),
                Appointment.start_time > now,
                Appointment.start_time <= now + timedelta(hours=2),
            )
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def mark_24h_reminder_sent(self, appointment: Appointment) -> None:
        appointment.reminder_24h_sent_at = datetime.now(timezone.utc)
        self.db.flush()

    def mark_2h_reminder_sent(self, appointment: Appointment) -> None:
        appointment.reminder_2h_sent_at = datetime.now(timezone.utc)
        self.db.flush()
