from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from ..database import get_db
from ..services.service_service import ServiceService
from ..services.auth_service import get_current_admin
from ..schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse, ServiceListResponse

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("", response_model=ServiceListResponse)
def get_services(db: Session = Depends(get_db)):
    """Каталог активных услуг. Публичный эндпоинт."""
    return ServiceService(db).get_all()


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
