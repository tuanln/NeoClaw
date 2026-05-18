"""neoclaw control — Direct claw control."""
from __future__ import annotations

import click


@click.command()
@click.option("--simulator", is_flag=True, help="Use simulator instead of real hardware")
@click.option("--speed", default=1.0, help="Motor speed (0.0-1.0)")
def control(simulator, speed):
    """Control the claw machine directly.

    Use arrow-like commands to move the claw.
    Type 'help' for available commands.
    """
    if simulator:
        click.echo("Starting claw simulator...")
        from neoclaw.hardware.simulator import ClawSimulator
        sim = ClawSimulator()
        claw = sim.machine
    else:
        click.echo("Connecting to hardware...")
        from neoclaw.hardware.claw_machine import ClawMachine
        claw = ClawMachine.create()
        sim = None

    click.echo("Claw ready! Type commands (left/right/up/down/forward/backward/grab/release/quit)")
    click.echo(f"Speed: {speed}")

    commands = {
        "left": lambda: claw.move_left(speed=speed),
        "right": lambda: claw.move_right(speed=speed),
        "up": lambda: claw.move_up(speed=speed),
        "down": lambda: claw.move_down(speed=speed),
        "forward": lambda: claw.move_forward(speed=speed),
        "backward": lambda: claw.move_backward(speed=speed),
        "grab": claw.grab,
        "release": claw.release,
        "state": lambda: click.echo(claw.get_state().to_dict()),
        "stop": claw.emergency_stop,
    }

    while True:
        try:
            cmd = click.prompt("claw", prompt_suffix="> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd in ("quit", "exit", "q"):
            break

        if cmd == "help":
            click.echo("Commands: " + ", ".join(commands.keys()) + ", quit")
            continue

        handler = commands.get(cmd)
        if handler:
            handler()
            if sim:
                pos = sim.position
                click.echo(f"  Position: x={pos[0]:.1f} y={pos[1]:.1f} z={pos[2]:.1f}")
        else:
            click.echo(f"Unknown command: {cmd}. Type 'help' for commands.")

    claw.shutdown()
    click.echo("Claw shut down.")
