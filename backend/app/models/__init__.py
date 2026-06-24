# Импортируем все модели здесь — это нужно чтобы Alembic
# видел их при автогенерации миграций.

from .enums import (
    AppointmentStatus,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
    UserRole,
)
from .user import User
from .master import Master, MasterService
from .service import Service
from .schedule import Schedule
from .appointment import Appointment
from .notification import Notification
from .review import Review
from .password_reset_token import PasswordResetToken
from .login_attempt import LoginAttempt
from .site_settings import SiteSettings

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
    "Review",
    "PasswordResetToken",
    "LoginAttempt",
    "SiteSettings",
]
