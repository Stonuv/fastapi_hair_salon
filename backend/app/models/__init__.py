# Импортируем все модели здесь — это нужно чтобы Alembic
# видел их при автогенерации миграций.

from .enums import (
    UserRole,
    AppointmentStatus,
    NotificationType,
    NotificationChannel,
    NotificationStatus,
)
from .user         import User
from .master       import Master, MasterService
from .service      import Service
from .schedule     import Schedule
from .appointment  import Appointment
from .notification import Notification

__all__ = [
    "UserRole",
    "AppointmentStatus",
    "NotificationType",
    "NotificationChannel",
    "NotificationStatus",
    "User",
    "Master",
    "MasterService",
    "Service",
    "Schedule",
    "Appointment",
    "Notification",
]
