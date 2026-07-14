import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.email_verification_token import EmailVerificationToken


class EmailVerificationTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_valid_by_hash(self, token_hash: str) -> Optional[EmailVerificationToken]:
        """Токен валиден если не использован и не просрочен."""
        now = datetime.now(timezone.utc)
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > now,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, user_id: uuid.UUID, token_hash: str,
               expires_at: datetime) -> EmailVerificationToken:
        token = EmailVerificationToken(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        self.db.add(token)
        self.db.flush()
        self.db.refresh(token)
        return token

    def count_created_since(self, user_id: uuid.UUID, since: datetime) -> int:
        """Сколько писем подтверждения выдано пользователю за окно — для rate limit
        повторной отправки."""
        stmt = select(func.count()).select_from(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.created_at >= since,
        )
        return self.db.execute(stmt).scalar_one()

    def invalidate_all_for_user(self, user_id: uuid.UUID) -> None:
        """Гасит все неиспользованные токены пользователя при новой отправке письма."""
        now = datetime.now(timezone.utc)
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used_at.is_(None),
        )
        for token in self.db.execute(stmt).scalars().all():
            token.used_at = now
        self.db.flush()

    def mark_used(self, token: EmailVerificationToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        self.db.flush()
