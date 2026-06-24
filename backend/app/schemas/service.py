from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .fields import PositiveMoney

# ── Базовые поля ─────────────────────────────────────────────────


class ServiceBase(BaseModel):
    name:         Annotated[str, Field(min_length=2, max_length=200, description="Название услуги")]
    description:  Annotated[str | None, Field(default=None, description="Описание")]
    price:        Annotated[PositiveMoney, Field(description="Базовая цена (> 0)")]
    duration_min: Annotated[int, Field(gt=0, description="Длительность в минутах")]


# ── Создание / обновление ────────────────────────────────────────


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name:         Annotated[str | None, Field(default=None, min_length=2, max_length=200)]
    description:  Annotated[str | None, Field(default=None)]
    price:        Annotated[float | None, Field(default=None, gt=0)]
    duration_min: Annotated[int | None, Field(default=None, gt=0)]
    is_active:    Annotated[bool | None, Field(default=None)]


# ── Ответ API ────────────────────────────────────────────────────


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           UUID
    name:         str
    description:  str | None
    price:        float
    duration_min: int
    is_active:    bool
