from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Path, Query, Request
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.dependencies import AuthContext, get_auth_context, get_event_publisher
from app.api.v1.endpoints._common import get_request_meta, parse_iso_datetime, to_iso_z, utc_now
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services import (
    EventPublisher,
    compute_deposit,
    compute_rent_price,
    get_cached_response,
    resolve_active_price_rule,
    store_cached_response,
    write_audit_log,
)

router = APIRouter(prefix="/rentals", tags=["rental"])
settings = get_settings()


class RentalItemSnapshot(BaseModel):
    item_id: str
    final_rent_price: int
    final_deposit: int
    status: Literal["rented", "returned", "lost"]


class CreateRentalContractRequest(BaseModel):
    customer_id: int = Field(gt=0)
    item_ids: list[str] = Field(min_length=1)
    due_date: str
    deposit_policy: Literal["auto", "manual"] = "auto"
    manual_deposit: int | None = Field(default=None, ge=0)
    request_id: str = Field(min_length=6, max_length=128)

    @model_validator(mode="after")
    def validate_contract(self) -> CreateRentalContractRequest:
        if len(set(self.item_ids)) != len(self.item_ids):
            raise ValueError("item_ids must be unique")
        if self.deposit_policy == "manual" and self.manual_deposit is None:
            raise ValueError("manual_deposit is required when deposit_policy is manual")
        return self


class CreateRentalContractPayload(BaseModel):
    contract_id: str
    customer_id: str
    rent_date: str
    due_date: str
    deposit_total: int
    rental_items: list[RentalItemSnapshot]


class ExtendRentalContractRequest(BaseModel):
    new_due_date: str
    extension_reason: str | None = None
    additional_deposit: int = Field(default=0, ge=0)
    request_id: str = Field(min_length=6, max_length=128)


class ExtendRentalContractPayload(BaseModel):
    contract_id: str
    old_due_date: str
    new_due_date: str
    additional_fee: int
    additional_deposit: int
    status: Literal["active", "overdue"]


class ReturnItemLine(BaseModel):
    item_id: str
    condition_after: Literal["good", "minor_damage", "major_damage", "lost"]


class ReturnRentalItemsRequest(BaseModel):
    return_lines: list[ReturnItemLine] = Field(min_length=1)
    returned_at: str | None = None
    request_id: str = Field(min_length=6, max_length=128)

    @model_validator(mode="after")
    def validate_unique_items(self) -> ReturnRentalItemsRequest:
        item_ids = [line.item_id for line in self.return_lines]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("return_lines must not contain duplicate item_id")
        return self


class ReturnRentalItemsPayload(BaseModel):
    settlement_id: str
    contract_id: str
    rental_fee: int
    late_fee: int
    damage_fee: int
    lost_fee: int
    total_fee: int
    deducted_from_deposit: int
    refund_to_customer: int
    remaining_debt: int
    contract_status: Literal["partial_returned", "closed"]


class RentalSettlementStatusPayload(BaseModel):
    settlement_id: str | None
    contract_id: str
    rental_fee: int
    late_fee: int
    damage_fee: int
    lost_fee: int
    total_fee: int
    deducted_from_deposit: int
    refund_to_customer: int
    remaining_debt: int
    settled_at: str | None
    contract_status: Literal["active", "partial_returned", "closed", "overdue", "cancelled"]


class RentalContractPreviewLine(BaseModel):
    item_id: str
    barcode: str
    title: str
    rental_fee: int
    final_deposit: int
    overdue_days: int


class RentalContractPreviewPayload(BaseModel):
    contract_id: str
    customer_id: str
    customer_name: str
    status: Literal["active", "partial_returned", "closed", "overdue", "cancelled"]
    due_date: str
    deposit_total: int
    remaining_deposit: int
    overdue_fee_per_day: int
    damage_fee_minor_percent: int
    damage_fee_major_percent: int
    return_lines: list[RentalContractPreviewLine]


class ReturnableRentalContractListItemPayload(BaseModel):
    contract_id: str
    customer_id: str
    customer_name: str
    customer_phone: str
    status: Literal["active", "partial_returned", "overdue"]
    due_date: str
    remaining_deposit: int
    open_item_count: int
    rented_items_preview: str


class ItemRentalStatusPayload(BaseModel):
    """Response for checking if an item is currently rented"""
    rental_contract_id: str | None
    item_status: str


def _condition_to_level(condition: str, fallback: int) -> int:
    if condition == "good":
        return max(fallback, 90)
    if condition == "minor_damage":
        return min(fallback, 70)
    if condition == "major_damage":
        return min(fallback, 40)
    return 0


def _calculate_damage_fee(final_deposit: int, condition_after: str) -> int:
    if condition_after == "minor_damage":
        return int(final_deposit * settings.damage_fee_minor_percent / 100)
    if condition_after == "major_damage":
        return int(final_deposit * settings.damage_fee_major_percent / 100)
    return 0


