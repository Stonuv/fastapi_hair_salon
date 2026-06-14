from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from ..database import get_db
from ..services.admin_service import AdminService
from ..services.auth_service import get_current_admin
from ..models.enums import UserRole
from ..schemas.user import UserResponse
from ..schemas.master import MasterResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ChangeRoleRequest(BaseModel):
    role: UserRole


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def change_user_role(
    user_id: UUID,
    data: ChangeRoleRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """
    Сменить роль пользователя.
    Только для администратора.
    """
    return AdminService(db).change_role(user_id, data.role)


@router.post("/users/{user_id}/master", response_model=MasterResponse,
             status_code=status.HTTP_201_CREATED)
def create_master_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """
    Создать профиль мастера для пользователя с ролью 'master'.
    Только для администратора.
    """
    return AdminService(db).create_master_profile(user_id)
