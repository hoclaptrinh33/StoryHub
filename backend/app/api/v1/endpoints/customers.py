from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, Depends, Path, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.dependencies import AuthContext, get_auth_context
from app.api.v1.endpoints._common import get_request_meta
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services import get_cached_response, store_cached_response, write_audit_log

router = APIRouter(prefix="/customers", tags=["crm"])

_PHONE_PATTERN = re.compile(r"^[0-9]{9,15}$")


class UpsertCustomerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    membership_level: Literal["standard", "silver", "gold", "vip", "regular"]
    address: str | None = None
    deposit_delta: int = 0
    debt_delta: int = 0
    blacklist_flag: bool | None = None
    request_id: str = Field(min_length=6, max_length=128)
    phone: str | None = None


class UpsertCustomerPayload(BaseModel):
    customer_id: str
    phone: str
    name: str
    membership_level: str
    deposit_balance: int
    debt: int
    blacklist_flag: bool
    updated_at: str


class CustomerListItem(BaseModel):
    id: int
    name: str
    phone: str
    membership_level: str
    deposit_balance: int
    debt: int
    blacklist_flag: bool
    address: str | None = None


def _ensure_phone_valid(phone: str) -> None:
    if not _PHONE_PATTERN.match(phone):
        raise AppError(
            code="INVALID_PHONE",
            message="So dien thoai khong dung dinh dang hop le.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@router.get("/", response_model=ResponseEnvelope[list[CustomerListItem]])
async def list_customers(
    q: str | None = None,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[CustomerListItem]]:
    auth.require_role("cashier", "manager")
    auth.require_scope("crm:read")

    query_str = """
        SELECT
            id,
            name,
            phone,
            membership_level,
            deposit_balance,
            debt,
            blacklist_flag,
            address
        FROM customer
        WHERE deleted_at IS NULL
    """
    params: dict[str, object] = {}

    if q:
        query_str += " AND (name LIKE :q OR phone LIKE :q)"
        params["q"] = f"%{q}%"

    query_str += " ORDER BY name ASC LIMIT 100"

    result = await session.execute(text(query_str), params)
    rows = result.mappings().all()

    customers = [
        CustomerListItem(
            id=row["id"],
            name=row["name"],
            phone=row["phone"],
            membership_level=row["membership_level"],
            deposit_balance=row["deposit_balance"],
            debt=row["debt"],
            blacklist_flag=bool(row["blacklist_flag"]),
            address=row["address"],
        )
        for row in rows
    ]

    return success_response(customers)


@router.put("/{phone}", response_model=ResponseEnvelope[UpsertCustomerPayload])
async def upsert_customer_profile(
    payload: UpsertCustomerRequest,
    request: Request,
    phone: str = Path(min_length=9, max_length=15),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[UpsertCustomerPayload] | dict[str, object]:
    auth.require_role("cashier", "manager")
    auth.require_scope("crm:write")

    if payload.phone is not None and payload.phone != phone:
        raise AppError(
            code="INVALID_PHONE",
            message="So dien thoai trong body khong khop voi duong dan.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    _ensure_phone_valid(phone)

    cached = await get_cached_response(
        session,
        scope="crm.upsert",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload
    if session.in_transaction():
        await session.rollback()

    async with session.begin():
        existing_result = await session.execute(
            text(
                """
                SELECT
                    id,
                    name,
                    phone,
                    address,
                    membership_level,
                    deposit_balance,
                    debt,
                    blacklist_flag,
                    updated_at
                FROM customer
                WHERE phone = :phone AND deleted_at IS NULL;
                """
            ),
            {"phone": phone},
        )
        existing_row = existing_result.mappings().first()

        before_payload = dict(existing_row) if existing_row is not None else None

        if existing_row is None:
            if payload.deposit_delta < 0 or payload.debt_delta < 0:
                raise AppError(
                    code="NEGATIVE_BALANCE_NOT_ALLOWED",
                    message="Khong the tao khach moi voi so du coc hoac cong no am.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            blacklist_flag = (
                bool(payload.blacklist_flag) if payload.blacklist_flag is not None else False
            )
            await session.execute(
                text(
                    """
                    INSERT INTO customer (
                        name,
                        phone,
                        address,
                        membership_level,
                        deposit_balance,
                        debt,
                        blacklist_flag,
                        created_at,
                        updated_at,
                        deleted_at
                    )
                    VALUES (
                        :name,
                        :phone,
                        :address,
                        :membership_level,
                        :deposit_balance,
                        :debt,
                        :blacklist_flag,
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP,
                        NULL
                    );
                    """
                ),
                {
                    "name": payload.name,
                    "phone": phone,
                    "address": payload.address,
                    "membership_level": payload.membership_level,
                    "deposit_balance": payload.deposit_delta,
                    "debt": payload.debt_delta,
                    "blacklist_flag": 1 if blacklist_flag else 0,
                },
            )
            customer_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
            customer_id = int(customer_id_result.scalar_one())
        else:
            if int(existing_row["blacklist_flag"]) == 1 and auth.role != "manager":
                sensitive_mutation = (
                    payload.deposit_delta != 0
                    or payload.debt_delta != 0
                    or payload.blacklist_flag is False
                    or payload.membership_level != existing_row["membership_level"]
                )
                if sensitive_mutation:
                    raise AppError(
                        code="BLACKLISTED_CUSTOMER_MUTATION_DENIED",
                        message="Khong duoc cap nhat truong nhay cam cho khach blacklist.",
                        status_code=status.HTTP_403_FORBIDDEN,
                    )

            if (
                int(existing_row["blacklist_flag"]) == 1
                and payload.blacklist_flag is False
                and auth.role != "manager"
            ):
                raise AppError(
                    code="BLACKLISTED_CUSTOMER_MUTATION_DENIED",
                    message="Chi manager moi co the go blacklist cho khach hang.",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            new_deposit = int(existing_row["deposit_balance"]) + payload.deposit_delta
            new_debt = int(existing_row["debt"]) + payload.debt_delta
            if new_deposit < 0 or new_debt < 0:
                raise AppError(
                    code="NEGATIVE_BALANCE_NOT_ALLOWED",
                    message="So du coc hoac cong no sau cap nhat khong hop le.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            next_blacklist_flag = (
                int(existing_row["blacklist_flag"])
                if payload.blacklist_flag is None
                else int(payload.blacklist_flag)
            )

            await session.execute(
                text(
                    """
                    UPDATE customer
                    SET
                        name = :name,
                        address = :address,
                        membership_level = :membership_level,
                        deposit_balance = :deposit_balance,
                        debt = :debt,
                        blacklist_flag = :blacklist_flag,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :customer_id;
                    """
                ),
                {
                    "name": payload.name,
                    "address": payload.address,
                    "membership_level": payload.membership_level,
                    "deposit_balance": new_deposit,
                    "debt": new_debt,
                    "blacklist_flag": next_blacklist_flag,
                    "customer_id": int(existing_row["id"]),
                },
            )
            customer_id = int(existing_row["id"])

        updated_result = await session.execute(
            text(
                """
                SELECT
                    id,
                    phone,
                    name,
                    membership_level,
                    deposit_balance,
                    debt,
                    blacklist_flag,
                    updated_at
                FROM customer
                WHERE id = :customer_id;
                """
            ),
            {"customer_id": customer_id},
        )
        updated_row = updated_result.mappings().one()

        ip_address, device_id = get_request_meta(request)
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="CUSTOMER_UPSERTED",
            entity_type="customer",
            entity_id=str(customer_id),
            before=before_payload,
            after=dict(updated_row),
            ip_address=ip_address,
            device_id=device_id,
        )

    envelope = success_response(
        UpsertCustomerPayload(
            customer_id=str(customer_id),
            phone=str(updated_row["phone"]),
            name=str(updated_row["name"]),
            membership_level=str(updated_row["membership_level"]),
            deposit_balance=int(updated_row["deposit_balance"]),
            debt=int(updated_row["debt"]),
            blacklist_flag=bool(updated_row["blacklist_flag"]),
            updated_at=str(updated_row["updated_at"]),
        )
    )

    try:
        async with session.begin():
            await store_cached_response(
                session,
                scope="crm.upsert",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        cached = await get_cached_response(
            session, scope="crm.upsert", request_id=payload.request_id
        )
        if cached is not None:
            return cached.payload
        raise

    return envelope


# ==========================================
# ADMIN-ONLY ENDPOINTS (Owner chỉ)
# ==========================================

class AdminCustomerOverrideRequest(BaseModel):
    """Chỉ dùng bởi Owner để ghi đè trực tiếp giá trị tuyệt đối."""
    deposit_balance: int | None = None  # Ghi đè số dư cọc
    debt: int | None = None             # Ghi đè công nợ
    blacklist_flag: bool | None = None  # Bật/tắt blacklist
    reason: str = Field(min_length=5, max_length=300, description="Lý do ghi đè (bắt buộc để audit)")


@router.get("/all", response_model=ResponseEnvelope[list[CustomerListItem]])
async def list_all_customers_admin(
    q: str | None = None,
    blacklisted_only: bool = False,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[CustomerListItem]]:
    """Admin view: toàn bộ khách hàng, không giới hạn số lượng, dành cho Owner."""
    auth.require_role("owner")
    auth.require_scope("admin:read")

    query_str = """
        SELECT id, name, phone, membership_level,
               deposit_balance, debt, blacklist_flag, address
        FROM customer
        WHERE deleted_at IS NULL
    """
    params: dict[str, object] = {}

    if q:
        query_str += " AND (name LIKE :q OR phone LIKE :q)"
        params["q"] = f"%{q}%"

    if blacklisted_only:
        query_str += " AND blacklist_flag = 1"

    query_str += " ORDER BY updated_at DESC LIMIT 1000"

    result = await session.execute(text(query_str), params)
    rows = result.mappings().all()

    customers = [
        CustomerListItem(
            id=row["id"],
            name=row["name"],
            phone=row["phone"],
            membership_level=row["membership_level"],
            deposit_balance=row["deposit_balance"],
            debt=row["debt"],
            blacklist_flag=bool(row["blacklist_flag"]),
            address=row["address"],
        )
        for row in rows
    ]
    return success_response(customers)


@router.patch("/{customer_id}/admin-override", response_model=ResponseEnvelope[dict[str, object]])
async def admin_override_customer(
    customer_id: int,
    payload: AdminCustomerOverrideRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[dict[str, object]]:
    """Owner ghi đè trực tiếp công nợ, tiền cọc hoặc blacklist (bypass validation thông thường)."""
    auth.require_role("owner")
    auth.require_scope("admin:write")

    if all(v is None for v in [payload.deposit_balance, payload.debt, payload.blacklist_flag]):
        raise AppError(
            code="NO_CHANGES",
            message="Vui lòng chỉ định ít nhất một trường cần thay đổi.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Lấy dữ liệu hiện tại để audit
    old_result = await session.execute(
        text("SELECT id, name, deposit_balance, debt, blacklist_flag FROM customer WHERE id = :id AND deleted_at IS NULL"),
        {"id": customer_id},
    )
    old_row = old_result.mappings().first()
    if not old_row:
        raise AppError(
            code="CUSTOMER_NOT_FOUND",
            message="Không tìm thấy khách hàng.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Xây dựng câu UPDATE động
    set_clauses: list[str] = ["updated_at = CURRENT_TIMESTAMP"]
    params: dict[str, object] = {"id": customer_id}

    if payload.deposit_balance is not None:
        if payload.deposit_balance < 0:
            raise AppError(code="INVALID_VALUE", message="Tiền cọc không thể âm.", status_code=status.HTTP_400_BAD_REQUEST)
        set_clauses.append("deposit_balance = :deposit_balance")
        params["deposit_balance"] = payload.deposit_balance

    if payload.debt is not None:
        if payload.debt < 0:
            raise AppError(code="INVALID_VALUE", message="Công nợ không thể âm.", status_code=status.HTTP_400_BAD_REQUEST)
        set_clauses.append("debt = :debt")
        params["debt"] = payload.debt

    if payload.blacklist_flag is not None:
        set_clauses.append("blacklist_flag = :blacklist_flag")
        params["blacklist_flag"] = 1 if payload.blacklist_flag else 0

    ip_address, device_id = get_request_meta(request)

    async with session.begin():
        await session.execute(
            text(f"UPDATE customer SET {', '.join(set_clauses)} WHERE id = :id"),
            params,
        )
        # Ghi audit log (note lưu vào after_json)
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="ADMIN_CUSTOMER_OVERRIDE",
            entity_type="customer",
            entity_id=str(customer_id),
            before={
                "deposit_balance": old_row["deposit_balance"],
                "debt": old_row["debt"],
                "blacklist_flag": bool(old_row["blacklist_flag"]),
            },
            after={
                **{k: v for k, v in payload.model_dump().items() if v is not None and k != "reason"},
                "_reason": payload.reason,
            },
            ip_address=ip_address,
            device_id=device_id,
        )

    return success_response({"status": "overridden", "customer_id": customer_id})

class CustomerSpendingItem(BaseModel):
    id: int
    name: str
    phone: str
    membership_level: str
    deposit_balance: int
    debt: int
    blacklist_flag: bool
    total_spent: int
    spending_tier: str


@router.get("/spending-stats", response_model=ResponseEnvelope[list[CustomerSpendingItem]])
async def get_customer_spending_stats(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[CustomerSpendingItem]]:
    """Lấy danh sách khách hàng kèm tổng chi tiêu và xếp loại — Owner only."""
    auth.require_role("owner")
    auth.require_scope("admin:read")

    # Tính tổng chi tiêu: (Tổng hóa đơn bán lẻ) + (Tổng phí thuê thực tế đã tất toán)
    query = """
        SELECT 
            c.id, c.name, c.phone, c.membership_level, c.deposit_balance, c.debt, c.blacklist_flag,
            (
                COALESCE((
                    SELECT SUM(po.grand_total) 
                    FROM pos_order po 
                    WHERE po.customer_id = c.id AND po.deleted_at IS NULL AND po.status = 'completed'
                ), 0)
                +
                COALESCE((
                    SELECT SUM(rs.total_fee) 
                    FROM rental_settlement rs 
                    JOIN rental_contract rc ON rs.contract_id = rc.id 
                    WHERE rc.customer_id = c.id AND rc.deleted_at IS NULL
                ), 0)
            ) as total_spent
        FROM customer c
        WHERE c.deleted_at IS NULL
        ORDER BY total_spent DESC
    """
    
    result = await session.execute(text(query))
    rows = result.mappings().all()

    def get_tier(spent: int) -> str:
        if spent >= 5000000: return "vip"
        if spent >= 2000000: return "gold"
        if spent >= 500000: return "silver"
        return "bronze"

    stats = [
        CustomerSpendingItem(
            **dict(row),
            spending_tier=get_tier(row["total_spent"])
        )
        for row in rows
    ]

    return success_response(stats)
