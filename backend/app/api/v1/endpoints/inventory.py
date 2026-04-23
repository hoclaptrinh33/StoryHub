from __future__ import annotations

import asyncio
import json
import uuid
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Path, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.dependencies import AuthContext, get_auth_context, get_event_publisher
from app.api.v1.endpoints._common import get_request_meta, to_iso_z, utc_now
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services import (
    EventPublisher,
    compute_sell_price,
    get_cached_response,
    is_remote_image_url,
    save_cover_from_base64,
    save_cover_from_url,
    store_cached_response,
    write_audit_log,
)

router = APIRouter(prefix="/kho", tags=["kho"])


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
    volume_id: int | None = None
    name: str  # title name + volume number
    code: str  # sku or barcode
    price: int
    stock_quantity: int | None = None
    status: str
    type: str


class InventoryItemStatusPayload(BaseModel):
    item_id: str
    status: str
    changed_at: str
    item_type: Literal["rental", "retail"]

class ConvertToRentalRequest(BaseModel):
    volume_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)
    request_id: str = Field(min_length=6, max_length=128)

class ConvertToRentalPayload(BaseModel):
    volume_id: int
    converted_quantity: int
    new_skus: list[str]

class CreateVolumeRequest(BaseModel):
    title_name: str = Field(min_length=1)
    author: str = Field(default="Unknown")
    description: str | None = Field(default=None, max_length=5000)
    cover_url: str | None = Field(default=None, max_length=500)
    categories: list[str] = Field(default_factory=list)
    page_count: int | None = Field(default=None, ge=1)
    published_date: str | None = Field(default=None, max_length=50)
    volume_number: int = Field(gt=0)
    isbn: str = Field(min_length=5, max_length=20)
    retail_stock: int = Field(ge=0)
    p_sell_new: int = Field(default=0, ge=0)
    request_id: str = Field(min_length=6, max_length=128)

class CreateVolumePayload(BaseModel):
    volume_id: int
    title_id: int
    isbn: str
    retail_stock: int


class UpdateVolumePriceRequest(BaseModel):
    p_sell_new: int = Field(ge=1000, le=100_000_000)
    request_id: str = Field(min_length=6, max_length=128)


class UpdateVolumePricePayload(BaseModel):
    volume_id: int
    isbn: str
    old_price: int
    new_price: int
    updated_at: str


class ImportCoverRequest(BaseModel):
    isbn: str = Field(min_length=5, max_length=20)
    image_url: str | None = Field(default=None, max_length=2000)
    image_base64: str | None = Field(default=None, max_length=12_000_000)
    request_id: str = Field(min_length=6, max_length=128)

    @model_validator(mode="after")
    def validate_source(self) -> ImportCoverRequest:
        has_url = bool((self.image_url or "").strip())
        has_base64 = bool((self.image_base64 or "").strip())
        if has_url == has_base64:
            raise ValueError("Chi duoc truyen mot nguon anh: image_url hoac image_base64.")
        return self


class ImportCoverPayload(BaseModel):
    cover_url: str
    source: Literal["url", "base64"]


