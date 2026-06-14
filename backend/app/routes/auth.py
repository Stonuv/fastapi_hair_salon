from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.auth_service import AuthService, get_current_user
from ..schemas.user import UserCreate, UserResponse
from ..schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse,
             status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового клиента. Возвращает токен сразу."""
    return AuthService(db).register(data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Вход по email и паролю."""
    return AuthService(db).login(data.email, data.password)


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    """Данные текущего авторизованного пользователя."""
    return UserResponse.model_validate(current_user)
