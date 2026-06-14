from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID

from ..repositories.user_repository import UserRepository
from ..repositories.master_repository import MasterRepository
from ..models.enums import UserRole
from ..schemas.user import UserResponse
from ..schemas.master import MasterResponse


class AdminService:
    def __init__(self, db: Session):
        self.user_repo   = UserRepository(db)
        self.master_repo = MasterRepository(db)

    def change_role(self, user_id: UUID, role: UserRole) -> UserResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        user.role = role
        # Если понижаем с master до client — деактивируем профиль мастера
        if role != UserRole.master and user.master_profile:
            user.master_profile.is_active = False

        db = self.user_repo.db
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)

    def create_master_profile(self, user_id: UUID) -> MasterResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )
        if user.role != UserRole.master:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сначала назначьте пользователю роль 'master'",
            )
        if self.master_repo.get_by_user_id(user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Профиль мастера уже существует",
            )

        master = self.master_repo.create(user_id)
        master = self.master_repo.get_by_id(master.id)
        return MasterResponse.model_validate(master)
