import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.enums import NotificationChannel, NotificationStatus, NotificationType
from ..models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_appointment(self, appointment_id: uuid.UUID) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.appointment_id == appointment_id)
            .order_by(Notification.scheduled_at)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_pending(self, up_to: datetime) -> list[Notification]:
        """
        Все pending-уведомления, которые должны быть отправлены до up_to.
        Используется Celery-воркером для обхода очереди.
        """
        stmt = (
            select(Notification)
            .where(
                Notification.status == NotificationStatus.pending,
                Notification.scheduled_at <= up_to,
            )
            .order_by(Notification.scheduled_at)
        )
        return list(self.db.execute(stmt).scalars().all())

    # ── Создание ─────────────────────────────────────────────────

    def create(self, appointment_id: uuid.UUID, type: NotificationType,
               channel: NotificationChannel,
               scheduled_at: datetime) -> Notification:
        notification = Notification(
            appointment_id=appointment_id,
            type=type,
            channel=channel,
            scheduled_at=scheduled_at,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def bulk_create(self, notifications: list[Notification]) -> None:
        """Создаёт несколько уведомлений за один коммит."""
        self.db.add_all(notifications)
        self.db.commit()

    # ── Обновление статуса ────────────────────────────────────────

    def mark_sent(self, notification: Notification) -> Notification:
        notification.status = NotificationStatus.sent
        notification.sent_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_failed(self, notification: Notification,
                    error: str) -> Notification:
        notification.status = NotificationStatus.failed
        notification.error_message = error
        self.db.commit()
        self.db.refresh(notification)
        return notification
