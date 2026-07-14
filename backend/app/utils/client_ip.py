from fastapi import Request


def client_ip(request: Request) -> str:
    """Реальный IP клиента из X-Forwarded-For, а не request.client.host —
    за приложением всегда стоит Caddy -> nginx (см. Caddyfile/
    frontend/nginx.conf), поэтому request.client.host — это IP nginx-
    контейнера, один и тот же для всех запросов независимо от того, кто их
    прислал (rate_limit.py — общий лимит на всех вместо per-visitor;
    login_attempts.ip_address — бесполезная для аудита константа). Берём
    ПЕРВЫЙ адрес в цепочке — это исходный клиент (каждый прокси добавляет
    свой хоп в конец), и это безопасно от подделки: у Caddyfile нет
    `trusted_proxies`, поэтому Caddy по умолчанию игнорирует
    X-Forwarded-For из исходного запроса и подставляет реальный увиденный
    им IP сам (см. документацию Caddy по reverse_proxy X-Forwarded-*) —
    тот же баг обхода через подделку заголовка есть и у встроенного
    slowapi.util.get_ipaddr, но по ДРУГОЙ причине: там ищется заголовок
    "X_FORWARDED_FOR" (подчёркивание) вместо настоящего "X-Forwarded-For"
    (дефис), и он никогда не совпадает — get_ipaddr тихо всегда падает
    обратно на request.client.host. Без заголовка (локальная разработка
    без прокси) — просто адрес соединения."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
