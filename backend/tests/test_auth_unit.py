"""Пароли и RBAC-зависимости — без БД."""
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import UserRole
from app.repositories._query_utils import escape_like
from app.services.auth_service import (AuthService, _verify_password,
                                       hash_password, require_role)


class TestPasswordHashing:
    def test_roundtrip(self):
        hashed = hash_password("secret-password")
        assert _verify_password("secret-password", hashed)
        assert not _verify_password("wrong-password", hashed)

    def test_over_72_bytes_returns_false_instead_of_raising(self):
        # bcrypt 5.x бросает ValueError на >72 байта — логин обязан вернуть
        # «неверный пароль», а не 500
        hashed = hash_password("secret-password")
        assert _verify_password("x" * 100, hashed) is False


class TestRequireRole:
    def _user(self, role: UserRole):
        return SimpleNamespace(role=role)

    def test_allowed_role_passes(self):
        dep = require_role(UserRole.master, UserRole.admin)
        user = self._user(UserRole.master)
        assert dep(current_user=user) is user

    def test_admin_passes_where_included(self):
        dep = require_role(UserRole.client, UserRole.admin)
        assert dep(current_user=self._user(UserRole.admin))

    def test_forbidden_role_raises_403(self):
        dep = require_role(UserRole.admin)
        with pytest.raises(HTTPException) as exc:
            dep(current_user=self._user(UserRole.client))
        assert exc.value.status_code == 403


class TestLoginOAuthOnlyAccount:
    """VK ID-аккаунты не имеют password_hash — login() обязан отклонить
    попытку входа по паролю тем же 401, что и "пользователь не найден",
    а не упасть на bcrypt.checkpw(None)."""

    def _service(self, user):
        svc = AuthService.__new__(AuthService)
        svc.db = SimpleNamespace(commit=lambda: None)
        svc.user_repo = SimpleNamespace(get_by_email=lambda email: user)
        svc.login_attempt_repo = SimpleNamespace(
            count_recent_failed=lambda email, window_start: 0,
            create=lambda **kwargs: None,
        )
        return svc

    def test_rejects_with_401_instead_of_raising(self):
        user = SimpleNamespace(id=uuid.uuid4(), email="vk-user@example.com",
                               password_hash=None, is_blocked=False)
        svc = self._service(user)
        with pytest.raises(HTTPException) as exc:
            svc.login("vk-user@example.com", "any-password")
        assert exc.value.status_code == 401


class TestEscapeLike:
    def test_percent_and_underscore_escaped(self):
        assert escape_like("100%_x") == r"100\%\_x"

    def test_backslash_escaped_first(self):
        assert escape_like("a\\b") == "a\\\\b"

    def test_plain_string_unchanged(self):
        assert escape_like("Иван") == "Иван"
