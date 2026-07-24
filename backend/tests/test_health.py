"""GET /health — SELECT 1 против БД, не только "процесс жив" (см. main.py).
TestClient на реальном app с переопределённым get_db — фейковая сессия,
без реальной БД (реальная БД — забота интеграционных тестов, не этого файла)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.main import app


class _WorkingSession:
    def execute(self, *args, **kwargs):
        return None


class _BrokenSession:
    def execute(self, *args, **kwargs):
        raise SQLAlchemyError("connection refused")


def _fake_get_db(session):
    def _get_db():
        yield session
    return _get_db


@pytest.fixture(autouse=True)
def _clear_override():
    yield
    app.dependency_overrides.pop(get_db, None)


class TestHealth:
    def test_returns_ok_when_database_reachable(self):
        app.dependency_overrides[get_db] = _fake_get_db(_WorkingSession())
        res = TestClient(app).get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

    def test_returns_503_when_database_unreachable(self):
        app.dependency_overrides[get_db] = _fake_get_db(_BrokenSession())
        res = TestClient(app).get("/health")
        assert res.status_code == 503
        assert res.json() == {"detail": "database unavailable"}
