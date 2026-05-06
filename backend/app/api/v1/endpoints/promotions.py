from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.dependencies import AuthContext, get_auth_context
from app.api.v1.endpoints._common import get_request_meta
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services import write_audit_log

router = APIRouter(prefix="/promotions", tags=["promotions"])

# ==========================================
# VOUCHER (Mã giảm giá)
# ==========================================

class VoucherCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    voucher_type: str = Field(pattern="^(percent|amount)$")
    value: int = Field(gt=0)
    min_spend: int = Field(default=0, ge=0)
    max_discount: int | None = None
    max_uses: int | None = None
    start_at: str | None = None
    end_at: str | None = None

class VoucherPatch(BaseModel):
    is_active: bool | None = None
    value: int | None = Field(default=None, gt=0)
    min_spend: int | None = Field(default=None, ge=0)
    max_discount: int | None = None
    max_uses: int | None = None
    end_at: str | None = None


@router.get("/vouchers", response_model=ResponseEnvelope[list[dict[str, Any]]])
async def list_vouchers(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[dict[str, Any]]]:
    """Danh sách toàn bộ voucher — chỉ Owner xem."""
    auth.require_role("owner")
    auth.require_scope("admin:read")

    result = await session.execute(
        text("SELECT * FROM voucher ORDER BY created_at DESC")
    )
    return success_response([dict(r) for r in result.mappings().all()])


