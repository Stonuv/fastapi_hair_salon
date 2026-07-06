"""Первичная настройка (создание первого админа) — без БД, фейковый репозиторий."""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import UserRole
from app.schemas.setup import SetupRequest
from app.schemas.user import UserCreate
from app.services import setup_service as setup_service_module
from app.services.setup_service import SetupService


def make_service(*, admin_exists=False, email_exists=False, phone_exists=False, create_result=None):
    svc = SetupService.__new__(SetupService)
    svc.db = None

    def create(*args, **kwargs):
        if create_result is None:
            raise AssertionError("create() must not be called when setup is rejected")
        return create_result

    svc.user_repo = SimpleNamespace(
        has_role=lambda role: admin_exists,
        email_exists=lambda email: email_exists,
        phone_exists=lambda phone: phone_exists,
        create=create,
    )
    return svc


def make_fake_user():
    return SimpleNamespace(
        id=uuid.uuid4(), email="owner@example.com", first_name="Иван", last_name="Иванов",
        phone=None, role=UserRole.admin, is_blocked=False, token_version=0,
        created_at=datetime.now(timezone.utc),
    )


def make_request(phone=None, setup_token=None):
    return SetupRequest(admin=UserCreate(
        email="owner@example.com", first_name="Иван", last_name="Иванов",
        phone=phone, password="supersecret",
    ), setup_token=setup_token)


class TestIsCompleted:
    def test_reflects_has_role(self):
        assert make_service(admin_exists=True).is_completed() is True
        assert make_service(admin_exists=False).is_completed() is False


class TestComplete:
    def test_rejects_when_admin_already_exists(self):
        svc = make_service(admin_exists=True)
        with pytest.raises(HTTPException) as exc:
            svc.complete(make_request())
        assert exc.value.status_code == 409

    def test_rejects_duplicate_email(self):
        svc = make_service(admin_exists=False, email_exists=True)
        with pytest.raises(HTTPException) as exc:
            svc.complete(make_request())
        assert exc.value.status_code == 409

    def test_rejects_duplicate_phone(self):
        svc = make_service(admin_exists=False, phone_exists=True)
        with pytest.raises(HTTPException) as exc:
            svc.complete(make_request(phone="+7 999 123-45-67"))
        assert exc.value.status_code == 409

    def test_succeeds_and_returns_token_when_no_admin_yet(self):
        svc = make_service(admin_exists=False, create_result=make_fake_user())
        res = svc.complete(make_request())
        assert res.user.role == UserRole.admin
        assert res.access_token


class TestSetupTokenGate:
    """SETUP_TOKEN (config.py) закрывает публичный /api/setup вне debug —
    без него первый, кто откроет /setup после деплоя, становится админом."""

    def test_requires_token_false_when_not_configured(self, monkeypatch):
        monkeypatch.setattr(setup_service_module.settings, "setup_token", None)
        assert make_service().requires_token() is False

    def test_requires_token_true_when_configured(self, monkeypatch):
        monkeypatch.setattr(setup_service_module.settings, "setup_token", "s3cr3t")
        assert make_service().requires_token() is True

    def test_rejects_missing_token_when_configured(self, monkeypatch):
        monkeypatch.setattr(setup_service_module.settings, "setup_token", "s3cr3t")
        svc = make_service(admin_exists=False)
        with pytest.raises(HTTPException) as exc:
            svc.complete(make_request(setup_token=None))
        assert exc.value.status_code == 403

    def test_rejects_wrong_token_when_configured(self, monkeypatch):
        monkeypatch.setattr(setup_service_module.settings, "setup_token", "s3cr3t")
        svc = make_service(admin_exists=False)
        with pytest.raises(HTTPException) as exc:
            svc.complete(make_request(setup_token="wrong"))
        assert exc.value.status_code == 403

    def test_accepts_correct_token(self, monkeypatch):
        monkeypatch.setattr(setup_service_module.settings, "setup_token", "s3cr3t")
        svc = make_service(admin_exists=False, create_result=make_fake_user())
        res = svc.complete(make_request(setup_token="s3cr3t"))
        assert res.access_token

    def test_token_not_required_when_not_configured(self, monkeypatch):
        monkeypatch.setattr(setup_service_module.settings, "setup_token", None)
        svc = make_service(admin_exists=False, create_result=make_fake_user())
        res = svc.complete(make_request(setup_token=None))
        assert res.access_token
