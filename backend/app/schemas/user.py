from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID

from ..models.enums import UserRole


# ── Базовые поля ─────────────────────────────────────────────────

class UserBase(BaseModel):
    email:      EmailStr    = Field(..., description="Email пользователя")
    first_name: str         = Field(..., min_length=1, max_length=100,
                                    description="Имя")
    last_name:  str         = Field(..., min_length=1, max_length=100,
                                    description="Фамилия")
    phone:      Optional[str] = Field(None, max_length=20,
                                      description="Номер телефона")


# ── Создание ─────────────────────────────────────────────────────

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Пароль (мин. 8 символов)")


# ── Обновление (все поля опциональны) ────────────────────────────

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name:  Optional[str] = Field(None, min_length=1, max_length=100)
    phone:      Optional[str] = Field(None, max_length=20)


# ── Ответ API ────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id:         UUID        = Field(..., description="UUID пользователя")
    email:      str
    first_name: str
    last_name:  str
    phone:      Optional[str]
    role:       UserRole    = Field(..., description="Роль: client / master / admin")
    created_at: datetime

    model_config = {"from_attributes": True}
