import uuid

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
