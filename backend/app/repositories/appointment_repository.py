from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import Optional
from uuid import UUID
from datetime import datetime

from ..models.appointment import Appointment
from ..models.enums import AppointmentStatus
from ..schemas.appointment import AppointmentCreate


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, appointment_id: UUID) -> Optional[Appointment]:
        """Загружает запись со всеми связями для детальной страницы."""
        return (
            self.db.query(Appointment)
            .options(
                joinedload(Appointment.client),
                joinedload(Appointment.master).joinedload("user"),
                joinedload(Appointment.service),
            )
            .filter(Appointment.id == appointment_id)
            .first()
        )

    def get_by_client(self, client_id: UUID) -> list[Appointment]:
        """Все записи клиента, свежие сверху."""
        return (
            self.db.query(Appointment)
            .filter(Appointment.client_id == client_id)
            .order_by(Appointment.start_time.desc())
            .all()
        )

    def get_by_master(self, master_id: UUID,
                      date_from: Optional[datetime] = None,
                      date_to:   Optional[datetime] = None) -> list[Appointment]:
        """Записи мастера, опционально ограниченные диапазоном дат."""
        query = (
            self.db.query(Appointment)
            .filter(Appointment.master_id == master_id)
        )
        if date_from:
            query = query.filter(Appointment.start_time >= date_from)
        if date_to:
            query = query.filter(Appointment.start_time <= date_to)
        return query.order_by(Appointment.start_time).all()

    def get_overlapping(self, master_id: UUID,
                        start_time: datetime,
                        end_time:   datetime,
                        exclude_id: Optional[UUID] = None) -> Optional[Appointment]:
        """
        Ищет пересекающиеся записи у мастера в заданном диапазоне времени.
        Нужно для проверки двойного бронирования на уровне сервиса —
        до того как PostgreSQL выбросит ошибку из EXCLUDE USING gist.

        Два интервала [A, B) и [C, D) пересекаются когда A < D и C < B.
        """
        query = self.db.query(Appointment).filter(
            Appointment.master_id == master_id,
            Appointment.status.notin_([
                AppointmentStatus.cancelled,
            ]),
            Appointment.start_time < end_time,
            Appointment.end_time   > start_time,
        )
        if exclude_id:
            query = query.filter(Appointment.id != exclude_id)
        return query.first()

    # ── Создание ─────────────────────────────────────────────────

    def create(self, client_id: UUID, data: AppointmentCreate,
               end_time: datetime, final_price: float) -> Appointment:
        """
        end_time и final_price вычисляются в сервисе и передаются сюда готовыми.
        Репозиторий только сохраняет — без логики.
        """
        appointment = Appointment(
            client_id   = client_id,
            master_id   = data.master_id,
            service_id  = data.service_id,
            start_time  = data.start_time,
            end_time    = end_time,
            final_price = final_price,
            status      = AppointmentStatus.pending,
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
