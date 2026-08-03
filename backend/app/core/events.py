from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DomainEvent:
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: str | None = None
    event_type: str = ""
    data: dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[DomainEvent], Any]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def register(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug("Handler registered for event: %s", event_type)

    def unregister(self, event_type: str, handler: EventHandler) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h is not handler
            ]
            logger.debug("Handler unregistered for event: %s", event_type)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(event.event_type, [])
        logger.info(
            "Publishing event %s with %d handlers",
            event.event_type,
            len(handlers),
        )
        for handler in handlers:
            try:
                result = handler(event)
                if hasattr(result, "__await__"):
                    await result
            except Exception as exc:
                logger.error(
                    "Handler failed for event %s: %s",
                    event.event_type,
                    exc,
                )

    def clear(self) -> None:
        self._handlers.clear()


event_bus = EventBus()
