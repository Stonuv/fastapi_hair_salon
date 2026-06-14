from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime, timedelta, timezone, date

from ..repositories.appointment_repository import AppointmentRepository
from ..repositories.master_repository import MasterRepository
from ..repositories.service_repository import ServiceRepository
from ..repositories.schedule_repository import ScheduleRepository
from ..models.enums import AppointmentStatus
from ..schemas.appointment import (AppointmentCreate, AppointmentResponse,
                                   AppointmentBriefResponse, AppointmentListResponse,
                                   SlotResponse, SlotListResponse)


class AppointmentService:
    def __init__(self, db: Session):
        self.appointment_repo = AppointmentRepository(db)
        self.master_repo      = MasterRepository(db)
        self.service_repo     = ServiceRepository(db)
        self.schedule_repo    = ScheduleRepository(db)

    # ── Создание записи ──────────────────────────────────────────

    def create(self, client_id: UUID, data: AppointmentCreate) -> AppointmentResponse:
        # 1. Проверяем что мастер и услуга существуют
        master = self.master_repo.get_by_id(data.master_id)
        if not master or not master.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Мастер не найден или неактивен")

        service = self.service_repo.get_by_id(data.service_id)
        if not service or not service.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Услуга не найдена или неактивна")

        # 2. Мастер оказывает эту услугу?
        ms = self.master_repo.get_master_service(data.master_id, data.service_id)
        if not ms:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Мастер не оказывает данную услугу")

        # 3. Вычисляем end_time и финальную цену
        end_time = data.start_time + timedelta(minutes=service.duration_min)
        final_price = (
            float(ms.price_override)
            if ms.price_override is not None
            else float(service.price) * float(master.coefficient)
        )

        # 4. Попадает ли слот в рабочее расписание?
        self._validate_within_schedule(data.master_id, data.start_time, end_time)

        # 5. Нет ли пересечения с другой записью?
        overlap = self.appointment_repo.get_overlapping(
            data.master_id, data.start_time, end_time
        )
        if overlap:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Выбранное время уже занято")

        # 6. Сохраняем
        appointment = self.appointment_repo.create(
            client_id, data, end_time, round(final_price, 2)
        )
        return AppointmentResponse.model_validate(
            self.appointment_repo.get_by_id(appointment.id)
        )

    # ── Получение записей ────────────────────────────────────────

    def get_by_id(self, appointment_id: UUID,
                  requesting_user_id: UUID) -> AppointmentResponse:
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Запись не найдена")

        # Клиент видит только свои записи
        master = self.master_repo.get_by_user_id(requesting_user_id)
        is_owner  = appointment.client_id == requesting_user_id
        is_master = master and master.id == appointment.master_id
        if not is_owner and not is_master:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Нет доступа к этой записи")

        return AppointmentResponse.model_validate(appointment)

    def get_my_appointments(self, client_id: UUID) -> AppointmentListResponse:
        appointments = self.appointment_repo.get_by_client(client_id)
        return AppointmentListResponse(
            appointments=[AppointmentBriefResponse.model_validate(a)
                          for a in appointments],
            total=len(appointments),
        )

    def get_master_appointments(self, master_id: UUID,
                                date_from: datetime | None,
                                date_to:   datetime | None) -> AppointmentListResponse:
        appointments = self.appointment_repo.get_by_master(
            master_id, date_from, date_to
        )
        return AppointmentListResponse(
            appointments=[AppointmentBriefResponse.model_validate(a)
                          for a in appointments],
            total=len(appointments),
        )

    # ── Отмена ───────────────────────────────────────────────────

    def cancel(self, appointment_id: UUID,
               requesting_user_id: UUID) -> AppointmentResponse:
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Запись не найдена")

        if appointment.client_id != requesting_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Можно отменить только свою запись")

        if appointment.status not in (AppointmentStatus.pending,
                                      AppointmentStatus.confirmed):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Нельзя отменить запись со статусом '{appointment.status}'")

        appointment = self.appointment_repo.update_status(
            appointment, AppointmentStatus.cancelled
        )
        return AppointmentResponse.model_validate(appointment)

    # ── Свободные слоты ──────────────────────────────────────────

    def get_available_slots(self, master_id: UUID,
                            target_date: date,
                            service_id: UUID) -> SlotListResponse:
        """
        Возвращает список свободных слотов мастера на конкретный день.
        Алгоритм:
          1. Берём расписание мастера на этот день недели
          2. Разбиваем рабочий день на слоты по длительности услуги
          3. Убираем слоты которые пересекаются с существующими записями
        """
        master = self.master_repo.get_by_id(master_id)
        if not master:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Мастер не найден")

        service = self.service_repo.get_by_id(service_id)
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Услуга не найдена")

        # day_of_week: weekday() возвращает 0=пн … 6=вс — совпадает с нашей схемой
        day_of_week = target_date.weekday()
        schedule = self.schedule_repo.get_by_master_and_day(master_id, day_of_week)

        if not schedule or not schedule.is_working:
            return SlotListResponse(
                master_id=master_id,
                date=target_date.isoformat(),
                slots=[],
            )

        # Существующие записи мастера на этот день
        day_start = datetime.combine(target_date, schedule.start_time).replace(
            tzinfo=timezone.utc
        )
        day_end = datetime.combine(target_date, schedule.end_time).replace(
            tzinfo=timezone.utc
        )
        booked = self.appointment_repo.get_by_master(
            master_id, date_from=day_start, date_to=day_end
        )
        booked_ranges = [
            (a.start_time, a.end_time)
            for a in booked
            if a.status != AppointmentStatus.cancelled
        ]

        # Генерируем слоты
        duration = timedelta(minutes=service.duration_min)
        slots    = []
        current  = day_start

        while current + duration <= day_end:
            slot_end = current + duration
            # Слот свободен если не пересекается ни с одной записью
            is_free = not any(
                current < b_end and slot_end > b_start
                for b_start, b_end in booked_ranges
            )
            if is_free:
                slots.append(SlotResponse(start_time=current, end_time=slot_end))
            current += duration

        return SlotListResponse(
            master_id=master_id,
            date=target_date.isoformat(),
            slots=slots,
        )

    # ── Вспомогательное ──────────────────────────────────────────

    def _validate_within_schedule(self, master_id: UUID,
                                  start_time: datetime,
                                  end_time: datetime) -> None:
        """Проверяет что запись попадает в рабочие часы мастера."""
        day_of_week = start_time.weekday()
        schedule = self.schedule_repo.get_by_master_and_day(master_id, day_of_week)

        if not schedule or not schedule.is_working:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Мастер не работает в этот день",
            )

        work_start = datetime.combine(start_time.date(), schedule.start_time).replace(
            tzinfo=start_time.tzinfo
        )
        work_end = datetime.combine(start_time.date(), schedule.end_time).replace(
            tzinfo=start_time.tzinfo
        )

        if start_time < work_start or end_time > work_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Запись выходит за рамки рабочего времени мастера "
                       f"({schedule.start_time}–{schedule.end_time})",
            )
