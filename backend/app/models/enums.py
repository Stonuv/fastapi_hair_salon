import enum


class UserRole(str, enum.Enum):
    client = "client"
    master = "master"
    admin  = "admin"


class AppointmentStatus(str, enum.Enum):
    pending   = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    done      = "done"


class NotificationType(str, enum.Enum):
    confirmation = "confirmation"
    reminder_24h = "reminder_24h"
    reminder_1h  = "reminder_1h"
    cancellation = "cancellation"


class NotificationChannel(str, enum.Enum):
    email     = "email"
    messenger = "messenger"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent    = "sent"
    failed  = "failed"
