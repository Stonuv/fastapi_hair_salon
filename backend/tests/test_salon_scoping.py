"""Salon-scoping (ROADMAP.md §4.8, Фаза C) — owner видит всю сеть или
выбранную точку, admin всегда только свою. Фейковые репозитории, без БД:
resolve_salon_scope и repository-level join'ы (UserRepository/ReviewRepository
salon_id) отдельно проверены на реальном Postgres, см. tests/integration/."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import AppointmentStatus, UserRole
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.master_repository import MasterRepository
from app.repositories.review_repository import ReviewRepository
from app.routes import masters as masters_module
from app.services._salon_scope import resolve_salon_scope
from app.services.appointment_service import AppointmentService
from app.services.review_service import ReviewService

SALON_A = uuid.uuid4()
SALON_B = uuid.uuid4()
MASTER_ID = uuid.uuid4()


class TestReviewServiceRealInit:
    def test_real_construction_wires_all_repos(self):
        """make_review_service() below builds ReviewService via __new__ +
        manual fakes, so it would never notice __init__ losing or misnaming a
        repo — only this test calls the real constructor (see project memory
        'test-fakes-bypass-init'). Also the only place in the automated
        suite that touches ReviewService's real __init__ at all — no
        integration test hits /api/reviews yet."""
        svc = ReviewService(db=None)
        assert isinstance(svc.review_repo, ReviewRepository)
        assert isinstance(svc.appointment_repo, AppointmentRepository)
        assert isinstance(svc.master_repo, MasterRepository)


def make_admin(salon_id=SALON_A):
    return SimpleNamespace(role=UserRole.admin, salon_id=salon_id, id=uuid.uuid4())


def make_owner():
    return SimpleNamespace(role=UserRole.owner, salon_id=None, id=uuid.uuid4())


# ── resolve_salon_scope ──────────────────────────────────────────


class TestResolveSalonScope:
    def test_owner_with_no_param_sees_whole_network(self):
        assert resolve_salon_scope(make_owner(), None) is None

    def test_owner_can_narrow_to_specific_salon(self):
        assert resolve_salon_scope(make_owner(), SALON_B) == SALON_B

    def test_admin_with_no_param_is_forced_to_own_salon(self):
        assert resolve_salon_scope(make_admin(), None) == SALON_A

    def test_admin_repeating_own_salon_id_is_allowed(self):
        assert resolve_salon_scope(make_admin(), SALON_A) == SALON_A

    def test_admin_requesting_another_salon_is_rejected(self):
        with pytest.raises(HTTPException) as exc:
            resolve_salon_scope(make_admin(), SALON_B)
        assert exc.value.status_code == 403


# ── _ensure_can_manage_master (routes/masters.py) ───────────────


def patch_master_repo(monkeypatch, *, by_id=None, by_user_id=None):
    monkeypatch.setattr(
        masters_module, "MasterRepository",
        lambda db: SimpleNamespace(get_by_id=lambda mid: by_id, get_by_user_id=lambda uid: by_user_id),
    )


class TestEnsureCanManageMaster:
    def test_owner_can_manage_any_master(self, monkeypatch):
        patch_master_repo(monkeypatch, by_id=None)  # даже "несуществующий" не важен для owner
        masters_module._ensure_can_manage_master(MASTER_ID, make_owner(), db=None)

    def test_admin_can_manage_master_of_own_salon(self, monkeypatch):
        patch_master_repo(monkeypatch, by_id=SimpleNamespace(salon_id=SALON_A))
        masters_module._ensure_can_manage_master(MASTER_ID, make_admin(salon_id=SALON_A), db=None)

    def test_admin_cannot_manage_master_of_other_salon(self, monkeypatch):
        patch_master_repo(monkeypatch, by_id=SimpleNamespace(salon_id=SALON_B))
        with pytest.raises(HTTPException) as exc:
            masters_module._ensure_can_manage_master(MASTER_ID, make_admin(salon_id=SALON_A), db=None)
        assert exc.value.status_code == 403

    def test_admin_gets_403_not_404_for_nonexistent_master(self, monkeypatch):
        """Не раскрываем существование мастера чужой точки — 403, как и mismatch."""
        patch_master_repo(monkeypatch, by_id=None)
        with pytest.raises(HTTPException) as exc:
            masters_module._ensure_can_manage_master(MASTER_ID, make_admin(), db=None)
        assert exc.value.status_code == 403

    def test_master_can_manage_own_profile(self, monkeypatch):
        own = SimpleNamespace(id=MASTER_ID)
        patch_master_repo(monkeypatch, by_user_id=own)
        master_user = SimpleNamespace(role=UserRole.master, salon_id=SALON_A, id=uuid.uuid4())
        masters_module._ensure_can_manage_master(MASTER_ID, master_user, db=None)

    def test_master_cannot_manage_other_profile(self, monkeypatch):
        patch_master_repo(monkeypatch, by_user_id=SimpleNamespace(id=uuid.uuid4()))
        master_user = SimpleNamespace(role=UserRole.master, salon_id=SALON_A, id=uuid.uuid4())
        with pytest.raises(HTTPException) as exc:
            masters_module._ensure_can_manage_master(MASTER_ID, master_user, db=None)
        assert exc.value.status_code == 403


# ── ReviewService moderation/delete salon scoping ───────────────


def make_review_service(*, master_salon_id=SALON_A):
    svc = ReviewService.__new__(ReviewService)
    review = SimpleNamespace(id=uuid.uuid4(), master_id=MASTER_ID, client_id=uuid.uuid4(),
                             is_published=True)
    svc.review_repo = SimpleNamespace(get_by_id=lambda rid: review, delete=lambda r: None)
    svc.master_repo = SimpleNamespace(
        get_by_id=lambda mid: SimpleNamespace(id=mid, salon_id=master_salon_id),
    )
    return svc, review


class TestReviewModerationScoping:
    """_ensure_can_moderate — тестируется напрямую, а не через moderate():
    та в конце сериализует полный ReviewResponse (все поля отзыва), что не
    относится к самой проверке прав. delete() не сериализует ничего — там
    можно и нужно гонять публичный метод целиком."""

    def test_owner_can_moderate_any_salon(self):
        svc, review = make_review_service(master_salon_id=SALON_B)
        svc._ensure_can_moderate(review, make_owner())

    def test_admin_can_moderate_review_of_own_salon(self):
        svc, review = make_review_service(master_salon_id=SALON_A)
        svc._ensure_can_moderate(review, make_admin(salon_id=SALON_A))

    def test_admin_cannot_moderate_review_of_other_salon(self):
        svc, review = make_review_service(master_salon_id=SALON_B)
        with pytest.raises(HTTPException) as exc:
            svc._ensure_can_moderate(review, make_admin(salon_id=SALON_A))
        assert exc.value.status_code == 403

    def test_admin_cannot_delete_review_of_other_salon(self):
        svc, review = make_review_service(master_salon_id=SALON_B)
        with pytest.raises(HTTPException) as exc:
            svc.delete(review.id, make_admin(salon_id=SALON_A))
        assert exc.value.status_code == 403

    def test_admin_can_delete_review_of_own_salon(self):
        svc, review = make_review_service(master_salon_id=SALON_A)
        svc.delete(review.id, make_admin(salon_id=SALON_A))

    def test_client_can_delete_own_review(self):
        svc, review = make_review_service()
        client = SimpleNamespace(role=UserRole.client, id=review.client_id)
        svc.delete(review.id, client)

    def test_client_cannot_delete_others_review(self):
        svc, review = make_review_service()
        other_client = SimpleNamespace(role=UserRole.client, id=uuid.uuid4())
        with pytest.raises(HTTPException) as exc:
            svc.delete(review.id, other_client)
        assert exc.value.status_code == 403


# ── AppointmentService.get_by_id salon tightening ───────────────


def make_fake_appointment_full(*, salon_id, client_id=None):
    """Полностью сформированный фейк — get_by_id() в конце сериализует
    AppointmentResponse целиком (client/master/service), не только права
    доступа (тот же паттерн, что make_fake_appointment в test_business_hours.py)."""
    client = SimpleNamespace(id=client_id or uuid.uuid4(), email="client@example.com",
                             first_name="Иван", last_name="Иванов", phone=None)
    master = SimpleNamespace(id=MASTER_ID, first_name="Пётр", last_name="Петров",
                             specialization=None, photo_url=None, coefficient=Decimal("1.00"))
    service = SimpleNamespace(id=uuid.uuid4(), name="Стрижка", description=None,
                              price=Decimal("1000.00"), duration_min=30, is_active=True)
    return SimpleNamespace(
        id=uuid.uuid4(), client_id=client.id, master_id=MASTER_ID, salon_id=salon_id,
        client=client, master=master, service=service,
        start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc),
        final_price=Decimal("1000.00"), status=AppointmentStatus.pending,
        created_at=datetime.now(timezone.utc),
    )


def make_appointment_service_for_get_by_id(*, salon_id=SALON_A, client_id=None):
    svc = AppointmentService.__new__(AppointmentService)
    appointment = make_fake_appointment_full(salon_id=salon_id, client_id=client_id)
    svc.appointment_repo = SimpleNamespace(get_by_id=lambda aid: appointment)
    svc.master_repo = SimpleNamespace(get_by_user_id=lambda uid: None)
    return svc, appointment


class TestAppointmentGetByIdScoping:
    def test_owner_sees_appointment_of_any_salon(self):
        svc, appointment = make_appointment_service_for_get_by_id(salon_id=SALON_B)
        svc.get_by_id(appointment.id, make_owner())

    def test_admin_sees_appointment_of_own_salon(self):
        svc, appointment = make_appointment_service_for_get_by_id(salon_id=SALON_A)
        svc.get_by_id(appointment.id, make_admin(salon_id=SALON_A))

    def test_admin_cannot_see_appointment_of_other_salon(self):
        """Regression (ROADMAP.md §4.8 Фаза C): раньше любой admin видел
        любую запись сети, независимо от точки."""
        svc, appointment = make_appointment_service_for_get_by_id(salon_id=SALON_B)
        with pytest.raises(HTTPException) as exc:
            svc.get_by_id(appointment.id, make_admin(salon_id=SALON_A))
        assert exc.value.status_code == 403

    def test_unrelated_client_is_rejected(self):
        svc, appointment = make_appointment_service_for_get_by_id()
        stranger = SimpleNamespace(role=UserRole.client, id=uuid.uuid4())
        with pytest.raises(HTTPException) as exc:
            svc.get_by_id(appointment.id, stranger)
        assert exc.value.status_code == 403
