"""neoclaw init — Initialize configuration and detect board."""
from __future__ import annotations

from pathlib import Path

import click


@click.command()
@click.option("--board", type=click.Choice(["neo_one", "pico_w"]), default=None, help="Board type")
def init_cmd(board):
    """Initialize NeoClaw configuration."""
    config_dir = Path.home() / ".neoclaw"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "config.toml"

    if board is None:
        board = _detect_board()
        click.echo(f"Detected board: {board}")

    if not config_file.exists():
        config_file.write_text(f'[hardware]\nboard = "{board}"\n')
        click.echo(f"Created config: {config_file}")
    else:
        click.echo(f"Config already exists: {config_file}")

    # Create data directories
    (config_dir / "apps").mkdir(exist_ok=True)
    (config_dir / "exports").mkdir(exist_ok=True)

    click.echo("NeoClaw initialized successfully!")
    click.echo(f"  Board: {board}")
    click.echo(f"  Config: {config_file}")
    click.echo(f"  Apps: {config_dir / 'apps'}")


def _detect_board() -> str:
    """Try to auto-detect the board type."""
    try:
        model_path = Path("/proc/device-tree/model")
        if model_path.exists():
            model = model_path.read_text().lower()
            if "pico" in model:
                return "pico_w"
    except Exception:
        pass
    return "neo_one"
