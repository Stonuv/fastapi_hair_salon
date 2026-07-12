from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .fields import NormalizedEmailStr, PasswordStr
from .user import UserResponse

# ── Запрос на вход ───────────────────────────────────────────────


class LoginRequest(BaseModel):
    email:    Annotated[NormalizedEmailStr, Field(description="Email пользователя")]
    password: Annotated[str, Field(description="Пароль")]


# ── Ответ с токеном ──────────────────────────────────────────────


class TokenResponse(BaseModel):
    access_token: Annotated[str, Field(description="JWT access-токен")]
    token_type:   Literal["bearer"] = "bearer"
    user:         Annotated[UserResponse, Field(description="Данные авторизованного пользователя")]


# ── Восстановление пароля ──────────────────────────────────────


class PasswordResetRequest(BaseModel):
    email: Annotated[NormalizedEmailStr, Field(description="Email для восстановления пароля")]


class PasswordResetConfirm(BaseModel):
    token:        Annotated[str, Field(description="Токен из ссылки восстановления")]
    new_password: Annotated[PasswordStr, Field(description="Новый пароль (8–72 символа)")]
