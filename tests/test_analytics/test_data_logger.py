"""Tests for data logger."""
import tempfile
from pathlib import Path

from neoclaw.analytics.data_logger import DataLogger


def test_log_and_query_sensor():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        logger = DataLogger(db_path=db_path)

        logger.log_sensor("temperature", 25.5)
        logger.log_sensor("temperature", 26.0)

        readings = logger.query_sensors(sensor_name="temperature")
        assert len(readings) == 2
        assert readings[0]["value"] == 26.0  # Most recent first

        logger.close()


def test_log_and_query_events():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        logger = DataLogger(db_path=db_path)

        logger.log_event("motor_start", {"axis": "X"})
        logger.log_event("grab", {"success": True})

        events = logger.query_events()
        assert len(events) == 2

        motor_events = logger.query_events(event_type="motor_start")
        assert len(motor_events) == 1

        logger.close()


def test_usage_session():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        logger = DataLogger(db_path=db_path)

        session_id = logger.start_session("student1", "c1_l1_e1")
        assert session_id > 0

        logger.end_session(session_id, code_runs=5, commands=10)
        logger.close()
