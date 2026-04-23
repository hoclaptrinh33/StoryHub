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
from app.api.v1.endpoints._common import get_request_meta, to_iso_z, utc_now
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services import (
    EventPublisher,
    compute_deposit,
    compute_rent_price,
    compute_sell_price,
    get_cached_response,
    resolve_active_price_rule,
    store_cached_response,
    write_audit_log,
)

router = APIRouter(prefix="/checkout", tags=["checkout"])
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


class UnifiedCheckoutRequest(BaseModel):
    customer_id: int | None = Field(default=None, gt=0)
    scanned_codes: list[str] = Field(min_length=1)
    discount_type: Literal["none", "percent", "amount"] = "none"
    discount_value: int = Field(default=0, ge=0)
    split_payments: list[SplitPaymentLine] = Field(min_length=1)
    checkout_override: CheckoutOverride | None = None
    rental_days: int = Field(default=3, gt=0)
    request_id: str = Field(min_length=6, max_length=128)

    @model_validator(mode="after")
    def validate_discount(self) -> UnifiedCheckoutRequest:
        if self.discount_type == "percent" and self.discount_value > 100:
            raise ValueError("discount_value must be <= 100 when percent")
        if len(set(self.scanned_codes)) != len(self.scanned_codes):
            raise ValueError("scanned_codes must be unique")
        return self

class UnifiedCheckoutPayload(BaseModel):
    order_id: str | None
    rental_contract_id: str | None
    total_sales: int
    total_rentals: int
    total_deposit: int
    grand_total: int
    price_rule_version: int
    price_override_applied: bool
    override_reason_code: str | None = None
    request_id: str


class CheckoutInvoiceLineItem(BaseModel):
    item_code: str
    title: str
    transaction_kind: Literal["sale", "rental"]
    quantity: int
    unit_price: int
    deposit: int = 0
    line_total: int


class CheckoutInvoicePaymentLine(BaseModel):
    method: Literal["cash", "bank_transfer", "e_wallet", "card"]
    amount: int


