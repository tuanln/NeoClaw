"""Data export utilities."""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Optional

from neoclaw.analytics.data_logger import DataLogger
from neoclaw.config.settings import get_settings

logger = logging.getLogger(__name__)


class DataExporter:
    """Export analytics data to CSV and JSON formats."""

    def __init__(self, data_logger: DataLogger, export_dir: Optional[str] = None):
        self._logger = data_logger
        path = export_dir or get_settings().analytics.export_path
        self._export_dir = Path(path).expanduser()
        self._export_dir.mkdir(parents=True, exist_ok=True)

    def export_sensors_csv(
        self,
        filename: str = "sensor_data.csv",
        sensor_name: Optional[str] = None,
        limit: int = 10000,
    ) -> Path:
        """Export sensor readings to CSV."""
        data = self._logger.query_sensors(sensor_name=sensor_name, limit=limit)
        filepath = self._export_dir / filename

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "sensor_name", "value", "device_id"])
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Exported {len(data)} sensor readings to {filepath}")
        return filepath

    def export_events_csv(
        self,
        filename: str = "events.csv",
        event_type: Optional[str] = None,
        limit: int = 10000,
    ) -> Path:
        """Export events to CSV."""
        data = self._logger.query_events(event_type=event_type, limit=limit)
        filepath = self._export_dir / filename

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "event_type", "data", "device_id"])
            writer.writeheader()
            for row in data:
                row["data"] = json.dumps(row["data"]) if row["data"] else ""
                writer.writerow(row)

        logger.info(f"Exported {len(data)} events to {filepath}")
        return filepath

    def export_json(
        self,
        filename: str = "export.json",
        include_sensors: bool = True,
        include_events: bool = True,
        limit: int = 10000,
    ) -> Path:
        """Export all data to JSON."""
        data: dict = {}

        if include_sensors:
            data["sensor_readings"] = self._logger.query_sensors(limit=limit)
        if include_events:
            data["events"] = self._logger.query_events(limit=limit)

        filepath = self._export_dir / filename
        filepath.write_text(json.dumps(data, indent=2))
        logger.info(f"Exported data to {filepath}")
        return filepath
