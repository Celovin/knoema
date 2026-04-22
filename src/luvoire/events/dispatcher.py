"""Synchronous event dispatcher."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from knoema.types import WorldEvent

EventHandler = Callable[[WorldEvent], None]


class EventDispatcher:
    """Route world events to registered handlers by event type."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if not event_type.strip():
            raise ValueError("event_type must not be blank")
        self._handlers[event_type].append(handler)

    def dispatch(self, event: WorldEvent) -> int:
        handlers = [*self._handlers.get("*", []), *self._handlers.get(event.event_type, [])]
        for handler in handlers:
            handler(event)
        return len(handlers)


__all__ = ["EventDispatcher", "EventHandler"]
