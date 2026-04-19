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
from app.services import get_cached_response, store_cached_response, write_audit_log
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
