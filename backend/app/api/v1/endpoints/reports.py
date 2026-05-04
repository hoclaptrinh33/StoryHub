from __future__ import annotations

from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.dependencies import AuthContext, get_auth_context
from app.api.v1.endpoints._common import parse_iso_datetime
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services import get_cached_response, store_cached_response

router = APIRouter(prefix="/reports", tags=["report"])

_MAX_REPORT_RANGE = timedelta(days=366)


class RevenueSummaryRequest(BaseModel):
    from_date: str = Field(min_length=10)
    to_date: str = Field(min_length=10)
    group_by: Literal["day", "week", "month"]
    include_top_titles: bool = True
    include_inventory_alert: bool = True
    request_id: str = Field(min_length=6, max_length=128)


class RevenueTopTitle(BaseModel):
    title: str
    qty: int
    revenue: int = 0


class InventoryAlertItem(BaseModel):
    title: str
    available_items: int


class FluctuationRequest(BaseModel):
    from_date: str = Field(min_length=10)
    to_date: str = Field(min_length=10)
    group_by: Literal["day", "week", "month", "year"]
    title_id: int | None = None
    request_id: str = Field(min_length=6, max_length=128)


class FluctuationItem(BaseModel):
    period: str
    stock_in: int
    sale: int
    rental: int


class FluctuationTotals(BaseModel):
    stock_in: int = 0
    sale: int = 0
    rental: int = 0


class FluctuationPayload(BaseModel):
    data: list[FluctuationItem]
    totals: FluctuationTotals | None = None


class FluctuationDetailRequest(FluctuationRequest):
    period: str


class FluctuationDetailItem(BaseModel):
    volume_id: int
    volume_name: str
    isbn: str | None
    stock_in: int
    sale: int
    rental: int


class FluctuationDetailPayload(BaseModel):
    data: list[FluctuationDetailItem]


class ReportTopCustomer(BaseModel):
    id: int
    name: str
    total_transactions: int
    total_spent: int


class ReportTransactionItem(BaseModel):
    transaction_type: Literal["sale", "rental"]
    reference_id: str
    customer_name: str
    amount: int
    created_at: str


class RevenueSummaryPayload(BaseModel):
    sell_revenue: int
    rental_revenue: int
    penalty_revenue: int
    total_revenue: int
    sold_items: int
    rented_items: int
    new_customers: int
    top_sell_titles: list[RevenueTopTitle]
    top_rent_titles: list[RevenueTopTitle]
    top_customers: list[ReportTopCustomer]
    recent_transactions: list[ReportTransactionItem]
    inventory_alerts: list[InventoryAlertItem]


def _to_positive_int(value: object) -> int:
    try:
        normalized = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, normalized)


async def _detect_pos_order_item_volume_column(session: AsyncSession) -> str:
    table_info_result = await session.execute(text("PRAGMA table_info(pos_order_item);"))
    columns = {str(row[1]) for row in table_info_result.fetchall()}
    if "volume_id" in columns:
        return "volume_id"
    if "item_id" in columns:
        return "item_id"
    raise AppError(
        code="DATA_SOURCE_LOCKED",
        message="Không xác định được cấu trúc dữ liệu cho báo cáo.",
        status_code=status.HTTP_423_LOCKED,
    )


