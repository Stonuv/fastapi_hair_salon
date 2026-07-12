"""AdminService.create_master_profile() — реактивация вместо блокировки при
повторном назначении роли master. Фейковый репозиторий, без БД."""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import UserRole
from app.services.admin_service import AdminService

USER_ID = uuid.uuid4()


def make_fake_user(role=UserRole.master):
    return SimpleNamespace(
        id=USER_ID, role=role, email="master@example.com", first_name="Иван",
        last_name="Иванов", phone=None, is_blocked=False,
        created_at=datetime.now(timezone.utc),
    )


def make_fake_master(*, is_active):
    return SimpleNamespace(
        id=uuid.uuid4(), user=make_fake_user(), specialization=None,
        photo_url=None, coefficient=1.0, is_active=is_active,
    )


def make_service(*, existing_master=None, create_result=None):
    svc = AdminService.__new__(AdminService)
    svc.user_repo = SimpleNamespace(get_by_id=lambda uid: make_fake_user())

    calls = {"create": False, "reactivate": None}

    def create(uid):
        calls["create"] = True
        return create_result

    def reactivate(master):
        calls["reactivate"] = master
        master.is_active = True
        return master

    svc.master_repo = SimpleNamespace(
        get_by_user_id=lambda uid: existing_master,
        create=create,
        reactivate=reactivate,
        get_by_id=lambda mid: create_result if create_result else existing_master,
    )
    svc._calls = calls
    return svc


class TestCreateMasterProfile:
    def test_creates_new_when_none_exists(self):
        created = make_fake_master(is_active=True)
        svc = make_service(existing_master=None, create_result=created)
        result = svc.create_master_profile(USER_ID)
        assert svc._calls["create"] is True
        assert svc._calls["reactivate"] is None
        assert result.is_active is True

    def test_rejects_when_active_profile_already_exists(self):
        existing = make_fake_master(is_active=True)
        svc = make_service(existing_master=existing)
        with pytest.raises(HTTPException) as exc:
            svc.create_master_profile(USER_ID)
        assert exc.value.status_code == 409

    def test_reactivates_deactivated_profile_instead_of_blocking(self):
        """Regression: change_role() only deactivates (is_active=False), never
        deletes — a stale inactive Master row must not permanently block
        re-promoting the same user, forcing account recreation."""
        existing = make_fake_master(is_active=False)
        svc = make_service(existing_master=existing)
        result = svc.create_master_profile(USER_ID)
        assert svc._calls["reactivate"] is existing
        assert svc._calls["create"] is False
        assert result.is_active is True
