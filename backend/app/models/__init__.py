# Импортируем все модели здесь — это нужно чтобы Alembic
# видел их при автогенерации миграций.

from .enums import AppointmentStatus, UserRole
from .salon import Salon
from .user import User
from .master import Master, MasterService
from .service import Service
from .schedule import Schedule
from .appointment import Appointment
from .review import Review
from .password_reset_token import PasswordResetToken
from .email_verification_token import EmailVerificationToken
from .login_attempt import LoginAttempt
from .site_settings import SiteSettings
from .session import Session

__all__ = [
    "UserRole",
    "AppointmentStatus",
    "Salon",
    "User",
    "Master",
    "MasterService",
    "Service",
    "Schedule",
    "Appointment",
    "Review",
    "PasswordResetToken",
    "EmailVerificationToken",
    "LoginAttempt",
    "SiteSettings",
    "Session",
]
