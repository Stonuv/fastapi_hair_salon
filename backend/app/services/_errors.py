"""Общие утилиты обработки ошибок БД в сервисном слое.

Пред-проверки вида «email уже занят» в сервисах — это check-then-insert,
между проверкой и вставкой возможна гонка. Реальную целостность гарантируют
констрейнты PostgreSQL (частичные unique-индексы, EXCLUDE USING gist) —
IntegrityError от них сервис обязан перехватить и превратить в 409,
иначе проигравший гонку запрос получает 500.
"""
from sqlalchemy.exc import IntegrityError


def constraint_name(exc: IntegrityError) -> str | None:
    """Имя нарушенного констрейнта из диагностики psycopg (если доступно)."""
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)
