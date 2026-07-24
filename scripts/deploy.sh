#!/usr/bin/env bash
set -euo pipefail

# Однокомандный деплой обновлений на VPS: подтягивает код, пересобирает и
# перезапускает стек, дожидается healthcheck'ов backend/frontend/caddy
# (см. ROADMAP.md Фаза 1) прежде чем считать деплой успешным — падает с
# ненулевым кодом, если что-то не поднялось здоровым, а не оставляет
# сломанный деплой молча висеть. Миграции накатываются автоматически при
# старте backend-контейнера (см. backend/Dockerfile) — отдельного шага
# здесь не нужно.
#
# Не подменяет собой полноценный CD (нет автозапуска на merge/push,
# нет отката) — задокументированный промежуточный шаг, см. ROADMAP.md
# Фаза 3. Запуск на сервере из корня уже склонированного репозитория:
#
#   ./scripts/deploy.sh

cd "$(dirname "$0")/.."

echo "==> git pull"
git pull --ff-only

echo "==> docker compose up --build -d (ждём healthcheck)"
docker compose up --build -d --wait --wait-timeout 120

echo "==> деплой успешен"
docker compose ps
