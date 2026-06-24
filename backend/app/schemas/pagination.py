from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, ConfigDict, computed_field

T = TypeVar("T")


class PageParams:
    """Переиспользуемая зависимость пагинации — не больше 20 записей на страницу (1.4)."""

    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Номер страницы")] = 1,
        page_size: Annotated[int, Query(ge=1, le=20, description="Размер страницы (макс. 20)")] = 20,
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PageResponse(BaseModel, Generic[T]):
    """Универсальная обёртка для постраничных списков."""

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    page_size: int

    @computed_field
    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return -(-self.total // self.page_size)
