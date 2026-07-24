import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..models.master import Master, MasterService
from ..models.service import Service
from ..models.user import User
from ..schemas.master import MasterUpdate
from ._query_utils import LIKE_ESCAPE_CHAR, escape_like, paginated


class MasterRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, master_id: uuid.UUID, *, include_deleted: bool = False) -> Master | None:
        """Загружает мастера вместе с профилем пользователя."""
        stmt = select(Master).options(joinedload(Master.user)).where(Master.id == master_id)
        if not include_deleted:
            stmt = stmt.where(Master.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_user_id(self, user_id: uuid.UUID) -> Master | None:
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
        sort_by: Literal["name", "price"] = "name",
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
            stmt = stmt.where(Master.specialization.ilike(
                f"%{escape_like(specialization)}%", escape=LIKE_ESCAPE_CHAR
            ))
        if service_id is not None:
            stmt = (stmt.join(Master.services).join(MasterService.service)
                        .where(MasterService.service_id == service_id))

        if sort_by == "name":
            sort_column = User.last_name
        elif service_id is not None:
            # Услуга выбрана — точная итоговая цена для неё: override, если
            # задан, иначе base_price * coefficient (см. _final_price в
            # services/master_service.py — та же формула).
            sort_column = func.coalesce(MasterService.price_override, Service.price * Master.coefficient)
        else:
            # Без выбранной услуги единой цены не существует (у мастера может
            # быть много услуг по разным ценам) — coefficient как приближение
            # общего уровня цен; наружу термин "коэффициент" не выставляется,
            # только "цена" (см. sort_by в routes/masters.py).
            sort_column = Master.coefficient
        order = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        stmt = stmt.order_by(order)

        return paginated(self.db, stmt, page=page, page_size=page_size)

    def get_with_services(self, master_id: uuid.UUID) -> Master | None:
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
        self.db.flush()
        self.db.refresh(master)
        return master

    # ── Обновление ───────────────────────────────────────────────

    def update(self, master: Master, data: MasterUpdate) -> Master:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(master, field, value)
        self.db.flush()
        self.db.refresh(master)
        return master

    def deactivate(self, master: Master) -> None:
        """Скрывает мастера из каталога без мягкого удаления (например, при смене роли)."""
        master.is_active = False
        self.db.flush()

    def reactivate(self, master: Master) -> Master:
        """Обратное к deactivate() — при повторном назначении роли master тому
        же пользователю восстанавливает его старый профиль (специализация,
        коэффициент, услуги, история отзывов) вместо создания нового."""
        master.is_active = True
        self.db.flush()
        self.db.refresh(master)
        return master

    def soft_delete(self, master: Master) -> None:
        master.deleted_at = datetime.now(timezone.utc)
        master.is_active = False
        self.db.flush()

    # ── Услуги мастера ───────────────────────────────────────────

    def add_service(self, master_id: uuid.UUID, service_id: uuid.UUID,
                    price_override: Decimal | None = None) -> MasterService:
        ms = MasterService(
            master_id=master_id,
            service_id=service_id,
            price_override=price_override,
        )
        self.db.add(ms)
        self.db.flush()
        self.db.refresh(ms)
        return ms

    def remove_service(self, master_id: uuid.UUID, service_id: uuid.UUID) -> bool:
        ms = self.get_master_service(master_id, service_id)
        if not ms:
            return False
        self.db.delete(ms)
        self.db.flush()
        return True

    def get_master_service(self, master_id: uuid.UUID,
                           service_id: uuid.UUID) -> MasterService | None:
        stmt = select(MasterService).where(
            MasterService.master_id == master_id,
            MasterService.service_id == service_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()
