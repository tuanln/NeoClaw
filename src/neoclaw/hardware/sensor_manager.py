"""Sensor management for limit switches and extensible sensors."""
from __future__ import annotations

import logging
import time
from typing import Callable

from neoclaw.config.pin_maps import PinMap
from neoclaw.hardware.gpio_backend import IGPIOBackend
from neoclaw.hardware.models import SensorReading

logger = logging.getLogger(__name__)


class SensorManager:
    """Manages limit switches and other sensors."""

    def __init__(self, backend: IGPIOBackend, pin_map: PinMap):
        self._backend = backend
        self._pin_map = pin_map
        self._callbacks: list[Callable[[SensorReading], None]] = []

        # Limit switch mapping: name → pin
        self._limit_switches: dict[str, int] = {
            "x_left": pin_map.limit_x_left,
            "y_forward": pin_map.limit_y_forward,
            "y_backward": pin_map.limit_y_backward,
            "z_up": pin_map.limit_z_up,
            "z_down": pin_map.limit_z_down,
        }

        # Setup all limit switch pins
        for name, pin in self._limit_switches.items():
            backend.setup_input(pin, pull_up=True)
            backend.set_callback(pin, self._on_limit_change)

    def _on_limit_change(self, pin: int, value: bool) -> None:
        """Handle limit switch state change."""
        name = self._pin_to_name(pin)
        reading = SensorReading(
            name=f"limit_{name}",
            value=not value,  # Active LOW: pressed=True when pin is LOW
            pin=pin,
            timestamp=time.time(),
        )
        logger.debug(f"Limit switch {name} (pin {pin}): {'TRIGGERED' if reading.value else 'released'}")
        for callback in self._callbacks:
            callback(reading)

    def _pin_to_name(self, pin: int) -> str:
        for name, p in self._limit_switches.items():
            if p == pin:
                return name
        return f"pin_{pin}"

    def is_limit_triggered(self, name: str) -> bool:
        """Check if a limit switch is triggered. Active LOW."""
        pin = self._limit_switches.get(name)
        if pin is None:
            return False
        return not self._backend.read(pin)  # Active LOW

    def get_all_limits(self) -> dict[str, bool]:
        """Get all limit switch states."""
        return {name: self.is_limit_triggered(name) for name in self._limit_switches}

    def on_change(self, callback: Callable[[SensorReading], None]) -> None:
        """Register a callback for sensor changes."""
        self._callbacks.append(callback)

    def read_all(self) -> list[SensorReading]:
        """Read all sensors and return readings."""
        readings = []
        now = time.time()
        for name, pin in self._limit_switches.items():
            readings.append(SensorReading(
                name=f"limit_{name}",
                value=self.is_limit_triggered(name),
                pin=pin,
                timestamp=now,
            ))
        return readings
