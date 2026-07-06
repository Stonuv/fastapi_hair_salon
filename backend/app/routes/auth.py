from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.auth import (LoginRequest, PasswordResetConfirm,
                            PasswordResetRequest, TokenResponse)
from ..schemas.user import UserCreate, UserResponse, UserUpdate
from ..services.auth_service import (AuthService, clear_auth_cookie,
                                     get_current_user, set_auth_cookie)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse,
             status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, response: Response, db: Session = Depends(get_db)):
    token_response = AuthService(db).register(data)
    set_auth_cookie(response, token_response.access_token)
    return token_response


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, response: Response,
          db: Session = Depends(get_db)):
    ip_address = request.client.host if request.client else None
    token_response = AuthService(db).login(data.email, data.password, ip_address)
    set_auth_cookie(response, token_response.access_token)
    return token_response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Отзывает текущий access-токен (см. token_version) и снимает cookie."""
    AuthService(db).logout(current_user)
    clear_auth_cookie(response)


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
    return AuthService(db).update_profile(current_user, data)


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
