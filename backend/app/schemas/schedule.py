from pydantic import BaseModel, Field, model_validator
from typing import Optional
from uuid import UUID
from datetime import time


# ── Создание / обновление ────────────────────────────────────────

class ScheduleCreate(BaseModel):
    day_of_week: int  = Field(..., ge=0, le=6,
                               description="День недели: 0=пн … 6=вс")
    start_time:  time = Field(..., description="Начало рабочего дня")
    end_time:    time = Field(..., description="Конец рабочего дня")
    is_working:  bool = Field(default=True, description="Рабочий день?")

    @model_validator(mode="after")
    def end_after_start(self) -> "ScheduleCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time должен быть позже start_time")
        return self


class ScheduleUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time:   Optional[time] = None
    is_working: Optional[bool] = None

    @model_validator(mode="after")
    def end_after_start(self) -> "ScheduleUpdate":
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError("end_time должен быть позже start_time")
        return self


# ── Ответ API ────────────────────────────────────────────────────

class ScheduleResponse(BaseModel):
    id:          UUID
    master_id:   UUID
    day_of_week: int
    start_time:  time
    end_time:    time
    is_working:  bool

    model_config = {"from_attributes": True}
