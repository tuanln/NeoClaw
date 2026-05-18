"""Chat history manager."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Message:
    role: str  # "user", "assistant", "system"
    content: str


class ConversationManager:
    """Manages chat history with configurable turn limit."""

    def __init__(self, max_turns: int = 6):
        self._history: list[Message] = []
        self._max_turns = max_turns

    def add_user(self, content: str) -> None:
        self._history.append(Message(role="user", content=content))
        self._trim()

    def add_assistant(self, content: str) -> None:
        self._history.append(Message(role="assistant", content=content))
        self._trim()

    def get_history(self) -> list[dict[str, str]]:
        """Return history as list of dicts for LLM API."""
        return [{"role": m.role, "content": m.content} for m in self._history]

    def clear(self) -> None:
        self._history.clear()

    def _trim(self) -> None:
        """Keep only the last max_turns * 2 messages (user + assistant pairs)."""
        max_messages = self._max_turns * 2
        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]

    @property
    def turn_count(self) -> int:
        return len([m for m in self._history if m.role == "user"])
