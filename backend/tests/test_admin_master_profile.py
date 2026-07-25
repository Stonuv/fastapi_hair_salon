"""AdminService.create_master_profile() — реактивация вместо блокировки при
повторном назначении роли master, плюс (ROADMAP.md §4.10 Фаза B) резолюция
salon_id по роли вызывающего. Фейковый репозиторий, без БД."""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import UserRole
from app.services.admin_service import AdminService

USER_ID = uuid.uuid4()
ADMIN_SALON_ID = uuid.uuid4()
OTHER_SALON_ID = uuid.uuid4()


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
        salon=SimpleNamespace(id=ADMIN_SALON_ID, name="Салон №1", slug="salon-1"),
    )


def make_requesting_admin(salon_id=ADMIN_SALON_ID):
    return SimpleNamespace(role=UserRole.admin, salon_id=salon_id)


def make_requesting_owner():
    return SimpleNamespace(role=UserRole.owner, salon_id=None)


def make_service(*, existing_master=None, create_result=None, known_salon_ids=frozenset()):
    svc = AdminService.__new__(AdminService)
    svc.user_repo = SimpleNamespace(get_by_id=lambda uid: make_fake_user())

    calls = {"create": False, "create_salon_id": None, "reactivate": None}

    def create(uid, salon_id):
        calls["create"] = True
        calls["create_salon_id"] = salon_id
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
    svc.salon_repo = SimpleNamespace(
        get_by_id=lambda sid: SimpleNamespace(id=sid) if sid in known_salon_ids else None,
    )
    svc._calls = calls
    return svc


class TestCreateMasterProfile:
    def test_creates_new_when_none_exists(self):
        created = make_fake_master(is_active=True)
        svc = make_service(existing_master=None, create_result=created)
        result = svc.create_master_profile(USER_ID, None, make_requesting_admin())
        assert svc._calls["create"] is True
        assert svc._calls["reactivate"] is None
        assert result.is_active is True

    def test_rejects_when_active_profile_already_exists(self):
        existing = make_fake_master(is_active=True)
        svc = make_service(existing_master=existing)
        with pytest.raises(HTTPException) as exc:
            svc.create_master_profile(USER_ID, None, make_requesting_admin())
        assert exc.value.status_code == 409

    def test_reactivates_deactivated_profile_instead_of_blocking(self):
        """Regression: change_role() only deactivates (is_active=False), never
        deletes — a stale inactive Master row must not permanently block
        re-promoting the same user, forcing account recreation."""
        existing = make_fake_master(is_active=False)
        svc = make_service(existing_master=existing)
        result = svc.create_master_profile(USER_ID, None, make_requesting_admin())
        assert svc._calls["reactivate"] is existing
        assert svc._calls["create"] is False
        assert result.is_active is True


class TestCreateMasterProfileSalonResolution:
    def test_admin_omitting_salon_id_defaults_to_own_salon(self):
        svc = make_service(create_result=make_fake_master(is_active=True))
        svc.create_master_profile(USER_ID, None, make_requesting_admin())
        assert svc._calls["create_salon_id"] == ADMIN_SALON_ID

    def test_admin_repeating_own_salon_id_is_allowed(self):
        svc = make_service(create_result=make_fake_master(is_active=True))
        svc.create_master_profile(USER_ID, ADMIN_SALON_ID, make_requesting_admin())
        assert svc._calls["create_salon_id"] == ADMIN_SALON_ID

    def test_admin_cannot_create_master_in_another_salon(self):
        svc = make_service(create_result=make_fake_master(is_active=True))
        with pytest.raises(HTTPException) as exc:
            svc.create_master_profile(USER_ID, OTHER_SALON_ID, make_requesting_admin())
        assert exc.value.status_code == 403
        assert svc._calls["create"] is False

    def test_owner_must_specify_salon_id(self):
        svc = make_service(create_result=make_fake_master(is_active=True))
        with pytest.raises(HTTPException) as exc:
            svc.create_master_profile(USER_ID, None, make_requesting_owner())
        assert exc.value.status_code == 400
        assert svc._calls["create"] is False

    def test_owner_specifying_unknown_salon_id_gets_404(self):
        svc = make_service(create_result=make_fake_master(is_active=True), known_salon_ids=set())
        with pytest.raises(HTTPException) as exc:
            svc.create_master_profile(USER_ID, OTHER_SALON_ID, make_requesting_owner())
        assert exc.value.status_code == 404
        assert svc._calls["create"] is False

    def test_owner_specifying_known_salon_id_is_used_as_is(self):
        svc = make_service(create_result=make_fake_master(is_active=True),
                           known_salon_ids={OTHER_SALON_ID})
        svc.create_master_profile(USER_ID, OTHER_SALON_ID, make_requesting_owner())
        assert svc._calls["create_salon_id"] == OTHER_SALON_ID
