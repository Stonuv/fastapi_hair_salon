import uuid
from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from ..database import Base
from .enums import UserRole


class User(Base):
    __tablename__ = "users" # Название таблицы

    # Атрибуты таблицы, какие поля есть и какого они типа
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name    = Column(String(100), nullable=False)
    last_name     = Column(String(100), nullable=False)
    phone         = Column(String(20),  unique=True) # added nullable=False
    role          = Column(Enum(UserRole), nullable=False, default=UserRole.client)
    created_at    = Column(DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    # Профиль мастера (только если role = 'master')
    master_profile = relationship("Master", back_populates="user",
                                  uselist=False, cascade="all, delete-orphan")

    # Записи клиента (только если role = 'client')
    appointments   = relationship("Appointment", back_populates="client",
                                  foreign_keys="Appointment.client_id")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
