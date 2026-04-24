from __future__ import annotations

from datetime import timedelta
from functools import lru_cache

from app.core.security import create_access_token

_ROLE_SCOPES: dict[str, tuple[str, ...]] = {
    "cashier": (
        "inventory:read",
        "inventory:reserve",
        "inventory:write",
        "crm:read",
        "crm:write",
        "metadata:read",
        "pos:write",
        "rental:write",
        "rental:return",
        "rental:extend",
    ),
    "manager": (
        "inventory:read",
        "inventory:reserve",
        "inventory:write",
        "crm:read",
        "crm:write",
        "metadata:read",
        "pos:write",
        "pos:refund",
        "report:read",
        "rental:write",
        "rental:return",
        "rental:extend",
        "system:backup",
    ),
    "owner": (
        "inventory:read",
        "inventory:reserve",
        "inventory:write",
        "crm:read",
        "crm:write",
        "metadata:read",
        "pos:write",
        "pos:refund",
        "report:read",
        "rental:write",
        "rental:return",
        "rental:extend",
        "system:backup",
        "admin:read",
        "admin:write",
    ),
}

_DEMO_TOKEN_TO_ROLE: dict[str, str] = {
    "cashier-demo": "cashier",
    "manager-demo": "manager",
    "owner-demo": "owner",
}


@lru_cache
def _mint_demo_jwt(role: str) -> str:
    return create_access_token(
        {
            "sub": f"{role}-01",
            "role": role,
            "scopes": list(_ROLE_SCOPES[role]),
            "branch_id": "main",
            "username": f"{role}-demo",
        },
        expires_delta=timedelta(hours=12),
    )


def token_for_auth(token: str) -> str:
    role = _DEMO_TOKEN_TO_ROLE.get(token)
    if role is None:
        return token
    return _mint_demo_jwt(role)


def build_auth_headers(
    token: str | None,
    *,
    include_branch: bool = False,
    include_request_id: bool = False,
) -> dict[str, str]:
    headers: dict[str, str] = {"X-Device-Id": "TEST-KIOSK-01"}
    if include_branch:
        headers["X-Branch-Id"] = "main"
    if include_request_id:
        headers["X-Request-Id"] = "test-header-request-id"
    if token is not None:
        headers["Authorization"] = f"Bearer {token_for_auth(token)}"
    return headers


def ws_token(token: str) -> str:
    return token_for_auth(token)
