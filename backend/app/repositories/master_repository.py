from sqlalchemy.orm import Session, joinedload
from typing import Optional
from uuid import UUID

from ..models.master import Master, MasterService
from ..schemas.master import MasterUpdate


class MasterRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, master_id: UUID) -> Optional[Master]:
        """Загружает мастера вместе с профилем пользователя."""
        return (
            self.db.query(Master)
            .options(joinedload(Master.user))
            .filter(Master.id == master_id)
            .first()
        )

    def get_by_user_id(self, user_id: UUID) -> Optional[Master]:
        return (
            self.db.query(Master)
            .options(joinedload(Master.user))
            .filter(Master.user_id == user_id)
            .first()
        )

    def get_all_active(self) -> list[Master]:
        """Список активных мастеров для каталога."""
        return (
            self.db.query(Master)
            .options(joinedload(Master.user))
            .filter(Master.is_active == True)
            .all()
        )

    def get_with_services(self, master_id: UUID) -> Optional[Master]:
        """Загружает мастера вместе с его услугами и базовыми ценами."""
        return (
            self.db.query(Master)
            .options(
                joinedload(Master.user),
                joinedload(Master.services).joinedload(MasterService.service),
            )
            .filter(Master.id == master_id)
            .first()
        )

    # ── Создание ─────────────────────────────────────────────────

    def create(self, user_id: UUID) -> Master:
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

    # ── Услуги мастера ───────────────────────────────────────────

    def add_service(self, master_id: UUID, service_id: UUID,
                    price_override: float | None = None) -> MasterService:
        ms = MasterService(
            master_id      = master_id,
            service_id     = service_id,
            price_override = price_override,
        )
        self.db.add(ms)
        self.db.commit()
        self.db.refresh(ms)
        return ms

    def remove_service(self, master_id: UUID, service_id: UUID) -> bool:
        ms = (
            self.db.query(MasterService)
            .filter(
                MasterService.master_id  == master_id,
                MasterService.service_id == service_id,
            )
            .first()
        )
        if not ms:
            return False
        self.db.delete(ms)
        self.db.commit()
        return True

    def get_master_service(self, master_id: UUID,
                           service_id: UUID) -> Optional[MasterService]:
        return (
            self.db.query(MasterService)
            .filter(
                MasterService.master_id  == master_id,
                MasterService.service_id == service_id,
            )
            .first()
        )
