"""Student progress and usage analytics."""
from __future__ import annotations


from neoclaw.analytics.data_logger import DataLogger
from neoclaw.education.progress_tracker import ProgressTracker


class UsageAnalytics:
    """Analyzes student usage patterns and progress."""

    def __init__(self, data_logger: DataLogger, progress_tracker: ProgressTracker):
        self._logger = data_logger
        self._tracker = progress_tracker

    def get_summary(self) -> dict:
        """Get overall usage summary."""
        progress = self._tracker.get_progress()
        completed = sum(1 for e in progress.exercises.values() if e.completed)
        total = len(progress.exercises)

        return {
            "student_id": progress.student_id,
            "total_exercises": total,
            "completed_exercises": completed,
            "completion_rate": self._tracker.get_completion_rate(),
            "total_code_runs": progress.total_code_runs,
            "skill_levels": progress.skill_levels,
            "next_exercise": self._tracker.get_next_exercise(),
        }

    def get_exercise_stats(self, exercise_id: str) -> dict:
        """Get stats for a specific exercise."""
        progress = self._tracker.get_progress()
        ep = progress.exercises.get(exercise_id)

        if ep is None:
            return {"exercise_id": exercise_id, "status": "not_started"}

        return {
            "exercise_id": exercise_id,
            "completed": ep.completed,
            "attempts": ep.attempts,
            "best_score": ep.best_score,
            "hints_used": ep.hints_used,
        }

    def get_skill_radar(self) -> dict[str, int]:
        """Get skill levels for radar chart visualization."""
        progress = self._tracker.get_progress()
        all_concepts = [
            "import", "function_call", "variables", "float",
            "for_loop", "range", "if_else", "def", "parameters",
        ]
        return {
            concept: progress.skill_levels.get(concept, 0)
            for concept in all_concepts
        }

    def get_activity_timeline(self, days: int = 7) -> list[dict]:
        """Get activity data for timeline chart."""
        import time
        start = time.time() - days * 86400
        events = self._logger.query_events(limit=1000)
        return [e for e in events if e["timestamp"] >= start]
