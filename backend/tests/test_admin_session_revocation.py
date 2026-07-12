"""AdminService: события безопасности (принудительная смена пароля,
блокировка, мягкое удаление) обязаны отзывать не только token_version, но и
все refresh-сессии пользователя — иначе access-токен отозван, а /auth/refresh
тихо выдаёт новый рабочий взамен. Фейковые репозитории, без БД."""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.models.enums import UserRole
from app.schemas.user import AdminUserUpdate
from app.services.admin_service import AdminService

USER_ID = uuid.uuid4()
ADMIN_ID = uuid.uuid4()


def make_fake_user(*, is_blocked=False):
    return SimpleNamespace(
        id=USER_ID, role=UserRole.client, email="client@example.com",
        first_name="Иван", last_name="Иванов", phone=None, is_blocked=is_blocked,
        created_at=datetime.now(timezone.utc),
    )


def make_service(*, user=None):
    svc = AdminService.__new__(AdminService)
    calls = {"bumped": False, "sessions_revoked_for": None}

    def bump_token_version(u):
        calls["bumped"] = True

    def set_blocked(u, is_blocked):
        u.is_blocked = is_blocked
        return u

    def set_password(u, hashed):
        pass

    svc.user_repo = SimpleNamespace(
        get_by_id=lambda uid: user,
        set_blocked=set_blocked,
        set_password=set_password,
        soft_delete=lambda u: None,
        bump_token_version=bump_token_version,
        # update_user() path
        update=lambda u, data: u,
        email_exists=lambda email: False,
        phone_exists=lambda phone: False,
    )
    svc.master_repo = SimpleNamespace(
        get_by_user_id=lambda uid: None,
        soft_delete=lambda master: None,
    )
    svc.session_repo = SimpleNamespace(
        delete_all_for_user=lambda uid: calls.__setitem__("sessions_revoked_for", uid),
    )
    svc._calls = calls
    return svc


class TestSetBlocked:
    def test_blocking_revokes_all_sessions(self):
        user = make_fake_user()
        svc = make_service(user=user)
        svc.set_blocked(USER_ID, True, requesting_admin_id=ADMIN_ID)
        assert svc._calls["bumped"] is True
        assert svc._calls["sessions_revoked_for"] == USER_ID

    def test_unblocking_does_not_revoke_sessions(self):
        user = make_fake_user(is_blocked=True)
        svc = make_service(user=user)
        svc.set_blocked(USER_ID, False, requesting_admin_id=ADMIN_ID)
        assert svc._calls["bumped"] is False
        assert svc._calls["sessions_revoked_for"] is None


class TestUpdateUserForcedPasswordChange:
    def test_new_password_revokes_all_sessions(self):
        user = make_fake_user()
        svc = make_service(user=user)
        svc.update_user(USER_ID, AdminUserUpdate(new_password="new-secret-pw"))
        assert svc._calls["bumped"] is True
        assert svc._calls["sessions_revoked_for"] == USER_ID

    def test_no_password_change_does_not_revoke_sessions(self):
        user = make_fake_user()
        svc = make_service(user=user)
        svc.update_user(USER_ID, AdminUserUpdate(first_name="Пётр"))
        assert svc._calls["bumped"] is False
        assert svc._calls["sessions_revoked_for"] is None


class TestDeleteUser:
    def test_soft_delete_revokes_all_sessions(self):
        user = make_fake_user()
        svc = make_service(user=user)
        svc.delete_user(USER_ID)
        assert svc._calls["bumped"] is True
        assert svc._calls["sessions_revoked_for"] == USER_ID
