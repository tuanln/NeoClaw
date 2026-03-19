"""4-DOF robot arm + sweeper using ThingBot servos.

Joint layout:
    S1 — BASE:     Base rotation (yaw, 0-180°)
    S2 — SHOULDER: Shoulder joint (pitch, 0-180°)
    S3 — ELBOW:    Elbow joint (pitch, 0-180°)
    S4 — GRIPPER:  Gripper open/close (0=open, 90=closed)
    S5 — SWEEPER:  Sweeper arm (side-mounted pusher)

Side view of arm:
         S2 (shoulder)
          ╲
           ╲ upper arm
            ╲
             S3 (elbow)
             ╱
            ╱ forearm
           ╱
        S4 [gripper]

Top view:
    S1 rotates entire arm assembly around vertical axis.
"""
from __future__ import annotations

import logging
import time

from neoclaw.hardware.models import (
    ARM_POSES,
    ArmState,
    JointName,
    JOINT_LIMITS,
    JOINT_SERVO_MAP,
    ServoID,
)
from neoclaw.hardware.thingbot import ThingBot

logger = logging.getLogger(__name__)

# Delay between servo steps for smooth movement (seconds)
_STEP_DELAY = 0.02  # 20ms per degree step


class RobotArm:
    """4-DOF robot arm with gripper and sweeper.

    Controls ThingBot S1-S5 with angle limits and smooth movement.

    Usage:
        bot = ThingBot.connect()
        arm = RobotArm(bot)
        arm.home()
        arm.set_joint(JointName.BASE, 45)
        arm.set_joint(JointName.SHOULDER, 60)
        arm.grip()
        arm.pose("carry")
        arm.sweep()
        arm.release()
    """

    def __init__(self, thingbot: ThingBot, smooth: bool = True):
        """Initialize arm.

        Args:
            thingbot: ThingBot hardware interface
            smooth: If True, move servos gradually instead of snapping
        """
        self._bot = thingbot
        self._smooth = smooth
        self._state = ArmState()

    @property
    def state(self) -> ArmState:
        return self._state

    # ── Joint control ──

    def set_joint(self, joint: JointName, angle: int) -> None:
        """Set a joint to a specific angle.

        Args:
            joint: Which joint to move
            angle: Target angle in degrees (clamped to joint limits)
        """
        lo, hi = JOINT_LIMITS[joint]
        angle = max(lo, min(hi, angle))

        if self._smooth:
            self._move_smooth(joint, angle)
        else:
            self._move_direct(joint, angle)

        self._state.joint_angles[joint] = angle

    def get_joint(self, joint: JointName) -> int:
        """Get current angle of a joint."""
        return self._state.joint_angles[joint]

    # ── Gripper ──

    def grip(self, force: int = 70) -> None:
        """Close gripper.

        Args:
            force: Closing angle (0=open, 90=max close). Default 70.
        """
        self.set_joint(JointName.GRIPPER, force)
        self._state.gripper_holding = True
        logger.info(f"Gripper closed (force={force})")

    def release(self) -> None:
        """Open gripper fully."""
        self.set_joint(JointName.GRIPPER, 0)
        self._state.gripper_holding = False
        logger.info("Gripper opened")

    @property
    def is_gripping(self) -> bool:
        return self._state.gripper_holding

    # ── Sweeper (S5) ──

    def sweep(self, angle: int = 0, return_angle: int = 180) -> None:
        """Activate sweeper arm — push motion.

        Moves to `angle`, then returns to `return_angle`.

        Args:
            angle: Sweep target angle
            return_angle: Return position after sweep
        """
        self.set_joint(JointName.SWEEPER, angle)
        time.sleep(0.3)
        self.set_joint(JointName.SWEEPER, return_angle)
        logger.info(f"Sweep: {angle}° → {return_angle}°")

    def set_sweeper(self, angle: int) -> None:
        """Set sweeper to a specific position."""
        self.set_joint(JointName.SWEEPER, angle)

    # ── Preset poses ──

    def pose(self, pose_name: str) -> None:
        """Move arm to a named preset pose.

        Available poses: home, reach_forward, reach_down, carry, rest

        Args:
            pose_name: Name of the pose
        """
        if pose_name not in ARM_POSES:
            raise ValueError(
                f"Unknown pose '{pose_name}'. Available: {list(ARM_POSES.keys())}"
            )

        target = ARM_POSES[pose_name]
        for joint, angle in target.items():
            self.set_joint(joint, angle)

        logger.info(f"Arm pose: {pose_name}")

    def home(self) -> None:
        """Move to home position (all joints centered)."""
        self.pose("home")

    # ── Multi-joint movement ──

    def move_to(self, base: int, shoulder: int, elbow: int) -> None:
        """Move arm to a specific position (base, shoulder, elbow).

        Moves base first, then shoulder and elbow together.

        Args:
            base: Base rotation angle (0-180°)
            shoulder: Shoulder angle (0-180°)
            elbow: Elbow angle (0-180°)
        """
        self.set_joint(JointName.BASE, base)
        self.set_joint(JointName.SHOULDER, shoulder)
        self.set_joint(JointName.ELBOW, elbow)

    # ── Internal servo movement ──

    def _move_direct(self, joint: JointName, angle: int) -> None:
        """Snap servo to angle immediately."""
        servo = JOINT_SERVO_MAP[joint]
        self._bot.servo(servo, angle)

    def _move_smooth(self, joint: JointName, target: int) -> None:
        """Move servo gradually for smooth motion."""
        servo = JOINT_SERVO_MAP[joint]
        current = self._state.joint_angles.get(joint, 90)

        if current == target:
            return

        step = 1 if target > current else -1
        for angle in range(current, target + step, step):
            self._bot.servo(servo, angle)
            time.sleep(_STEP_DELAY)

    # ── State ──

    def get_angles(self) -> dict[str, int]:
        """Get all joint angles as a simple dict."""
        return {j.name: a for j, a in self._state.joint_angles.items()}
