from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .service import ServiceResponse
from .user import UserPublicResponse, UserResponse

# ── Услуга мастера (с возможным price_override) ──────────────────


class MasterServiceResponse(BaseModel):
    """Услуга в контексте конкретного мастера — показывает итоговую цену."""

    model_config = ConfigDict(from_attributes=True)

    service:        ServiceResponse
    price_override: Annotated[float | None, Field(
        default=None, description="Индивидуальная цена мастера; None = базовая × коэффициент"
    )]
    final_price:    Annotated[float, Field(description="Итоговая цена для этого мастера")]


# ── Краткий профиль (для списков) ────────────────────────────────


class MasterBriefResponse(BaseModel):
    """Краткая карточка мастера — для каталога и списков."""

    model_config = ConfigDict(from_attributes=True)

    id:             UUID
    first_name:     str
    last_name:      str
    specialization: str | None
    photo_url:      str | None
    coefficient:    float


# ── Полный профиль (для страницы мастера) ────────────────────────


class MasterResponse(BaseModel):
    """Полный профиль мастера — для самого мастера и администратора
    (содержит контакты пользователя, наружу не отдаётся)."""

    model_config = ConfigDict(from_attributes=True)

    id:             UUID
    user:           UserResponse
    specialization: str | None
    photo_url:      str | None
    coefficient:    float
    is_active:      bool


class MasterPublicResponse(BaseModel):
    """Публичный профиль мастера — без email/телефона/роли пользователя."""

    model_config = ConfigDict(from_attributes=True)

    id:             UUID
    user:           UserPublicResponse
    specialization: str | None
    photo_url:      str | None
    coefficient:    float


# ── Обновление профиля мастера ───────────────────────────────────


class MasterUpdate(BaseModel):
    specialization: Annotated[str | None, Field(default=None, max_length=200)]
    photo_url:      Annotated[str | None, Field(default=None, max_length=500)]
    coefficient:    Annotated[float | None, Field(default=None, gt=0)]
    is_active:      Annotated[bool | None, Field(default=None)]
