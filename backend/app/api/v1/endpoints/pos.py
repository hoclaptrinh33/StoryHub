from __future__ import annotations

from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Path, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.dependencies import (
    AuthContext,
    build_auth_context_from_token,
    get_auth_context,
    get_event_publisher,
)
from app.api.v1.endpoints._common import get_request_meta, parse_iso_datetime, to_iso_z, utc_now
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services import (
    EventPublisher,
    compute_sell_price,
    get_cached_response,
    resolve_active_price_rule,
    store_cached_response,
    write_audit_log,
)

router = APIRouter(prefix="/pos", tags=["pos"])
_OVERRIDE_FLOOR_RATIO = 0.7


class SplitPaymentLine(BaseModel):
    method: Literal["cash", "bank_transfer", "e_wallet", "card"]
    amount: int = Field(gt=0)


class CheckoutOverride(BaseModel):
    new_grand_total: int = Field(gt=0)
    reason_code: Literal[
        "damaged_cover",
        "yellow_pages",
        "missing_insert",
        "complaint_recovery",
        "promo_match",
        "other",
    ]
    reason_note: str | None = Field(default=None, max_length=255)
    manager_approval_token: str = Field(min_length=3, max_length=128)
    manager_auth_method: Literal["pin", "card"] = "pin"


class PosOrderLine(BaseModel):
    item_id: str
    final_sell_price: int
    quantity: int
    line_total: int


class CreatePosOrderRequest(BaseModel):
    customer_id: int | None = Field(default=None, gt=0)
    item_ids: list[str] = Field(min_length=1)
    discount_type: Literal["none", "percent", "amount"]
    discount_value: int = Field(ge=0)
    split_payments: list[SplitPaymentLine] = Field(min_length=1)
    checkout_override: CheckoutOverride | None = None
    note: str | None = None
    request_id: str = Field(min_length=6, max_length=128)

    @model_validator(mode="after")
    def validate_discount_value(self) -> CreatePosOrderRequest:
        if self.discount_type == "percent" and self.discount_value > 100:
            raise ValueError("discount_value must be <= 100 when discount_type is percent")
        if len(set(self.item_ids)) != len(self.item_ids):
            raise ValueError("item_ids must be unique")
        return self


class CreatePosOrderPayload(BaseModel):
    order_id: str
    status: Literal["paid", "cancelled"]
    subtotal: int
    discount_total: int
    grand_total: int
    price_rule_version: int
    price_override_applied: bool
    override_reason_code: str | None = None
    payment_breakdown: list[SplitPaymentLine]
    line_items: list[PosOrderLine]


class RefundItemLine(BaseModel):
    volume_id: int
    quantity: int = Field(default=1, ge=1)


class RefundPosOrderRequest(BaseModel):
    refund_items: list[RefundItemLine] = Field(min_length=1)
    reason: str = Field(min_length=3, max_length=255)
    refund_method: Literal["cash", "bank_transfer", "e_wallet", "original_method"] = (
        "original_method"
    )
    request_id: str = Field(min_length=6, max_length=128)


class RefundPosOrderPayload(BaseModel):
    refund_id: str
    order_id: str
    refunded_total: int
    order_status: Literal["refunded", "partially_refunded"]
    processed_at: str


