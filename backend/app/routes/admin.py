from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from ..database import get_db
from ..services.admin_service import AdminService
from ..services.auth_service import get_current_admin
from ..models.enums import UserRole
from ..schemas.user import UserResponse
from ..schemas.master import MasterResponse
from ..schemas.service import ServiceUpdate, ServiceResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ChangeRoleRequest(BaseModel):
    role: UserRole


# ── Пользователи ─────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Список всех пользователей."""
    users = AdminService(db).get_all_users()
    return [UserResponse.model_validate(u) for u in users]


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def change_user_role(user_id: UUID, data: ChangeRoleRequest,
                     db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Сменить роль пользователя."""
    return AdminService(db).change_role(user_id, data.role)


@router.post("/users/{user_id}/master", response_model=MasterResponse,
             status_code=status.HTTP_201_CREATED)
def create_master_profile(user_id: UUID,
                          db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Создать профиль мастера."""
    return AdminService(db).create_master_profile(user_id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID,
                db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Удалить пользователя."""
    AdminService(db).delete_user(user_id)


# ── Услуги ───────────────────────────────────────────────────────

@router.patch("/services/{service_id}", response_model=ServiceResponse)
def update_service(service_id: UUID, data: ServiceUpdate,
                   db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Обновить услугу."""
    from ..services.service_service import ServiceService
    return ServiceService(db).update(service_id, data)


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: UUID,
                   db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Удалить услугу."""
    AdminService(db).delete_service(service_id)


# ── Мастера ──────────────────────────────────────────────────────

@router.patch("/masters/{master_id}/photo")
def update_master_photo(master_id: UUID, photo_url: str,
                        db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Обновить фото мастера."""
    from ..repositories.master_repository import MasterRepository
    from ..schemas.master import MasterUpdate
    master = MasterRepository(db).get_by_id(master_id)
    if not master:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Мастер не найден")
    master = MasterRepository(db).update(master, MasterUpdate(photo_url=photo_url))
    return {"photo_url": master.photo_url}
