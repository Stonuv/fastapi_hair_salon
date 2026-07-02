from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

T = TypeVar("T")

# Символ экранирования для escape_like/ilike — один на все репозитории.
LIKE_ESCAPE_CHAR = "\\"


def escape_like(value: str) -> str:
    """Экранирует спецсимволы LIKE/ILIKE (%, _) в пользовательском вводе.
    Использовать в паре с .ilike(f"%{escape_like(s)}%", escape=LIKE_ESCAPE_CHAR),
    иначе поиск по "100%" или "_" искажает результаты и позволяет дорогие сканы."""
    return (value.replace(LIKE_ESCAPE_CHAR, LIKE_ESCAPE_CHAR * 2)
                 .replace("%", LIKE_ESCAPE_CHAR + "%")
                 .replace("_", LIKE_ESCAPE_CHAR + "_"))


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
