"""Education/curriculum API routes."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SubmitCodeRequest(BaseModel):
    exercise_id: str
    code: str


@router.get("/lessons")
async def list_lessons(phase: int = 1):
    """Get all lessons for a phase."""
    from neoclaw.education.curriculum import get_lessons
    lessons = get_lessons(phase)
    return {
        "lessons": [
            {
                "id": lesson.id,
                "title": lesson.title,
                "description": lesson.description,
                "concepts": lesson.concepts,
                "exercises": [
                    {"id": e.id, "title": e.title, "difficulty": e.difficulty}
                    for e in lesson.exercises
                ],
            }
            for lesson in lessons
        ]
    }


@router.get("/exercise/{exercise_id}")
async def get_exercise(exercise_id: str):
    """Get exercise details with starter code."""
    from neoclaw.education.curriculum import get_exercise
    ex = get_exercise(exercise_id)
    if ex is None:
        return {"error": "Exercise not found"}
    return {
        "id": ex.id,
        "title": ex.title,
        "description": ex.description,
        "starter_code": ex.starter_code,
        "difficulty": ex.difficulty,
        "concepts": ex.expected_concepts,
    }


@router.post("/submit")
async def submit_exercise(req: SubmitCodeRequest):
    """Submit code for an exercise and get feedback."""
    from neoclaw.education.exercises import validate_exercise
    result = validate_exercise(req.exercise_id, req.code)
    return {
        "passed": result.passed,
        "score": result.score,
        "feedback": result.feedback,
        "concepts_demonstrated": result.concepts_demonstrated,
        "stdout": result.execution.stdout,
        "stderr": result.execution.stderr,
    }


@router.get("/progress")
async def get_progress():
    """Get student progress."""
    from neoclaw.education.progress_tracker import ProgressTracker
    tracker = ProgressTracker()
    progress = tracker.get_progress()
    return {
        "completion_rate": tracker.get_completion_rate(),
        "next_exercise": tracker.get_next_exercise(),
        "exercises": {
            eid: {
                "completed": ep.completed,
                "attempts": ep.attempts,
                "best_score": ep.best_score,
            }
            for eid, ep in progress.exercises.items()
        },
    }
