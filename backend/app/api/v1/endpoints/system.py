from __future__ import annotations

import asyncio
import hashlib
import shutil
import zipfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.dependencies import AuthContext, get_auth_context
from app.api.v1.endpoints._common import get_request_meta, to_iso_z, utc_now
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.migration import resolve_sqlite_path
from app.db.session import get_db_session
from app.services import (
    get_cached_response,
    resolve_active_price_rule,
    store_cached_response,
    write_audit_log,
)
from app.services.cover_storage import ensure_storage_tree, resolve_runtime_root

router = APIRouter(prefix="/system", tags=["system"])

_BACKUP_JOB_TIMEOUT_SECONDS = 20
_ALLOWED_ENCRYPTION_REFS = {"storyhub-local", "storyhub-default"}


class CreateSystemBackupRequest(BaseModel):
    backup_type: Literal["full", "incremental"]
    include_media: bool = False
    encryption_password_ref: str | None = Field(default=None, max_length=128)
    request_id: str = Field(min_length=6, max_length=128)


class BackupJobPayload(BaseModel):
    backup_job_id: str
    status: Literal["queued", "running", "success", "failed"]
    file_path: str
    checksum: str
    created_at: str


class LatestBackupPayload(BaseModel):
    backup_job_id: str
    backup_type: Literal["full", "incremental"]
    status: Literal["queued", "running", "success", "failed"]
    file_path: str | None = None
    checksum: str | None = None
    error_message: str | None = None
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None


