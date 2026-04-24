from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import AuthContext, get_auth_context
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.db.session import get_db_session

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    remember_me: bool = Field(default=False)

class TokenPayload(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]

class UserInfoResponse(BaseModel):
    id: int
    username: str
    full_name: str | None
    role: str
    scopes: list[str]

@router.post("/login", response_model=ResponseEnvelope[TokenPayload])
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[TokenPayload]:
    # Tìm kiếm user
    result = await session.execute(
        text("SELECT id, username, hashed_password, full_name, role, is_active FROM user WHERE username = :u AND deleted_at IS NULL"),
        {"u": payload.username}
    )
    user = result.mappings().first()

    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản của bạn đã bị khóa.",
        )

    # Định nghĩa scopes dựa trên role
    role_scopes = {
        "cashier": [
            "inventory:read", "inventory:reserve", "inventory:write",
            "crm:read", "crm:write", "metadata:read",
            "pos:write", "rental:write", "rental:return", "rental:extend"
        ],
        "manager": [
             "inventory:read", "inventory:reserve", "inventory:write",
             "crm:read", "crm:write", "metadata:read",
             "pos:write", "pos:refund", "report:read",
             "rental:write", "rental:return", "rental:extend", "system:backup"
        ],
        "owner": [
             "inventory:read", "inventory:reserve", "inventory:write",
             "crm:read", "crm:write", "metadata:read",
             "pos:write", "pos:refund", "report:read",
             "rental:write", "rental:return", "rental:extend", "system:backup",
             "admin:read", "admin:write",
        ]
    }
    
    scopes = role_scopes.get(user["role"], [])
    
    # Tính toán thời gian hết hạn dựa trên Remember Me
    if payload.remember_me:
        # 30 ngày
        access_token_expires = timedelta(days=30)
    else:
        # 1 ngày (Mặc định trong kiosk thường nên ngắn hơn nếu không ghi nhớ)
        access_token_expires = timedelta(hours=24)
    
    access_token = create_access_token(
        data={
            "sub": str(user["id"]),
            "role": user["role"],
            "scopes": scopes,
            "username": user["username"]
        },
        expires_delta=access_token_expires
    )
    
    return success_response(TokenPayload(
        access_token=access_token,
        user={
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "scopes": scopes
        }
    ))

@router.get("/me", response_model=ResponseEnvelope[UserInfoResponse])
async def get_me(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[UserInfoResponse]:
    result = await session.execute(
        text("SELECT id, username, full_name, role FROM user WHERE id = :id"),
        {"id": auth.user_id}
    )
    user = result.mappings().first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin người dùng này.")
    
    return success_response(UserInfoResponse(
        id=user["id"],
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
        scopes=list(auth.scopes)
    ))
