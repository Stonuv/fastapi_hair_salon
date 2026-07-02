from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.enums import AppointmentStatus, UserRole
from ..models.user import User
from ..repositories.appointment_repository import AppointmentRepository
from ..repositories.master_repository import MasterRepository
from ..repositories.schedule_repository import ScheduleRepository
from ..repositories.service_repository import ServiceRepository
from ..schemas.appointment import (AppointmentBriefResponse, AppointmentCreate,
                                   AppointmentResponse, SlotListResponse, SlotResponse)
from ..schemas.pagination import PageResponse

# Допустимые переходы статуса записи (1.5 — машина состояний).
# pending -> confirmed -> done — основной путь, cancelled достижим из pending/confirmed.
# done и cancelled — терминальные состояния, переходов из них нет.
#
# Осознанная политика (зафиксировано по итогам аудита, ISSUES.md 4.5):
# - клиент может отменить запись в любой момент до её завершения, в том числе
#   прямо перед началом — штрафов/дедлайна отмены в ТЗ нет;
# - мастер может пометить запись done до её фактического начала (например,
#   клиент пришёл раньше) — привязки к start_time сознательно нет.
ALLOWED_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.pending:   {AppointmentStatus.confirmed, AppointmentStatus.cancelled},
    AppointmentStatus.confirmed: {AppointmentStatus.done, AppointmentStatus.cancelled},
    AppointmentStatus.done:      set(),
    AppointmentStatus.cancelled: set(),
}


