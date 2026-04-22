from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from time import monotonic
from typing import Any
from uuid import uuid4

from app.services.realtime_metrics import RealtimeMetrics
from app.services.websocket_manager import WebSocketConnectionManager

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _ThrottleBucket:
    last_sent_at: float = 0.0
    pending_payload: dict[str, Any] | None = None
    pending_branch_id: str | None = None
    task: asyncio.Task[None] | None = None


class EventPublisher:
    def __init__(
        self,
        connection_manager: WebSocketConnectionManager,
        metrics: RealtimeMetrics | None = None,
    ) -> None:
        self._connection_manager = connection_manager
        self._metrics = metrics
        self._throttle_buckets: dict[str, _ThrottleBucket] = {}
        self._lock = asyncio.Lock()
        self._tasks: set[asyncio.Task[None]] = set()

    async def publish_item_status_changed(
        self,
        *,
        item_id: str,
        old_status: str,
        new_status: str,
        changed_at: str,
        source_api: str,
        changed_by: str,
        branch_id: str,
    ) -> None:
        payload = {
            "event_id": f"evt-{uuid4().hex}",
            "item_id": item_id,
            "old_status": old_status,
            "new_status": new_status,
            "changed_at": changed_at,
            "source_api": source_api,
            "changed_by": changed_by,
        }
        await self._publish_with_throttle(
            event_name="item_status_changed",
            event_key=item_id,
            payload=payload,
            branch_id=branch_id,
            throttle_seconds=0.3,
        )

    async def publish_rental_settlement_finished(
        self,
        *,
        settlement_id: str,
        contract_id: str,
        total_fee: int,
        refund_to_customer: int,
        remaining_debt: int,
        settled_at: str,
        branch_id: str,
    ) -> None:
        payload = {
            "event_id": f"evt-{uuid4().hex}",
            "settlement_id": settlement_id,
            "contract_id": contract_id,
            "total_fee": total_fee,
            "refund_to_customer": refund_to_customer,
            "remaining_debt": remaining_debt,
            "settled_at": settled_at,
        }
        await self._publish_with_throttle(
            event_name="rental_settlement_finished",
            event_key=settlement_id,
            payload=payload,
            branch_id=branch_id,
            throttle_seconds=0.2,
        )

    async def publish_volume_stock_updated(
        self,
        *,
        volume_id: int,
        new_stock: int,
        branch_id: str,
    ) -> None:
        payload = {
            "event_id": f"evt-{uuid4().hex}",
            "volume_id": volume_id,
            "new_stock": new_stock,
            "changed_at": datetime.now().isoformat() + "Z",
        }
        await self._publish_with_throttle(
            event_name="volume_stock_updated",
            event_key=str(volume_id),
            payload=payload,
            branch_id=branch_id,
            throttle_seconds=0.1,
        )

    async def publish_inventory_data_changed(
        self,
        *,
        reason: str,
        branch_id: str,
    ) -> None:
        payload = {
            "event_id": f"evt-{uuid4().hex}",
            "reason": reason,
            "changed_at": datetime.now().isoformat() + "Z",
        }
        await self._deliver_event(
            event_name="inventory_data_changed",
            payload=payload,
            branch_id=branch_id,
        )

    async def publish_item_mutated(
        self,
        *,
        item_id: str,
        action: str,
        branch_id: str,
    ) -> None:
        payload = {
            "event_id": f"evt-{uuid4().hex}",
            "item_id": item_id,
            "action": action,
            "changed_at": datetime.now().isoformat() + "Z",
        }
        await self._deliver_event(
            event_name="item_mutated",
            payload=payload,
            branch_id=branch_id,
        )

    async def _publish_with_throttle(
        self,
        *,
        event_name: str,
        event_key: str,
        payload: dict[str, Any],
        branch_id: str,
        throttle_seconds: float,
    ) -> None:
        bucket_key = f"{event_name}:{event_key}"
        should_send_now = False

        async with self._lock:
            bucket = self._throttle_buckets.setdefault(bucket_key, _ThrottleBucket())
            now = monotonic()
            elapsed = now - bucket.last_sent_at

            if elapsed >= throttle_seconds and bucket.task is None:
                bucket.last_sent_at = now
                should_send_now = True
            else:
                bucket.pending_payload = payload
                bucket.pending_branch_id = branch_id
                if bucket.task is None:
                    delay = max(throttle_seconds - elapsed, 0.0)
                    bucket.task = asyncio.create_task(
                        self._flush_bucket_after_delay(
                            bucket_key=bucket_key,
                            event_name=event_name,
                            delay_seconds=delay,
                        )
                    )
                    self._tasks.add(bucket.task)
                    bucket.task.add_done_callback(self._tasks.discard)

        if should_send_now:
            await self._deliver_event(
                event_name=event_name,
                payload=payload,
                branch_id=branch_id,
            )

    async def _flush_bucket_after_delay(
        self,
        *,
        bucket_key: str,
        event_name: str,
        delay_seconds: float,
    ) -> None:
        try:
            await asyncio.sleep(delay_seconds)

            payload: dict[str, Any] | None = None
            branch_id: str | None = None
            async with self._lock:
                bucket = self._throttle_buckets.get(bucket_key)
                if bucket is None:
                    return

                payload = bucket.pending_payload
                branch_id = bucket.pending_branch_id
                bucket.pending_payload = None
                bucket.pending_branch_id = None
                bucket.task = None
                bucket.last_sent_at = monotonic()

            if payload is None or branch_id is None:
                return

            await self._deliver_event(
                event_name=event_name,
                payload=payload,
                branch_id=branch_id,
            )
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("Unexpected error while flushing throttled event")

    async def _deliver_event(
        self,
        *,
        event_name: str,
        payload: dict[str, Any],
        branch_id: str,
    ) -> None:
        try:
            started = monotonic()
            sent_count = await self._connection_manager.broadcast(
                event_name=event_name,
                payload=payload,
                branch_id=branch_id,
                allowed_roles={"cashier", "manager", "owner"},
            )
            if self._metrics is not None:
                await self._metrics.record_event_published(
                    event_name,
                    latency_ms=(monotonic() - started) * 1000,
                )
            logger.debug(
                "Realtime event delivered",
                extra={
                    "event_name": event_name,
                    "event_id": payload.get("event_id"),
                    "sent_count": sent_count,
                    "branch_id": branch_id,
                },
            )
        except Exception:
            if self._metrics is not None:
                await self._metrics.record_broadcast_failure()
            logger.exception("Failed to deliver realtime event %s", event_name)

    async def shutdown(self) -> None:
        for task in list(self._tasks):
            task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()
