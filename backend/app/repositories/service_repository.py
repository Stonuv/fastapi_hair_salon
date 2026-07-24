import uuid
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.service import Service
from ..schemas.service import ServiceCreate, ServiceUpdate
from ._query_utils import LIKE_ESCAPE_CHAR, escape_like, paginated


class ServiceRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, service_id: uuid.UUID, *, include_deleted: bool = False) -> Service | None:
        stmt = select(Service).where(Service.id == service_id)
        if not include_deleted:
            stmt = stmt.where(Service.deleted_at.is_(None))
        return self.db.execute(stmt).scalar_one_or_none()

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        is_active: bool | None = None,
        sort_by: Literal["name", "price", "duration_min"] = "name",
        sort_order: Literal["asc", "desc"] = "asc",
    ) -> tuple[list[Service], int]:
        """Каталог услуг — поиск по названию + фильтр по цене/активности (1.4)."""
        stmt = select(Service).where(Service.deleted_at.is_(None))
        if search:
            stmt = stmt.where(Service.name.ilike(
                f"%{escape_like(search)}%", escape=LIKE_ESCAPE_CHAR
            ))
        if min_price is not None:
            stmt = stmt.where(Service.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Service.price <= max_price)
        if is_active is not None:
            stmt = stmt.where(Service.is_active.is_(is_active))

        sort_column = {"name": Service.name, "price": Service.price,
                      "duration_min": Service.duration_min}[sort_by]
        order = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        stmt = stmt.order_by(order)

        return paginated(self.db, stmt, page=page, page_size=page_size)

    # ── Создание ─────────────────────────────────────────────────

    def create(self, data: ServiceCreate) -> Service:
        service = Service(**data.model_dump())
        self.db.add(service)
        self.db.flush()
        self.db.refresh(service)
        return service

    # ── Обновление ───────────────────────────────────────────────

    def update(self, service: Service, data: ServiceUpdate) -> Service:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(service, field, value)
        self.db.flush()
        self.db.refresh(service)
        return service

    def soft_delete(self, service: Service) -> None:
        service.deleted_at = datetime.now(timezone.utc)
        service.is_active = False
        self.db.flush()
