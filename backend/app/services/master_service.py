from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID

from ..repositories.master_repository import MasterRepository
from ..repositories.service_repository import ServiceRepository
from ..repositories.schedule_repository import ScheduleRepository
from ..schemas.master import (MasterResponse, MasterBriefResponse,
                               MasterListResponse, MasterUpdate,
                               MasterServiceResponse)
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from ..schemas.service import ServiceResponse


class MasterService:
    def __init__(self, db: Session):
        self.master_repo   = MasterRepository(db)
        self.service_repo  = ServiceRepository(db)
        self.schedule_repo = ScheduleRepository(db)

    # ── Каталог мастеров ─────────────────────────────────────────

    def get_all(self) -> MasterListResponse:
        masters = self.master_repo.get_all_active()
        return MasterListResponse(
            masters=[MasterBriefResponse(
                id             = m.id,
                first_name     = m.user.first_name,
                last_name      = m.user.last_name,
                specialization = m.specialization,
                photo_url      = m.photo_url,
                coefficient    = float(m.coefficient),
            ) for m in masters],
            total=len(masters),
        )

    def get_by_id(self, master_id: UUID) -> MasterResponse:
        master = self.master_repo.get_by_id(master_id)
        if not master:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Мастер {master_id} не найден",
            )
        return MasterResponse.model_validate(master)

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
            # Итоговая цена: price_override если задан, иначе price * coefficient
            final_price = (
                float(ms.price_override)
                if ms.price_override is not None
                else float(ms.service.price) * float(master.coefficient)
            )
            result.append(MasterServiceResponse(
                service        = ServiceResponse.model_validate(ms.service),
                price_override = float(ms.price_override) if ms.price_override else None,
                final_price    = round(final_price, 2),
            ))
        return result

    def add_service(self, master_id: UUID, service_id: UUID,
                    price_override: float | None = None) -> MasterServiceResponse:
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
        final_price = (
            float(price_override)
            if price_override is not None
            else float(service.price) * float(master.coefficient)
        )
        return MasterServiceResponse(
            service        = ServiceResponse.model_validate(service),
            price_override = price_override,
            final_price    = round(final_price, 2),
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
        schedule = self.schedule_repo.update(schedule, data)
        return ScheduleResponse.model_validate(schedule)

    # ── Вспомогательное ──────────────────────────────────────────

    def _check_master_exists(self, master_id: UUID) -> None:
        if not self.master_repo.get_by_id(master_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Мастер {master_id} не найден",
            )