@router.get(
    "/contracts",
    response_model=ResponseEnvelope[list[ReturnableRentalContractListItemPayload]],
)
async def get_returnable_rental_contracts(
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=30, ge=1, le=100),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[ReturnableRentalContractListItemPayload]]:
    auth.require_role("cashier", "manager")
    auth.require_scope("rental:return")

    query_term = (q or "").strip()
    query_like = f"%{query_term}%"

    result = await session.execute(
        text(
            """
            SELECT
                rc.id AS contract_id,
                rc.customer_id,
                rc.status,
                rc.due_date,
                rc.remaining_deposit,
                c.name AS customer_name,
                c.phone AS customer_phone,
                SUM(CASE WHEN ri.status = 'rented' THEN 1 ELSE 0 END) AS open_item_count,
                (
                    SELECT GROUP_CONCAT(
                        COALESCE(t2.name, 'Khong xac dinh')
                        || CASE
                            WHEN v2.volume_number IS NULL THEN ''
                            ELSE ' Tap ' || CAST(v2.volume_number AS TEXT)
                        END,
                        ', '
                    )
                    FROM rental_item ri2
                    LEFT JOIN item i2 ON i2.id = ri2.item_id
                    LEFT JOIN volume v2 ON v2.id = i2.volume_id
                    LEFT JOIN title t2 ON t2.id = v2.title_id
                    WHERE ri2.contract_id = rc.id
                      AND ri2.status = 'rented'
                ) AS rented_items_preview
            FROM rental_contract rc
            JOIN customer c ON c.id = rc.customer_id
            LEFT JOIN rental_item ri ON ri.contract_id = rc.id
            WHERE rc.deleted_at IS NULL
              AND c.deleted_at IS NULL
              AND rc.status IN ('active', 'partial_returned', 'overdue')
              AND (
                :query_term = ''
                OR CAST(rc.id AS TEXT) LIKE :query_like
                OR LOWER(c.name) LIKE :query_like_lower
                OR c.phone LIKE :query_like
              )
            GROUP BY
                rc.id,
                rc.customer_id,
                rc.status,
                rc.due_date,
                rc.remaining_deposit,
                c.name,
                c.phone
            HAVING SUM(CASE WHEN ri.status = 'rented' THEN 1 ELSE 0 END) > 0
            ORDER BY rc.due_date ASC, rc.id DESC
            LIMIT :limit;
            """
        ),
        {
            "query_term": query_term,
            "query_like": query_like,
            "query_like_lower": query_like.lower(),
            "limit": limit,
        },
    )

    contracts: list[ReturnableRentalContractListItemPayload] = []
    for row in result.mappings():
        due_date = parse_iso_datetime(str(row["due_date"]))
        contracts.append(
            ReturnableRentalContractListItemPayload(
                contract_id=str(row["contract_id"]),
                customer_id=str(row["customer_id"]),
                customer_name=str(row["customer_name"]),
                customer_phone=str(row["customer_phone"]),
                status=str(row["status"]),
                due_date=to_iso_z(due_date),
                remaining_deposit=int(row["remaining_deposit"] or 0),
                open_item_count=int(row["open_item_count"] or 0),
                rented_items_preview=str(row["rented_items_preview"] or ""),
            )
        )

    return success_response(contracts)


