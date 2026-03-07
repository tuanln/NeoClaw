"""neoclaw deploy — Deploy apps to NEO devices."""
from __future__ import annotations

from pathlib import Path

import click


@click.command()
@click.argument("app_path", type=click.Path(exists=True))
@click.option("--app-id", default=None, help="Application ID")
@click.option("--start", is_flag=True, help="Start app after deploy")
def deploy(app_path, app_id, start):
    """Deploy an application to the NEO device."""
    from neoclaw.iot.app_manager import AppManager

    manager = AppManager()
    path = Path(app_path)

    click.echo(f"Deploying {path.name}...")
    app = manager.deploy(path, app_id)
    click.echo(f"Deployed: {app.app_id} (v{app.version})")

    if start:
        click.echo("Starting app...")
        if manager.start(app.app_id):
            click.echo(f"App {app.app_id} is running.")
        else:
            click.echo("Failed to start app.")
