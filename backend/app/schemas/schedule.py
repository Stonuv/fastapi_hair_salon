from datetime import time
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ── Создание / обновление ────────────────────────────────────────


class ScheduleCreate(BaseModel):
    day_of_week: Annotated[int, Field(ge=0, le=6, description="День недели: 0=пн … 6=вс")]
    start_time:  Annotated[time, Field(description="Начало рабочего дня")]
    end_time:    Annotated[time, Field(description="Конец рабочего дня")]
    is_working:  Annotated[bool, Field(default=True, description="Рабочий день?")]

    @model_validator(mode="after")
    def end_after_start(self) -> "ScheduleCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time должен быть позже start_time")
        return self


class ScheduleUpdate(BaseModel):
    start_time: Annotated[time | None, Field(default=None)]
    end_time:   Annotated[time | None, Field(default=None)]
    is_working: Annotated[bool | None, Field(default=None)]

    @model_validator(mode="after")
    def end_after_start(self) -> "ScheduleUpdate":
        # Сравнение по `is not None`: time(0, 0) — falsy, truthiness молча
        # пропускала бы валидацию для полуночи. Когда передано лишь одно из
        # полей, пару с существующим значением проверяет MasterService.
        if (self.start_time is not None and self.end_time is not None
                and self.end_time <= self.start_time):
            raise ValueError("end_time должен быть позже start_time")
        return self


# ── Ответ API ────────────────────────────────────────────────────


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:          UUID
    master_id:   UUID
    day_of_week: int
    start_time:  time
    end_time:    time
    is_working:  bool
