"""Natural language to claw command interpreter."""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from neoclaw.agent.models import ClawCommand, ClawCommandType

logger = logging.getLogger(__name__)

# Vietnamese/English keyword mapping to commands
_KEYWORD_MAP: dict[str, ClawCommandType] = {
    # Vietnamese
    "trai": ClawCommandType.MOVE_LEFT,
    "sang trai": ClawCommandType.MOVE_LEFT,
    "phai": ClawCommandType.MOVE_RIGHT,
    "sang phai": ClawCommandType.MOVE_RIGHT,
    "tien": ClawCommandType.MOVE_FORWARD,
    "di tien": ClawCommandType.MOVE_FORWARD,
    "lui": ClawCommandType.MOVE_BACKWARD,
    "di lui": ClawCommandType.MOVE_BACKWARD,
    "len": ClawCommandType.MOVE_UP,
    "di len": ClawCommandType.MOVE_UP,
    "nang len": ClawCommandType.MOVE_UP,
    "xuong": ClawCommandType.MOVE_DOWN,
    "ha xuong": ClawCommandType.MOVE_DOWN,
    "gap": ClawCommandType.GRAB,
    "bat nam cham": ClawCommandType.GRAB,
    "tha": ClawCommandType.RELEASE,
    "tat nam cham": ClawCommandType.RELEASE,
    "dung": ClawCommandType.EMERGENCY_STOP,
    "dung lai": ClawCommandType.EMERGENCY_STOP,
    # English
    "left": ClawCommandType.MOVE_LEFT,
    "move left": ClawCommandType.MOVE_LEFT,
    "right": ClawCommandType.MOVE_RIGHT,
    "move right": ClawCommandType.MOVE_RIGHT,
    "forward": ClawCommandType.MOVE_FORWARD,
    "move forward": ClawCommandType.MOVE_FORWARD,
    "backward": ClawCommandType.MOVE_BACKWARD,
    "move backward": ClawCommandType.MOVE_BACKWARD,
    "up": ClawCommandType.MOVE_UP,
    "move up": ClawCommandType.MOVE_UP,
    "down": ClawCommandType.MOVE_DOWN,
    "move down": ClawCommandType.MOVE_DOWN,
    "grab": ClawCommandType.GRAB,
    "pick up": ClawCommandType.GRAB,
    "release": ClawCommandType.RELEASE,
    "drop": ClawCommandType.RELEASE,
    "stop": ClawCommandType.EMERGENCY_STOP,
}


class NLInterpreter:
    """Interprets natural language into claw commands.

    Uses offline keyword matching first, falls back to LLM if available.
    """

    def __init__(self, llm_client=None):
        self._llm = llm_client

    def interpret(self, text: str) -> list[ClawCommand]:
        """Parse natural language text into claw commands."""
        commands = self._keyword_parse(text)
        if commands:
            return commands

        if self._llm is not None and self._llm.is_available():
            return self._llm_parse(text)

        return []

    def _keyword_parse(self, text: str) -> list[ClawCommand]:
        """Offline keyword-based parsing."""
        text_lower = text.lower().strip()
        text_normalized = self._remove_diacritics(text_lower)
        commands = []

        # Try multi-word matches first (longer phrases)
        remaining = text_normalized
        sorted_keywords = sorted(_KEYWORD_MAP.keys(), key=len, reverse=True)

        for keyword in sorted_keywords:
            if keyword in remaining:
                cmd_type = _KEYWORD_MAP[keyword]
                duration = self._extract_duration(remaining)
                kwargs = {}
                if duration is not None:
                    kwargs["duration"] = duration
                commands.append(ClawCommand(command_type=cmd_type, kwargs=kwargs))
                remaining = remaining.replace(keyword, "", 1).strip()

        return commands

    def _llm_parse(self, text: str) -> list[ClawCommand]:
        """Use LLM to parse complex natural language."""
        from neoclaw.agent.prompt_templates import CLAW_NL_INTERPRETER_SYSTEM

        response = self._llm.generate(
            prompt=text,
            system_prompt=CLAW_NL_INTERPRETER_SYSTEM,
            max_tokens=200,
        )

        try:
            data = json.loads(response)
            commands = []
            for cmd_data in data.get("commands", []):
                cmd_name = cmd_data.get("cmd", "")
                try:
                    cmd_type = ClawCommandType[cmd_name]
                except KeyError:
                    continue
                commands.append(ClawCommand(
                    command_type=cmd_type,
                    kwargs=cmd_data.get("kwargs", {}),
                ))
            return commands
        except (json.JSONDecodeError, KeyError):
            logger.warning(f"Failed to parse LLM response: {response}")
            return []

    @staticmethod
    def _extract_duration(text: str) -> Optional[float]:
        """Extract duration from text like '2 giay', '1.5 seconds', '3s'."""
        match = re.search(r"(\d+\.?\d*)\s*(?:giay|seconds?|s\b)", text)
        if match:
            return float(match.group(1))
        return None

    @staticmethod
    def _remove_diacritics(text: str) -> str:
        """Remove Vietnamese diacritics for keyword matching."""
        replacements = {
            "à": "a", "á": "a", "ả": "a", "ã": "a", "ạ": "a",
            "ă": "a", "ằ": "a", "ắ": "a", "ẳ": "a", "ẵ": "a", "ặ": "a",
            "â": "a", "ầ": "a", "ấ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a",
            "è": "e", "é": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
            "ê": "e", "ề": "e", "ế": "e", "ể": "e", "ễ": "e", "ệ": "e",
            "ì": "i", "í": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
            "ò": "o", "ó": "o", "ỏ": "o", "õ": "o", "ọ": "o",
            "ô": "o", "ồ": "o", "ố": "o", "ổ": "o", "ỗ": "o", "ộ": "o",
            "ơ": "o", "ờ": "o", "ớ": "o", "ở": "o", "ỡ": "o", "ợ": "o",
            "ù": "u", "ú": "u", "ủ": "u", "ũ": "u", "ụ": "u",
            "ư": "u", "ừ": "u", "ứ": "u", "ử": "u", "ữ": "u", "ự": "u",
            "ỳ": "y", "ý": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
            "đ": "d",
        }
        for src, dst in replacements.items():
            text = text.replace(src, dst)
        return text
