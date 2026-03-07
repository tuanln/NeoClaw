"""Progressive hint system with 4 levels."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class HintLevel(IntEnum):
    NUDGE = 1       # Gentle direction
    GUIDANCE = 2    # More specific
    EXPLICIT = 3    # Clear instruction
    SOLUTION = 4    # Full solution


@dataclass
class Hint:
    level: HintLevel
    message: str


# Hints per exercise
_HINTS: dict[str, list[Hint]] = {
    "c1_l1_e1": [
        Hint(HintLevel.NUDGE, "Think about what number represents 1 second..."),
        Hint(HintLevel.GUIDANCE, "The duration parameter takes a number in seconds."),
        Hint(HintLevel.EXPLICIT, "Replace ___ with 1.0 to move for 1 second."),
        Hint(HintLevel.SOLUTION, "move_left(duration=1.0)"),
    ],
    "c1_l1_e2": [
        Hint(HintLevel.NUDGE, "What function activates the magnet?"),
        Hint(HintLevel.GUIDANCE, "Use the grab() function to pick up objects."),
        Hint(HintLevel.EXPLICIT, "Replace ___ with grab()"),
        Hint(HintLevel.SOLUTION, "grab()"),
    ],
    "c1_l2_e1": [
        Hint(HintLevel.NUDGE, "Speed is a decimal number between 0 and 1..."),
        Hint(HintLevel.GUIDANCE, "Try a value like 0.5 for half speed."),
        Hint(HintLevel.EXPLICIT, "Replace ___ with 0.5 (or any value 0.0-1.0)."),
        Hint(HintLevel.SOLUTION, "speed = 0.5"),
    ],
    "c1_l2_e2": [
        Hint(HintLevel.NUDGE, "What's a fast speed value?"),
        Hint(HintLevel.GUIDANCE, "Fast should be higher than slow (0.3). Try close to 1.0."),
        Hint(HintLevel.EXPLICIT, "Replace ___ with 1.0 for maximum speed."),
        Hint(HintLevel.SOLUTION, "fast = 1.0"),
    ],
    "c1_l3_e1": [
        Hint(HintLevel.NUDGE, "How many times should the zigzag repeat?"),
        Hint(HintLevel.GUIDANCE, "The description says 3 times."),
        Hint(HintLevel.EXPLICIT, "Replace ___ with 3"),
        Hint(HintLevel.SOLUTION, "for i in range(3):"),
    ],
    "c1_l3_e2": [
        Hint(HintLevel.NUDGE, "What should you divide by to get values from 0.2 to 1.0?"),
        Hint(HintLevel.GUIDANCE, "If i goes 0-4, then (i+1)/? should give 0.2, 0.4, ..., 1.0"),
        Hint(HintLevel.EXPLICIT, "Replace ___ with 5 so speed goes from 0.2 to 1.0"),
        Hint(HintLevel.SOLUTION, "speed = (i + 1) / 5"),
    ],
    "c1_l4_e1": [
        Hint(HintLevel.NUDGE, "What function activates the magnet?"),
        Hint(HintLevel.GUIDANCE, "Use grab() inside the if block."),
        Hint(HintLevel.EXPLICIT, "Replace ___ with grab()"),
        Hint(HintLevel.SOLUTION, "    grab()"),
    ],
    "c1_l5_e1": [
        Hint(HintLevel.NUDGE, "How do you get the positive version of a negative number?"),
        Hint(HintLevel.GUIDANCE, "Use abs() to convert negative duration to positive."),
        Hint(HintLevel.EXPLICIT, "Replace ___ with abs(x_duration)"),
        Hint(HintLevel.SOLUTION, "move_left(duration=abs(x_duration))"),
    ],
    "c1_l6_e1": [
        Hint(HintLevel.NUDGE, "What needs to happen between positioning and grabbing?"),
        Hint(HintLevel.GUIDANCE, "Step 2: lower the claw. Step 6: release the object."),
        Hint(HintLevel.EXPLICIT, "Step 2: move_down(duration=2.0) / Step 6: release()"),
        Hint(HintLevel.SOLUTION, "    move_down(duration=2.0)\n    ...\n    release()"),
    ],
}


class HintManager:
    """Manages hint progression per student per exercise."""

    def __init__(self):
        self._hint_indices: dict[str, int] = {}  # exercise_id → current level

    def get_hint(self, exercise_id: str) -> Hint | None:
        """Get the next hint for an exercise, advancing the level."""
        hints = _HINTS.get(exercise_id)
        if not hints:
            return None

        idx = self._hint_indices.get(exercise_id, 0)
        if idx >= len(hints):
            return hints[-1]  # Return solution repeatedly

        hint = hints[idx]
        self._hint_indices[exercise_id] = idx + 1
        return hint

    def reset(self, exercise_id: str) -> None:
        """Reset hint progression for an exercise."""
        self._hint_indices.pop(exercise_id, None)

    def reset_all(self) -> None:
        """Reset all hint progressions."""
        self._hint_indices.clear()

    def current_level(self, exercise_id: str) -> HintLevel:
        """Get current hint level for an exercise."""
        idx = self._hint_indices.get(exercise_id, 0)
        hints = _HINTS.get(exercise_id, [])
        if not hints or idx >= len(hints):
            return HintLevel.SOLUTION
        return hints[idx].level
