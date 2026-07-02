"""Юнит-тесты без БД: сервисы получают фейковые репозитории, схемы и чистые
функции тестируются напрямую. Интеграционных тестов с PostgreSQL нет —
ключевая защита от двойного бронирования на уровне БД (EXCLUDE USING gist)
проверяется вручную/на стенде."""
import sys
from pathlib import Path

# Запуск из любого места: добавляем backend/ в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
