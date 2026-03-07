"""Telemetrix GPIO backend for ThingBot hardware over serial/TCP.

This backend implements IGPIOBackend using the ThingBot Telemetrix protocol,
which communicates with an Arduino-based ThingBot board via USB serial or TCP/IP.

Architecture difference vs GpiozeroBackend:
  - GpiozeroBackend: direct register access on local GPIO (Pi/NEO One)
  - TelemetrixBackend: binary protocol over serial/TCP to Arduino firmware

Key design decision — async vs sync reads:
  Telemetrix uses callback-based async reads. To satisfy IGPIOBackend.read()
  which is synchronous, we cache pin state locally whenever the Arduino
  reports a change. The first read() before any callback may return the
  pull_up default (True for INPUT_PULLUP).

Install: pip install thingbot-telemetrix
"""
from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class TelemetrixBackend:
    """IGPIOBackend implementation using ThingBot Telemetrix protocol.

    Supports both USB serial and TCP/IP transport (e.g. WiFi-connected ThingBot).

    Usage:
        backend = TelemetrixBackend(com_port="/dev/ttyACM0")
        backend = TelemetrixBackend(ip_address="192.168.1.100", ip_port=31335)

    For direct ThingBot motor control (DC motors), access the underlying
    Telemetrix instance via the .telemetrix property and use ThingBotMotorController
    instead of routing motor commands through GPIO pins.
    """

    def __init__(
        self,
        com_port: Optional[str] = None,
        ip_address: Optional[str] = None,
        ip_port: int = 31335,
        arduino_instance_id: int = 1,
    ):
        """
        :param com_port: Serial port, e.g. '/dev/ttyACM0' or 'COM3'.
                         None = auto-detect.
        :param ip_address: IP address for TCP/IP connected ThingBot.
                           Mutually exclusive with com_port.
        :param ip_port: TCP port for network connection (default 31335).
        :param arduino_instance_id: Must match firmware's ARDUINO_INSTANCE_ID.
        """
        from thingbot_telemetrix.telemetrix import Telemetrix

        self._tele = Telemetrix(
            com_port=com_port,
            ip_address=ip_address,
            ip_port=ip_port,
            arduino_instance_id=arduino_instance_id,
        )
        # Local cache for synchronous read() — updated by async callbacks
        self._pin_states: dict[int, bool] = {}
        # User-registered callbacks (pin → callback(pin, value))
        self._user_callbacks: dict[int, Callable[[int, bool], None]] = {}
        self._lock = threading.Lock()

    # ── Internal helpers ──

    def _make_input_cb(self, pin: int) -> Callable:
        """Build an internal Telemetrix callback that adapts to IGPIOBackend format.

        gpio().set_pin_mode_digital_input callback signature: callback(value)
        where value is 0 (LOW) or 1 (HIGH). Pin info is not passed by Telemetrix —
        we capture it via closure instead.

        IGPIOBackend callback signature: callback(pin: int, value: bool)
        """
        def _internal(value: int) -> None:
            bool_value = bool(value)
            with self._lock:
                self._pin_states[pin] = bool_value
            user_cb = self._user_callbacks.get(pin)
            if user_cb:
                user_cb(pin, bool_value)

        return _internal

    # ── IGPIOBackend interface ──

    def setup_output(self, pin: int) -> None:
        """Configure pin as digital output."""
        self._tele.gpio().set_pin_mode_output(pin)
        with self._lock:
            self._pin_states[pin] = False

    def setup_input(self, pin: int, pull_up: bool = True) -> None:
        """Configure pin as digital input, registers internal callback for state caching.

        Note: pull_up is passed as a hint for initial state caching only.
        The actual INPUT vs INPUT_PULLUP mode must be set in Arduino firmware
        (set_pin_mode_digital_input does not accept a mode parameter).
        """
        cb = self._make_input_cb(pin)
        self._tele.gpio().set_pin_mode_digital_input(pin, cb)
        with self._lock:
            # Optimistic default: pull_up pins start HIGH (not triggered)
            self._pin_states[pin] = True if pull_up else False

    def write(self, pin: int, value: bool) -> None:
        """Write digital HIGH/LOW to output pin."""
        self._tele.gpio().digital_write(pin, 1 if value else 0)
        with self._lock:
            self._pin_states[pin] = value

    def read(self, pin: int) -> bool:
        """Read cached pin state. Updated asynchronously by Arduino callbacks."""
        with self._lock:
            return self._pin_states.get(pin, False)

    def pwm_start(self, pin: int, frequency: int, duty_cycle: float) -> None:
        """Write PWM value (0.0–1.0) to an analog-capable output pin.

        Note: frequency parameter is ignored — ThingBot firmware sets PWM
        frequency in firmware. duty_cycle is mapped to 0–255 range.
        """
        pwm_value = int(max(0.0, min(1.0, duty_cycle)) * 255)
        self._tele.gpio().analog_write(pin, pwm_value)

    def pwm_stop(self, pin: int) -> None:
        """Stop PWM by writing 0 to the pin."""
        self._tele.gpio().analog_write(pin, 0)

    def set_callback(self, pin: int, callback: Callable[[int, bool], None]) -> None:
        """Register a user callback for pin state changes.

        The callback will be invoked from the Telemetrix reporter thread
        whenever the Arduino reports a pin state change.
        """
        self._user_callbacks[pin] = callback

    def cleanup(self) -> None:
        """Shutdown Telemetrix connection and release serial/socket resources."""
        try:
            self._tele.shutdown()
        except Exception:
            pass
        with self._lock:
            self._pin_states.clear()
        self._user_callbacks.clear()

    # ── ThingBot-specific access ──

    @property
    def telemetrix(self):
        """Direct access to Telemetrix instance for ThingBot-specific features.

        Use this to access thingbot().control_dc(), thingbot().control_servo(),
        dht().set_pin_mode_dht(), etc.
        """
        return self._tele
