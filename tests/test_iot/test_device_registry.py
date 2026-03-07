"""Tests for device registry."""
from neoclaw.iot.device_registry import DeviceRegistry
from neoclaw.iot.models import DeviceInfo, DeviceStatus


def test_register_device():
    registry = DeviceRegistry()
    device = DeviceInfo(device_id="neo-001", name="Test Claw")
    registry.register(device)

    assert registry.device_count == 1
    assert registry.get("neo-001") is not None


def test_list_devices():
    registry = DeviceRegistry()
    registry.register(DeviceInfo(device_id="neo-001", name="Claw 1"))
    registry.register(DeviceInfo(device_id="neo-002", name="Claw 2"))

    devices = registry.list_devices()
    assert len(devices) == 2


def test_unregister_device():
    registry = DeviceRegistry()
    registry.register(DeviceInfo(device_id="neo-001"))
    registry.unregister("neo-001")
    assert registry.device_count == 0


def test_heartbeat():
    registry = DeviceRegistry()
    registry.register(DeviceInfo(device_id="neo-001"))
    registry.heartbeat("neo-001")

    device = registry.get("neo-001")
    assert device is not None
    assert device.status == DeviceStatus.ONLINE
