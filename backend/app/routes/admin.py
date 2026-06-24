from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.enums import UserRole
from ..repositories.master_repository import MasterRepository
from ..schemas.admin_stats import AdminStatsResponse
from ..schemas.master import MasterResponse, MasterUpdate
from ..schemas.pagination import PageParams, PageResponse
from ..schemas.service import ServiceResponse, ServiceUpdate
from ..schemas.user import AdminUserCreate, AdminUserUpdate, UserResponse
from ..services.admin_service import AdminService
from ..services.auth_service import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ChangeRoleRequest(BaseModel):
    role: UserRole


# ── Статистика / дашборд ──────────────────────────────────────────

@router.get("/stats", response_model=AdminStatsResponse)
def get_stats(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Счётчики и график регистраций для главной страницы админ-панели (4.4)."""
    return AdminService(db).get_stats()


# ── Пользователи ─────────────────────────────────────────────────

@router.get("/users", response_model=PageResponse[UserResponse])
def get_all_users(
    *,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
    page_params: Annotated[PageParams, Depends()],
    role: UserRole | None = None,
    search: Annotated[str | None, Query(description="Поиск по имени/фамилии/email")] = None,
    sort_by: Literal["created_at", "email"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
):
    """Список пользователей — фильтр по роли + поиск + пагинация (1.4)."""
    return AdminService(db).list_users(
        page=page_params.page, page_size=page_params.page_size,
        role=role, search=search, sort_by=sort_by, sort_order=sort_order,
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: AdminUserCreate,
                db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Создать пользователя. Роль задаётся сразу."""
    return AdminService(db).create_user(data)


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, data: AdminUserUpdate,
                db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Обновить данные пользователя (имя, email, телефон, пароль)."""
    return AdminService(db).update_user(user_id, data)


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
    """Мягко удалить пользователя — запись скрывается, история сохраняется."""
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
    """Мягко удалить услугу — скрывается из каталога, история записей сохраняется."""
    AdminService(db).delete_service(service_id)


# ── Мастера ──────────────────────────────────────────────────────

@router.patch("/masters/{master_id}/photo")
def update_master_photo(master_id: UUID, photo_url: str,
                        db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Обновить фото мастера."""
    master = MasterRepository(db).get_by_id(master_id)
    if not master:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Мастер не найден")
    master = MasterRepository(db).update(master, MasterUpdate(photo_url=photo_url))
    return {"photo_url": master.photo_url}
