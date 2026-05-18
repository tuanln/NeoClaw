"""Unit tests for OmniBase mecanum kinematics.

These tests drive the OmniBase against a stub ThingBot that records each
`dc()` call. The wheel speeds are computed by NeoClaw's mecanum math,
so we verify the 6 canonical motion patterns produce the expected
(M1, M2, M3, M4) sign pattern.

Reference convention (from omni_base.py docstring):
    Forward:     M1+ M2+ M3+ M4+
    Backward:    M1- M2- M3- M4-
    Strafe R:    M1+ M2- M3- M4+
    Strafe L:    M1- M2+ M3+ M4-
    Rotate CW:   M1+ M2- M3+ M4-
    Rotate CCW:  M1- M2+ M3- M4+
"""
from __future__ import annotations

from neoclaw.hardware.models import MotorID
from neoclaw.hardware.omni_base import OmniBase


class StubThingBot:
    """Records every `dc(motor, speed)` call. No real hardware."""

    def __init__(self):
        self.dc_calls: list[tuple[MotorID, int]] = []

    def dc(self, motor: MotorID, speed: int) -> None:
        self.dc_calls.append((motor, speed))

    def last_speeds(self) -> dict[MotorID, int]:
        """Return the most recent speed set per motor."""
        result: dict[MotorID, int] = {}
        for motor, speed in self.dc_calls:
            result[motor] = speed
        return result


# ── Direct methods ──


def test_forward_all_motors_positive():
    bot = StubThingBot()
    base = OmniBase(bot)
    base.forward(speed=60)
    speeds = bot.last_speeds()
    assert speeds[MotorID.M1] == 60
    assert speeds[MotorID.M2] == 60
    assert speeds[MotorID.M3] == 60
    assert speeds[MotorID.M4] == 60


def test_backward_all_motors_negative():
    bot = StubThingBot()
    base = OmniBase(bot)
    base.backward(speed=60)
    speeds = bot.last_speeds()
    assert speeds[MotorID.M1] == -60
    assert speeds[MotorID.M2] == -60
    assert speeds[MotorID.M3] == -60
    assert speeds[MotorID.M4] == -60


def test_strafe_right_pattern():
    """Strafe R: M1+ M2- M3- M4+"""
    bot = StubThingBot()
    base = OmniBase(bot)
    base.strafe_right(speed=60)
    speeds = bot.last_speeds()
    assert speeds[MotorID.M1] == 60
    assert speeds[MotorID.M2] == -60
    assert speeds[MotorID.M3] == -60
    assert speeds[MotorID.M4] == 60


def test_strafe_left_pattern():
    """Strafe L: M1- M2+ M3+ M4-"""
    bot = StubThingBot()
    base = OmniBase(bot)
    base.strafe_left(speed=60)
    speeds = bot.last_speeds()
    assert speeds[MotorID.M1] == -60
    assert speeds[MotorID.M2] == 60
    assert speeds[MotorID.M3] == 60
    assert speeds[MotorID.M4] == -60


def test_rotate_cw_pattern():
    """Rotate CW: M1+ M2- M3+ M4-"""
    bot = StubThingBot()
    base = OmniBase(bot)
    base.rotate_cw(speed=50)
    speeds = bot.last_speeds()
    assert speeds[MotorID.M1] == 50
    assert speeds[MotorID.M2] == -50
    assert speeds[MotorID.M3] == 50
    assert speeds[MotorID.M4] == -50


def test_rotate_ccw_pattern():
    """Rotate CCW: M1- M2+ M3- M4+"""
    bot = StubThingBot()
    base = OmniBase(bot)
    base.rotate_ccw(speed=50)
    speeds = bot.last_speeds()
    assert speeds[MotorID.M1] == -50
    assert speeds[MotorID.M2] == 50
    assert speeds[MotorID.M3] == -50
    assert speeds[MotorID.M4] == 50


# ── Diagonals ──


def test_diagonal_forward_right():
    """Diagonal FR (per omni_base.py): M1+ M2=0 M3=0 M4+"""
    bot = StubThingBot()
    base = OmniBase(bot)
    base.diagonal_forward_right(speed=60)
    speeds = bot.last_speeds()
    assert speeds[MotorID.M1] == 60
    assert speeds[MotorID.M2] == 0
    assert speeds[MotorID.M3] == 0
    assert speeds[MotorID.M4] == 60


def test_diagonal_forward_left():
    """Diagonal FL (per omni_base.py): M1=0 M2+ M3+ M4=0"""
    bot = StubThingBot()
    base = OmniBase(bot)
    base.diagonal_forward_left(speed=60)
    speeds = bot.last_speeds()
    assert speeds[MotorID.M1] == 0
    assert speeds[MotorID.M2] == 60
    assert speeds[MotorID.M3] == 60
    assert speeds[MotorID.M4] == 0


# ── Stop ──


def test_stop_zeros_all_wheels():
    bot = StubThingBot()
    base = OmniBase(bot)
    base.forward(speed=80)
    base.stop()
    speeds = bot.last_speeds()
    assert speeds[MotorID.M1] == 0
    assert speeds[MotorID.M2] == 0
    assert speeds[MotorID.M3] == 0
    assert speeds[MotorID.M4] == 0


def test_state_is_moving_after_forward():
    bot = StubThingBot()
    base = OmniBase(bot)
    base.forward(speed=60)
    assert base.state.is_moving()
    base.stop()
    assert not base.state.is_moving()


# ── Vector drive (inverse kinematics) ──


def test_drive_pure_forward_vector():
    """drive(vx=1, vy=0, omega=0) → forward pattern."""
    bot = StubThingBot()
    base = OmniBase(bot)
    base.drive(vx=1.0, vy=0.0, omega=0.0, speed=60)
    speeds = bot.last_speeds()
    # Pure forward: all wheels equal positive
    assert speeds[MotorID.M1] == speeds[MotorID.M2] == speeds[MotorID.M3] == speeds[MotorID.M4]
    assert speeds[MotorID.M1] > 0


def test_drive_clamps_to_speed_scale():
    """Inputs over speed scale are normalized so max magnitude ≤ speed."""
    bot = StubThingBot()
    base = OmniBase(bot)
    base.drive(vx=2.0, vy=0.0, omega=0.0, speed=50)  # vx > 1
    speeds = bot.last_speeds()
    max_mag = max(abs(s) for s in speeds.values())
    assert max_mag <= 50, f"Max wheel speed {max_mag} > scale 50"
