from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.site_settings import SiteSettings


class SiteSettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self) -> SiteSettings | None:
        return self.db.execute(select(SiteSettings)).scalars().first()

    def create(self) -> SiteSettings:
        settings = SiteSettings()
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def update(self, settings: SiteSettings, hero_photo_url: str | None) -> SiteSettings:
        settings.hero_photo_url = hero_photo_url
        self.db.commit()
        self.db.refresh(settings)
        return settings
