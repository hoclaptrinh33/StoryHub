from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header
from starlette import status

from app.core.errors import AppError


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
                message="Ban khong co scope phu hop de thuc hien thao tac nay.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    def require_role(self, *roles: str) -> None:
        if self.role not in roles:
            raise AppError(
                code="AUTH_ROLE_DENIED",
                message="Ban khong co vai tro phu hop de thuc hien thao tac nay.",
                status_code=status.HTTP_403_FORBIDDEN,
            )


_TOKEN_PRESETS: dict[str, tuple[str, frozenset[str], str]] = {
    "cashier-demo": (
        "cashier",
        frozenset(
            {
                "inventory:read",
                "inventory:reserve",
                "crm:read",
                "crm:write",
                "pos:write",
                "rental:write",
                "rental:return",
                "rental:extend",
            }
        ),
        "cashier-01",
    ),
    "manager-demo": (
        "manager",
        frozenset(
            {
                "inventory:read",
                "inventory:reserve",
                "crm:read",
                "crm:write",
                "pos:write",
                "pos:refund",
                "rental:write",
                "rental:return",
                "rental:extend",
            }
        ),
        "manager-01",
    ),
    "owner-demo": (
        "owner",
        frozenset(
            {
                "inventory:read",
                "inventory:reserve",
                "crm:read",
                "crm:write",
                "pos:write",
                "pos:refund",
                "rental:write",
                "rental:return",
                "rental:extend",
                "system:backup",
            }
        ),
        "owner-01",
    ),
}


def _parse_authorization_header(value: str | None) -> str | None:
    if not value:
        return None

    parts = value.split(" ", maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise AppError(
            code="AUTH_INVALID_TOKEN",
            message="Authorization header khong hop le.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return parts[1].strip()


async def get_auth_context(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_branch_id: str | None = Header(default=None),
) -> AuthContext:
    token = _parse_authorization_header(authorization)

    # Fallback to cashier-demo if no token provided (useful for dev/POS environment)
    if not token:
        token = "cashier-demo"

    preset = _TOKEN_PRESETS.get(token)
    if preset is None:
        raise AppError(
            code="AUTH_INVALID_TOKEN",
            message="Token xac thuc khong duoc ho tro.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    role, scopes, default_user_id = preset
    return AuthContext(
        user_id=x_user_id or default_user_id,
        role=role,
        scopes=scopes,
        branch_id=x_branch_id or "main",
    )
