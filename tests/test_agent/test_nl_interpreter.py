"""Tests for natural language interpreter."""
from neoclaw.agent.models import ClawCommandType
from neoclaw.agent.nl_interpreter import NLInterpreter


def test_basic_english():
    nl = NLInterpreter()
    cmds = nl.interpret("move left")
    assert len(cmds) >= 1
    assert cmds[0].command_type == ClawCommandType.MOVE_LEFT


def test_basic_vietnamese():
    nl = NLInterpreter()
    cmds = nl.interpret("sang phai")
    assert len(cmds) >= 1
    assert cmds[0].command_type == ClawCommandType.MOVE_RIGHT


def test_grab_command():
    nl = NLInterpreter()
    cmds = nl.interpret("grab")
    assert len(cmds) == 1
    assert cmds[0].command_type == ClawCommandType.GRAB


def test_stop_command():
    nl = NLInterpreter()
    cmds = nl.interpret("stop")
    assert len(cmds) == 1
    assert cmds[0].command_type == ClawCommandType.EMERGENCY_STOP


def test_duration_extraction():
    nl = NLInterpreter()
    cmds = nl.interpret("move left 2 seconds")
    assert len(cmds) >= 1
    assert cmds[0].kwargs.get("duration") == 2.0


def test_unknown_input():
    nl = NLInterpreter()
    cmds = nl.interpret("xyzzy foobar")
    assert len(cmds) == 0
