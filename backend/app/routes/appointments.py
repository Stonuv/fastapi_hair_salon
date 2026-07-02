from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.enums import AppointmentStatus
from ..models.user import User
from ..schemas.appointment import (AppointmentBriefResponse, AppointmentCreate,
                                   AppointmentResponse, AppointmentStatusUpdate)
from ..schemas.pagination import PageParams, PageResponse
from ..services.appointment_service import AppointmentService
from ..services.auth_service import (get_current_admin, get_current_client,
                                      get_current_master, get_current_user)

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentResponse,
             status_code=status.HTTP_201_CREATED)
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
):
    """
    Создать запись к мастеру.
    Доступно клиентам и администраторам.
    """
    return AppointmentService(db).create(current_user.id, data)


@router.get("/my", response_model=PageResponse[AppointmentBriefResponse])
def get_my_appointments(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
    page_params: Annotated[PageParams, Depends()],
    status_filter: AppointmentStatus | None = None,
):
    """Мои записи (личный кабинет клиента) — фильтр по статусу + пагинация."""
    return AppointmentService(db).list_for_client(
        current_user.id, page=page_params.page, page_size=page_params.page_size,
        status_filter=status_filter,
    )


@router.get("/master/{master_id}", response_model=PageResponse[AppointmentBriefResponse])
def get_master_appointments(
    master_id: UUID,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_master),
    page_params: Annotated[PageParams, Depends()],
    status_filter: AppointmentStatus | None = None,
    date_from: datetime | None = None,
    date_to:   datetime | None = None,
):
    """
    Записи конкретного мастера.
    Мастер видит только свои записи, администратор — любые.
    Параметры: ?date_from=2024-06-01T00:00:00&date_to=2024-06-30T23:59:59
    """
    return AppointmentService(db).list_for_master(
        master_id, current_user,
        page=page_params.page, page_size=page_params.page_size,
        status_filter=status_filter, date_from=date_from, date_to=date_to,
    )


@router.get("", response_model=PageResponse[AppointmentBriefResponse])
def get_all_appointments(
    *,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
    page_params: Annotated[PageParams, Depends()],
    client_id: UUID | None = None,
    master_id: UUID | None = None,
    status_filter: AppointmentStatus | None = None,
    date_from: datetime | None = None,
    date_to:   datetime | None = None,
):
    """Все записи системы — для администратора. Фильтр + пагинация (1.4)."""
    return AppointmentService(db).list_all(
        page=page_params.page, page_size=page_params.page_size,
        client_id=client_id, master_id=master_id, status_filter=status_filter,
        date_from=date_from, date_to=date_to,
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Детали записи. Доступно клиенту-владельцу, мастеру и администратору."""
    return AppointmentService(db).get_by_id(appointment_id, current_user)


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
):
    """Отменить запись. Только владелец записи."""
    return AppointmentService(db).cancel(appointment_id, current_user.id)


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: UUID,
    data: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_master),
):
    """
    Подтвердить / завершить / отменить запись со стороны мастера или администратора.
    Переход статуса проверяется машиной состояний (1.5): pending → confirmed → done,
    cancelled достижим из pending/confirmed, done/cancelled — терминальные.
    """
    return AppointmentService(db).update_status(appointment_id, data.status, current_user)