def _compute_file_checksum(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _resolve_backup_destination(backup_type: str, include_media: bool) -> Path:
    now = utc_now()
    runtime_root = resolve_runtime_root()
    backup_dir = runtime_root / "backups" / now.strftime("%Y-%m-%d")
    backup_dir.mkdir(parents=True, exist_ok=True)

    extension = "zip" if include_media else "bak"
    file_name = f"{backup_type}-{now.strftime('%Y%m%dT%H%M%SZ')}.{extension}"
    return backup_dir / file_name


def _backup_file_path_to_output(path: Path) -> str:
    runtime_root = resolve_runtime_root()
    try:
        return path.resolve().relative_to(runtime_root).as_posix()
    except ValueError:
        return str(path.resolve())


def _create_backup_artifact(backup_type: str, include_media: bool) -> tuple[str, str]:
    settings = get_settings()
    source_db_path = resolve_sqlite_path(settings.database_url)

    if str(source_db_path) == ":memory:" or not source_db_path.exists():
        raise OSError("Database file is unavailable for backup.")

    destination = _resolve_backup_destination(backup_type, include_media)

    if include_media:
        covers_dir = ensure_storage_tree()
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(source_db_path, arcname=f"database/{source_db_path.name}")
            if covers_dir.exists():
                for file_path in covers_dir.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(covers_dir.parent)
                        archive.write(file_path, arcname=f"storage/{relative_path.as_posix()}")
    else:
        shutil.copy2(source_db_path, destination)

    checksum = _compute_file_checksum(destination)
    return _backup_file_path_to_output(destination), checksum


async def _mark_backup_job_failed(
    session: AsyncSession,
    *,
    backup_job_id: int,
    error_message: str,
) -> None:
    finished_at = to_iso_z(utc_now())
    if session.in_transaction():
        await session.rollback()
    async with session.begin():
        await session.execute(
            text(
                """
                UPDATE backup_job
                SET
                    status = 'failed',
                    error_message = :error_message,
                    finished_at = :finished_at
                WHERE id = :backup_job_id;
                """
            ),
            {
                "backup_job_id": backup_job_id,
                "error_message": error_message,
                "finished_at": finished_at,
            },
        )


@router.post("/backups", response_model=ResponseEnvelope[BackupJobPayload])
async def create_system_backup(
    payload: CreateSystemBackupRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[BackupJobPayload] | dict[str, object]:
    auth.require_role("manager", "owner")
    auth.require_scope("system:backup")

    if payload.encryption_password_ref and payload.encryption_password_ref not in _ALLOWED_ENCRYPTION_REFS:
        raise AppError(
            code="ENCRYPTION_KEY_NOT_FOUND",
            message="Không tìm thấy khóa mã hóa theo tham chiếu đã cung cấp.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    cached = await get_cached_response(
        session,
        scope="system.create_backup",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload

    if session.in_transaction():
        await session.rollback()

    active_backup_result = await session.execute(
        text(
            """
            SELECT id
            FROM backup_job
            WHERE status IN ('queued', 'running')
            LIMIT 1;
            """
        )
    )
    if active_backup_result.first() is not None:
        raise AppError(
            code="BACKUP_ALREADY_RUNNING",
            message="Hiện đang có một tiến trình sao lưu khác đang chạy. Vui lòng đợi tiến trình trước hoàn tất.",
            status_code=status.HTTP_409_CONFLICT,
        )

    started_at = to_iso_z(utc_now())
    if session.in_transaction():
        await session.rollback()
    async with session.begin():
        await session.execute(
            text(
                """
                INSERT INTO backup_job (
                    backup_type,
                    status,
                    file_path,
                    checksum,
                    error_message,
                    started_at,
                    finished_at,
                    created_by_user_id
                )
                VALUES (
                    :backup_type,
                    'running',
                    :file_path,
                    NULL,
                    NULL,
                    :started_at,
                    NULL,
                    :created_by_user_id
                );
                """
            ),
            {
                "backup_type": payload.backup_type,
                "file_path": "pending",
                "started_at": started_at,
                "created_by_user_id": auth.user_id,
            },
        )
        backup_job_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
        backup_job_id = int(backup_job_id_result.scalar_one())

    try:
        file_path, checksum = await asyncio.wait_for(
            asyncio.to_thread(
                _create_backup_artifact,
                payload.backup_type,
                payload.include_media,
            ),
            timeout=_BACKUP_JOB_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        await _mark_backup_job_failed(
            session,
            backup_job_id=backup_job_id,
            error_message="Backup job timeout.",
        )
        raise AppError(
            code="BACKUP_JOB_TIMEOUT",
            message="Tiến trình sao lưu đã vượt quá thời gian phản hồi cho phép.",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        ) from exc
    except OSError as exc:
        await _mark_backup_job_failed(
            session,
            backup_job_id=backup_job_id,
            error_message=str(exc),
        )
        raise AppError(
            code="BACKUP_STORAGE_UNAVAILABLE",
            message="Không thể ghi tệp sao lưu vào bộ nhớ lưu trữ. Vui lòng kiểm tra dung lượng ổ đĩa.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc

    finished_at = to_iso_z(utc_now())
    ip_address, device_id = get_request_meta(request)
    if session.in_transaction():
        await session.rollback()
    async with session.begin():
        await session.execute(
            text(
                """
                UPDATE backup_job
                SET
                    status = 'success',
                    file_path = :file_path,
                    checksum = :checksum,
                    error_message = NULL,
                    finished_at = :finished_at
                WHERE id = :backup_job_id;
                """
            ),
            {
                "backup_job_id": backup_job_id,
                "file_path": file_path,
                "checksum": checksum,
                "finished_at": finished_at,
            },
        )

        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="SYSTEM_BACKUP_CREATED",
            entity_type="backup_job",
            entity_id=str(backup_job_id),
            before=None,
            after={
                "backup_type": payload.backup_type,
                "status": "success",
                "file_path": file_path,
                "checksum": checksum,
                "include_media": payload.include_media,
            },
            ip_address=ip_address,
            device_id=device_id,
        )

    envelope = success_response(
        BackupJobPayload(
            backup_job_id=f"BKP-{backup_job_id:04d}",
            status="success",
            file_path=file_path,
            checksum=checksum,
            created_at=started_at,
        )
    )

    try:
        if session.in_transaction():
            await session.rollback()
        async with session.begin():
            await store_cached_response(
                session,
                scope="system.create_backup",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        replay = await get_cached_response(
            session,
            scope="system.create_backup",
            request_id=payload.request_id,
        )
        if replay is not None:
            return replay.payload
        raise

    return envelope


@router.get("/backups/latest", response_model=ResponseEnvelope[LatestBackupPayload])
async def get_latest_backup_status(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[LatestBackupPayload]:
    auth.require_role("manager", "owner")
    auth.require_scope("system:backup")

    result = await session.execute(
        text(
            """
            SELECT
                id,
                backup_type,
                status,
                file_path,
                checksum,
                error_message,
                started_at,
                finished_at
            FROM backup_job
            ORDER BY COALESCE(finished_at, started_at) DESC, id DESC
            LIMIT 1;
            """
        )
    )
    row = result.mappings().first()
    if row is None:
        raise AppError(
            code="BACKUP_NOT_FOUND",
            message="Chưa có dữ liệu về các lịch sử sao lưu trước đó.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    created_at = row.get("started_at") or row.get("finished_at") or to_iso_z(utc_now())

    return success_response(
        LatestBackupPayload(
            backup_job_id=f"BKP-{int(row['id']):04d}",
            backup_type=str(row["backup_type"]),
            status=str(row["status"]),
            file_path=str(row["file_path"]) if row.get("file_path") else None,
            checksum=str(row["checksum"]) if row.get("checksum") else None,
            error_message=str(row["error_message"]) if row.get("error_message") else None,
            created_at=str(created_at),
            started_at=str(row["started_at"]) if row.get("started_at") else None,
            finished_at=str(row["finished_at"]) if row.get("finished_at") else None,
        )
    )


# ==========================================
# SYSTEM CONFIG (Cấu hình cửa hàng)
# ==========================================

_ALLOWED_CONFIG_KEYS = frozenset({
    "shop_name", "shop_address", "shop_phone", "bill_footer", "penalty_per_day",
})

class SystemConfigPatch(BaseModel):
    configs: dict[str, str] = Field(description="Map key -> value của các config cần cập nhật")


@router.get("/config", response_model=ResponseEnvelope[dict[str, str]])
async def get_system_config(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, str]]:
    """Đọc tất cả cấu hình hệ thống — owner only."""
    auth.require_role("owner")
    auth.require_scope("admin:read")

    result = await session.execute(text("SELECT config_key, config_value FROM system_config ORDER BY config_key"))
    config_map = {row["config_key"]: row["config_value"] for row in result.mappings().all()}
    return success_response(config_map)


@router.patch("/config", response_model=ResponseEnvelope[dict[str, str]])
async def update_system_config(
    payload: SystemConfigPatch,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, str]]:
    """Cập nhật một hoặc nhiều cấu hình — owner only."""
    auth.require_role("owner")
    auth.require_scope("admin:write")

    # Chỉ cho phép các key đã được định nghĩa trước
    invalid_keys = set(payload.configs.keys()) - _ALLOWED_CONFIG_KEYS
    if invalid_keys:
        raise AppError(
            code="INVALID_CONFIG_KEY",
            message=f"Các key không hợp lệ: {', '.join(sorted(invalid_keys))}. Các key cho phép: {', '.join(sorted(_ALLOWED_CONFIG_KEYS))}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    ip_address, device_id = get_request_meta(request)

    async with session.begin():
        for key, value in payload.configs.items():
            await session.execute(
                text("""
                    INSERT INTO system_config (config_key, config_value, updated_at)
                    VALUES (:key, :value, CURRENT_TIMESTAMP)
                    ON CONFLICT(config_key) DO UPDATE SET
                        config_value = excluded.config_value,
                        updated_at = excluded.updated_at
                """),
                {"key": key, "value": value},
            )

        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="SYSTEM_CONFIG_UPDATED",
            entity_type="system_config",
            entity_id="batch",
            before=None,
            after=payload.configs,
            ip_address=ip_address,
            device_id=device_id,
        )

    return success_response(payload.configs)


# ==========================================
# AUDIT LOGS (Nhật ký hoạt động)
# ==========================================

@router.get("/audit-logs", response_model=ResponseEnvelope[list[dict]])
async def list_audit_logs(
    limit: int = 50,
    offset: int = 0,
    action: str | None = None,
    entity_type: str | None = None,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[dict]]:
    """Xem nhật ký hệ thống — owner only."""
    auth.require_role("owner")
    auth.require_scope("admin:read")

    query = """
        SELECT a.id, a.action, a.entity_type, a.entity_id,
               a.before_json, a.after_json, a.ip_address, a.device_id,
               a.created_at, u.username AS actor_name, u.full_name AS actor_full_name
        FROM audit_log a
        LEFT JOIN user u ON CAST(a.actor_user_id AS TEXT) = CAST(u.id AS TEXT)
        WHERE 1=1
    """
    params: dict[str, object] = {"limit": min(limit, 200), "offset": offset}

    if action:
        query += " AND a.action = :action"
        params["action"] = action

    if entity_type:
        query += " AND a.entity_type = :entity_type"
        params["entity_type"] = entity_type

    query += " ORDER BY a.created_at DESC LIMIT :limit OFFSET :offset"

    result = await session.execute(text(query), params)
    return success_response([dict(r) for r in result.mappings().all()])


# ==========================================
# USER MANAGEMENT (Quản lý nhân viên)
# ==========================================

import re as _re
from app.core.security import get_password_hash as _get_password_hash

_USERNAME_PATTERN = _re.compile(r"^[a-z0-9_]{3,50}$")

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    full_name: str | None = None
    role: str = Field(default="cashier", pattern="^(cashier|manager)$")  # Owner không tạo được Owner khác

class UserStatusPatch(BaseModel):
    is_active: bool | None = None
    full_name: str | None = None
    role: str | None = Field(default=None, pattern="^(cashier|manager)$")
    new_password: str | None = Field(default=None, min_length=6, max_length=100)


@router.get("/users", response_model=ResponseEnvelope[list[dict]])
async def list_users(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[dict]]:
    """Danh sách nhân viên — owner only."""
    auth.require_role("owner")
    auth.require_scope("admin:read")

    result = await session.execute(
        text("SELECT id, username, full_name, role, is_active, created_at FROM user WHERE deleted_at IS NULL ORDER BY role, username")
    )
    return success_response([dict(r) for r in result.mappings().all()])


@router.post("/users", response_model=ResponseEnvelope[dict])
async def create_user(
    payload: UserCreate,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict]:
    """Tạo tài khoản nhân viên mới — owner only."""
    auth.require_role("owner")
    auth.require_scope("admin:write")

    # Validate username format
    if not _USERNAME_PATTERN.match(payload.username):
        raise AppError(
            code="INVALID_USERNAME",
            message="Username chỉ được chứa chữ thường, số và dấu gạch dưới (3-50 ký tự).",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Kiểm tra trùng username
    existing = await session.execute(
        text("SELECT id FROM user WHERE username = :u AND deleted_at IS NULL"), {"u": payload.username}
    )
    if existing.first():
        raise AppError(code="USERNAME_EXISTS", message=f"Username '{payload.username}' đã tồn tại.", status_code=status.HTTP_409_CONFLICT)

    hashed = _get_password_hash(payload.password)
    ip_address, device_id = get_request_meta(request)

    async with session.begin():
        await session.execute(
            text("INSERT INTO user (username, hashed_password, full_name, role, is_active) VALUES (:u, :hp, :fn, :role, 1)"),
            {"u": payload.username, "hp": hashed, "fn": payload.full_name, "role": payload.role},
        )
        new_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
        new_id = int(new_id_result.scalar_one())

        await write_audit_log(
            session, actor_user_id=auth.user_id, action="USER_CREATED",
            entity_type="user", entity_id=str(new_id),
            before=None,
            after={"username": payload.username, "role": payload.role, "full_name": payload.full_name},
            ip_address=ip_address, device_id=device_id,
        )

    return success_response({"id": new_id, "username": payload.username, "role": payload.role})


@router.patch("/users/{user_id}", response_model=ResponseEnvelope[dict])
async def update_user(
    user_id: int,
    payload: UserStatusPatch,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict]:
    """Cập nhật thông tin nhân viên: khóa/mở TK, đổi mật khẩu, đổi vai trò — owner only."""
    auth.require_role("owner")
    auth.require_scope("admin:write")

    # Không cho phép sửa chính mình (tránh tự lock)
    if str(user_id) == str(auth.user_id):
        raise AppError(code="SELF_EDIT_DENIED", message="Không thể sửa tài khoản của chính mình.", status_code=status.HTTP_403_FORBIDDEN)

    existing = await session.execute(
        text("SELECT id, username, role, is_active FROM user WHERE id = :id AND deleted_at IS NULL"), {"id": user_id}
    )
    row = existing.mappings().first()
    if not row:
        raise AppError(code="USER_NOT_FOUND", message="Không tìm thấy tài khoản.", status_code=status.HTTP_404_NOT_FOUND)

    # Không cho phép sửa tài khoản owner khác
    if str(row["role"]) == "owner":
        raise AppError(code="OWNER_EDIT_DENIED", message="Không thể sửa tài khoản Chủ sở hữu khác.", status_code=status.HTTP_403_FORBIDDEN)

    set_clauses = ["updated_at = CURRENT_TIMESTAMP"]
    params: dict[str, object] = {"id": user_id}

    if payload.is_active is not None:
        set_clauses.append("is_active = :is_active")
        params["is_active"] = 1 if payload.is_active else 0

    if payload.full_name is not None:
        set_clauses.append("full_name = :full_name")
        params["full_name"] = payload.full_name

    if payload.role is not None:
        set_clauses.append("role = :role")
        params["role"] = payload.role

    if payload.new_password is not None:
        set_clauses.append("hashed_password = :hashed_password")
        params["hashed_password"] = _get_password_hash(payload.new_password)

    ip_address, device_id = get_request_meta(request)

    async with session.begin():
        await session.execute(text(f"UPDATE user SET {', '.join(set_clauses)} WHERE id = :id"), params)
        await write_audit_log(
            session, actor_user_id=auth.user_id, action="USER_UPDATED",
            entity_type="user", entity_id=str(user_id),
            before={"username": row["username"], "role": row["role"], "is_active": bool(row["is_active"])},
            after={k: v for k, v in payload.model_dump().items() if v is not None and k != "new_password"},
            ip_address=ip_address, device_id=device_id,
        )

    return success_response({"status": "updated", "user_id": user_id})


# ==========================================
# ADMIN TRANSACTION MONITORING
# ==========================================

class AdminTransactionKind(BaseModel):
    transaction_type: Literal["sale", "rental"]
    reference_id: str
    customer_name: str
    amount: int
    created_at: str
    status: str
    can_refund: bool
    can_hard_delete: bool


class HardDeleteTransactionRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=300)


class EmergencyRefundSaleOrderRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=255)
    request_id: str = Field(min_length=6, max_length=128)
    refund_method: Literal["cash", "bank_transfer", "e_wallet", "original_method"] = "original_method"


class EmergencyRefundSaleOrderPayload(BaseModel):
    refund_id: str
    order_id: str
    refunded_total: int
    order_status: Literal["refunded", "partially_refunded"]
    processed_at: str


class EmergencyRefundRentalContractRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=255)
    request_id: str = Field(min_length=6, max_length=128)
    refund_method: Literal["cash", "bank_transfer", "e_wallet", "original_method"] = "original_method"


class EmergencyRefundRentalContractPayload(BaseModel):
    refund_id: str
    contract_id: str
    refunded_total: int
    contract_status: Literal["cancelled"]
    processed_at: str


def _parse_reference_id(reference_id: str) -> int:
    try:
        normalized = int(reference_id)
    except ValueError as exc:
        raise AppError(
            code="INVALID_REFERENCE_ID",
            message="Ma giao dich khong hop le.",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc
    if normalized <= 0:
        raise AppError(
            code="INVALID_REFERENCE_ID",
            message="Ma giao dich khong hop le.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return normalized


async def _hard_delete_sale_transaction(session: AsyncSession, order_id: int) -> dict[str, object]:
    order_result = await session.execute(
        text(
            """
            SELECT id, status, grand_total, created_at
            FROM pos_order
            WHERE id = :order_id
              AND deleted_at IS NULL;
            """
        ),
        {"order_id": order_id},
    )
    order_row = order_result.mappings().first()
    if order_row is None:
        raise AppError(
            code="TRANSACTION_NOT_FOUND",
            message="Khong tim thay hoa don ban hang de xoa cung.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    refund_count_result = await session.execute(
        text("SELECT COUNT(*) FROM pos_refund WHERE order_id = :order_id;"),
        {"order_id": order_id},
    )
    refund_count = int(refund_count_result.scalar_one() or 0)

    restored_items_result = await session.execute(
        text(
            """
            UPDATE item
            SET
                status = 'available',
                reserved_by_customer_id = NULL,
                reserved_at = NULL,
                reservation_expire_at = NULL,
                updated_at = CURRENT_TIMESTAMP,
                version_no = version_no + 1
            WHERE id IN (
                SELECT item_id
                FROM order_item
                WHERE pos_order_id = :order_id
                  AND item_id IS NOT NULL
            )
              AND deleted_at IS NULL;
            """
        ),
        {"order_id": order_id},
    )

    await session.execute(
        text("DELETE FROM order_item WHERE pos_order_id = :order_id;"),
        {"order_id": order_id},
    )
    await session.execute(
        text(
            """
            DELETE FROM pos_refund_item
            WHERE refund_id IN (
                SELECT id
                FROM pos_refund
                WHERE order_id = :order_id
            );
            """
        ),
        {"order_id": order_id},
    )
    await session.execute(
        text("DELETE FROM pos_refund WHERE order_id = :order_id;"),
        {"order_id": order_id},
    )
    await session.execute(
        text("DELETE FROM pos_payment WHERE order_id = :order_id;"),
        {"order_id": order_id},
    )
    await session.execute(
        text("DELETE FROM pos_order_item WHERE order_id = :order_id;"),
        {"order_id": order_id},
    )
    await session.execute(
        text("DELETE FROM pos_order WHERE id = :order_id;"),
        {"order_id": order_id},
    )

    return {
        "transaction_type": "sale",
        "reference_id": str(order_id),
        "status_before": str(order_row["status"]),
        "amount_before": int(order_row["grand_total"]),
        "created_at": str(order_row["created_at"]),
        "restored_items": int(restored_items_result.rowcount or 0),
        "deleted_refunds": refund_count,
    }


async def _hard_delete_rental_transaction(session: AsyncSession, contract_id: int) -> dict[str, object]:
    contract_result = await session.execute(
        text(
            """
            SELECT id, status, rent_date
            FROM rental_contract
            WHERE id = :contract_id
              AND deleted_at IS NULL;
            """
        ),
        {"contract_id": contract_id},
    )
    contract_row = contract_result.mappings().first()
    if contract_row is None:
        raise AppError(
            code="TRANSACTION_NOT_FOUND",
            message="Khong tim thay hop dong thue de xoa cung.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    restored_items_result = await session.execute(
        text(
            """
            UPDATE item
            SET
                status = 'available',
                reserved_by_customer_id = NULL,
                reserved_at = NULL,
                reservation_expire_at = NULL,
                updated_at = CURRENT_TIMESTAMP,
                version_no = version_no + 1
            WHERE id IN (
                SELECT item_id
                FROM rental_item
                WHERE contract_id = :contract_id
            )
              AND deleted_at IS NULL;
            """
        ),
        {"contract_id": contract_id},
    )

    await session.execute(
        text("DELETE FROM order_item WHERE rental_contract_id = :contract_id;"),
        {"contract_id": contract_id},
    )
    await session.execute(
        text("DELETE FROM rental_settlement WHERE contract_id = :contract_id;"),
        {"contract_id": contract_id},
    )
    await session.execute(
        text("DELETE FROM rental_item WHERE contract_id = :contract_id;"),
        {"contract_id": contract_id},
    )
    await session.execute(
        text("DELETE FROM rental_contract WHERE id = :contract_id;"),
        {"contract_id": contract_id},
    )

    return {
        "transaction_type": "rental",
        "reference_id": str(contract_id),
        "status_before": str(contract_row["status"]),
        "amount_before": 0,
        "created_at": str(contract_row["rent_date"]),
        "restored_items": int(restored_items_result.rowcount or 0),
        "deleted_refunds": 0,
    }


@router.get("/transactions", response_model=ResponseEnvelope[list[AdminTransactionKind]])
async def list_admin_transactions(
    q: str | None = None,
    kind: Literal["all", "sale", "rental"] = "all",
    limit: int = 50,
    offset: int = 0,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[AdminTransactionKind]]:
    auth.require_role("owner")
    auth.require_scope("admin:read")

    normalized_query = (q or "").strip()
    params: dict[str, object] = {
        "kind": kind,
        "q": normalized_query,
        "q_like": f"%{normalized_query}%",
        "limit": max(1, min(limit, 200)),
        "offset": max(offset, 0),
    }

    result = await session.execute(
        text(
            """
            SELECT
                t.transaction_type,
                t.reference_id,
                t.customer_name,
                t.amount,
                t.created_at,
                t.status,
                t.can_refund,
                1 AS can_hard_delete
            FROM (
                SELECT
                    'sale' AS transaction_type,
                    CAST(po.id AS TEXT) AS reference_id,
                    COALESCE(c.name, 'Khach le') AS customer_name,
                    po.grand_total AS amount,
                    po.created_at AS created_at,
                    po.status AS status,
                    CASE WHEN po.status IN ('paid', 'partially_refunded') THEN 1 ELSE 0 END AS can_refund
                FROM pos_order po
                LEFT JOIN customer c ON c.id = po.customer_id
                WHERE po.deleted_at IS NULL

                UNION ALL

                SELECT
                    'rental' AS transaction_type,
                    CAST(rc.id AS TEXT) AS reference_id,
                    COALESCE(c.name, 'Khach le') AS customer_name,
                    COALESCE(SUM(ri.final_rent_price + ri.final_deposit), 0)
                        + COALESCE(MAX(rs.total_fee), 0) AS amount,
                    rc.rent_date AS created_at,
                    rc.status AS status,
                    CASE
                        WHEN rc.status IN ('active', 'partial_returned', 'overdue')
                         AND NOT EXISTS (
                            SELECT 1
                            FROM rental_refund rr
                            WHERE rr.contract_id = rc.id
                         )
                        THEN 1
                        ELSE 0
                    END AS can_refund
                FROM rental_contract rc
                LEFT JOIN customer c ON c.id = rc.customer_id
                LEFT JOIN rental_item ri ON ri.contract_id = rc.id
                LEFT JOIN rental_settlement rs ON rs.contract_id = rc.id
                WHERE rc.deleted_at IS NULL
                GROUP BY rc.id, c.name, rc.rent_date, rc.status
            ) t
            WHERE (:kind = 'all' OR t.transaction_type = :kind)
              AND (
                    :q = ''
                    OR LOWER(t.customer_name) LIKE LOWER(:q_like)
                    OR t.reference_id LIKE :q_like
              )
            ORDER BY datetime(t.created_at) DESC
            LIMIT :limit OFFSET :offset;
            """
        ),
        params,
    )

    payload = [
        AdminTransactionKind(
            transaction_type=str(row["transaction_type"]),
            reference_id=str(row["reference_id"]),
            customer_name=str(row["customer_name"]),
            amount=int(row["amount"] or 0),
            created_at=str(row["created_at"]),
            status=str(row["status"]),
            can_refund=bool(row["can_refund"]),
            can_hard_delete=True,
        )
        for row in result.mappings().all()
    ]
    return success_response(payload)


@router.post(
    "/transactions/sale/{order_id}/emergency-refund",
    response_model=ResponseEnvelope[EmergencyRefundSaleOrderPayload],
)
async def emergency_refund_sale_order(
    order_id: int,
    payload: EmergencyRefundSaleOrderRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[EmergencyRefundSaleOrderPayload]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    if session.in_transaction():
        await session.rollback()

    now_iso = to_iso_z(utc_now())
    async with session.begin():
        order_result = await session.execute(
            text(
                """
                SELECT id, status, paid_total
                FROM pos_order
                WHERE id = :order_id
                  AND deleted_at IS NULL;
                """
            ),
            {"order_id": order_id},
        )
        order_row = order_result.mappings().first()
        if order_row is None:
            raise AppError(
                code="ORDER_NOT_FOUND",
                message="Khong tim thay hoa don ban hang de hoan tien.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        order_items_result = await session.execute(
            text(
                """
                SELECT id, volume_id, quantity, final_sell_price
                FROM pos_order_item
                WHERE order_id = :order_id;
                """
            ),
            {"order_id": order_id},
        )
        order_items = [dict(row) for row in order_items_result.mappings().all()]
        if not order_items:
            raise AppError(
                code="ORDER_EMPTY",
                message="Khong tim thay dong hang trong hoa don ban hang.",
                status_code=status.HTTP_409_CONFLICT,
            )

        refunded_items_result = await session.execute(
            text(
                """
                SELECT pri.volume_id
                FROM pos_refund_item pri
                JOIN pos_refund pr ON pr.id = pri.refund_id
                WHERE pr.order_id = :order_id;
                """
            ),
            {"order_id": order_id},
        )
        already_refunded = {int(row["volume_id"]) for row in refunded_items_result.mappings().all()}

        refundable_items = [
            item for item in order_items if int(item["volume_id"]) not in already_refunded
        ]
        if not refundable_items:
            raise AppError(
                code="ORDER_ALREADY_REFUNDED",
                message="Hoa don da duoc hoan tien het, khong con dong nao de hoan khan cap.",
                status_code=status.HTTP_409_CONFLICT,
            )

        refund_amount = sum(
            int(item["final_sell_price"]) * int(item["quantity"])
            for item in refundable_items
        )

        refunded_total_result = await session.execute(
            text(
                """
                SELECT COALESCE(SUM(refunded_total), 0) AS total
                FROM pos_refund
                WHERE order_id = :order_id;
                """
            ),
            {"order_id": order_id},
        )
        refunded_total_before = int(refunded_total_result.scalar_one() or 0)
        if refunded_total_before + refund_amount > int(order_row["paid_total"]):
            raise AppError(
                code="REFUND_EXCEEDS_PAID_AMOUNT",
                message="Tong tien hoan vuot qua so tien da thanh toan cua hoa don.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        stored_refund_method = payload.refund_method
        if stored_refund_method == "original_method":
            method_result = await session.execute(
                text(
                    """
                    SELECT method
                    FROM pos_payment
                    WHERE order_id = :order_id
                    ORDER BY id ASC
                    LIMIT 1;
                    """
                ),
                {"order_id": order_id},
            )
            stored_refund_method = str(method_result.scalar_one_or_none() or "cash")

        await session.execute(
            text(
                """
                INSERT INTO pos_refund (
                    order_id,
                    reason,
                    refund_method,
                    refunded_total,
                    request_id,
                    created_by_user_id,
                    created_at
                )
                VALUES (
                    :order_id,
                    :reason,
                    :refund_method,
                    :refunded_total,
                    :request_id,
                    :created_by_user_id,
                    CURRENT_TIMESTAMP
                );
                """
            ),
            {
                "order_id": order_id,
                "reason": payload.reason,
                "refund_method": stored_refund_method,
                "refunded_total": refund_amount,
                "request_id": payload.request_id,
                "created_by_user_id": auth.user_id,
            },
        )
        refund_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
        refund_id = int(refund_id_result.scalar_one())

        for item in refundable_items:
            quantity = int(item["quantity"])
            await session.execute(
                text(
                    """
                    INSERT INTO pos_refund_item (
                        refund_id,
                        order_item_id,
                        volume_id,
                        amount
                    )
                    VALUES (
                        :refund_id,
                        :order_item_id,
                        :volume_id,
                        :amount
                    );
                    """
                ),
                {
                    "refund_id": refund_id,
                    "order_item_id": int(item["id"]),
                    "volume_id": int(item["volume_id"]),
                    "amount": int(item["final_sell_price"]) * quantity,
                },
            )
            await session.execute(
                text(
                    """
                    UPDATE volume
                    SET
                        retail_stock = retail_stock + :quantity,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :volume_id;
                    """
                ),
                {"quantity": quantity, "volume_id": int(item["volume_id"])},
            )

        refunded_total_after = refunded_total_before + refund_amount
        order_status = (
            "refunded"
            if refunded_total_after == int(order_row["paid_total"])
            else "partially_refunded"
        )

        await session.execute(
            text(
                """
                UPDATE pos_order
                SET
                    status = :status,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :order_id;
                """
            ),
            {"status": order_status, "order_id": order_id},
        )

        ip_address, device_id = get_request_meta(request)
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="POS_ORDER_EMERGENCY_REFUNDED",
            entity_type="pos_order",
            entity_id=str(order_id),
            before={"status": str(order_row["status"])},
            after={
                "status": order_status,
                "refund_id": refund_id,
                "refunded_total": refund_amount,
                "reason": payload.reason,
            },
            ip_address=ip_address,
            device_id=device_id,
        )

    return success_response(
        EmergencyRefundSaleOrderPayload(
            refund_id=str(refund_id),
            order_id=str(order_id),
            refunded_total=refund_amount,
            order_status=order_status,
            processed_at=now_iso,
        )
    )


@router.post(
    "/transactions/rental/{contract_id}/emergency-refund",
    response_model=ResponseEnvelope[EmergencyRefundRentalContractPayload],
)
async def emergency_refund_rental_contract(
    contract_id: int,
    payload: EmergencyRefundRentalContractRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[EmergencyRefundRentalContractPayload] | dict[str, object]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    cached = await get_cached_response(
        session,
        scope="system.emergency_refund_rental",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload

    replay_result = await session.execute(
        text(
            """
            SELECT id, contract_id, refunded_total, created_at
            FROM rental_refund
            WHERE request_id = :request_id
            LIMIT 1;
            """
        ),
        {"request_id": payload.request_id},
    )
    replay_row = replay_result.mappings().first()
    if replay_row is not None:
        return success_response(
            EmergencyRefundRentalContractPayload(
                refund_id=str(replay_row["id"]),
                contract_id=str(replay_row["contract_id"]),
                refunded_total=int(replay_row["refunded_total"]),
                contract_status="cancelled",
                processed_at=str(replay_row["created_at"]),
            )
        )

    if session.in_transaction():
        await session.rollback()

    now_iso = to_iso_z(utc_now())
    async with session.begin():
        contract_result = await session.execute(
            text(
                """
                SELECT
                    id,
                    status,
                    rent_date,
                    due_date,
                    deposit_total,
                    remaining_deposit,
                    debt_total
                FROM rental_contract
                WHERE id = :contract_id
                  AND deleted_at IS NULL;
                """
            ),
            {"contract_id": contract_id},
        )
        contract_row = contract_result.mappings().first()
        if contract_row is None:
            raise AppError(
                code="CONTRACT_NOT_FOUND",
                message="Khong tim thay hop dong thue de hoan tien khan cap.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if str(contract_row["status"]) == "cancelled":
            raise AppError(
                code="CONTRACT_NOT_REFUNDABLE",
                message="Hop dong da o trang thai da huy.",
                status_code=status.HTTP_409_CONFLICT,
            )

        existing_refund_result = await session.execute(
            text(
                """
                SELECT id
                FROM rental_refund
                WHERE contract_id = :contract_id
                LIMIT 1;
                """
            ),
            {"contract_id": contract_id},
        )
        if existing_refund_result.first() is not None:
            raise AppError(
                code="CONTRACT_ALREADY_REFUNDED",
                message="Hop dong da co ban ghi hoan tien khan cap truoc do.",
                status_code=status.HTTP_409_CONFLICT,
            )

        rental_items_result = await session.execute(
            text(
                """
                SELECT
                    id,
                    item_id,
                    final_rent_price,
                    final_deposit
                FROM rental_item
                WHERE contract_id = :contract_id;
                """
            ),
            {"contract_id": contract_id},
        )
        rental_items = [dict(row) for row in rental_items_result.mappings().all()]
        if not rental_items:
            raise AppError(
                code="CONTRACT_EMPTY",
                message="Khong tim thay dong thue de xu ly hoan tien khan cap.",
                status_code=status.HTTP_409_CONFLICT,
            )

        refund_amount = sum(
            int(row["final_rent_price"]) + int(row["final_deposit"])
            for row in rental_items
        )
        stored_refund_method = payload.refund_method

        await session.execute(
            text(
                """
                INSERT INTO rental_refund (
                    contract_id,
                    reason,
                    refund_method,
                    refunded_total,
                    request_id,
                    created_by_user_id,
                    created_at
                )
                VALUES (
                    :contract_id,
                    :reason,
                    :refund_method,
                    :refunded_total,
                    :request_id,
                    :created_by_user_id,
                    CURRENT_TIMESTAMP
                );
                """
            ),
            {
                "contract_id": contract_id,
                "reason": payload.reason,
                "refund_method": stored_refund_method,
                "refunded_total": refund_amount,
                "request_id": payload.request_id,
                "created_by_user_id": auth.user_id,
            },
        )
        refund_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
        refund_id = int(refund_id_result.scalar_one())

        for row in rental_items:
            item_amount = int(row["final_rent_price"]) + int(row["final_deposit"])
            await session.execute(
                text(
                    """
                    INSERT INTO rental_refund_item (
                        refund_id,
                        rental_item_id,
                        item_id,
                        amount
                    )
                    VALUES (
                        :refund_id,
                        :rental_item_id,
                        :item_id,
                        :amount
                    );
                    """
                ),
                {
                    "refund_id": refund_id,
                    "rental_item_id": int(row["id"]),
                    "item_id": str(row["item_id"]),
                    "amount": item_amount,
                },
            )

        restored_items_result = await session.execute(
            text(
                """
                UPDATE item
                SET
                    status = 'available',
                    reserved_by_customer_id = NULL,
                    reserved_at = NULL,
                    reservation_expire_at = NULL,
                    updated_at = CURRENT_TIMESTAMP,
                    version_no = version_no + 1
                WHERE id IN (
                    SELECT item_id
                    FROM rental_item
                    WHERE contract_id = :contract_id
                )
                  AND deleted_at IS NULL;
                """
            ),
            {"contract_id": contract_id},
        )

        await session.execute(
            text(
                """
                UPDATE rental_item
                SET
                    status = 'returned',
                    condition_after = COALESCE(condition_after, condition_before)
                WHERE contract_id = :contract_id;
                """
            ),
            {"contract_id": contract_id},
        )
        await session.execute(
            text("DELETE FROM rental_settlement WHERE contract_id = :contract_id;"),
            {"contract_id": contract_id},
        )
        await session.execute(
            text(
                """
                UPDATE rental_contract
                SET
                    status = 'cancelled',
                    remaining_deposit = 0,
                    debt_total = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :contract_id;
                """
            ),
            {"contract_id": contract_id},
        )

        ip_address, device_id = get_request_meta(request)
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="RENTAL_CONTRACT_EMERGENCY_REFUNDED",
            entity_type="rental_contract",
            entity_id=str(contract_id),
            before={
                "status": str(contract_row["status"]),
                "deposit_total": int(contract_row["deposit_total"] or 0),
                "remaining_deposit": int(contract_row["remaining_deposit"] or 0),
                "debt_total": int(contract_row["debt_total"] or 0),
            },
            after={
                "status": "cancelled",
                "refund_id": refund_id,
                "refunded_total": refund_amount,
                "reason": payload.reason,
                "restored_items": int(restored_items_result.rowcount or 0),
            },
            ip_address=ip_address,
            device_id=device_id,
        )

    envelope = success_response(
        EmergencyRefundRentalContractPayload(
            refund_id=str(refund_id),
            contract_id=str(contract_id),
            refunded_total=refund_amount,
            contract_status="cancelled",
            processed_at=now_iso,
        )
    )

    try:
        if session.in_transaction():
            await session.rollback()
        async with session.begin():
            await store_cached_response(
                session,
                scope="system.emergency_refund_rental",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        replay = await get_cached_response(
            session,
            scope="system.emergency_refund_rental",
            request_id=payload.request_id,
        )
        if replay is not None:
            return replay.payload
        raise

    return envelope


@router.post(
    "/transactions/{transaction_type}/{reference_id}/hard-delete",
    response_model=ResponseEnvelope[dict[str, object]],
)
async def hard_delete_transaction(
    transaction_type: Literal["sale", "rental"],
    reference_id: str,
    payload: HardDeleteTransactionRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, object]]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    normalized_reference = _parse_reference_id(reference_id)

    if session.in_transaction():
        await session.rollback()

    async with session.begin():
        if transaction_type == "sale":
            delete_summary = await _hard_delete_sale_transaction(session, normalized_reference)
        else:
            delete_summary = await _hard_delete_rental_transaction(session, normalized_reference)

        ip_address, device_id = get_request_meta(request)
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="TRANSACTION_HARD_DELETED",
            entity_type=f"{transaction_type}_transaction",
            entity_id=str(normalized_reference),
            before={
                "status": delete_summary["status_before"],
                "amount": delete_summary["amount_before"],
                "created_at": delete_summary["created_at"],
            },
            after={
                "reason": payload.reason,
                "restored_items": delete_summary["restored_items"],
                "deleted_refunds": delete_summary["deleted_refunds"],
            },
            ip_address=ip_address,
            device_id=device_id,
        )

    return success_response(
        {
            "status": "hard_deleted",
            "transaction_type": transaction_type,
            "reference_id": str(normalized_reference),
            "restored_items": delete_summary["restored_items"],
            "deleted_refunds": delete_summary["deleted_refunds"],
        }
    )


# ==========================================
# PRICING ENGINE MANAGEMENT
# ==========================================

class ActivePriceRulePayload(BaseModel):
    rule_id: int | None
    version_no: int
    k_rent: float
    k_deposit: float
    d_floor: int
    used_demand_factor: float
    used_cap_ratio: float
    note: str | None = None
    activated_at: str | None = None


class UpdateActivePriceRuleRequest(BaseModel):
    k_rent: float = Field(ge=0.01, le=0.95)
    k_deposit: float = Field(ge=0.1, le=3.0)
    d_floor: int = Field(ge=1000, le=5_000_000)
    used_demand_factor: float = Field(default=1.0, ge=0.2, le=2.0)
    used_cap_ratio: float = Field(default=1.0, ge=0.2, le=1.0)
    note: str | None = Field(default=None, max_length=255)


class BulkPriceUpdateRequest(BaseModel):
    percent_delta: float = Field(ge=-90, le=500)
    reason: str = Field(min_length=3, max_length=255)


class BulkPriceUpdatePayload(BaseModel):
    total_volumes: int
    affected_volumes: int
    percent_delta: float
    min_new_price: int
    max_new_price: int


async def _load_active_price_rule_row(session: AsyncSession) -> dict[str, object] | None:
    result = await session.execute(
        text(
            """
            SELECT
                id,
                rule_code,
                version_no,
                k_rent,
                k_deposit,
                d_floor,
                used_demand_factor,
                used_cap_ratio,
                note,
                activated_at
            FROM price_rule
            WHERE status = 'active'
              AND (valid_from IS NULL OR valid_from <= CURRENT_TIMESTAMP)
              AND (valid_to IS NULL OR valid_to > CURRENT_TIMESTAMP)
            ORDER BY activated_at DESC, id DESC
            LIMIT 1;
            """
        )
    )
    row = result.mappings().first()
    return dict(row) if row is not None else None


@router.get("/pricing/active", response_model=ResponseEnvelope[ActivePriceRulePayload])
async def get_active_pricing_rule(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[ActivePriceRulePayload]:
    auth.require_role("owner")
    auth.require_scope("admin:read")

    row = await _load_active_price_rule_row(session)
    if row is None:
        resolved = await resolve_active_price_rule(session)
        return success_response(
            ActivePriceRulePayload(
                rule_id=resolved.rule_id,
                version_no=resolved.version_no,
                k_rent=resolved.k_rent,
                k_deposit=resolved.k_deposit,
                d_floor=resolved.d_floor,
                used_demand_factor=resolved.used_demand_factor,
                used_cap_ratio=resolved.used_cap_ratio,
                note="Default runtime pricing rule",
                activated_at=None,
            )
        )

    return success_response(
        ActivePriceRulePayload(
            rule_id=int(row["id"]),
            version_no=int(row["version_no"]),
            k_rent=float(row["k_rent"]),
            k_deposit=float(row["k_deposit"]),
            d_floor=int(row["d_floor"]),
            used_demand_factor=float(row["used_demand_factor"]),
            used_cap_ratio=float(row["used_cap_ratio"]),
            note=str(row["note"]) if row.get("note") else None,
            activated_at=str(row["activated_at"]) if row.get("activated_at") else None,
        )
    )


@router.patch("/pricing/active", response_model=ResponseEnvelope[ActivePriceRulePayload])
async def update_active_pricing_rule(
    payload: UpdateActivePriceRuleRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[ActivePriceRulePayload]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    if payload.k_deposit < payload.k_rent:
        raise AppError(
            code="PRICE_RULE_INVALID",
            message="He so coc phai lon hon hoac bang he so thue.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    now_iso = to_iso_z(utc_now())
    current_rule = await _load_active_price_rule_row(session)
    next_version = 1
    rule_code = "default"
    before_payload: dict[str, object] | None = None
    if current_rule is not None:
        next_version = int(current_rule["version_no"]) + 1
        rule_code = str(current_rule["rule_code"])
        before_payload = {
            "rule_id": int(current_rule["id"]),
            "version_no": int(current_rule["version_no"]),
            "k_rent": float(current_rule["k_rent"]),
            "k_deposit": float(current_rule["k_deposit"]),
            "d_floor": int(current_rule["d_floor"]),
            "used_demand_factor": float(current_rule["used_demand_factor"]),
            "used_cap_ratio": float(current_rule["used_cap_ratio"]),
        }

    ip_address, device_id = get_request_meta(request)
    async with session.begin():
        if current_rule is not None:
            await session.execute(
                text(
                    """
                    UPDATE price_rule
                    SET
                        status = 'retired',
                        valid_to = :valid_to,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :rule_id;
                    """
                ),
                {"valid_to": now_iso, "rule_id": int(current_rule["id"])},
            )

        await session.execute(
            text(
                """
                INSERT INTO price_rule (
                    rule_code,
                    version_no,
                    status,
                    k_rent,
                    k_deposit,
                    d_floor,
                    used_demand_factor,
                    used_cap_ratio,
                    valid_from,
                    valid_to,
                    created_by_user_id,
                    activated_by_user_id,
                    note,
                    activated_at
                )
                VALUES (
                    :rule_code,
                    :version_no,
                    'active',
                    :k_rent,
                    :k_deposit,
                    :d_floor,
                    :used_demand_factor,
                    :used_cap_ratio,
                    :valid_from,
                    NULL,
                    :created_by_user_id,
                    :activated_by_user_id,
                    :note,
                    :activated_at
                );
                """
            ),
            {
                "rule_code": rule_code,
                "version_no": next_version,
                "k_rent": payload.k_rent,
                "k_deposit": payload.k_deposit,
                "d_floor": payload.d_floor,
                "used_demand_factor": payload.used_demand_factor,
                "used_cap_ratio": payload.used_cap_ratio,
                "valid_from": now_iso,
                "created_by_user_id": auth.user_id,
                "activated_by_user_id": auth.user_id,
                "note": payload.note,
                "activated_at": now_iso,
            },
        )
        rule_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
        new_rule_id = int(rule_id_result.scalar_one())

        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="PRICE_RULE_UPDATED",
            entity_type="price_rule",
            entity_id=str(new_rule_id),
            before=before_payload,
            after={
                "rule_id": new_rule_id,
                "version_no": next_version,
                "k_rent": payload.k_rent,
                "k_deposit": payload.k_deposit,
                "d_floor": payload.d_floor,
                "used_demand_factor": payload.used_demand_factor,
                "used_cap_ratio": payload.used_cap_ratio,
                "note": payload.note,
            },
            ip_address=ip_address,
            device_id=device_id,
        )

    return success_response(
        ActivePriceRulePayload(
            rule_id=new_rule_id,
            version_no=next_version,
            k_rent=payload.k_rent,
            k_deposit=payload.k_deposit,
            d_floor=payload.d_floor,
            used_demand_factor=payload.used_demand_factor,
            used_cap_ratio=payload.used_cap_ratio,
            note=payload.note,
            activated_at=now_iso,
        )
    )


@router.post("/pricing/bulk-update", response_model=ResponseEnvelope[BulkPriceUpdatePayload])
async def apply_bulk_price_update(
    payload: BulkPriceUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[BulkPriceUpdatePayload]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    rows_result = await session.execute(
        text(
            """
            SELECT id, p_sell_new
            FROM volume
            WHERE deleted_at IS NULL;
            """
        )
    )
    rows = rows_result.mappings().all()
    if not rows:
        return success_response(
            BulkPriceUpdatePayload(
                total_volumes=0,
                affected_volumes=0,
                percent_delta=payload.percent_delta,
                min_new_price=0,
                max_new_price=0,
            )
        )

    multiplier = 1.0 + (payload.percent_delta / 100.0)
    planned_updates: list[tuple[int, int, int]] = []
    for row in rows:
        old_price = int(row["p_sell_new"])
        new_price = max(int(round(old_price * multiplier)), 1000)
        if new_price != old_price:
            planned_updates.append((int(row["id"]), old_price, new_price))

    if planned_updates:
        async with session.begin():
            for volume_id, _old_price, new_price in planned_updates:
                await session.execute(
                    text(
                        """
                        UPDATE volume
                        SET
                            p_sell_new = :new_price,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :volume_id;
                        """
                    ),
                    {"new_price": new_price, "volume_id": volume_id},
                )

            ip_address, device_id = get_request_meta(request)
            await write_audit_log(
                session,
                actor_user_id=auth.user_id,
                action="PRICING_BULK_UPDATE_APPLIED",
                entity_type="volume",
                entity_id="batch",
                before={
                    "total_volumes": len(rows),
                    "affected_volumes": len(planned_updates),
                },
                after={
                    "percent_delta": payload.percent_delta,
                    "reason": payload.reason,
                    "sample_changes": [
                        {
                            "volume_id": volume_id,
                            "old_price": old_price,
                            "new_price": new_price,
                        }
                        for volume_id, old_price, new_price in planned_updates[:10]
                    ],
                },
                ip_address=ip_address,
                device_id=device_id,
            )

    min_new = min((new_price for _volume_id, _old_price, new_price in planned_updates), default=0)
    max_new = max((new_price for _volume_id, _old_price, new_price in planned_updates), default=0)

    return success_response(
        BulkPriceUpdatePayload(
            total_volumes=len(rows),
            affected_volumes=len(planned_updates),
            percent_delta=payload.percent_delta,
            min_new_price=min_new,
            max_new_price=max_new,
        )
    )

