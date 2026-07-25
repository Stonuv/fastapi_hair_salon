from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..repositories.salon_repository import SalonRepository
from ..schemas.salon import SalonCreate, SalonResponse, SalonUpdate
from ..utils.slug import generate_unique_slug


class SalonService:
    def __init__(self, db: Session):
        self.salon_repo = SalonRepository(db)

    def list_all(self, *, is_active: bool | None = None) -> list[SalonResponse]:
        salons = self.salon_repo.list_all(is_active=is_active)
        return [SalonResponse.model_validate(s) for s in salons]

    def get_by_id(self, salon_id: UUID) -> SalonResponse:
        salon = self.salon_repo.get_by_id(salon_id)
        if not salon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Салон {salon_id} не найден")
        return SalonResponse.model_validate(salon)

    def create(self, data: SalonCreate) -> SalonResponse:
        salon = self.salon_repo.create(data, self._slug_for(data.name))
        return SalonResponse.model_validate(salon)

    def ensure_primary(self, data: SalonCreate) -> SalonResponse:
        """Первая точка сети при первичной настройке (/api/setup).

        Миграция 0013 всегда оставляет ровно одну строку-заглушку («Салон №1»
        с адресом «Адрес не указан»), поэтому здесь её нужно ЗАПОЛНИТЬ
        реальными данными, а не создавать вторую точку рядом — иначе свежая
        инсталляция стартовала бы с двумя салонами, один из которых мусорный.
        create() — только на случай БД без этой заглушки."""
        existing = self.salon_repo.get_first()
        if existing is None:
            return self.create(data)
        slug = self._slug_for(data.name, exclude_id=existing.id)
        salon = self.salon_repo.replace_details(existing, data, slug)
        return SalonResponse.model_validate(salon)

    def _slug_for(self, name: str, *, exclude_id: UUID | None = None) -> str:
        """exclude_id — чтобы точка не считала коллизией собственный slug
        при переименовании (см. ensure_primary)."""
        def taken(candidate: str) -> bool:
            found = self.salon_repo.get_by_slug(candidate)
            return found is not None and found.id != exclude_id
        return generate_unique_slug(name, exists=taken)

    def update(self, salon_id: UUID, data: SalonUpdate) -> SalonResponse:
        salon = self.salon_repo.get_by_id(salon_id)
        if not salon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Салон {salon_id} не найден")
        # Pydantic проверяет пару open/close только когда переданы оба поля —
        # при частичном обновлении сверяем с текущими значениями (тот же
        # приём, что MasterService.update_schedule).
        new_open = data.open_time if data.open_time is not None else salon.open_time
        new_close = data.close_time if data.close_time is not None else salon.close_time
        if new_close <= new_open:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="close_time должен быть позже open_time")
        salon = self.salon_repo.update(salon, data)
        return SalonResponse.model_validate(salon)
