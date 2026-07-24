"""AuthService email-verification methods — фейковые репозитории, без БД."""
import datetime as _dt
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.config import settings
from app.models.enums import UserRole
from app.services import auth_service as auth_service_module
from app.services.auth_service import AuthService, _hash_token


def make_user(**overrides):
    # Полный набор полей UserResponse — register()/update_profile() в конце
    # прогоняют пользователя через build_token_response -> UserResponse.model_validate.
    defaults = {
        "id": uuid.uuid4(), "email": "client@example.com", "first_name": "Иван",
        "last_name": "Иванов", "phone": None, "role": UserRole.client, "is_blocked": False,
        "token_version": 0, "created_at": _dt.datetime.now(_dt.timezone.utc),
        "email_verified_at": None,
    }
    defaults.update(overrides)
    user = SimpleNamespace(**defaults)
    # email_verified — @property на реальной модели User; на SimpleNamespace
    # выставляем явно тем же значением.
    user.email_verified = user.email_verified_at is not None
    return user


def make_service(*, user=None, count_since=0, valid_token=None):
    svc = AuthService.__new__(AuthService)
    svc.db = SimpleNamespace(commit=lambda: None)
    calls = {"invalidated": [], "created": [], "marked_used": [], "verified": None}

    svc.verification_token_repo = SimpleNamespace(
        count_created_since=lambda user_id, since: count_since,
        invalidate_all_for_user=lambda user_id: calls["invalidated"].append(user_id),
        create=lambda user_id, token_hash, expires_at: calls["created"].append(
            (user_id, token_hash, expires_at)
        ),
        get_valid_by_hash=lambda token_hash: valid_token,
        mark_used=lambda token: calls["marked_used"].append(token),
    )
    svc.user_repo = SimpleNamespace(
        get_by_id=lambda uid: user if user and user.id == uid else None,
        set_email_verified_at=lambda u, value: calls.__setitem__("verified", (u, value)) or u,
    )
    svc._calls = calls
    return svc


class TestSendVerificationEmail:
    def test_noop_when_no_email(self, monkeypatch):
        sent = []
        monkeypatch.setattr(auth_service_module, "send_email", lambda **kw: sent.append(kw))
        svc = make_service()
        user = make_user(email=None)
        svc.send_verification_email(user)
        assert sent == []
        assert svc._calls["created"] == []

    def test_sends_email_and_creates_token(self, monkeypatch):
        sent = []
        monkeypatch.setattr(auth_service_module, "send_email", lambda **kw: sent.append(kw))
        svc = make_service()
        user = make_user()
        svc.send_verification_email(user)

        assert len(sent) == 1
        assert sent[0]["to"] == user.email
        assert "подтвердите" in sent[0]["subject"].lower() or "email" in sent[0]["subject"].lower()
        assert svc._calls["invalidated"] == [user.id]
        assert len(svc._calls["created"]) == 1
        created_user_id, token_hash, _expires_at = svc._calls["created"][0]
        assert created_user_id == user.id
        # В письме должна быть ссылка ровно с тем токеном, чей хеш ушёл в БД —
        # иначе письмо со ссылкой, которая никогда не подтвердится.
        link = sent[0]["text_body"]
        assert "token=" in link
        raw_token = link.split("token=")[1].split()[0].split("\n")[0]
        assert _hash_token(raw_token) == token_hash

    def test_noop_when_rate_limited(self, monkeypatch):
        sent = []
        monkeypatch.setattr(auth_service_module, "send_email", lambda **kw: sent.append(kw))
        svc = make_service(count_since=settings.email_verification_max_requests_per_hour)
        svc.send_verification_email(make_user())
        assert sent == []
        assert svc._calls["created"] == []


