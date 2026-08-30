"""The AI tutor must be briefed on the robot that exists.

The prompts used to describe the gantry API (move_left/move_up/grab), so the
tutor would confidently teach a child functions the sandbox does not have and
the robot cannot perform — the most expensive kind of drift, because it looks
authoritative.
"""
from __future__ import annotations

import ast
import re

from neoclaw.agent import prompt_templates
from neoclaw.agent.code_executor import generate_claw_wrapper_code
from neoclaw.hardware.dispatch import COMMAND_NAMES
from neoclaw.hardware.models import ClawCommandType

GANTRY_VERBS = {"move_left", "move_right", "move_up", "move_down", "grab"}


def _all_prompts() -> dict[str, str]:
    return {
        name: value
        for name, value in vars(prompt_templates).items()
        if name.isupper() and isinstance(value, str)
    }


def _sandbox_names() -> set[str]:
    wrapper = generate_claw_wrapper_code()
    start = wrapper.index("for _name in (")
    end = wrapper.index("):", start)
    return set(ast.literal_eval(wrapper[start + len("for _name in ") : end + 1]))


def test_no_prompt_mentions_a_gantry_verb():
    for name, text in _all_prompts().items():
        found = {verb for verb in GANTRY_VERBS if re.search(rf"\b{verb}\b", text)}
        assert found == set(), f"{name} still teaches: {found}"


def test_every_function_named_in_a_prompt_exists_in_the_sandbox():
    known = _sandbox_names()
    for name, text in _all_prompts().items():
        mentioned = set(re.findall(r"\b([a-z_]{3,})\(", text))
        unknown = mentioned - known - {"range", "print", "def", "abs"}
        assert unknown == set(), f"{name} names functions that do not exist: {unknown}"


def test_nl_interpreter_prompt_lists_only_real_command_types():
    text = prompt_templates.CLAW_NL_INTERPRETER_SYSTEM
    mentioned = set(re.findall(r"\b([A-Z][A-Z_]{2,})\b", text))
    real = {c.name for c in ClawCommandType} | {"ONLY", "JSON"}
    assert mentioned <= real, f"prompt invents commands: {mentioned - real}"


def test_nl_interpreter_prompt_covers_the_moves_kids_ask_for():
    text = prompt_templates.CLAW_NL_INTERPRETER_SYSTEM
    for command in ("FORWARD", "STRAFE_LEFT", "TURN_RIGHT", "PICK_UP", "EMERGENCY_STOP"):
        assert command in text, f"NL prompt never mentions {command}"
    assert set(COMMAND_NAMES)  # sanity: the vocabulary is not empty
