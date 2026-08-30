"""Telemetry reports the robot that exists.

The collector used to read ClawMachine's gantry fields — motors/limits/magnet.
ClawBot has wheels, arm joints and a gripper, so those are what a dashboard
receives.
"""
from __future__ import annotations

import pytest

from neoclaw.hardware.claw_robot import ClawRobot
from neoclaw.iot.telemetry import TelemetryCollector


@pytest.fixture
def robot():
    bot = ClawRobot.create(simulator=True, smooth=False)
    yield bot
    bot.shutdown()


def test_packet_reports_every_wheel(robot):
    packet = TelemetryCollector(robot=robot, device_id="clawbot-1").collect_once()
    assert set(packet.motor_states) == {"FRONT_LEFT", "FRONT_RIGHT", "REAR_LEFT", "REAR_RIGHT"}


def test_moving_wheels_show_as_active(robot):
    robot.forward(speed=50)
    packet = TelemetryCollector(robot=robot).collect_once()
    assert all(packet.motor_states.values())


def test_stopped_wheels_show_as_inactive(robot):
    robot.forward(speed=50)
    robot.stop()
    packet = TelemetryCollector(robot=robot).collect_once()
    assert not any(packet.motor_states.values())


def test_arm_joint_angles_are_reported_as_sensor_readings(robot):
    packet = TelemetryCollector(robot=robot).collect_once()
    assert "arm_shoulder" in packet.sensor_readings
    assert "arm_gripper" in packet.sensor_readings


def test_gripper_state_travels_in_the_packet(robot):
    robot.arm.grip()
    packet = TelemetryCollector(robot=robot).collect_once()
    assert packet.gripper_holding is True


def test_device_id_defaults_but_is_overridable(robot):
    assert TelemetryCollector(robot=robot).collect_once().device_id == "default"
    assert TelemetryCollector(robot=robot, device_id="lab-2").collect_once().device_id == "lab-2"
