"""Input debounce utility."""
from __future__ import annotations

import threading
from typing import Callable, Optional


class Debouncer:
    """Debounce rapid input signals (e.g., button presses).

    Usage:
        debouncer = Debouncer(delay_ms=50)
        debouncer.call(my_function, arg1, arg2)
        # my_function is called only if no new call within 50ms
    """

    def __init__(self, delay_ms: int = 50):
        self._delay = delay_ms / 1000.0
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> None:
        """Schedule a debounced function call."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._delay, func, args, kwargs)
            self._timer.start()

    def cancel(self) -> None:
        """Cancel any pending call."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None


class InputDebouncer:
    """Per-pin debouncer for multiple button inputs."""

    def __init__(self, delay_ms: int = 50):
        self._delay_ms = delay_ms
        self._debouncers: dict[int, Debouncer] = {}
        self._last_values: dict[int, bool] = {}

    def process(self, pin: int, value: bool, callback: Callable[[int, bool], None]) -> None:
        """Process a pin change with debouncing."""
        if pin not in self._debouncers:
            self._debouncers[pin] = Debouncer(self._delay_ms)

        def _debounced():
            old_value = self._last_values.get(pin)
            if old_value != value:
                self._last_values[pin] = value
                callback(pin, value)

        self._debouncers[pin].call(_debounced)

    def cleanup(self) -> None:
        """Cancel all pending debounce timers."""
        for debouncer in self._debouncers.values():
            debouncer.cancel()
        self._debouncers.clear()
