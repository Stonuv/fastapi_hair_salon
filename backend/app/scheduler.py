import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI

from .config import settings
from .database import SessionLocal
from .services.reminder_service import ReminderService

logger = logging.getLogger(__name__)


async def _run_reminder_pass() -> None:
    db = SessionLocal()
    try:
        # Синхронные SQLAlchemy/SMTP-вызовы — уводим в отдельный поток, чтобы
        # не блокировать event loop, который в этом же процессе обслуживает
        # HTTP-запросы (см. README — отдельного воркера для рассылок нет).
        await asyncio.to_thread(ReminderService(db).send_due_reminders)
    finally:
        db.close()


async def _reminder_loop() -> None:
    while True:
        try:
            await _run_reminder_pass()
        except Exception:
            logger.exception("Не удалось выполнить проход напоминаний о записях")
        await asyncio.sleep(settings.reminder_poll_interval_seconds)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(_reminder_loop())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
