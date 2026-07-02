from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.enums import UserRole
from ..models.user import User
from ..schemas.pagination import PageParams, PageResponse
from ..schemas.service import ServiceCreate, ServiceResponse, ServiceUpdate
from ..services.auth_service import get_current_admin, get_current_user_optional
from ..services.service_service import ServiceService

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("", response_model=PageResponse[ServiceResponse])
def get_services(
    *,
    db: Session = Depends(get_db),
    page_params: Annotated[PageParams, Depends()],
    search: Annotated[str | None, Query(description="Поиск по названию")] = None,
    min_price: Annotated[float | None, Query(ge=0, description="Минимальная цена")] = None,
    max_price: Annotated[float | None, Query(ge=0, description="Максимальная цена")] = None,
    is_active: Annotated[bool | None, Query(description="Только активные/неактивные (фильтр доступен администратору)")] = None,
    sort_by: Annotated[Literal["name", "price", "duration_min"], Query()] = "name",
    sort_order: Annotated[Literal["asc", "desc"], Query()] = "asc",
    current_user: User | None = Depends(get_current_user_optional),
):
    """Каталог услуг — поиск + фильтр по цене + сортировка + пагинация (1.4).
    Публичный эндпоинт: снятые с публикации услуги видит только администратор."""
    if current_user is None or current_user.role != UserRole.admin:
        is_active = True
    return ServiceService(db).list_paginated(
        page=page_params.page, page_size=page_params.page_size,
        search=search, min_price=min_price, max_price=max_price, is_active=is_active,
        sort_by=sort_by, sort_order=sort_order,
    )


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: UUID, db: Session = Depends(get_db)):
    """Детали одной услуги."""
    return ServiceService(db).get_by_id(service_id)


@router.post("", response_model=ServiceResponse,
             status_code=status.HTTP_201_CREATED)
def create_service(data: ServiceCreate, db: Session = Depends(get_db),
                   _=Depends(get_current_admin)):
    """Создать услугу. Только для администратора."""
    return ServiceService(db).create(data)


@router.patch("/{service_id}", response_model=ServiceResponse)
def update_service(service_id: UUID, data: ServiceUpdate,
                   db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Обновить услугу. Только для администратора."""
    return ServiceService(db).update(service_id, data)
