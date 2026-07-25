from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.enums import UserRole
from ..models.user import User
from ..schemas.salon import SalonCreate, SalonResponse, SalonUpdate
from ..services.auth_service import (get_current_admin, get_current_owner,
                                     get_current_user_optional)
from ..services.salon_service import SalonService

router = APIRouter(prefix="/api/salons", tags=["salons"])


def _ensure_can_manage_salon(salon_id: UUID, data: SalonUpdate, current_user: User) -> None:
    """Владелец сети может редактировать любую точку целиком. Admin — только
    свою (домашний salon_id), и не может закрыть/открыть её — is_active
    касается сети в целом, не решение отдельной точки."""
    if current_user.role == UserRole.owner:
        return
    if current_user.salon_id != salon_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Доступ только к своей точке")
    if data.is_active is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Закрыть/открыть точку может только владелец сети")


@router.get("", response_model=list[SalonResponse])
def get_salons(
    *,
    db: Session = Depends(get_db),
    is_active: Annotated[bool | None, Query(
        description="Фильтр по активности (полноценно доступен только администратору/владельцу)"
    )] = None,
    current_user: User | None = Depends(get_current_user_optional),
):
    """Список точек сети — без пагинации, у сети физически десятки точек
    максимум. Публичный эндпоинт: закрытые точки видит только admin/owner."""
    if current_user is None or current_user.role not in (UserRole.admin, UserRole.owner):
        is_active = True
    return SalonService(db).list_all(is_active=is_active)


@router.get("/{salon_id}", response_model=SalonResponse)
def get_salon(salon_id: UUID, db: Session = Depends(get_db)):
    """Детали одной точки. Публичный эндпоинт."""
    return SalonService(db).get_by_id(salon_id)


@router.post("", response_model=SalonResponse, status_code=status.HTTP_201_CREATED)
def create_salon(data: SalonCreate, db: Session = Depends(get_db),
                 _=Depends(get_current_owner)):
    """Онбординг новой точки сети. Только владелец сети — самостоятельно,
    без участия разработчика/оператора (ROADMAP.md §4, «Договорённости»)."""
    return SalonService(db).create(data)


@router.patch("/{salon_id}", response_model=SalonResponse)
def update_salon(salon_id: UUID, data: SalonUpdate,
                 db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_admin)):
    """Обновить точку. Владелец сети — любую; администратор — только свою
    (см. _ensure_can_manage_salon)."""
    _ensure_can_manage_salon(salon_id, data, current_user)
    return SalonService(db).update(salon_id, data)
