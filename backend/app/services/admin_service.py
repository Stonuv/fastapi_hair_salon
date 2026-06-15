from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID

from ..repositories.user_repository import UserRepository
from ..repositories.master_repository import MasterRepository
from ..repositories.service_repository import ServiceRepository
from ..models.enums import UserRole
from ..schemas.user import UserResponse
from ..schemas.master import MasterResponse


class AdminService:
    def __init__(self, db: Session):
        self.user_repo    = UserRepository(db)
        self.master_repo  = MasterRepository(db)
        self.service_repo = ServiceRepository(db)

    def change_role(self, user_id: UUID, role: UserRole) -> UserResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Пользователь не найден")
        user.role = role
        if role != UserRole.master and user.master_profile:
            user.master_profile.is_active = False
        db = self.user_repo.db
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)

    def create_master_profile(self, user_id: UUID) -> MasterResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Пользователь не найден")
        if user.role != UserRole.master:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Сначала назначьте пользователю роль 'master'")
        if self.master_repo.get_by_user_id(user_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Профиль мастера уже существует")
        master = self.master_repo.create(user_id)
        master = self.master_repo.get_by_id(master.id)
        return MasterResponse.model_validate(master)

    def delete_user(self, user_id: UUID) -> None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Пользователь не найден")
        db = self.user_repo.db
        db.delete(user)
        db.commit()

    def delete_service(self, service_id: UUID) -> None:
        service = self.service_repo.get_by_id(service_id)
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Услуга не найдена")
        db = self.service_repo.db
        db.delete(service)
        db.commit()

    def get_all_users(self):
        db = self.user_repo.db
        from ..models.user import User
        return db.query(User).order_by(User.created_at.desc()).all()
