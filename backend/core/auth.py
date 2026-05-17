from __future__ import annotations

import os
from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    from chamber19_desktop_toolkit.auth import (
        ToolkitBearerError,
        verify_toolkit_bearer,
    )

    _TOOLKIT_AUTH_AVAILABLE = True
except ImportError:
    class ToolkitBearerError(Exception):
        pass

    verify_toolkit_bearer = None
    _TOOLKIT_AUTH_AVAILABLE = False


_BEARER = HTTPBearer(auto_error=False)


def _activation_hmac_secret() -> str:
    return os.getenv("ACTIVATION_HMAC_SECRET", "")


def _disable_auth() -> bool:
    return os.getenv("DISABLE_AUTH", "0") == "1"


def _legacy_user() -> dict[str, str]:
    return {
        "email": "anonymous@local",
        "name": "Anonymous User",
        "picture": "",
        "sub": "anonymous",
        "auth_method": "legacy",
    }


def _disabled_user() -> dict[str, str]:
    return {
        "email": "dev@local",
        "name": "Dev User",
        "picture": "",
        "sub": "dev",
        "auth_method": "disabled",
    }


def _is_toolkit_bearer(token: str) -> bool:
    return token.startswith("v1.") and token.count(".") == 3


def _launcher_user(machine_id: str) -> dict[str, str]:
    short = machine_id[:12] if len(machine_id) >= 12 else machine_id
    return {
        "email": f"launcher+{short}@chamber-19.internal",
        "name": f"Launcher ({short})",
        "picture": "",
        "sub": f"toolkit:{machine_id}",
        "auth_method": "toolkit_bearer",
    }


def _try_toolkit_bearer(creds: HTTPAuthorizationCredentials) -> Optional[dict[str, str]]:
    if not _activation_hmac_secret():
        return None

    token = creds.credentials
    if not _is_toolkit_bearer(token):
        return None

    if not _TOOLKIT_AUTH_AVAILABLE or verify_toolkit_bearer is None:
        raise HTTPException(status_code=500, detail="Toolkit bearer verification is not available")

    try:
        claims = verify_toolkit_bearer(token)
    except ToolkitBearerError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid toolkit bearer: {exc}") from exc

    return _launcher_user(str(claims["machine_id"]))


def require_auth(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Security(_BEARER),
) -> dict[str, str]:
    if _disable_auth():
        user = _disabled_user()
        request.state.user = user
        return user

    if creds is not None:
        toolkit_user = _try_toolkit_bearer(creds)
        if toolkit_user is not None:
            request.state.user = toolkit_user
            return toolkit_user

    user = _legacy_user()
    request.state.user = user
    return user
