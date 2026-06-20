from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ..models.user import User
from ..models.enums import UserRole
from ..schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    # Read 

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_phone(self, phone: str) -> Optional[User]:
        return self.db.query(User).filter(User.phone == phone).first()

    def get_all_by_role(self, role: UserRole) -> list[User]:
        return self.db.query(User).filter(User.role == role).all()

    # Create 

    def create(self, data: UserCreate, password_hash: str) -> User:
        """
        Принимает схему UserCreate и уже готовый хеш пароля.
        Хешировать пароль — задача сервиса, не репозитория.
        """
        user = User(
            email         = data.email,
            password_hash = password_hash,
            first_name    = data.first_name,
            last_name     = data.last_name,
            phone         = data.phone,
            role          = UserRole.client,  # новый пользователь всегда клиент
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # Update 

    def update(self, user: User, data: UserUpdate) -> User:
        """
        Обновляет только те поля, которые переданы (не None).
        Паттерн model_dump(exclude_unset=True) — берём только явно
        переданные поля, не затираем остальные нулями.
        """
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    # Вспомогательное 

    def email_exists(self, email: str) -> bool:
        return self.db.query(User).filter(User.email == email).first() is not None

    def phone_exists(self, phone: str) -> bool:
        return self.db.query(User).filter(User.phone == phone).first() is not None
