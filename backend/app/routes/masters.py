from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.enums import UserRole
from ..models.user import User
from ..repositories.master_repository import MasterRepository
from ..schemas.appointment import SlotListResponse
from ..schemas.master import (MasterBriefResponse, MasterPublicResponse,
                              MasterResponse, MasterServiceCreate,
                              MasterServiceResponse, MasterUpdate)
from ..schemas.pagination import PageParams, PageResponse
from ..schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleUpdate
from ..services.appointment_service import AppointmentService
from ..services.auth_service import get_current_admin, get_current_master
from ..services.master_service import MasterService

router = APIRouter(prefix="/api/masters", tags=["masters"])


def _ensure_owner_or_admin(master_id: UUID, current_user: User, db: Session) -> None:
    """Мастер может управлять только своим профилем/расписанием — админ может всеми."""
    if current_user.role == UserRole.admin:
        return
    own_master = MasterRepository(db).get_by_user_id(current_user.id)
    if not own_master or own_master.id != master_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Доступ только к своему профилю")


# ── Каталог ──────────────────────────────────────────────────────

@router.get("", response_model=PageResponse[MasterBriefResponse])
def get_masters(
    *,
    db: Session = Depends(get_db),
    page_params: Annotated[PageParams, Depends()],
    specialization: Annotated[str | None, Query(description="Поиск по специализации")] = None,
    service_id: Annotated[UUID | None, Query(description="Фильтр: оказывает указанную услугу")] = None,
    sort_by: Annotated[Literal["name", "price"], Query()] = "name",
    sort_order: Annotated[Literal["asc", "desc"], Query()] = "asc",
):
    """Каталог активных мастеров — фильтр + сортировка + пагинация (1.4). Публичный эндпоинт."""
    return MasterService(db).list_paginated(
        page=page_params.page, page_size=page_params.page_size,
        specialization=specialization, service_id=service_id,
        sort_by=sort_by, sort_order=sort_order,
    )


@router.get("/me", response_model=MasterResponse)
def get_my_master_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_master),
):
    """Профиль мастера текущего пользователя — для кабинета мастера."""
    master = MasterRepository(db).get_by_user_id(current_user.id)
    if not master:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Профиль мастера не найден")
    return MasterResponse.model_validate(master)


@router.get("/{master_id}", response_model=MasterPublicResponse)
def get_master(master_id: UUID, db: Session = Depends(get_db)):
    """Профиль мастера. Публичный эндпоинт — без контактов пользователя,
    деактивированные мастера не отдаются."""
    return MasterService(db).get_public_by_id(master_id)


@router.patch("/{master_id}", response_model=MasterResponse)
def update_master(master_id: UUID, data: MasterUpdate,
                  db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_master)):
    """Обновить профиль мастера. Сам мастер или администратор."""
    _ensure_owner_or_admin(master_id, current_user, db)
    return MasterService(db).update(master_id, data)


# ── Услуги мастера ───────────────────────────────────────────────

@router.get("/{master_id}/services", response_model=list[MasterServiceResponse])
def get_master_services(master_id: UUID, db: Session = Depends(get_db)):
    """Услуги мастера с итоговыми ценами. Публичный эндпоинт."""
    return MasterService(db).get_services(master_id)


@router.post("/{master_id}/services", response_model=MasterServiceResponse,
             status_code=status.HTTP_201_CREATED)
def add_master_service(master_id: UUID, data: MasterServiceCreate,
                       db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Добавить услугу мастеру. Только для администратора."""
    return MasterService(db).add_service(master_id, data.service_id, data.price_override)


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


@router.post("/{master_id}/schedule", response_model=ScheduleResponse)
def set_schedule(master_id: UUID, data: ScheduleCreate,
                 db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_master)):
    """Задать расписание на день (upsert: существующий день перезаписывается,
    поэтому 200, а не 201). Сам мастер или администратор."""
    _ensure_owner_or_admin(master_id, current_user, db)
    return MasterService(db).set_schedule(master_id, data)


@router.patch("/{master_id}/schedule/{day_of_week}", response_model=ScheduleResponse)
def update_schedule(master_id: UUID,
                    day_of_week: Annotated[int, Path(ge=0, le=6, description="0=пн … 6=вс")],
                    data: ScheduleUpdate,
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_master)):
    """Обновить расписание на конкретный день (0=пн … 6=вс). Сам мастер или администратор."""
    _ensure_owner_or_admin(master_id, current_user, db)
    return MasterService(db).update_schedule(master_id, day_of_week, data)


# ── Свободные слоты ──────────────────────────────────────────────

@router.get("/{master_id}/slots", response_model=SlotListResponse)
def get_slots(master_id: UUID, service_id: UUID, target_date: date,
              exclude_appointment_id: UUID | None = None,
              db: Session = Depends(get_db)):
    """
    Свободные временные слоты мастера на дату.
    Публичный эндпоинт — используется на странице записи.

    exclude_appointment_id — для переноса записи мастером: свой же текущий
    слот не должен считаться занятым при выборе нового времени.

    Параметры запроса: ?service_id=...&target_date=2024-06-15
    """
    return AppointmentService(db).get_available_slots(
        master_id, target_date, service_id,
        exclude_appointment_id=exclude_appointment_id,
    )
