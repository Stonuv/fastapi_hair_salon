from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories.user_repository import UserRepository
from ..schemas.auth import (LoginRequest, PasswordResetConfirm,
                            PasswordResetRequest, TokenResponse)
from ..schemas.user import UserCreate, UserResponse, UserUpdate
from ..services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse,
             status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    return AuthService(db).register(data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip_address = request.client.host if request.client else None
    return AuthService(db).login(data.email, data.password, ip_address)


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Обновить своё имя, фамилию или телефон."""
    user = UserRepository(db).update(current_user, data)
    return UserResponse.model_validate(user)


# ── Восстановление пароля ─────────────────────────────────────────


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Если email зарегистрирован, ссылка для сброса пишется в лог сервера
    (нет SMTP-провайдера для реальной отправки). Ответ одинаковый независимо
    от результата — не раскрываем, какие email зарегистрированы.
    """
    AuthService(db).request_password_reset(data.email)
    return {"detail": "Если email зарегистрирован, ссылка для сброса пароля отправлена"}


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    AuthService(db).confirm_password_reset(data.token, data.new_password)
