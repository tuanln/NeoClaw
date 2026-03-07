"""Telemetry collection from claw machine."""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from neoclaw.config.settings import get_settings
from neoclaw.hardware.claw_machine import ClawMachine
from neoclaw.iot.models import TelemetryPacket

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """Collects and publishes telemetry data from the claw machine."""

    def __init__(
        self,
        claw: ClawMachine,
        device_id: str = "default",
        on_telemetry: Optional[Callable[[TelemetryPacket], None]] = None,
    ):
        self._claw = claw
        self._device_id = device_id
        self._interval = get_settings().iot.telemetry_interval
        self._on_telemetry = on_telemetry
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        """Start collecting telemetry."""
        self._running = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
        logger.info(f"Telemetry collection started (interval={self._interval}s)")

    def stop(self) -> None:
        """Stop collecting telemetry."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)

    def collect_once(self) -> TelemetryPacket:
        """Collect a single telemetry packet."""
        state = self._claw.get_state()

        packet = TelemetryPacket(
            device_id=self._device_id,
            motor_states={k: v.active for k, v in state.motors.items()},
            sensor_readings={k: float(v) for k, v in state.limits.items()},
            magnet_active=state.magnet_active,
        )

        # Try to get system metrics
        try:
            import os
            load_avg = os.getloadavg()
            packet.cpu_percent = load_avg[0] * 100
        except (OSError, AttributeError):
            pass

        return packet

    def _collect_loop(self) -> None:
        """Background thread for periodic telemetry collection."""
        while self._running:
            try:
                packet = self.collect_once()
                if self._on_telemetry:
                    self._on_telemetry(packet)
            except Exception as e:
                logger.error(f"Telemetry collection error: {e}")

            time.sleep(self._interval)
