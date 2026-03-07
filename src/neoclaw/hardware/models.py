"""Hardware data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class Axis(Enum):
    X = auto()
    Y = auto()
    Z = auto()


class Direction(Enum):
    LEFT = auto()
    RIGHT = auto()
    FORWARD = auto()
    BACKWARD = auto()
    UP = auto()
    DOWN = auto()


class MotorMode(Enum):
    OFF = auto()
    ON = auto()
    PWM = auto()


@dataclass
class MotorState:
    """State of a single motor."""
    axis: Axis
    direction: Direction
    active: bool = False
    speed: float = 1.0  # 0.0 to 1.0
    mode: MotorMode = MotorMode.OFF
    runtime_seconds: float = 0.0


@dataclass
class SensorReading:
    """A sensor reading with timestamp."""
    name: str
    value: bool | float | int
    pin: int
    timestamp: float = 0.0


@dataclass
class ClawState:
    """Complete state of the claw machine."""
    # Motor states
    motors: dict[str, MotorState] = field(default_factory=dict)
    # Electromagnet
    magnet_active: bool = False
    # Limit switches (True = triggered/at limit)
    limits: dict[str, bool] = field(default_factory=dict)
    # Buttons (True = pressed)
    buttons: dict[str, bool] = field(default_factory=dict)
    # LED
    led_on: bool = False
    # Position estimate (based on limit switches)
    at_x_left: bool = False
    at_y_forward: bool = False
    at_y_backward: bool = False
    at_z_up: bool = False
    at_z_down: bool = False

    def any_motor_active(self) -> bool:
        return any(m.active for m in self.motors.values())

    def to_dict(self) -> dict:
        return {
            "magnet_active": self.magnet_active,
            "led_on": self.led_on,
            "motors": {k: {"active": v.active, "speed": v.speed} for k, v in self.motors.items()},
            "limits": dict(self.limits),
            "buttons": dict(self.buttons),
        }
