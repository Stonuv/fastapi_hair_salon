import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.salon import Salon
from ..schemas.salon import SalonCreate, SalonUpdate


class SalonRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_id(self, salon_id: uuid.UUID) -> Salon | None:
        stmt = select(Salon).where(Salon.id == salon_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> Salon | None:
        stmt = select(Salon).where(Salon.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_first(self) -> Salon | None:
        """Старейшая точка сети — временный дефолт там, где salon_id ещё
        не выбирается явно вызывающей стороной (AdminService.create_master_profile,
        Фаза A ROADMAP.md §4.10 — Фаза B заменит его обязательным параметром)."""
        stmt = select(Salon).order_by(Salon.created_at).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self, *, is_active: bool | None = None) -> list[Salon]:
        """Без пагинации — намеренно, у сети физически десятки точек
        максимум (ROADMAP.md §4.8)."""
        stmt = select(Salon).order_by(Salon.name)
        if is_active is not None:
            stmt = stmt.where(Salon.is_active.is_(is_active))
        return list(self.db.execute(stmt).scalars().all())

    # ── Создание / обновление ───────────────────────────────────────

    def create(self, data: SalonCreate, slug: str) -> Salon:
        salon = Salon(**data.model_dump(), slug=slug)
        self.db.add(salon)
        self.db.flush()
        self.db.refresh(salon)
        return salon

    def update(self, salon: Salon, data: SalonUpdate) -> Salon:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(salon, field, value)
        self.db.flush()
        self.db.refresh(salon)
        return salon
