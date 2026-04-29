"""Small in-memory debug event store for MVP diagnostics."""

from __future__ import annotations

from collections import deque
from datetime import datetime


MAX_EVENTS = 200
_events: deque[dict] = deque(maxlen=MAX_EVENTS)


def add_event(kind: str, message: str, **details) -> dict:
    event = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "kind": kind,
        "message": message,
        "details": details,
    }
    _events.append(event)
    return event


def list_events() -> list[dict]:
    return list(_events)


def clear_events() -> None:
    _events.clear()
