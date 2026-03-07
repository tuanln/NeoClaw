"""Analytics API routes."""
from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter()

_data_logger = None
_progress_tracker = None


def _get_logger():
    global _data_logger
    if _data_logger is None:
        from neoclaw.analytics.data_logger import DataLogger
        _data_logger = DataLogger()
    return _data_logger


def _get_tracker():
    global _progress_tracker
    if _progress_tracker is None:
        from neoclaw.education.progress_tracker import ProgressTracker
        _progress_tracker = ProgressTracker()
    return _progress_tracker


@router.get("/summary")
async def analytics_summary():
    """Get usage analytics summary."""
    from neoclaw.analytics.usage_analytics import UsageAnalytics
    ua = UsageAnalytics(_get_logger(), _get_tracker())
    return ua.get_summary()


@router.get("/sensors")
async def sensor_data(
    sensor: str = Query(None, description="Filter by sensor name"),
    limit: int = Query(100, le=10000),
):
    """Get sensor readings."""
    return {"readings": _get_logger().query_sensors(sensor_name=sensor, limit=limit)}


@router.get("/events")
async def event_data(
    event_type: str = Query(None),
    limit: int = Query(100, le=10000),
):
    """Get events."""
    return {"events": _get_logger().query_events(event_type=event_type, limit=limit)}
