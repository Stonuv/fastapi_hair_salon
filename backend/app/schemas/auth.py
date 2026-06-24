from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from .user import UserResponse

# ── Запрос на вход ───────────────────────────────────────────────


class LoginRequest(BaseModel):
    email:    Annotated[EmailStr, Field(description="Email пользователя")]
    password: Annotated[str, Field(description="Пароль")]


# ── Ответ с токеном ──────────────────────────────────────────────


class TokenResponse(BaseModel):
    access_token: Annotated[str, Field(description="JWT access-токен")]
    token_type:   Annotated[str, Field(default="bearer")]
    user:         Annotated[UserResponse, Field(description="Данные авторизованного пользователя")]


# ── Восстановление пароля (без реальной отправки email — см. config.py) ──


class PasswordResetRequest(BaseModel):
    email: Annotated[EmailStr, Field(description="Email для восстановления пароля")]


class PasswordResetConfirm(BaseModel):
    token:        Annotated[str, Field(description="Токен из ссылки восстановления")]
    new_password: Annotated[str, Field(min_length=8, description="Новый пароль (мин. 8 символов)")]