class TestResendVerificationEmail:
    def test_raises_400_when_no_email(self, monkeypatch):
        svc = make_service()
        with pytest.raises(HTTPException) as exc:
            svc.resend_verification_email(make_user(email=None))
        assert exc.value.status_code == 400

    def test_raises_400_when_already_verified(self, monkeypatch):
        svc = make_service()
        user = make_user(email_verified_at=_dt.datetime.now(_dt.timezone.utc))
        with pytest.raises(HTTPException) as exc:
            svc.resend_verification_email(user)
        assert exc.value.status_code == 400

    def test_raises_429_when_rate_limited(self, monkeypatch):
        svc = make_service(count_since=settings.email_verification_max_requests_per_hour)
        with pytest.raises(HTTPException) as exc:
            svc.resend_verification_email(make_user())
        assert exc.value.status_code == 429

    def test_sends_when_ok(self, monkeypatch):
        sent = []
        monkeypatch.setattr(auth_service_module, "send_email", lambda **kw: sent.append(kw))
        svc = make_service()
        svc.resend_verification_email(make_user())
        assert len(sent) == 1


class TestConfirmEmailVerification:
    def test_raises_400_when_token_invalid_or_expired(self):
        svc = make_service(valid_token=None)
        with pytest.raises(HTTPException) as exc:
            svc.confirm_email_verification("stale-or-unknown-token")
        assert exc.value.status_code == 400

    def test_raises_400_when_user_missing(self):
        token = SimpleNamespace(user_id=uuid.uuid4())
        svc = make_service(user=None, valid_token=token)
        with pytest.raises(HTTPException) as exc:
            svc.confirm_email_verification("some-token")
        assert exc.value.status_code == 400

    def test_marks_user_verified_and_token_used(self):
        user = make_user()
        token = SimpleNamespace(user_id=user.id)
        svc = make_service(user=user, valid_token=token)
        svc.confirm_email_verification("valid-token")

        verified_user, verified_value = svc._calls["verified"]
        assert verified_user is user
        assert verified_value is not None
        assert svc._calls["marked_used"] == [token]


class TestRegisterSendsVerificationEmail:
    """register() должен разослать письмо подтверждения новому аккаунту —
    без разговора о полном пайплайне отправки (см. TestSendVerificationEmail
    выше), только сам факт вызова с правильным пользователем."""

    def _service(self, created_user):
        svc = AuthService.__new__(AuthService)
        svc.db = SimpleNamespace()
        svc.user_repo = SimpleNamespace(
            email_exists=lambda email: False,
            phone_exists=lambda phone: False,
            create=lambda data, password_hash: created_user,
        )
        sent = []
        svc.send_verification_email = lambda user: sent.append(user)
        svc._sent = sent
        return svc

    def test_sends_verification_email_to_new_user(self):
        from app.schemas.user import UserCreate
        user = make_user()
        svc = self._service(user)
        data = UserCreate(email="client@example.com", first_name="Иван",
                          last_name="Иванов", password="password123")
        svc.register(data)
        assert svc._sent == [user]


class TestUpdateProfileEmailChangeSendsVerification:
    """Смена email в профиле обязана сбросить подтверждение (см.
    UserRepository.set_email) и заново отправить письмо — новый адрес не
    доказан, даже если старый уже был подтверждён."""

    def _service(self, user, updated_user):
        svc = AuthService.__new__(AuthService)
        svc.db = SimpleNamespace()
        svc.user_repo = SimpleNamespace(
            email_exists=lambda email: False,
            phone_exists=lambda phone: False,
            set_email=lambda u, email: updated_user,
        )
        sent = []
        svc.send_verification_email = lambda user: sent.append(user)
        svc._sent = sent
        return svc

    def test_email_change_triggers_new_verification_email(self):
        from app.schemas.user import UserUpdate
        user = make_user(email="old@example.com")
        updated_user = make_user(id=user.id, email="new@example.com")
        svc = self._service(user, updated_user)
        svc.update_profile(user, UserUpdate(email="new@example.com"))
        assert svc._sent == [updated_user]

    def test_unrelated_field_change_does_not_send_email(self):
        from app.schemas.user import UserUpdate
        user = make_user(email="old@example.com")
        svc = AuthService.__new__(AuthService)
        svc.db = SimpleNamespace()
        svc.user_repo = SimpleNamespace(
            phone_exists=lambda phone: False,
            update=lambda u, data: user,
        )
        sent = []
        svc.send_verification_email = lambda u: sent.append(u)
        svc.update_profile(user, UserUpdate(first_name="Пётр"))
        assert sent == []
