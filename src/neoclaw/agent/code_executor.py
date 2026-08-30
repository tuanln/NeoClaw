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
    """Generate the `claw` module a student's code imports.

    Student code runs in a separate process and never touches the serial port:
    each call prints one `__NEO_CLAW__:` line, and the parent turns those lines
    into ClawCommand objects for neoclaw.hardware.dispatch. The verbs here are
    the robot's own — anything callable in the sandbox has a handler in
    COMMAND_HANDLERS, and a test enforces that.
    """
    max_cmds = get_settings().execution.max_claw_commands
    return textwrap.dedent(f'''\
        import sys
        import json
        import time
        import types

        _MAX_CLAW_COMMANDS = {max_cmds}

        class _NeoClawProxy:
            """Proxy that captures robot commands and prints them as JSON."""

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

            # ── Di chuyen (de omni) ──

            def forward(self, speed=60, duration=1.0):
                """Di tien."""
                self._emit("FORWARD", speed=speed, duration=duration)

            def backward(self, speed=60, duration=1.0):
                """Di lui."""
                self._emit("BACKWARD", speed=speed, duration=duration)

            def strafe_left(self, speed=60, duration=1.0):
                """Di ngang sang trai (khong xoay than xe)."""
                self._emit("STRAFE_LEFT", speed=speed, duration=duration)

            def strafe_right(self, speed=60, duration=1.0):
                """Di ngang sang phai (khong xoay than xe)."""
                self._emit("STRAFE_RIGHT", speed=speed, duration=duration)

            def turn_left(self, speed=50, duration=0.5):
                """Xoay trai tai cho."""
                self._emit("TURN_LEFT", speed=speed, duration=duration)

            def turn_right(self, speed=50, duration=0.5):
                """Xoay phai tai cho."""
                self._emit("TURN_RIGHT", speed=speed, duration=duration)

            def stop(self):
                """Dung banh xe."""
                self._emit("STOP")

            # ── Tay gap ──

            def arm_pose(self, pose="rest"):
                """Dat tay vao mot tu the: home, reach_forward, reach_down, carry, rest."""
                self._emit("ARM_POSE", pose=pose)

            def grip(self):
                """Dong kep."""
                self._emit("GRIP")

            def release(self):
                """Mo kep."""
                self._emit("RELEASE")

            def pick_up(self):
                """Ha tay, gap, roi nang len."""
                self._emit("PICK_UP")

            def put_down(self):
                """Ha tay roi tha ra."""
                self._emit("PUT_DOWN")

            def sweep(self):
                """Gat vat the bang can gat."""
                self._emit("SWEEP")

            # ── Trang thai ──

            def get_state(self):
                """Doc trang thai robot.

                Trong sandbox, tien trinh con khong giu cong serial nen khong
                doc duoc trang thai that — tra ve mot ban do co du cac khoa ma
                bai hoc dung, de code cua hoc sinh chay duoc o ca hai noi.
                """
                self._emit("GET_STATE")
                return {{
                    "gripper_holding": False,
                    "moving": False,
                    "heading": 0.0,
                    "wheels": {{
                        "FRONT_LEFT": 0, "FRONT_RIGHT": 0,
                        "REAR_LEFT": 0, "REAR_RIGHT": 0,
                    }},
                }}

        _proxy = _NeoClawProxy()
        _claw_module = types.ModuleType("claw")
        for _name in (
            "forward", "backward", "strafe_left", "strafe_right",
            "turn_left", "turn_right", "stop",
            "arm_pose", "grip", "release", "pick_up", "put_down", "sweep",
            "get_state",
        ):
            setattr(_claw_module, _name, getattr(_proxy, _name))
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
