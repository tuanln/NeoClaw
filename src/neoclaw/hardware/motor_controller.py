"""DC motor controller with PWM speed support."""
from __future__ import annotations

import logging
import time
from typing import Optional

from neoclaw.config.pin_maps import PinMap
from neoclaw.hardware.gpio_backend import IGPIOBackend
from neoclaw.hardware.models import Axis, Direction, MotorMode, MotorState

logger = logging.getLogger(__name__)


class DCMotorController:
    """Controls a pair of DC motors for one axis (two directions)."""

    def __init__(
        self,
        backend: IGPIOBackend,
        axis: Axis,
        pin_positive: int,
        pin_negative: int,
        pwm_pin_positive: int = -1,
        pwm_pin_negative: int = -1,
        pwm_frequency: int = 1000,
    ):
        self._backend = backend
        self._axis = axis
        self._pin_pos = pin_positive
        self._pin_neg = pin_negative
        self._pwm_pin_pos = pwm_pin_positive
        self._pwm_pin_neg = pwm_pin_negative
        self._pwm_freq = pwm_frequency
        self._has_pwm = pwm_pin_positive >= 0 and pwm_pin_negative >= 0

        # State
        self._state_pos = MotorState(axis=axis, direction=self._dir_positive())
        self._state_neg = MotorState(axis=axis, direction=self._dir_negative())
        self._start_time: Optional[float] = None

        # Setup pins
        backend.setup_output(pin_positive)
        backend.setup_output(pin_negative)

    def _dir_positive(self) -> Direction:
        return {Axis.X: Direction.LEFT, Axis.Y: Direction.FORWARD, Axis.Z: Direction.UP}[self._axis]

    def _dir_negative(self) -> Direction:
        return {Axis.X: Direction.RIGHT, Axis.Y: Direction.BACKWARD, Axis.Z: Direction.DOWN}[self._axis]

    def run_positive(self, speed: float = 1.0) -> None:
        """Run motor in positive direction."""
        self.stop_negative()
        speed = max(0.0, min(1.0, speed))

        if self._has_pwm and speed < 1.0:
            self._backend.pwm_start(self._pwm_pin_pos, self._pwm_freq, speed)
            self._state_pos.mode = MotorMode.PWM
        else:
            self._backend.write(self._pin_pos, True)
            self._state_pos.mode = MotorMode.ON

        self._state_pos.active = True
        self._state_pos.speed = speed
        self._start_time = time.monotonic()
        logger.debug(f"Motor {self._axis.name} positive ON (speed={speed:.2f})")

    def run_negative(self, speed: float = 1.0) -> None:
        """Run motor in negative direction."""
        self.stop_positive()
        speed = max(0.0, min(1.0, speed))

        if self._has_pwm and speed < 1.0:
            self._backend.pwm_start(self._pwm_pin_neg, self._pwm_freq, speed)
            self._state_neg.mode = MotorMode.PWM
        else:
            self._backend.write(self._pin_neg, True)
            self._state_neg.mode = MotorMode.ON

        self._state_neg.active = True
        self._state_neg.speed = speed
        self._start_time = time.monotonic()
        logger.debug(f"Motor {self._axis.name} negative ON (speed={speed:.2f})")

    def stop_positive(self) -> None:
        """Stop positive direction motor."""
        if self._state_pos.active:
            self._backend.write(self._pin_pos, False)
            if self._has_pwm:
                self._backend.pwm_stop(self._pwm_pin_pos)
            self._state_pos.active = False
            self._state_pos.mode = MotorMode.OFF
            self._update_runtime()

    def stop_negative(self) -> None:
        """Stop negative direction motor."""
        if self._state_neg.active:
            self._backend.write(self._pin_neg, False)
            if self._has_pwm:
                self._backend.pwm_stop(self._pwm_pin_neg)
            self._state_neg.active = False
            self._state_neg.mode = MotorMode.OFF
            self._update_runtime()

    def stop_all(self) -> None:
        """Emergency stop both directions."""
        self._backend.write(self._pin_pos, False)
        self._backend.write(self._pin_neg, False)
        if self._has_pwm:
            self._backend.pwm_stop(self._pwm_pin_pos)
            self._backend.pwm_stop(self._pwm_pin_neg)
        self._state_pos.active = False
        self._state_neg.active = False
        self._state_pos.mode = MotorMode.OFF
        self._state_neg.mode = MotorMode.OFF
        self._update_runtime()

    def _update_runtime(self) -> None:
        if self._start_time is not None:
            elapsed = time.monotonic() - self._start_time
            self._state_pos.runtime_seconds += elapsed
            self._state_neg.runtime_seconds += elapsed
            self._start_time = None

    @property
    def is_active(self) -> bool:
        return self._state_pos.active or self._state_neg.active

    def get_states(self) -> tuple[MotorState, MotorState]:
        return self._state_pos, self._state_neg


def create_motor_controllers(
    backend: IGPIOBackend, pin_map: PinMap, pwm_frequency: int = 1000
) -> dict[Axis, DCMotorController]:
    """Create motor controllers for all 3 axes from a pin map."""
    return {
        Axis.X: DCMotorController(
            backend, Axis.X,
            pin_map.motor_x_left, pin_map.motor_x_right,
            pin_map.pwm_x_left, pin_map.pwm_x_right, pwm_frequency,
        ),
        Axis.Y: DCMotorController(
            backend, Axis.Y,
            pin_map.motor_y_forward, pin_map.motor_y_backward,
            pin_map.pwm_y_forward, pin_map.pwm_y_backward, pwm_frequency,
        ),
        Axis.Z: DCMotorController(
            backend, Axis.Z,
            pin_map.motor_z_up, pin_map.motor_z_down,
            pin_map.pwm_z_up, pin_map.pwm_z_down, pwm_frequency,
        ),
    }
