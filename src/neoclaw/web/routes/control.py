"""Robot control REST routes.

Thin on purpose: command names, the vocabulary and the robot calls all come
from neoclaw.hardware.dispatch, which is covered by tests that run without a
web stack installed. This module only translates HTTP into that call.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from neoclaw.hardware.dispatch import COMMAND_NAMES, apply_command, command_from_name

router = APIRouter()

# Lazy-loaded robot instance
_robot = None


class CommandRequest(BaseModel):
    command: str
    kwargs: dict = {}


def _get_robot():
    global _robot
    if _robot is None:
        from neoclaw.hardware.claw_robot import ClawRobot
        _robot = ClawRobot.create(simulator=True)
    return _robot


@router.get("/commands")
async def list_commands():
    """Every verb this robot understands."""
    return {"commands": sorted(COMMAND_NAMES)}


@router.post("/command")
async def execute_command(req: CommandRequest):
    """Execute one robot command."""
    try:
        command = command_from_name(req.command, **req.kwargs)
    except KeyError:
        return {"error": f"Unknown command: {req.command}"}

    result = apply_command(_get_robot(), command)
    return {"command": req.command, "result": result}


@router.get("/state")
async def get_state():
    """Current robot state."""
    return _get_robot().get_state().to_dict()
