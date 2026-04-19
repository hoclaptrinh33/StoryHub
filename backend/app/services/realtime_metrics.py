from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from datetime import UTC, datetime


class RealtimeMetrics:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._active_connections = 0
        self._connection_rejections_total = 0
        self._events_published_total: defaultdict[str, int] = defaultdict(int)
        self._broadcast_failures_total = 0
        self._latency_samples_ms: deque[float] = deque(maxlen=5000)

    async def set_active_connections(self, value: int) -> None:
        async with self._lock:
            self._active_connections = max(0, value)

    async def increment_connection_rejections(self, count: int = 1) -> None:
        async with self._lock:
            self._connection_rejections_total += max(0, count)

    async def record_event_published(self, event_name: str, latency_ms: float) -> None:
        async with self._lock:
            self._events_published_total[event_name] += 1
            self._latency_samples_ms.append(max(0.0, latency_ms))

    async def record_broadcast_failure(self, count: int = 1) -> None:
        async with self._lock:
            self._broadcast_failures_total += max(0, count)

    async def snapshot(self) -> dict[str, object]:
        async with self._lock:
            samples = sorted(self._latency_samples_ms)
            return {
                "ws_connections_active": self._active_connections,
                "ws_connection_rejections_total": self._connection_rejections_total,
                "ws_events_published_total": dict(self._events_published_total),
                "ws_event_latency_ms": {
                    "count": len(samples),
                    "p50": _percentile(samples, 50),
                    "p95": _percentile(samples, 95),
                    "p99": _percentile(samples, 99),
                    "max": samples[-1] if samples else 0.0,
                },
                "ws_broadcast_failures_total": self._broadcast_failures_total,
                "generated_at": datetime.now(UTC)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
            }


def _percentile(samples: list[float], p: int) -> float:
    if not samples:
        return 0.0

    ratio = max(0.0, min(1.0, p / 100))
    index = int(round((len(samples) - 1) * ratio))
    return samples[index]
