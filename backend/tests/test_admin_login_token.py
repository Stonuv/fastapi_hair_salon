"""Второй фактор админ-панели (ADMIN_LOGIN_TOKEN) — без БД.

Проверяется главное свойство: код спрашивается только у owner/admin и только
когда он задан на сервере, а неверный код неотличим по последствиям от
неверного пароля (та же запись о неудачной попытке, та же блокировка перебора).
"""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.config import settings
from app.models.enums import UserRole
from app.services.auth_service import (AuthService, admin_login_token_required,
                                       admin_token_accepted, hash_password)

PASSWORD = "correct-horse-battery"
TOKEN = "s3cret-admin-code"


@pytest.fixture
def admin_token(monkeypatch):
    monkeypatch.setattr(settings, "admin_login_token", TOKEN)
    return TOKEN


@pytest.fixture
def no_admin_token(monkeypatch):
    monkeypatch.setattr(settings, "admin_login_token", None)


def make_user(role: UserRole):
    return SimpleNamespace(
        id=uuid.uuid4(), email="owner@example.com", role=role,
        password_hash=hash_password(PASSWORD), is_blocked=False, token_version=1,
        first_name="О", last_name="В", phone=None, email_verified=True,
        created_at=datetime.now(timezone.utc), salon=None,
    )


def make_service(user):
    """AuthService с фейковыми репозиториями; журнал попыток пишется в список,
    чтобы проверить, что неудача с кодом в него попадает."""
    svc = AuthService.__new__(AuthService)
    svc.db = SimpleNamespace(commit=lambda: None)
    svc.user_repo = SimpleNamespace(get_by_email=lambda email: user)
    svc.attempts = []
    svc.login_attempt_repo = SimpleNamespace(
        count_recent_failed=lambda email, window_start: 0,
        create=lambda **kwargs: svc.attempts.append(kwargs),
    )
    return svc


class TestAdminTokenAccepted:
    def test_not_configured_accepts_everyone(self, no_admin_token):
        assert admin_login_token_required() is False
        for role in UserRole:
            assert admin_token_accepted(role, None) is True

    def test_configured_but_role_is_not_admin(self, admin_token):
        assert admin_login_token_required() is True
        assert admin_token_accepted(UserRole.client, None) is True
        assert admin_token_accepted(UserRole.master, None) is True

    def test_configured_admin_roles_need_the_code(self, admin_token):
        for role in (UserRole.owner, UserRole.admin):
            assert admin_token_accepted(role, None) is False
            assert admin_token_accepted(role, "") is False
            assert admin_token_accepted(role, "wrong") is False
            assert admin_token_accepted(role, TOKEN) is True

    def test_prefix_of_the_code_is_not_enough(self, admin_token):
        # compare_digest, а не startswith/==: частичное совпадение не проходит
        assert admin_token_accepted(UserRole.owner, TOKEN[:-1]) is False
        assert admin_token_accepted(UserRole.owner, TOKEN + "x") is False


class TestLoginWithAdminToken:
    def test_owner_without_code_gets_401(self, admin_token):
        svc = make_service(make_user(UserRole.owner))
        with pytest.raises(HTTPException) as exc:
            svc.login("owner@example.com", PASSWORD)
        assert exc.value.status_code == 401

    def test_owner_with_wrong_code_gets_401(self, admin_token):
        svc = make_service(make_user(UserRole.owner))
        with pytest.raises(HTTPException) as exc:
            svc.login("owner@example.com", PASSWORD, admin_token="wrong")
        assert exc.value.status_code == 401

    def test_failed_code_is_logged_as_failed_attempt(self, admin_token):
        """Иначе код можно было бы перебирать мимо блокировки: она считает
        именно неудачные записи в login_attempts."""
        svc = make_service(make_user(UserRole.owner))
        with pytest.raises(HTTPException):
            svc.login("owner@example.com", PASSWORD, admin_token="wrong")
        assert len(svc.attempts) == 1
        assert svc.attempts[0]["success"] is False

    def test_owner_with_correct_code_logs_in(self, admin_token):
        svc = make_service(make_user(UserRole.owner))
        result = svc.login("owner@example.com", PASSWORD, admin_token=TOKEN)
        assert result.access_token
        assert svc.attempts[0]["success"] is True

    def test_client_does_not_need_the_code(self, admin_token):
        svc = make_service(make_user(UserRole.client))
        assert svc.login("owner@example.com", PASSWORD).access_token

    def test_without_configured_token_owner_logs_in_as_before(self, no_admin_token):
        """Совместимость: сервер без ADMIN_LOGIN_TOKEN работает как раньше."""
        svc = make_service(make_user(UserRole.owner))
        assert svc.login("owner@example.com", PASSWORD).access_token

    def test_wrong_password_wins_over_the_code(self, admin_token):
        """Верный код не должен подсказывать, что пароль неверен: 401 тот же."""
        svc = make_service(make_user(UserRole.owner))
        with pytest.raises(HTTPException) as exc:
            svc.login("owner@example.com", "wrong-password", admin_token=TOKEN)
        assert exc.value.status_code == 401
        assert exc.value.detail == "Неверный email или пароль"
