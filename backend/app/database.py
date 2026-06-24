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
def get_db() -> Session:
    """
    Dependency для FastAPI-роутов.
    Открывает сессию на запрос и гарантированно закрывает её после.

    Использование в роуте:
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
