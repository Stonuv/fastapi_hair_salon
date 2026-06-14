from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from ..database import get_db
from ..services.appointment_service import AppointmentService
from ..services.auth_service import (get_current_user, get_current_client,
                                      get_current_master, get_current_admin)
from ..models.user import User
from ..schemas.appointment import (AppointmentCreate, AppointmentResponse,
                                    AppointmentListResponse)

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


@router.get("/my", response_model=AppointmentListResponse)
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
):
    """Мои записи (личный кабинет клиента)."""
    return AppointmentService(db).get_my_appointments(current_user.id)


@router.get("/master/{master_id}", response_model=AppointmentListResponse)
def get_master_appointments(
    master_id: UUID,
    date_from: datetime | None = None,
    date_to:   datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_master),
):
    """
    Записи конкретного мастера.
    Доступно мастерам и администраторам.
    Параметры: ?date_from=2024-06-01T00:00:00&date_to=2024-06-30T23:59:59
    """
    return AppointmentService(db).get_master_appointments(
        master_id, date_from, date_to
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Детали записи. Доступно клиенту-владельцу, мастеру и администратору."""
    return AppointmentService(db).get_by_id(appointment_id, current_user.id)


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_client),
):
    """Отменить запись. Только владелец записи."""
    return AppointmentService(db).cancel(appointment_id, current_user.id)
