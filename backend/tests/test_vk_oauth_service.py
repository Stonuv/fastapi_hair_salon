"""VK ID OAuth (PKCE) — без сети и БД: фейковый репозиторий + httpx.post."""
import base64
import hashlib
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services import vk_oauth_service as vk_module
from app.services.vk_oauth_service import (VkOAuthError, VkOAuthService,
                                           build_authorize_url,
                                           generate_pkce, is_enabled)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def make_fake_user(**overrides):
    defaults = dict(
        id=uuid.uuid4(), email="client@example.com", first_name="Иван", last_name="Иванов",
        phone=None, role="client", vk_user_id=None, is_blocked=False, token_version=0,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_service(*, by_vk_id=None, by_email=None, created=None, linked=None):
    svc = VkOAuthService.__new__(VkOAuthService)
    calls = {"create": None, "link": None}

    def create_vk_oauth_user(**kwargs):
        calls["create"] = kwargs
        return created

    def link_vk_id(user, vk_user_id):
        calls["link"] = (user, vk_user_id)
        return linked or user

    svc.user_repo = SimpleNamespace(
        get_by_vk_id=lambda vk_id: by_vk_id,
        get_by_email=lambda email: by_email,
        create_vk_oauth_user=create_vk_oauth_user,
        link_vk_id=link_vk_id,
    )
    svc._calls = calls
    return svc


def patch_http(monkeypatch, *, token_payload, user_payload):
    def fake_post(url, data=None, timeout=None):
        if url == vk_module._TOKEN_URL:
            return FakeResponse(token_payload)
        if url == vk_module._USER_INFO_URL:
            return FakeResponse({"user": user_payload})
        raise AssertionError(f"unexpected URL {url}")
    monkeypatch.setattr(vk_module.httpx, "post", fake_post)


class TestIsEnabled:
    def test_false_without_client_id(self, monkeypatch):
        monkeypatch.setattr(vk_module.settings, "vk_client_id", None)
        assert is_enabled() is False

    def test_true_with_client_id(self, monkeypatch):
        monkeypatch.setattr(vk_module.settings, "vk_client_id", "abc123")
        assert is_enabled() is True


class TestPkce:
    def test_challenge_matches_verifier_sha256(self):
        verifier, challenge = generate_pkce()
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).rstrip(b"=").decode()
        assert challenge == expected

    def test_verifier_has_no_padding_or_unsafe_chars(self):
        verifier, challenge = generate_pkce()
        assert len(verifier) >= 43
        assert not any(c in verifier + challenge for c in "+/=")


class TestBuildAuthorizeUrl:
    def test_contains_required_params(self, monkeypatch):
        monkeypatch.setattr(vk_module.settings, "vk_client_id", "client-1")
        monkeypatch.setattr(vk_module.settings, "vk_redirect_uri",
                            "http://localhost:8000/api/auth/vk/callback")
        url = build_authorize_url("state-1", "challenge-1")
        assert url.startswith("https://id.vk.com/authorize?")
        assert "client_id=client-1" in url
        assert "state=state-1" in url
        assert "code_challenge=challenge-1" in url
        assert "code_challenge_method=S256" in url
        assert "scope=email" in url


class TestHandleCallback:
    def test_existing_vk_user_logs_in_directly(self, monkeypatch):
        existing = make_fake_user(vk_user_id="vk-1")
        patch_http(monkeypatch, token_payload={"access_token": "tok", "user_id": "vk-1"},
                  user_payload={"email": "client@example.com", "first_name": "Иван", "last_name": "Иванов"})
        svc = make_service(by_vk_id=existing)
        res = svc.handle_callback(code="c", code_verifier="v", device_id="d")
        assert res.user.email == "client@example.com"
        assert svc._calls["create"] is None
        assert svc._calls["link"] is None

    def test_links_existing_email_account(self, monkeypatch):
        existing = make_fake_user(vk_user_id=None)
        patch_http(monkeypatch, token_payload={"access_token": "tok", "user_id": "vk-2"},
                  user_payload={"email": "client@example.com", "first_name": "Иван", "last_name": "Иванов"})
        svc = make_service(by_vk_id=None, by_email=existing, linked=existing)
        res = svc.handle_callback(code="c", code_verifier="v", device_id="d")
        assert svc._calls["link"] == (existing, "vk-2")
        assert svc._calls["create"] is None
        assert res.user.email == "client@example.com"

    def test_creates_new_user_when_no_match(self, monkeypatch):
        created = make_fake_user(vk_user_id="vk-3", email="new@example.com")
        patch_http(monkeypatch, token_payload={"access_token": "tok", "user_id": "vk-3"},
                  user_payload={"email": "new@example.com", "first_name": "Пётр", "last_name": "Петров"})
        svc = make_service(by_vk_id=None, by_email=None, created=created)
        res = svc.handle_callback(code="c", code_verifier="v", device_id="d")
        assert svc._calls["create"]["email"] == "new@example.com"
        assert res.user.email == "new@example.com"

    def test_raises_when_vk_account_has_no_email(self, monkeypatch):
        patch_http(monkeypatch, token_payload={"access_token": "tok", "user_id": "vk-4"},
                  user_payload={"first_name": "Без", "last_name": "Почты"})
        svc = make_service(by_vk_id=None, by_email=None)
        with pytest.raises(VkOAuthError) as exc:
            svc.handle_callback(code="c", code_verifier="v", device_id="d")
        assert exc.value.error_code == "vk_email_required"

    def test_raises_when_token_response_missing_fields(self, monkeypatch):
        patch_http(monkeypatch, token_payload={}, user_payload={})
        svc = make_service()
        with pytest.raises(VkOAuthError) as exc:
            svc.handle_callback(code="c", code_verifier="v", device_id="d")
        assert exc.value.error_code == "vk_token_exchange_failed"

    def test_raises_for_blocked_account(self, monkeypatch):
        existing = make_fake_user(vk_user_id="vk-5", is_blocked=True)
        patch_http(monkeypatch, token_payload={"access_token": "tok", "user_id": "vk-5"},
                  user_payload={"email": "client@example.com"})
        svc = make_service(by_vk_id=existing)
        with pytest.raises(VkOAuthError) as exc:
            svc.handle_callback(code="c", code_verifier="v", device_id="d")
        assert exc.value.error_code == "account_blocked"
