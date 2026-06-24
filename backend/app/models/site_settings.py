from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SiteSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Глобальные настройки сайта — singleton, всегда ровно одна строка
    (создаётся лениво в SiteSettingsService при первом обращении)."""

    __tablename__ = "site_settings"

    hero_photo_url: Mapped[str | None] = mapped_column(String(2048), default=None)
