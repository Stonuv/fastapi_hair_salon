import uuid
from datetime import datetime
from typing import Literal, Optional

from sqlalchemy import select
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

    def get_by_id(self, appointment_id: uuid.UUID) -> Optional[Appointment]:
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
        stmt = select(Appointment)
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
        """Все записи мастера в диапазоне — для расчёта свободных слотов (без пагинации,
        нужен полный набор, а не одна страница)."""
        stmt = (
            select(Appointment)
            .where(
                Appointment.master_id == master_id,
                Appointment.start_time >= date_from,
                Appointment.start_time <= date_to,
            )
            .order_by(Appointment.start_time)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_overlapping(self, master_id: uuid.UUID,
                        start_time: datetime,
                        end_time: datetime,
                        exclude_id: uuid.UUID | None = None) -> Optional[Appointment]:
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
               end_time: datetime, final_price: float) -> Appointment:
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
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    # ── Обновление статуса ────────────────────────────────────────

    def update_status(self, appointment: Appointment,
                      status: AppointmentStatus) -> Appointment:
        appointment.status = status
        self.db.commit()
        self.db.refresh(appointment)
        return appointment