@router.get(
    "/contracts/{contract_id}",
    response_model=ResponseEnvelope[RentalContractPreviewPayload],
)
async def get_rental_contract_preview(
    contract_id: int = Path(gt=0),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[RentalContractPreviewPayload]:
    auth.require_role("cashier", "manager")
    auth.require_scope("rental:return")

    now = utc_now()

    contract_result = await session.execute(
        text(
            """
            SELECT
                rc.id,
                rc.customer_id,
                rc.status,
                rc.due_date,
                rc.deposit_total,
                rc.remaining_deposit,
                c.name AS customer_name
            FROM rental_contract rc
            JOIN customer c ON c.id = rc.customer_id
            WHERE rc.id = :contract_id
              AND rc.deleted_at IS NULL
              AND c.deleted_at IS NULL;
            """
        ),
        {"contract_id": contract_id},
    )
    contract_row = contract_result.mappings().first()
    if contract_row is None:
        raise AppError(
            code="CONTRACT_NOT_FOUND",
            message="Khong tim thay hop dong can kiem dinh tra.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    if contract_row["status"] in {"closed", "cancelled"}:
        raise AppError(
            code="CONTRACT_NOT_RETURNABLE",
            message="Hop dong da dong hoac da huy, khong the kiem dinh tra.",
            status_code=status.HTTP_409_CONFLICT,
        )

    due_date = parse_iso_datetime(str(contract_row["due_date"]))
    overdue_days = max((now.date() - due_date.date()).days, 0)

    return_line_result = await session.execute(
        text(
            """
            SELECT
                ri.item_id,
                ri.final_rent_price,
                ri.final_deposit,
                t.name AS title_name,
                v.volume_number
            FROM rental_item ri
            LEFT JOIN item i ON i.id = ri.item_id
            LEFT JOIN volume v ON v.id = i.volume_id
            LEFT JOIN title t ON t.id = v.title_id
            WHERE ri.contract_id = :contract_id
              AND ri.status = 'rented'
            ORDER BY ri.id;
            """
        ),
        {"contract_id": contract_id},
    )

    preview_lines: list[RentalContractPreviewLine] = []
    for row in return_line_result.mappings():
        item_id = str(row["item_id"])
        title_name = str(row["title_name"] or "Khong xac dinh")
        volume_number = row["volume_number"]
        title = (
            f"{title_name} Tap {volume_number}"
            if volume_number is not None
            else title_name
        )
        preview_lines.append(
            RentalContractPreviewLine(
                item_id=item_id,
                barcode=item_id,
                title=title,
                rental_fee=int(row["final_rent_price"]),
                final_deposit=int(row["final_deposit"]),
                overdue_days=overdue_days,
            )
        )

    return success_response(
        RentalContractPreviewPayload(
            contract_id=str(contract_row["id"]),
            customer_id=str(contract_row["customer_id"]),
            customer_name=str(contract_row["customer_name"]),
            status=str(contract_row["status"]),
            due_date=to_iso_z(due_date),
            deposit_total=int(contract_row["deposit_total"]),
            remaining_deposit=int(contract_row["remaining_deposit"]),
            overdue_fee_per_day=int(settings.overdue_fee_per_day),
            damage_fee_minor_percent=int(settings.damage_fee_minor_percent),
            damage_fee_major_percent=int(settings.damage_fee_major_percent),
            return_lines=preview_lines,
        )
    )


@router.get(
    "/contracts/{contract_id}/settlement",
    response_model=ResponseEnvelope[RentalSettlementStatusPayload],
)
async def get_rental_settlement_status(
    contract_id: int = Path(gt=0),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[RentalSettlementStatusPayload]:
    auth.require_role("cashier", "manager", "owner")
    auth.require_scope("rental:return")

    result = await session.execute(
        text(
            """
            SELECT
                rc.id AS contract_id,
                rc.status AS contract_status,
                rs.id AS settlement_id,
                rs.rental_fee,
                rs.late_fee,
                rs.damage_fee,
                rs.lost_fee,
                rs.total_fee,
                rs.deducted_from_deposit,
                rs.refund_to_customer,
                rs.remaining_debt,
                rs.settled_at
            FROM rental_contract rc
            LEFT JOIN rental_settlement rs ON rs.contract_id = rc.id
            WHERE rc.id = :contract_id
              AND rc.deleted_at IS NULL;
            """
        ),
        {"contract_id": contract_id},
    )
    row = result.mappings().first()
    if row is None:
        raise AppError(
            code="CONTRACT_NOT_FOUND",
            message="Khong tim thay hop dong can xem settlement.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return success_response(
        RentalSettlementStatusPayload(
            settlement_id=str(row["settlement_id"]) if row["settlement_id"] is not None else None,
            contract_id=str(row["contract_id"]),
            rental_fee=int(row["rental_fee"] or 0),
            late_fee=int(row["late_fee"] or 0),
            damage_fee=int(row["damage_fee"] or 0),
            lost_fee=int(row["lost_fee"] or 0),
            total_fee=int(row["total_fee"] or 0),
            deducted_from_deposit=int(row["deducted_from_deposit"] or 0),
            refund_to_customer=int(row["refund_to_customer"] or 0),
            remaining_debt=int(row["remaining_debt"] or 0),
            settled_at=str(row["settled_at"]) if row["settled_at"] is not None else None,
            contract_status=str(row["contract_status"]),
        )
    )


@router.post("/contracts", response_model=ResponseEnvelope[CreateRentalContractPayload])
async def create_rental_contract(
    payload: CreateRentalContractRequest,
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> ResponseEnvelope[CreateRentalContractPayload] | dict[str, object]:
    auth.require_role("cashier", "manager")
    auth.require_scope("rental:write")

    cached = await get_cached_response(
        session,
        scope="rental.create_contract",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload
    if session.in_transaction():
        await session.rollback()

    now = utc_now()
    now_iso = to_iso_z(now)
    due_date = parse_iso_datetime(payload.due_date)
    due_date_iso = to_iso_z(due_date)
    if due_date <= now:
        raise AppError(
            code="INVALID_DUE_DATE",
            message="Due date phai lon hon thoi diem tao hop dong.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    async with session.begin():
        pricing_rule = await resolve_active_price_rule(session)

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
                message="Khong tim thay khach hang cho hop dong thue.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if int(customer_row["blacklist_flag"]) == 1:
            raise AppError(
                code="CUSTOMER_BLACKLISTED",
                message="Khach hang dang blacklist, khong the tao hop dong thue.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        selected_items: list[dict[str, object]] = []
        for item_id in payload.item_ids:
            row_result = await session.execute(
                text(
                    """
                    SELECT
                        i.id,
                        i.volume_id,
                        i.status,
                        i.reserved_by_customer_id,
                        i.reservation_expire_at,
                        i.condition_level,
                        i.health_percent,
                        v.p_sell_new
                    FROM item i
                    JOIN volume v ON v.id = i.volume_id
                    WHERE i.id = :item_id
                      AND i.deleted_at IS NULL
                      AND v.deleted_at IS NULL;
                    """
                ),
                {"item_id": item_id},
            )
            item_row = row_result.mappings().first()
            if item_row is None:
                raise AppError(
                    code="ITEM_NOT_AVAILABLE",
                    message="Mot hoac nhieu item khong san sang de cho thue.",
                    status_code=status.HTTP_409_CONFLICT,
                )

            if item_row["status"] == "reserved" and item_row["reservation_expire_at"] is not None:
                expire_at = parse_iso_datetime(str(item_row["reservation_expire_at"]))
                if expire_at <= now:
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
                            WHERE id = :item_id;
                            """
                        ),
                        {"item_id": item_id},
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
                        {"item_id": item_id, "now_iso": now_iso},
                    )
                    item_row = {
                        **dict(item_row),
                        "status": "available",
                        "reserved_by_customer_id": None,
                    }

            is_reserved_for_customer = (
                item_row["status"] == "reserved"
                and int(item_row["reserved_by_customer_id"] or 0) == payload.customer_id
            )
            if item_row["status"] != "available" and not is_reserved_for_customer:
                raise AppError(
                    code="ITEM_NOT_AVAILABLE",
                    message="Mot hoac nhieu item khong san sang de cho thue.",
                    status_code=status.HTTP_409_CONFLICT,
                )

            selected_items.append(dict(item_row))

        rental_items: list[RentalItemSnapshot] = []
        auto_deposit_total = 0
        for item_row in selected_items:
            p_sell_new = int(item_row["p_sell_new"])
            rent_price = compute_rent_price(
                condition_level=int(item_row["condition_level"]),
                p_sell_new=p_sell_new,
                k_rent=pricing_rule.k_rent,
            )
            deposit_amount = compute_deposit(
                p_sell_new=p_sell_new,
                k_deposit=pricing_rule.k_deposit,
                d_floor=pricing_rule.d_floor,
            )
            auto_deposit_total += deposit_amount
            rental_items.append(
                RentalItemSnapshot(
                    item_id=str(item_row["id"]),
                    final_rent_price=rent_price,
                    final_deposit=deposit_amount,
                    status="rented",
                )
            )

        if payload.deposit_policy == "manual":
            manual_deposit = int(payload.manual_deposit or 0)
            if manual_deposit < auto_deposit_total:
                raise AppError(
                    code="DEPOSIT_NOT_ENOUGH",
                    message="Tien coc thu cong thap hon muc toi thieu cua he thong.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            deposit_total = manual_deposit
        else:
            deposit_total = auto_deposit_total

        for selected_item in selected_items:
            lock_result = await session.execute(
                text(
                    """
                    UPDATE item
                    SET
                        status = 'rented',
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
                            AND reserved_by_customer_id = :customer_id
                            AND reservation_expire_at > :now_iso
                        )
                      );
                    """
                ),
                {
                    "item_id": selected_item["id"],
                    "customer_id": payload.customer_id,
                    "now_iso": now_iso,
                },
            )
            if lock_result.rowcount != 1:
                raise AppError(
                    code="RENTAL_LOCK_CONFLICT",
                    message="Khong the khoa item de tao hop dong thue.",
                    status_code=status.HTTP_423_LOCKED,
                )

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
                    created_by_user_id,
                    created_at,
                    updated_at,
                    deleted_at
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
                    :created_by_user_id,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP,
                    NULL
                );
                """
            ),
            {
                "customer_id": payload.customer_id,
                "rent_date": now_iso,
                "due_date": due_date_iso,
                "deposit_total": deposit_total,
                "remaining_deposit": deposit_total,
                "request_id": payload.request_id,
                "created_by_user_id": auth.user_id,
            },
        )
        contract_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
        contract_id = int(contract_id_result.scalar_one())

        for rental_item in rental_items:
            item_meta = next(item for item in selected_items if item["id"] == rental_item.item_id)
            await session.execute(
                text(
                    """
                    INSERT INTO rental_item (
                        contract_id,
                        item_id,
                        final_rent_price,
                        final_deposit,
                        status,
                        condition_before,
                        condition_after
                    )
                    VALUES (
                        :contract_id,
                        :item_id,
                        :final_rent_price,
                        :final_deposit,
                        'rented',
                        :condition_before,
                        NULL
                    );
                    """
                ),
                {
                    "contract_id": contract_id,
                    "item_id": rental_item.item_id,
                    "final_rent_price": rental_item.final_rent_price,
                    "final_deposit": rental_item.final_deposit,
                    "condition_before": int(item_meta["condition_level"]),
                },
            )
            rental_item_id_result = await session.execute(text("SELECT last_insert_rowid() AS value;"))
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
                        0,
                        NULL,
                        NULL,
                        NULL,
                        NULL
                    );
                    """
                ),
                {
                    "rental_contract_id": contract_id,
                    "rental_item_id": rental_item_id,
                    "volume_id": int(item_meta["volume_id"]),
                    "item_id": rental_item.item_id,
                    "p_sell_new_snapshot": int(item_meta["p_sell_new"]),
                    "rent_ratio_snapshot": pricing_rule.k_rent,
                    "deposit_ratio_snapshot": pricing_rule.k_deposit,
                    "deposit_floor_snapshot": pricing_rule.d_floor,
                    "final_rent_price": rental_item.final_rent_price,
                    "final_deposit": rental_item.final_deposit,
                    "line_total": rental_item.final_rent_price + rental_item.final_deposit,
                    "price_rule_id": pricing_rule.rule_id,
                    "price_rule_version": pricing_rule.version_no,
                },
            )
            await session.execute(
                text(
                    """
                    UPDATE reservation
                    SET status = 'converted', converted_to = 'rented'
                    WHERE item_id = :item_id AND status = 'active';
                    """
                ),
                {"item_id": rental_item.item_id},
            )

        ip_address, device_id = get_request_meta(request)
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="RENTAL_CONTRACT_CREATED",
            entity_type="rental_contract",
            entity_id=str(contract_id),
            before=None,
            after={
                "status": "active",
                "customer_id": payload.customer_id,
                "due_date": due_date_iso,
                "deposit_total": deposit_total,
                "price_rule_version": pricing_rule.version_no,
            },
            ip_address=ip_address,
            device_id=device_id,
        )

    envelope = success_response(
        CreateRentalContractPayload(
            contract_id=str(contract_id),
            customer_id=str(payload.customer_id),
            rent_date=now_iso,
            due_date=due_date_iso,
            deposit_total=deposit_total,
            rental_items=rental_items,
        )
    )

    for selected_item in selected_items:
        await event_publisher.publish_item_status_changed(
            item_id=str(selected_item["id"]),
            old_status=str(selected_item["status"]),
            new_status="rented",
            changed_at=now_iso,
            source_api="rental_create_contract_v1",
            changed_by=auth.user_id,
            branch_id=auth.branch_id,
        )

    try:
        async with session.begin():
            await store_cached_response(
                session,
                scope="rental.create_contract",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        cached = await get_cached_response(
            session,
            scope="rental.create_contract",
            request_id=payload.request_id,
        )
        if cached is not None:
            return cached.payload
        raise

    return envelope


@router.post(
    "/contracts/{contract_id}/extend",
    response_model=ResponseEnvelope[ExtendRentalContractPayload],
)
async def extend_rental_contract(
    payload: ExtendRentalContractRequest,
    request: Request,
    contract_id: int = Path(gt=0),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[ExtendRentalContractPayload] | dict[str, object]:
    auth.require_role("cashier", "manager")
    auth.require_scope("rental:extend")

    cached = await get_cached_response(
        session,
        scope="rental.extend_contract",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload
    if session.in_transaction():
        await session.rollback()

    now = utc_now()
    new_due_date = parse_iso_datetime(payload.new_due_date)
    new_due_date_iso = to_iso_z(new_due_date)

    async with session.begin():
        contract_result = await session.execute(
            text(
                """
                SELECT id, status, due_date, deposit_total, remaining_deposit
                FROM rental_contract
                WHERE id = :contract_id AND deleted_at IS NULL;
                """
            ),
            {"contract_id": contract_id},
        )
        contract_row = contract_result.mappings().first()
        if contract_row is None:
            raise AppError(
                code="CONTRACT_NOT_FOUND",
                message="Khong tim thay hop dong can gia han.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if contract_row["status"] in {"closed", "cancelled"}:
            raise AppError(
                code="CONTRACT_ALREADY_CLOSED",
                message="Hop dong da dong, khong the gia han.",
                status_code=status.HTTP_409_CONFLICT,
            )
        if contract_row["status"] not in {"active", "overdue"}:
            raise AppError(
                code="EXTENSION_NOT_ALLOWED",
                message="Trang thai hop dong hien tai khong cho phep gia han.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        old_due_date = parse_iso_datetime(str(contract_row["due_date"]))
        if new_due_date <= old_due_date:
            raise AppError(
                code="INVALID_DUE_DATE",
                message="Due date moi phai lon hon due date hien tai.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        next_status: Literal["active", "overdue"] = "active"
        if new_due_date < now:
            next_status = "overdue"

        next_deposit_total = int(contract_row["deposit_total"]) + payload.additional_deposit
        next_remaining_deposit = int(contract_row["remaining_deposit"]) + payload.additional_deposit

        await session.execute(
            text(
                """
                UPDATE rental_contract
                SET
                    due_date = :new_due_date,
                    status = :status,
                    deposit_total = :deposit_total,
                    remaining_deposit = :remaining_deposit,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :contract_id;
                """
            ),
            {
                "new_due_date": new_due_date_iso,
                "status": next_status,
                "deposit_total": next_deposit_total,
                "remaining_deposit": next_remaining_deposit,
                "contract_id": contract_id,
            },
        )

        ip_address, device_id = get_request_meta(request)
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="RENTAL_CONTRACT_EXTENDED",
            entity_type="rental_contract",
            entity_id=str(contract_id),
            before={
                "status": contract_row["status"],
                "due_date": contract_row["due_date"],
            },
            after={
                "status": next_status,
                "due_date": new_due_date_iso,
                "additional_deposit": payload.additional_deposit,
            },
            ip_address=ip_address,
            device_id=device_id,
        )

    envelope = success_response(
        ExtendRentalContractPayload(
            contract_id=str(contract_id),
            old_due_date=to_iso_z(old_due_date),
            new_due_date=new_due_date_iso,
            additional_fee=0,
            additional_deposit=payload.additional_deposit,
            status=next_status,
        )
    )

    try:
        async with session.begin():
            await store_cached_response(
                session,
                scope="rental.extend_contract",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        cached = await get_cached_response(
            session,
            scope="rental.extend_contract",
            request_id=payload.request_id,
        )
        if cached is not None:
            return cached.payload
        raise

    return envelope


@router.post(
    "/contracts/{contract_id}/return",
    response_model=ResponseEnvelope[ReturnRentalItemsPayload],
)
async def return_rental_items(
    payload: ReturnRentalItemsRequest,
    request: Request,
    contract_id: int = Path(gt=0),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> ResponseEnvelope[ReturnRentalItemsPayload] | dict[str, object]:
    auth.require_role("cashier", "manager")
    auth.require_scope("rental:return")

    cached = await get_cached_response(
        session,
        scope="rental.return_items",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload
    if session.in_transaction():
        await session.rollback()

    returned_at = parse_iso_datetime(payload.returned_at) if payload.returned_at else utc_now()
    returned_at_iso = to_iso_z(returned_at)

    async with session.begin():
        contract_result = await session.execute(
            text(
                """
                SELECT id, status, due_date, remaining_deposit, debt_total
                FROM rental_contract
                WHERE id = :contract_id AND deleted_at IS NULL;
                """
            ),
            {"contract_id": contract_id},
        )
        contract_row = contract_result.mappings().first()
        if contract_row is None:
            raise AppError(
                code="CONTRACT_NOT_FOUND",
                message="Khong tim thay hop dong can xu ly tra.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if contract_row["status"] in {"closed", "cancelled"}:
            raise AppError(
                code="CONTRACT_NOT_FOUND",
                message="Hop dong da dong hoac da huy, khong the xu ly tra.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        due_date = parse_iso_datetime(str(contract_row["due_date"]))
        delay_days = max((returned_at.date() - due_date.date()).days, 0)

        rental_item_result = await session.execute(
            text(
                """
                SELECT
                    id,
                    item_id,
                    final_rent_price,
                    final_deposit,
                    status,
                    condition_before,
                    condition_after
                FROM rental_item
                WHERE contract_id = :contract_id;
                """
            ),
            {"contract_id": contract_id},
        )
        contract_items = {str(row["item_id"]): dict(row) for row in rental_item_result.mappings()}

        rental_fee = 0
        late_fee = 0
        damage_fee = 0
        lost_fee = 0
        status_change_events: list[tuple[str, str, str]] = []

        for line in payload.return_lines:
            item_row = contract_items.get(line.item_id)
            if item_row is None:
                raise AppError(
                    code="ITEM_NOT_IN_CONTRACT",
                    message="Co item khong thuoc hop dong hien tai.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if item_row["status"] in {"returned", "lost"}:
                raise AppError(
                    code="RETURN_DUPLICATED",
                    message="Item da duoc ghi nhan tra truoc do.",
                    status_code=status.HTTP_409_CONFLICT,
                )

            rent_price = int(item_row["final_rent_price"])
            deposit = int(item_row["final_deposit"])
            rental_fee += rent_price
            if delay_days > 0:
                late_fee += delay_days * int(settings.overdue_fee_per_day)
            damage_fee += _calculate_damage_fee(deposit, line.condition_after)
            if line.condition_after == "lost":
                lost_fee += deposit

            next_status = "lost" if line.condition_after == "lost" else "returned"
            condition_level_after = _condition_to_level(
                line.condition_after, int(item_row["condition_before"])
            )

            await session.execute(
                text(
                    """
                    UPDATE rental_item
                    SET
                        status = :status,
                        condition_after = :condition_after
                    WHERE id = :rental_item_id;
                    """
                ),
                {
                    "status": next_status,
                    "condition_after": condition_level_after,
                    "rental_item_id": int(item_row["id"]),
                },
            )

            item_target_status = "lost" if line.condition_after == "lost" else "available"
            await session.execute(
                text(
                    """
                    UPDATE item
                    SET
                        status = :status,
                        condition_level = :condition_level,
                        health_percent = :health_percent,
                        reserved_by_customer_id = NULL,
                        reserved_at = NULL,
                        reservation_expire_at = NULL,
                        version_no = version_no + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :item_id;
                    """
                ),
                {
                    "status": item_target_status,
                    "condition_level": condition_level_after,
                    "health_percent": condition_level_after,
                    "item_id": line.item_id,
                },
            )
            status_change_events.append((line.item_id, str(item_row["status"]), item_target_status))

        total_fee = rental_fee + late_fee + damage_fee + lost_fee
        remaining_deposit_before = int(contract_row["remaining_deposit"])
        deducted_from_deposit = min(total_fee, remaining_deposit_before)
        remaining_debt = max(total_fee - remaining_deposit_before, 0)
        remaining_deposit_after = remaining_deposit_before - deducted_from_deposit

        open_items_result = await session.execute(
            text(
                """
                SELECT COUNT(*) AS total
                FROM rental_item
                WHERE contract_id = :contract_id AND status = 'rented';
                """
            ),
            {"contract_id": contract_id},
        )
        open_items = int(open_items_result.scalar_one())
        contract_status: Literal["partial_returned", "closed"] = (
            "closed" if open_items == 0 else "partial_returned"
        )

        refund_to_customer = 0
        stored_remaining_deposit = remaining_deposit_after
        if contract_status == "closed" and remaining_deposit_after > 0:
            refund_to_customer = remaining_deposit_after
            stored_remaining_deposit = 0

        next_debt_total = int(contract_row["debt_total"]) + remaining_debt

        await session.execute(
            text(
                """
                UPDATE rental_contract
                SET
                    status = :status,
                    remaining_deposit = :remaining_deposit,
                    debt_total = :debt_total,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :contract_id;
                """
            ),
            {
                "status": contract_status,
                "remaining_deposit": stored_remaining_deposit,
                "debt_total": next_debt_total,
                "contract_id": contract_id,
            },
        )

        settlement_result = await session.execute(
            text(
                """
                SELECT
                    id,
                    rental_fee,
                    late_fee,
                    damage_fee,
                    lost_fee,
                    total_fee,
                    deducted_from_deposit,
                    refund_to_customer,
                    remaining_debt
                FROM rental_settlement
                WHERE contract_id = :contract_id;
                """
            ),
            {"contract_id": contract_id},
        )
        settlement_row = settlement_result.mappings().first()

        if settlement_row is None:
            await session.execute(
                text(
                    """
                    INSERT INTO rental_settlement (
                        contract_id,
                        rental_fee,
                        late_fee,
                        damage_fee,
                        lost_fee,
                        total_fee,
                        deducted_from_deposit,
                        refund_to_customer,
                        remaining_debt,
                        settled_at
                    )
                    VALUES (
                        :contract_id,
                        :rental_fee,
                        :late_fee,
                        :damage_fee,
                        :lost_fee,
                        :total_fee,
                        :deducted_from_deposit,
                        :refund_to_customer,
                        :remaining_debt,
                        :settled_at
                    );
                    """
                ),
                {
                    "contract_id": contract_id,
                    "rental_fee": rental_fee,
                    "late_fee": late_fee,
                    "damage_fee": damage_fee,
                    "lost_fee": lost_fee,
                    "total_fee": total_fee,
                    "deducted_from_deposit": deducted_from_deposit,
                    "refund_to_customer": refund_to_customer,
                    "remaining_debt": remaining_debt,
                    "settled_at": returned_at_iso,
                },
            )
            settlement_id_result = await session.execute(
                text("SELECT last_insert_rowid() AS value;")
            )
            settlement_id = int(settlement_id_result.scalar_one())
            aggregated = {
                "rental_fee": rental_fee,
                "late_fee": late_fee,
                "damage_fee": damage_fee,
                "lost_fee": lost_fee,
                "total_fee": total_fee,
                "deducted_from_deposit": deducted_from_deposit,
                "refund_to_customer": refund_to_customer,
                "remaining_debt": remaining_debt,
            }
        else:
            settlement_id = int(settlement_row["id"])
            aggregated = {
                "rental_fee": int(settlement_row["rental_fee"]) + rental_fee,
                "late_fee": int(settlement_row["late_fee"]) + late_fee,
                "damage_fee": int(settlement_row["damage_fee"]) + damage_fee,
                "lost_fee": int(settlement_row["lost_fee"]) + lost_fee,
                "total_fee": int(settlement_row["total_fee"]) + total_fee,
                "deducted_from_deposit": int(settlement_row["deducted_from_deposit"])
                + deducted_from_deposit,
                "refund_to_customer": int(settlement_row["refund_to_customer"])
                + refund_to_customer,
                "remaining_debt": int(settlement_row["remaining_debt"]) + remaining_debt,
            }
            await session.execute(
                text(
                    """
                    UPDATE rental_settlement
                    SET
                        rental_fee = :rental_fee,
                        late_fee = :late_fee,
                        damage_fee = :damage_fee,
                        lost_fee = :lost_fee,
                        total_fee = :total_fee,
                        deducted_from_deposit = :deducted_from_deposit,
                        refund_to_customer = :refund_to_customer,
                        remaining_debt = :remaining_debt,
                        settled_at = :settled_at
                    WHERE id = :settlement_id;
                    """
                ),
                {
                    "rental_fee": aggregated["rental_fee"],
                    "late_fee": aggregated["late_fee"],
                    "damage_fee": aggregated["damage_fee"],
                    "lost_fee": aggregated["lost_fee"],
                    "total_fee": aggregated["total_fee"],
                    "deducted_from_deposit": aggregated["deducted_from_deposit"],
                    "refund_to_customer": aggregated["refund_to_customer"],
                    "remaining_debt": aggregated["remaining_debt"],
                    "settled_at": returned_at_iso,
                    "settlement_id": settlement_id,
                },
            )

        ip_address, device_id = get_request_meta(request)
        await write_audit_log(
            session,
            actor_user_id=auth.user_id,
            action="RENTAL_SETTLEMENT_RECORDED",
            entity_type="rental_contract",
            entity_id=str(contract_id),
            before={
                "status": contract_row["status"],
                "remaining_deposit": contract_row["remaining_deposit"],
            },
            after={
                "status": contract_status,
                "remaining_deposit": stored_remaining_deposit,
                "remaining_debt": next_debt_total,
                "settlement_id": settlement_id,
            },
            ip_address=ip_address,
            device_id=device_id,
        )

    envelope = success_response(
        ReturnRentalItemsPayload(
            settlement_id=str(settlement_id),
            contract_id=str(contract_id),
            rental_fee=int(aggregated["rental_fee"]),
            late_fee=int(aggregated["late_fee"]),
            damage_fee=int(aggregated["damage_fee"]),
            lost_fee=int(aggregated["lost_fee"]),
            total_fee=int(aggregated["total_fee"]),
            deducted_from_deposit=int(aggregated["deducted_from_deposit"]),
            refund_to_customer=int(aggregated["refund_to_customer"]),
            remaining_debt=int(aggregated["remaining_debt"]),
            contract_status=contract_status,
        )
    )

    for item_id, old_status, new_status in status_change_events:
        await event_publisher.publish_item_status_changed(
            item_id=item_id,
            old_status=old_status,
            new_status=new_status,
            changed_at=returned_at_iso,
            source_api="rental_return_items_v1",
            changed_by=auth.user_id,
            branch_id=auth.branch_id,
        )

    await event_publisher.publish_rental_settlement_finished(
        settlement_id=str(settlement_id),
        contract_id=str(contract_id),
        total_fee=int(aggregated["total_fee"]),
        refund_to_customer=int(aggregated["refund_to_customer"]),
        remaining_debt=int(aggregated["remaining_debt"]),
        settled_at=returned_at_iso,
        branch_id=auth.branch_id,
    )

    try:
        async with session.begin():
            await store_cached_response(
                session,
                scope="rental.return_items",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        cached = await get_cached_response(
            session,
            scope="rental.return_items",
            request_id=payload.request_id,
        )
        if cached is not None:
            return cached.payload
        raise

    return envelope


@router.get(
    "/items/{item_id}/rental-status",
    response_model=ResponseEnvelope[ItemRentalStatusPayload],
)
async def get_item_rental_status(
    item_id: str = Path(min_length=1, max_length=50),
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[ItemRentalStatusPayload]:
    """
    Check if an item is currently rented by looking for active rental contracts.
    Scanner can use this to determine whether to route to return page or create new rental.
    """
    auth.require_scope("rental:read")

    # Query: find if this item is in an active rental contract
    result = await session.execute(
        text(
            """
            SELECT
                rc.id AS contract_id,
                i.status AS item_status
            FROM rental_item ri
            JOIN rental_contract rc ON rc.id = ri.contract_id
            JOIN item i ON i.id = ri.item_id
            WHERE ri.item_id = :item_id
              AND ri.status = 'rented'
              AND rc.status IN ('active', 'partial_returned', 'overdue')
              AND rc.deleted_at IS NULL
            LIMIT 1;
            """
        ),
        {"item_id": item_id},
    )

    row = result.mappings().first()

    if row:
        # Item is rented in an active/partial/overdue contract
        return success_response(
            ItemRentalStatusPayload(
                rental_contract_id=str(row["contract_id"]),
                item_status=str(row["item_status"]),
            )
        )
    else:
        # Item is not currently rented (or not in an active contract)
        return success_response(
            ItemRentalStatusPayload(
                rental_contract_id=None,
                item_status="available",
            )
        )

