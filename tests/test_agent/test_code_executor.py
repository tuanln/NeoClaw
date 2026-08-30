"""Student code runs in a sandbox that speaks the ClawBot vocabulary.

The sandbox used to expose the gantry verbs (move_left/move_up/grab) while the
robot on the desk was an omni base with an arm — a kid following the lesson
could not have driven the real machine. These tests pin the sandbox to the same
vocabulary the robot understands.
"""
from neoclaw.agent.code_executor import (
    execute_student_code,
    generate_claw_wrapper_code,
    parse_claw_output_line,
)
from neoclaw.agent.models import ClawCommandType
from neoclaw.hardware.dispatch import COMMAND_HANDLERS


def test_execute_simple_code():
    result = execute_student_code('from claw import *\nforward(duration=1.0)\n')
    assert result.success is True
    assert len(result.commands) == 1
    assert result.commands[0].command_type == ClawCommandType.FORWARD


def test_execute_multiple_commands():
    code = 'from claw import *\nforward()\nstrafe_left()\ngrip()\n'
    result = execute_student_code(code)
    assert result.success is True
    assert [c.command_type for c in result.commands] == [
        ClawCommandType.FORWARD,
        ClawCommandType.STRAFE_LEFT,
        ClawCommandType.GRIP,
    ]


def test_arm_pose_carries_its_argument():
    result = execute_student_code('from claw import *\narm_pose("reach_down")\n')
    assert result.commands[0].command_type == ClawCommandType.ARM_POSE
    assert result.commands[0].kwargs["pose"] == "reach_down"


def test_combined_actions_are_available():
    result = execute_student_code('from claw import *\npick_up()\nput_down()\nsweep()\n')
    assert [c.command_type for c in result.commands] == [
        ClawCommandType.PICK_UP,
        ClawCommandType.PUT_DOWN,
        ClawCommandType.SWEEP,
    ]


def test_execute_with_error():
    result = execute_student_code('from claw import *\nraise ValueError("test")\n')
    assert result.success is False
    assert "ValueError" in result.stderr


def test_execute_with_print():
    result = execute_student_code('from claw import *\nprint("hello")\nforward()\n')
    assert result.success is True
    assert "hello" in result.stdout
    assert len(result.commands) == 1


def test_parse_output_line():
    line = '__NEO_CLAW__:{"cmd": "FORWARD", "kwargs": {"duration": 1.0}}'
    cmd = parse_claw_output_line(line)
    assert cmd is not None
    assert cmd.command_type == ClawCommandType.FORWARD


def test_gantry_verbs_are_gone():
    """A lesson written against the old API must fail loudly, not silently."""
    result = execute_student_code('from claw import *\nmove_left()\n')
    assert result.success is False


def test_every_sandbox_verb_is_executable_on_the_robot():
    """Anything a kid can call must have a handler — no dead verbs in the sandbox."""
    wrapper = generate_claw_wrapper_code()
    emitted = {
        line.split('_emit("', 1)[1].split('"', 1)[0]
        for line in wrapper.splitlines()
        if "_emit(\"" in line
    }
    handled = {c.name for c in COMMAND_HANDLERS}
    assert emitted <= handled, f"sandbox emits verbs the robot cannot run: {emitted - handled}"
