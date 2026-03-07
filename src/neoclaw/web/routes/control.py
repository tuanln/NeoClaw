"""Claw control REST and WebSocket routes."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# Lazy-loaded claw instance
_claw = None


class CommandRequest(BaseModel):
    command: str
    kwargs: dict = {}


def _get_claw():
    global _claw
    if _claw is None:
        from neoclaw.hardware.claw_machine import ClawMachine
        _claw = ClawMachine.create(simulator=True)
    return _claw


@router.post("/command")
async def execute_command(req: CommandRequest):
    """Execute a claw command."""
    claw = _get_claw()

    cmd_map = {
        "move_left": claw.move_left,
        "move_right": claw.move_right,
        "move_forward": claw.move_forward,
        "move_backward": claw.move_backward,
        "move_up": claw.move_up,
        "move_down": claw.move_down,
        "grab": lambda **kw: claw.grab(),
        "release": lambda **kw: claw.release(),
        "emergency_stop": lambda **kw: claw.emergency_stop(),
    }

    handler = cmd_map.get(req.command)
    if handler is None:
        return {"error": f"Unknown command: {req.command}"}

    result = handler(**req.kwargs)
    return {"command": req.command, "result": result}


@router.get("/state")
async def get_state():
    """Get current claw state."""
    claw = _get_claw()
    return claw.get_state().to_dict()
