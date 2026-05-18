"""ClawRobot — mobile robot with arm = OmniBase + RobotArm + Sweeper.

Physical layout:
    ┌─────────────────────────────┐
    │  M1(FL) ╲       ╱ M2(FR)   │  ← Omni wheels (4x DC motor)
    │          ╲     ╱            │
    │           [ARM]             │  ← Robot arm (4x servo)
    │          ╱     ╲            │     S1=base, S2=shoulder,
    │  M3(RL) ╱       ╲ M4(RR)   │     S3=elbow, S4=gripper
    │                   [SWEEP]   │  ← Sweeper (1x servo S5)
    └─────────────────────────────┘

Uses ALL ThingBot channels:
    M1-M4: Omni base wheels
    S1-S4: Robot arm joints
    S5:    Sweeper arm
    Buzzer, LEDs, Switch: feedback
"""
from __future__ import annotations

import logging
import time

from neoclaw.config.settings import get_settings
from neoclaw.hardware.models import (
    ClawRobotState,
    LedID,
)
from neoclaw.hardware.omni_base import OmniBase
from neoclaw.hardware.robot_arm import RobotArm
from neoclaw.hardware.thingbot import ThingBot

logger = logging.getLogger(__name__)


class ClawRobot:
    """High-level API for the NeoClaw mobile robot.

    Combines OmniBase (4-wheel omni) + RobotArm (4-DOF + sweeper)
    into a unified robot interface for education.

    Usage:
        robot = ClawRobot.create()             # auto-detect hardware
        robot = ClawRobot.create(simulator=True) # no hardware needed

        # Movement
        robot.forward(speed=60, duration=1.0)
        robot.strafe_right(speed=50, duration=0.5)

        # Arm
        robot.arm.move_to(base=45, shoulder=60, elbow=120)
        robot.arm.grip()
        robot.forward(speed=40, duration=2.0)
        robot.arm.release()

        # Sweeper
        robot.arm.sweep()

        # Combined action
        robot.pick_up()    # lower arm + grip
        robot.put_down()   # lower arm + release

        robot.shutdown()
    """

    def __init__(self, thingbot: ThingBot):
        self._bot = thingbot
        self._base = OmniBase(thingbot)
        self._arm = RobotArm(thingbot, smooth=True)
        self._state = ClawRobotState()

        # Register switch as emergency stop by default
        thingbot.on_switch(self._on_switch)

    @classmethod
    def create(
        cls,
        simulator: bool = False,
        com_port: str | None = None,
    ) -> ClawRobot:
        """Factory method to create a ClawRobot.

        Args:
            simulator: If True, use simulated hardware
            com_port: Serial port for ThingBot (None = auto-detect)
        """
        if simulator:
            bot = ThingBot.create_simulator()
        else:
            settings = get_settings()
            bot = ThingBot.connect(
                com_port=com_port or settings.hardware.com_port or None,
                arduino_instance_id=settings.hardware.arduino_instance_id,
            )

        robot = cls(bot)
        logger.info(f"ClawRobot created (simulator={simulator})")
        return robot

    # ── Properties ──

    @property
    def base(self) -> OmniBase:
        """Access omni base controls directly."""
        return self._base

    @property
    def arm(self) -> RobotArm:
        """Access robot arm controls directly."""
        return self._arm

    @property
    def thingbot(self) -> ThingBot:
        """Access raw ThingBot hardware."""
        return self._bot

    # ── Base movement shortcuts ──

    def forward(self, speed: int = 60, duration: float | None = None) -> None:
        """Move forward."""
        self._base.forward(speed, duration)

    def backward(self, speed: int = 60, duration: float | None = None) -> None:
        """Move backward."""
        self._base.backward(speed, duration)

    def strafe_left(self, speed: int = 60, duration: float | None = None) -> None:
        """Strafe left."""
        self._base.strafe_left(speed, duration)

    def strafe_right(self, speed: int = 60, duration: float | None = None) -> None:
        """Strafe right."""
        self._base.strafe_right(speed, duration)

    def turn_left(self, speed: int = 50, duration: float | None = None) -> None:
        """Turn left (rotate CCW)."""
        self._base.rotate_ccw(speed, duration)

    def turn_right(self, speed: int = 50, duration: float | None = None) -> None:
        """Turn right (rotate CW)."""
        self._base.rotate_cw(speed, duration)

    def stop(self) -> None:
        """Stop all base movement."""
        self._base.stop()

    # ── Combined actions ──

    def pick_up(self, shoulder: int = 30, elbow: int = 60) -> None:
        """Combined action: lower arm, close gripper, lift.

        Args:
            shoulder: Shoulder angle for reaching down
            elbow: Elbow angle for reaching down
        """
        self._arm.release()
        self._arm.pose("reach_down")
        time.sleep(0.3)
        self._arm.grip()
        time.sleep(0.2)
        self._arm.pose("carry")
        self._beep_ok()
        logger.info("Pick up complete")

    def put_down(self) -> None:
        """Combined action: lower arm, release, lift."""
        self._arm.pose("reach_down")
        time.sleep(0.3)
        self._arm.release()
        time.sleep(0.2)
        self._arm.pose("home")
        logger.info("Put down complete")

    def sweep_clear(self) -> None:
        """Use sweeper arm to push objects aside."""
        self._arm.sweep(angle=0, return_angle=180)

    # ── Feedback ──

    def beep(self, frequency: int = 100, duration: float = 0.2) -> None:
        """Play a beep sound."""
        self._bot.buzzer(frequency)
        time.sleep(duration)
        self._bot.buzzer_off()

    def set_led(self, led: LedID, brightness: int) -> None:
        """Set LED brightness (0-100)."""
        self._bot.led(led, brightness)

    def _beep_ok(self) -> None:
        """Short confirmation beep."""
        self.beep(100, 0.1)

    # ── Switch / Emergency ──

    def _on_switch(self, pressed: bool) -> None:
        """Handle ThingBot switch press — emergency stop."""
        self._state.switch_pressed = pressed
        if pressed:
            logger.warning("Switch pressed — emergency stop")
            self.emergency_stop()

    def emergency_stop(self) -> None:
        """Stop everything immediately."""
        self._bot.stop_all_motors()
        logger.warning("EMERGENCY STOP")

    # ── State ──

    def get_state(self) -> ClawRobotState:
        """Get complete robot state."""
        self._state.base = self._base.state
        self._state.arm = self._arm.state
        return self._state

    # ── Lifecycle ──

    def shutdown(self) -> None:
        """Safe shutdown: stop motors, home arm, cleanup."""
        self._base.stop()
        try:
            self._arm.home()
        except Exception:
            pass
        self._bot.shutdown()
        logger.info("ClawRobot shut down")
