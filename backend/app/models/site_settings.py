from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base
from .mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SiteSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Глобальные настройки/контент сайта — singleton, всегда ровно одна
    строка (создаётся лениво в SiteSettingsService при первом обращении).
    `content` хранит весь редактируемый текст сайта (см. schemas/site_settings.py
    SiteContent) — JSONB, а не отдельные колонки, чтобы новые редактируемые
    поля не требовали миграции на каждое изменение."""

    __tablename__ = "site_settings"

    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
