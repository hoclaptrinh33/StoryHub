from __future__ import annotations

import asyncio
from typing import Any

from app.services.event_publisher import EventPublisher


class DummyConnectionManager:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.broadcast_calls: list[dict[str, Any]] = []

    async def broadcast(
        self,
        *,
        event_name: str,
        payload: dict[str, Any],
        branch_id: str | None,
        allowed_roles: set[str] | None = None,
    ) -> int:
        if self.should_fail:
            raise RuntimeError("forced broadcast failure")

        self.broadcast_calls.append(
            {
                "event_name": event_name,
                "payload": payload,
                "branch_id": branch_id,
                "allowed_roles": allowed_roles,
            }
        )
        return 2


def test_item_status_throttling_keeps_last_payload_in_window() -> None:
    async def scenario() -> None:
        manager = DummyConnectionManager()
        publisher = EventPublisher(manager)

        await publisher.publish_item_status_changed(
            item_id="ITM-001",
            old_status="available",
            new_status="reserved",
            changed_at="2026-04-19T10:00:00Z",
            source_api="inventory_reserve_item_v1",
            changed_by="cashier-01",
            branch_id="main",
        )
        await publisher.publish_item_status_changed(
            item_id="ITM-001",
            old_status="reserved",
            new_status="rented",
            changed_at="2026-04-19T10:00:00Z",
            source_api="rental_create_contract_v1",
            changed_by="cashier-01",
            branch_id="main",
        )
        await publisher.publish_item_status_changed(
            item_id="ITM-001",
            old_status="rented",
            new_status="sold",
            changed_at="2026-04-19T10:00:01Z",
            source_api="pos_create_order_v1",
            changed_by="cashier-01",
            branch_id="main",
        )

        await asyncio.sleep(0.35)

        assert len(manager.broadcast_calls) == 2
        assert manager.broadcast_calls[0]["event_name"] == "item_status_changed"
        assert manager.broadcast_calls[1]["payload"]["new_status"] == "sold"

        await publisher.shutdown()

    asyncio.run(scenario())


def test_settlement_event_payload_contains_required_fields() -> None:
    async def scenario() -> None:
        manager = DummyConnectionManager()
        publisher = EventPublisher(manager)

        await publisher.publish_rental_settlement_finished(
            settlement_id="5001",
            contract_id="2001",
            total_fee=42000,
            refund_to_customer=8000,
            remaining_debt=0,
            settled_at="2026-04-19T10:05:00Z",
            branch_id="main",
        )

        assert len(manager.broadcast_calls) == 1
        payload = manager.broadcast_calls[0]["payload"]
        assert payload["settlement_id"] == "5001"
        assert payload["contract_id"] == "2001"
        assert payload["total_fee"] == 42000
        assert payload["refund_to_customer"] == 8000
        assert payload["remaining_debt"] == 0
        assert payload["settled_at"] == "2026-04-19T10:05:00Z"

        await publisher.shutdown()

    asyncio.run(scenario())


def test_broadcast_failures_are_handled_without_crashing() -> None:
    async def scenario() -> None:
        manager = DummyConnectionManager(should_fail=True)
        publisher = EventPublisher(manager)

        await publisher.publish_item_status_changed(
            item_id="ITM-001",
            old_status="available",
            new_status="reserved",
            changed_at="2026-04-19T10:00:00Z",
            source_api="inventory_reserve_item_v1",
            changed_by="cashier-01",
            branch_id="main",
        )

        await publisher.shutdown()

    asyncio.run(scenario())