@router.post("/vouchers", response_model=ResponseEnvelope[dict[str, Any]])
async def create_voucher(
    payload: VoucherCreate,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    """Tạo mã giảm giá mới."""
    auth.require_role("owner")
    auth.require_scope("admin:write")

    # Kiểm tra code trùng
    existing = await session.execute(text("SELECT id FROM voucher WHERE code = :code"), {"code": payload.code.upper()})
    if existing.first():
        raise AppError(code="VOUCHER_CODE_EXISTS", message=f"Mã '{payload.code}' đã tồn tại.", status_code=status.HTTP_409_CONFLICT)

    if session.in_transaction():
        await session.rollback()

    ip_address, device_id = get_request_meta(request)

    async with session.begin():
        await session.execute(
            text("""
                INSERT INTO voucher (code, voucher_type, value, min_spend, max_discount, max_uses, start_at, end_at)
                VALUES (:code, :voucher_type, :value, :min_spend, :max_discount, :max_uses, :start_at, :end_at)
            """),
            {
                "code": payload.code.upper(),
                "voucher_type": payload.voucher_type,
                "value": payload.value,
                "min_spend": payload.min_spend,
                "max_discount": payload.max_discount,
                "max_uses": payload.max_uses,
                "start_at": payload.start_at,
                "end_at": payload.end_at,
            }
        )
        new_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
        new_id = int(new_id_result.scalar_one())
        await write_audit_log(
            session, actor_user_id=auth.user_id, action="VOUCHER_CREATED",
            entity_type="voucher", entity_id=str(new_id),
            before=None, after=payload.model_dump(), ip_address=ip_address, device_id=device_id,
        )

    return success_response({"id": new_id, "code": payload.code.upper()})


@router.patch("/vouchers/{voucher_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def update_voucher(
    voucher_id: int,
    payload: VoucherPatch,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    """Cập nhật voucher (kích hoạt/tắt, sửa giá trị...)."""
    auth.require_role("owner")
    auth.require_scope("admin:write")

    existing = await session.execute(text("SELECT * FROM voucher WHERE id = :id"), {"id": voucher_id})
    row = existing.mappings().first()
    if not row:
        raise AppError(code="VOUCHER_NOT_FOUND", message="Không tìm thấy voucher.", status_code=status.HTTP_404_NOT_FOUND)

    set_clauses = ["updated_at = CURRENT_TIMESTAMP"]
    params: dict[str, object] = {"id": voucher_id}

    for field, col in [("is_active", "is_active"), ("value", "value"), ("min_spend", "min_spend"),
                       ("max_discount", "max_discount"), ("max_uses", "max_uses"), ("end_at", "end_at")]:
        val = getattr(payload, field)
        if val is not None:
            set_clauses.append(f"{col} = :{col}")
            params[col] = (1 if val else 0) if isinstance(val, bool) else val

    if session.in_transaction():
        await session.rollback()

    ip_address, device_id = get_request_meta(request)

    async with session.begin():
        await session.execute(text(f"UPDATE voucher SET {', '.join(set_clauses)} WHERE id = :id"), params)
        await write_audit_log(
            session, actor_user_id=auth.user_id, action="VOUCHER_UPDATED",
            entity_type="voucher", entity_id=str(voucher_id),
            before=dict(row), after={k: v for k, v in payload.model_dump().items() if v is not None},
            ip_address=ip_address, device_id=device_id,
        )

    return success_response({"status": "updated", "voucher_id": voucher_id})


@router.delete("/vouchers/{voucher_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def delete_voucher(
    voucher_id: int,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    """Xóa vĩnh viễn voucher (chỉ khi chưa được sử dụng)."""
    auth.require_role("owner")
    auth.require_scope("admin:write")

    existing = await session.execute(text("SELECT id, current_uses FROM voucher WHERE id = :id"), {"id": voucher_id})
    row = existing.mappings().first()
    if not row:
        raise AppError(code="VOUCHER_NOT_FOUND", message="Không tìm thấy voucher.", status_code=status.HTTP_404_NOT_FOUND)

    if int(row["current_uses"]) > 0:
        raise AppError(
            code="VOUCHER_IN_USE",
            message=f"Voucher đã được sử dụng {row['current_uses']} lần, không thể xóa. Hãy tắt (is_active=false) thay vì xóa.",
            status_code=status.HTTP_409_CONFLICT,
        )

    if session.in_transaction():
        await session.rollback()

    ip_address, device_id = get_request_meta(request)
    async with session.begin():
        await session.execute(text("DELETE FROM voucher WHERE id = :id"), {"id": voucher_id})
        await write_audit_log(
            session, actor_user_id=auth.user_id, action="VOUCHER_DELETED",
            entity_type="voucher", entity_id=str(voucher_id),
            before=dict(row), after=None, ip_address=ip_address, device_id=device_id,
        )

    return success_response({"status": "deleted", "voucher_id": voucher_id})


@router.get("/vouchers/lookup", response_model=ResponseEnvelope[dict[str, Any]])
async def lookup_voucher(
    code: str,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    """Tra cứu mã voucher và trả về thông tin chi tiết nếu hợp lệ."""
    auth.require_role("cashier", "manager", "owner")
    auth.require_scope("admin:read")

    q = code.upper().strip()
    result = await session.execute(
        text("""
            SELECT id, code, voucher_type, value, min_spend, max_discount, 
                   max_uses, current_uses, is_active, start_at, end_at
            FROM voucher
            WHERE code = :code
        """),
        {"code": q}
    )
    row = result.mappings().first()
    if not row:
        raise AppError(code="VOUCHER_NOT_FOUND", message="Mã giảm giá không tồn tại.", status_code=status.HTTP_404_NOT_FOUND)

    if not row["is_active"]:
        raise AppError(code="VOUCHER_INACTIVE", message="Mã giảm giá này đã bị tạm ngưng.", status_code=status.HTTP_400_BAD_REQUEST)

    # Check date
    now = datetime.now().isoformat()
    if row["start_at"] and row["start_at"] > now:
        raise AppError(code="VOUCHER_NOT_STARTED", message="Mã giảm giá chưa đến thời gian áp dụng.", status_code=status.HTTP_400_BAD_REQUEST)
    if row["end_at"] and row["end_at"] < now:
        raise AppError(code="VOUCHER_EXPIRED", message="Mã giảm giá đã hết hạn.", status_code=status.HTTP_400_BAD_REQUEST)

    # Check uses
    if row["max_uses"] is not None and row["current_uses"] >= row["max_uses"]:
        raise AppError(code="VOUCHER_LIMIT_REACHED", message="Mã giảm giá đã hết lượt sử dụng.", status_code=status.HTTP_400_BAD_REQUEST)

    return success_response(dict(row))


# ==========================================
# AUTOMATIC PROMOTION (Khuyến mãi tự động)
# ==========================================

class AutoPromoCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    day_of_week: int = Field(ge=0, le=6)  # 0=Mon, 6=Sun
    discount_percent: int = Field(ge=1, le=100)

class AutoPromoToggle(BaseModel):
    is_active: bool


class AutoPromoPatch(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=255)
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    discount_percent: int | None = Field(default=None, ge=1, le=100)
    is_active: bool | None = None


@router.get("/auto-promotions", response_model=ResponseEnvelope[list[dict[str, Any]]])
async def list_auto_promotions(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[dict[str, Any]]]:
    auth.require_role("owner")
    auth.require_scope("admin:read")

    result = await session.execute(text("SELECT * FROM automatic_promotion ORDER BY day_of_week ASC"))
    return success_response([dict(r) for r in result.mappings().all()])


@router.post("/auto-promotions", response_model=ResponseEnvelope[dict[str, Any]])
async def create_auto_promotion(
    payload: AutoPromoCreate,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    ip_address, device_id = get_request_meta(request)
    async with session.begin():
        await session.execute(
            text("INSERT INTO automatic_promotion (name, day_of_week, discount_percent) VALUES (:name, :dow, :pct)"),
            {"name": payload.name, "dow": payload.day_of_week, "pct": payload.discount_percent},
        )
        new_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
        new_id = int(new_id_result.scalar_one())
        await write_audit_log(
            session, actor_user_id=auth.user_id, action="AUTO_PROMO_CREATED",
            entity_type="automatic_promotion", entity_id=str(new_id),
            before=None, after=payload.model_dump(), ip_address=ip_address, device_id=device_id,
        )

    return success_response({"id": new_id})


@router.patch("/auto-promotions/{promo_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def update_auto_promotion(
    promo_id: int,
    payload: AutoPromoPatch,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    existing = await session.execute(
        text(
            """
            SELECT id, name, day_of_week, discount_percent, is_active
            FROM automatic_promotion
            WHERE id = :id
            """
        ),
        {"id": promo_id},
    )
    row = existing.mappings().first()
    if not row:
        raise AppError(
            code="PROMO_NOT_FOUND",
            message="KhĂ´ng tĂ¬m tháº¥y chÆ°Æ¡ng trĂ¬nh khuyáº¿n mĂ£i.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise AppError(
            code="NO_CHANGES",
            message="Vui lĂ²ng cung cáº¥p Ă­t nháº¥t má»™t thuá»™c tĂ­nh cáº§n cáº­p nháº­t.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    set_clauses = ["updated_at = CURRENT_TIMESTAMP"]
    params: dict[str, object] = {"id": promo_id}
    for field_name in ("name", "day_of_week", "discount_percent", "is_active"):
        value = updates.get(field_name)
        if value is None:
            continue
        set_clauses.append(f"{field_name} = :{field_name}")
        if field_name == "is_active" and isinstance(value, bool):
            params[field_name] = 1 if value else 0
        else:
            params[field_name] = value

    if session.in_transaction():
        await session.rollback()

    ip_address, device_id = get_request_meta(request)
    async with session.begin():
        await session.execute(
            text(f"UPDATE automatic_promotion SET {', '.join(set_clauses)} WHERE id = :id"),
            params,
        )
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="AUTO_PROMO_UPDATED",
            entity_type="automatic_promotion",
            entity_id=str(promo_id),
            before=dict(row),
            after=updates,
            ip_address=ip_address,
            device_id=device_id,
        )

    return success_response({"status": "updated", "promo_id": promo_id})


@router.patch("/auto-promotions/{promo_id}/toggle", response_model=ResponseEnvelope[dict[str, Any]])
async def toggle_auto_promotion(
    promo_id: int,
    payload: AutoPromoToggle,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    existing = await session.execute(text("SELECT id, is_active FROM automatic_promotion WHERE id = :id"), {"id": promo_id})
    if not existing.first():
        raise AppError(code="PROMO_NOT_FOUND", message="Không tìm thấy chương trình khuyến mãi.", status_code=status.HTTP_404_NOT_FOUND)

    if session.in_transaction():
        await session.rollback()

    ip_address, device_id = get_request_meta(request)
    async with session.begin():
        await session.execute(
            text("UPDATE automatic_promotion SET is_active = :active, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
            {"active": 1 if payload.is_active else 0, "id": promo_id},
        )
        await write_audit_log(
            session, actor_user_id=auth.user_id,
            action="AUTO_PROMO_ACTIVATED" if payload.is_active else "AUTO_PROMO_DEACTIVATED",
            entity_type="automatic_promotion", entity_id=str(promo_id),
            before=None, after={"is_active": payload.is_active}, ip_address=ip_address, device_id=device_id,
        )

    return success_response({"status": "updated", "promo_id": promo_id, "is_active": payload.is_active})


@router.delete("/auto-promotions/{promo_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def delete_auto_promotion(
    promo_id: int,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    ip_address, device_id = get_request_meta(request)
    async with session.begin():
        await session.execute(text("DELETE FROM automatic_promotion WHERE id = :id"), {"id": promo_id})
        await write_audit_log(
            session, actor_user_id=auth.user_id, action="AUTO_PROMO_DELETED",
            entity_type="automatic_promotion", entity_id=str(promo_id),
            before=None, after=None, ip_address=ip_address, device_id=device_id,
        )

    return success_response({"status": "deleted", "promo_id": promo_id})
# ==========================================
# PROMOTION EVENT (Sự kiện Giảm giá)
# ==========================================

class PromotionEventCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    discount_type: str = Field(pattern="^(percent|amount)$")
    discount_value: int = Field(gt=0)
    start_date: str
    end_date: str
    is_active: bool = True
    description: str | None = None

class PromotionEventPatch(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=255)
    discount_type: str | None = Field(default=None, pattern="^(percent|amount)$")
    discount_value: int | None = Field(default=None, gt=0)
    start_date: str | None = None
    end_date: str | None = None
    is_active: bool | None = None
    description: str | None = None

class PromotionItemAdd(BaseModel):
    target_type: str = Field(pattern="^(title|volume)$")
    target_id: int


@router.get("/events", response_model=ResponseEnvelope[list[dict[str, Any]]])
async def list_promotion_events(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[dict[str, Any]]]:
    """Danh sách sự kiện giảm giá — Owner only."""
    auth.require_role("owner")
    auth.require_scope("admin:read")

    result = await session.execute(
        text("SELECT * FROM promotion ORDER BY created_at DESC")
    )
    return success_response([dict(r) for r in result.mappings().all()])


@router.post("/events", response_model=ResponseEnvelope[dict[str, Any]])
async def create_promotion_event(
    payload: PromotionEventCreate,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    ip_address, device_id = get_request_meta(request)

    # Ensure columns exist (Self-healing for missing migration columns)
    try:
        async with session.begin():
            # Check description
            try: await session.execute(text("ALTER TABLE promotion ADD COLUMN description TEXT"))
            except Exception: pass
            
            # Check is_active
            try: await session.execute(text("ALTER TABLE promotion ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            except Exception: pass
    except Exception:
        pass

    async with session.begin():
        await session.execute(
            text("""
                INSERT INTO promotion (name, discount_type, discount_value, start_date, end_date, is_active, description)
                VALUES (:name, :dtype, :dval, :start, :end, :active, :desc)
            """),
            {
                "name": payload.name,
                "dtype": payload.discount_type,
                "dval": payload.discount_value,
                "start": payload.start_date,
                "end": payload.end_date,
                "active": 1 if payload.is_active else 0,
                "desc": payload.description,
            }
        )
        new_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
        new_id = int(new_id_result.scalar_one())
        
        await write_audit_log(
            session, actor_user_id=auth.user_id, action="PROMO_EVENT_CREATED",
            entity_type="promotion", entity_id=str(new_id),
            before=None, after=payload.model_dump(), ip_address=ip_address, device_id=device_id,
        )

    return success_response({"id": new_id})


@router.patch("/events/{promo_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def update_promotion_event(
    promo_id: int,
    payload: PromotionEventPatch,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    existing = await session.execute(text("SELECT * FROM promotion WHERE id = :id"), {"id": promo_id})
    row = existing.mappings().first()
    if not row:
        raise AppError(code="PROMO_NOT_FOUND", message="Không tìm thấy sự kiện giảm giá.", status_code=status.HTTP_404_NOT_FOUND)

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise AppError(code="NO_CHANGES", message="Vui lòng cung cấp ít nhất một thuộc tính cần cập nhật.", status_code=status.HTTP_400_BAD_REQUEST)

    set_clauses = ["updated_at = CURRENT_TIMESTAMP"]
    params: dict[str, object] = {"id": promo_id}
    for field, value in updates.items():
        set_clauses.append(f"{field} = :{field}")
        params[field] = (1 if value else 0) if isinstance(value, bool) else value

    ip_address, device_id = get_request_meta(request)
    async with session.begin():
        await session.execute(text(f"UPDATE promotion SET {', '.join(set_clauses)} WHERE id = :id"), params)
        await write_audit_log(
            session, actor_user_id=auth.user_id, action="PROMO_EVENT_UPDATED",
            entity_type="promotion", entity_id=str(promo_id),
            before=dict(row), after=updates, ip_address=ip_address, device_id=device_id,
        )

    return success_response({"id": promo_id})


@router.delete("/events/{promo_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def delete_promotion_event(
    promo_id: int,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    ip_address, device_id = get_request_meta(request)
    async with session.begin():
        # promotion_items will be deleted by ON DELETE CASCADE if configured in DB,
        # but let's be explicit if not sure about manual DB creation details.
        await session.execute(text("DELETE FROM promotion_item WHERE promotion_id = :id"), {"id": promo_id})
        await session.execute(text("DELETE FROM promotion WHERE id = :id"), {"id": promo_id})
        
        await write_audit_log(
            session, actor_user_id=auth.user_id, action="PROMO_EVENT_DELETED",
            entity_type="promotion", entity_id=str(promo_id),
            before=None, after=None, ip_address=ip_address, device_id=device_id,
        )

    return success_response({"id": promo_id})


@router.get("/events/{promo_id}/items", response_model=ResponseEnvelope[list[dict[str, Any]]])
async def list_promotion_items(
    promo_id: int,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[dict[str, Any]]]:
    auth.require_role("owner")
    auth.require_scope("admin:read")

    # We join with title or volume to show names in UI
    query = """
        SELECT pi.*, 
               CASE 
                 WHEN pi.target_type = 'title' THEN (SELECT name FROM title WHERE id = pi.target_id)
                 WHEN pi.target_type = 'volume' THEN (SELECT 'Vol ' || volume_number || ' - ' || (SELECT name FROM title WHERE id = v.title_id) FROM volume v WHERE v.id = pi.target_id)
               END as target_name
        FROM promotion_item pi
        WHERE pi.promotion_id = :promo_id
    """
    result = await session.execute(text(query), {"promo_id": promo_id})
    return success_response([dict(r) for r in result.mappings().all()])


@router.post("/events/{promo_id}/items", response_model=ResponseEnvelope[dict[str, Any]])
async def add_promotion_item(
    promo_id: int,
    payload: PromotionItemAdd,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    ip_address, device_id = get_request_meta(request)
    async with session.begin():
        await session.execute(
            text("""
                INSERT OR IGNORE INTO promotion_item (promotion_id, target_type, target_id)
                VALUES (:pid, :ttype, :tid)
            """),
            {"pid": promo_id, "ttype": payload.target_type, "tid": payload.target_id}
        )
        
        await write_audit_log(
            session, actor_user_id=auth.user_id, action="PROMO_ITEM_ADDED",
            entity_type="promotion", entity_id=str(promo_id),
            before=None, after=payload.model_dump(), ip_address=ip_address, device_id=device_id,
        )

    return success_response({"status": "added"})


@router.delete("/events/{promo_id}/items/{item_id}", response_model=ResponseEnvelope[dict[str, Any]])
async def remove_promotion_item(
    promo_id: int,
    item_id: int,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, Any]]:
    auth.require_role("owner")
    auth.require_scope("admin:write")

    ip_address, device_id = get_request_meta(request)
    async with session.begin():
        await session.execute(
            text("DELETE FROM promotion_item WHERE id = :id AND promotion_id = :pid"),
            {"id": item_id, "pid": promo_id}
        )
        
        await write_audit_log(
            session, actor_user_id=auth.user_id, action="PROMO_ITEM_REMOVED",
            entity_type="promotion", entity_id=str(promo_id),
            before={"item_id": item_id}, after=None, ip_address=ip_address, device_id=device_id,
        )

    return success_response({"status": "removed"})
