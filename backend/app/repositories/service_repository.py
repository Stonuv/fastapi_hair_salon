from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ..models.service import Service
from ..schemas.service import ServiceCreate, ServiceUpdate


class ServiceRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, service_id: UUID) -> Optional[Service]:
        return self.db.query(Service).filter(Service.id == service_id).first()

    def get_all_active(self) -> list[Service]:
        return (
            self.db.query(Service)
            .filter(Service.is_active == True)
            .all()
        )

    def get_all(self) -> list[Service]:
        """Для админа — все услуги включая неактивные."""
        return self.db.query(Service).all()

    # ── Создание ─────────────────────────────────────────────────

    def create(self, data: ServiceCreate) -> Service:
        service = Service(**data.model_dump())
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        return service

    # ── Обновление ───────────────────────────────────────────────

    def update(self, service: Service, data: ServiceUpdate) -> Service:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(service, field, value)
        self.db.commit()
        self.db.refresh(service)
        return service
