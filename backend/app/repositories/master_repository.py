import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..models.master import Master, MasterService
from ..models.user import User
from ..schemas.master import MasterUpdate
from ._query_utils import paginated


class MasterRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, master_id: uuid.UUID, *, include_deleted: bool = False) -> Optional[Master]:
        """Загружает мастера вместе с профилем пользователя."""
        stmt = select(Master).options(joinedload(Master.user)).where(Master.id == master_id)
        if not include_deleted:
            stmt = stmt.where(Master.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Master]:
        stmt = (
            select(Master)
            .options(joinedload(Master.user))
            .where(Master.user_id == user_id, Master.deleted_at.is_(None))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        specialization: str | None = None,
        service_id: uuid.UUID | None = None,
        sort_by: Literal["name", "coefficient"] = "name",
        sort_order: Literal["asc", "desc"] = "asc",
    ) -> tuple[list[Master], int]:
        """Каталог активных мастеров — фильтр по специализации и/или оказываемой услуге."""
        stmt = (
            select(Master)
            .join(Master.user)
            .options(joinedload(Master.user))
            .where(Master.deleted_at.is_(None), Master.is_active.is_(True))
        )
        if specialization:
            stmt = stmt.where(Master.specialization.ilike(f"%{specialization}%"))
        if service_id is not None:
            stmt = stmt.join(Master.services).where(MasterService.service_id == service_id)

        sort_column = User.last_name if sort_by == "name" else Master.coefficient
        order = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        stmt = stmt.order_by(order)

        return paginated(self.db, stmt, page=page, page_size=page_size)

    def get_with_services(self, master_id: uuid.UUID) -> Optional[Master]:
        """Загружает мастера вместе с его услугами и базовыми ценами."""
        stmt = (
            select(Master)
            .options(
                joinedload(Master.user),
                joinedload(Master.services).joinedload(MasterService.service),
            )
            .where(Master.id == master_id, Master.deleted_at.is_(None))
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    # ── Создание ─────────────────────────────────────────────────

    def create(self, user_id: uuid.UUID) -> Master:
        """Создаёт профиль мастера для существующего пользователя."""
        master = Master(user_id=user_id)
        self.db.add(master)
        self.db.commit()
        self.db.refresh(master)
        return master

    # ── Обновление ───────────────────────────────────────────────

    def update(self, master: Master, data: MasterUpdate) -> Master:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(master, field, value)
        self.db.commit()
        self.db.refresh(master)
        return master

    def deactivate(self, master: Master) -> None:
        """Скрывает мастера из каталога без мягкого удаления (например, при смене роли)."""
        master.is_active = False
        self.db.commit()

    def soft_delete(self, master: Master) -> None:
        master.deleted_at = datetime.now(timezone.utc)
        master.is_active = False
        self.db.commit()

    # ── Услуги мастера ───────────────────────────────────────────

    def add_service(self, master_id: uuid.UUID, service_id: uuid.UUID,
                    price_override: float | None = None) -> MasterService:
        ms = MasterService(
            master_id=master_id,
            service_id=service_id,
            price_override=price_override,
        )
        self.db.add(ms)
        self.db.commit()
        self.db.refresh(ms)
        return ms

    def remove_service(self, master_id: uuid.UUID, service_id: uuid.UUID) -> bool:
        ms = self.get_master_service(master_id, service_id)
        if not ms:
            return False
        self.db.delete(ms)
        self.db.commit()
        return True

    def get_master_service(self, master_id: uuid.UUID,
                           service_id: uuid.UUID) -> Optional[MasterService]:
        stmt = select(MasterService).where(
            MasterService.master_id == master_id,
            MasterService.service_id == service_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()
