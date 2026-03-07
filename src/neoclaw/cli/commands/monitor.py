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
    click.echo("Real-time claw monitor (Ctrl+C to stop)")
    click.echo("-" * 50)

    import time
    from neoclaw.hardware.claw_machine import ClawMachine

    try:
        claw = ClawMachine.create(simulator=True)
    except Exception as e:
        click.echo(f"Failed to connect: {e}")
        return

    try:
        while True:
            state = claw.get_state()
            click.clear()
            click.echo("=== NeoClaw Monitor ===")
            click.echo(f"Magnet: {'ON' if state.magnet_active else 'OFF'}")
            click.echo(f"LED: {'ON' if state.led_on else 'OFF'}")

            click.echo("\nLimits:")
            for name, triggered in state.limits.items():
                status = "TRIGGERED" if triggered else "ok"
                click.echo(f"  {name}: {status}")

            click.echo("\nMotors:")
            for name, motor in state.motors.items():
                if motor.active:
                    click.echo(f"  {name}: ACTIVE (speed={motor.speed:.1f})")

            active_btns = [k for k, v in state.buttons.items() if v]
            if active_btns:
                click.echo(f"\nButtons pressed: {', '.join(active_btns)}")

            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        claw.shutdown()
        click.echo("\nMonitor stopped.")
