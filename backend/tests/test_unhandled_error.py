"""Необработанное исключение отдаётся как {"detail": "..."} со статусом 500
(main.py: unhandled_exception_handler), а не как text/plain "Internal Server
Error" — фронтенд читает именно detail и на голом тексте показал бы пустое
сообщение, а перехватчик в api/client.js по статусу уводит на страницу /500.

raise_server_exceptions=False обязателен: Starlette после хендлера всё равно
поднимает исходное исключение дальше (чтобы его увидели лог uvicorn и
Sentry), и TestClient по умолчанию перевыбросил бы его вместо ответа. Здесь
проверяется ровно то, что уходит по сети реальному клиенту.

debug=False — тоже обязательное условие, а не деталь: в debug-режиме
ServerErrorMiddleware отдаёт трассировку и до хендлера дело не доходит.
Проверяется именно продовая конфигурация (docker-compose.yml: DEBUG=false),
а не дефолт config.py, где debug=True ради локальной разработки.
"""
import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


class _ExplodingSession:
    def execute(self, *args, **kwargs):
        raise RuntimeError("баг в коде, а не недоступная зависимость")


def _fake_get_db():
    yield _ExplodingSession()


@pytest.fixture(autouse=True)
def _production_like_app():
    """debug=False + пересборка middleware-стека: Starlette фиксирует debug в
    ServerErrorMiddleware при сборке стека, менять один флаг post factum
    недостаточно. После теста возвращаем оба значения на место — app в этом
    проекте общий для всех тестов."""
    original_debug, original_stack = app.debug, app.middleware_stack
    app.debug = False
    app.middleware_stack = app.build_middleware_stack()
    yield
    app.debug, app.middleware_stack = original_debug, original_stack
    app.dependency_overrides.pop(get_db, None)


class TestUnhandledError:
    def test_returns_500_with_detail(self):
        app.dependency_overrides[get_db] = _fake_get_db
        res = TestClient(app, raise_server_exceptions=False).get("/health")

        assert res.status_code == 500
        assert res.json() == {"detail": "Внутренняя ошибка сервера. Попробуйте позже."}

    def test_does_not_leak_exception_text(self):
        app.dependency_overrides[get_db] = _fake_get_db
        res = TestClient(app, raise_server_exceptions=False).get("/health")

        # Ни текста исключения, ни трассировки — разбор по логу и Sentry.
        assert "баг в коде" not in res.text
        assert "Traceback" not in res.text