class CheckoutInvoicePayload(BaseModel):
    invoice_key: str
    transaction_type: Literal["sale", "rental"]
    order_id: str | None = None
    rental_contract_id: str | None = None
    customer_name: str
    customer_phone: str | None = None
    created_at: str
    due_date: str | None = None
    status: str
    subtotal_sales: int
    subtotal_rentals: int
    total_deposit: int
    penalty_total: int
    grand_total: int
    lines: list[CheckoutInvoiceLineItem]
    payments: list[CheckoutInvoicePaymentLine]


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
            message="Yêu cầu mã phê duyệt của Quản lý (Manager Token) không hợp lệ để ghi đè giá.",
            status_code=status.HTTP_403_FORBIDDEN,
        ) from exc

    if approval_auth.role not in {"manager", "owner"}:
        raise AppError(
            code="MANAGER_APPROVAL_REQUIRED",
            message="Chỉ Quản lý hoặc Chủ cửa hàng mới có quyền phê duyệt ghi đè giá tại quầy.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return approval_auth


def _allocate_sales_payment(
    *,
    payments: list[SplitPaymentLine],
    sales_target_total: int,
    grand_total: int,
) -> list[int]:
    if sales_target_total <= 0 or grand_total <= 0:
        return [0 for _ in payments]

    allocations: list[int] = []
    remaining = sales_target_total
    last_index = len(payments) - 1

    for index, payment in enumerate(payments):
        if index == last_index:
            allocated = remaining
        else:
            allocated = (payment.amount * sales_target_total) // grand_total
            allocated = max(min(allocated, remaining), 0)
        allocations.append(allocated)
        remaining -= allocated

    if remaining != 0 and allocations:
        allocations[-1] += remaining
    return allocations


def _normalize_reference_id(reference_id: str) -> int:
    try:
        normalized = int(str(reference_id).strip())
    except ValueError as exc:
        raise AppError(
            code="INVALID_REFERENCE_ID",
            message="Mã giao dịch không hợp lệ.",
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    if normalized <= 0:
        raise AppError(
            code="INVALID_REFERENCE_ID",
            message="Mã giao dịch không hợp lệ.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return normalized


@router.post("/unified", response_model=ResponseEnvelope[UnifiedCheckoutPayload])
async def unified_checkout(
    payload: UnifiedCheckoutRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> ResponseEnvelope[UnifiedCheckoutPayload] | dict[str, object]:
    auth.require_role("cashier", "manager")
    auth.require_scope("pos:write")

    cached = await get_cached_response(
        session,
        scope="checkout.unified",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload

    if session.in_transaction():
        await session.rollback()

    now = utc_now()
    now_iso = to_iso_z(now)
    due_date_iso = to_iso_z(now + timedelta(days=payload.rental_days))

    sale_items_to_process: list[dict[str, object]] = [] # Items that exist in 'item' table as 'retail'
    sale_volumes_to_process: list[dict[str, object]] = [] # Volumes scanned via ISBN
    rental_items_to_process: list[dict[str, object]] = [] # Items that exist in 'item' table as 'rental'

    async with session.begin():
        for code in payload.scanned_codes:
            # 1. Check if it's an Item
            item_res = await session.execute(
                text("""
                    SELECT i.id, i.volume_id, i.item_type, i.status, i.condition_level, v.p_sell_new
                    FROM item i
                    JOIN volume v ON v.id = i.volume_id
                    WHERE i.id = :code AND i.deleted_at IS NULL AND v.deleted_at IS NULL
                """),
                {"code": code}
            )
            item_row = item_res.mappings().first()

            if item_row:
                if item_row["status"] != "available":
                     raise AppError(
                        code="ITEM_NOT_AVAILABLE",
                        message=f"Sản phẩm {code} đang ở trạng thái '{item_row['status']}', không thể thực hiện giao dịch.",
                        status_code=status.HTTP_409_CONFLICT,
                    )
                
                if item_row["item_type"] == "rental":
                    rental_items_to_process.append(dict(item_row))
                else:
                    sale_items_to_process.append(dict(item_row))
            else:
                # 2. Check if it's a Volume ISBN
                vol_res = await session.execute(
                    text("""
                        SELECT id, isbn, retail_stock, p_sell_new
                        FROM volume
                        WHERE isbn = :code AND deleted_at IS NULL
                    """),
                    {"code": code}
                )
                vol_row = vol_res.mappings().first()
                if vol_row:
                    # Robust check: try to find an available individual retail item first
                    # because volume.retail_stock might be inconsistent with the item table
                    avail_item_res = await session.execute(
                        text("""
                            SELECT i.id, i.volume_id, i.item_type, i.status, i.condition_level, v.p_sell_new
                            FROM item i
                            JOIN volume v ON v.id = i.volume_id
                            WHERE i.volume_id = :vid AND i.item_type = 'retail' AND i.status = 'available' AND i.deleted_at IS NULL
                            LIMIT 1
                        """),
                        {"vid": vol_row["id"]}
                    )
                    avail_item = avail_item_res.mappings().first()
                    
                    if avail_item:
                        sale_items_to_process.append(dict(avail_item))
                    elif int(vol_row["retail_stock"]) > 0:
                        sale_volumes_to_process.append(dict(vol_row))
                    else:
                        raise AppError(
                            code="INSUFFICIENT_STOCK",
                            message=f"Tập truyện mã ISBN {code} đã hết hàng bán lẻ.",
                            status_code=status.HTTP_409_CONFLICT,
                        )
                else:
                    raise AppError(
                        code="ITEM_NOT_FOUND",
                        message=f"Không tìm thấy sản phẩm hoặc mã ISBN: {code}",
                        status_code=status.HTTP_404_NOT_FOUND,
                    )

        pricing_rule = await resolve_active_price_rule(session)
        total_sales = 0
        total_rentals = 0
        total_deposit = 0
        
        sale_order_items: list[dict[str, object]] = []
        rental_item_rows: list[dict[str, object]] = []

        # Process Sale Items (from 'item' table)
        for it in sale_items_to_process:
            p_sell_new = int(it["p_sell_new"])
            sell_price = compute_sell_price(
                condition_level=it["condition_level"],
                p_sell_new=p_sell_new,
                used_demand_factor=pricing_rule.used_demand_factor,
                used_cap_ratio=pricing_rule.used_cap_ratio,
            )
            total_sales += sell_price
            sale_order_items.append({
                "item_id": it["id"],
                "volume_id": it["volume_id"],
                "p_sell_new": p_sell_new,
                "line_total": sell_price,
                "final_sell_price": sell_price,
            })
            # Update item status
            await session.execute(
                text("UPDATE item SET status = 'sold', updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"id": it["id"]}
            )
            # Update volume stock
            await session.execute(
                text("UPDATE volume SET retail_stock = retail_stock - 1, updated_at = CURRENT_TIMESTAMP WHERE id = :vid"),
                {"vid": it["volume_id"]}
            )

        # Process Sale Volumes (from ISBN)
        for vol in sale_volumes_to_process:
            p_sell_new = int(vol["p_sell_new"])
            sell_price = compute_sell_price(
                condition_level=100, # Assume new for ISBN sales
                p_sell_new=p_sell_new,
                used_demand_factor=pricing_rule.used_demand_factor,
                used_cap_ratio=pricing_rule.used_cap_ratio,
            )
            total_sales += sell_price
            
            # Find an available retail item to consume if possible
            item_to_consume_res = await session.execute(
                text("SELECT id FROM item WHERE volume_id = :vid AND item_type = 'retail' AND status = 'available' LIMIT 1"),
                {"vid": vol["id"]}
            )
            item_to_consume = item_to_consume_res.scalar_one_or_none()
            
            sale_order_items.append({
                "item_id": item_to_consume, # May be NULL if sold by qty only
                "volume_id": vol["id"],
                "p_sell_new": p_sell_new,
                "line_total": sell_price,
                "final_sell_price": sell_price,
            })
            
            if item_to_consume:
                await session.execute(
                    text("UPDATE item SET status = 'sold', updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                    {"id": item_to_consume}
                )
            
            await session.execute(
                text("UPDATE volume SET retail_stock = retail_stock - 1, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"id": vol["id"]}
            )

        # Process Rental Items
        if rental_items_to_process and payload.customer_id is None:
             raise AppError(
                code="CUSTOMER_REQUIRED_FOR_RENTAL",
                message="Giao dịch cho thuê bắt buộc phải có thông tin khách hàng.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        for it in rental_items_to_process:
            if it["id"].upper().startswith("RNT-"):
                raise AppError(
                    code="CANNOT_RENT_VIRTUAL_ITEM",
                    message=f"Bản sao {it['id']} được tạo tự động, không có mã vạch thật. Không thể cho thuê.",
                    status_code=400)
    
            p_sell_new = int(it["p_sell_new"])
            p_rent = compute_rent_price(
                condition_level=it["condition_level"],
                p_sell_new=p_sell_new,
                k_rent=pricing_rule.k_rent,
            )
            p_deposit = compute_deposit(
                p_sell_new=p_sell_new,
                k_deposit=pricing_rule.k_deposit,
                d_floor=pricing_rule.d_floor,
            )
            total_rentals += p_rent
            total_deposit += p_deposit
            rental_item_rows.append({
                "item_id": it["id"],
                "volume_id": it["volume_id"],
                "p_sell_new": p_sell_new,
                "rent_price": p_rent,
                "deposit": p_deposit,
                "condition_level": it["condition_level"],
            })
            await session.execute(
                text("UPDATE item SET status = 'rented', updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                {"id": it["id"]}
            )

        subtotal_fee = total_sales + total_rentals
        discount_total = _calculate_discount(subtotal_fee, payload.discount_type, payload.discount_value)
        final_fee = max(subtotal_fee - discount_total, 0)

        base_grand_total = final_fee + total_deposit
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
                    message="Giá ghi đè thấp hơn mức tối thiểu cho phép (70% tổng giá trị).",
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
                code="PAYMENT_MISMATCH",
                message=f"Số tiền thanh toán thực tế ({payment_total:,}đ) không khớp với tổng tiền phải trả ({grand_total:,}đ).",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        order_id_out: str | None = None
        contract_id_out: str | None = None

        if sale_order_items:
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
                        created_by_user_id
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
                        :created_by_user_id
                    );
                    """
                ),
                {
                    "customer_id": payload.customer_id,
                    "subtotal": total_sales,
                    "discount_type": payload.discount_type,
                    "discount_value": payload.discount_value,
                    "discount_total": discount_total,
                    "grand_total": final_fee,
                    "paid_total": final_fee,
                    "request_id": f"pos_{payload.request_id}",
                    "created_by_user_id": auth.user_id,
                },
            )

            res = await session.execute(text("SELECT last_insert_rowid()"))
            order_id = int(res.scalar_one())
            order_id_out = str(order_id)

            for line in sale_order_items:
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
                            1,
                            :line_total
                        );
                        """
                    ),
                    {
                        "order_id": order_id,
                        "volume_id": line["volume_id"],
                        "final_sell_price": line["final_sell_price"],
                        "line_total": line["line_total"],
                    },
                )
                pos_order_item_id_result = await session.execute(
                    text("SELECT last_insert_rowid()")
                )
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
                        "volume_id": line["volume_id"],
                        "item_id": line.get("item_id"),
                        "p_sell_new_snapshot": line["p_sell_new"],
                        "final_sell_price": line["final_sell_price"],
                        "line_total": line["line_total"],
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

            payment_allocations = _allocate_sales_payment(
                payments=payload.split_payments,
                sales_target_total=final_fee,
                grand_total=grand_total,
            )
            for payment, allocated_amount in zip(
                payload.split_payments,
                payment_allocations,
                strict=True,
            ):
                if allocated_amount <= 0:
                    continue
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
                        "amount": allocated_amount,
                        "paid_at": now_iso,
                    },
                )

        if rental_item_rows:
            await session.execute(
                text(
                    """
                    INSERT INTO rental_contract (
                        customer_id,
                        status,
                        rent_date,
                        due_date,
                        deposit_total,
                        remaining_deposit,
                        debt_total,
                        request_id,
                        created_by_user_id
                    )
                    VALUES (
                        :customer_id,
                        'active',
                        :rent_date,
                        :due_date,
                        :deposit_total,
                        :remaining_deposit,
                        0,
                        :request_id,
                        :created_by_user_id
                    );
                    """
                ),
                {
                    "customer_id": payload.customer_id,
                    "rent_date": now_iso,
                    "due_date": due_date_iso,
                    "deposit_total": total_deposit,
                    "remaining_deposit": total_deposit,
                    "request_id": f"rent_{payload.request_id}",
                    "created_by_user_id": auth.user_id,
                },
            )

            res = await session.execute(text("SELECT last_insert_rowid()"))
            contract_id = int(res.scalar_one())
            contract_id_out = str(contract_id)

            for item in rental_item_rows:
                await session.execute(
                    text(
                        """
                        INSERT INTO rental_item (
                            contract_id,
                            item_id,
                            final_rent_price,
                            final_deposit,
                            status,
                            condition_before
                        )
                        VALUES (
                            :contract_id,
                            :item_id,
                            :final_rent_price,
                            :final_deposit,
                            'rented',
                            :condition_before
                        );
                        """
                    ),
                    {
                        "contract_id": contract_id,
                        "item_id": item["item_id"],
                        "final_rent_price": item["rent_price"],
                        "final_deposit": item["deposit"],
                        "condition_before": item["condition_level"],
                    },
                )
                rental_item_id_result = await session.execute(
                    text("SELECT last_insert_rowid()")
                )
                rental_item_id = int(rental_item_id_result.scalar_one())
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
                            rent_ratio_snapshot,
                            deposit_ratio_snapshot,
                            deposit_floor_snapshot,
                            final_rent_price,
                            final_deposit,
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
                            'rental',
                            NULL,
                            :rental_contract_id,
                            NULL,
                            :rental_item_id,
                            :volume_id,
                            :item_id,
                            1,
                            :p_sell_new_snapshot,
                            :rent_ratio_snapshot,
                            :deposit_ratio_snapshot,
                            :deposit_floor_snapshot,
                            :final_rent_price,
                            :final_deposit,
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
                        "rental_contract_id": contract_id,
                        "rental_item_id": rental_item_id,
                        "volume_id": item["volume_id"],
                        "item_id": item["item_id"],
                        "p_sell_new_snapshot": item["p_sell_new"],
                        "rent_ratio_snapshot": pricing_rule.k_rent,
                        "deposit_ratio_snapshot": pricing_rule.k_deposit,
                        "deposit_floor_snapshot": pricing_rule.d_floor,
                        "final_rent_price": item["rent_price"],
                        "final_deposit": item["deposit"],
                        "line_total": int(item["rent_price"]) + int(item["deposit"]),
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

        ip_addr, device = get_request_meta(request)
        if price_override_applied:
            await write_audit_log(
                session,
                actor_user_id=auth.user_id,
                action="POS_PRICE_OVERRIDE",
                entity_type="pos_order" if order_id_out is not None else "checkout",
                entity_id=order_id_out or payload.request_id,
                before={"grand_total": base_grand_total},
                after={
                    "grand_total": grand_total,
                    "reason_code": override_reason_code,
                    "approved_by_user_id": approved_by_user_id,
                    "approved_via": approved_via,
                },
                ip_address=ip_addr,
                device_id=device,
            )

        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="UNIFIED_CHECKOUT_SUCCESS",
            entity_type="system",
            entity_id=payload.request_id,
            before=None,
            after={
                "order_id": order_id_out,
                "contract_id": contract_id_out,
                "grand_total": grand_total,
                "price_rule_version": pricing_rule.version_no,
                "price_override_applied": price_override_applied,
                "override_reason_code": override_reason_code,
            },
            ip_address=ip_addr,
            device_id=device,
        )

    envelope = success_response(
        UnifiedCheckoutPayload(
            order_id=order_id_out,
            rental_contract_id=contract_id_out,
            total_sales=total_sales,
            total_rentals=total_rentals,
            total_deposit=total_deposit,
            grand_total=grand_total,
            price_rule_version=pricing_rule.version_no,
            price_override_applied=price_override_applied,
            override_reason_code=override_reason_code,
            request_id=payload.request_id,
        )
    )

    for rental_item in rental_item_rows:
        await event_publisher.publish_item_status_changed(
            item_id=str(rental_item["item_id"]),
            old_status="available",
            new_status="rented",
            changed_at=now_iso,
            source_api="checkout_unified_v1",
            changed_by=auth.user_id,
            branch_id=auth.branch_id,
        )

    try:
        async with session.begin():
            await store_cached_response(
                session,
                scope="checkout.unified",
                request_id=payload.request_id,
                status_code=200,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        cached = await get_cached_response(
            session,
            scope="checkout.unified",
            request_id=payload.request_id,
        )
        if cached is not None:
            return cached.payload
        raise

    return envelope


@router.get(
    "/invoices/{transaction_type}/{reference_id}",
    response_model=ResponseEnvelope[CheckoutInvoicePayload],
)
async def get_checkout_invoice(
    transaction_type: Literal["sale", "rental"],
    reference_id: str = Path(min_length=1, max_length=32),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[CheckoutInvoicePayload]:
    auth.require_role("cashier", "manager", "owner")
    auth.require_scope("pos:write")

    normalized_id = _normalize_reference_id(reference_id)

    if transaction_type == "sale":
        order_result = await session.execute(
            text(
                """
                SELECT
                    po.id,
                    po.status,
                    po.created_at,
                    po.grand_total,
                    c.name AS customer_name,
                    c.phone AS customer_phone
                FROM pos_order po
                LEFT JOIN customer c ON c.id = po.customer_id
                WHERE po.id = :order_id
                  AND po.deleted_at IS NULL;
                """
            ),
            {"order_id": normalized_id},
        )
        order_row = order_result.mappings().first()
        if order_row is None:
            raise AppError(
                code="INVOICE_NOT_FOUND",
                message="Không tìm thấy hóa đơn bán hàng theo mã yêu cầu.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        line_result = await session.execute(
            text(
                """
                SELECT
                    v.isbn AS item_code,
                    t.name AS title,
                    poi.quantity,
                    poi.final_sell_price,
                    poi.line_total
                FROM pos_order_item poi
                JOIN volume v ON v.id = poi.volume_id
                JOIN title t ON t.id = v.title_id
                WHERE poi.order_id = :order_id
                ORDER BY poi.id ASC;
                """
            ),
            {"order_id": normalized_id},
        )

        lines = [
            CheckoutInvoiceLineItem(
                item_code=str(row["item_code"]),
                title=str(row["title"]),
                transaction_kind="sale",
                quantity=max(int(row["quantity"]), 1),
                unit_price=max(int(row["final_sell_price"]), 0),
                deposit=0,
                line_total=max(int(row["line_total"]), 0),
            )
            for row in line_result.mappings().all()
        ]

        payment_result = await session.execute(
            text(
                """
                SELECT method, amount
                FROM pos_payment
                WHERE order_id = :order_id
                ORDER BY id ASC;
                """
            ),
            {"order_id": normalized_id},
        )
        payments = [
            CheckoutInvoicePaymentLine(
                method=str(row["method"]),
                amount=max(int(row["amount"]), 0),
            )
            for row in payment_result.mappings().all()
        ]

        subtotal_sales = sum(line.line_total for line in lines)
        payload = CheckoutInvoicePayload(
            invoice_key=f"SALE-{normalized_id}",
            transaction_type="sale",
            order_id=str(order_row["id"]),
            rental_contract_id=None,
            customer_name=str(order_row["customer_name"] or "Khach le"),
            customer_phone=(
                str(order_row["customer_phone"])
                if order_row["customer_phone"] is not None
                else None
            ),
            created_at=str(order_row["created_at"]),
            due_date=None,
            status=str(order_row["status"]),
            subtotal_sales=subtotal_sales,
            subtotal_rentals=0,
            total_deposit=0,
            penalty_total=0,
            grand_total=max(int(order_row["grand_total"]), 0),
            lines=lines,
            payments=payments,
        )
        return success_response(payload)

    contract_result = await session.execute(
        text(
            """
            SELECT
                rc.id,
                rc.status,
                rc.rent_date,
                rc.due_date,
                c.name AS customer_name,
                c.phone AS customer_phone
            FROM rental_contract rc
            LEFT JOIN customer c ON c.id = rc.customer_id
            WHERE rc.id = :contract_id
              AND rc.deleted_at IS NULL;
            """
        ),
        {"contract_id": normalized_id},
    )
    contract_row = contract_result.mappings().first()
    if contract_row is None:
        raise AppError(
            code="INVOICE_NOT_FOUND",
            message="Không tìm thấy hóa đơn thuê theo mã yêu cầu.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    rental_line_result = await session.execute(
        text(
            """
            SELECT
                ri.item_id,
                t.name AS title,
                ri.final_rent_price,
                ri.final_deposit
            FROM rental_item ri
            JOIN item i ON i.id = ri.item_id
            JOIN volume v ON v.id = i.volume_id
            JOIN title t ON t.id = v.title_id
            WHERE ri.contract_id = :contract_id
            ORDER BY ri.id ASC;
            """
        ),
        {"contract_id": normalized_id},
    )
    rental_lines = [
        CheckoutInvoiceLineItem(
            item_code=str(row["item_id"]),
            title=str(row["title"]),
            transaction_kind="rental",
            quantity=1,
            unit_price=max(int(row["final_rent_price"]), 0),
            deposit=max(int(row["final_deposit"]), 0),
            line_total=max(int(row["final_rent_price"]) + int(row["final_deposit"]), 0),
        )
        for row in rental_line_result.mappings().all()
    ]

    settlement_result = await session.execute(
        text(
            """
            SELECT
                COALESCE(SUM(late_fee + damage_fee + lost_fee), 0) AS penalty_total
            FROM rental_settlement
            WHERE contract_id = :contract_id;
            """
        ),
        {"contract_id": normalized_id},
    )
    penalty_total = max(int(settlement_result.scalar_one() or 0), 0)

    subtotal_rentals = sum(line.unit_price for line in rental_lines)
    total_deposit = sum(line.deposit for line in rental_lines)
    grand_total = subtotal_rentals + total_deposit + penalty_total

    payload = CheckoutInvoicePayload(
        invoice_key=f"RENT-{normalized_id}",
        transaction_type="rental",
        order_id=None,
        rental_contract_id=str(contract_row["id"]),
        customer_name=str(contract_row["customer_name"] or "Khach le"),
        customer_phone=(
            str(contract_row["customer_phone"])
            if contract_row["customer_phone"] is not None
            else None
        ),
        created_at=str(contract_row["rent_date"]),
        due_date=str(contract_row["due_date"]),
        status=str(contract_row["status"]),
        subtotal_sales=0,
        subtotal_rentals=subtotal_rentals,
        total_deposit=total_deposit,
        penalty_total=penalty_total,
        grand_total=grand_total,
        lines=rental_lines,
        payments=[],
    )
    return success_response(payload)
