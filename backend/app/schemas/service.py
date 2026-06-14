from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


# ── Базовые поля ─────────────────────────────────────────────────

class ServiceBase(BaseModel):
    name:         str            = Field(..., min_length=2, max_length=200,
                                         description="Название услуги")
    description:  Optional[str] = Field(None, description="Описание")
    price:        float          = Field(..., gt=0, description="Базовая цена (> 0)")
    duration_min: int            = Field(..., gt=0, description="Длительность в минутах")


# ── Создание / обновление ────────────────────────────────────────

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name:         Optional[str]   = Field(None, min_length=2, max_length=200)
    description:  Optional[str]   = None
    price:        Optional[float] = Field(None, gt=0)
    duration_min: Optional[int]   = Field(None, gt=0)
    is_active:    Optional[bool]  = None


# ── Ответ API ────────────────────────────────────────────────────

class ServiceResponse(BaseModel):
    id:           UUID
    name:         str
    description:  Optional[str]
    price:        float
    duration_min: int
    is_active:    bool

    model_config = {"from_attributes": True}


class ServiceListResponse(BaseModel):
    services: list[ServiceResponse]
    total:    int = Field(..., description="Общее количество услуг")
