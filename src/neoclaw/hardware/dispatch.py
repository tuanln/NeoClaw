"""One place that turns a ClawCommand into a ClawRobot call.

Every surface that can drive the robot — the student sandbox, natural-language
input, the REST/WebSocket API, the CLI, the AI agent — goes through this table.
They used to keep three separate hand-written tables, all of them written for
the retired gantry ClawMachine; one table, tested against a real ClawRobot, is
what stops that from happening again.

This is also the surface an MCP tool layer should wrap: one MCP tool per
ClawCommandType, no second mapping.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from neoclaw.hardware.claw_robot import ClawRobot
from neoclaw.hardware.models import ClawCommand, ClawCommandType

logger = logging.getLogger(__name__)


def _drive(method_name: str) -> Callable[[ClawRobot, dict], Any]:
    """Movement verbs share a signature: (speed, duration)."""

    def handler(robot: ClawRobot, kwargs: dict) -> Any:
        method = getattr(robot, method_name)
        call: dict[str, Any] = {}
        if "speed" in kwargs:
            call["speed"] = int(kwargs["speed"])
        if "duration" in kwargs:
            call["duration"] = float(kwargs["duration"])
        return method(**call)

    return handler


def _arm_pose(robot: ClawRobot, kwargs: dict) -> Any:
    return robot.arm.pose(str(kwargs.get("pose", "rest")))


# Handlers take (robot, kwargs) and ignore any keyword they do not know: student
# code and NL parsing both produce stray arguments, and a typo must not stop the
# robot mid-lesson.
COMMAND_HANDLERS: dict[ClawCommandType, Callable[[ClawRobot, dict], Any]] = {
    ClawCommandType.FORWARD: _drive("forward"),
    ClawCommandType.BACKWARD: _drive("backward"),
    ClawCommandType.STRAFE_LEFT: _drive("strafe_left"),
    ClawCommandType.STRAFE_RIGHT: _drive("strafe_right"),
    ClawCommandType.TURN_LEFT: _drive("turn_left"),
    ClawCommandType.TURN_RIGHT: _drive("turn_right"),
    ClawCommandType.STOP: lambda robot, kwargs: robot.stop(),
    ClawCommandType.ARM_POSE: _arm_pose,
    ClawCommandType.GRIP: lambda robot, kwargs: robot.arm.grip(),
    ClawCommandType.RELEASE: lambda robot, kwargs: robot.arm.release(),
    ClawCommandType.PICK_UP: lambda robot, kwargs: robot.pick_up(),
    ClawCommandType.PUT_DOWN: lambda robot, kwargs: robot.put_down(),
    ClawCommandType.SWEEP: lambda robot, kwargs: robot.sweep_clear(),
    ClawCommandType.GET_STATE: lambda robot, kwargs: robot.get_state().to_dict(),
    ClawCommandType.EMERGENCY_STOP: lambda robot, kwargs: robot.emergency_stop(),
}


def apply_command(robot: ClawRobot, command: ClawCommand) -> Any:
    """Run one command on the robot and return whatever it produces."""
    handler = COMMAND_HANDLERS.get(command.command_type)
    if handler is None:
        raise KeyError(f"No handler for {command.command_type.name}")
    logger.debug("dispatch %s %s", command.command_type.name, command.kwargs)
    return handler(robot, command.kwargs)


# ── String names ─────────────────────────────────────────────────────────────
#
# The REST API, the CLI and (later) the MCP tool layer all address commands by
# name. Derived from the enum rather than typed out again, so a new verb cannot
# be reachable from one surface and invisible to another.
COMMAND_NAMES: dict[str, ClawCommandType] = {c.name.lower(): c for c in ClawCommandType}


def command_from_name(name: str, **kwargs: Any) -> ClawCommand:
    """Build a ClawCommand from a wire/CLI name. Raises KeyError if unknown."""
    try:
        command_type = COMMAND_NAMES[name.lower()]
    except KeyError:
        raise KeyError(
            f"Unknown command '{name}'. Known: {sorted(COMMAND_NAMES)}"
        ) from None
    return ClawCommand(command_type=command_type, kwargs=kwargs)
