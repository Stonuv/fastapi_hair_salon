from datetime import datetime, time
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .fields import PhoneStr

# ── Базовые поля ─────────────────────────────────────────────────


class SalonBase(BaseModel):
    name:       Annotated[str, Field(min_length=1, max_length=150, description="Название точки")]
    address:    Annotated[str, Field(min_length=1, max_length=300, description="Адрес")]
    phone:      Annotated[PhoneStr | None, Field(default=None, description="Телефон точки")]
    open_time:  Annotated[time, Field(description="Открытие")]
    close_time: Annotated[time, Field(description="Закрытие")]
    photo_url:  Annotated[str | None, Field(default=None, max_length=500)]


# ── Создание / обновление ────────────────────────────────────────
# slug сюда не входит — генерируется сервером из name (см. utils/slug.py),
# не редактируется вручную в v1 (ROADMAP.md §4.2).


class SalonCreate(SalonBase):
    @model_validator(mode="after")
    def close_after_open(self) -> "SalonCreate":
        if self.close_time <= self.open_time:
            raise ValueError("close_time должен быть позже open_time")
        return self


class SalonUpdate(BaseModel):
    name:       Annotated[str | None, Field(default=None, min_length=1, max_length=150)]
    address:    Annotated[str | None, Field(default=None, min_length=1, max_length=300)]
    phone:      Annotated[PhoneStr | None, Field(default=None)]
    open_time:  Annotated[time | None, Field(default=None)]
    close_time: Annotated[time | None, Field(default=None)]
    photo_url:  Annotated[str | None, Field(default=None, max_length=500)]
    is_active:  Annotated[bool | None, Field(default=None, description="Закрыть/открыть точку")]

    @model_validator(mode="after")
    def close_after_open(self) -> "SalonUpdate":
        # Как в ScheduleUpdate: пара валидируется тут только когда переданы
        # оба поля сразу — частичное обновление сверяет с текущим значением
        # в SalonService (иначе некорректная пара дошла бы до CHECK в БД и
        # дала бы 500 вместо понятной 400).
        if (self.open_time is not None and self.close_time is not None
                and self.close_time <= self.open_time):
            raise ValueError("close_time должен быть позже open_time")
        return self


# ── Ответ API ────────────────────────────────────────────────────


class SalonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         UUID
    name:       str
    slug:       str
    address:    str
    phone:      str | None
    open_time:  time
    close_time: time
    photo_url:  str | None
    is_active:  bool
    created_at: datetime


class SalonBriefResponse(BaseModel):
    """Для встраивания в другие ответы (UserResponse.salon, MasterResponse.salon)."""

    model_config = ConfigDict(from_attributes=True)

    id:   UUID
    name: str
    slug: str
