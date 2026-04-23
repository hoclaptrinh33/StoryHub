from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header
from starlette import status

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import decode_access_token


_ROLE_SCOPES: dict[str, tuple[str, ...]] = {
    "cashier": (
        "inventory:read",
        "inventory:reserve",
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
    ),
}

_DEMO_TOKEN_PAYLOADS: dict[str, dict[str, str | list[str]]] = {
    "cashier-demo": {
        "sub": "cashier-01",
        "role": "cashier",
        "scopes": list(_ROLE_SCOPES["cashier"]),
        "branch_id": "main",
    },
    "manager-demo": {
        "sub": "manager-01",
        "role": "manager",
        "scopes": list(_ROLE_SCOPES["manager"]),
        "branch_id": "main",
    },
    "owner-demo": {
        "sub": "owner-01",
        "role": "owner",
        "scopes": list(_ROLE_SCOPES["owner"]),
        "branch_id": "main",
    },
}


@dataclass(frozen=True, slots=True)
class AuthContext:
    user_id: str
    role: str
    scopes: frozenset[str]
    branch_id: str

    def require_scope(self, scope: str) -> None:
        if scope not in self.scopes:
            raise AppError(
                code="AUTH_SCOPE_DENIED",
                message="Lỗi: Bạn không có scope phù hợp để thực hiện thao tác này.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    def require_role(self, *roles: str) -> None:
        if self.role not in roles:
            raise AppError(
                code="AUTH_ROLE_DENIED",
                message="Lỗi: Bạn không có vai trò phù hợp để thực hiện thao tác này.",
                status_code=status.HTTP_403_FORBIDDEN,
            )


def _parse_authorization_header(value: str | None) -> str | None:
    if not value:
        return None

    parts = value.split(" ", maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise AppError(
            code="AUTH_INVALID_TOKEN",
            message="Authorization header không hợp lệ.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return parts[1].strip()


def _resolve_auth_payload(token: str) -> dict[str, object] | None:
    payload = decode_access_token(token)
    if payload:
        return payload

    settings = get_settings()
    if settings.auth_allow_demo_tokens:
        demo_payload = _DEMO_TOKEN_PAYLOADS.get(token)
        if demo_payload is not None:
            return dict(demo_payload)

    return None


def build_auth_context_from_token(
    token: str | None,
    *,
    user_id: str | None = None,
    branch_id: str | None = None,
) -> AuthContext:
    if not token:
        raise AppError(
            code="AUTH_MISSING_TOKEN",
            message="Vui lòng đăng nhập để sử dụng tính năng này.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    payload = _resolve_auth_payload(token)
    if not payload:
        raise AppError(
            code="AUTH_INVALID_TOKEN",
            message="Token xác thực không hợp lệ hoặc đã hết hạn.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    resolved_sub = payload.get("sub")
    if not isinstance(resolved_sub, str) or not resolved_sub:
        raise AppError(
            code="AUTH_INVALID_TOKEN",
            message="Token xác thực không hợp lệ hoặc thiếu thông tin user.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    resolved_role = payload.get("role", "cashier")
    if not isinstance(resolved_role, str) or not resolved_role:
        resolved_role = "cashier"

    raw_scopes = payload.get("scopes", [])
    if isinstance(raw_scopes, (list, tuple, set)):
        resolved_scopes = frozenset(str(scope) for scope in raw_scopes)
    else:
        resolved_scopes = frozenset()

    resolved_branch = payload.get("branch_id", "main")
    if not isinstance(resolved_branch, str) or not resolved_branch:
        resolved_branch = "main"

    return AuthContext(
        user_id=user_id or resolved_sub,
        role=resolved_role,
        scopes=resolved_scopes,
        branch_id=branch_id or resolved_branch,
    )


async def get_auth_context(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_branch_id: str | None = Header(default=None),
) -> AuthContext:
    token = _parse_authorization_header(authorization)
    return build_auth_context_from_token(
        token,
        user_id=x_user_id,
        branch_id=x_branch_id,
    )
