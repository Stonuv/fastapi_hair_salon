from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date

from ..database import get_db
from ..services.master_service import MasterService
from ..services.appointment_service import AppointmentService
from ..services.auth_service import get_current_admin, get_current_master, get_current_user
from ..schemas.master import (MasterListResponse, MasterResponse,
                               MasterUpdate, MasterServiceResponse)
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from ..schemas.appointment import SlotListResponse

router = APIRouter(prefix="/api/masters", tags=["masters"])


# ── Каталог ──────────────────────────────────────────────────────

@router.get("", response_model=MasterListResponse)
def get_masters(db: Session = Depends(get_db)):
    """Список активных мастеров. Публичный эндпоинт."""
    return MasterService(db).get_all()


@router.get("/{master_id}", response_model=MasterResponse)
def get_master(master_id: UUID, db: Session = Depends(get_db)):
    """Профиль мастера. Публичный эндпоинт."""
    return MasterService(db).get_by_id(master_id)


@router.patch("/{master_id}", response_model=MasterResponse)
def update_master(master_id: UUID, data: MasterUpdate,
                  db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Обновить профиль мастера. Только для администратора."""
    return MasterService(db).update(master_id, data)


# ── Услуги мастера ───────────────────────────────────────────────

@router.get("/{master_id}/services", response_model=list[MasterServiceResponse])
def get_master_services(master_id: UUID, db: Session = Depends(get_db)):
    """Услуги мастера с итоговыми ценами. Публичный эндпоинт."""
    return MasterService(db).get_services(master_id)


@router.post("/{master_id}/services", response_model=MasterServiceResponse,
             status_code=status.HTTP_201_CREATED)
def add_master_service(master_id: UUID, service_id: UUID,
                       price_override: float | None = None,
                       db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Добавить услугу мастеру. Только для администратора."""
    return MasterService(db).add_service(master_id, service_id, price_override)


@router.delete("/{master_id}/services/{service_id}",
               status_code=status.HTTP_204_NO_CONTENT)
def remove_master_service(master_id: UUID, service_id: UUID,
                          db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Убрать услугу у мастера. Только для администратора."""
    MasterService(db).remove_service(master_id, service_id)


# ── Расписание ───────────────────────────────────────────────────

@router.get("/{master_id}/schedule", response_model=list[ScheduleResponse])
def get_schedule(master_id: UUID, db: Session = Depends(get_db)):
    """Расписание мастера по дням недели. Публичный эндпоинт."""
    return MasterService(db).get_schedule(master_id)


@router.post("/{master_id}/schedule", response_model=ScheduleResponse,
             status_code=status.HTTP_201_CREATED)
def set_schedule(master_id: UUID, data: ScheduleCreate,
                 db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Задать расписание на день. Если уже существует — перезапишет."""
    return MasterService(db).set_schedule(master_id, data)


@router.patch("/{master_id}/schedule/{day_of_week}", response_model=ScheduleResponse)
def update_schedule(master_id: UUID, day_of_week: int, data: ScheduleUpdate,
                    db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Обновить расписание на конкретный день (0=пн … 6=вс)."""
    return MasterService(db).update_schedule(master_id, day_of_week, data)


# ── Свободные слоты ──────────────────────────────────────────────

@router.get("/{master_id}/slots", response_model=SlotListResponse)
def get_slots(master_id: UUID, service_id: UUID, target_date: date,
              db: Session = Depends(get_db)):
    """
    Свободные временные слоты мастера на дату.
    Публичный эндпоинт — используется на странице записи.

    Параметры запроса: ?service_id=...&target_date=2024-06-15
    """
    return AppointmentService(db).get_available_slots(
        master_id, target_date, service_id
    )
