"""Agent data models.

The command vocabulary itself lives with the robot it describes
(`neoclaw.hardware.models`) and is re-exported here so agent-side callers keep
their import path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from neoclaw.hardware.models import ClawCommand, ClawCommandType

__all__ = ["AgentAction", "AgentMode", "ClawCommand", "ClawCommandType"]


class AgentMode(Enum):
    TEACH = auto()
    FREE_PLAY = auto()
    VOICE_CONTROL = auto()
    CHALLENGE = auto()


@dataclass
class AgentAction:
    """An action the agent wants to take."""
    action_type: str  # "execute_code", "send_hint", "run_command", "explain"
    content: str
    metadata: dict = field(default_factory=dict)
