"""Пароли и RBAC-зависимости — без БД."""
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.enums import UserRole
from app.repositories._query_utils import escape_like
from app.services.auth_service import (AuthService, _hash_token,
                                       _verify_password, hash_password,
                                       require_role)


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


class _FakeDb:
    """Достаточно add/flush/refresh — ровно то, что использует
    SessionRepository.create() внутри create_session()."""

    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        pass

    def refresh(self, obj):
        pass


def make_auth_service(*, session=None, user=None):
    svc = AuthService.__new__(AuthService)
    svc.db = _FakeDb()
    calls = {"deleted_by_hash": None, "deleted_session": None}

    svc.session_repo = SimpleNamespace(
        get_valid_by_hash=lambda token_hash: session,
        delete_by_hash=lambda token_hash: calls.__setitem__("deleted_by_hash", token_hash),
        delete=lambda sess: calls.__setitem__("deleted_session", sess),
    )
    svc.user_repo = SimpleNamespace(get_by_id=lambda uid: user)
    svc._calls = calls
    return svc


class TestLogout:
    """logout() отзывает ровно текущую сессию по refresh-токену устройства,
    а не все сессии пользователя разом (см. models/session.py)."""

    def test_deletes_session_matching_current_refresh_token(self):
        svc = make_auth_service()
        svc.logout("raw-refresh-token")
        assert svc._calls["deleted_by_hash"] == _hash_token("raw-refresh-token")

    def test_noop_without_refresh_token(self):
        svc = make_auth_service()
        svc.logout(None)
        assert svc._calls["deleted_by_hash"] is None


class TestRefreshSession:
    def _user(self, is_blocked=False):
        import datetime as _dt
        return SimpleNamespace(
            id=uuid.uuid4(), email="client@example.com", first_name="Иван",
            last_name="Иванов", phone=None, role=UserRole.client,
            is_blocked=is_blocked, token_version=0,
            created_at=_dt.datetime.now(_dt.timezone.utc),
        )

    def _session(self, user_id):
        return SimpleNamespace(id=uuid.uuid4(), user_id=user_id, token_hash="x")

    def test_raises_401_when_session_not_found(self):
        svc = make_auth_service(session=None)
        with pytest.raises(HTTPException) as exc:
            svc.refresh_session("stale-or-unknown-token")
        assert exc.value.status_code == 401
        assert svc._calls["deleted_session"] is None

    def test_rotates_session_and_returns_new_refresh_token(self):
        """Успешный refresh удаляет старую сессию и создаёт новую — старый
        refresh-токен становится одноразовым (защита от повторного использования)."""
        user = self._user()
        session = self._session(user.id)
        svc = make_auth_service(session=session, user=user)
        token_response, new_raw_token = svc.refresh_session("current-refresh-token")
        assert svc._calls["deleted_session"] is session
        assert token_response.user.id == user.id
        assert isinstance(new_raw_token, str) and new_raw_token
        assert len(svc.db.added) == 1
        assert svc.db.added[0].user_id == user.id
        assert svc.db.added[0].token_hash == _hash_token(new_raw_token)

    def test_raises_401_and_deletes_session_when_user_blocked(self):
        user = self._user(is_blocked=True)
        session = self._session(user.id)
        svc = make_auth_service(session=session, user=user)
        with pytest.raises(HTTPException) as exc:
            svc.refresh_session("current-refresh-token")
        assert exc.value.status_code == 401
        assert svc._calls["deleted_session"] is session
        assert svc.db.added == []

    def test_raises_401_and_deletes_session_when_user_missing(self):
        """Пользователь удалён между выдачей refresh-токена и его
        использованием — сессия не должна пережить это."""
        session = self._session(uuid.uuid4())
        svc = make_auth_service(session=session, user=None)
        with pytest.raises(HTTPException) as exc:
            svc.refresh_session("current-refresh-token")
        assert exc.value.status_code == 401
        assert svc._calls["deleted_session"] is session


class TestEscapeLike:
    def test_percent_and_underscore_escaped(self):
        assert escape_like("100%_x") == r"100\%\_x"

    def test_backslash_escaped_first(self):
        assert escape_like("a\\b") == "a\\\\b"

    def test_plain_string_unchanged(self):
        assert escape_like("Иван") == "Иван"
