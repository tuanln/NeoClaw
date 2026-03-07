"""Tests for code executor."""
from neoclaw.agent.code_executor import execute_student_code, parse_claw_output_line
from neoclaw.agent.models import ClawCommandType


def test_execute_simple_code():
    code = 'from claw import *\nmove_left(duration=1.0)\n'
    result = execute_student_code(code)
    assert result.success is True
    assert len(result.commands) == 1
    assert result.commands[0].command_type == ClawCommandType.MOVE_LEFT


def test_execute_multiple_commands():
    code = 'from claw import *\nmove_left()\nmove_down()\ngrab()\n'
    result = execute_student_code(code)
    assert result.success is True
    assert len(result.commands) == 3


def test_execute_with_error():
    code = 'from claw import *\nraise ValueError("test")\n'
    result = execute_student_code(code)
    assert result.success is False
    assert "ValueError" in result.stderr


def test_execute_with_print():
    code = 'from claw import *\nprint("hello")\nmove_left()\n'
    result = execute_student_code(code)
    assert result.success is True
    assert "hello" in result.stdout
    assert len(result.commands) == 1


def test_parse_output_line():
    line = '__NEO_CLAW__:{"cmd": "MOVE_LEFT", "kwargs": {"duration": 1.0}}'
    cmd = parse_claw_output_line(line)
    assert cmd is not None
    assert cmd.command_type == ClawCommandType.MOVE_LEFT
    assert cmd.kwargs["duration"] == 1.0


def test_parse_invalid_line():
    assert parse_claw_output_line("just a normal line") is None
    assert parse_claw_output_line("__NEO_CLAW__:invalid json") is None
