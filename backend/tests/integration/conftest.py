"""Интеграционные тесты на реальном Postgres.

Юнит-тесты (backend/tests/*.py, вне этого пакета) намеренно работают с
фейковыми репозиториями и не трогают БД — см. docstring backend/tests/conftest.py.
Этот пакет проверяет ровно то, что юнит-тесты в принципе не могут: EXCLUDE
USING gist (защита от двойного бронирования), partial unique indexes
(soft-delete освобождает email) и happy path целиком через реальный HTTP-стек
поверх реальной БД.

Без TEST_DATABASE_URL весь пакет пропускается (см. ниже) — bare `pytest -q`
без этой переменной работает как раньше, ничего не меняется для обычной
разработки без Postgres под рукой.

Локальный запуск (одноразовый disposable Postgres, не тот, что в
docker-compose.yml дев-стека):

    docker run --rm -d --name barbershop-test-db \\
        -e POSTGRES_USER=barbershop -e POSTGRES_PASSWORD=barbershop \\
        -e POSTGRES_DB=barbershop_test -p 55432:5432 postgres:16-alpine
    TEST_DATABASE_URL=postgresql://barbershop:barbershop@localhost:55432/barbershop_test \\
        pytest -m integration tests/integration -q

Путь `tests/integration` в команде выше обязателен, не просто пример: bare
`pytest -m integration` (без пути) при сборе тестов сначала импортирует и
юнит-тесты тоже, а через них — app.config, ДО того как этот файл успеет
выставить DATABASE_URL, и миграции применятся не к той базе. Проверка ниже
превращает такую ошибку использования в понятное исключение вместо тихого
прогона против чужой БД.
"""
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    pytest.skip(
        "TEST_DATABASE_URL не задан — интеграционные тесты пропущены (см. docstring модуля)",
        allow_module_level=True,
    )

if "app.config" in sys.modules:
    raise RuntimeError(
        "app.config уже был импортирован до tests/integration/conftest.py — DATABASE_URL "
        "мог зафиксироваться на неверном значении до того, как этот файл успел его "
        "выставить. Запускайте интеграционные тесты со scoped-путём: "
        "`pytest -m integration tests/integration`, а не bare `pytest -m integration`."
    )
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from alembic import command  # noqa: E402
from alembic.config import Config as AlembicConfig  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.master import Master  # noqa: E402
from app.models.service import Service  # noqa: E402
from app.models.user import User  # noqa: E402
from app.repositories.master_repository import MasterRepository  # noqa: E402
from app.repositories.schedule_repository import ScheduleRepository  # noqa: E402
from app.repositories.service_repository import ServiceRepository  # noqa: E402
from app.repositories.user_repository import UserRepository  # noqa: E402
from app.schemas.schedule import ScheduleCreate  # noqa: E402
from app.schemas.service import ServiceCreate  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402
from app.services.auth_service import hash_password  # noqa: E402
from app.utils.rate_limit import limiter  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[2]

# Пароль тестовых аккаунтов — не нужно каждый раз придумывать новый,
# уникальность обеспечивается email'ом.
TEST_PASSWORD = "TestPass123!"


def next_weekday_at(weekday: int, hour: int, minute: int = 0) -> datetime:
    """Следующая дата с указанным днём недели (0=пн … 6=вс) на фиксированный
    час UTC — минимум +1 день от сегодня, гарантированно в будущем независимо
    от того, когда именно запущен тест."""
    today = datetime.now(timezone.utc).date()
    days_ahead = (weekday - today.weekday()) % 7
    days_ahead = days_ahead or 7
    target_date = today + timedelta(days=days_ahead)
    return datetime.combine(target_date, time(hour, minute), tzinfo=timezone.utc)


@pytest.fixture(scope="session")
def test_engine():
    """Прогоняет миграции один раз на сессию и отдаёт движок для тестов.

    env.py читает URL из app.config.settings.database_url, которая к этому
    моменту уже смотрит на TEST_DATABASE_URL (см. верх файла) — свой URL
    здесь передавать не нужно.
    """
    alembic_cfg = AlembicConfig(str(BACKEND_DIR / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    return sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """slowapi хранит счётчики в памяти процесса на весь pytest-сеанс
    (см. utils/rate_limit.py) — без сброса второй тест, дергающий /register
    или /appointments, мог бы словить 429 просто из-за порядка запуска."""
    limiter.reset()
    yield


@pytest.fixture(autouse=True)
def _cleanup_db(test_engine):
    """Каждый тест начинает и заканчивает работу на пустой БД. TRUNCATE, а не
    откат транзакции — код приложения сам коммитит по ходу дела (get_db коммитит
    в конце каждого запроса, AuthService.login коммитит журнал попыток входа
    явно), так что обычная transaction-rollback-обёртка вокруг теста ничего бы
    не откатила."""
    yield
    table_names = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with test_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db_session(test_session_factory) -> Session:
    """Прямой доступ к БД для arrange/assert в обход HTTP-слоя."""
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
async def client(test_session_factory):
    """httpx.AsyncClient поверх реального ASGI-приложения и реальной БД.

    get_db переопределён на сессию из test_session_factory (не prod-engine),
    с тем же коммит/роллбэк/close поведением, что и настоящий get_db —
    каждый вызов получает свежую сессию, как в проде (важно для теста
    настоящей конкурентности — два одновременных запроса не должны делить
    один Session, он не потокобезопасен)."""
    def _override_get_db():
        db = test_session_factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


@dataclass
class BookableSetup:
    master_user: User
    master: Master
    master_password: str
    service: Service


@pytest.fixture
def bookable_setup(db_session: Session) -> BookableSetup:
    """Мастер + услуга + расписание на весь понедельник (09:00–20:00 UTC) —
    готовая база для тестов бронирования, без завязки на конкретный час."""
    email = f"master-{uuid.uuid4().hex}@example.com"
    user_repo = UserRepository(db_session)
    master_user = user_repo.create(
        UserCreate(email=email, first_name="Мастер", last_name="Тестовый", password=TEST_PASSWORD),
        hash_password(TEST_PASSWORD),
        role=UserRole.master,
    )
    master_repo = MasterRepository(db_session)
    master = master_repo.create(master_user.id)

    service = ServiceRepository(db_session).create(
        ServiceCreate(name="Стрижка (тест)", price=Decimal("1000.00"), duration_min=60)
    )
    master_repo.add_service(master.id, service.id)

    ScheduleRepository(db_session).create(
        master.id,
        ScheduleCreate(day_of_week=0, start_time=time(9, 0), end_time=time(20, 0)),
    )
    db_session.commit()
    return BookableSetup(
        master_user=master_user, master=master, master_password=TEST_PASSWORD, service=service
    )
