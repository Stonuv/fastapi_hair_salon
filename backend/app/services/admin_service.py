from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.enums import UserRole
from ..repositories.master_repository import MasterRepository
from ..repositories.service_repository import ServiceRepository
from ..repositories.stats_repository import StatsRepository
from ..repositories.user_repository import UserRepository
from ..schemas.admin_stats import AdminStatsResponse, DailyCount
from ..schemas.master import MasterResponse
from ..schemas.pagination import PageResponse
from ..schemas.user import UserResponse


class AdminService:
    def __init__(self, db: Session):
        self.user_repo    = UserRepository(db)
        self.master_repo  = MasterRepository(db)
        self.service_repo = ServiceRepository(db)
        self.stats_repo   = StatsRepository(db)

    # ── Пользователи ─────────────────────────────────────────────

    def list_users(self, *, page: int, page_size: int,
                   role: UserRole | None = None,
                   search: str | None = None,
                   sort_by: Literal["created_at", "email"] = "created_at",
                   sort_order: Literal["asc", "desc"] = "desc",
                   ) -> PageResponse[UserResponse]:
        users, total = self.user_repo.list_paginated(
            page=page, page_size=page_size, role=role, search=search,
            sort_by=sort_by, sort_order=sort_order,
        )
        return PageResponse[UserResponse](
            items=[UserResponse.model_validate(u) for u in users],
            total=total, page=page, page_size=page_size,
        )

    def change_role(self, user_id: UUID, role: UserRole) -> UserResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Пользователь не найден")
        user = self.user_repo.set_role(user, role)
        if role != UserRole.master:
            master = self.master_repo.get_by_user_id(user_id)
            if master:
                self.master_repo.deactivate(master)
        return UserResponse.model_validate(user)

    def create_master_profile(self, user_id: UUID) -> MasterResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Пользователь не найден")
        if user.role != UserRole.master:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Сначала назначьте пользователю роль 'master'")
        if self.master_repo.get_by_user_id(user_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Профиль мастера уже существует")
        master = self.master_repo.create(user_id)
        master = self.master_repo.get_by_id(master.id)
        return MasterResponse.model_validate(master)

    def delete_user(self, user_id: UUID) -> None:
        """Мягкое удаление — пользователь скрывается, но история записей сохраняется."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Пользователь не найден")
        master = self.master_repo.get_by_user_id(user_id)
        if master:
            self.master_repo.soft_delete(master)
        self.user_repo.soft_delete(user)

    # ── Услуги ───────────────────────────────────────────────────

    def delete_service(self, service_id: UUID) -> None:
        """Мягкое удаление — услуга скрывается, но остаётся доступна
        для уже существующих записей (FK ondelete=RESTRICT)."""
        service = self.service_repo.get_by_id(service_id)
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Услуга не найдена")
        self.service_repo.soft_delete(service)

    # ── Статистика / дашборд (4.4) ────────────────────────────────

    def get_stats(self) -> AdminStatsResponse:
        by_role = self.stats_repo.count_users_by_role()
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = now - timedelta(days=30)

        appointments_count, revenue = self.stats_repo.appointments_and_revenue_since(month_start)
        registrations = self.stats_repo.daily_registrations(thirty_days_ago)

        return AdminStatsResponse(
            total_users=sum(by_role.values()),
            total_clients=by_role.get(UserRole.client, 0),
            total_masters=self.stats_repo.count_active_masters(),
            total_services=self.stats_repo.count_active_services(),
            appointments_this_month=appointments_count,
            revenue_this_month=float(revenue),
            registrations_last_30_days=[
                DailyCount(date=day, count=count) for day, count in registrations
            ],
        )
