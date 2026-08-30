"""Interactive robot control from the terminal."""
from __future__ import annotations

import click

from neoclaw.hardware.dispatch import COMMAND_NAMES, apply_command, command_from_name

# Short aliases so the prompt stays quick to type.
_ALIASES = {
    "w": "forward",
    "s": "backward",
    "a": "strafe_left",
    "d": "strafe_right",
    "q": "turn_left",
    "e": "turn_right",
    "g": "grip",
    "r": "release",
    " ": "stop",
}


@click.command()
@click.option("--simulator", is_flag=True, help="Chay khong can phan cung")
@click.option("--speed", default=60, help="Toc do 0-100")
def control(simulator: bool, speed: int):
    """Dieu khien ClawBot bang ban phim.

    Go ten lenh (forward, strafe_left, grip...) hoac phim tat w/a/s/d/q/e/g/r.
    Go `state` de xem trang thai, `quit` de thoat.
    """
    from neoclaw.hardware.claw_robot import ClawRobot

    robot = ClawRobot.create(simulator=simulator)
    click.echo(f"ClawBot san sang (simulator={simulator}). Lenh: {', '.join(sorted(COMMAND_NAMES))}")

    try:
        while True:
            raw = click.prompt("claw", prompt_suffix="> ", default="", show_default=False)
            name = _ALIASES.get(raw.strip(), raw.strip())

            if name in ("quit", "exit"):
                break
            if not name:
                continue
            if name == "state":
                click.echo(robot.get_state().to_dict())
                continue

            try:
                command = command_from_name(name, speed=speed)
            except KeyError as exc:
                click.echo(str(exc))
                continue

            result = apply_command(robot, command)
            if result is not None:
                click.echo(result)
    finally:
        robot.shutdown()
