from __future__ import annotations

from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
import uuid

from app.api.v1.dependencies import AuthContext, get_auth_context
from app.api.v1.endpoints._common import get_request_meta, to_iso_z, utc_now
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services import (
    compute_sell_price,
    get_cached_response,
    store_cached_response,
    write_audit_log,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


class ReserveInventoryItemRequest(BaseModel):
    item_id: str = Field(min_length=1)
    customer_id: int = Field(gt=0)
    reservation_minutes: int = Field(ge=1, le=240)
    request_id: str = Field(min_length=6, max_length=128)


class ReserveInventoryItemPayload(BaseModel):
    reservation_id: str
    item_id: str
    customer_id: str
    status: Literal["active", "expired", "converted", "cancelled"]
    reserved_at: str
    reservation_expire_at: str


class InventoryItemListItem(BaseModel):
    id: str  # backendItemId
    name: str  # title name + volume number
    code: str  # sku or barcode
    price: int
    status: str
    type: str

class ConvertToRentalRequest(BaseModel):
    volume_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)
    request_id: str = Field(min_length=6, max_length=128)

class ConvertToRentalPayload(BaseModel):
    volume_id: int
    converted_quantity: int
    new_skus: list[str]


@router.post(
    "/reservations",
    response_model=ResponseEnvelope[ReserveInventoryItemPayload],
)
async def reserve_inventory_item(
    payload: ReserveInventoryItemRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[ReserveInventoryItemPayload] | dict[str, object]:
    auth.require_role("cashier", "manager")
    auth.require_scope("inventory:reserve")

    cached = await get_cached_response(
        session,
        scope="inventory.reserve",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload
    if session.in_transaction():
        await session.rollback()

    now = utc_now()
    now_iso = to_iso_z(now)
    expire_at_iso = to_iso_z(now + timedelta(minutes=payload.reservation_minutes))

    async with session.begin():
        customer_result = await session.execute(
            text(
                """
                SELECT id, blacklist_flag
                FROM customer
                WHERE id = :customer_id AND deleted_at IS NULL;
                """
            ),
            {"customer_id": payload.customer_id},
        )
        customer_row = customer_result.mappings().first()
        if customer_row is None:
            raise AppError(
                code="CUSTOMER_NOT_FOUND",
                message="Khong tim thay khach hang cho yeu cau giu cho.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if int(customer_row["blacklist_flag"]) == 1:
            raise AppError(
                code="CUSTOMER_BLACKLISTED",
                message="Khach hang dang nam trong danh sach blacklist.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        await session.execute(
            text(
                """
                UPDATE item
                SET
                    status = 'available',
                    reserved_by_customer_id = NULL,
                    reserved_at = NULL,
                    reservation_expire_at = NULL,
                    version_no = version_no + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :item_id
                  AND status = 'reserved'
                  AND reservation_expire_at IS NOT NULL
                  AND reservation_expire_at <= :now_iso;
                """
            ),
            {"item_id": payload.item_id, "now_iso": now_iso},
        )

        await session.execute(
            text(
                """
                UPDATE reservation
                SET status = 'expired'
                WHERE item_id = :item_id
                  AND status = 'active'
                  AND expire_at <= :now_iso;
                """
            ),
            {"item_id": payload.item_id, "now_iso": now_iso},
        )

        lock_result = await session.execute(
            text(
                """
                UPDATE item
                SET
                    status = 'reserved',
                    reserved_by_customer_id = :customer_id,
                    reserved_at = :now_iso,
                    reservation_expire_at = :expire_at_iso,
                    version_no = version_no + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :item_id
                  AND deleted_at IS NULL
                  AND status = 'available';
                """
            ),
            {
                "customer_id": payload.customer_id,
                "now_iso": now_iso,
                "expire_at_iso": expire_at_iso,
                "item_id": payload.item_id,
            },
        )
        if lock_result.rowcount != 1:
            raise AppError(
                code="ITEM_NOT_AVAILABLE",
                message="Item khong o trang thai san sang de giu cho.",
                status_code=status.HTTP_409_CONFLICT,
            )

        await session.execute(
            text(
                """
                INSERT INTO reservation (
                    item_id,
                    customer_id,
                    status,
                    reserved_at,
                    expire_at,
                    converted_to,
                    created_by_user_id
                )
                VALUES (
                    :item_id,
                    :customer_id,
                    'active',
                    :reserved_at,
                    :expire_at,
                    NULL,
                    :created_by_user_id
                );
                """
            ),
            {
                "item_id": payload.item_id,
                "customer_id": payload.customer_id,
                "reserved_at": now_iso,
                "expire_at": expire_at_iso,
                "created_by_user_id": auth.user_id,
            },
        )
        reservation_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
        reservation_id = int(reservation_id_result.scalar_one())

        ip_address, device_id = get_request_meta(request)
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="RESERVATION_CREATED",
            entity_type="reservation",
            entity_id=str(reservation_id),
            before=None,
            after={
                "item_id": payload.item_id,
                "customer_id": payload.customer_id,
                "status": "active",
                "expire_at": expire_at_iso,
            },
            ip_address=ip_address,
            device_id=device_id,
        )

    envelope = success_response(
        ReserveInventoryItemPayload(
            reservation_id=str(reservation_id),
            item_id=payload.item_id,
            customer_id=str(payload.customer_id),
            status="active",
            reserved_at=now_iso,
            reservation_expire_at=expire_at_iso,
        )
    )

    try:
        async with session.begin():
            await store_cached_response(
                session,
                scope="inventory.reserve",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        cached = await get_cached_response(
            session,
            scope="inventory.reserve",
            request_id=payload.request_id,
        )
        if cached is not None:
            return cached.payload
        raise

    return envelope
@router.get("/items", response_model=ResponseEnvelope[list[InventoryItemListItem]])
async def list_inventory_items(
    q: str | None = None,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[InventoryItemListItem]]:
    auth.require_role("cashier", "manager")
    auth.require_scope("inventory:read")

    query_str = """
        SELECT
            v.isbn AS item_id,
            t.name AS title_name,
            v.volume_number,
            v.isbn AS isbn,
            'available' AS status,
            100 AS condition_level,
            'retail' AS type
        FROM volume v
        JOIN title t ON v.title_id = t.id
        WHERE v.deleted_at IS NULL AND v.retail_stock > 0 AND v.isbn IS NOT NULL
        
        UNION ALL
        
        SELECT
            i.id AS item_id,
            t.name AS title_name,
            v.volume_number,
            v.isbn AS isbn,
            i.status,
            i.condition_level,
            'rental' AS type
        FROM item i
        JOIN volume v ON i.volume_id = v.id
        JOIN title t ON v.title_id = t.id
        WHERE i.deleted_at IS NULL
    """
    
    params: dict[str, object] = {}
    if q:
        query_str = f"SELECT * FROM ({query_str}) WHERE title_name LIKE :q OR item_id LIKE :q OR isbn LIKE :q"
        params["q"] = f"%{q}%"
        
    query_str += " ORDER BY title_name ASC, volume_number ASC LIMIT 200"

    result = await session.execute(text(query_str), params)
    rows = result.mappings().all()

    items = [
        InventoryItemListItem(
            id=row["item_id"],
            name=f"{row['title_name']} Tập {row['volume_number']}",
            code=row["isbn"] or row["item_id"],
            price=compute_sell_price(condition_level=int(row["condition_level"])),
            status=row["status"],
            type=row["type"],
        )
        for row in rows
    ]

    return success_response(items)

@router.post("/convert-to-rental", response_model=ResponseEnvelope[ConvertToRentalPayload])
async def convert_to_rental(
    payload: ConvertToRentalRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[ConvertToRentalPayload] | dict[str, object]:
    auth.require_role("manager")
    auth.require_scope("inventory:write")

    cached = await get_cached_response(session, scope="inventory.convert", request_id=payload.request_id)
    if cached is not None:
        return cached.payload

    if session.in_transaction():
        await session.rollback()

    async with session.begin():
        vol_result = await session.execute(
            text("SELECT id, retail_stock FROM volume WHERE id = :vid AND deleted_at IS NULL"),
            {"vid": payload.volume_id}
        )
        volume_row = vol_result.mappings().first()
        if not volume_row:
            raise AppError(code="VOLUME_NOT_FOUND", message="Khong tim thay tap truyen.", status_code=404)
            
        if volume_row["retail_stock"] < payload.quantity:
            raise AppError(code="INSUFFICIENT_STOCK", message="Ton kho khong du de chuyen doi sang thue.", status_code=409)

        await session.execute(
            text("UPDATE volume SET retail_stock = retail_stock - :qty, updated_at = CURRENT_TIMESTAMP WHERE id = :vid"),
            {"qty": payload.quantity, "vid": payload.volume_id}
        )

        new_skus = []
        for _ in range(payload.quantity):
            new_sku = f"RNT-{payload.volume_id}-{uuid.uuid4().hex[:6].upper()}"
            new_skus.append(new_sku)
            await session.execute(
                text(
                    """INSERT INTO item (id, volume_id, condition_level, status, health_percent) 
                       VALUES (:id, :vid, 100, 'available', 100)"""
                ),
                {"id": new_sku, "vid": payload.volume_id}
            )

        ip_addr, device = get_request_meta(request)
        await write_audit_log(session, actor_user_id=auth.user_id, action="INVENTORY_TO_RENTAL", entity_type="volume", entity_id=str(payload.volume_id), before={"retail_stock": volume_row["retail_stock"]}, after={"retail_stock": volume_row["retail_stock"] - payload.quantity, "new_skus": new_skus}, ip_address=ip_addr, device_id=device)

    envelope = success_response(ConvertToRentalPayload(volume_id=payload.volume_id, converted_quantity=payload.quantity, new_skus=new_skus))
    try:
        async with session.begin():
            await store_cached_response(session, scope="inventory.convert", request_id=payload.request_id, status_code=200, payload=envelope.model_dump())
    except IntegrityError:
        pass
        
    return envelope

