"""GPIO backend using MEO ThingBot via Telemetrix serial protocol.

MEO ThingBot is the first supported external hardware device.
Communication happens over USB/Serial using the Telemetrix protocol,
which sends binary commands: [length, command_id, param1, param2, ...]

Architecture note:
    IGPIOBackend (Protocol)
    ├── GpiozeroBackend      ← NEO One / Raspberry Pi (direct GPIO)
    ├── TelemetrixBackend    ← MEO ThingBot (serial Telemetrix)  ← THIS
    ├── SimulatorBackend     ← Testing (in-memory)
    └── (future) PiZeroBackend, etc.
"""
from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class TelemetrixBackend:
    """GPIO backend bridging IGPIOBackend to MEO ThingBot via thingbot-telemetrix.

    Translates NeoClaw's pin-based GPIO operations into Telemetrix serial commands.
    Supports digital I/O, PWM (analog_write 0-255), and interrupt callbacks.

    Usage:
        from neoclaw.hardware.telemetrix_backend import TelemetrixBackend
        backend = TelemetrixBackend(com_port="/dev/ttyUSB0")
        # or auto-detect:
        backend = TelemetrixBackend()
    """

    def __init__(
        self,
        com_port: str | None = None,
        arduino_instance_id: int = 1,
        arduino_wait: float = 4,
    ):
        try:
            from thingbot_telemetrix import Telemetrix
        except ImportError:
            raise ImportError(
                "thingbot-telemetrix is required for MEO ThingBot support. "
                "Install it with: pip install thingbot-telemetrix"
            )

        self._board = Telemetrix(
            com_port=com_port,
            arduino_instance_id=arduino_instance_id,
            arduino_wait=arduino_wait,
        )
        self._gpio = self._board.gpio()
        self._thingbot = self._board.thingbot()

        # Pin state cache (Telemetrix reads are async/callback-based)
        self._pin_values: dict[int, bool] = {}
        self._pin_lock = threading.Lock()

        # User callbacks
        self._callbacks: dict[int, Callable[[int, bool], None]] = {}

        # Output pin tracking
        self._output_pins: set[int] = set()
        self._input_pins: set[int] = set()
        self._pwm_pins: set[int] = set()

        logger.info(
            f"TelemetrixBackend initialized "
            f"(port={com_port or 'auto-detect'})"
        )

    # ── IGPIOBackend implementation ──

    def setup_output(self, pin: int) -> None:
        self._gpio.set_pin_mode_output(pin)
        self._output_pins.add(pin)
        self._pin_values[pin] = False

    def setup_input(self, pin: int, pull_up: bool = True) -> None:
        from thingbot_telemetrix.private_constants import PinModes

        pin_mode = PinModes.INPUT_PULLUP if pull_up else PinModes.INPUT

        def _on_digital_report(value: int) -> None:
            bool_val = bool(value)
            with self._pin_lock:
                old_val = self._pin_values.get(pin)
                self._pin_values[pin] = bool_val
            if old_val is not None and old_val != bool_val:
                cb = self._callbacks.get(pin)
                if cb:
                    cb(pin, bool_val)

        if pull_up:
            self._gpio.set_pin_mode_digital_input(pin, callback=_on_digital_report)
        else:
            self._gpio.set_pin_mode_digital_input(pin, callback=_on_digital_report)

        self._input_pins.add(pin)
        self._pin_values[pin] = True if pull_up else False

    def write(self, pin: int, value: bool) -> None:
        self._gpio.digital_write(pin, 1 if value else 0)
        with self._pin_lock:
            self._pin_values[pin] = value

    def read(self, pin: int) -> bool:
        with self._pin_lock:
            return self._pin_values.get(pin, False)

    def pwm_start(self, pin: int, frequency: int, duty_cycle: float) -> None:
        # Telemetrix analog_write uses 0-255 range
        value = int(max(0.0, min(1.0, duty_cycle)) * 255)
        self._gpio.analog_write(pin, value)
        self._pwm_pins.add(pin)

    def pwm_stop(self, pin: int) -> None:
        self._gpio.analog_write(pin, 0)
        self._pwm_pins.discard(pin)

    def set_callback(self, pin: int, callback: Callable[[int, bool], None]) -> None:
        self._callbacks[pin] = callback

    def cleanup(self) -> None:
        # Stop all PWM
        for pin in list(self._pwm_pins):
            try:
                self._gpio.analog_write(pin, 0)
            except Exception:
                pass

        # Turn off all outputs
        for pin in self._output_pins:
            try:
                self._gpio.digital_write(pin, 0)
            except Exception:
                pass

        # Shutdown telemetrix connection
        try:
            self._board.shutdown()
        except Exception:
            pass

        self._output_pins.clear()
        self._input_pins.clear()
        self._pwm_pins.clear()
        self._pin_values.clear()
        self._callbacks.clear()

        logger.info("TelemetrixBackend cleaned up")

    # ── ThingBot-specific extensions ──
    #
    # These methods communicate with the PCA9685 PWM driver on ThingBot.
    # Motor speed: -100 to 100 (firmware maps 0-100 → PCA9685 0-4095)
    # Servo angle: 0 to 180 (firmware maps → PCA9685 pulse 150-600)
    # Buzzer: 0-255 (0=off, mapped to PCA9685 PWM)
    # LED: 0-100 brightness (mapped to PCA9685 0-4095)
    #
    # Firmware command format: [length, command_id, param1, param2]
    #   DC_WRITE=7:    [2, 7, motor_num, speed_byte]
    #   SERVO_WRITE=8: [2, 8, servo_num, angle_byte]
    #   BUZZER_WRITE=9:[1, 9, freq_byte]
    #   LED_WRITE=10:  [2, 10, led_num, state_byte]

    def control_dc(self, motor_number: int, speed: int) -> None:
        """ThingBot DC motor control via PCA9685.

        Args:
            motor_number: 1-4 (M1-M4)
            speed: -100 to 100 (negative = reverse, 0 = stop)
                   Firmware maps |speed| 0-100 → PCA9685 duty 0-4095
        """
        speed = max(-100, min(100, speed))
        self._thingbot.control_dc(motor_number, speed)

    def control_servo(self, servo_number: int, angle: int) -> None:
        """ThingBot servo control via PCA9685.

        Args:
            servo_number: 1-5 (S1-S5)
            angle: 0-180 degrees
                   Firmware maps angle → PCA9685 pulse 150-600
        """
        angle = max(0, min(180, angle))
        self._thingbot.control_servo(servo_number, angle)

    def control_buzzer(self, frequency: int) -> None:
        """ThingBot buzzer via PCA9685.

        Args:
            frequency: 0-255 (0 = off, mapped to PCA9685 PWM)
        """
        frequency = max(0, min(255, frequency))
        self._thingbot.control_buzzer(frequency)

    def control_led(self, led_number: int, brightness: int) -> None:
        """ThingBot LED via PCA9685.

        Args:
            led_number: 1 or 2
            brightness: 0 (off) to 100 (full)
                        Firmware maps 0-100 → PCA9685 duty 0-4095
        """
        brightness = max(0, min(100, brightness))
        self._thingbot.control_led(led_number, brightness)

    def set_switch_callback(self, callback: Callable[[bool], None]) -> None:
        """Register callback for ThingBot onboard switch (SW3, GPIO 3).

        Switch is INPUT_PULLUP on ESP32-C3. Firmware sends
        THINGBOT_SW_REPORT (id=12) on state change.
        """
        self._thingbot.set_sw_callback(callback)
