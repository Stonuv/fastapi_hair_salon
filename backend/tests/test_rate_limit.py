"""Rate-limit wiring (utils/rate_limit.py + main.py exception handler) —
проверяется на изолированном тестовом приложении с одним фиктивным
эндпоинтом, а не через реальные /api/auth/register и т.п.: тем нужна
настоящая БД для собственно бизнес-логики (email_exists и т.д.), а здесь
важен только сам факт, что декоратор @limiter.limit(...) и наш JSON-хендлер
429 работают как задумано — тот же приём, что и остальной проект (сервисы
тестируются в изоляции от роутов, см. test_auth_unit.py)."""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.main import rate_limit_handler
from app.utils.rate_limit import limiter
from slowapi.errors import RateLimitExceeded

# Приложение и роут регистрируются РОВНО ОДИН РАЗ на уровне модуля, а не в
# фикстуре — limiter.reset() (см. ниже) чистит только счётчики, а не список
# зарегистрированных лимитов; пересоздавая @limiter.limit(...) на каждый
# тест, поймали бы дублирующиеся правила на одном и том же роуте (один
# реальный запрос декрементил бы общий счётчик по разу за каждую копию
# правила) — так первый же запрос в каждом следующем тесте внезапно
# оказывался "лишним".
_app = FastAPI()
_app.state.limiter = limiter
_app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


@_app.get("/limited")
@limiter.limit("2/minute")
def _limited_endpoint(request: Request):
    return {"ok": True}


@pytest.fixture
def client():
    # Тот же limiter-синглтон, что использует настоящее приложение (см.
    # app/main.py) — только сброс счётчиков между тестами, регистрация
    # роута/лимита выше не трогается.
    limiter.reset()
    return TestClient(_app)


class TestRateLimitWiring:
    def test_requests_within_limit_pass_through(self, client):
        assert client.get("/limited").status_code == 200
        assert client.get("/limited").status_code == 200

    def test_request_over_limit_is_rejected_with_429(self, client):
        client.get("/limited")
        client.get("/limited")
        res = client.get("/limited")
        assert res.status_code == 429

    def test_429_response_uses_project_error_shape_in_russian(self, client):
        client.get("/limited")
        client.get("/limited")
        res = client.get("/limited")
        # {"detail": "..."} — тот же формат, что и остальные ошибки проекта
        # (friendlyValidationError на фронтенде читает именно "detail"), а
        # не {"error": "..."} по умолчанию из slowapi._rate_limit_exceeded_handler.
        assert res.json() == {"detail": "Слишком много запросов. Попробуйте позже."}

    def test_different_ips_have_independent_limits(self, client):
        # client_ip (см. utils/client_ip.py) — лимит по IP, не глобальный:
        # разные клиенты не должны блокировать друг друга.
        client.get("/limited", headers={"X-Forwarded-For": "1.1.1.1"})
        client.get("/limited", headers={"X-Forwarded-For": "1.1.1.1"})
        blocked = client.get("/limited", headers={"X-Forwarded-For": "1.1.1.1"})
        assert blocked.status_code == 429

        other_ip = client.get("/limited", headers={"X-Forwarded-For": "2.2.2.2"})
        assert other_ip.status_code == 200

    def test_uses_first_ip_in_forwarded_chain_not_the_proxy_hop(self, client):
        # Цепочка "<реальный клиент>, <IP ближайшего прокси>" — см. Caddyfile
        # (без trusted_proxies Caddy подставляет реальный IP сам) + nginx.conf
        # ($proxy_add_x_forwarded_for). Второе значение (хоп nginx) не должно
        # участвовать в ключе — иначе все посетители делили бы один лимит.
        client.get("/limited", headers={"X-Forwarded-For": "3.3.3.3, 172.20.0.5"})
        client.get("/limited", headers={"X-Forwarded-For": "3.3.3.3, 172.20.0.5"})
        blocked = client.get("/limited", headers={"X-Forwarded-For": "3.3.3.3, 172.20.0.5"})
        assert blocked.status_code == 429

        different_client_same_proxy_hop = client.get(
            "/limited", headers={"X-Forwarded-For": "4.4.4.4, 172.20.0.5"}
        )
        assert different_client_same_proxy_hop.status_code == 200
