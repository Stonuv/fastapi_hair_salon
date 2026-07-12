from decimal import ROUND_HALF_UP, Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..repositories.master_repository import MasterRepository
from ..repositories.review_repository import ReviewRepository
from ..repositories.schedule_repository import ScheduleRepository
from ..repositories.service_repository import ServiceRepository
from ..schemas.master import (MasterBriefResponse, MasterPublicResponse,
                              MasterResponse, MasterServiceResponse, MasterUpdate)
from ..schemas.pagination import PageResponse
from ..schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleUpdate
from ..schemas.service import ServiceResponse


def _final_price(price_override: Decimal | None, base_price: Decimal,
                 coefficient: Decimal) -> Decimal:
    """Итоговая цена услуги мастера: override, если задан, иначе базовая ×
    коэффициент. Вся арифметика в Decimal — та же формула, что в
    AppointmentService.create()."""
    if price_override is not None:
        return price_override
    return (base_price * coefficient).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class MasterService:
    def __init__(self, db: Session):
        self.master_repo   = MasterRepository(db)
        self.service_repo  = ServiceRepository(db)
        self.schedule_repo = ScheduleRepository(db)
        self.review_repo   = ReviewRepository(db)

    # ── Каталог мастеров ─────────────────────────────────────────

    def list_paginated(
        self, *, page: int, page_size: int,
        specialization: str | None = None,
        service_id: UUID | None = None,
        sort_by: Literal["name", "price"] = "name",
        sort_order: Literal["asc", "desc"] = "asc",
    ) -> PageResponse[MasterBriefResponse]:
        masters, total = self.master_repo.list_paginated(
            page=page, page_size=page_size, specialization=specialization,
            service_id=service_id, sort_by=sort_by, sort_order=sort_order,
        )
        return PageResponse[MasterBriefResponse](
            items=[MasterBriefResponse(
                id=m.id,
                first_name=m.user.first_name,
                last_name=m.user.last_name,
                specialization=m.specialization,
                photo_url=m.photo_url,
                coefficient=float(m.coefficient),
            ) for m in masters],
            total=total, page=page, page_size=page_size,
        )

    def get_by_id(self, master_id: UUID) -> MasterResponse:
        master = self.master_repo.get_by_id(master_id)
        if not master:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Мастер {master_id} не найден",
            )
        return MasterResponse.model_validate(master)

    def get_public_by_id(self, master_id: UUID) -> MasterPublicResponse:
        """Публичный профиль: деактивированный мастер наружу не отдаётся,
        контакты пользователя в схему не входят."""
        master = self.master_repo.get_by_id(master_id)
        if not master or not master.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Мастер {master_id} не найден",
            )
        rating, reviews_count = self.review_repo.rating_summary(master_id)
        response = MasterPublicResponse.model_validate(master)
        response.rating = rating
        response.reviews_count = reviews_count
        return response

    def update(self, master_id: UUID, data: MasterUpdate) -> MasterResponse:
        master = self.master_repo.get_by_id(master_id)
        if not master:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Мастер {master_id} не найден",
            )
        master = self.master_repo.update(master, data)
        return MasterResponse.model_validate(master)

    # ── Услуги мастера ───────────────────────────────────────────

    def get_services(self, master_id: UUID) -> list[MasterServiceResponse]:
        """Возвращает услуги мастера с итоговыми ценами."""
        master = self.master_repo.get_with_services(master_id)
        if not master:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Мастер {master_id} не найден",
            )
        result = []
        for ms in master.services:
            result.append(MasterServiceResponse(
                service        = ServiceResponse.model_validate(ms.service),
                price_override = ms.price_override,
                final_price    = _final_price(ms.price_override, ms.service.price,
                                              master.coefficient),
            ))
        return result

    def add_service(self, master_id: UUID, service_id: UUID,
                    price_override: Decimal | None = None) -> MasterServiceResponse:
        master  = self.master_repo.get_by_id(master_id)
        service = self.service_repo.get_by_id(service_id)

        if not master:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Мастер {master_id} не найден")
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Услуга {service_id} не найдена")

        existing = self.master_repo.get_master_service(master_id, service_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Услуга уже добавлена этому мастеру")

        ms = self.master_repo.add_service(master_id, service_id, price_override)
        return MasterServiceResponse(
            service        = ServiceResponse.model_validate(service),
            price_override = ms.price_override,
            final_price    = _final_price(ms.price_override, service.price,
                                          master.coefficient),
        )

    def remove_service(self, master_id: UUID, service_id: UUID) -> None:
        removed = self.master_repo.remove_service(master_id, service_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Услуга не найдена у этого мастера",
            )

    # ── Расписание мастера ───────────────────────────────────────

    def get_schedule(self, master_id: UUID) -> list[ScheduleResponse]:
        self._check_master_exists(master_id)
        schedules = self.schedule_repo.get_by_master(master_id)
        return [ScheduleResponse.model_validate(s) for s in schedules]

    def set_schedule(self, master_id: UUID,
                     data: ScheduleCreate) -> ScheduleResponse:
        self._check_master_exists(master_id)

        existing = self.schedule_repo.get_by_master_and_day(
            master_id, data.day_of_week
        )
        if existing:
            # Если расписание на этот день уже есть — обновляем
            schedule = self.schedule_repo.update(existing, data)  # type: ignore[arg-type]
        else:
            schedule = self.schedule_repo.create(master_id, data)

        return ScheduleResponse.model_validate(schedule)

    def update_schedule(self, master_id: UUID, day_of_week: int,
                        data: ScheduleUpdate) -> ScheduleResponse:
        self._check_master_exists(master_id)
        schedule = self.schedule_repo.get_by_master_and_day(master_id, day_of_week)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Расписание на день {day_of_week} не найдено",
            )

        # Pydantic проверяет пару start/end только когда переданы оба поля —
        # при частичном обновлении сверяем с текущими значениями, иначе
        # некорректная пара дойдёт до CHECK-констрейнта БД и даст 500.
        new_start = data.start_time if data.start_time is not None else schedule.start_time
        new_end   = data.end_time   if data.end_time   is not None else schedule.end_time
        if new_end <= new_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_time должен быть позже start_time",
            )

        schedule = self.schedule_repo.update(schedule, data)
        return ScheduleResponse.model_validate(schedule)

    # ── Вспомогательное ──────────────────────────────────────────

    def _check_master_exists(self, master_id: UUID) -> None:
        if not self.master_repo.get_by_id(master_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Мастер {master_id} не найден",
            )
