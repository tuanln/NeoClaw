"""Hardware data models for NeoClaw multi-robot platform."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto


# ── Legacy Claw Machine enums (backward compatible) ──

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


# ── ThingBot hardware IDs (match Arduino firmware) ──

class MotorID(IntEnum):
    """ThingBot DC motor IDs. PCA9685 channels defined in firmware."""
    M1 = 1  # PCA9685 ch 2(A) / 3(B)
    M2 = 2  # PCA9685 ch 4(A) / 5(B)
    M3 = 3  # PCA9685 ch 7(A) / 8(B)
    M4 = 4  # PCA9685 ch 1(A) / 0(B)


class ServoID(IntEnum):
    """ThingBot servo IDs. PCA9685 channels defined in firmware."""
    S1 = 1  # PCA9685 ch 12
    S2 = 2  # PCA9685 ch 11
    S3 = 3  # PCA9685 ch 10
    S4 = 4  # PCA9685 ch 9
    S5 = 5  # PCA9685 ch 8


class LedID(IntEnum):
    """ThingBot LED IDs."""
    LED1 = 1  # PCA9685 ch 15
    LED2 = 2  # PCA9685 ch 13


# ── Robot Profiles ──

class RobotProfile(Enum):
    """Supported robot configurations using ThingBot hardware."""
    CLAW_MACHINE = "claw_machine"     # Legacy: 3-axis gantry + electromagnet
    CLAW_ROBOT = "claw_robot"         # Omni base + robot arm
    OTTO_BIPED = "otto_biped"         # 4-servo biped (future)


# ── Omni Base ──

class WheelPosition(Enum):
    """Wheel positions for 4-wheel omni base (top view)."""
    FRONT_LEFT = auto()   # M1
    FRONT_RIGHT = auto()  # M2
    REAR_LEFT = auto()    # M3
    REAR_RIGHT = auto()   # M4


# Motor-to-wheel mapping
WHEEL_MOTOR_MAP: dict[WheelPosition, MotorID] = {
    WheelPosition.FRONT_LEFT: MotorID.M1,
    WheelPosition.FRONT_RIGHT: MotorID.M2,
    WheelPosition.REAR_LEFT: MotorID.M3,
    WheelPosition.REAR_RIGHT: MotorID.M4,
}


@dataclass
class OmniBaseState:
    """State of the 4-wheel omnidirectional base."""
    wheel_speeds: dict[WheelPosition, int] = field(
        default_factory=lambda: {w: 0 for w in WheelPosition}
    )
    heading: float = 0.0  # estimated heading in degrees

    def is_moving(self) -> bool:
        return any(s != 0 for s in self.wheel_speeds.values())

    def to_dict(self) -> dict:
        return {
            "wheels": {w.name: s for w, s in self.wheel_speeds.items()},
            "heading": self.heading,
            "moving": self.is_moving(),
        }


# ── Robot Arm (4-DOF + sweeper) ──

class JointName(Enum):
    """Robot arm joint names."""
    BASE = auto()      # S1: base rotation (yaw, 0-180°)
    SHOULDER = auto()  # S2: shoulder (pitch, 0-180°)
    ELBOW = auto()     # S3: elbow (pitch, 0-180°)
    GRIPPER = auto()   # S4: gripper (open/close)
    SWEEPER = auto()   # S5: sweeper arm


# Servo-to-joint mapping
JOINT_SERVO_MAP: dict[JointName, ServoID] = {
    JointName.BASE: ServoID.S1,
    JointName.SHOULDER: ServoID.S2,
    JointName.ELBOW: ServoID.S3,
    JointName.GRIPPER: ServoID.S4,
    JointName.SWEEPER: ServoID.S5,
}

# Default angle limits per joint
JOINT_LIMITS: dict[JointName, tuple[int, int]] = {
    JointName.BASE: (0, 180),
    JointName.SHOULDER: (0, 180),
    JointName.ELBOW: (0, 180),
    JointName.GRIPPER: (0, 90),     # 0=open, 90=closed
    JointName.SWEEPER: (0, 180),
}


@dataclass
class ArmState:
    """State of the robot arm."""
    joint_angles: dict[JointName, int] = field(
        default_factory=lambda: {
            JointName.BASE: 90,
            JointName.SHOULDER: 90,
            JointName.ELBOW: 90,
            JointName.GRIPPER: 0,
            JointName.SWEEPER: 90,
        }
    )
    gripper_holding: bool = False

    def to_dict(self) -> dict:
        return {
            "joints": {j.name: a for j, a in self.joint_angles.items()},
            "gripper_holding": self.gripper_holding,
        }


# ── Arm Preset Poses ──

ARM_POSES: dict[str, dict[JointName, int]] = {
    "home": {
        JointName.BASE: 90, JointName.SHOULDER: 90,
        JointName.ELBOW: 90, JointName.GRIPPER: 0,
    },
    "reach_forward": {
        JointName.BASE: 90, JointName.SHOULDER: 45,
        JointName.ELBOW: 135, JointName.GRIPPER: 0,
    },
    "reach_down": {
        JointName.BASE: 90, JointName.SHOULDER: 30,
        JointName.ELBOW: 60, JointName.GRIPPER: 0,
    },
    "carry": {
        JointName.BASE: 90, JointName.SHOULDER: 120,
        JointName.ELBOW: 60, JointName.GRIPPER: 70,
    },
    "rest": {
        JointName.BASE: 90, JointName.SHOULDER: 150,
        JointName.ELBOW: 30, JointName.GRIPPER: 0,
    },
}


# ── Combined Robot State ──

@dataclass
class ClawRobotState:
    """Complete state of the Claw Robot (omni base + arm)."""
    base: OmniBaseState = field(default_factory=OmniBaseState)
    arm: ArmState = field(default_factory=ArmState)
    switch_pressed: bool = False
    buzzer_freq: int = 0
    leds: dict[LedID, int] = field(
        default_factory=lambda: {LedID.LED1: 0, LedID.LED2: 0}
    )

    def to_dict(self) -> dict:
        return {
            "base": self.base.to_dict(),
            "arm": self.arm.to_dict(),
            "switch_pressed": self.switch_pressed,
            "buzzer_freq": self.buzzer_freq,
            "leds": {led.name: v for led, v in self.leds.items()},
        }


# ── Legacy models (backward compatible) ──

@dataclass
class MotorState:
    """State of a single motor (legacy claw machine)."""
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
    """Complete state of the claw machine (legacy)."""
    motors: dict[str, MotorState] = field(default_factory=dict)
    magnet_active: bool = False
    limits: dict[str, bool] = field(default_factory=dict)
    buttons: dict[str, bool] = field(default_factory=dict)
    led_on: bool = False
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


# ── Command vocabulary ───────────────────────────────────────────────────────
#
# The verbs the whole app speaks: student sandbox, natural-language parsing,
# REST/WebSocket, CLI and the AI agent all produce ClawCommand objects and hand
# them to neoclaw.hardware.dispatch. Kept here, next to ClawRobot's state, so
# the vocabulary can never describe a robot that does not exist.


class ClawCommandType(Enum):
    """ClawBot verbs. Movement is omni (no Z axis — that was the gantry)."""

    FORWARD = auto()
    BACKWARD = auto()
    STRAFE_LEFT = auto()
    STRAFE_RIGHT = auto()
    TURN_LEFT = auto()
    TURN_RIGHT = auto()
    STOP = auto()

    ARM_POSE = auto()
    GRIP = auto()
    RELEASE = auto()
    PICK_UP = auto()
    PUT_DOWN = auto()
    SWEEP = auto()

    GET_STATE = auto()
    EMERGENCY_STOP = auto()


@dataclass
class ClawCommand:
    """One parsed command, from student code, natural language or an API call."""

    command_type: ClawCommandType
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "cmd": self.command_type.name,
            "args": list(self.args),
            "kwargs": self.kwargs,
        }
