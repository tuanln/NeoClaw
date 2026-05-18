"""Thread-safety tests for SensorManager + TelemetrixBackend callbacks lists.

These tests don't need real hardware — they use SimulatorBackend and the
in-memory SensorManager. The goal is to catch races between callback
registration and callback dispatch when multiple threads hammer them.
"""
from __future__ import annotations

import threading
import time

from neoclaw.config.pin_maps import get_pin_map
from neoclaw.hardware.gpio_backend import SimulatorBackend
from neoclaw.hardware.models import SensorReading
from neoclaw.hardware.sensor_manager import SensorManager


# ── SensorManager concurrent register + dispatch ──


def test_sensor_manager_concurrent_register_and_dispatch():
    """Hammering on_change from multiple threads while firing limit events
    must not raise, lose callbacks silently, or corrupt the list.
    """
    backend = SimulatorBackend()
    pins = get_pin_map()
    backend.setup_input(pins.limit_x_left, pull_up=True)
    backend.setup_input(pins.limit_y_forward, pull_up=True)
    sensors = SensorManager(backend, pins)

    seen: list[SensorReading] = []
    seen_lock = threading.Lock()

    def make_callback(idx: int):
        def cb(reading: SensorReading) -> None:
            # Mark which callback fired so we can verify all were dispatched.
            with seen_lock:
                seen.append(reading)
        return cb

    # 4 registrar threads each adding 25 callbacks = 100 total.
    NUM_THREADS = 4
    PER_THREAD = 25

    def registrar(start_idx: int):
        for i in range(PER_THREAD):
            sensors.on_change(make_callback(start_idx + i))
            # Yield occasionally to encourage interleaving.
            if i % 5 == 0:
                time.sleep(0.0001)

    threads = [
        threading.Thread(target=registrar, args=(t * PER_THREAD,))
        for t in range(NUM_THREADS)
    ]

    # Start registrars + a thread that fires events concurrently.
    stop = threading.Event()

    def event_firer():
        while not stop.is_set():
            sensors._on_limit_change(pins.limit_x_left, False)
            time.sleep(0.0001)

    firer = threading.Thread(target=event_firer)

    for t in threads:
        t.start()
    firer.start()

    for t in threads:
        t.join(timeout=5.0)
    stop.set()
    firer.join(timeout=5.0)

    # After all threads done, exactly 100 callbacks must be registered.
    with sensors._callbacks_lock:
        assert len(sensors._callbacks) == NUM_THREADS * PER_THREAD

    # Fire one final event — every callback must run exactly once.
    seen.clear()
    sensors._on_limit_change(pins.limit_x_left, False)
    assert len(seen) == NUM_THREADS * PER_THREAD


def test_sensor_manager_callback_can_register_another():
    """A callback that calls on_change must not deadlock (snapshot pattern)."""
    backend = SimulatorBackend()
    pins = get_pin_map()
    backend.setup_input(pins.limit_x_left, pull_up=True)
    sensors = SensorManager(backend, pins)

    invoked: list[str] = []

    def inner(_r: SensorReading) -> None:
        invoked.append("inner")

    def outer(_r: SensorReading) -> None:
        invoked.append("outer")
        sensors.on_change(inner)  # would deadlock if dispatch held lock

    sensors.on_change(outer)

    # Fire event. outer registers inner. inner does NOT run this dispatch
    # (snapshot was taken before inner was added).
    sensors._on_limit_change(pins.limit_x_left, False)
    assert invoked == ["outer"]

    # Fire again. Now both run.
    invoked.clear()
    sensors._on_limit_change(pins.limit_x_left, False)
    assert set(invoked) == {"outer", "inner"}


# ── TelemetrixBackend lock layout (lite test — no real hardware) ──


def test_telemetrix_backend_lock_attribute_exists():
    """Smoke test: the consolidated `_state_lock` attribute name exists on
    the class (caught the previous `_pin_lock` → `_state_lock` rename).
    """
    from neoclaw.hardware import telemetrix_backend as tb_mod
    src = open(tb_mod.__file__, encoding="utf-8").read()
    assert "_state_lock" in src
    # Old name should be fully gone.
    assert "_pin_lock" not in src
