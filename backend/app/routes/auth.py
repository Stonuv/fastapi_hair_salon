import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..schemas.auth import (LoginRequest, PasswordResetConfirm,
                            PasswordResetRequest, TokenResponse)
from ..schemas.user import UserCreate, UserResponse, UserUpdate
from ..services.auth_service import (AuthService, clear_auth_cookie,
                                     get_current_user, set_auth_cookie)
from ..services.vk_oauth_service import (COOKIE_MAX_AGE, COOKIE_PATH,
                                         STATE_COOKIE, VERIFIER_COOKIE,
                                         VkOAuthError, VkOAuthService,
                                         build_authorize_url, generate_pkce,
                                         is_enabled)

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
    Если email зарегистрирован, ссылка для сброса отправляется письмом (SMTP).
    Ответ одинаковый независимо от результата — не раскрываем, какие email
    зарегистрированы.
    """
    AuthService(db).request_password_reset(data.email)
    return {"detail": "Если email зарегистрирован, ссылка для сброса пароля отправлена"}


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    AuthService(db).confirm_password_reset(data.token, data.new_password)


# ── VK ID (OAuth 2.1 + PKCE) ────────────────────────────────────────
#
# Классический redirect-флоу, а не SPA-попап: /vk/login отдаёт 307 на VK со
# state+PKCE в httpOnly-cookie, VK возвращает браузер на /vk/callback, который
# сам логинит пользователя (та же cookie-сессия, что и обычный /login) и
# редиректит обратно на фронтенд. SPA ничего не знает про code/token — просто
# видит уже залогиненную сессию, когда попадает на "/".


@router.get("/vk/enabled")
def vk_enabled():
    """Фронтенд скрывает кнопку "Войти через VK", пока VK_CLIENT_ID не задан."""
    return {"enabled": is_enabled()}


@router.get("/vk/login")
def vk_login():
    if not is_enabled():
        return RedirectResponse(f"{settings.frontend_base_url}/login?error=vk_not_configured")

    state = secrets.token_urlsafe(24)
    verifier, challenge = generate_pkce()
    redirect = RedirectResponse(build_authorize_url(state, challenge))
    for key, value in ((STATE_COOKIE, state), (VERIFIER_COOKIE, verifier)):
        redirect.set_cookie(
            key=key, value=value, max_age=COOKIE_MAX_AGE, path=COOKIE_PATH,
            httponly=True, secure=settings.cookie_secure, samesite="lax",
        )
    return redirect


@router.get("/vk/callback")
def vk_callback(
    request: Request,
    db: Session = Depends(get_db),
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    device_id: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query(description="Код ошибки от VK, если пользователь отменил вход")] = None,
):
    def fail(error_code: str) -> RedirectResponse:
        redirect = RedirectResponse(f"{settings.frontend_base_url}/login?error={error_code}")
        redirect.delete_cookie(STATE_COOKIE, path=COOKIE_PATH)
        redirect.delete_cookie(VERIFIER_COOKIE, path=COOKIE_PATH)
        return redirect

    if error:
        return fail("vk_auth_cancelled")

    cookie_state = request.cookies.get(STATE_COOKIE)
    verifier = request.cookies.get(VERIFIER_COOKIE)
    # state сверяется с cookie, а не просто "присутствует" — это и есть защита
    # от CSRF на этом эндпоинте (классический OAuth state-параметр).
    if not (code and device_id and state and cookie_state and verifier) or state != cookie_state:
        return fail("vk_auth_failed")

    try:
        token_response = VkOAuthService(db).handle_callback(
            code=code, code_verifier=verifier, device_id=device_id,
        )
    except VkOAuthError as exc:
        db.rollback()
        return fail(exc.error_code)

    redirect = RedirectResponse(f"{settings.frontend_base_url}/")
    set_auth_cookie(redirect, token_response.access_token)
    redirect.delete_cookie(STATE_COOKIE, path=COOKIE_PATH)
    redirect.delete_cookie(VERIFIER_COOKIE, path=COOKIE_PATH)
    return redirect
