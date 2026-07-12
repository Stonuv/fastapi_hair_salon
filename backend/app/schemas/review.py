from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from .fields import RatingInt
from ..utils.content_filter import contains_link, contains_profanity

# ── Создание (от клиента, по завершённой записи) ─────────────────


def _validate_comment_content(v: str | None) -> str | None:
    # Отзыв публикуется сразу, без модерации (см. Review.is_published —
    # это лишь пост-фактум скрытие админом), поэтому фильтр обязан
    # отклонить запрос здесь, а не просто пометить на проверку.
    if v:
        if contains_profanity(v):
            raise ValueError("Комментарий содержит недопустимые слова — отредактируйте текст")
        if contains_link(v):
            raise ValueError("Ссылки и адреса сайтов в отзывах размещать нельзя")
    return v


class ReviewCreate(BaseModel):
    appointment_id: Annotated[UUID, Field(description="UUID завершённой записи")]
    rating:         Annotated[RatingInt, Field(description="Оценка от 1 до 5")]
    comment:        Annotated[str | None, Field(default=None, max_length=2000, description="Комментарий"),
                              AfterValidator(_validate_comment_content)]


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
