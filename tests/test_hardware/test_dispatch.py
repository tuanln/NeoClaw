"""One command vocabulary for the whole app, dispatched onto a real ClawRobot.

Before this module, web routes, the CLI and the AI agent each carried their own
hand-written `{"move_left": claw.move_left, ...}` table — all three written for
the retired gantry ClawMachine, none of them for the robot the product actually
ships. A single table, exercised against a real (simulated) ClawRobot, is what
keeps the layers from drifting apart again.
"""
from __future__ import annotations

import pytest

from neoclaw.hardware.claw_robot import ClawRobot
from neoclaw.hardware.dispatch import COMMAND_HANDLERS, apply_command
from neoclaw.hardware.models import ClawCommand, ClawCommandType


@pytest.fixture
def robot():
    bot = ClawRobot.create(simulator=True, smooth=False)
    yield bot
    bot.shutdown()


def test_every_command_type_has_a_handler():
    """A verb the vocabulary names but nothing can execute is a broken promise."""
    missing = [c.name for c in ClawCommandType if c not in COMMAND_HANDLERS]
    assert missing == []


def test_forward_spins_all_four_wheels_the_same_way(robot):
    apply_command(robot, ClawCommand(ClawCommandType.FORWARD, kwargs={"speed": 60}))
    wheels = robot.get_state().to_dict()["base"]["wheels"]
    assert set(wheels.values()) == {60}


def test_strafe_left_uses_the_mecanum_pattern(robot):
    apply_command(robot, ClawCommand(ClawCommandType.STRAFE_LEFT, kwargs={"speed": 50}))
    wheels = robot.get_state().to_dict()["base"]["wheels"]
    assert wheels["FRONT_LEFT"] == -50
    assert wheels["FRONT_RIGHT"] == 50
    assert wheels["REAR_LEFT"] == 50
    assert wheels["REAR_RIGHT"] == -50


def test_turn_right_drives_the_sides_opposite(robot):
    apply_command(robot, ClawCommand(ClawCommandType.TURN_RIGHT, kwargs={"speed": 40}))
    wheels = robot.get_state().to_dict()["base"]["wheels"]
    assert wheels["FRONT_LEFT"] == -wheels["FRONT_RIGHT"]
    assert wheels["FRONT_LEFT"] != 0


def test_stop_halts_every_wheel(robot):
    apply_command(robot, ClawCommand(ClawCommandType.FORWARD, kwargs={"speed": 60}))
    apply_command(robot, ClawCommand(ClawCommandType.STOP))
    wheels = robot.get_state().to_dict()["base"]["wheels"]
    assert set(wheels.values()) == {0}


def test_grip_then_release_toggles_the_gripper(robot):
    apply_command(robot, ClawCommand(ClawCommandType.GRIP))
    assert robot.get_state().to_dict()["arm"]["gripper_holding"] is True
    apply_command(robot, ClawCommand(ClawCommandType.RELEASE))
    assert robot.get_state().to_dict()["arm"]["gripper_holding"] is False


def test_arm_pose_moves_the_joints(robot):
    apply_command(robot, ClawCommand(ClawCommandType.ARM_POSE, kwargs={"pose": "reach_down"}))
    joints = robot.get_state().to_dict()["arm"]["joints"]
    assert joints["SHOULDER"] != 90 or joints["ELBOW"] != 90


def test_get_state_returns_the_robot_state(robot):
    result = apply_command(robot, ClawCommand(ClawCommandType.GET_STATE))
    assert "base" in result
    assert "arm" in result


def test_emergency_stop_is_dispatchable(robot):
    apply_command(robot, ClawCommand(ClawCommandType.FORWARD, kwargs={"speed": 80}))
    apply_command(robot, ClawCommand(ClawCommandType.EMERGENCY_STOP))
    wheels = robot.get_state().to_dict()["base"]["wheels"]
    assert set(wheels.values()) == {0}


def test_unknown_kwargs_do_not_crash_the_robot(robot):
    """Student code and NL parsing both produce stray kwargs; they must be ignored."""
    apply_command(robot, ClawCommand(ClawCommandType.FORWARD, kwargs={"speed": 30, "colour": "red"}))
    assert robot.get_state().to_dict()["base"]["wheels"]["FRONT_LEFT"] == 30


def test_vocabulary_has_no_gantry_verbs():
    """MOVE_UP/MOVE_DOWN belonged to the Z axis of the arcade claw machine."""
    names = {c.name for c in ClawCommandType}
    assert "MOVE_UP" not in names
    assert "MOVE_DOWN" not in names


def test_simulated_robot_can_skip_smooth_servo_motion():
    """Smooth motion sleeps between servo steps — real on a board, dead weight in tests."""
    import time

    from neoclaw.hardware.models import ARM_POSES

    bot = ClawRobot.create(simulator=True, smooth=False)
    try:
        started = time.monotonic()
        apply_command(bot, ClawCommand(ClawCommandType.ARM_POSE, kwargs={"pose": "carry"}))
        elapsed = time.monotonic() - started
        # Read before shutdown — shutting down parks the arm at home.
        joints = bot.get_state().to_dict()["arm"]["joints"]
    finally:
        bot.shutdown()

    assert elapsed < 0.2
    for joint, angle in ARM_POSES["carry"].items():
        assert joints[joint.name] == angle


# ── Tên lệnh dạng chuỗi (REST, CLI, và sau này là MCP) ──


def test_command_name_maps_to_the_vocabulary():
    from neoclaw.hardware.dispatch import command_from_name

    cmd = command_from_name("strafe_left", speed=40)
    assert cmd.command_type is ClawCommandType.STRAFE_LEFT
    assert cmd.kwargs == {"speed": 40}


def test_every_command_type_has_a_string_name():
    from neoclaw.hardware.dispatch import COMMAND_NAMES

    assert {c for c in ClawCommandType} == set(COMMAND_NAMES.values())


def test_command_names_are_lowercase_snake_case():
    from neoclaw.hardware.dispatch import COMMAND_NAMES

    for name in COMMAND_NAMES:
        assert name == name.lower()
        assert " " not in name


def test_unknown_command_name_is_rejected():
    from neoclaw.hardware.dispatch import command_from_name

    with pytest.raises(KeyError):
        command_from_name("move_up")
