"""Application deployment and management on NEO devices."""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

from neoclaw.iot.models import AppInfo

logger = logging.getLogger(__name__)


class AppManager:
    """Deploy, start, stop, and monitor apps on NEO devices."""

    def __init__(self, apps_dir: Optional[Path] = None):
        self._apps_dir = apps_dir or Path.home() / ".neoclaw" / "apps"
        self._apps_dir.mkdir(parents=True, exist_ok=True)
        self._running: dict[str, subprocess.Popen] = {}
        self._apps: dict[str, AppInfo] = {}

    def deploy(self, app_path: Path, app_id: Optional[str] = None) -> AppInfo:
        """Deploy an application from a directory or file."""
        app_id = app_id or app_path.stem
        dest = self._apps_dir / app_id
        dest.mkdir(parents=True, exist_ok=True)

        if app_path.is_file():
            import shutil
            shutil.copy2(app_path, dest / app_path.name)
            entry_point = app_path.name
        elif app_path.is_dir():
            import shutil
            shutil.copytree(app_path, dest, dirs_exist_ok=True)
            entry_point = "main.py"
        else:
            raise FileNotFoundError(f"App path not found: {app_path}")

        app = AppInfo(
            app_id=app_id,
            name=app_id,
            entry_point=entry_point,
            status="stopped",
        )
        self._apps[app_id] = app
        logger.info(f"Deployed app: {app_id} to {dest}")
        return app

    def start(self, app_id: str) -> bool:
        """Start a deployed application."""
        app = self._apps.get(app_id)
        if not app:
            logger.error(f"App not found: {app_id}")
            return False

        if app_id in self._running:
            logger.warning(f"App already running: {app_id}")
            return False

        app_dir = self._apps_dir / app_id
        entry = app_dir / app.entry_point

        if not entry.exists():
            logger.error(f"Entry point not found: {entry}")
            return False

        proc = subprocess.Popen(
            [sys.executable, str(entry)],
            cwd=str(app_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._running[app_id] = proc
        app.status = "running"
        logger.info(f"Started app: {app_id} (PID {proc.pid})")
        return True

    def stop(self, app_id: str) -> bool:
        """Stop a running application."""
        proc = self._running.pop(app_id, None)
        if proc is None:
            return False

        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

        app = self._apps.get(app_id)
        if app:
            app.status = "stopped"
        logger.info(f"Stopped app: {app_id}")
        return True

    def get_logs(self, app_id: str, lines: int = 50) -> str:
        """Get stdout/stderr from a running app."""
        proc = self._running.get(app_id)
        if proc is None:
            return ""

        if proc.stdout and proc.stdout.readable():
            return proc.stdout.read(4096).decode(errors="replace")
        return ""

    def list_apps(self) -> list[AppInfo]:
        """List all deployed applications."""
        # Update status of running apps
        for app_id, proc in list(self._running.items()):
            if proc.poll() is not None:
                self._running.pop(app_id)
                app = self._apps.get(app_id)
                if app:
                    app.status = "stopped"
        return list(self._apps.values())

    def get_app(self, app_id: str) -> Optional[AppInfo]:
        return self._apps.get(app_id)
