from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class SiteSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hero_photo_url: Annotated[str | None, Field(default=None, description="Фото в шапке главной страницы")]


class SiteSettingsUpdate(BaseModel):
    hero_photo_url: Annotated[str | None, Field(default=None, max_length=2048)]
