"""Student progress tracking."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ExerciseProgress:
    """Progress for a single exercise."""
    exercise_id: str
    completed: bool = False
    attempts: int = 0
    best_score: int = 0
    hints_used: int = 0
    completed_at: Optional[float] = None


@dataclass
class StudentProgress:
    """Overall student progress."""
    student_id: str = "default"
    exercises: dict[str, ExerciseProgress] = field(default_factory=dict)
    skill_levels: dict[str, int] = field(default_factory=dict)  # concept → level (1-5)
    total_code_runs: int = 0
    total_time_seconds: float = 0.0
    started_at: float = field(default_factory=time.time)


class ProgressTracker:
    """Tracks and persists student progress."""

    def __init__(self, save_path: Optional[Path] = None):
        self._save_path = save_path or Path.home() / ".neoclaw" / "progress.json"
        self._progress = self._load()

    def record_attempt(
        self, exercise_id: str, passed: bool, score: int, hints_used: int = 0
    ) -> ExerciseProgress:
        """Record an exercise attempt."""
        if exercise_id not in self._progress.exercises:
            self._progress.exercises[exercise_id] = ExerciseProgress(exercise_id=exercise_id)

        ep = self._progress.exercises[exercise_id]
        ep.attempts += 1
        ep.hints_used += hints_used
        ep.best_score = max(ep.best_score, score)

        if passed and not ep.completed:
            ep.completed = True
            ep.completed_at = time.time()

        self._progress.total_code_runs += 1
        self._save()
        return ep

    def update_skill(self, concept: str, level: int) -> None:
        """Update skill level for a concept (1-5)."""
        level = max(1, min(5, level))
        self._progress.skill_levels[concept] = level
        self._save()

    def get_progress(self) -> StudentProgress:
        return self._progress

    def get_completion_rate(self) -> float:
        """Get percentage of exercises completed."""
        if not self._progress.exercises:
            return 0.0
        completed = sum(1 for e in self._progress.exercises.values() if e.completed)
        return completed / len(self._progress.exercises) * 100

    def get_next_exercise(self) -> Optional[str]:
        """Suggest the next exercise to work on."""
        from neoclaw.education.curriculum import CLAW_LESSONS

        for lesson in CLAW_LESSONS:
            for exercise in lesson.exercises:
                ep = self._progress.exercises.get(exercise.id)
                if ep is None or not ep.completed:
                    return exercise.id
        return None

    def _load(self) -> StudentProgress:
        if self._save_path.exists():
            try:
                data = json.loads(self._save_path.read_text())
                progress = StudentProgress()
                progress.student_id = data.get("student_id", "default")
                progress.total_code_runs = data.get("total_code_runs", 0)
                progress.total_time_seconds = data.get("total_time_seconds", 0.0)
                progress.started_at = data.get("started_at", time.time())
                progress.skill_levels = data.get("skill_levels", {})

                for eid, edata in data.get("exercises", {}).items():
                    progress.exercises[eid] = ExerciseProgress(
                        exercise_id=eid,
                        completed=edata.get("completed", False),
                        attempts=edata.get("attempts", 0),
                        best_score=edata.get("best_score", 0),
                        hints_used=edata.get("hints_used", 0),
                        completed_at=edata.get("completed_at"),
                    )
                return progress
            except (json.JSONDecodeError, KeyError):
                pass
        return StudentProgress()

    def _save(self) -> None:
        self._save_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "student_id": self._progress.student_id,
            "total_code_runs": self._progress.total_code_runs,
            "total_time_seconds": self._progress.total_time_seconds,
            "started_at": self._progress.started_at,
            "skill_levels": self._progress.skill_levels,
            "exercises": {
                eid: {
                    "completed": ep.completed,
                    "attempts": ep.attempts,
                    "best_score": ep.best_score,
                    "hints_used": ep.hints_used,
                    "completed_at": ep.completed_at,
                }
                for eid, ep in self._progress.exercises.items()
            },
        }
        self._save_path.write_text(json.dumps(data, indent=2))
