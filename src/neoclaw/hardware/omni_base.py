"""4-wheel omnidirectional mobile base using ThingBot DC motors.

Wheel layout (top view, mecanum rollers):

       FRONT
    M1 ╲   ╱ M2
    (FL)     (FR)
         ●
    M3 ╱   ╲ M4
    (RL)     (RR)
       REAR

Mecanum kinematics:
    Forward:     M1+ M2+ M3+ M4+
    Backward:    M1- M2- M3- M4-
    Strafe R:    M1+ M2- M3- M4+
    Strafe L:    M1- M2+ M3+ M4-
    Rotate CW:   M1+ M2- M3+ M4-
    Rotate CCW:  M1- M2+ M3- M4+
    Diagonal FR: M1+ M2= M3= M4+
    Diagonal FL: M1= M2+ M3+ M4=
"""
from __future__ import annotations

import logging
import time

from neoclaw.hardware.models import (
    OmniBaseState,
    WheelPosition,
    WHEEL_MOTOR_MAP,
)
from neoclaw.hardware.thingbot import ThingBot

logger = logging.getLogger(__name__)


class OmniBase:
    """4-wheel omnidirectional mobile base.

    Controls ThingBot M1-M4 with mecanum/omni wheel kinematics.
    Supports movement in any direction + rotation.

    Usage:
        bot = ThingBot.connect()
        base = OmniBase(bot)
        base.forward(speed=60, duration=1.0)
        base.strafe_right(speed=50, duration=0.5)
        base.rotate(speed=40, duration=0.3)
        base.stop()
    """

    def __init__(self, thingbot: ThingBot):
        self._bot = thingbot
        self._state = OmniBaseState()

    @property
    def state(self) -> OmniBaseState:
        return self._state

    # ── Basic movements ──

    def forward(self, speed: int = 60, duration: float | None = None) -> None:
        """Move forward. All wheels same direction."""
        self._drive(speed, speed, speed, speed, duration)

    def backward(self, speed: int = 60, duration: float | None = None) -> None:
        """Move backward."""
        self._drive(-speed, -speed, -speed, -speed, duration)

    def strafe_left(self, speed: int = 60, duration: float | None = None) -> None:
        """Strafe left (sideways movement)."""
        self._drive(-speed, speed, speed, -speed, duration)

    def strafe_right(self, speed: int = 60, duration: float | None = None) -> None:
        """Strafe right (sideways movement)."""
        self._drive(speed, -speed, -speed, speed, duration)

    def rotate_cw(self, speed: int = 50, duration: float | None = None) -> None:
        """Rotate clockwise (turn right)."""
        self._drive(speed, -speed, speed, -speed, duration)

    def rotate_ccw(self, speed: int = 50, duration: float | None = None) -> None:
        """Rotate counter-clockwise (turn left)."""
        self._drive(-speed, speed, -speed, speed, duration)

    # ── Diagonal movements ──

    def diagonal_forward_right(self, speed: int = 60, duration: float | None = None) -> None:
        """Move diagonally forward-right."""
        self._drive(speed, 0, 0, speed, duration)

    def diagonal_forward_left(self, speed: int = 60, duration: float | None = None) -> None:
        """Move diagonally forward-left."""
        self._drive(0, speed, speed, 0, duration)

    def diagonal_backward_right(self, speed: int = 60, duration: float | None = None) -> None:
        """Move diagonally backward-right."""
        self._drive(0, -speed, -speed, 0, duration)

    def diagonal_backward_left(self, speed: int = 60, duration: float | None = None) -> None:
        """Move diagonally backward-left."""
        self._drive(-speed, 0, 0, -speed, duration)

    # ── Advanced: vector drive ──

    def drive(self, vx: float, vy: float, omega: float = 0, speed: int = 60) -> None:
        """Drive with arbitrary velocity vector.

        Args:
            vx: Forward/backward component (-1.0 to 1.0)
            vy: Left/right strafe component (-1.0 to 1.0)
            omega: Rotation component (-1.0 to 1.0, positive = CW)
            speed: Max speed scale (0-100)
        """
        # Mecanum inverse kinematics
        fl = vx + vy + omega   # M1 front-left
        fr = vx - vy - omega   # M2 front-right
        rl = vx - vy + omega   # M3 rear-left
        rr = vx + vy - omega   # M4 rear-right

        # Normalize to max speed
        max_val = max(abs(fl), abs(fr), abs(rl), abs(rr), 1.0)
        scale = speed / max_val

        self._set_wheels(
            int(fl * scale),
            int(fr * scale),
            int(rl * scale),
            int(rr * scale),
        )

    # ── Stop ──

    def stop(self) -> None:
        """Stop all wheels immediately."""
        self._set_wheels(0, 0, 0, 0)

    # ── Internal ──

    def _drive(
        self, fl: int, fr: int, rl: int, rr: int,
        duration: float | None = None,
    ) -> None:
        """Set wheel speeds with optional timed movement."""
        self._set_wheels(fl, fr, rl, rr)
        if duration is not None:
            time.sleep(duration)
            self.stop()

    def _set_wheels(self, fl: int, fr: int, rl: int, rr: int) -> None:
        """Set individual wheel speeds."""
        speeds = {
            WheelPosition.FRONT_LEFT: fl,
            WheelPosition.FRONT_RIGHT: fr,
            WheelPosition.REAR_LEFT: rl,
            WheelPosition.REAR_RIGHT: rr,
        }

        for wheel, speed in speeds.items():
            motor = WHEEL_MOTOR_MAP[wheel]
            self._bot.dc(motor, speed)
            self._state.wheel_speeds[wheel] = speed

    def get_wheel_speeds(self) -> dict[str, int]:
        """Get current wheel speeds as a simple dict."""
        return {w.name: s for w, s in self._state.wheel_speeds.items()}
