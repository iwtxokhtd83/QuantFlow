"""Event bus for decoupled communication between system components."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class EventType(Enum):
    BAR = auto()
    ORDER_SUBMITTED = auto()
    ORDER_FILLED = auto()
    ORDER_CANCELLED = auto()
    TRADE_OPENED = auto()
    TRADE_CLOSED = auto()
    RISK_BREACH = auto()
    ENGINE_START = auto()
    ENGINE_STOP = auto()


@dataclass
class Event:
    type: EventType
    data: Any = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EventBus:
    """Publish-subscribe event bus for system-wide communication."""

    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)

    def publish(self, event: Event) -> None:
        for handler in self._subscribers.get(event.type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error("Event handler error for %s: %s", event.type, e)