@router.post(
    "/reservations",
    response_model=ResponseEnvelope[ReserveInventoryItemPayload],
)
async def reserve_inventory_item(
    payload: ReserveInventoryItemRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
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
                message="Không tìm thấy thông tin khách hàng để thực hiện yêu cầu giữ chỗ.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if int(customer_row["blacklist_flag"]) == 1:
            raise AppError(
                code="CUSTOMER_BLACKLISTED",
                message="Khách hàng này hiện đang nằm trong danh sách hạn chế (Blacklist). Không thể thực hiện giữ chỗ.",
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
                message="Sản phẩm hiện không ở trạng thái sẵn sàng để thực hiện giữ chỗ.",
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

    await event_publisher.publish_item_status_changed(
        item_id=payload.item_id,
        old_status="available",
        new_status="reserved",
        changed_at=now_iso,
        source_api="inventory_reserve_item_v1",
        changed_by=auth.user_id,
        branch_id=auth.branch_id,
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
            v.id AS volume_id,
            v.isbn AS item_id,
            t.name AS title_name,
            v.volume_number,
            v.isbn AS isbn,
            v.p_sell_new AS p_sell_new,
            v.retail_stock AS stock_quantity,
            CASE 
                WHEN v.p_sell_new <= 0 THEN 'unready'
                WHEN v.retail_stock > 0 THEN 'available'
                ELSE 'out_of_stock'
            END AS status,
            100 AS condition_level,
            'retail' AS type
        FROM volume v
        JOIN title t ON v.title_id = t.id
        WHERE v.deleted_at IS NULL AND v.isbn IS NOT NULL
        
        UNION ALL
        
        SELECT
            v.id AS volume_id,
            i.id AS item_id,
            t.name AS title_name,
            v.volume_number,
            v.isbn AS isbn,
            v.p_sell_new AS p_sell_new,
            1 AS stock_quantity,
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
            volume_id=row["volume_id"],
            name=f"{row['title_name']} Tập {row['volume_number']}",
            code=row["isbn"] or row["item_id"],
            price=compute_sell_price(
                condition_level=int(row["condition_level"]),
                p_sell_new=int(row["p_sell_new"]),
            ),
            stock_quantity=(
                int(row["stock_quantity"])
                if row.get("stock_quantity") is not None
                else None
            ),
            status=row["status"],
            type=row["type"],
        )
        for row in rows
    ]

    return success_response(items)


@router.get(
    "/items/{item_id}/status",
    response_model=ResponseEnvelope[InventoryItemStatusPayload],
)
async def get_inventory_item_status(
    item_id: str = Path(min_length=1, max_length=64),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[InventoryItemStatusPayload]:
    auth.require_role("cashier", "manager", "owner")
    auth.require_scope("inventory:read")

    rental_item_result = await session.execute(
        text(
            """
            SELECT id, status, updated_at
            FROM item
            WHERE id = :item_id AND deleted_at IS NULL;
            """
        ),
        {"item_id": item_id},
    )
    rental_item = rental_item_result.mappings().first()
    if rental_item is not None:
        return success_response(
            InventoryItemStatusPayload(
                item_id=str(rental_item["id"]),
                status=str(rental_item["status"]),
                changed_at=str(rental_item["updated_at"]),
                item_type="rental",
            )
        )

    retail_item_result = await session.execute(
        text(
            """
            SELECT
                isbn,
                retail_stock,
                p_sell_new,
                updated_at
            FROM volume
            WHERE isbn = :item_id AND deleted_at IS NULL;
            """
        ),
        {"item_id": item_id},
    )
    retail_item = retail_item_result.mappings().first()
    if retail_item is not None:
        if int(retail_item["p_sell_new"]) <= 0:
            retail_status = "unready"
        else:
            retail_status = "available" if int(retail_item["retail_stock"]) > 0 else "out_of_stock"
            
        return success_response(
            InventoryItemStatusPayload(
                item_id=str(retail_item["isbn"]),
                status=retail_status,
                changed_at=str(retail_item["updated_at"]),
                item_type="retail",
            )
        )

    raise AppError(
        code="ITEM_NOT_FOUND",
        message="Không tìm thấy sản phẩm yêu cầu trong hệ thống dữ liệu.",
        status_code=status.HTTP_404_NOT_FOUND,
    )

@router.post("/convert-to-rental", response_model=ResponseEnvelope[ConvertToRentalPayload])
async def convert_to_rental(
    payload: ConvertToRentalRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> ResponseEnvelope[ConvertToRentalPayload] | dict[str, object]:
    auth.require_role("manager","owner")
    auth.require_scope("inventory:write")
    print(f"[DEBUG] Request ID: {payload.request_id}")

    cached = await get_cached_response(session, scope="inventory.convert", request_id=payload.request_id)
    if cached is not None:
        return cached.payload

    if session.in_transaction():
        await session.rollback()

    async with session.begin():
        vol_result = await session.execute(
            text("SELECT id, retail_stock FROM volume WHERE CAST(id AS INTEGER) = CAST(:vid AS INTEGER) AND deleted_at IS NULL"),
            {"vid": payload.volume_id}
        )

        volume_row = vol_result.mappings().first()
        if not volume_row:
            raise AppError(
                code="VOLUME_NOT_FOUND", 
                message=f"Không tìm thấy tập truyện tương ứng với ID={payload.volume_id}. Vui lòng liên hệ hỗ trợ kỹ thuật.", 
                status_code=404
            )

            
        if volume_row["retail_stock"] < payload.quantity:
            raise AppError(code="INSUFFICIENT_STOCK", message="Số lượng tồn kho hiện tại không đủ để thực hiện chuyển đổi sang hàng thuê.", status_code=409)

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
        
    await event_publisher.publish_volume_stock_updated(
        volume_id=payload.volume_id,
        new_stock=volume_row["retail_stock"] - payload.quantity,
        branch_id=auth.branch_id
    )
    for sku in new_skus:
        await event_publisher.publish_item_mutated(item_id=sku, action="created", branch_id=auth.branch_id)

    return envelope


@router.post("/covers/import", response_model=ResponseEnvelope[ImportCoverPayload])
async def import_cover_image(
    payload: ImportCoverRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[ImportCoverPayload] | dict[str, object]:
    auth.require_role("manager")
    auth.require_scope("inventory:write")

    cached = await get_cached_response(
        session,
        scope="inventory.import_cover",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload

    if session.in_transaction():
        await session.rollback()

    source: Literal["url", "base64"] = "url"
    try:
        if (payload.image_url or "").strip():
            source = "url"
            cover_url = await asyncio.to_thread(
                save_cover_from_url,
                payload.isbn,
                str(payload.image_url),
            )
        else:
            source = "base64"
            cover_url = await asyncio.to_thread(
                save_cover_from_base64,
                payload.isbn,
                str(payload.image_base64),
            )
    except ValueError as exc:
        raise AppError(
            code="COVER_IMPORT_FAILED",
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    ip_addr, device = get_request_meta(request)
    async with session.begin():
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="INVENTORY_COVER_IMPORTED",
            entity_type="cover",
            entity_id=payload.isbn,
            before=None,
            after={
                "isbn": payload.isbn,
                "source": source,
                "cover_url": cover_url,
            },
            ip_address=ip_addr,
            device_id=device,
        )

    envelope = success_response(ImportCoverPayload(cover_url=cover_url, source=source))
    try:
        async with session.begin():
            await store_cached_response(
                session,
                scope="inventory.import_cover",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        cached = await get_cached_response(
            session,
            scope="inventory.import_cover",
            request_id=payload.request_id,
        )
        if cached is not None:
            return cached.payload
        raise

    return envelope

@router.post("/volumes", response_model=ResponseEnvelope[CreateVolumePayload])
async def create_volume(
    payload: CreateVolumeRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> ResponseEnvelope[CreateVolumePayload] | dict[str, object]:
    auth.require_role("manager","owner")
    auth.require_scope("inventory:write")

    normalized_title_name = payload.title_name.strip()
    normalized_author = payload.author.strip() or "Unknown"
    normalized_description = (payload.description or "").strip()
    normalized_cover_url = (payload.cover_url or "").strip()
    normalized_categories = [
        category.strip()
        for category in payload.categories
        if isinstance(category, str) and category.strip()
    ]
    normalized_genre = ", ".join(normalized_categories)
    normalized_published_date = (payload.published_date or "").strip()
    normalized_page_count = payload.page_count if payload.page_count and payload.page_count > 0 else None

    if normalized_cover_url and is_remote_image_url(normalized_cover_url):
        try:
            normalized_cover_url = await asyncio.to_thread(
                save_cover_from_url,
                payload.isbn,
                normalized_cover_url,
            )
        except ValueError as exc:
            raise AppError(
                code="COVER_IMPORT_FAILED",
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from exc

    has_extended_metadata = bool(
        normalized_description
        or normalized_cover_url
        or normalized_categories
        or normalized_page_count is not None
        or normalized_published_date
    )

    cached = await get_cached_response(session, scope="inventory.create_volume", request_id=payload.request_id)
    if cached is not None:
        return cached.payload

    if session.in_transaction():
        await session.rollback()

    async with session.begin():
        title_res = await session.execute(
            text("SELECT id FROM title WHERE name = :name COLLATE NOCASE AND deleted_at IS NULL"),
            {"name": normalized_title_name}
        )
        title_row = title_res.mappings().first()
        if title_row:
            title_id = title_row["id"]
            await session.execute(
                text(
                    """
                    UPDATE title
                    SET
                        author = CASE
                            WHEN (author IS NULL OR TRIM(author) = '' OR author = 'Unknown') AND :author <> ''
                                THEN :author
                            ELSE author
                        END,
                        description = CASE
                            WHEN :description <> '' THEN :description
                            ELSE description
                        END,
                        cover_url = CASE
                            WHEN :cover_url <> '' THEN :cover_url
                            ELSE cover_url
                        END,
                        genre = CASE
                            WHEN :genre <> '' THEN :genre
                            ELSE genre
                        END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :title_id
                    """
                ),
                {
                    "title_id": title_id,
                    "author": normalized_author,
                    "description": normalized_description,
                    "cover_url": normalized_cover_url,
                    "genre": normalized_genre,
                },
            )
        else:
            await session.execute(
                text(
                    """
                    INSERT INTO title (name, author, description, cover_url, genre)
                    VALUES (:name, :author, :description, :cover_url, :genre)
                    """
                ),
                {
                    "name": normalized_title_name,
                    "author": normalized_author,
                    "description": normalized_description or None,
                    "cover_url": normalized_cover_url or None,
                    "genre": normalized_genre or None,
                }
            )
            title_id_res = await session.execute(text("SELECT last_insert_rowid() AS value"))
            title_id = int(title_id_res.scalar_one())
            
        try:
            await session.execute(
                text(
                    """
                    INSERT INTO volume (title_id, volume_number, isbn, retail_stock, p_sell_new)
                    VALUES (:tid, :vnum, :isbn, :stock, :price)
                    """
                ),
                {
                    "tid": title_id,
                    "vnum": payload.volume_number,
                    "isbn": payload.isbn,
                    "stock": payload.retail_stock,
                    "price": payload.p_sell_new
                }
            )
            vol_id_res = await session.execute(text("SELECT last_insert_rowid() AS value"))
            volume_id = int(vol_id_res.scalar_one())
        except IntegrityError:
            await session.execute(
                text(
                    """
                    UPDATE volume 
                    SET retail_stock = retail_stock + :qty, isbn = :isbn, updated_at = CURRENT_TIMESTAMP
                    WHERE title_id = :tid AND volume_number = :vnum
                    """
                ),
                {
                    "qty": payload.retail_stock,
                    "isbn": payload.isbn,
                    "tid": title_id,
                    "vnum": payload.volume_number
                }
            )
            vol_id_res = await session.execute(
                text("SELECT id FROM volume WHERE title_id = :tid AND volume_number = :vnum"),
                {"tid": title_id, "vnum": payload.volume_number}
            )
            volume_id = vol_id_res.mappings().first()["id"]

        if has_extended_metadata:
            metadata_payload = {
                "title": normalized_title_name,
                "authors": [entry.strip() for entry in normalized_author.split(",") if entry.strip()],
                "description": normalized_description,
                "imageLinks": normalized_cover_url,
                "pageCount": normalized_page_count,
                "categories": normalized_categories,
                "publishedDate": normalized_published_date,
                "language": "vi",
            }
            await session.execute(
                text(
                    """
                    INSERT INTO metadata_cache (query_key, source, payload_json, confidence, cached_at, expire_at)
                    VALUES (:query_key, :source, :payload_json, :confidence, CURRENT_TIMESTAMP, datetime('now', '+365 day'))
                    ON CONFLICT(query_key)
                    DO UPDATE SET
                        payload_json = excluded.payload_json,
                        confidence = excluded.confidence,
                        cached_at = CURRENT_TIMESTAMP,
                        expire_at = datetime('now', '+365 day')
                    """
                ),
                {
                    "query_key": f"google_books:isbn:{payload.isbn}",
                    "source": "google_books_vi",
                    "payload_json": json.dumps(metadata_payload, ensure_ascii=False),
                    "confidence": 1.0,
                },
            )

        ip_addr, device = get_request_meta(request)
        await write_audit_log(session, actor_user_id=auth.user_id, action="INVENTORY_VOLUME_CREATED", entity_type="volume", entity_id=str(volume_id), before=None, after={"title_id": title_id, "isbn": payload.isbn, "stock": payload.retail_stock, "metadata_cached": has_extended_metadata}, ip_address=ip_addr, device_id=device)

    envelope = success_response(CreateVolumePayload(volume_id=volume_id, title_id=title_id, isbn=payload.isbn, retail_stock=payload.retail_stock))
    try:
        async with session.begin():
            await store_cached_response(session, scope="inventory.create_volume", request_id=payload.request_id, status_code=200, payload=envelope.model_dump())
    except IntegrityError:
        pass
        
    await event_publisher.publish_inventory_data_changed(reason="volume_created", branch_id=auth.branch_id)
    return envelope


@router.patch("/volumes/{volume_id}/price", response_model=ResponseEnvelope[UpdateVolumePricePayload])
async def update_volume_price(
    payload: UpdateVolumePriceRequest,
    request: Request,
    volume_id: int = Path(gt=0),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> ResponseEnvelope[UpdateVolumePricePayload] | dict[str, object]:
    auth.require_role("manager", "owner")
    auth.require_scope("inventory:write")

    cached = await get_cached_response(
        session,
        scope="inventory.update_price",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload

    if session.in_transaction():
        await session.rollback()

    now_iso = to_iso_z(utc_now())
    async with session.begin():
        volume_result = await session.execute(
            text(
                """
                SELECT id, isbn, p_sell_new
                FROM volume
                WHERE id = :volume_id
                  AND deleted_at IS NULL;
                """
            ),
            {"volume_id": volume_id},
        )
        volume_row = volume_result.mappings().first()
        if volume_row is None:
            raise AppError(
                code="VOLUME_NOT_FOUND",
                message="Khong tim thay tap truyen can cap nhat gia.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        old_price = int(volume_row["p_sell_new"])
        await session.execute(
            text(
                """
                UPDATE volume
                SET p_sell_new = :new_price,
                    updated_at = :updated_at
                WHERE id = :volume_id;
                """
            ),
            {
                "new_price": payload.p_sell_new,
                "updated_at": now_iso,
                "volume_id": volume_id,
            },
        )

        ip_addr, device = get_request_meta(request)
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="INVENTORY_VOLUME_PRICE_UPDATED",
            entity_type="volume",
            entity_id=str(volume_id),
            before={"p_sell_new": old_price},
            after={"p_sell_new": payload.p_sell_new},
            ip_address=ip_addr,
            device_id=device,
        )

        envelope = success_response(
            UpdateVolumePricePayload(
                volume_id=volume_id,
                isbn=str(volume_row["isbn"]),
                old_price=old_price,
                new_price=payload.p_sell_new,
                updated_at=now_iso,
            )
        )

    try:
        async with session.begin():
            await store_cached_response(
                session,
                scope="inventory.update_price",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        cached = await get_cached_response(
            session,
            scope="inventory.update_price",
            request_id=payload.request_id,
        )
        if cached is not None:
            return cached.payload
        raise

    await event_publisher.publish_volume_stock_updated(
        volume_id=volume_id,
        new_stock=int(volume_row["retail_stock"]),
        branch_id=auth.branch_id
    )
    return envelope


# ---------------------------------------------------------------------------
# GET /kho/titles  — Danh sách đầu truyện grouped (title → volumes → items)
# ---------------------------------------------------------------------------

class TitleItemRow(BaseModel):
    id: str
    status: str
    type: str # retail|rental
    condition_level: int
    notes: str | None
    has_barcode: bool  # True = có mã vạch thật → được phép thuê
    version_no: int
    reserved_at: str | None
    reservation_expire_at: str | None


class TitleVolumeRow(BaseModel):
    id: int
    volume_number: int
    isbn: str | None
    p_sell_new: int
    price_rental: int   # = p_sell_new * 5%  (tính tự động)
    price_deposit: int  # = p_sell_new * 30% (tính tự động)
    retail_stock: int
    rental_item_count: int  # số bản sao thuê available
    items: list[TitleItemRow]

class TitleRow(BaseModel):
    id: int
    name: str
    author: str | None
    genre: str | None
    publisher: str | None
    description: str | None
    cover_url: str | None
    volumes: list[TitleVolumeRow]


@router.get("/titles", response_model=ResponseEnvelope[list[TitleRow]])
async def list_titles_with_volumes(
    q: str | None = None,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[TitleRow]]:
    """Trả về toàn bộ đầu truyện kèm volumes và rental items cho trang quản lý kho."""
    auth.require_scope("inventory:read")

    # 1. Lấy danh sách titles
    title_filter = ""
    params: dict[str, object] = {}
    if q:
        title_filter = "WHERE t.deleted_at IS NULL AND t.name LIKE :q"
        params["q"] = f"%{q}%"
    else:
        title_filter = "WHERE t.deleted_at IS NULL"

    title_result = await session.execute(
        text(f"""
            SELECT t.id, t.name, t.author, t.genre, t.publisher, t.description, t.cover_url
            FROM title t
            {title_filter}
            ORDER BY t.name ASC
        """),
        params,
    )
    title_rows = title_result.mappings().all()
    if not title_rows:
        return success_response([])

    title_ids = [int(r["id"]) for r in title_rows]
    id_placeholders = ",".join(str(i) for i in title_ids)

    # 2. Lấy volumes của các titles đó
    vol_result = await session.execute(
        text(f"""
            SELECT id, title_id, volume_number, isbn, p_sell_new, retail_stock
            FROM volume
            WHERE title_id IN ({id_placeholders}) AND deleted_at IS NULL
            ORDER BY title_id ASC, volume_number ASC
        """)
    )
    vol_rows = vol_result.mappings().all()

    volume_ids = [int(r["id"]) for r in vol_rows]

    # 3. Lấy items thuê của các volumes đó
    items_by_volume: dict[int, list[TitleItemRow]] = {}
    rental_count_by_volume: dict[int, int] = {}

    if volume_ids:
        vol_id_placeholders = ",".join(str(i) for i in volume_ids)
        item_result = await session.execute(
            text(f"""
                SELECT id, volume_id, status, condition_level, notes, version_no, reserved_at, reservation_expire_at
                FROM item
                WHERE volume_id IN ({vol_id_placeholders}) AND deleted_at IS NULL

                ORDER BY volume_id ASC, id ASC
            """)
        )
        item_rows = item_result.mappings().all()
        for ir in item_rows:
            vid = int(ir["volume_id"])
            # Có barcode thật = id không bắt đầu bằng "RNT-" (RNT- là auto-gen khi convert)
            # Theo quy tắc: item phải có mã vạch (barcode thật) mới cho thuê
            item_id = str(ir["id"])
            is_real_barcode = not item_id.upper().startswith("RNT-")
            row = TitleItemRow(
                id=item_id,
                status=str(ir["status"]),
                type="rental",
                condition_level=int(ir["condition_level"]),
                notes=ir["notes"],
                has_barcode=is_real_barcode,
                version_no=int(ir["version_no"] or 1),
                reserved_at=str(ir["reserved_at"]) if ir["reserved_at"] else None,
                reservation_expire_at=str(ir["reservation_expire_at"]) if ir["reservation_expire_at"] else None,
            )

            items_by_volume.setdefault(vid, []).append(row)
            if str(ir["status"]) == "available":
                rental_count_by_volume[vid] = rental_count_by_volume.get(vid, 0) + 1

    # 4. Ghép kết quả
    K_RENT = 0.05
    K_DEPOSIT = 0.30

    volumes_by_title: dict[int, list[TitleVolumeRow]] = {}
    for vr in vol_rows:
        tid = int(vr["title_id"])
        vid = int(vr["id"])
        p_sell = int(vr["p_sell_new"] or 0)
        auto_rental = max(int(round(p_sell * K_RENT)), 500)
        volumes_by_title.setdefault(tid, []).append(
            TitleVolumeRow(
                id=vid,
                volume_number=int(vr["volume_number"]),
                isbn=vr["isbn"],
                p_sell_new=p_sell,
                price_rental=auto_rental,
                price_deposit=max(int(round(p_sell * K_DEPOSIT)), 1000),
                retail_stock=int(vr["retail_stock"] or 0),
                rental_item_count=rental_count_by_volume.get(vid, 0),
                items=items_by_volume.get(vid, []),
            )
        )

    result_list = [
        TitleRow(
            id=int(tr["id"]),
            name=str(tr["name"]),
            author=tr["author"],
            genre=tr["genre"],
            publisher=tr["publisher"],
            description=tr["description"],
            cover_url=tr["cover_url"],
            volumes=volumes_by_title.get(int(tr["id"]), []),
        )
        for tr in title_rows
    ]

    return success_response(result_list)
# ---------------------------------------------------------------------------
# CRUD Đầu truyện (Title)
# ---------------------------------------------------------------------------

class TitleMutateRequest(BaseModel):
    name: str = Field(min_length=1)
    author: str | None = None
    description: str | None = None
    genre: str | None = None
    publisher: str | None = None

@router.post("/titles")
async def create_new_title(
    payload: TitleMutateRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    result = await session.execute(
        text("""
            INSERT INTO title (name, author, description, genre, publisher)
            VALUES (:name, :author, :desc, :genre, :pub)
            RETURNING id
        """),
        {"name": payload.name, "author": payload.author, "desc": payload.description, "genre": payload.genre, "pub": payload.publisher}
    )
    new_id = result.scalar()
    await session.commit()
    await write_audit_log(
        session=session,
        actor_user_id=auth.user_id,
        action="CREATE_TITLE",
        entity_type="title",
        entity_id=str(new_id),
        before=None,
        after={"name": payload.name},
        ip_address=None,
        device_id=None,
    )
    await event_publisher.publish_inventory_data_changed(reason="title_created", branch_id=auth.branch_id)
    return success_response({"id": new_id})

@router.put("/titles/{title_id}")
async def update_title(
    title_id: int,
    payload: TitleMutateRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    await session.execute(
        text("""
            UPDATE title
            SET name = :name, author = :author, description = :desc, genre = :genre, publisher = :pub, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id AND deleted_at IS NULL
        """),
        {"id": title_id, "name": payload.name, "author": payload.author, "desc": payload.description, "genre": payload.genre, "pub": payload.publisher}
    )
    await session.commit()
    await write_audit_log(
        session=session,
        actor_user_id=auth.user_id,
        action="UPDATE_TITLE",
        entity_type="title",
        entity_id=str(title_id),
        before=None,
        after=None,
        ip_address=None,
        device_id=None,
    )
    await event_publisher.publish_inventory_data_changed(reason="title_updated", branch_id=auth.branch_id)
    return success_response({"id": title_id})

@router.delete("/titles/{title_id}")
async def delete_title(
    title_id: int,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    await session.execute(
        text("UPDATE title SET deleted_at = CURRENT_TIMESTAMP WHERE id = :id"),
        {"id": title_id}
    )
    await session.execute(
        text("UPDATE volume SET deleted_at = CURRENT_TIMESTAMP WHERE title_id = :id"),
        {"id": title_id}
    )
    await session.execute(
        text("UPDATE item SET deleted_at = CURRENT_TIMESTAMP WHERE volume_id IN (SELECT id FROM volume WHERE title_id = :id)"),
        {"id": title_id}
    )
    await session.commit()
    await write_audit_log(
        session=session,
        actor_user_id=auth.user_id,
        action="DELETE_TITLE",
        entity_type="title",
        entity_id=str(title_id),
        before=None,
        after=None,
        ip_address=None,
        device_id=None,
    )
    await event_publisher.publish_inventory_data_changed(reason="title_deleted", branch_id=auth.branch_id)
    return success_response({"deleted": True})


# ---------------------------------------------------------------------------
# CRUD Tập truyện (Volume)
# ---------------------------------------------------------------------------

class VolumeMutateRequest(BaseModel):
    volume_number: int = Field(gt=0)
    isbn: str | None = None
    p_sell_new: int = Field(ge=0)
    retail_stock: int = Field(ge=0)

@router.put("/volumes/{volume_id}")
async def update_volume(
    volume_id: int,
    payload: VolumeMutateRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    await session.execute(
        text("""
            UPDATE volume
            SET volume_number = :vol_num, isbn = :isbn, p_sell_new = :p_sell, retail_stock = :stock, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id AND deleted_at IS NULL
        """),
        {
            "id": volume_id, 
            "vol_num": payload.volume_number, 
            "isbn": payload.isbn, 
            "p_sell": payload.p_sell_new, 
            "stock": payload.retail_stock
        }
    )
    await session.commit()
    await write_audit_log(
        session=session,
        actor_user_id=auth.user_id,
        action="UPDATE_VOLUME",
        entity_type="volume",
        entity_id=str(volume_id),
        before=None,
        after=None,
        ip_address=None,
        device_id=None,
    )
    await event_publisher.publish_inventory_data_changed(reason="volume_updated", branch_id=auth.branch_id)
    return success_response({"id": volume_id})

@router.delete("/volumes/{volume_id}")
async def delete_volume(
    volume_id: int,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    await session.execute(
        text("UPDATE volume SET deleted_at = CURRENT_TIMESTAMP WHERE id = :id"),
        {"id": volume_id}
    )
    await session.execute(
        text("UPDATE item SET deleted_at = CURRENT_TIMESTAMP WHERE volume_id = :id"),
        {"id": volume_id}
    )
    await session.commit()
    await write_audit_log(
        session=session,
        actor_user_id=auth.user_id,
        action="DELETE_VOLUME",
        entity_type="volume",
        entity_id=str(volume_id),
        before=None,
        after=None,
        ip_address=None,
        device_id=None,
    )
    await event_publisher.publish_inventory_data_changed(reason="volume_deleted", branch_id=auth.branch_id)
    return success_response({"deleted": True})


# ---------------------------------------------------------------------------
# CRUD Bản sao (Item)
# ---------------------------------------------------------------------------

class ItemCreateRequest(BaseModel):
    volume_id: int
    id: str | None = None # barcode. If none, auto-generate RNT-{uuid}
    type: Literal["retail", "rental"] = "retail"
    condition_level: int = Field(ge=0, le=100, default=100)

    notes: str | None = None
    version_no: int = Field(default=1)

class ItemUpdateRequest(BaseModel):
    status: str
    condition_level: int = Field(ge=0, le=100)
    notes: str | None = None

@router.post("/items")
async def create_item(
    request: Request,
    payload: ItemCreateRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session), # noqa: B008
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    item_id = str(payload.id).strip() if (payload.id is not None and str(payload.id).strip()) else f"RNT-{str(uuid.uuid4()).replace('-', '')[:8].upper()}"
    
    # Kiem tra id xem co trung khong
    exist = await session.execute(text("SELECT id FROM item WHERE id = :id"), {"id": item_id})
    if exist.scalar():
        raise AppError(status_code=400, message="Mã bản sao đã tồn tại")

    await session.execute(
        text("""
            INSERT INTO item (id, volume_id, status, condition_level, health_percent, version_no, notes)
            VALUES (:id, :vid, 'available', :cond, :cond, :ver, :notes)
        """),
        {
            "id": item_id,
            "vid": payload.volume_id,
            "cond": payload.condition_level,
            "ver": payload.version_no,
            "notes": payload.notes
        }

    )
    await session.commit()
    await write_audit_log(
        session=session,
        actor_user_id=auth.user_id,
        action="CREATE_ITEM",
        entity_type="item",
        entity_id=item_id,
        before=None,
        after=None,
        ip_address=None,
        device_id=None,
    )
    await event_publisher.publish_item_mutated(item_id=item_id, action="created", branch_id=auth.branch_id)
    return success_response({"id": item_id})

@router.put("/items/{item_id}")
async def update_item(
    item_id: str,
    payload: ItemUpdateRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    await session.execute(
        text("""
            UPDATE item
            SET status = :status, condition_level = :cond, notes = :notes, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id AND deleted_at IS NULL
        """),
        {"id": item_id, "status": payload.status, "cond": payload.condition_level, "notes": payload.notes}
    )
    await session.commit()
    await write_audit_log(
        session=session,
        actor_user_id=auth.user_id,
        action="UPDATE_ITEM",
        entity_type="item",
        entity_id=item_id,
        before=None,
        after=None,
        ip_address=None,
        device_id=None,
    )
    await event_publisher.publish_item_mutated(item_id=item_id, action="updated", branch_id=auth.branch_id)
    return success_response({"id": item_id})

@router.delete("/items/{item_id}")
async def delete_item(
    item_id: str,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    await session.execute(
        text("UPDATE item SET deleted_at = CURRENT_TIMESTAMP WHERE id = :id"),
        {"id": item_id}
    )
    await session.commit()
    await session.commit()
    await write_audit_log(
        session=session,
        actor_user_id=auth.user_id,
        action="DELETE_ITEM",
        entity_type="item",
        entity_id=item_id,
        before=None,
        after=None,
        ip_address=None,
        device_id=None,
    )
    await event_publisher.publish_item_mutated(item_id=item_id, action="deleted", branch_id=auth.branch_id)
    return success_response({"deleted": True})
