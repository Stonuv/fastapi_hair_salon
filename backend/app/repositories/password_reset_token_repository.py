import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_valid_by_hash(self, token_hash: str) -> Optional[PasswordResetToken]:
        """Токен валиден если не использован и не просрочен."""
        now = datetime.now(timezone.utc)
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, user_id: uuid.UUID, token_hash: str,
               expires_at: datetime) -> PasswordResetToken:
        token = PasswordResetToken(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def invalidate_all_for_user(self, user_id: uuid.UUID) -> None:
        """Гасит все неиспользованные токены пользователя при новом запросе сброса."""
        now = datetime.now(timezone.utc)
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
        for token in self.db.execute(stmt).scalars().all():
            token.used_at = now
        self.db.commit()

    def mark_used(self, token: PasswordResetToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        self.db.commit()
