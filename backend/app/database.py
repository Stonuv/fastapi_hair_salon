from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from .config import settings

# ── Engine ───────────────────────────────────────────────────────
# pool_pre_ping=True — проверяет соединение перед каждым запросом,
# защищает от ошибок при простое (PostgreSQL закрывает idle-соединения).
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

# ── Session factory ──────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ── Base для всех моделей (SQLAlchemy 2.0 style) ──────────────────
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ───────────────────────────────────────────
def get_db() -> Iterator[Session]:
    """
    Dependency для FastAPI-роутов: сессия на запрос (unit-of-work).

    Транзакцией управляет этот генератор: успешный запрос коммитится один
    раз в конце, любое исключение (включая HTTPException) откатывает всё.
    Репозитории делают только flush() — многошаговые операции сервисов
    (смена роли + деактивация мастера, удаление пользователя + профиля и
    т.п.) атомарны. Исключение — журнал попыток входа: AuthService.login
    коммитит его явно, чтобы запись пережила 401/429.

    Использование в роуте:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
