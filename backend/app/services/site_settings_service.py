from sqlalchemy.orm import Session

from ..repositories.site_settings_repository import SiteSettingsRepository
from ..schemas.site_settings import SiteSettingsResponse, SiteSettingsUpdate


class SiteSettingsService:
    def __init__(self, db: Session):
        self.repo = SiteSettingsRepository(db)

    def get(self) -> SiteSettingsResponse:
        settings = self.repo.get() or self.repo.create()
        return SiteSettingsResponse.model_validate(settings)

    def update(self, data: SiteSettingsUpdate) -> SiteSettingsResponse:
        settings = self.repo.get() or self.repo.create()
        settings = self.repo.update(settings, data.hero_photo_url)
        return SiteSettingsResponse.model_validate(settings)