@router.post("/revenue-summary", response_model=ResponseEnvelope[RevenueSummaryPayload])
async def get_revenue_summary_report(
    payload: RevenueSummaryRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[RevenueSummaryPayload] | dict[str, object]:
    auth.require_role("manager", "owner")
    auth.require_scope("report:read")

    cached = await get_cached_response(
        session,
        scope="reports.revenue_summary",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload

    from_date = parse_iso_datetime(payload.from_date)
    to_date = parse_iso_datetime(payload.to_date)

    if from_date > to_date:
        raise AppError(
            code="INVALID_DATE_RANGE",
            message="Khoảng thời gian từ ngày và đến ngày không hợp lệ.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if to_date - from_date > _MAX_REPORT_RANGE:
        raise AppError(
            code="REPORT_RANGE_TOO_LARGE",
            message="Khoảng thời gian báo cáo vượt giới hạn cho phép (tối đa 1 năm).",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Chỉ khóa dữ liệu nếu có backup job đang chạy và được tạo trong vòng 10 phút qua
    # giúp tránh tình trạng bị "kẹt" lock nếu server sập đột ngột
    backup_lock_result = await session.execute(
        text(
            """
            SELECT id
            FROM backup_job
            WHERE status IN ('queued', 'running')
              AND (started_at >= datetime('now', '-10 minutes') OR started_at IS NULL)
            LIMIT 1;
            """
        )
    )
    if backup_lock_result.first() is not None:
        raise AppError(
            code="DATA_SOURCE_LOCKED",
            message="Dữ liệu báo cáo hiện đang bị tạm khóa để đảm bảo an toàn trong quá trình sao lưu hệ thống (đang diễn ra). Vui lòng thử lại sau vài phút.",
            status_code=status.HTTP_423_LOCKED,
        )

    from_iso = payload.from_date
    to_iso = payload.to_date

    sell_result = await session.execute(
        text(
            """
            SELECT COALESCE(SUM(grand_total), 0) AS sell_revenue
            FROM pos_order
            WHERE status IN ('paid', 'partially_refunded', 'refunded')
              AND deleted_at IS NULL
                            AND datetime(created_at) BETWEEN datetime(:from_date) AND datetime(:to_date);
            """
        ),
        {"from_date": from_iso, "to_date": to_iso},
    )
    sell_revenue = _to_positive_int(sell_result.scalar_one())

    rental_result = await session.execute(
        text(
            """
            SELECT
                COALESCE(SUM(rental_fee), 0) AS rental_revenue,
                COALESCE(SUM(late_fee + damage_fee + lost_fee), 0) AS penalty_revenue
            FROM rental_settlement
            WHERE datetime(settled_at) BETWEEN datetime(:from_date) AND datetime(:to_date);
            """
        ),
        {"from_date": from_iso, "to_date": to_iso},
    )
    rental_row = rental_result.mappings().first() or {}
    rental_revenue = _to_positive_int(rental_row.get("rental_revenue"))
    penalty_revenue = _to_positive_int(rental_row.get("penalty_revenue"))

    sold_items_result = await session.execute(
        text(
            """
            SELECT COALESCE(SUM(poi.quantity), 0) AS sold_items
            FROM pos_order_item poi
            JOIN pos_order po ON po.id = poi.order_id
            WHERE po.status IN ('paid', 'partially_refunded', 'refunded')
              AND po.deleted_at IS NULL
              AND datetime(po.created_at) BETWEEN datetime(:from_date) AND datetime(:to_date);
            """
        ),
        {"from_date": from_iso, "to_date": to_iso},
    )
    sold_items = _to_positive_int(sold_items_result.scalar_one())

    rented_items_result = await session.execute(
        text(
            """
            SELECT COALESCE(COUNT(*), 0) AS rented_items
            FROM rental_item ri
            JOIN rental_contract rc ON rc.id = ri.contract_id
            WHERE datetime(rc.rent_date) BETWEEN datetime(:from_date) AND datetime(:to_date);
            """
        ),
        {"from_date": from_iso, "to_date": to_iso},
    )
    rented_items = _to_positive_int(rented_items_result.scalar_one())

    new_customers_result = await session.execute(
        text(
            """
            SELECT COALESCE(COUNT(*), 0) AS new_customers
            FROM customer
            WHERE deleted_at IS NULL
              AND datetime(created_at) BETWEEN datetime(:from_date) AND datetime(:to_date);
            """
        ),
        {"from_date": from_iso, "to_date": to_iso},
    )
    new_customers = _to_positive_int(new_customers_result.scalar_one())

    top_sell_titles: list[RevenueTopTitle] = []
    top_rent_titles: list[RevenueTopTitle] = []
    top_customers: list[ReportTopCustomer] = []
    recent_transactions: list[ReportTransactionItem] = []
    inventory_alerts: list[InventoryAlertItem] = []

    if payload.include_top_titles:
        join_column = await _detect_pos_order_item_volume_column(session)

        if join_column == "volume_id":
            top_sell_query = text(
                """
                SELECT
                    t.name AS title,
                    COALESCE(SUM(poi.quantity), 0) AS qty,
                    COALESCE(SUM(poi.line_total), 0) AS revenue
                FROM pos_order_item poi
                JOIN pos_order po ON po.id = poi.order_id
                JOIN volume v ON v.id = poi.volume_id
                JOIN title t ON t.id = v.title_id
                WHERE po.status IN ('paid', 'partially_refunded', 'refunded')
                  AND po.deleted_at IS NULL
                                    AND datetime(po.created_at) BETWEEN datetime(:from_date) AND datetime(:to_date)
                GROUP BY t.id, t.name
                ORDER BY qty DESC, revenue DESC, t.name ASC
                LIMIT 5;
                """
            )
        else:
            top_sell_query = text(
                """
                SELECT
                    t.name AS title,
                    COALESCE(SUM(poi.quantity), 0) AS qty,
                    COALESCE(SUM(poi.line_total), 0) AS revenue
                FROM pos_order_item poi
                JOIN pos_order po ON po.id = poi.order_id
                JOIN item i ON i.id = poi.item_id
                JOIN volume v ON v.id = i.volume_id
                JOIN title t ON t.id = v.title_id
                WHERE po.status IN ('paid', 'partially_refunded', 'refunded')
                  AND po.deleted_at IS NULL
                                    AND datetime(po.created_at) BETWEEN datetime(:from_date) AND datetime(:to_date)
                GROUP BY t.id, t.name
                ORDER BY qty DESC, revenue DESC, t.name ASC
                LIMIT 5;
                """
            )

        top_sell_result = await session.execute(
            top_sell_query,
            {"from_date": from_iso, "to_date": to_iso},
        )
        top_sell_titles = [
            RevenueTopTitle(
                title=str(row["title"]),
                qty=_to_positive_int(row["qty"]),
                revenue=_to_positive_int(row["revenue"]),
            )
            for row in top_sell_result.mappings().all()
        ]

        top_rent_result = await session.execute(
            text(
                """
                SELECT
                    t.name AS title,
                    COUNT(*) AS qty,
                    COALESCE(SUM(ri.final_rent_price), 0) AS revenue
                FROM rental_item ri
                JOIN rental_contract rc ON rc.id = ri.contract_id
                JOIN item i ON i.id = ri.item_id
                JOIN volume v ON v.id = i.volume_id
                JOIN title t ON t.id = v.title_id
                WHERE datetime(rc.rent_date) BETWEEN datetime(:from_date) AND datetime(:to_date)
                GROUP BY t.id, t.name
                ORDER BY qty DESC, revenue DESC, t.name ASC
                LIMIT 5;
                """
            ),
            {"from_date": from_iso, "to_date": to_iso},
        )
        top_rent_titles = [
            RevenueTopTitle(
                title=str(row["title"]),
                qty=_to_positive_int(row["qty"]),
                revenue=_to_positive_int(row["revenue"]),
            )
            for row in top_rent_result.mappings().all()
        ]

        top_customer_result = await session.execute(
            text(
                """
                WITH customer_txn AS (
                    SELECT
                        po.customer_id AS customer_id,
                        po.id AS txn_id,
                        po.grand_total AS txn_amount
                    FROM pos_order po
                    WHERE po.customer_id IS NOT NULL
                      AND po.status IN ('paid', 'partially_refunded', 'refunded')
                      AND po.deleted_at IS NULL
                      AND datetime(po.created_at) BETWEEN datetime(:from_date) AND datetime(:to_date)

                    UNION ALL

                    SELECT
                        rc.customer_id AS customer_id,
                        rc.id AS txn_id,
                        COALESCE(SUM(ri.final_rent_price + ri.final_deposit), 0) AS txn_amount
                    FROM rental_contract rc
                    LEFT JOIN rental_item ri ON ri.contract_id = rc.id
                    WHERE rc.customer_id IS NOT NULL
                      AND rc.deleted_at IS NULL
                      AND datetime(rc.rent_date) BETWEEN datetime(:from_date) AND datetime(:to_date)
                    GROUP BY rc.id, rc.customer_id
                )
                SELECT
                    c.id AS customer_id,
                    c.name AS customer_name,
                    COUNT(*) AS total_transactions,
                    COALESCE(SUM(customer_txn.txn_amount), 0) AS total_spent
                FROM customer_txn
                JOIN customer c ON c.id = customer_txn.customer_id
                WHERE c.deleted_at IS NULL
                GROUP BY c.id, c.name
                ORDER BY total_transactions DESC, total_spent DESC, c.name ASC
                LIMIT 10;
                """
            ),
            {"from_date": from_iso, "to_date": to_iso},
        )
        top_customers = [
            ReportTopCustomer(
                id=int(row["customer_id"]),
                name=str(row["customer_name"]),
                total_transactions=_to_positive_int(row["total_transactions"]),
                total_spent=_to_positive_int(row["total_spent"]),
            )
            for row in top_customer_result.mappings().all()
        ]

        recent_txn_result = await session.execute(
            text(
                """
                SELECT
                    *
                FROM (
                    SELECT
                        'sale' AS transaction_type,
                        CAST(po.id AS TEXT) AS reference_id,
                        COALESCE(c.name, 'Khach le') AS customer_name,
                        po.grand_total AS amount,
                        po.created_at AS created_at
                    FROM pos_order po
                    LEFT JOIN customer c ON c.id = po.customer_id
                    WHERE po.status IN ('paid', 'partially_refunded', 'refunded')
                      AND po.deleted_at IS NULL
                      AND datetime(po.created_at) BETWEEN datetime(:from_date) AND datetime(:to_date)

                    UNION ALL

                    SELECT
                        'rental' AS transaction_type,
                        CAST(rc.id AS TEXT) AS reference_id,
                        COALESCE(c.name, 'Khach le') AS customer_name,
                        COALESCE(SUM(ri.final_rent_price + ri.final_deposit), 0) AS amount,
                        rc.rent_date AS created_at
                    FROM rental_contract rc
                    LEFT JOIN customer c ON c.id = rc.customer_id
                    LEFT JOIN rental_item ri ON ri.contract_id = rc.id
                    WHERE rc.deleted_at IS NULL
                      AND datetime(rc.rent_date) BETWEEN datetime(:from_date) AND datetime(:to_date)
                    GROUP BY rc.id, rc.customer_id, c.name, rc.rent_date
                )
                ORDER BY datetime(created_at) DESC
                LIMIT 20;
                """
            ),
            {"from_date": from_iso, "to_date": to_iso},
        )
        recent_transactions = [
            ReportTransactionItem(
                transaction_type=str(row["transaction_type"]),
                reference_id=str(row["reference_id"]),
                customer_name=str(row["customer_name"]),
                amount=_to_positive_int(row["amount"]),
                created_at=str(row["created_at"]),
            )
            for row in recent_txn_result.mappings().all()
        ]

    if payload.include_inventory_alert:
        inventory_alert_result = await session.execute(
            text(
                """
                SELECT
                    t.name AS title,
                    COUNT(i.id) AS available_items
                FROM item i
                JOIN volume v ON v.id = i.volume_id
                JOIN title t ON t.id = v.title_id
                WHERE i.deleted_at IS NULL
                  AND i.status = 'available'
                GROUP BY t.id, t.name
                HAVING COUNT(i.id) <= 2
                ORDER BY available_items ASC, t.name ASC
                LIMIT 10;
                """
            )
        )
        inventory_alerts = [
            InventoryAlertItem(
                title=str(row["title"]),
                available_items=_to_positive_int(row["available_items"]),
            )
            for row in inventory_alert_result.mappings().all()
        ]

    total_revenue = sell_revenue + rental_revenue + penalty_revenue

    envelope = success_response(
        RevenueSummaryPayload(
            sell_revenue=sell_revenue,
            rental_revenue=rental_revenue,
            penalty_revenue=penalty_revenue,
            total_revenue=total_revenue,
            sold_items=sold_items,
            rented_items=rented_items,
            new_customers=new_customers,
            top_sell_titles=top_sell_titles,
            top_rent_titles=top_rent_titles,
            top_customers=top_customers,
            recent_transactions=recent_transactions,
            inventory_alerts=inventory_alerts,
        )
    )

    try:
        if session.in_transaction():
            await session.rollback()
        async with session.begin():
            await store_cached_response(
                session,
                scope="reports.revenue_summary",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        await session.rollback()
        replay = await get_cached_response(
            session,
            scope="reports.revenue_summary",
            request_id=payload.request_id,
        )
        if replay is not None:
            return replay.payload
        raise

    return envelope


@router.post("/inventory-fluctuations", response_model=ResponseEnvelope[FluctuationPayload])
async def get_inventory_fluctuations(
    payload: FluctuationRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[FluctuationPayload] | dict[str, object]:
    auth.require_role("manager", "owner")
    auth.require_scope("report:read")

    cached = await get_cached_response(
        session,
        scope="reports.inventory_fluctuations",
        request_id=payload.request_id,
    )
    if cached is not None:
        return cached.payload

    from_iso = payload.from_date
    to_iso = payload.to_date
    group_by = payload.group_by
    title_id = payload.title_id

    # SQLite format string based on group_by
    if group_by == "day":
        date_fmt = "%Y-%m-%d"
    elif group_by == "week":
        date_fmt = "%Y-W%W"
    elif group_by == "month":
        date_fmt = "%Y-%m"
    else:  # year
        date_fmt = "%Y"

    # Check join column for pos_order_item
    join_column = await _detect_pos_order_item_volume_column(session)

    # Base filter for title_id
    stock_title_filter = "AND v.title_id = :title_id" if title_id else ""
    sale_title_filter = ""
    rental_title_filter = "AND v.title_id = :title_id" if title_id else ""

    if title_id:
        if join_column == "volume_id":
            sale_title_filter = "AND v.title_id = :title_id"
        else:
            sale_title_filter = "AND v.title_id = :title_id" # both join through volume

    query = f"""
        SELECT 
            period,
            SUM(stock_in) AS stock_in,
            SUM(sale) AS sale,
            SUM(rental) AS rental
        FROM (
            -- STOCK_IN
            SELECT 
                strftime('{date_fmt}', l.created_at) AS period,
                SUM(l.change_qty) AS stock_in,
                0 AS sale,
                0 AS rental
            FROM inventory_log l
            JOIN volume v ON CAST(l.target_id AS INTEGER) = v.id
            WHERE l.action_type = 'STOCK_IN' 
              AND l.target_type = 'VOLUME'
              AND date(l.created_at) BETWEEN date(:from_date) AND date(:to_date)
              {stock_title_filter}
            GROUP BY period

            UNION ALL

            -- SALE
            SELECT 
                strftime('{date_fmt}', po.created_at) AS period,
                0 AS stock_in,
                SUM(poi.quantity) AS sale,
                0 AS rental
            FROM pos_order_item poi
            JOIN pos_order po ON po.id = poi.order_id
            {"JOIN volume v ON v.id = poi.volume_id" if join_column == "volume_id" else "JOIN item i ON i.id = poi.item_id JOIN volume v ON v.id = i.volume_id"}
            WHERE po.status IN ('paid', 'partially_refunded', 'refunded')
              AND po.deleted_at IS NULL
              AND date(po.created_at) BETWEEN date(:from_date) AND date(:to_date)
              {sale_title_filter}
            GROUP BY period

            UNION ALL

            -- RENTAL
            SELECT 
                strftime('{date_fmt}', rc.rent_date) AS period,
                0 AS stock_in,
                0 AS sale,
                COUNT(*) AS rental
            FROM rental_item ri
            JOIN rental_contract rc ON rc.id = ri.contract_id
            JOIN item i ON i.id = ri.item_id
            JOIN volume v ON v.id = i.volume_id
            WHERE rc.deleted_at IS NULL
              AND date(rc.rent_date) BETWEEN date(:from_date) AND date(:to_date)
              {rental_title_filter}
            GROUP BY period
        )
        GROUP BY period
        ORDER BY period ASC;
    """

    params = {"from_date": from_iso, "to_date": to_iso}
    if title_id:
        params["title_id"] = title_id

    result = await session.execute(text(query), params)
    rows = result.mappings().all()

    data = [
        FluctuationItem(
            period=str(row["period"]),
            stock_in=int(row["stock_in"] or 0),
            sale=int(row["sale"] or 0),
            rental=int(row["rental"] or 0)
        )
        for row in rows
    ]

    totals = FluctuationTotals(
        stock_in=sum(i.stock_in for i in data),
        sale=sum(i.sale for i in data),
        rental=sum(i.rental for i in data)
    )

    envelope = success_response(FluctuationPayload(data=data, totals=totals))

    try:
        if session.in_transaction():
            await session.rollback()
        async with session.begin():
            await store_cached_response(
                session,
                scope="reports.inventory_fluctuations",
                request_id=payload.request_id,
                status_code=status.HTTP_200_OK,
                payload=envelope.model_dump(),
            )
    except IntegrityError:
        pass

    return envelope


@router.post("/inventory-fluctuations/detail", response_model=ResponseEnvelope[FluctuationDetailPayload])
async def get_fluctuation_details(
    payload: FluctuationDetailRequest,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[FluctuationDetailPayload] | dict[str, object]:
    auth.require_role("manager", "owner")
    auth.require_scope("report:read")

    # Grouping logic remains similar but adds v.id and v.volume_number
    if payload.group_by == "day":
        date_fmt = "%Y-%m-%d"
    elif payload.group_by == "week":
        date_fmt = "%Y-W%W"
    elif payload.group_by == "month":
        date_fmt = "%Y-%m"
    else:
        date_fmt = "%Y"

    from_iso = payload.from_date
    to_iso = payload.to_date
    title_id = payload.title_id
    period = payload.period

    join_column = await _detect_pos_order_item_volume_column(session)
    stock_title_filter = "AND v.title_id = :title_id" if title_id else ""
    sale_title_filter = "AND v.title_id = :title_id" if title_id else ""
    rental_title_filter = "AND v.title_id = :title_id" if title_id else ""

    query = f"""
        SELECT 
            v.id AS volume_id,
            t.name || ' - Tập ' || v.volume_number AS volume_name,
            v.isbn,
            SUM(stock_in) AS stock_in,
            SUM(sale) AS sale,
            SUM(rental) AS rental
        FROM (
            -- STOCK_IN
            SELECT 
                CAST(l.target_id AS INTEGER) as volume_id,
                SUM(l.change_qty) AS stock_in,
                0 AS sale,
                0 AS rental
            FROM inventory_log l
            WHERE l.action_type = 'STOCK_IN' 
              AND l.target_type = 'VOLUME'
              AND strftime('{date_fmt}', l.created_at) = :period
              AND date(l.created_at) BETWEEN date(:from_date) AND date(:to_date)
            GROUP BY volume_id

            UNION ALL

            -- SALE
            SELECT 
                {"poi.volume_id" if join_column == "volume_id" else "v.id"} AS volume_id,
                0 AS stock_in,
                SUM(poi.quantity) AS sale,
                0 AS rental
            FROM pos_order_item poi
            JOIN pos_order po ON po.id = poi.order_id
            {"JOIN volume v ON v.id = poi.volume_id" if join_column == "volume_id" else "JOIN item i ON i.id = poi.item_id JOIN volume v ON v.id = i.volume_id"}
            WHERE po.status IN ('paid', 'partially_refunded', 'refunded')
              AND po.deleted_at IS NULL
              AND strftime('{date_fmt}', po.created_at) = :period
              AND date(po.created_at) BETWEEN date(:from_date) AND date(:to_date)
            GROUP BY volume_id

            UNION ALL

            -- RENTAL
            SELECT 
                v.id AS volume_id,
                0 AS stock_in,
                0 AS sale,
                COUNT(*) AS rental
            FROM rental_item ri
            JOIN rental_contract rc ON rc.id = ri.contract_id
            JOIN item i ON i.id = ri.item_id
            JOIN volume v ON v.id = i.volume_id
            WHERE rc.deleted_at IS NULL
              AND strftime('{date_fmt}', rc.rent_date) = :period
              AND date(rc.rent_date) BETWEEN date(:from_date) AND date(:to_date)
            GROUP BY volume_id
        ) combined
        JOIN volume v ON v.id = combined.volume_id
        JOIN title t ON t.id = v.title_id
        {f"WHERE t.id = :title_id" if title_id else ""}
        GROUP BY v.id, volume_name, v.isbn
        ORDER BY volume_name ASC;
    """

    params = {"from_date": from_iso, "to_date": to_iso, "period": period}
    if title_id:
        params["title_id"] = title_id

    result = await session.execute(text(query), params)
    rows = result.mappings().all()

    data = [
        FluctuationDetailItem(
            volume_id=row["volume_id"],
            volume_name=row["volume_name"],
            isbn=row["isbn"],
            stock_in=int(row["stock_in"] or 0),
            sale=int(row["sale"] or 0),
            rental=int(row["rental"] or 0)
        )
        for row in rows
    ]

    return success_response(FluctuationDetailPayload(data=data))
