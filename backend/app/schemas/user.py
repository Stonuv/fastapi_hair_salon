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


class AdminUserCreate(UserCreate):
    """Создание пользователя администратором — в отличие от саморегистрации,
    роль задаётся сразу, а не выставляется отдельным запросом."""
    role: Annotated[UserRole, Field(default=UserRole.client, description="Роль: client / master / admin")]


# ── Обновление (все поля опциональны) ────────────────────────────


class UserUpdate(BaseModel):
    first_name: Annotated[NameStr | None, Field(default=None)]
    last_name:  Annotated[NameStr | None, Field(default=None)]
    phone:      Annotated[PhoneStr | None, Field(default=None)]


class AdminUserUpdate(BaseModel):
    """Редактирование пользователя администратором — в отличие от
    самостоятельного обновления профиля (UserUpdate), позволяет также
    менять email и принудительно задать новый пароль."""
    email:        Annotated[EmailStr | None, Field(default=None)]
    first_name:   Annotated[NameStr | None,  Field(default=None)]
    last_name:    Annotated[NameStr | None,  Field(default=None)]
    phone:        Annotated[PhoneStr | None, Field(default=None)]
    new_password: Annotated[str | None, Field(default=None, min_length=8, description="Оставьте пустым, чтобы не менять")]


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
