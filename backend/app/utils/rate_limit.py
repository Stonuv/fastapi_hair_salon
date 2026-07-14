from fastapi import Request
from slowapi import Limiter

# По IP, не по пользователю — decorator slowapi проверяет лимит ДО того, как
# FastAPI успевает прогнать Depends() эндпоинта (current_user ещё недоступен
# в этот момент), а привязка к IP не требует такого порядка и уже достаточна:
# это защита от спама/автоматизированного перебора (регистрация, запись,
# отзывы), не замена бизнес-ограничений (например
# max_active_appointments_per_client в AppointmentService). В памяти процесса
# (без Redis) — приложение и так рассчитано на один инстанс бэкенда (см.
# ReminderService/scheduler.py), лимиты обнуляются при рестарте, что для
# soft-защиты от спама допустимо.


def _client_ip(request: Request) -> str:
    """Реальный IP клиента из X-Forwarded-For, а не request.client.host —
    за приложением всегда стоит Caddy -> nginx (см. Caddyfile/
    frontend/nginx.conf), поэтому request.client.host — это IP nginx-
    контейнера, один и тот же для всех посетителей сайта (лимит был бы
    общим на всех, а не per-visitor). Берём ПЕРВЫЙ адрес в цепочке — это
    исходный клиент (каждый прокси добавляет свой хоп в конец), и это
    безопасно от подделки: у Caddyfile нет `trusted_proxies`, поэтому Caddy
    по умолчанию игнорирует X-Forwarded-For из исходного запроса и
    подставляет реальный увиденный им IP сам (see Caddy docs on
    reverse_proxy X-Forwarded-* handling) — тот же баг обхода через
    подделку заголовка есть и у встроенного slowapi.util.get_ipaddr, но по
    ДРУГОЙ причине: там ищется заголовок "X_FORWARDED_FOR" (подчёркивание)
    вместо настоящего "X-Forwarded-For" (дефис), и он никогда не совпадает
    — get_ipaddr тихо всегда падает обратно на request.client.host.
    Без заголовка (локальная разработка без прокси) — просто адрес
    соединения."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=_client_ip)
