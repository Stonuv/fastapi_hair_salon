FROM python:3.14-slim

WORKDIR /app

RUN groupadd --system appuser && useradd --system --gid appuser --home-dir /app appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

# /app/uploads — точка монтирования именованного volume'а uploads (см.
# docker-compose.yml). Создаём и отдаём владение appuser'у здесь, до
# первого монтирования: Docker инициализирует НОВЫЙ именованный volume
# правами того, что уже лежит в этом пути в образе. На уже существующем
# volume'е (обновление деплоя, где он создавался ещё под root) владение
# нужно поправить один раз вручную: `docker compose exec -u root backend
# chown -R appuser:appuser /app/uploads`.
RUN mkdir -p /app/uploads && chown appuser:appuser /app/uploads

USER appuser

EXPOSE 8000

# Миграции накатываются на старте: контейнер БД должен быть готов
# (docker-compose ждёт healthcheck postgres).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
