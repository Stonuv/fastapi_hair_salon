from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from ..models.notification import Notification
from ..models.enums import NotificationType, NotificationChannel, NotificationStatus


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Чтение ───────────────────────────────────────────────────

    def get_by_appointment(self, appointment_id: UUID) -> list[Notification]:
        return (
            self.db.query(Notification)
            .filter(Notification.appointment_id == appointment_id)
            .order_by(Notification.scheduled_at)
            .all()
        )

    def get_pending(self, up_to: datetime) -> list[Notification]:
        """
        Все pending-уведомления, которые должны быть отправлены до up_to.
        Используется Celery-воркером для обхода очереди.
        """
        return (
            self.db.query(Notification)
            .filter(
                Notification.status       == NotificationStatus.pending,
                Notification.scheduled_at <= up_to,
            )
            .order_by(Notification.scheduled_at)
            .all()
        )

    # ── Создание ─────────────────────────────────────────────────

    def create(self, appointment_id: UUID, type: NotificationType,
               channel: NotificationChannel,
               scheduled_at: datetime) -> Notification:
        notification = Notification(
            appointment_id = appointment_id,
            type           = type,
            channel        = channel,
            scheduled_at   = scheduled_at,
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
        notification.status  = NotificationStatus.sent
        notification.sent_at = datetime.now()
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_failed(self, notification: Notification,
                    error: str) -> Notification:
        notification.status        = NotificationStatus.failed
        notification.error_message = error
        self.db.commit()
        self.db.refresh(notification)
        return notification
