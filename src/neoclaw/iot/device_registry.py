"""Device discovery and fleet management."""
from __future__ import annotations

import logging
import time
from typing import Optional

from neoclaw.iot.models import DeviceInfo, DeviceStatus

logger = logging.getLogger(__name__)

# Device considered offline after this many seconds without heartbeat
_OFFLINE_THRESHOLD = 60


class DeviceRegistry:
    """Registry for managing NeoClaw devices."""

    def __init__(self):
        self._devices: dict[str, DeviceInfo] = {}

    def register(self, device: DeviceInfo) -> None:
        """Register or update a device."""
        device.last_seen = time.time()
        device.status = DeviceStatus.ONLINE
        self._devices[device.device_id] = device
        logger.info(f"Device registered: {device.device_id} ({device.name})")

    def heartbeat(self, device_id: str) -> None:
        """Update last seen time for a device."""
        device = self._devices.get(device_id)
        if device:
            device.last_seen = time.time()
            device.status = DeviceStatus.ONLINE

    def unregister(self, device_id: str) -> None:
        """Remove a device from the registry."""
        self._devices.pop(device_id, None)

    def get(self, device_id: str) -> Optional[DeviceInfo]:
        """Get device by ID."""
        return self._devices.get(device_id)

    def list_devices(self, status: Optional[DeviceStatus] = None) -> list[DeviceInfo]:
        """List all devices, optionally filtered by status."""
        self._update_status()
        if status:
            return [d for d in self._devices.values() if d.status == status]
        return list(self._devices.values())

    def list_online(self) -> list[DeviceInfo]:
        """List online devices."""
        return self.list_devices(DeviceStatus.ONLINE)

    def _update_status(self) -> None:
        """Update device status based on last seen time."""
        now = time.time()
        for device in self._devices.values():
            if device.status == DeviceStatus.ONLINE:
                if now - device.last_seen > _OFFLINE_THRESHOLD:
                    device.status = DeviceStatus.OFFLINE

    @property
    def device_count(self) -> int:
        return len(self._devices)

    @property
    def online_count(self) -> int:
        return len(self.list_online())
