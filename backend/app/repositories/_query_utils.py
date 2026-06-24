from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

T = TypeVar("T")


def paginated(db: Session, stmt: "Select[tuple[T]]", *, page: int, page_size: int) -> tuple[list[T], int]:
    """Выполняет уже отфильтрованный/отсортированный select с пагинацией.
    Возвращает (элементы страницы, общее количество строк без LIMIT/OFFSET)."""
    total = db.execute(
        select(func.count()).select_from(stmt.order_by(None).subquery())
    ).scalar_one()
    items = db.execute(
        stmt.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return list(items), total
