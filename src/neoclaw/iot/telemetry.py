"""Telemetry collection from the ClawBot robot."""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from neoclaw.config.settings import get_settings
from neoclaw.hardware.claw_robot import ClawRobot
from neoclaw.iot.models import TelemetryPacket

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """Collects and publishes telemetry data from a ClawRobot."""

    def __init__(
        self,
        robot: ClawRobot,
        device_id: str = "default",
        on_telemetry: Optional[Callable[[TelemetryPacket], None]] = None,
    ):
        self._robot = robot
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
        state = self._robot.get_state().to_dict()

        # A wheel counts as active when it is turning, in either direction.
        motor_states = {
            wheel: speed != 0 for wheel, speed in state["base"]["wheels"].items()
        }
        # Joint angles ride along as sensor readings — a dashboard plots them
        # the same way it plots anything else numeric.
        sensor_readings = {
            f"arm_{joint.lower()}": float(angle)
            for joint, angle in state["arm"]["joints"].items()
        }
        sensor_readings["heading"] = float(state["base"]["heading"])

        packet = TelemetryPacket(
            device_id=self._device_id,
            motor_states=motor_states,
            sensor_readings=sensor_readings,
            gripper_holding=bool(state["arm"]["gripper_holding"]),
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
