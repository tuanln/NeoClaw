"""SQLite time-series data logger."""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional

from neoclaw.config.settings import get_settings

logger = logging.getLogger(__name__)


class DataLogger:
    """Logs sensor readings and events to SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        path = db_path or get_settings().analytics.database_path
        self._db_path = Path(path).expanduser()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                sensor_name TEXT NOT NULL,
                value REAL NOT NULL,
                device_id TEXT DEFAULT 'default'
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                event_type TEXT NOT NULL,
                data TEXT,
                device_id TEXT DEFAULT 'default'
            );

            CREATE TABLE IF NOT EXISTS usage_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                exercise_id TEXT,
                code_runs INTEGER DEFAULT 0,
                commands_executed INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_readings(timestamp);
            CREATE INDEX IF NOT EXISTS idx_event_timestamp ON events(timestamp);
        """)
        self._conn.commit()

    def log_sensor(self, sensor_name: str, value: float, device_id: str = "default") -> None:
        """Log a sensor reading."""
        if self._conn:
            self._conn.execute(
                "INSERT INTO sensor_readings (timestamp, sensor_name, value, device_id) VALUES (?, ?, ?, ?)",
                (time.time(), sensor_name, value, device_id),
            )
            self._conn.commit()

    def log_event(self, event_type: str, data: Optional[dict] = None, device_id: str = "default") -> None:
        """Log an event."""
        if self._conn:
            self._conn.execute(
                "INSERT INTO events (timestamp, event_type, data, device_id) VALUES (?, ?, ?, ?)",
                (time.time(), event_type, json.dumps(data) if data else None, device_id),
            )
            self._conn.commit()

    def start_session(self, student_id: str, exercise_id: Optional[str] = None) -> int:
        """Start a usage session. Returns session ID."""
        if not self._conn:
            return -1
        cursor = self._conn.execute(
            "INSERT INTO usage_sessions (student_id, start_time, exercise_id) VALUES (?, ?, ?)",
            (student_id, time.time(), exercise_id),
        )
        self._conn.commit()
        return cursor.lastrowid or -1

    def end_session(self, session_id: int, code_runs: int = 0, commands: int = 0) -> None:
        """End a usage session."""
        if self._conn:
            self._conn.execute(
                "UPDATE usage_sessions SET end_time=?, code_runs=?, commands_executed=? WHERE id=?",
                (time.time(), code_runs, commands, session_id),
            )
            self._conn.commit()

    def query_sensors(
        self,
        sensor_name: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 1000,
    ) -> list[dict]:
        """Query sensor readings."""
        if not self._conn:
            return []

        query = "SELECT timestamp, sensor_name, value, device_id FROM sensor_readings WHERE 1=1"
        params: list = []

        if sensor_name:
            query += " AND sensor_name=?"
            params.append(sensor_name)
        if start_time:
            query += " AND timestamp>=?"
            params.append(start_time)
        if end_time:
            query += " AND timestamp<=?"
            params.append(end_time)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(query, params).fetchall()
        return [
            {"timestamp": r[0], "sensor_name": r[1], "value": r[2], "device_id": r[3]}
            for r in rows
        ]

    def query_events(self, event_type: Optional[str] = None, limit: int = 100) -> list[dict]:
        """Query events."""
        if not self._conn:
            return []

        if event_type:
            rows = self._conn.execute(
                "SELECT timestamp, event_type, data, device_id FROM events WHERE event_type=? ORDER BY timestamp DESC LIMIT ?",
                (event_type, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT timestamp, event_type, data, device_id FROM events ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [
            {
                "timestamp": r[0],
                "event_type": r[1],
                "data": json.loads(r[2]) if r[2] else None,
                "device_id": r[3],
            }
            for r in rows
        ]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
