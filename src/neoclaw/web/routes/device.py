"""Device management API routes."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# Lazy-loaded shared state
_registry = None


def _get_registry():
    global _registry
    if _registry is None:
        from neoclaw.iot.device_registry import DeviceRegistry
        _registry = DeviceRegistry()
    return _registry


@router.get("/status")
async def device_status():
    """Get current device status."""
    from neoclaw.config.settings import get_settings
    settings = get_settings()
    return {
        "board": settings.hardware.board,
        "gpio_enabled": settings.hardware.enable_gpio,
        "version": settings.version,
    }


@router.get("/list")
async def list_devices():
    """List all registered devices."""
    registry = _get_registry()
    return {"devices": [d.to_dict() for d in registry.list_devices()]}


@router.get("/{device_id}")
async def get_device(device_id: str):
    """Get device details."""
    registry = _get_registry()
    device = registry.get(device_id)
    if device is None:
        return {"error": "Device not found"}
    return device.to_dict()
