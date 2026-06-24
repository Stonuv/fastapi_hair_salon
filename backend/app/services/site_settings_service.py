from sqlalchemy.orm import Session

from ..repositories.site_settings_repository import SiteSettingsRepository
from ..schemas.site_settings import SiteContent


class SiteSettingsService:
    def __init__(self, db: Session):
        self.repo = SiteSettingsRepository(db)

    def get(self) -> SiteContent:
        settings = self.repo.get() or self.repo.create()
        return SiteContent.model_validate(settings.content)

    def update(self, data: SiteContent) -> SiteContent:
        settings = self.repo.get() or self.repo.create()
        settings = self.repo.update(settings, data.model_dump(mode="json"))
        return SiteContent.model_validate(settings.content)
