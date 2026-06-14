from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from ..database import get_db
from ..config import settings
from ..models.user import User
from ..models.enums import UserRole
from ..repositories.user_repository import UserRepository
from ..schemas.user import UserCreate, UserResponse
from ..schemas.auth import TokenResponse

# ── Утилиты для паролей ──────────────────────────────────────────
def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ── OAuth2 схема — указывает FastAPI где брать токен ─────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    # ── Регистрация ──────────────────────────────────────────────

    def register(self, data: UserCreate) -> TokenResponse:
        if self.user_repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует",
            )
        if data.phone and self.user_repo.phone_exists(data.phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким номером телефона уже существует",
            )

        password_hash = _hash_password(data.password)
        user = self.user_repo.create(data, password_hash)

        token = _create_access_token(user.id)
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    # ── Вход ─────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.user_repo.get_by_email(email)

        # Намеренно одно сообщение для обоих случаев —
        # не даём угадать, существует ли такой email.
        if not user or not _verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
            )

        token = _create_access_token(user.id)
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )


# ── JWT — вспомогательные функции ────────────────────────────────

def _create_access_token(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def _decode_token(token: str) -> Optional[UUID]:
    """Декодирует токен и возвращает user_id или None при ошибке."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        user_id = payload.get("sub")
        return UUID(user_id) if user_id else None
    except (JWTError, ValueError):
        return None


# ── FastAPI Dependencies ──────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db),
) -> User:
    """Возвращает текущего пользователя или 401."""
    user_id = _decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    return user


def require_role(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав",
            )
        return current_user
    return dependency


# ── Готовые dependency-константы для удобства ────────────────────
get_current_client = require_role(UserRole.client, UserRole.admin)
get_current_master = require_role(UserRole.master, UserRole.admin)
get_current_admin  = require_role(UserRole.admin)
