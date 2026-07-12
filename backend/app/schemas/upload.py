from typing import Annotated

from pydantic import BaseModel, Field


class ImageUploadResponse(BaseModel):
    url: Annotated[str, Field(description="URL сохранённого изображения (для photo_url/hero и т.п.)")]