class AppointmentService:
    def __init__(self, db: Session):
        self.db = db
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

        if master.user_id == client_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Нельзя записаться к себе")

        service = self.service_repo.get_by_id(data.service_id)
        if not service or not service.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Услуга не найдена или неактивна")

        # 2. Мастер оказывает эту услугу?
        ms = self.master_repo.get_master_service(data.master_id, data.service_id)
        if not ms:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Мастер не оказывает данную услугу")

        # Записаться можно только на будущее время
        if data.start_time <= datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Нельзя записаться на прошедшее время")

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

        # 6. Сохраняем. Проверка пересечения выше — только pre-flight для
        # понятной ошибки; от гонки двух одновременных бронирований защищает
        # EXCLUDE-констрейнт no_double_booking, и его нарушение — это 409, не 500.
        try:
            appointment = self.appointment_repo.create(
                client_id, data, end_time, round(final_price, 2)
            )
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Выбранное время уже занято")
        return AppointmentResponse.model_validate(
            self.appointment_repo.get_by_id(appointment.id)
        )

    # ── Получение записей ────────────────────────────────────────

    def get_by_id(self, appointment_id: UUID,
                  requesting_user: User) -> AppointmentResponse:
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Запись не найдена")

        # Доступ: владелец записи, её мастер или администратор
        if requesting_user.role != UserRole.admin:
            master = self.master_repo.get_by_user_id(requesting_user.id)
            is_owner  = appointment.client_id == requesting_user.id
            is_master = master and master.id == appointment.master_id
            if not is_owner and not is_master:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Нет доступа к этой записи")

        return AppointmentResponse.model_validate(appointment)

    def list_for_client(self, client_id: UUID, *, page: int, page_size: int,
                        status_filter: AppointmentStatus | None = None,
                        ) -> PageResponse[AppointmentBriefResponse]:
        """Мои записи (личный кабинет клиента)."""
        appointments, total = self.appointment_repo.list_paginated(
            page=page, page_size=page_size,
            client_id=client_id, status=status_filter,
        )
        return PageResponse[AppointmentBriefResponse](
            items=[AppointmentBriefResponse.model_validate(a) for a in appointments],
            total=total, page=page, page_size=page_size,
        )

    def list_for_master(self, master_id: UUID, requesting_user: User, *,
                        page: int, page_size: int,
                        status_filter: AppointmentStatus | None = None,
                        date_from: datetime | None = None,
                        date_to: datetime | None = None,
                        ) -> PageResponse[AppointmentBriefResponse]:
        """
        Записи конкретного мастера. Мастер может смотреть только свои —
        админ может смотреть любые.
        """
        if requesting_user.role != UserRole.admin:
            own_master = self.master_repo.get_by_user_id(requesting_user.id)
            if not own_master or own_master.id != master_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Можно смотреть только свои записи")

        appointments, total = self.appointment_repo.list_paginated(
            page=page, page_size=page_size, master_id=master_id,
            status=status_filter, date_from=date_from, date_to=date_to,
        )
        return PageResponse[AppointmentBriefResponse](
            items=[AppointmentBriefResponse.model_validate(a) for a in appointments],
            total=total, page=page, page_size=page_size,
        )

    def list_all(self, *, page: int, page_size: int,
                client_id: UUID | None = None,
                master_id: UUID | None = None,
                status_filter: AppointmentStatus | None = None,
                date_from: datetime | None = None,
                date_to: datetime | None = None,
                ) -> PageResponse[AppointmentBriefResponse]:
        """Все записи системы — для администратора (1.4: фильтр + пагинация)."""
        appointments, total = self.appointment_repo.list_paginated(
            page=page, page_size=page_size, client_id=client_id, master_id=master_id,
            status=status_filter, date_from=date_from, date_to=date_to,
        )
        return PageResponse[AppointmentBriefResponse](
            items=[AppointmentBriefResponse.model_validate(a) for a in appointments],
            total=total, page=page, page_size=page_size,
        )

    # ── Отмена (клиентом) ─────────────────────────────────────────

    def cancel(self, appointment_id: UUID,
              requesting_user_id: UUID) -> AppointmentResponse:
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Запись не найдена")

        if appointment.client_id != requesting_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Можно отменить только свою запись")

        if AppointmentStatus.cancelled not in ALLOWED_TRANSITIONS[appointment.status]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Нельзя отменить запись со статусом '{appointment.status.value}'")

        appointment = self.appointment_repo.update_status(
            appointment, AppointmentStatus.cancelled
        )
        return AppointmentResponse.model_validate(appointment)

    # ── Смена статуса (мастером / админом) ───────────────────────

    def update_status(self, appointment_id: UUID, new_status: AppointmentStatus,
                      requesting_user: User) -> AppointmentResponse:
        """
        confirm/done/cancel со стороны мастера или администратора —
        переход проверяется по ALLOWED_TRANSITIONS (1.5).
        """
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Запись не найдена")

        if requesting_user.role != UserRole.admin:
            own_master = self.master_repo.get_by_user_id(requesting_user.id)
            if not own_master or own_master.id != appointment.master_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Можно менять статус только своих записей")

        if new_status not in ALLOWED_TRANSITIONS[appointment.status]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Переход '{appointment.status.value}' → '{new_status.value}' недопустим",
            )

        appointment = self.appointment_repo.update_status(appointment, new_status)
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
        if not master or not master.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Мастер не найден или неактивен")

        service = self.service_repo.get_by_id(service_id)
        if not service or not service.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Услуга не найдена или неактивна")

        # Слоты имеют смысл только для услуги, которую мастер оказывает —
        # те же проверки, что и при создании записи.
        if not self.master_repo.get_master_service(master_id, service_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Мастер не оказывает данную услугу")

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
        # Репозиторий уже отфильтровал отменённые и вернул записи,
        # пересекающие рабочее окно (в т.ч. начавшиеся до него).
        booked_ranges = [
            (a.start_time, a.end_time)
            for a in self.appointment_repo.get_by_master_in_range(
                master_id, day_start, day_end
            )
        ]

        # Генерируем слоты. Сетка не фиксированная: наткнувшись на занятый
        # интервал, следующий слот начинаем сразу после его конца — иначе
        # запись, не выровненная по шагу duration (другая услуга с другой
        # длительностью), «съедала» бы два слота, а реальные окна между
        # записями не предлагались. Прошедшие слоты (на сегодня) не отдаём.
        now      = datetime.now(timezone.utc)
        duration = timedelta(minutes=service.duration_min)
        slots    = []
        current  = day_start

        while current + duration <= day_end:
            slot_end = current + duration
            conflict_end = max(
                (b_end for b_start, b_end in booked_ranges
                 if current < b_end and slot_end > b_start),
                default=None,
            )
            if conflict_end is not None:
                current = conflict_end
                continue
            if current > now:
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
        """Проверяет что запись попадает в рабочие часы мастера.

        Конвенция таймзон: Schedule.start_time/end_time — «настенные часы»
        салона в UTC. start_time приходит сюда уже нормализованным в UTC
        (валидатор AppointmentCreate), поэтому и день недели, и рабочее окно
        считаются в UTC — так же, как в get_available_slots. Раньше окно
        собиралось с tzinfo клиента, и одна и та же запись валидировалась
        против разных интервалов в двух местах.
        """
        day_of_week = start_time.weekday()
        schedule = self.schedule_repo.get_by_master_and_day(master_id, day_of_week)

        if not schedule or not schedule.is_working:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Мастер не работает в этот день",
            )

        work_start = datetime.combine(start_time.date(), schedule.start_time).replace(
            tzinfo=timezone.utc
        )
        work_end = datetime.combine(start_time.date(), schedule.end_time).replace(
            tzinfo=timezone.utc
        )

        if start_time < work_start or end_time > work_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Запись выходит за рамки рабочего времени мастера "
                       f"({schedule.start_time}–{schedule.end_time})",
            )
