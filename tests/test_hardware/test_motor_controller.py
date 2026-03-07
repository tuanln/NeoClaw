"""Tests for motor controller."""
from neoclaw.hardware.models import Axis


def test_motor_run_positive(motors, sim_backend):
    motor = motors[Axis.X]
    motor.run_positive(speed=1.0)

    pos, neg = motor.get_states()
    assert pos.active is True
    assert neg.active is False
    assert motor.is_active is True


def test_motor_run_negative(motors, sim_backend):
    motor = motors[Axis.Y]
    motor.run_negative(speed=0.5)

    pos, neg = motor.get_states()
    assert pos.active is False
    assert neg.active is True


def test_motor_stop_all(motors, sim_backend):
    motor = motors[Axis.Z]
    motor.run_positive()
    motor.stop_all()

    pos, neg = motor.get_states()
    assert pos.active is False
    assert neg.active is False


def test_motor_direction_switch(motors, sim_backend):
    """Running positive should stop negative."""
    motor = motors[Axis.X]
    motor.run_negative()
    motor.run_positive()

    pos, neg = motor.get_states()
    assert pos.active is True
    assert neg.active is False


def test_speed_clamping(motors, sim_backend):
    motor = motors[Axis.X]
    motor.run_positive(speed=1.5)  # Should clamp to 1.0

    pos, _ = motor.get_states()
    assert pos.speed == 1.0

    motor.run_negative(speed=-0.5)  # Should clamp to 0.0
    _, neg = motor.get_states()
    assert neg.speed == 0.0
