from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

from .user import UserResponse
from .service import ServiceResponse


# ── Услуга мастера (с возможным price_override) ──────────────────

class MasterServiceResponse(BaseModel):
    """Услуга в контексте конкретного мастера — показывает итоговую цену."""
    service:        ServiceResponse
    price_override: Optional[float] = Field(
        None, description="Индивидуальная цена мастера; None = базовая × коэффициент"
    )
    final_price:    float = Field(..., description="Итоговая цена для этого мастера")

    model_config = {"from_attributes": True}


# ── Краткий профиль (для списков) ────────────────────────────────

class MasterBriefResponse(BaseModel):
    """Краткая карточка мастера — для каталога и списков."""
    id:             UUID
    first_name:     str
    last_name:      str
    specialization: Optional[str]
    photo_url:      Optional[str]
    coefficient:    float

    model_config = {"from_attributes": True}


# ── Полный профиль (для страницы мастера) ────────────────────────

class MasterResponse(BaseModel):
    """Полный профиль мастера с услугами."""
    id:             UUID
    user:           UserResponse
    specialization: Optional[str]
    photo_url:      Optional[str]
    coefficient:    float
    is_active:      bool

    model_config = {"from_attributes": True}


# ── Обновление профиля мастера ───────────────────────────────────

class MasterUpdate(BaseModel):
    specialization: Optional[str]   = Field(None, max_length=200)
    photo_url:      Optional[str]   = Field(None, max_length=500)
    coefficient:    Optional[float] = Field(None, gt=0)
    is_active:      Optional[bool]  = None


# ── Список мастеров ──────────────────────────────────────────────

class MasterListResponse(BaseModel):
    masters: list[MasterBriefResponse]
    total:   int
