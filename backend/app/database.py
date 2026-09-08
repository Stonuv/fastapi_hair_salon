from collections.abc import Iterator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from .config import settings

# ── Engine ───────────────────────────────────────────────────────
# pool_pre_ping=True — проверяет соединение перед каждым запросом,
# защищает от ошибок при простое (PostgreSQL закрывает idle-соединения).
#
# pool_size/max_overflow — те же числа, что и дефолт SQLAlchemy (5/10),
# выставлены явно, чтобы это было осознанным решением, а не молчаливым
# дефолтом. До 15 одновременных соединений от backend — с большим запасом
# укладывается в default max_connections=100 у Postgres (16-alpine в
# docker-compose.yml не переопределяет его), даже с учётом отдельных
# подключений backup-сервиса/ручного psql. Приложение и так рассчитано на
# один инстанс backend (см. ROADMAP.md — rate-limiting/scheduler
# in-process), поэтому здесь не 15 * N реплик, а просто 15. Пересмотреть,
# если реальная нагрузка (или горизонтальное масштабирование backend)
# когда-нибудь этот запас исчерпает.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# ── Session factory ──────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ── Соглашение об именах ограничений ─────────────────────────────
# Стандарт именования (zapiska/db_naming_standards.md) задаёт префиксы для
# всех объектов схемы. Индексы, CHECK- и UNIQUE-ограничения именуются в
# моделях явно, а первичные и внешние ключи имени не получают -- их
# придумывает сама СУБД (users_pkey, appointments_client_id_fkey). Это
# соглашение подставляет им имена по стандарту: pk_<таблица> и
# fk_<дочерняя>_<родительская>. Без него autogenerate новых миграций
# продолжил бы плодить системные имена в обход стандарта.
NAMING_CONVENTION = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(referred_table_name)s",
}


# ── Base для всех моделей (SQLAlchemy 2.0 style) ──────────────────
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


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
