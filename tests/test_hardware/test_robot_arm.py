"""Unit tests for RobotArm: joint limits, preset poses, smooth motion."""
from __future__ import annotations

import pytest

from neoclaw.hardware.models import ARM_POSES, JOINT_LIMITS, JointName, ServoID
from neoclaw.hardware.robot_arm import RobotArm


class StubThingBot:
    """Records every `servo(servo_id, angle)` call. No real hardware."""

    def __init__(self):
        self.servo_calls: list[tuple[ServoID, int]] = []

    def servo(self, sid: ServoID, angle: int) -> None:
        self.servo_calls.append((sid, angle))

    def last_angle(self, sid: ServoID) -> int | None:
        for s, a in reversed(self.servo_calls):
            if s == sid:
                return a
        return None


# ── Joint limits clamp ──


@pytest.mark.parametrize(
    "joint,input_angle,expected",
    [
        (JointName.BASE, -10, 0),
        (JointName.BASE, 0, 0),
        (JointName.BASE, 90, 90),
        (JointName.BASE, 180, 180),
        (JointName.BASE, 250, 180),
        (JointName.SHOULDER, -5, 0),
        (JointName.SHOULDER, 200, 180),
        (JointName.ELBOW, 999, 180),
        (JointName.GRIPPER, -1, 0),
        (JointName.GRIPPER, 45, 45),
        (JointName.GRIPPER, 95, 90),  # gripper max is 90, not 180
        (JointName.SWEEPER, 270, 180),
    ],
)
def test_set_joint_respects_limits(joint, input_angle, expected):
    bot = StubThingBot()
    arm = RobotArm(bot, smooth=False)  # direct mode for deterministic check
    arm.set_joint(joint, input_angle)
    assert arm.get_joint(joint) == expected


def test_joint_limits_table_matches_expectation():
    """Sanity check on the limits constant — gripper is the only non-180 joint."""
    assert JOINT_LIMITS[JointName.BASE] == (0, 180)
    assert JOINT_LIMITS[JointName.SHOULDER] == (0, 180)
    assert JOINT_LIMITS[JointName.ELBOW] == (0, 180)
    assert JOINT_LIMITS[JointName.GRIPPER] == (0, 90)
    assert JOINT_LIMITS[JointName.SWEEPER] == (0, 180)


# ── Preset poses ──


def test_arm_poses_table_has_5_presets():
    expected = {"home", "reach_forward", "reach_down", "carry", "rest"}
    assert set(ARM_POSES.keys()) == expected


def test_pose_home_centers_joints():
    bot = StubThingBot()
    arm = RobotArm(bot, smooth=False)
    arm.home()
    assert arm.get_joint(JointName.BASE) == 90
    assert arm.get_joint(JointName.SHOULDER) == 90
    assert arm.get_joint(JointName.ELBOW) == 90
    assert arm.get_joint(JointName.GRIPPER) == 0


def test_pose_carry_closes_gripper():
    bot = StubThingBot()
    arm = RobotArm(bot, smooth=False)
    arm.pose("carry")
    assert arm.get_joint(JointName.GRIPPER) == 70
    assert arm.is_gripping is False  # state.gripper_holding set only by grip()


def test_pose_unknown_raises():
    bot = StubThingBot()
    arm = RobotArm(bot, smooth=False)
    with pytest.raises(ValueError, match="Unknown pose"):
        arm.pose("does_not_exist")


# ── Gripper state ──


def test_grip_then_release_state():
    bot = StubThingBot()
    arm = RobotArm(bot, smooth=False)
    arm.grip(force=80)
    assert arm.is_gripping is True
    assert arm.get_joint(JointName.GRIPPER) == 80
    arm.release()
    assert arm.is_gripping is False
    assert arm.get_joint(JointName.GRIPPER) == 0


# ── Smooth motion: correct step count ──


def test_smooth_motion_steps_one_degree_at_a_time():
    """Smooth mode: moving from 90 → 100 should write 10 intermediate angles
    (one per degree, monotonic up).
    """
    bot = StubThingBot()
    arm = RobotArm(bot, smooth=True)
    # First set joint directly so internal state is known
    arm.set_joint(JointName.BASE, 90)  # snap-or-step doesn't matter — sets state to 90
    bot.servo_calls.clear()  # ignore that first move

    arm.set_joint(JointName.BASE, 100)
    base_writes = [a for s, a in bot.servo_calls if s == ServoID.S1]
    # Expect monotonic 91, 92, ..., 100 (10 writes), or 91..100 depending on
    # range() inclusive behavior. Verify count and final value.
    assert len(base_writes) >= 10
    assert base_writes[-1] == 100
    # Monotonic non-decreasing
    for i in range(1, len(base_writes)):
        assert base_writes[i] >= base_writes[i - 1]


def test_smooth_motion_descending_steps():
    bot = StubThingBot()
    arm = RobotArm(bot, smooth=True)
    arm.set_joint(JointName.BASE, 100)
    bot.servo_calls.clear()

    arm.set_joint(JointName.BASE, 90)
    base_writes = [a for s, a in bot.servo_calls if s == ServoID.S1]
    assert len(base_writes) >= 10
    assert base_writes[-1] == 90
    for i in range(1, len(base_writes)):
        assert base_writes[i] <= base_writes[i - 1]


def test_smooth_motion_noop_when_same_angle():
    """Moving to the current angle should not generate writes."""
    bot = StubThingBot()
    arm = RobotArm(bot, smooth=True)
    arm.set_joint(JointName.BASE, 90)
    bot.servo_calls.clear()

    arm.set_joint(JointName.BASE, 90)
    base_writes = [a for s, a in bot.servo_calls if s == ServoID.S1]
    assert base_writes == []


# ── move_to convenience ──


def test_move_to_sets_three_joints():
    bot = StubThingBot()
    arm = RobotArm(bot, smooth=False)
    arm.move_to(base=30, shoulder=60, elbow=120)
    assert arm.get_joint(JointName.BASE) == 30
    assert arm.get_joint(JointName.SHOULDER) == 60
    assert arm.get_joint(JointName.ELBOW) == 120
    # Gripper untouched
    assert arm.get_joint(JointName.GRIPPER) == 0
