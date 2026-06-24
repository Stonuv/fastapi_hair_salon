from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .fields import RatingInt

# ── Создание (от клиента, по завершённой записи) ─────────────────


class ReviewCreate(BaseModel):
    appointment_id: Annotated[UUID, Field(description="UUID завершённой записи")]
    rating:         Annotated[RatingInt, Field(description="Оценка от 1 до 5")]
    comment:        Annotated[str | None, Field(default=None, max_length=2000, description="Комментарий")]


# ── Модерация (публикация/скрытие — быстрое действие админа) ─────


class ReviewModerate(BaseModel):
    is_published: Annotated[bool, Field(description="Опубликован ли отзыв")]


# ── Ответ API ────────────────────────────────────────────────────


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:             UUID
    appointment_id: UUID
    client_id:      UUID
    client_name:    str
    master_id:      UUID
    master_name:    str
    service_id:     UUID
    service_name:   str
    rating:         int
    comment:        str | None
    is_published:   bool
    created_at:     datetime
