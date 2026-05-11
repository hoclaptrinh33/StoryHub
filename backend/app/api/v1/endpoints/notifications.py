"""
Smart Notification Center — on-the-fly notifications endpoint.

Computes notifications from existing data (rental_contract, volume, customer,
reservation, item) without requiring any new database tables.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import AuthContext, get_auth_context
from app.api.v1.endpoints._common import to_iso_z, utc_now
from app.api.v1.schemas import success_response
from app.db.models import Customer, Item, RentalContract, RentalItem, Reservation, Title, Volume
from app.db.session import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_notification(
    *,
    ntype: str,
    severity: str,
    title: str,
    message: str,
    entity_type: str,
    entity_id: str,
    action_url: str,
    created_at: datetime | None = None,
) -> dict:
    now = utc_now()
    return {
        "id": f"{ntype}-{entity_type}-{entity_id}",
        "type": ntype,
        "severity": severity,
        "title": title,
        "message": message,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "created_at": to_iso_z(created_at or now),
        "action_url": action_url,
    }


def _days_overdue(due_date: datetime, now: datetime) -> int:
    """Return the number of full days overdue (0 if not overdue)."""
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=UTC)
    delta = now - due_date
    return max(0, delta.days)


def _hours_until(due_date: datetime, now: datetime) -> float:
    """Return hours until due_date (negative if already past)."""
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=UTC)
    delta = due_date - now
    return delta.total_seconds() / 3600


# ─── Notification Builders ────────────────────────────────────────────────────

async def _build_overdue_notifications(session: AsyncSession, now: datetime) -> list[dict]:
    """Contracts past their due date that are still active/overdue."""
    notifications: list[dict] = []

    stmt = (
        select(
            RentalContract.id,
            RentalContract.customer_id,
            RentalContract.due_date,
            RentalContract.status,
            Customer.name.label("customer_name"),
            Customer.phone.label("customer_phone"),
            func.count(RentalItem.id).label("open_items"),
        )
        .join(Customer, Customer.id == RentalContract.customer_id)
        .outerjoin(
            RentalItem,
            and_(
                RentalItem.contract_id == RentalContract.id,
                RentalItem.status == "rented",
            ),
        )
        .where(
            RentalContract.deleted_at.is_(None),
            RentalContract.status.in_(["active", "overdue"]),
            RentalContract.due_date < now,
        )
        .group_by(RentalContract.id, Customer.id)
        .order_by(RentalContract.due_date.asc())
        .limit(50)
    )

    rows = (await session.execute(stmt)).all()

    for row in rows:
        days = _days_overdue(row.due_date, now)
        notifications.append(
            _make_notification(
                ntype="overdue",
                severity="critical",
                title=f"Hợp đồng #{row.id} quá hạn {days} ngày",
                message=f"Khách {row.customer_name} ({row.customer_phone}) — {row.open_items} cuốn chưa trả",
                entity_type="rental_contract",
                entity_id=str(row.id),
                action_url="/hoan-tra",
                created_at=row.due_date,
            )
        )

    return notifications


async def _build_due_soon_notifications(session: AsyncSession, now: datetime) -> list[dict]:
    """Active contracts due within the next 48 hours."""
    notifications: list[dict] = []
    deadline = now + timedelta(hours=48)

    stmt = (
        select(
            RentalContract.id,
            RentalContract.due_date,
            Customer.name.label("customer_name"),
            Customer.phone.label("customer_phone"),
            func.count(RentalItem.id).label("open_items"),
        )
        .join(Customer, Customer.id == RentalContract.customer_id)
        .outerjoin(
            RentalItem,
            and_(
                RentalItem.contract_id == RentalContract.id,
                RentalItem.status == "rented",
            ),
        )
        .where(
            RentalContract.deleted_at.is_(None),
            RentalContract.status == "active",
            RentalContract.due_date >= now,
            RentalContract.due_date <= deadline,
        )
        .group_by(RentalContract.id, Customer.id)
        .order_by(RentalContract.due_date.asc())
        .limit(50)
    )

    rows = (await session.execute(stmt)).all()

    for row in rows:
        hours = _hours_until(row.due_date, now)
        if hours <= 24:
            time_text = f"còn {int(hours)} giờ"
        else:
            time_text = f"còn {int(hours / 24)} ngày"

        notifications.append(
            _make_notification(
                ntype="due_soon",
                severity="warning",
                title=f"Hợp đồng #{row.id} sắp đến hạn ({time_text})",
                message=f"Khách {row.customer_name} — {row.open_items} cuốn đang thuê",
                entity_type="rental_contract",
                entity_id=str(row.id),
                action_url="/hoan-tra",
                created_at=row.due_date,
            )
        )

    return notifications


async def _build_low_stock_notifications(session: AsyncSession) -> list[dict]:
    """Volumes with retail stock critically low (1-2) or completely out (0)."""
    notifications: list[dict] = []

    stmt = (
        select(
            Volume.id,
            Volume.volume_number,
            Volume.retail_stock,
            Volume.isbn,
            Title.name.label("title_name"),
        )
        .join(Title, Title.id == Volume.title_id)
        .where(
            Volume.deleted_at.is_(None),
            Title.deleted_at.is_(None),
            Volume.retail_stock <= 2,
        )
        .order_by(Volume.retail_stock.asc(), Title.name.asc())
        .limit(50)
    )

    rows = (await session.execute(stmt)).all()

    for row in rows:
        vol_label = f"T{row.volume_number}" if row.volume_number else ""
        if row.retail_stock == 0:
            notifications.append(
                _make_notification(
                    ntype="out_of_stock",
                    severity="critical",
                    title=f"Hết hàng: {row.title_name} {vol_label}",
                    message=f"ISBN: {row.isbn or 'N/A'} — Tồn kho bán lẻ = 0",
                    entity_type="volume",
                    entity_id=str(row.id),
                    action_url="/kho",
                )
            )
        else:
            notifications.append(
                _make_notification(
                    ntype="low_stock",
                    severity="warning",
                    title=f"Sắp hết: {row.title_name} {vol_label}",
                    message=f"Chỉ còn {row.retail_stock} cuốn bán lẻ trong kho",
                    entity_type="volume",
                    entity_id=str(row.id),
                    action_url="/kho",
                )
            )

    return notifications


async def _build_customer_debt_notifications(session: AsyncSession) -> list[dict]:
    """Customers who currently have outstanding debt."""
    notifications: list[dict] = []

    stmt = (
        select(
            Customer.id,
            Customer.name,
            Customer.phone,
            Customer.debt,
        )
        .where(
            Customer.deleted_at.is_(None),
            Customer.debt > 0,
        )
        .order_by(Customer.debt.desc())
        .limit(30)
    )

    rows = (await session.execute(stmt)).all()

    for row in rows:
        formatted_debt = f"{row.debt:,}".replace(",", ".")
        notifications.append(
            _make_notification(
                ntype="customer_debt",
                severity="info",
                title=f"Công nợ: {row.name}",
                message=f"SĐT: {row.phone} — Nợ: {formatted_debt}₫",
                entity_type="customer",
                entity_id=str(row.id),
                action_url="/ban-hang",
            )
        )

    return notifications


async def _build_reservation_ready_notifications(session: AsyncSession) -> list[dict]:
    """Active reservations where the item is now available."""
    notifications: list[dict] = []

    stmt = (
        select(
            Reservation.id,
            Reservation.item_id,
            Reservation.customer_id,
            Reservation.reserved_at,
            Customer.name.label("customer_name"),
            Customer.phone.label("customer_phone"),
            Item.status.label("item_status"),
            Title.name.label("title_name"),
        )
        .join(Customer, Customer.id == Reservation.customer_id)
        .join(Item, Item.id == Reservation.item_id)
        .join(Volume, Volume.id == Item.volume_id)
        .join(Title, Title.id == Volume.title_id)
        .where(
            Reservation.status == "active",
            Item.status == "available",
        )
        .order_by(Reservation.reserved_at.asc())
        .limit(30)
    )

    rows = (await session.execute(stmt)).all()

    for row in rows:
        notifications.append(
            _make_notification(
                ntype="reservation_ready",
                severity="action",
                title=f"Đặt trước sẵn sàng: {row.title_name}",
                message=f"Khách {row.customer_name} ({row.customer_phone}) — Mã sách: {row.item_id}",
                entity_type="reservation",
                entity_id=str(row.id),
                action_url="/ban-hang?mode=rental",
                created_at=row.reserved_at,
            )
        )

    return notifications


# ─── Main Endpoint ────────────────────────────────────────────────────────────

@router.get("")
async def get_notifications(
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Fetch all active notifications computed on-the-fly from existing data.
    No new database table required.
    """
    now = utc_now()

    # Build all notification types concurrently-ish (sequential for SQLite safety)
    all_notifications: list[dict] = []

    overdue = await _build_overdue_notifications(session, now)
    all_notifications.extend(overdue)

    due_soon = await _build_due_soon_notifications(session, now)
    all_notifications.extend(due_soon)

    low_stock = await _build_low_stock_notifications(session)
    all_notifications.extend(low_stock)

    debts = await _build_customer_debt_notifications(session)
    all_notifications.extend(debts)

    reservations = await _build_reservation_ready_notifications(session)
    all_notifications.extend(reservations)

    # Build summary
    severity_counts = {"critical": 0, "warning": 0, "info": 0, "action": 0}
    for n in all_notifications:
        sev = n.get("severity", "info")
        if sev in severity_counts:
            severity_counts[sev] += 1

    # Sort: critical first, then warning, action, info
    severity_order = {"critical": 0, "warning": 1, "action": 2, "info": 3}
    all_notifications.sort(key=lambda n: severity_order.get(n.get("severity", "info"), 99))

    return success_response({
        "notifications": all_notifications,
        "summary": {
            "total": len(all_notifications),
            **severity_counts,
        },
    })
