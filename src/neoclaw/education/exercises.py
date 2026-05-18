"""Exercise validation and execution."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from neoclaw.agent.code_executor import ExecutionResult, execute_student_code
from neoclaw.education.curriculum import get_exercise


@dataclass
class ExerciseResult:
    """Result of validating a student's exercise attempt."""
    exercise_id: str
    passed: bool
    execution: ExecutionResult
    feedback: str
    concepts_demonstrated: list[str] = field(default_factory=list)
    score: int = 0  # 0-100


def validate_exercise(exercise_id: str, student_code: str) -> ExerciseResult:
    """Validate student code against an exercise's requirements."""
    exercise = get_exercise(exercise_id)
    if exercise is None:
        return ExerciseResult(
            exercise_id=exercise_id,
            passed=False,
            execution=ExecutionResult(success=False, stderr="Exercise not found"),
            feedback="Exercise not found.",
        )

    # Execute the code
    result = execute_student_code(student_code)

    # Check for blanks still present
    if "___" in student_code:
        return ExerciseResult(
            exercise_id=exercise_id,
            passed=False,
            execution=result,
            feedback="Please fill in all the blanks (___) in the code.",
        )

    # Check execution success
    if not result.success:
        return ExerciseResult(
            exercise_id=exercise_id,
            passed=False,
            execution=result,
            feedback=f"Code error: {result.stderr}",
        )

    # Check concepts demonstrated
    concepts = _detect_concepts(student_code)
    missing = [c for c in exercise.expected_concepts if c not in concepts]

    if missing:
        feedback = f"Good try! But you need to demonstrate: {', '.join(missing)}"
        passed = False
        score = max(0, 100 - len(missing) * 20)
    else:
        feedback = "Excellent! All concepts demonstrated."
        passed = True
        score = 100

    # Bonus for command count (efficiency)
    if result.commands and passed:
        if len(result.commands) <= 5:
            score = min(100, score + 10)
            feedback += " Very efficient!"

    return ExerciseResult(
        exercise_id=exercise_id,
        passed=passed,
        execution=result,
        feedback=feedback,
        concepts_demonstrated=concepts,
        score=score,
    )


def _detect_concepts(code: str) -> list[str]:
    """Detect Python concepts used in student code."""
    concepts = []

    if re.search(r"^import\s|^from\s", code, re.MULTILINE):
        concepts.append("import")
    if re.search(r"\w+\(", code):
        concepts.append("function_call")
    if re.search(r"^\w+\s*=\s*", code, re.MULTILINE):
        concepts.append("variables")
    if re.search(r"\d+\.\d+", code):
        concepts.append("float")
    if re.search(r"for\s+\w+\s+in\s+", code):
        concepts.append("for_loop")
    if re.search(r"range\(", code):
        concepts.append("range")
    if re.search(r"\bif\b", code):
        concepts.append("if_else")
    if re.search(r"\bdef\s+\w+", code):
        concepts.append("def")
    if re.search(r"def\s+\w+\([^)]+\)", code):
        concepts.append("parameters")
    if re.search(r"\breturn\b", code):
        concepts.append("return")
    if re.search(r"\babs\(", code):
        concepts.append("abs")
    if re.search(r"\bnot\b|\bTrue\b|\bFalse\b", code):
        concepts.append("boolean")
    if re.search(r"\[.+\]", code):
        concepts.append("dict_access")
    if re.search(r'f["\']', code):
        concepts.append("f-string")
    if re.search(r"\bwhile\b", code):
        concepts.append("while_loop")

    return concepts
