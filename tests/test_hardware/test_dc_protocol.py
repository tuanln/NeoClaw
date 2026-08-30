"""Wire-protocol tests for ThingBot DC motor speed encoding.

PROTOCOL-BUG (2026-05-18 survey, fixed here): the Telemetrix DC_WRITE
payload carries `speed` in a single byte. Firmware used to read it as
`uint8_t` and test `if (speed >= 0)`, which is always true for unsigned —
the reverse branch was unreachable. Python meanwhile passed -100..100
straight through.

Contract fixed by these tests: Python encodes signed speed as a
two's-complement byte (0..255); firmware casts it back with `(int8_t)`.
"""
from __future__ import annotations

import pytest

from neoclaw.hardware.telemetrix_backend import encode_speed_byte


def test_forward_speed_encodes_unchanged():
    """Positive speeds keep the legacy wire value — old firmware stays compatible."""
    assert encode_speed_byte(60) == 60


def test_reverse_speed_encodes_as_twos_complement_byte():
    """-60 must travel as 196 so `(int8_t)196` reads back as -60 on the ESP32."""
    assert encode_speed_byte(-60) == 196


def test_full_reverse_encodes_to_156():
    assert encode_speed_byte(-100) == 156


def test_zero_encodes_to_zero():
    assert encode_speed_byte(0) == 0


@pytest.mark.parametrize("speed", [-100, -60, -1, 0, 1, 60, 100])
def test_encoded_byte_round_trips_through_int8_cast(speed):
    """Decoding the way the firmware does must return the original speed."""
    raw = encode_speed_byte(speed)
    decoded = raw - 256 if raw > 127 else raw
    assert decoded == speed


@pytest.mark.parametrize("speed", [-255, -101, 101, 1000])
def test_out_of_range_speed_is_clamped_before_encoding(speed):
    """A stray value must never become an out-of-range PWM duty on the board."""
    raw = encode_speed_byte(speed)
    decoded = raw - 256 if raw > 127 else raw
    assert -100 <= decoded <= 100


@pytest.mark.parametrize("speed", [-100, -1, 0, 100])
def test_encoded_byte_always_fits_one_unsigned_byte(speed):
    assert 0 <= encode_speed_byte(speed) <= 255


class _FakeThingBot:
    """Records what the transport hands to the thingbot-telemetrix library."""

    def __init__(self):
        self.dc_calls: list[tuple[int, int]] = []

    def control_dc(self, motor_number, speed):
        self.dc_calls.append((motor_number, speed))

    def control_servo(self, servo_number, angle):
        pass


class _FakeTelemetrix:
    def __init__(self, **kwargs):
        self._thingbot = _FakeThingBot()

    def gpio(self):
        return object()

    def thingbot(self):
        return self._thingbot

    def shutdown(self):
        pass


@pytest.fixture
def backend(monkeypatch):
    """A TelemetrixBackend wired to a fake board (the real lib needs hardware)."""
    import sys
    import types

    fake_module = types.ModuleType("thingbot_telemetrix")
    fake_module.Telemetrix = _FakeTelemetrix
    monkeypatch.setitem(sys.modules, "thingbot_telemetrix", fake_module)

    from neoclaw.hardware.telemetrix_backend import TelemetrixBackend

    return TelemetrixBackend(com_port="/dev/fake")


def test_control_dc_sends_encoded_byte_for_reverse(backend):
    """The library must never receive a negative int — bytes() would reject it."""
    backend.control_dc(1, -60)
    assert backend._thingbot.dc_calls == [(1, 196)]


def test_control_dc_sends_plain_value_for_forward(backend):
    backend.control_dc(2, 60)
    assert backend._thingbot.dc_calls == [(2, 60)]


def test_control_dc_clamps_before_encoding(backend):
    backend.control_dc(3, -500)
    assert backend._thingbot.dc_calls == [(3, encode_speed_byte(-100))]
