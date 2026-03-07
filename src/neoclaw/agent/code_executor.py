"""Subprocess sandbox for executing student code with claw proxy."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field

from neoclaw.agent.models import ClawCommand, ClawCommandType
from neoclaw.config.settings import get_settings

logger = logging.getLogger(__name__)

_COMMAND_PREFIX = "__NEO_CLAW__:"
_LIMIT_PREFIX = "__NEO_CLAW_LIMIT__:"


def generate_claw_wrapper_code() -> str:
    """Generate Python code that wraps the claw module for student code.

    Student code imports `claw` → proxy captures calls → JSON on stdout.
    """
    max_cmds = get_settings().execution.max_claw_commands
    return textwrap.dedent(f'''\
        import sys
        import json
        import time
        import types

        _MAX_CLAW_COMMANDS = {max_cmds}

        class _NeoClawProxy:
            """Proxy that captures claw commands and prints them as JSON."""

            def __init__(self):
                self._cmd_count = 0

            def _emit(self, cmd_type, **kwargs):
                self._cmd_count += 1
                if self._cmd_count > _MAX_CLAW_COMMANDS:
                    if self._cmd_count == _MAX_CLAW_COMMANDS + 1:
                        print(f"__NEO_CLAW_LIMIT__:{{_MAX_CLAW_COMMANDS}}", flush=True)
                        print(f"Error: Too many commands! Limit {{_MAX_CLAW_COMMANDS}}.",
                              file=sys.stderr, flush=True)
                    sys.exit(1)
                data = {{"cmd": cmd_type, "kwargs": dict(kwargs)}}
                print(f"__NEO_CLAW__:{{json.dumps(data)}}", flush=True)
                time.sleep(0.01)

            def move_left(self, duration=0.5, speed=1.0):
                """Move claw left."""
                self._emit("MOVE_LEFT", duration=duration, speed=speed)

            def move_right(self, duration=0.5, speed=1.0):
                """Move claw right."""
                self._emit("MOVE_RIGHT", duration=duration, speed=speed)

            def move_forward(self, duration=0.5, speed=1.0):
                """Move claw forward."""
                self._emit("MOVE_FORWARD", duration=duration, speed=speed)

            def move_backward(self, duration=0.5, speed=1.0):
                """Move claw backward."""
                self._emit("MOVE_BACKWARD", duration=duration, speed=speed)

            def move_up(self, duration=0.5, speed=1.0):
                """Move claw up."""
                self._emit("MOVE_UP", duration=duration, speed=speed)

            def move_down(self, duration=0.5, speed=1.0):
                """Move claw down."""
                self._emit("MOVE_DOWN", duration=duration, speed=speed)

            def grab(self):
                """Activate electromagnet."""
                self._emit("GRAB")

            def release(self):
                """Deactivate electromagnet."""
                self._emit("RELEASE")

            def get_state(self):
                """Get claw state (returns placeholder in sandbox)."""
                self._emit("GET_STATE")
                return {{"magnet": False, "position": "unknown"}}

        _proxy = _NeoClawProxy()
        _claw_module = types.ModuleType("claw")
        _claw_module.move_left = _proxy.move_left
        _claw_module.move_right = _proxy.move_right
        _claw_module.move_forward = _proxy.move_forward
        _claw_module.move_backward = _proxy.move_backward
        _claw_module.move_up = _proxy.move_up
        _claw_module.move_down = _proxy.move_down
        _claw_module.grab = _proxy.grab
        _claw_module.release = _proxy.release
        _claw_module.get_state = _proxy.get_state
        sys.modules["claw"] = _claw_module
    ''')


@dataclass
class ExecutionResult:
    """Result of executing student code."""
    success: bool
    commands: list[ClawCommand] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False


def parse_claw_output_line(line: str) -> ClawCommand | None:
    """Parse a claw command from the proxy's stdout output."""
    if not line.startswith(_COMMAND_PREFIX):
        return None

    try:
        data = json.loads(line[len(_COMMAND_PREFIX):])
        cmd_name = data.get("cmd", "")
        cmd_type = ClawCommandType[cmd_name]
        return ClawCommand(command_type=cmd_type, kwargs=data.get("kwargs", {}))
    except (json.JSONDecodeError, KeyError):
        return None


def execute_student_code(code: str) -> ExecutionResult:
    """Execute student code in a subprocess sandbox.

    The code is prepended with the claw wrapper so `from claw import *` works.
    Commands are captured from stdout and returned.
    """
    settings = get_settings().execution
    wrapper = generate_claw_wrapper_code()
    full_code = wrapper + "\n" + code

    try:
        proc = subprocess.run(
            [sys.executable, "-c", full_code],
            capture_output=True,
            text=True,
            timeout=settings.timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            success=False,
            stderr=f"Code timed out after {settings.timeout_seconds}s",
            timed_out=True,
        )

    # Parse commands from stdout
    commands = []
    user_output_lines = []
    for line in proc.stdout.splitlines():
        cmd = parse_claw_output_line(line)
        if cmd is not None:
            commands.append(cmd)
        elif not line.startswith(_LIMIT_PREFIX):
            user_output_lines.append(line)

    return ExecutionResult(
        success=proc.returncode == 0,
        commands=commands,
        stdout="\n".join(user_output_lines),
        stderr=proc.stderr,
        exit_code=proc.returncode,
    )
