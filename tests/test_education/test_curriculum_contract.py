"""The curriculum must teach the robot that exists.

This is the test that would have caught the original drift: the lessons taught
`move_left()`/`grab()` — the arcade gantry's API — for months after the product
became an omni robot with an arm, and nothing failed. Every name a lesson puts
in front of a child is now checked against the sandbox the child runs in.
"""
from __future__ import annotations

import ast

import pytest

from neoclaw.agent.code_executor import generate_claw_wrapper_code
from neoclaw.education.curriculum import get_lessons
from neoclaw.education.hints import get_hints


def _sandbox_names() -> set[str]:
    """Names the generated `claw` module actually exposes to student code."""
    wrapper = generate_claw_wrapper_code()
    start = wrapper.index("for _name in (")
    end = wrapper.index("):", start)
    return set(ast.literal_eval(wrapper[start + len("for _name in ") : end + 1]))


def _called_names(code: str) -> set[str]:
    """Function names a snippet calls but does not define itself.

    Lessons 5 and 6 teach students to write their own functions and call them,
    so a name defined in the same snippet is the student's, not the robot's.
    """
    cleaned = code.replace("___", "1")
    try:
        tree = ast.parse(cleaned)
    except SyntaxError:
        return set()
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    defined = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    return called - defined


BUILTINS = {"print", "range", "len", "int", "float", "str", "input", "abs", "round"}

ALL_EXERCISES = [ex for lesson in get_lessons() for ex in lesson.exercises]


@pytest.mark.parametrize("exercise", ALL_EXERCISES, ids=lambda ex: ex.id)
def test_starter_code_only_calls_verbs_the_robot_has(exercise):
    unknown = _called_names(exercise.starter_code) - _sandbox_names() - BUILTINS
    assert unknown == set(), f"{exercise.id} teaches names the robot does not have: {unknown}"


@pytest.mark.parametrize("exercise", ALL_EXERCISES, ids=lambda ex: ex.id)
def test_solution_hint_only_calls_verbs_the_robot_has(exercise):
    """The level-4 hint is a worked solution; it must run on the real robot too."""
    for hint in get_hints(exercise.id):
        if int(hint.level) != 4:
            continue
        unknown = _called_names(hint.message) - _sandbox_names() - BUILTINS
        assert unknown == set(), f"{exercise.id} hint uses: {unknown}"


def test_every_exercise_has_a_full_hint_ladder():
    for exercise in ALL_EXERCISES:
        levels = sorted(int(h.level) for h in get_hints(exercise.id))
        assert levels == [1, 2, 3, 4], f"{exercise.id} hint levels: {levels}"


def test_lessons_are_written_in_vietnamese():
    """Audience is Vietnamese primary-school kids; lesson text is their language."""
    marker_words = ("robot", "xe", "tay", "em", "hãy", "của", "đi")
    for lesson in get_lessons():
        text = (lesson.title + " " + lesson.description).lower()
        assert any(word in text for word in marker_words), f"lesson {lesson.id}: {lesson.title}"


def test_expected_concepts_are_all_detectable():
    """A concept the validator cannot detect makes its exercise impossible to pass."""
    from neoclaw.education.exercises import _detect_concepts

    # Every branch of the detector, exercised by a snippet that triggers it.
    probe = (
        "from claw import *\n"
        "x = 1.5\n"
        "for i in range(3):\n"
        "    if not True:\n"
        "        print(f'{x}', abs(-1), [1][0])\n"
        "while False:\n"
        "    pass\n"
        "def f(a):\n"
        "    return a\n"
    )
    detectable = set(_detect_concepts(probe))

    for exercise in ALL_EXERCISES:
        undetectable = set(exercise.expected_concepts) - detectable
        assert undetectable == set(), (
            f"{exercise.id} can never pass — validator cannot detect: {undetectable}"
        )


def test_lesson_four_starter_code_runs_once_the_blank_is_filled():
    """A lesson that reads state must find the keys it reads in the sandbox."""
    from neoclaw.agent.code_executor import execute_student_code
    from neoclaw.education.curriculum import get_exercise

    exercise = get_exercise("c1_l4_e1")
    code = exercise.starter_code.replace("___", "grip()")

    result = execute_student_code(code)
    assert result.success is True, result.stderr
