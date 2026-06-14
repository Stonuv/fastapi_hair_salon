from pydantic import BaseModel, Field
from .user import UserResponse


# ── Запрос на вход ───────────────────────────────────────────────

class LoginRequest(BaseModel):
    email:    str = Field(..., description="Email пользователя")
    password: str = Field(..., description="Пароль")


# ── Ответ с токеном ──────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access-токен")
    token_type:   str = Field(default="bearer")
    user:         UserResponse = Field(..., description="Данные авторизованного пользователя")
