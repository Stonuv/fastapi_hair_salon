from datetime import date as date_
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from ..models.enums import AppointmentStatus
from .fields import MoneyOut
from .master import MasterBriefResponse
from .service import ServiceResponse
from .user import UserResponse

# ── Создание записи (от клиента) ─────────────────────────────────


class AppointmentCreate(BaseModel):
    """
    Клиент передаёт только эти три поля.
    end_time и final_price вычисляются на сервере автоматически.
    """
    master_id:  Annotated[UUID, Field(description="UUID мастера")]
    service_id: Annotated[UUID, Field(description="UUID услуги")]
    start_time: Annotated[AwareDatetime, Field(
        description="Желаемое время начала (обязательно с таймзоной; нормализуется в UTC)")]

    @field_validator("start_time")
    @classmethod
    def _normalize_to_utc(cls, v: datetime) -> datetime:
        # Вся логика расписания/слотов работает в UTC — приводим на входе,
        # чтобы день недели и рабочее окно не зависели от офсета клиента.
        return v.astimezone(timezone.utc)


# ── Смена статуса (от мастера / админа) ──────────────────────────


class AppointmentStatusUpdate(BaseModel):
    status: Annotated[AppointmentStatus, Field(description="Новый статус записи")]


# ── Краткий ответ (для списков) ───────────────────────────────────


class AppointmentBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           UUID
    client_id:    UUID
    client_name:  str
    master_id:    UUID
    master_name:  str
    service_id:   UUID
    service_name: str
    start_time:   datetime
    end_time:     datetime
    final_price:  MoneyOut
    status:       AppointmentStatus
    review_id:    Annotated[UUID | None, Field(default=None, description="Заполнено, если отзыв уже оставлен")]


# ── Полный ответ (для детальной страницы) ────────────────────────


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:          UUID
    client:      UserResponse
    master:      MasterBriefResponse
    service:     ServiceResponse
    start_time:  datetime
    end_time:    datetime
    final_price: MoneyOut
    status:      AppointmentStatus
    created_at:  datetime


# ── Свободные слоты ──────────────────────────────────────────────


class SlotResponse(BaseModel):
    """Один свободный временной слот у мастера."""
    start_time: Annotated[datetime, Field(description="Начало слота")]
    end_time:   Annotated[datetime, Field(description="Конец слота")]


class SlotListResponse(BaseModel):
    master_id: UUID
    date:      Annotated[date_, Field(description="Дата, на которую рассчитаны слоты")]
    slots:     list[SlotResponse]
