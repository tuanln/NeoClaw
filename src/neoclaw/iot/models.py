"""IoT data models."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class DeviceStatus(Enum):
    ONLINE = auto()
    OFFLINE = auto()
    ERROR = auto()
    UPDATING = auto()


@dataclass
class DeviceInfo:
    """Information about a NeoClaw device."""
    device_id: str
    name: str = ""
    board: str = "neo_one"
    ip_address: str = ""
    status: DeviceStatus = DeviceStatus.OFFLINE
    firmware_version: str = ""
    last_seen: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "board": self.board,
            "ip_address": self.ip_address,
            "status": self.status.name,
            "firmware_version": self.firmware_version,
            "last_seen": self.last_seen,
        }


@dataclass
class TelemetryPacket:
    """A telemetry data packet from a device."""
    device_id: str
    timestamp: float = field(default_factory=time.time)
    motor_states: dict[str, bool] = field(default_factory=dict)
    sensor_readings: dict[str, float] = field(default_factory=dict)
    gripper_holding: bool = False
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    temperature_c: float = 0.0

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "timestamp": self.timestamp,
            "motor_states": self.motor_states,
            "sensor_readings": self.sensor_readings,
            "gripper_holding": self.gripper_holding,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "temperature_c": self.temperature_c,
        }


@dataclass
class AppInfo:
    """Information about a deployed application."""
    app_id: str
    name: str
    version: str = "1.0.0"
    status: str = "stopped"  # "running", "stopped", "error"
    device_id: str = ""
    entry_point: str = "main.py"
