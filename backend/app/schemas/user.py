from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import UserRole
from .fields import NameStr, NormalizedEmailStr, PasswordStr, PhoneStr

# ── Базовые поля ─────────────────────────────────────────────────


class UserBase(BaseModel):
    email:      Annotated[NormalizedEmailStr, Field(description="Email пользователя")]
    first_name: Annotated[NameStr,  Field(description="Имя")]
    last_name:  Annotated[NameStr,  Field(description="Фамилия")]
    phone:      Annotated[PhoneStr | None, Field(default=None, description="Номер телефона")]


# ── Создание ─────────────────────────────────────────────────────


class UserCreate(UserBase):
    password: Annotated[PasswordStr, Field(description="Пароль (8–72 символа)")]


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
    email:        Annotated[NormalizedEmailStr | None, Field(default=None)]
    first_name:   Annotated[NameStr | None,  Field(default=None)]
    last_name:    Annotated[NameStr | None,  Field(default=None)]
    phone:        Annotated[PhoneStr | None, Field(default=None)]
    new_password: Annotated[PasswordStr | None, Field(default=None, description="Оставьте пустым, чтобы не менять")]


# ── API Response ─────────────────────────────────────────────────


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         Annotated[UUID, Field(description="UUID пользователя")]
    email:      str
    first_name: str
    last_name:  str
    phone:      str | None
    role:       Annotated[UserRole, Field(description="Роль: client / master / admin")]
    is_blocked: Annotated[bool, Field(default=False, description="Заблокирован ли аккаунт (вход запрещён)")]
    created_at: datetime


class UserPublicResponse(BaseModel):
    """Публичная проекция пользователя — только имя, без email/телефона.
    Используется на анонимных эндпоинтах (профиль мастера), чтобы не
    раскрывать персональные данные сотрудников."""
    model_config = ConfigDict(from_attributes=True)

    first_name: str
    last_name:  str


class ClientBriefResponse(BaseModel):
    """Клиент в контексте записи (AppointmentResponse.client) — имя и
    телефон (мастеру есть смысл связаться), без email/роли/is_blocked/
    created_at: клиенту эти поля о себе тут не нужны, мастеру/админу —
    тем более (ISSUES #23 — GET /appointments/{id} отдавал полный UserResponse)."""
    model_config = ConfigDict(from_attributes=True)

    first_name: str
    last_name:  str
    phone:      str | None
