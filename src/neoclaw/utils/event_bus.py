"""Pure-Python EventBus for decoupled component communication."""
from __future__ import annotations

import logging
import threading
from typing import Any, Callable

logger = logging.getLogger(__name__)


class EventBus:
    """Thread-safe pub/sub event bus.

    Usage:
        bus = EventBus.instance()
        bus.on("motor_started", lambda data: print(data))
        bus.emit("motor_started", {"axis": "X", "direction": "left"})
    """

    _instance: EventBus | None = None
    _lock = threading.Lock()

    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}
        self._listener_lock = threading.Lock()

    @classmethod
    def instance(cls) -> EventBus:
        """Get or create the singleton EventBus."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing)."""
        with cls._lock:
            cls._instance = None

    def on(self, event: str, callback: Callable) -> None:
        """Subscribe to an event."""
        with self._listener_lock:
            if event not in self._listeners:
                self._listeners[event] = []
            self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """Unsubscribe from an event."""
        with self._listener_lock:
            listeners = self._listeners.get(event, [])
            if callback in listeners:
                listeners.remove(callback)

    def emit(self, event: str, data: Any = None) -> None:
        """Emit an event to all subscribers."""
        with self._listener_lock:
            listeners = list(self._listeners.get(event, []))

        for callback in listeners:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"EventBus callback error for '{event}': {e}")

    def clear(self) -> None:
        """Remove all listeners."""
        with self._listener_lock:
            self._listeners.clear()

    @property
    def event_count(self) -> int:
        return len(self._listeners)
