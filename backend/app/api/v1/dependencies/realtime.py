from __future__ import annotations

from fastapi import Request

from app.services.event_publisher import EventPublisher


def get_event_publisher(request: Request) -> EventPublisher:
    publisher = getattr(request.app.state, "event_publisher", None)
    if publisher is None:
        raise RuntimeError("Event publisher has not been initialized.")
    return publisher
