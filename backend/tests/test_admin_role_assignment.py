"""AdminService.create_user/change_role/assign_salon — сетевая иерархия
ролей (ROADMAP.md §4.10 Фаза B). Назначать admin/owner может только owner —
без этой проверки salon-admin мог бы выдать owner себе или кому угодно
(захват всей сети, см. §4.8). Фейковые репозитории, без БД."""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import UserRole
from app.schemas.user import AdminUserCreate
from app.services.admin_service import AdminService

TARGET_ID = uuid.uuid4()
SALON_ID = uuid.uuid4()


def make_requesting_admin():
    return SimpleNamespace(role=UserRole.admin, salon_id=SALON_ID)


def make_requesting_owner():
    return SimpleNamespace(role=UserRole.owner, salon_id=None)


def make_fake_user(*, role=UserRole.client, salon_id=None):
    return SimpleNamespace(
        id=TARGET_ID, role=role, salon_id=salon_id, email="user@example.com",
        first_name="Иван", last_name="Иванов", phone=None, is_blocked=False,
        created_at=datetime.now(timezone.utc),
    )


def make_service(*, target_user=None, known_salon_ids=frozenset()):
    svc = AdminService.__new__(AdminService)

    def set_role(user, role):
        user.role = role
        return user

    def set_salon(user, salon_id):
        user.salon_id = salon_id
        return user

    svc.user_repo = SimpleNamespace(
        get_by_id=lambda uid: target_user,
        set_role=set_role,
        set_salon=set_salon,
        email_exists=lambda email: False,
        phone_exists=lambda phone: False,
        create=lambda data, pw_hash, role: make_fake_user(role=role),
    )
    svc.master_repo = SimpleNamespace(get_by_user_id=lambda uid: None)
    svc.salon_repo = SimpleNamespace(
        get_by_id=lambda sid: SimpleNamespace(id=sid) if sid in known_salon_ids else None,
    )
    return svc


def make_create_data(role: UserRole) -> AdminUserCreate:
    return AdminUserCreate(email="new@example.com", first_name="Пётр", last_name="Петров",
                           password="StrongPass123!", role=role)


class TestCreateUserRoleGuard:
    def test_admin_can_create_client(self):
        svc = make_service()
        result = svc.create_user(make_create_data(UserRole.client), make_requesting_admin())
        assert result.role == UserRole.client

    def test_admin_cannot_create_admin(self):
        svc = make_service()
        with pytest.raises(HTTPException) as exc:
            svc.create_user(make_create_data(UserRole.admin), make_requesting_admin())
        assert exc.value.status_code == 403

    def test_admin_cannot_create_owner(self):
        svc = make_service()
        with pytest.raises(HTTPException) as exc:
            svc.create_user(make_create_data(UserRole.owner), make_requesting_admin())
        assert exc.value.status_code == 403

    def test_owner_still_cannot_create_admin_directly(self):
        """role=admin требует salon_id (ck_users_admin_requires_salon), а
        AdminUserCreate его не задаёт — даже owner обязан пройти двухшаговый
        флоу (создать → назначить точку → повысить роль), см. change_role."""
        svc = make_service()
        with pytest.raises(HTTPException) as exc:
            svc.create_user(make_create_data(UserRole.admin), make_requesting_owner())
        assert exc.value.status_code == 400

    def test_owner_can_create_owner(self):
        """Технически разрешено на бэкенде — фронтенд сознательно не
        предлагает эту опцию в быстром дропдауне (ROADMAP.md §4.11)."""
        svc = make_service()
        result = svc.create_user(make_create_data(UserRole.owner), make_requesting_owner())
        assert result.role == UserRole.owner


class TestChangeRoleGuard:
    def test_admin_cannot_promote_to_admin(self):
        svc = make_service(target_user=make_fake_user())
        with pytest.raises(HTTPException) as exc:
            svc.change_role(TARGET_ID, UserRole.admin, make_requesting_admin())
        assert exc.value.status_code == 403

    def test_admin_can_promote_to_master(self):
        svc = make_service(target_user=make_fake_user())
        result = svc.change_role(TARGET_ID, UserRole.master, make_requesting_admin())
        assert result.role == UserRole.master

    def test_owner_promoting_to_admin_without_salon_is_rejected(self):
        svc = make_service(target_user=make_fake_user(salon_id=None))
        with pytest.raises(HTTPException) as exc:
            svc.change_role(TARGET_ID, UserRole.admin, make_requesting_owner())
        assert exc.value.status_code == 400

    def test_owner_promoting_to_admin_with_salon_already_set_succeeds(self):
        svc = make_service(target_user=make_fake_user(salon_id=SALON_ID))
        result = svc.change_role(TARGET_ID, UserRole.admin, make_requesting_owner())
        assert result.role == UserRole.admin


class TestAssignSalon:
    def test_sets_salon_on_existing_user(self):
        svc = make_service(target_user=make_fake_user(), known_salon_ids={SALON_ID})
        result = svc.assign_salon(TARGET_ID, SALON_ID)
        assert result.id == TARGET_ID

    def test_unknown_user_is_404(self):
        svc = make_service(target_user=None, known_salon_ids={SALON_ID})
        with pytest.raises(HTTPException) as exc:
            svc.assign_salon(TARGET_ID, SALON_ID)
        assert exc.value.status_code == 404

    def test_unknown_salon_is_404(self):
        svc = make_service(target_user=make_fake_user(), known_salon_ids=set())
        with pytest.raises(HTTPException) as exc:
            svc.assign_salon(TARGET_ID, SALON_ID)
        assert exc.value.status_code == 404
