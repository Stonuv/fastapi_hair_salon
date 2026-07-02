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