def _calculate_discount(subtotal: int, discount_type: str, discount_value: int) -> int:
    if discount_type == "none":
        return 0
    if discount_type == "amount":
        return min(discount_value, subtotal)
    return min((subtotal * discount_value) // 100, subtotal)


def _resolve_manager_approval(token: str) -> AuthContext:
    try:
        approval_auth = build_auth_context_from_token(token)
    except AppError as exc:
        raise AppError(
            code="MANAGER_APPROVAL_REQUIRED",
            message="Yêu cầu mã phê duyệt của Quản lý (Manager Token) không hợp lệ để thực hiện ghi đè giá.",
            status_code=status.HTTP_403_FORBIDDEN,
        ) from exc

    if approval_auth.role not in {"manager", "owner"}:
        raise AppError(
            code="MANAGER_APPROVAL_REQUIRED",
            message="Chỉ Quản lý hoặc Chủ cửa hàng mới có quyền phê duyệt thay đổi giá bán trực tiếp.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return approval_auth


@router.post("/orders", response_model=ResponseEnvelope[CreatePosOrderPayload])
async def create_pos_order(
    payload: CreatePosOrderRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> ResponseEnvelope[CreatePosOrderPayload] | dict[str, object]:
    auth.require_role("cashier", "manager")
    auth.require_scope("pos:write")

    cached = await get_cached_response(
        session,
        scope="pos.create_order",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload
    if session.in_transaction():
        await session.rollback()

    now = utc_now()
    now_iso = to_iso_z(now)

    async with session.begin():
        pricing_rule = await resolve_active_price_rule(session)
        item_rows: list[dict[str, object]] = []
        for code in payload.item_ids:
            # 1. Check if it's a specific Item
            item_res = await session.execute(
                text("""
                    SELECT i.id, i.volume_id, i.status, i.reserved_by_customer_id, 
                           i.reservation_expire_at, i.condition_level, v.p_sell_new
                    FROM item i
                    JOIN volume v ON v.id = i.volume_id
                    WHERE i.id = :code AND i.deleted_at IS NULL AND v.deleted_at IS NULL
                """),
                {"code": code},
            )
            row = item_res.mappings().first()

            if row:
                # Same reservation logic as before
                if row["status"] == "reserved" and row["reservation_expire_at"] is not None:
                    expire_at = parse_iso_datetime(str(row["reservation_expire_at"]))
                    if expire_at <= now:
                        await session.execute(
                            text("UPDATE item SET status = 'available', reserved_by_customer_id = NULL, reserved_at = NULL, reservation_expire_at = NULL, version_no = version_no + 1, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                            {"id": code}
                        )
                        row = {**dict(row), "status": "available", "reserved_by_customer_id": None, "reservation_expire_at": None}

                is_reserved_for_customer = (
                    row["status"] == "reserved"
                    and payload.customer_id is not None
                    and row["reserved_by_customer_id"] == payload.customer_id
                )
                if row["status"] != "available" and not is_reserved_for_customer:
                    raise AppError(
                        code="ITEM_NOT_AVAILABLE",
                        message=f"Sản phẩm {code} không sẵn sàng (đang ở trạng thái {row['status']}).",
                        status_code=status.HTTP_409_CONFLICT,
                    )
                item_rows.append(dict(row))
            else:
                # 2. Fallback to Volume ISBN
                vol_res = await session.execute(
                    text("SELECT id, retail_stock, p_sell_new FROM volume WHERE isbn = :isbn AND deleted_at IS NULL"),
                    {"isbn": code},
                )
                vol_row = vol_res.mappings().first()
                if vol_row:
                    # Robust check: try to find an available individual retail item first
                    avail_item_res = await session.execute(
                        text("SELECT id, volume_id, status, condition_level FROM item WHERE volume_id = :vid AND item_type = 'retail' AND status = 'available' AND deleted_at IS NULL LIMIT 1"),
                        {"vid": vol_row["id"]}
                    )
                    avail_item = avail_item_res.mappings().first()
                    
                    if avail_item:
                        item_rows.append({
                            "id": avail_item["id"],
                            "volume_id": vol_row["id"],
                            "status": "available",
                            "reserved_by_customer_id": None,
                            "reservation_expire_at": None,
                            "condition_level": avail_item["condition_level"],
                            "p_sell_new": vol_row["p_sell_new"]
                        })
                    elif int(vol_row["retail_stock"]) > 0:
                        # Sell by quantity only
                        item_rows.append({
                            "id": None, 
                            "volume_id": vol_row["id"],
                            "status": "available",
                            "reserved_by_customer_id": None,
                            "reservation_expire_at": None,
                            "condition_level": 100,
                            "p_sell_new": vol_row["p_sell_new"],
                            "is_qty_only": True
                        })
                    else:
                        raise AppError(
                            code="INSUFFICIENT_STOCK",
                            message=f"ISBN {code} đã hết số lượng hàng bán lẻ.",
                            status_code=status.HTTP_409_CONFLICT,
                        )
                else:
                    raise AppError(
                        code="ITEM_NOT_AVAILABLE",
                        message=f"Không tìm thấy sản phẩm hoặc ISBN: {code}",
                        status_code=status.HTTP_404_NOT_FOUND,
                    )

        line_items: list[PosOrderLine] = []
        line_snapshots: list[dict[str, int | str]] = []
        subtotal = 0
        for item_row in item_rows:
            p_sell_new = int(item_row["p_sell_new"])
            price = compute_sell_price(
                condition_level=int(item_row["condition_level"]),
                p_sell_new=p_sell_new,
                used_demand_factor=pricing_rule.used_demand_factor,
                used_cap_ratio=pricing_rule.used_cap_ratio,
            )
            subtotal += price
            line_items.append(
                PosOrderLine(
                    item_id=str(item_row["id"]) if item_row["id"] is not None else None,
                    final_sell_price=price,
                    quantity=1,
                    line_total=price,
                )
            )
            line_snapshots.append(
                {
                    "item_id": str(item_row["id"]) if item_row["id"] is not None else None,
                    "volume_id": int(item_row["volume_id"]),
                    "p_sell_new": p_sell_new,
                    "final_sell_price": price,
                    "line_total": price,
                }
            )

        discount_total = _calculate_discount(
            subtotal, payload.discount_type, payload.discount_value
        )
        base_grand_total = max(subtotal - discount_total, 0)
        grand_total = base_grand_total
        price_override_applied = False
        override_reason_code: str | None = None
        approved_by_user_id: str | None = None
        approved_via: str | None = None

        if payload.checkout_override is not None:
            approval_auth = _resolve_manager_approval(payload.checkout_override.manager_approval_token)
            override_floor = int(round(base_grand_total * _OVERRIDE_FLOOR_RATIO))
            if payload.checkout_override.new_grand_total < override_floor:
                raise AppError(
                    code="OVERRIDE_BELOW_FLOOR",
                    message="Giá bán sau khi sửa thấp hơn sàn cho phép (tối thiểu 70% giá trị gốc).",
                    status_code=status.HTTP_409_CONFLICT,
                )

            grand_total = payload.checkout_override.new_grand_total
            price_override_applied = True
            override_reason_code = payload.checkout_override.reason_code
            approved_by_user_id = approval_auth.user_id
            approved_via = payload.checkout_override.manager_auth_method

        payment_total = sum(line.amount for line in payload.split_payments)
        if payment_total != grand_total:
            raise AppError(
                code="SPLIT_PAYMENT_MISMATCH",
                message="Tổng giá trị các phương thức thanh toán không khớp với số tiền phải trả.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        for item_row in item_rows:
            # 1. Update individual Item status if exists
            if item_row["id"] is not None:
                lock_result = await session.execute(
                    text(
                        """
                        UPDATE item
                        SET
                            status = 'sold',
                            reserved_by_customer_id = NULL,
                            reserved_at = NULL,
                            reservation_expire_at = NULL,
                            version_no = version_no + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :item_id
                        AND deleted_at IS NULL
                        AND (
                                status = 'available'
                                OR (
                                    status = 'reserved'
                                    AND :customer_id IS NOT NULL
                                    AND reserved_by_customer_id = :customer_id
                                    AND reservation_expire_at > :now_iso
                                )
                        );
                        """
                    ),
                    {
                        "item_id": item_row["id"],
                        "customer_id": payload.customer_id,
                        "now_iso": now_iso,
                    },
                )
                if lock_result.rowcount != 1:
                    raise AppError(
                        code="ORDER_LOCK_CONFLICT",
                        message=f"Không thể khóa sản phẩm {item_row['id']} để tạo đơn hàng. Vui lòng thử lại sau.",
                        status_code=status.HTTP_423_LOCKED,
                    )
            
            # 2. Always decrement Volume stock
            await session.execute(
                text("UPDATE volume SET retail_stock = retail_stock - 1, updated_at = CURRENT_TIMESTAMP WHERE id = :vid"),
                {"vid": item_row["volume_id"]}
            )

        await session.execute(
            text(
                """
                INSERT INTO pos_order (
                    customer_id,
                    status,
                    subtotal,
                    discount_type,
                    discount_value,
                    discount_total,
                    grand_total,
                    paid_total,
                    request_id,
                    created_by_user_id,
                    created_at,
                    updated_at,
                    deleted_at
                )
                VALUES (
                    :customer_id,
                    'paid',
                    :subtotal,
                    :discount_type,
                    :discount_value,
                    :discount_total,
                    :grand_total,
                    :paid_total,
                    :request_id,
                    :created_by_user_id,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP,
                    NULL
                );
                """
            ),
            {
                "customer_id": payload.customer_id,
                "subtotal": subtotal,
                "discount_type": payload.discount_type,
                "discount_value": payload.discount_value,
                "discount_total": discount_total,
                "grand_total": grand_total,
                "paid_total": grand_total,
                "request_id": payload.request_id,
                "created_by_user_id": auth.user_id,
            },
        )
        order_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
        order_id = int(order_id_result.scalar_one())

        for line_snapshot in line_snapshots:
            await session.execute(
                text(
                    """
                    INSERT INTO pos_order_item (
                        order_id,
                        volume_id,
                        final_sell_price,
                        quantity,
                        line_total
                    )
                    VALUES (
                        :order_id,
                        :volume_id,
                        :final_sell_price,
                        :quantity,
                        :line_total
                    );
                    """
                ),
                {
                    "order_id": order_id,
                    "volume_id": line_snapshot["volume_id"],
                    "final_sell_price": line_snapshot["final_sell_price"],
                    "quantity": 1,
                    "line_total": line_snapshot["line_total"],
                },
            )
            pos_order_item_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
            pos_order_item_id = int(pos_order_item_id_result.scalar_one())
            await session.execute(
                text(
                    """
                    INSERT INTO order_item (
                        order_type,
                        pos_order_id,
                        rental_contract_id,
                        pos_order_item_id,
                        rental_item_id,
                        volume_id,
                        item_id,
                        quantity,
                        p_sell_new_snapshot,
                        final_sell_price,
                        line_total,
                        price_rule_id,
                        price_rule_version,
                        override_applied,
                        override_reason_code,
                        override_reason_note,
                        approved_by_user_id,
                        approved_via
                    )
                    VALUES (
                        'sale',
                        :pos_order_id,
                        NULL,
                        :pos_order_item_id,
                        NULL,
                        :volume_id,
                        :item_id,
                        1,
                        :p_sell_new_snapshot,
                        :final_sell_price,
                        :line_total,
                        :price_rule_id,
                        :price_rule_version,
                        :override_applied,
                        :override_reason_code,
                        :override_reason_note,
                        :approved_by_user_id,
                        :approved_via
                    );
                    """
                ),
                {
                    "pos_order_id": order_id,
                    "pos_order_item_id": pos_order_item_id,
                    "volume_id": line_snapshot["volume_id"],
                    "item_id": line_snapshot["item_id"],
                    "p_sell_new_snapshot": line_snapshot["p_sell_new"],
                    "final_sell_price": line_snapshot["final_sell_price"],
                    "line_total": line_snapshot["line_total"],
                    "price_rule_id": pricing_rule.rule_id,
                    "price_rule_version": pricing_rule.version_no,
                    "override_applied": 1 if price_override_applied else 0,
                    "override_reason_code": override_reason_code,
                    "override_reason_note": (
                        payload.checkout_override.reason_note
                        if payload.checkout_override is not None
                        else None
                    ),
                    "approved_by_user_id": approved_by_user_id,
                    "approved_via": approved_via,
                },
            )

        for payment in payload.split_payments:
            await session.execute(
                text(
                    """
                    INSERT INTO pos_payment (order_id, method, amount, paid_at)
                    VALUES (:order_id, :method, :amount, :paid_at);
                    """
                ),
                {
                    "order_id": order_id,
                    "method": payment.method,
                    "amount": payment.amount,
                    "paid_at": now_iso,
                },
            )

        for line_item in line_items:
            if line_item.item_id:
                await session.execute(
                    text(
                        """
                        UPDATE reservation
                        SET status = 'converted', converted_to = 'sold'
                        WHERE item_id = :item_id AND status = 'active';
                        """
                    ),
                    {"item_id": line_item.item_id},
                )

        ip_address, device_id = get_request_meta(request)
        if price_override_applied:
            await write_audit_log(
                session,
                actor_user_id=auth.user_id,
                action="POS_PRICE_OVERRIDE",
                entity_type="pos_order",
                entity_id=str(order_id),
                before={"grand_total": base_grand_total},
                after={
                    "grand_total": grand_total,
                    "reason_code": override_reason_code,
                    "approved_by_user_id": approved_by_user_id,
                    "approved_via": approved_via,
                },
                ip_address=ip_address,
                device_id=device_id,
            )

        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="POS_ORDER_PAID",
            entity_type="pos_order",
            entity_id=str(order_id),
            before=None,
            after={
                "status": "paid",
                "subtotal": subtotal,
                "discount_total": discount_total,
                "grand_total": grand_total,
                "item_ids": [line.item_id for line in line_items],
                "price_rule_version": pricing_rule.version_no,
                "price_override_applied": price_override_applied,
                "override_reason_code": override_reason_code,
            },
            ip_address=ip_address,
            device_id=device_id,
        )

    envelope = success_response(
        CreatePosOrderPayload(
            order_id=str(order_id),
            status="paid",
            subtotal=subtotal,
            discount_total=discount_total,
            grand_total=grand_total,
            price_rule_version=pricing_rule.version_no,
            price_override_applied=price_override_applied,
            override_reason_code=override_reason_code,
            payment_breakdown=payload.split_payments,
            line_items=line_items,
        )
    )

    for item_row in item_rows:
        if item_row["id"]:
            await event_publisher.publish_item_status_changed(
                item_id=str(item_row["id"]),
                old_status=str(item_row["status"]),
                new_status="sold",
                changed_at=now_iso,
                source_api="pos_create_order_v1",
                changed_by=auth.user_id,
                branch_id=auth.branch_id,
            )

    try:
        async with session.begin():
            await store_cached_response(
                session,
                scope="pos.create_order",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        cached = await get_cached_response(
            session,
            scope="pos.create_order",
            request_id=payload.request_id,
        )
        if cached is not None:
            return cached.payload
        raise

    return envelope


@router.post(
    "/orders/{order_id}/refund",
    response_model=ResponseEnvelope[RefundPosOrderPayload],
)
async def refund_pos_order(
    payload: RefundPosOrderRequest,
    request: Request,
    order_id: int = Path(gt=0),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[RefundPosOrderPayload] | dict[str, object]:
    auth.require_role("manager")
    auth.require_scope("pos:refund")

    cached = await get_cached_response(
        session,
        scope="pos.refund_order",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload
    if session.in_transaction():
        await session.rollback()

    now = utc_now()
    now_iso = to_iso_z(now)

    async with session.begin():
        order_result = await session.execute(
            text(
                """
                SELECT id, status, paid_total, created_at
                FROM pos_order
                WHERE id = :order_id AND deleted_at IS NULL;
                """
            ),
            {"order_id": order_id},
        )
        order_row = order_result.mappings().first()
        if order_row is None:
            raise AppError(
                code="ORDER_NOT_FOUND",
                message="Không tìm thấy đơn hàng tương ứng để thực hiện hoàn tiền.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        created_at = parse_iso_datetime(str(order_row["created_at"]))
        if now - created_at > timedelta(days=7):
            raise AppError(
                code="REFUND_WINDOW_EXPIRED",
                message="Đơn hàng đã quá thời hạn cho phép hoàn tiền (tối đa 7 ngày kể từ lúc mua).",
                status_code=status.HTTP_409_CONFLICT,
            )

        order_items_result = await session.execute(
            text(
                """
                SELECT id, volume_id, line_total, final_sell_price
                FROM pos_order_item
                WHERE order_id = :order_id;
                """
            ),
            {"order_id": order_id},
        )
        order_items = {int(row["volume_id"]): dict(row) for row in order_items_result.mappings()}

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
        already_refunded_items = {int(row["volume_id"]) for row in refunded_items_result.mappings()}

        refund_amount = 0
        selected_items: list[dict[str, object]] = []
        for refund_line in payload.refund_items:
            item = order_items.get(refund_line.volume_id)
            if item is None:
                raise AppError(
                    code="REFUND_EXCEEDS_PAID_AMOUNT",
                    message="Sản phẩm yêu cầu hoàn trả không tồn tại trong đơn hàng gốc.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if refund_line.volume_id in already_refunded_items:
                raise AppError(
                    code="ITEM_ALREADY_REFUNDED",
                    message="Sản phẩm này đã được thực hiện hoàn tiền trước đó.",
                    status_code=status.HTTP_409_CONFLICT,
                )

            amount = int(item["final_sell_price"]) * refund_line.quantity
            refund_amount += amount
            selected_items.append(
                {
                    "order_item_id": int(item["id"]),
                    "volume_id": refund_line.volume_id,
                    "amount": amount,
                    "quantity": refund_line.quantity,
                }
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
        refunded_total_before = int(refunded_total_result.scalar_one())
        if refunded_total_before + refund_amount > int(order_row["paid_total"]):
            raise AppError(
                code="REFUND_EXCEEDS_PAID_AMOUNT",
                message="Tổng số tiền hoàn trả vượt quá giới hạn số dư đã thanh toán của đơn hàng này.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        stored_refund_method = payload.refund_method
        if stored_refund_method == "original_method":
            payment_method_result = await session.execute(
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
            original_method = payment_method_result.scalar_one_or_none()
            stored_refund_method = str(original_method or "cash")

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

        for selected_item in selected_items:
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
                    "order_item_id": selected_item["order_item_id"],
                    "volume_id": selected_item["volume_id"],
                    "amount": selected_item["amount"],
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
                {"quantity": selected_item["quantity"], "volume_id": selected_item["volume_id"]},
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
            action="POS_ORDER_REFUNDED",
            entity_type="pos_order",
            entity_id=str(order_id),
            before={"status": str(order_row["status"])},
            after={"status": order_status, "refund_id": refund_id, "refunded_total": refund_amount},
            ip_address=ip_address,
            device_id=device_id,
        )

    envelope = success_response(
        RefundPosOrderPayload(
            refund_id=str(refund_id),
            order_id=str(order_id),
            refunded_total=refund_amount,
            order_status=order_status,
            processed_at=now_iso,
        )
    )

    try:
        async with session.begin():
            await store_cached_response(
                session,
                scope="pos.refund_order",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        cached = await get_cached_response(
            session,
            scope="pos.refund_order",
            request_id=payload.request_id,
        )
        if cached is not None:
            return cached.payload
        raise

    return envelope
