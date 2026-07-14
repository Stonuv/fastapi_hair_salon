"""client_ip() — реальный IP клиента из-за прокси-цепочки Caddy -> nginx
(см. utils/client_ip.py за подробным объяснением). Фейковый Request через
Starlette, без ASGI-приложения/TestClient — функция чистая."""
from starlette.requests import Request

from app.utils.client_ip import client_ip


def make_request(*, headers=None, client_host="127.0.0.1"):
    raw_headers = [
        (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "headers": raw_headers,
        "client": (client_host, 12345) if client_host else None,
    }
    return Request(scope)


class TestClientIp:
    def test_uses_first_address_in_forwarded_chain(self):
        # "<реальный клиент>, <хоп nginx>" — см. Caddyfile (без
        # trusted_proxies Caddy подставляет реальный IP сам) + nginx.conf
        # ($proxy_add_x_forwarded_for добавляет свой хоп в конец).
        request = make_request(headers={"X-Forwarded-For": "1.2.3.4, 172.20.0.5"})
        assert client_ip(request) == "1.2.3.4"

    def test_strips_whitespace_around_address(self):
        request = make_request(headers={"X-Forwarded-For": " 1.2.3.4 , 172.20.0.5"})
        assert client_ip(request) == "1.2.3.4"

    def test_single_address_without_proxy_hop(self):
        request = make_request(headers={"X-Forwarded-For": "1.2.3.4"})
        assert client_ip(request) == "1.2.3.4"

    def test_falls_back_to_connection_address_without_header(self):
        # Локальная разработка без Caddy/nginx перед бэкендом.
        request = make_request(headers={}, client_host="203.0.113.9")
        assert client_ip(request) == "203.0.113.9"

    def test_falls_back_to_unknown_without_header_or_client(self):
        request = make_request(headers={}, client_host=None)
        assert client_ip(request) == "unknown"

    def test_ignores_underscore_variant_header(self):
        # Регрессия на баг slowapi.util.get_ipaddr (см. docstring
        # client_ip.py) — настоящий заголовок "X-Forwarded-For" (дефис),
        # а не "X_FORWARDED_FOR" (подчёркивание), должен быть найден.
        request = make_request(headers={"X-Forwarded-For": "9.9.9.9"})
        assert client_ip(request) == "9.9.9.9"
