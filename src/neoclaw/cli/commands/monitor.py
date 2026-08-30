"""neoclaw monitor — Real-time monitoring."""
from __future__ import annotations

import click


@click.command()
@click.option("--web", is_flag=True, help="Launch web dashboard")
@click.option("--port", default=8080, help="Web server port")
@click.option("--interval", default=2, help="Update interval in seconds")
def monitor(web, port, interval):
    """Monitor the claw machine in real-time."""
    if web:
        click.echo(f"Starting web dashboard on http://localhost:{port}")
        from neoclaw.web.app import run_server
        run_server(port=port)
        return

    # Terminal monitoring
    click.echo("Theo doi ClawBot theo thoi gian thuc (Ctrl+C de dung)")
    click.echo("-" * 50)

    import time

    from neoclaw.hardware.claw_robot import ClawRobot

    try:
        robot = ClawRobot.create(simulator=True)
    except Exception as e:
        click.echo(f"Failed to connect: {e}")
        return

    try:
        while True:
            state = robot.get_state().to_dict()
            click.clear()
            click.echo("=== ClawBot Monitor ===")

            click.echo("\nBanh xe (de omni):")
            for wheel, speed in state["base"]["wheels"].items():
                bar = "#" * (abs(int(speed)) // 10)
                click.echo(f"  {wheel:<12} {speed:>4} {bar}")
            click.echo(f"  huong: {state['base']['heading']:.1f} do")

            click.echo("\nTay gap:")
            for joint, angle in state["arm"]["joints"].items():
                click.echo(f"  {joint:<10} {angle:>4} do")
            click.echo(f"  kep: {'DANG GIU' if state['arm']['gripper_holding'] else 'mo'}")

            if state["switch_pressed"]:
                click.echo("\nCONG TAC: DANG NHAN")
            if state["buzzer_freq"]:
                click.echo(f"Coi: {state['buzzer_freq']}")

            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        robot.shutdown()
        click.echo("\nMonitor stopped.")
