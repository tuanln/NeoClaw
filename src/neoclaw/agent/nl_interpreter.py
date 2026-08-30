"""Natural language to claw command interpreter."""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from neoclaw.agent.models import ClawCommand, ClawCommandType

logger = logging.getLogger(__name__)

# Vietnamese/English keywords → ClawBot commands.
#
# Written for the robot the product ships: an omni base (forward/back, sideways,
# turn in place) plus a 4-DOF arm. There is no up/down — that was the gantry
# claw machine's Z axis, and "đi lên" now parses to nothing rather than to a
# move the robot cannot make.
#
# Text is lower-cased and stripped of diacritics before matching, so each
# Vietnamese phrase is written here without them and both spellings work.
# Longest phrases match first (see _keyword_parse), which is what keeps
# "xoay trai" from being eaten by "trai".
_KEYWORD_MAP: dict[str, ClawCommandType] = {
    # ── Đi thẳng ──
    "di tien": ClawCommandType.FORWARD,
    "tien len": ClawCommandType.FORWARD,
    "chay toi": ClawCommandType.FORWARD,
    "tien": ClawCommandType.FORWARD,
    "di lui": ClawCommandType.BACKWARD,
    "lui lai": ClawCommandType.BACKWARD,
    "lui": ClawCommandType.BACKWARD,

    # ── Đi ngang (đế omni) ──
    "sang trai": ClawCommandType.STRAFE_LEFT,
    "di ngang trai": ClawCommandType.STRAFE_LEFT,
    "qua trai": ClawCommandType.STRAFE_LEFT,
    "sang phai": ClawCommandType.STRAFE_RIGHT,
    "di ngang phai": ClawCommandType.STRAFE_RIGHT,
    "qua phai": ClawCommandType.STRAFE_RIGHT,

    # ── Xoay tại chỗ ──
    "xoay trai": ClawCommandType.TURN_LEFT,
    "quay trai": ClawCommandType.TURN_LEFT,
    "re trai": ClawCommandType.TURN_LEFT,
    "xoay phai": ClawCommandType.TURN_RIGHT,
    "quay phai": ClawCommandType.TURN_RIGHT,
    "re phai": ClawCommandType.TURN_RIGHT,

    # ── Tay gắp ──
    "nhat len": ClawCommandType.PICK_UP,
    "gap len": ClawCommandType.PICK_UP,
    "dat xuong": ClawCommandType.PUT_DOWN,
    "tha xuong": ClawCommandType.PUT_DOWN,
    "gap": ClawCommandType.GRIP,
    "kep lai": ClawCommandType.GRIP,
    "tha ra": ClawCommandType.RELEASE,
    "nha ra": ClawCommandType.RELEASE,
    "tha": ClawCommandType.RELEASE,

    # ── Cần gạt ──
    "gat di": ClawCommandType.SWEEP,
    "gat": ClawCommandType.SWEEP,

    # ── Dừng ──
    "dung lai": ClawCommandType.EMERGENCY_STOP,
    "dung": ClawCommandType.EMERGENCY_STOP,

    # ── English ──
    "go forward": ClawCommandType.FORWARD,
    "forward": ClawCommandType.FORWARD,
    "go backward": ClawCommandType.BACKWARD,
    "backward": ClawCommandType.BACKWARD,
    "strafe left": ClawCommandType.STRAFE_LEFT,
    "strafe right": ClawCommandType.STRAFE_RIGHT,
    "turn left": ClawCommandType.TURN_LEFT,
    "turn right": ClawCommandType.TURN_RIGHT,
    "pick up": ClawCommandType.PICK_UP,
    "put down": ClawCommandType.PUT_DOWN,
    "grip": ClawCommandType.GRIP,
    "grab": ClawCommandType.GRIP,
    "release": ClawCommandType.RELEASE,
    "drop": ClawCommandType.RELEASE,
    "sweep": ClawCommandType.SWEEP,
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
