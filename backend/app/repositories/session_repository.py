import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

from ..models.session import Session


class SessionRepository:
    def __init__(self, db: DbSession):
        self.db = db

    def create(self, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> Session:
        session = Session(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(session)
        self.db.flush()
        self.db.refresh(session)
        return session

    def get_valid_by_hash(self, token_hash: str) -> Session | None:
        """Сессия валидна, если ещё не истёк срок её refresh-токена."""
        now = datetime.now(timezone.utc)
        stmt = select(Session).where(
            Session.token_hash == token_hash,
            Session.expires_at > now,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def delete(self, session: Session) -> None:
        self.db.delete(session)
        self.db.flush()

    def delete_by_hash(self, token_hash: str) -> None:
        self.db.execute(delete(Session).where(Session.token_hash == token_hash))
        self.db.flush()

    def delete_all_for_user(self, user_id: uuid.UUID) -> None:
        """Полный логаут со всех устройств — вызывается вместе с
        bump_token_version на событиях безопасности (см. models/session.py)."""
        self.db.execute(delete(Session).where(Session.user_id == user_id))
        self.db.flush()
