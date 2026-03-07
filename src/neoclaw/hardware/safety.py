"""Safety manager with limit switch enforcement and watchdog."""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from neoclaw.hardware.models import Axis, Direction
from neoclaw.hardware.motor_controller import DCMotorController
from neoclaw.hardware.sensor_manager import SensorManager

logger = logging.getLogger(__name__)

# Mapping: limit switch name → (axis, direction that should be blocked)
LIMIT_BLOCKS: dict[str, tuple[Axis, str]] = {
    "x_left": (Axis.X, "positive"),
    "y_forward": (Axis.Y, "positive"),
    "y_backward": (Axis.Y, "negative"),
    "z_up": (Axis.Z, "positive"),
    "z_down": (Axis.Z, "negative"),
}


class SafetyManager:
    """Enforces limit switches, watchdog timeout, and emergency stop."""

    def __init__(
        self,
        motors: dict[Axis, DCMotorController],
        sensors: SensorManager,
        watchdog_timeout: float = 30.0,
        max_motor_runtime: float = 60.0,
    ):
        self._motors = motors
        self._sensors = sensors
        self._watchdog_timeout = watchdog_timeout
        self._max_motor_runtime = max_motor_runtime
        self._last_activity: float = time.monotonic()
        self._watchdog_thread: Optional[threading.Thread] = None
        self._running = False
        self._emergency_stopped = False

    def start(self) -> None:
        """Start the safety watchdog."""
        self._running = True
        self._last_activity = time.monotonic()
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()
        logger.info("Safety manager started")

    def stop(self) -> None:
        """Stop the safety watchdog."""
        self._running = False
        if self._watchdog_thread is not None:
            self._watchdog_thread.join(timeout=2.0)

    def reset_watchdog(self) -> None:
        """Reset the watchdog timer (call on user activity)."""
        self._last_activity = time.monotonic()

    def check_limit(self, axis: Axis, direction: str) -> bool:
        """Check if movement is allowed (not blocked by limit switch).

        Returns True if movement is allowed, False if blocked.
        """
        for limit_name, (blocked_axis, blocked_dir) in LIMIT_BLOCKS.items():
            if blocked_axis == axis and blocked_dir == direction:
                if self._sensors.is_limit_triggered(limit_name):
                    logger.debug(f"Movement blocked: {axis.name} {direction} (limit {limit_name})")
                    return False
        return True

    def emergency_stop(self) -> None:
        """Immediately stop all motors."""
        logger.warning("EMERGENCY STOP activated")
        self._emergency_stopped = True
        for motor in self._motors.values():
            motor.stop_all()

    def clear_emergency(self) -> None:
        """Clear emergency stop state."""
        self._emergency_stopped = False
        logger.info("Emergency stop cleared")

    @property
    def is_emergency_stopped(self) -> bool:
        return self._emergency_stopped

    def _watchdog_loop(self) -> None:
        """Background thread: monitor for timeout and motor runtime."""
        while self._running:
            time.sleep(1.0)

            # Check watchdog timeout
            elapsed = time.monotonic() - self._last_activity
            if elapsed > self._watchdog_timeout:
                any_active = any(m.is_active for m in self._motors.values())
                if any_active:
                    logger.warning(
                        f"Watchdog timeout ({self._watchdog_timeout}s) — stopping all motors"
                    )
                    for motor in self._motors.values():
                        motor.stop_all()

            # Check max motor runtime
            for axis, motor in self._motors.items():
                pos_state, neg_state = motor.get_states()
                for state in (pos_state, neg_state):
                    if state.active and state.runtime_seconds > self._max_motor_runtime:
                        logger.warning(
                            f"Motor {axis.name} exceeded max runtime "
                            f"({self._max_motor_runtime}s) — stopping"
                        )
                        motor.stop_all()
