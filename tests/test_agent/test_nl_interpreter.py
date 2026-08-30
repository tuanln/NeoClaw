"""Natural language → ClawBot commands.

The robot is an omni base with an arm: it goes forward, sideways, turns, grips.
It has no Z axis — "lên"/"xuống" belonged to the gantry claw machine and no
longer parse to movement.
"""
from neoclaw.agent.models import ClawCommandType
from neoclaw.agent.nl_interpreter import NLInterpreter


def test_english_forward():
    nl = NLInterpreter()
    cmds = nl.interpret("go forward")
    assert cmds[0].command_type == ClawCommandType.FORWARD


def test_vietnamese_forward_without_diacritics():
    nl = NLInterpreter()
    cmds = nl.interpret("di tien")
    assert cmds[0].command_type == ClawCommandType.FORWARD


def test_vietnamese_with_diacritics():
    """Kids type with a Vietnamese keyboard; both spellings must work."""
    nl = NLInterpreter()
    cmds = nl.interpret("đi tiến")
    assert cmds[0].command_type == ClawCommandType.FORWARD


def test_strafe_is_distinct_from_turning():
    nl = NLInterpreter()
    assert nl.interpret("sang trai")[0].command_type == ClawCommandType.STRAFE_LEFT
    assert nl.interpret("xoay trai")[0].command_type == ClawCommandType.TURN_LEFT


def test_grip_and_release():
    nl = NLInterpreter()
    assert nl.interpret("gap")[0].command_type == ClawCommandType.GRIP
    assert nl.interpret("tha ra")[0].command_type == ClawCommandType.RELEASE


def test_pick_up_is_the_combined_action():
    nl = NLInterpreter()
    assert nl.interpret("nhat len")[0].command_type == ClawCommandType.PICK_UP


def test_sweep():
    nl = NLInterpreter()
    assert nl.interpret("gat di")[0].command_type == ClawCommandType.SWEEP


def test_stop_command():
    nl = NLInterpreter()
    cmds = nl.interpret("dung lai")
    assert cmds[0].command_type == ClawCommandType.EMERGENCY_STOP


def test_duration_extraction():
    nl = NLInterpreter()
    cmds = nl.interpret("di tien 2 giay")
    assert cmds[0].kwargs.get("duration") == 2.0


def test_english_duration_still_parses():
    nl = NLInterpreter()
    cmds = nl.interpret("forward 3 seconds")
    assert cmds[0].kwargs.get("duration") == 3.0


def test_unknown_input():
    nl = NLInterpreter()
    assert nl.interpret("xyzzy foobar") == []


def test_gantry_vocabulary_is_gone():
    """'lên'/'xuống' used to mean the Z axis; the robot has no such axis."""
    nl = NLInterpreter()
    assert nl.interpret("di len") == []
