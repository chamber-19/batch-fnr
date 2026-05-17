from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.core import auth


def _request() -> SimpleNamespace:
    return SimpleNamespace(state=SimpleNamespace())


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_valid_toolkit_bearer_returns_launcher_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACTIVATION_HMAC_SECRET", "secret")
    monkeypatch.delenv("DISABLE_AUTH", raising=False)
    monkeypatch.setattr(auth, "_TOOLKIT_AUTH_AVAILABLE", True)
    monkeypatch.setattr(
        auth,
        "verify_toolkit_bearer",
        lambda token: {"machine_id": "abcdef1234567890"},
    )

    request = _request()
    user = auth.require_auth(request, _creds("v1.abcdef1234567890.123.good"))

    assert user == {
        "email": "launcher+abcdef123456@chamber-19.internal",
        "name": "Launcher (abcdef123456)",
        "picture": "",
        "sub": "toolkit:abcdef1234567890",
        "auth_method": "toolkit_bearer",
    }
    assert request.state.user == user


def test_malformed_toolkit_bearer_hard_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACTIVATION_HMAC_SECRET", "secret")
    monkeypatch.delenv("DISABLE_AUTH", raising=False)
    monkeypatch.setattr(auth, "_TOOLKIT_AUTH_AVAILABLE", True)

    def reject(_token: str) -> dict:
        raise auth.ToolkitBearerError("bad signature")

    monkeypatch.setattr(auth, "verify_toolkit_bearer", reject)

    with pytest.raises(HTTPException) as exc_info:
        auth.require_auth(_request(), _creds("v1.abcdef1234567890.123.bad"))

    assert exc_info.value.status_code == 401
    assert "Invalid toolkit bearer" in exc_info.value.detail


def test_non_toolkit_bearer_falls_through_to_existing_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACTIVATION_HMAC_SECRET", "secret")
    monkeypatch.delenv("DISABLE_AUTH", raising=False)
    monkeypatch.setattr(auth, "_TOOLKIT_AUTH_AVAILABLE", True)
    monkeypatch.setattr(
        auth,
        "verify_toolkit_bearer",
        lambda _token: pytest.fail("non-toolkit bearer should not be verified"),
    )

    user = auth.require_auth(_request(), _creds("google-shaped-token"))

    assert user["email"] == "anonymous@local"
    assert user["auth_method"] == "legacy"


def test_activation_secret_unset_skips_toolkit_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ACTIVATION_HMAC_SECRET", raising=False)
    monkeypatch.delenv("DISABLE_AUTH", raising=False)
    monkeypatch.setattr(auth, "_TOOLKIT_AUTH_AVAILABLE", True)
    monkeypatch.setattr(
        auth,
        "verify_toolkit_bearer",
        lambda _token: pytest.fail("toolkit auth should be skipped without the secret"),
    )

    user = auth.require_auth(_request(), _creds("v1.abcdef1234567890.123.good"))

    assert user["email"] == "anonymous@local"
    assert user["auth_method"] == "legacy"


def test_disable_auth_bypasses_all_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACTIVATION_HMAC_SECRET", "secret")
    monkeypatch.setenv("DISABLE_AUTH", "1")
    monkeypatch.setattr(auth, "_TOOLKIT_AUTH_AVAILABLE", True)
    monkeypatch.setattr(
        auth,
        "verify_toolkit_bearer",
        lambda _token: pytest.fail("DISABLE_AUTH should bypass toolkit verification"),
    )

    user = auth.require_auth(_request(), _creds("v1.abcdef1234567890.123.good"))

    assert user == {
        "email": "dev@local",
        "name": "Dev User",
        "picture": "",
        "sub": "dev",
        "auth_method": "disabled",
    }
