"""Agent data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class ClawCommandType(Enum):
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    MOVE_FORWARD = auto()
    MOVE_BACKWARD = auto()
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    GRAB = auto()
    RELEASE = auto()
    GET_STATE = auto()
    EMERGENCY_STOP = auto()


class AgentMode(Enum):
    TEACH = auto()
    FREE_PLAY = auto()
    VOICE_CONTROL = auto()
    CHALLENGE = auto()


@dataclass
class ClawCommand:
    """A parsed claw command from student code or NL input."""
    command_type: ClawCommandType
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "cmd": self.command_type.name,
            "args": list(self.args),
            "kwargs": self.kwargs,
        }


@dataclass
class AgentAction:
    """An action the agent wants to take."""
    action_type: str  # "execute_code", "send_hint", "run_command", "explain"
    content: str
    metadata: dict = field(default_factory=dict)
