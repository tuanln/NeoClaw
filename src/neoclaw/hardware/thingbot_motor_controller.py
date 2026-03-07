"""ThingBot DC motor controller using motor_number + signed speed API.

ThingBot boards expose DC motors as numbered channels (1–4) controlled by
a single signed speed value:
    +255 = full forward,  0 = stop,  -255 = full reverse

This is fundamentally different from the GpiozeroBackend model which uses
two direction pins (pin_positive, pin_negative) + optional PWM enable pin.

This module provides ThingBotMotorController, a drop-in replacement for
DCMotorController when using a TelemetrixBackend, with the same interface
(run_positive, run_negative, stop_all, get_states) so the rest of NeoClaw
(SafetyManager, ClawMachine) works without modification.

Motor channel mapping:
    Axis.X → motor channel 1   (LEFT = +speed, RIGHT = -speed)
    Axis.Y → motor channel 2   (FORWARD = +speed, BACKWARD = -speed)
    Axis.Z → motor channel 3   (UP = +speed, DOWN = -speed)
    Motor channel 4 is reserved for optional 4th axis or auxiliary use.
"""
from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Optional

from neoclaw.hardware.models import Axis, Direction, MotorMode, MotorState

if TYPE_CHECKING:
    from neoclaw.hardware.telemetrix_backend import TelemetrixBackend

logger = logging.getLogger(__name__)

# Default motor channel assignment per axis
AXIS_TO_MOTOR_CHANNEL: dict[Axis, int] = {
    Axis.X: 1,
    Axis.Y: 2,
    Axis.Z: 3,
}

_DIR_POSITIVE: dict[Axis, Direction] = {
    Axis.X: Direction.LEFT,
    Axis.Y: Direction.FORWARD,
    Axis.Z: Direction.UP,
}

_DIR_NEGATIVE: dict[Axis, Direction] = {
    Axis.X: Direction.RIGHT,
    Axis.Y: Direction.BACKWARD,
    Axis.Z: Direction.DOWN,
}


class ThingBotMotorController:
    """Controls one claw axis via a ThingBot DC motor channel.

    Replaces DCMotorController for ThingBot boards. Uses
    thingbot().control_dc(motor_number, speed) where speed ∈ [-255, +255].

    Positive speed drives the motor in the positive direction of the axis
    (LEFT for X, FORWARD for Y, UP for Z). Negative speed drives reverse.

    Example:
        ctrl = ThingBotMotorController(backend, Axis.X, motor_channel=1)
        ctrl.run_positive(speed=0.7)   # move left at 70%
        ctrl.stop_all()
    """

    def __init__(
        self,
        backend: TelemetrixBackend,
        axis: Axis,
        motor_channel: int,
    ):
        """
        :param backend: TelemetrixBackend instance (provides .telemetrix access).
        :param axis: Which claw axis this controller manages (X, Y, or Z).
        :param motor_channel: ThingBot motor number (1–4).
        """
        self._backend = backend
        self._axis = axis
        self._channel = motor_channel

        self._state_pos = MotorState(axis=axis, direction=_DIR_POSITIVE[axis])
        self._state_neg = MotorState(axis=axis, direction=_DIR_NEGATIVE[axis])
        self._start_time: Optional[float] = None

    # ── Internal ──

    def _send_speed(self, speed: int) -> None:
        """Send signed speed (-255 to +255) to ThingBot motor channel."""
        self._backend.telemetrix.thingbot().control_dc(self._channel, speed)

    def _update_runtime(self) -> None:
        if self._start_time is not None:
            elapsed = time.monotonic() - self._start_time
            self._state_pos.runtime_seconds += elapsed
            self._state_neg.runtime_seconds += elapsed
            self._start_time = None

    # ── Public motor interface (mirrors DCMotorController) ──

    def run_positive(self, speed: float = 1.0) -> None:
        """Run motor in positive direction (left / forward / up).

        :param speed: 0.0 (stop) to 1.0 (full speed). Mapped to 0–255.
        """
        self.stop_negative()
        speed = max(0.0, min(1.0, speed))
        raw = int(speed * 255)
        self._send_speed(raw)

        self._state_pos.active = True
        self._state_pos.speed = speed
        self._state_pos.mode = MotorMode.PWM if speed < 1.0 else MotorMode.ON
        self._start_time = time.monotonic()
        logger.debug(
            f"ThingBot ch{self._channel} ({self._axis.name}+) speed={raw}"
        )

    def run_negative(self, speed: float = 1.0) -> None:
        """Run motor in negative direction (right / backward / down).

        :param speed: 0.0 (stop) to 1.0 (full speed). Mapped to 0 to -255.
        """
        self.stop_positive()
        speed = max(0.0, min(1.0, speed))
        raw = -int(speed * 255)
        self._send_speed(raw)

        self._state_neg.active = True
        self._state_neg.speed = speed
        self._state_neg.mode = MotorMode.PWM if speed < 1.0 else MotorMode.ON
        self._start_time = time.monotonic()
        logger.debug(
            f"ThingBot ch{self._channel} ({self._axis.name}-) speed={raw}"
        )

    def stop_positive(self) -> None:
        """Stop positive-direction movement."""
        if self._state_pos.active:
            self._send_speed(0)
            self._state_pos.active = False
            self._state_pos.mode = MotorMode.OFF
            self._update_runtime()

    def stop_negative(self) -> None:
        """Stop negative-direction movement."""
        if self._state_neg.active:
            self._send_speed(0)
            self._state_neg.active = False
            self._state_neg.mode = MotorMode.OFF
            self._update_runtime()

    def stop_all(self) -> None:
        """Emergency stop — immediately send speed=0 regardless of state."""
        self._send_speed(0)
        self._state_pos.active = False
        self._state_neg.active = False
        self._state_pos.mode = MotorMode.OFF
        self._state_neg.mode = MotorMode.OFF
        self._update_runtime()

    @property
    def is_active(self) -> bool:
        return self._state_pos.active or self._state_neg.active

    def get_states(self) -> tuple[MotorState, MotorState]:
        """Return (positive_state, negative_state) — same interface as DCMotorController."""
        return self._state_pos, self._state_neg


def create_thingbot_motor_controllers(
    backend: TelemetrixBackend,
    axis_channel_map: dict[Axis, int] | None = None,
) -> dict[Axis, ThingBotMotorController]:
    """Create ThingBot motor controllers for all three claw axes.

    :param backend: TelemetrixBackend with active Telemetrix connection.
    :param axis_channel_map: Optional override of default axis→channel mapping.
                             Defaults to {X:1, Y:2, Z:3}.
    :returns: Dict mapping Axis → ThingBotMotorController.
    """
    mapping = axis_channel_map or AXIS_TO_MOTOR_CHANNEL
    return {
        axis: ThingBotMotorController(backend, axis, channel)
        for axis, channel in mapping.items()
    }
