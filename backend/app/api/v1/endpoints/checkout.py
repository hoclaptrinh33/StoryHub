from __future__ import annotations

from datetime import timedelta
from typing import Literal
import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.dependencies import AuthContext, get_auth_context
from app.api.v1.endpoints._common import get_request_meta, to_iso_z, utc_now
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services import (
    compute_sell_price,
    compute_rent_price,
    compute_deposit,
    get_cached_response,
    store_cached_response,
    write_audit_log,
)

router = APIRouter(prefix="/checkout", tags=["checkout"])

class SplitPaymentLine(BaseModel):
    method: Literal["cash", "bank_transfer", "e_wallet", "card"]
    amount: int = Field(gt=0)
    
class UnifiedCheckoutRequest(BaseModel):
    customer_id: int | None = Field(default=None, gt=0)
    scanned_codes: list[str] = Field(min_length=1)
    discount_type: Literal["none", "percent", "amount"] = "none"
    discount_value: int = Field(default=0, ge=0)
    split_payments: list[SplitPaymentLine] = Field(min_length=1)
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
    request_id: str

def _calculate_discount(subtotal: int, discount_type: str, discount_value: int) -> int:
    if discount_type == "none":
        return 0
    if discount_type == "amount":
        return min(discount_value, subtotal)
    return min((subtotal * discount_value) // 100, subtotal)

@router.post("/unified", response_model=ResponseEnvelope[UnifiedCheckoutPayload])
async def unified_checkout(
    payload: UnifiedCheckoutRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[UnifiedCheckoutPayload] | dict[str, object]:
    auth.require_role("cashier", "manager")
    auth.require_scope("pos:write")

    cached = await get_cached_response(session, scope="checkout.unified", request_id=payload.request_id)
    if cached is not None:
        return cached.payload

    if session.in_transaction():
        await session.rollback()

    now = utc_now()
    now_iso = to_iso_z(now)
    due_date_iso = to_iso_z(now + timedelta(days=payload.rental_days))

    sales_isbns: list[str] = []
    rental_skus: list[str] = []
    
    for code in payload.scanned_codes:
        if code.startswith("RNT-") or code.startswith("ITM-"):
            rental_skus.append(code)
        else:
            sales_isbns.append(code)

    async with session.begin():
        # --- 1. HANDLE SALES (isbns) ---
        total_sales = 0
        sale_order_items = []
        if sales_isbns:
            for isbn in sales_isbns:
                vol_result = await session.execute(
                    text("SELECT id, retail_stock FROM volume WHERE isbn = :isbn"),
                    {"isbn": isbn}
                )
                volume_row = vol_result.mappings().first()
                if not volume_row or volume_row["retail_stock"] < 1:
                    raise AppError(
                        code="INSUFFICIENT_STOCK",
                        message=f"San pham ma {isbn} khong con du ton kho ban.",
                        status_code=status.HTTP_409_CONFLICT
                    )
                
                sell_price = compute_sell_price(condition_level=100)
                total_sales += sell_price
                sale_order_items.append({
                    "volume_id": volume_row["id"],
                    "line_total": sell_price,
                    "final_sell_price": sell_price
                })
                
                await session.execute(
                    text("UPDATE volume SET retail_stock = retail_stock - 1, updated_at = CURRENT_TIMESTAMP WHERE id = :id"),
                    {"id": volume_row["id"]}
                )

        # --- 2. HANDLE RENTALS (skus) ---
        total_rentals = 0
        total_deposit = 0
        rental_item_rows = []
        if rental_skus:
            if payload.customer_id is None:
                raise AppError(
                    code="CUSTOMER_REQUIRED_FOR_RENTAL",
                    message="Giao dich cho thue bat buoc phai co thong tin khach hang.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            for sku in rental_skus:
                item_result = await session.execute(
                    text("SELECT id, condition_level, status FROM item WHERE id = :sku AND deleted_at IS NULL"),
                    {"sku": sku}
                )
                item_row = item_result.mappings().first()
                if not item_row or item_row["status"] != "available":
                    raise AppError(
                        code="ITEM_NOT_AVAILABLE",
                        message=f"Item thue {sku} khong san sang: chua dang ky hoac bi loi.",
                        status_code=status.HTTP_409_CONFLICT
                    )
                
                p_rent = compute_rent_price(condition_level=int(item_row["condition_level"]))
                p_deposit = compute_deposit(rent_price=p_rent)
                
                total_rentals += p_rent
                total_deposit += p_deposit
                rental_item_rows.append({
                    "item_id": sku,
                    "rent_price": p_rent,
                    "deposit": p_deposit,
                    "condition_level": item_row["condition_level"]
                })
                
                lock_res = await session.execute(
                    text("UPDATE item SET status='rented', updated_at=CURRENT_TIMESTAMP WHERE id=:sku AND status='available'"),
                    {"sku": sku}
                )
                if lock_res.rowcount != 1:
                    raise AppError(
                        code="ITEM_LOCK_FAILED",
                        message=f"Khong the khoa item thue {sku}.",
                        status_code=status.HTTP_409_CONFLICT
                    )

        # --- 3. COMPUTE TOTALS AND PAYMENTS ---
        subtotal_fee = total_sales + total_rentals
        discount_total = _calculate_discount(subtotal_fee, payload.discount_type, payload.discount_value)
        final_fee = max(subtotal_fee - discount_total, 0)
        
        grand_total = final_fee + total_deposit
        payment_total = sum(line.amount for line in payload.split_payments)
        
        if payment_total != grand_total:
            raise AppError(
                code="PAYMENT_MISMATCH",
                message=f"Thanh toan ({payment_total}) lech voi tong ({grand_total}).",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # --- 4. CREATE DATABASE RECORDS ---
        order_id_out = None
        contract_id_out = None
        
        if sales_isbns:
            await session.execute(text(
                """INSERT INTO pos_order (customer_id, status, subtotal, discount_type, discount_value, discount_total, grand_total, paid_total, request_id, created_by_user_id) 
                   VALUES (:c, 'paid', :s, :dt, :dv, :dtot, :gtot, :ptot, :rid, :b)"""
            ), {"c": payload.customer_id, "s": total_sales, "dt": payload.discount_type, "dv": payload.discount_value, "dtot": discount_total, "gtot": final_fee, "ptot": final_fee, "rid": "pos_"+payload.request_id, "b": auth.user_id})
            
            res = await session.execute(text("SELECT last_insert_rowid()"))
            order_id = int(res.scalar_one())
            order_id_out = str(order_id)
            
            for line in sale_order_items:
                await session.execute(text(
                    "INSERT INTO pos_order_item (order_id, volume_id, final_sell_price, quantity, line_total) VALUES (:o, :v, :p, 1, :t)"
                ), {"o": order_id, "v": line["volume_id"], "p": line["final_sell_price"], "t": line["line_total"]})
                
            for payment in payload.split_payments:
                await session.execute(text(
                    "INSERT INTO pos_payment (order_id, method, amount, paid_at) VALUES (:o, :m, :a, :d)"
                ), {"o": order_id, "m": payment.method, "a": float(payment.amount) * (total_sales/subtotal_fee if subtotal_fee else 1), "d": now_iso}) # Distributed payment optionally

        if rental_skus:
            await session.execute(text(
                """INSERT INTO rental_contract (customer_id, status, rent_date, due_date, deposit_total, remaining_deposit, debt_total, request_id, created_by_user_id) 
                   VALUES (:c, 'active', :r, :d, :dep, :dep, 0, :rid, :b)"""
            ), {"c": payload.customer_id, "r": now_iso, "d": due_date_iso, "dep": total_deposit, "rid": "rent_"+payload.request_id, "b": auth.user_id})
            
            res = await session.execute(text("SELECT last_insert_rowid()"))
            contract_id = int(res.scalar_one())
            contract_id_out = str(contract_id)
            
            for item in rental_item_rows:
                await session.execute(text(
                    "INSERT INTO rental_item (contract_id, item_id, final_rent_price, final_deposit, status, condition_before) VALUES (:c, :i, :r, :d, 'rented', :cb)"
                ), {"c": contract_id, "i": item["item_id"], "r": item["rent_price"], "d": item["deposit"], "cb": item["condition_level"]})

        ip_addr, device = get_request_meta(request)
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="UNIFIED_CHECKOUT_SUCCESS",
            entity_type="system",
            entity_id=payload.request_id,
            before=None,
            after={"order_id": order_id_out, "contract_id": contract_id_out, "grand_total": grand_total},
            ip_address=ip_addr,
            device_id=device
        )
        
    envelope = success_response(
        UnifiedCheckoutPayload(
            order_id=order_id_out,
            rental_contract_id=contract_id_out,
            total_sales=total_sales,
            total_rentals=total_rentals,
            total_deposit=total_deposit,
            grand_total=grand_total,
            request_id=payload.request_id,
        )
    )

    try:
        async with session.begin():
            await store_cached_response(session, scope="checkout.unified", request_id=payload.request_id, status_code=200, payload=envelope.model_dump())
    except IntegrityError:
        pass
    
    return envelope
