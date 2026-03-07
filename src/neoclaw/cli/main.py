"""CLI entry point using Click."""
from __future__ import annotations

import click

from neoclaw import __version__


@click.group()
@click.version_option(version=__version__, prog_name="neoclaw")
def cli():
    """NeoClaw — Agentic Robot Education Platform.

    Learn Python by controlling a claw machine.
    """
    pass


# Register sub-commands
from neoclaw.cli.commands.init_cmd import init_cmd
from neoclaw.cli.commands.control import control
from neoclaw.cli.commands.teach import teach
from neoclaw.cli.commands.deploy import deploy
from neoclaw.cli.commands.monitor import monitor

cli.add_command(init_cmd, "init")
cli.add_command(control)
cli.add_command(teach)
cli.add_command(deploy)
cli.add_command(monitor)


if __name__ == "__main__":
    cli()
