from datetime import date as date_
from datetime import datetime, timezone
from io import BytesIO
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.enums import UserRole
from ..models.user import User
from ..repositories.master_repository import MasterRepository
from ..schemas.admin_stats import AdminStatsResponse
from ..schemas.master import MasterPhotoUpdate, MasterResponse, MasterUpdate
from ..schemas.pagination import PageParams, PageResponse
from ..schemas.report import ReportResponse
from ..schemas.service import ServiceResponse, ServiceUpdate
from ..schemas.user import AdminUserCreate, AdminUserUpdate, UserResponse
from ..services.admin_service import AdminService
from ..services.auth_service import get_current_admin
from ..services.report_service import ReportService
from ..services.service_service import ServiceService

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ChangeRoleRequest(BaseModel):
    role: UserRole


class BlockRequest(BaseModel):
    is_blocked: bool


def _resolve_report_period(date_from: date_ | None,
                           date_to: date_ | None) -> tuple[date_, date_]:
    """Дефолтный период отчёта — с начала текущего месяца по сегодня.
    Сутки в отчётах режутся по UTC (см. report_repository), поэтому и
    «сегодня» берётся по UTC."""
    today = datetime.now(timezone.utc).date()
    effective_from = date_from or today.replace(day=1)
    effective_to = date_to or today
    if effective_from > effective_to:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="date_from не может быть позже date_to")
    return effective_from, effective_to


# ── Статистика / дашборд ──────────────────────────────────────────

@router.get("/stats", response_model=AdminStatsResponse)
def get_stats(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Счётчики и график регистраций для главной страницы админ-панели (4.4)."""
    return AdminService(db).get_stats()


# ── Отчёты ───────────────────────────────────────────────────────

@router.get("/reports", response_model=ReportResponse)
def get_report(
    date_from: Annotated[date_ | None, Query(description="Начало периода (YYYY-MM-DD)")] = None,
    date_to: Annotated[date_ | None, Query(description="Конец периода (YYYY-MM-DD)")] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Аналитический отчёт за произвольный период."""
    effective_from, effective_to = _resolve_report_period(date_from, date_to)
    return ReportService(db).get_report(effective_from, effective_to)


@router.get("/reports/export")
def export_report(
    date_from: Annotated[date_ | None, Query(description="Начало периода (YYYY-MM-DD)")] = None,
    date_to: Annotated[date_ | None, Query(description="Конец периода (YYYY-MM-DD)")] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin),
):
    """Скачать отчёт в формате Excel (.xlsx)."""
    effective_from, effective_to = _resolve_report_period(date_from, date_to)
    data = ReportService(db).export_excel(effective_from, effective_to)
    filename = f"report_{effective_from}_{effective_to}.xlsx"
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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


@router.patch("/users/{user_id}/block", response_model=UserResponse)
def set_user_blocked(user_id: UUID, data: BlockRequest,
                     db: Session = Depends(get_db),
                     current_admin: User = Depends(get_current_admin)):
    """Заблокировать / разблокировать пользователя (ТЗ 4.2): аккаунт и история
    сохраняются, но вход и действия по токену запрещены."""
    return AdminService(db).set_blocked(user_id, data.is_blocked, current_admin.id)


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
    return ServiceService(db).update(service_id, data)


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: UUID,
                   db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Мягко удалить услугу — скрывается из каталога, история записей сохраняется."""
    AdminService(db).delete_service(service_id)


# ── Мастера ──────────────────────────────────────────────────────

@router.patch("/masters/{master_id}/photo", response_model=MasterResponse)
def update_master_photo(master_id: UUID, data: MasterPhotoUpdate,
                        db: Session = Depends(get_db), _=Depends(get_current_admin)):
    """Обновить (или очистить — photo_url=null) фото мастера."""
    repo = MasterRepository(db)
    master = repo.get_by_id(master_id)
    if not master:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Мастер не найден")
    master = repo.update(master, MasterUpdate(photo_url=data.photo_url))
    return MasterResponse.model_validate(master)
