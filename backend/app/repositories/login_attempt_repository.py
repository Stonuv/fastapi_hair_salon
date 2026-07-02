import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.login_attempt import LoginAttempt


class LoginAttemptRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, email_attempted: str, user_id: uuid.UUID | None,
               ip_address: str | None, success: bool) -> LoginAttempt:
        attempt = LoginAttempt(
            email_attempted=email_attempted,
            user_id=user_id,
            ip_address=ip_address,
            success=success,
        )
        self.db.add(attempt)
        self.db.commit()
        return attempt

    def count_recent_failed(self, email: str, since: datetime) -> int:
        """Неудачные попытки входа по email за окно — для временной блокировки.
        Покрыто индексом ix_login_attempts_email_created."""
        stmt = select(func.count()).select_from(LoginAttempt).where(
            LoginAttempt.email_attempted == email,
            LoginAttempt.success.is_(False),
            LoginAttempt.created_at >= since,
        )
        return self.db.execute(stmt).scalar_one()
