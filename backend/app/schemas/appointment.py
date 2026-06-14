from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

from ..models.enums import AppointmentStatus
from .master import MasterBriefResponse
from .service import ServiceResponse
from .user import UserResponse


# ── Создание записи (от клиента) ─────────────────────────────────

class AppointmentCreate(BaseModel):
    """
    Клиент передаёт только эти три поля.
    end_time и final_price вычисляются на сервере автоматически.
    """
    master_id:  UUID     = Field(..., description="UUID мастера")
    service_id: UUID     = Field(..., description="UUID услуги")
    start_time: datetime = Field(..., description="Желаемое время начала")


# ── Отмена / смена статуса (от мастера / админа) ─────────────────

class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus = Field(..., description="Новый статус записи")


# ── Краткий ответ (для списков) ───────────────────────────────────

class AppointmentBriefResponse(BaseModel):
    id:          UUID
    master_id:   UUID
    service_id:  UUID
    start_time:  datetime
    end_time:    datetime
    final_price: float
    status:      AppointmentStatus

    model_config = {"from_attributes": True}


# ── Полный ответ (для детальной страницы) ────────────────────────

class AppointmentResponse(BaseModel):
    id:          UUID
    client:      UserResponse
    master:      MasterBriefResponse
    service:     ServiceResponse
    start_time:  datetime
    end_time:    datetime
    final_price: float
    status:      AppointmentStatus
    created_at:  datetime

    model_config = {"from_attributes": True}


# ── Списки ───────────────────────────────────────────────────────

class AppointmentListResponse(BaseModel):
    appointments: list[AppointmentBriefResponse]
    total:        int


# ── Свободные слоты ──────────────────────────────────────────────

class SlotResponse(BaseModel):
    """Один свободный временной слот у мастера."""
    start_time: datetime = Field(..., description="Начало слота")
    end_time:   datetime = Field(..., description="Конец слота")


class SlotListResponse(BaseModel):
    master_id: UUID
    date:      str = Field(..., description="Дата в формате YYYY-MM-DD")
    slots:     list[SlotResponse]
