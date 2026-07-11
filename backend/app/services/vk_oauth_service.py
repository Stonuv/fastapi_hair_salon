import base64
import hashlib
import logging
import secrets
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..repositories.user_repository import UserRepository
from ..schemas.auth import TokenResponse
from .auth_service import build_token_response

logger = logging.getLogger(__name__)

_AUTHORIZE_URL = "https://id.vk.com/authorize"
_TOKEN_URL = "https://id.vk.com/oauth2/auth"
_USER_INFO_URL = "https://id.vk.com/oauth2/user_info"

# Cookies живут только на пути колбэка — state/verifier не нужны нигде,
# кроме обмена кода сразу после редиректа с VK.
STATE_COOKIE = "vk_oauth_state"
VERIFIER_COOKIE = "vk_oauth_verifier"
COOKIE_PATH = "/api/auth/vk"
COOKIE_MAX_AGE = 600  # 10 минут — с запасом на экран авторизации VK


def is_enabled() -> bool:
    return bool(settings.vk_client_id)


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def generate_pkce() -> tuple[str, str]:
    """(code_verifier, code_challenge) для OAuth 2.1 PKCE, метод S256."""
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


def build_authorize_url(state: str, code_challenge: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.vk_client_id,
        "redirect_uri": settings.vk_redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": "email",
    }
    return f"{_AUTHORIZE_URL}?{urlencode(params)}"


class VkOAuthError(Exception):
    """Ошибка на любом шаге обмена кода VK ID. Роут ловит её и делает redirect
    на /login?error=<error_code> вместо 500 — пользователь в этот момент уже
    в браузере посреди редиректа, показывать ему JSON бессмысленно."""

    def __init__(self, error_code: str):
        self.error_code = error_code
        super().__init__(error_code)


class VkOAuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def handle_callback(self, *, code: str, code_verifier: str, device_id: str) -> TokenResponse:
        token_data = self._exchange_code(code, code_verifier, device_id)
        access_token = token_data.get("access_token")
        vk_user_id = str(token_data.get("user_id") or "")
        if not access_token or not vk_user_id:
            raise VkOAuthError("vk_token_exchange_failed")

        profile = self._fetch_user_info(access_token)
        email = profile.get("email")
        first_name = profile.get("first_name") or "VK"
        last_name = profile.get("last_name") or "User"

        user = self.user_repo.get_by_vk_id(vk_user_id)
        if user is None:
            if not email:
                # Пользователь не привязал email к VK-аккаунту (scope=email не
                # дал результата) — без email завести локальную запись нечем.
                raise VkOAuthError("vk_email_required")
            existing = self.user_repo.get_by_email(email)
            if existing is not None:
                # VK подтверждает владение email — это тот же человек, что уже
                # зарегистрирован по паролю; просто привязываем VK к аккаунту.
                user = self.user_repo.link_vk_id(existing, vk_user_id)
            else:
                user = self.user_repo.create_vk_oauth_user(
                    email=email, first_name=first_name, last_name=last_name,
                    vk_user_id=vk_user_id,
                )

        if user.is_blocked:
            raise VkOAuthError("account_blocked")

        return build_token_response(user)

    def _exchange_code(self, code: str, code_verifier: str, device_id: str) -> dict:
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": code_verifier,
            "client_id": settings.vk_client_id,
            "redirect_uri": settings.vk_redirect_uri,
            "device_id": device_id,
        }
        if settings.vk_client_secret:
            payload["client_secret"] = settings.vk_client_secret
        try:
            resp = httpx.post(_TOKEN_URL, data=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            logger.exception("VK ID: обмен кода на токен не удался")
            raise VkOAuthError("vk_token_exchange_failed")

    def _fetch_user_info(self, access_token: str) -> dict:
        try:
            resp = httpx.post(
                _USER_INFO_URL,
                data={"access_token": access_token, "client_id": settings.vk_client_id},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("user", {})
        except httpx.HTTPError:
            logger.exception("VK ID: получение профиля не удалось")
            raise VkOAuthError("vk_user_info_failed")
