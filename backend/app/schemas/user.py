from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..models.enums import UserRole
from .fields import NameStr, PhoneStr

# ── Базовые поля ─────────────────────────────────────────────────


class UserBase(BaseModel):
    email:      Annotated[EmailStr, Field(description="Email пользователя")]
    first_name: Annotated[NameStr,  Field(description="Имя")]
    last_name:  Annotated[NameStr,  Field(description="Фамилия")]
    phone:      Annotated[PhoneStr | None, Field(default=None, description="Номер телефона")]


# ── Создание ─────────────────────────────────────────────────────


class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=8, description="Пароль (мин. 8 символов)")]


# ── Обновление (все поля опциональны) ────────────────────────────


class UserUpdate(BaseModel):
    first_name: Annotated[NameStr | None, Field(default=None)]
    last_name:  Annotated[NameStr | None, Field(default=None)]
    phone:      Annotated[PhoneStr | None, Field(default=None)]


# ── API Response ─────────────────────────────────────────────────


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         Annotated[UUID, Field(description="UUID пользователя")]
    email:      str
    first_name: str
    last_name:  str
    phone:      str | None
    role:       Annotated[UserRole, Field(description="Роль: client / master / admin")]
    created_at: datetime
