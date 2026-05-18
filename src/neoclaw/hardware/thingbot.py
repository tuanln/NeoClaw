"""ThingBot hardware abstraction — direct interface to MEO ThingBot board.

MEO ThingBot: ESP32-C3 + PCA9685 I2C PWM driver
Communication: USB Serial 115200 baud, Telemetrix binary protocol

Hardware channels (all via PCA9685):
    DC Motors:  M1(ch2/3) M2(ch4/5) M3(ch7/8) M4(ch1/0) — bidirectional, speed 0-100
    Servos:     S1(ch12) S2(ch11) S3(ch10) S4(ch9) S5(ch8) — angle 0-180
    Buzzer:     ch14 — frequency (0=off)
    LEDs:       LED1(ch15) LED2(ch13) — brightness 0-100
    Switch:     SW3 (ESP32-C3 GPIO 3, input pullup)

Telemetrix command format: [length, command_id, param1, param2, ...]
    7: DC_WRITE(motor, speed)
    8: SERVO_WRITE(servo, angle)
    9: BUZZER_WRITE(frequency)
   10: LED_WRITE(led, state)

Reports from ThingBot:
   12: THINGBOT_SW_REPORT(pin, value)
"""
from __future__ import annotations

import logging
from typing import Callable

from neoclaw.hardware.models import (
    LedID,
    MotorID,
    ServoID,
)

logger = logging.getLogger(__name__)


class ThingBot:
    """Direct interface to MEO ThingBot hardware.

    Provides typed access to all ThingBot peripherals.
    Can be used standalone or as the hardware layer for OmniBase/RobotArm.

    Usage:
        bot = ThingBot.connect()          # auto-detect USB serial
        bot.dc(MotorID.M1, 80)            # motor 1 forward at 80%
        bot.dc(MotorID.M1, -60)           # motor 1 reverse at 60%
        bot.servo(ServoID.S1, 90)         # servo 1 to 90°
        bot.buzzer(440)                   # buzzer at 440 Hz
        bot.led(LedID.LED1, 100)          # LED 1 full brightness
        bot.shutdown()
    """

    def __init__(self, backend):
        """Initialize with a TelemetrixBackend instance.

        Use ThingBot.connect() factory method instead of calling directly.
        """
        self._backend = backend
        self._motor_speeds: dict[MotorID, int] = {m: 0 for m in MotorID}
        self._servo_angles: dict[ServoID, int] = {
            ServoID.S1: 90, ServoID.S2: 90, ServoID.S3: 90,
            ServoID.S4: 0, ServoID.S5: 90,
        }
        self._buzzer_freq: int = 0
        self._led_states: dict[LedID, int] = {LedID.LED1: 0, LedID.LED2: 0}
        self._switch_state: bool = False
        self._switch_callbacks: list[Callable[[bool], None]] = []

    @classmethod
    def connect(
        cls,
        com_port: str | None = None,
        arduino_instance_id: int = 1,
    ) -> ThingBot:
        """Connect to ThingBot via USB serial.

        Args:
            com_port: Serial port (None = auto-detect)
            arduino_instance_id: Telemetrix board ID (default 1)
        """
        from neoclaw.hardware.telemetrix_backend import TelemetrixBackend

        backend = TelemetrixBackend(
            com_port=com_port,
            arduino_instance_id=arduino_instance_id,
        )
        bot = cls(backend)
        # Register switch callback
        backend.set_switch_callback(bot._on_switch)
        logger.info(f"ThingBot connected (port={com_port or 'auto'})")
        return bot

    @classmethod
    def create_simulator(cls) -> ThingBot:
        """Create a ThingBot with simulated backend (no hardware needed)."""
        from neoclaw.hardware.gpio_backend import SimulatorBackend

        backend = SimulatorBackend()
        bot = cls(backend)
        logger.info("ThingBot simulator created")
        return bot

    # ── DC Motors (M1-M4) ──

    def dc(self, motor: MotorID, speed: int) -> None:
        """Set DC motor speed.

        Args:
            motor: MotorID.M1 through M4
            speed: -100 to 100 (negative = reverse, 0 = stop)
        """
        speed = max(-100, min(100, speed))
        self._motor_speeds[motor] = speed

        if hasattr(self._backend, "control_dc"):
            self._backend.control_dc(int(motor), speed)
        else:
            logger.debug(f"[SIM] DC M{motor}: speed={speed}")

    def stop_motor(self, motor: MotorID) -> None:
        """Stop a specific motor."""
        self.dc(motor, 0)

    def stop_all_motors(self) -> None:
        """Emergency stop all motors."""
        for m in MotorID:
            self.dc(m, 0)

    # ── Servos (S1-S5) ──

    def servo(self, servo_id: ServoID, angle: int) -> None:
        """Set servo angle.

        Args:
            servo_id: ServoID.S1 through S5
            angle: 0 to 180 degrees
        """
        angle = max(0, min(180, angle))
        self._servo_angles[servo_id] = angle

        if hasattr(self._backend, "control_servo"):
            self._backend.control_servo(int(servo_id), angle)
        else:
            logger.debug(f"[SIM] Servo S{servo_id}: angle={angle}")

    # ── Buzzer ──

    def buzzer(self, frequency: int) -> None:
        """Set buzzer frequency. 0 = off.

        Args:
            frequency: 0-255 (mapped to PCA9685 PWM)
        """
        frequency = max(0, min(255, frequency))
        self._buzzer_freq = frequency

        if hasattr(self._backend, "control_buzzer"):
            self._backend.control_buzzer(frequency)
        else:
            logger.debug(f"[SIM] Buzzer: freq={frequency}")

    def buzzer_off(self) -> None:
        """Turn buzzer off."""
        self.buzzer(0)

    # ── LEDs ──

    def led(self, led_id: LedID, brightness: int) -> None:
        """Set LED brightness.

        Args:
            led_id: LedID.LED1 or LED2
            brightness: 0 (off) to 100 (full)
        """
        brightness = max(0, min(100, brightness))
        self._led_states[led_id] = brightness

        if hasattr(self._backend, "control_led"):
            self._backend.control_led(int(led_id), brightness)
        else:
            logger.debug(f"[SIM] LED{led_id}: brightness={brightness}")

    # ── Switch (SW3) ──

    def on_switch(self, callback: Callable[[bool], None]) -> None:
        """Register callback for switch state changes.

        Args:
            callback: Called with True when pressed, False when released
        """
        self._switch_callbacks.append(callback)

    @property
    def switch_pressed(self) -> bool:
        """Current switch state."""
        return self._switch_state

    def _on_switch(self, value: bool) -> None:
        """Internal switch callback from backend."""
        self._switch_state = value
        for cb in self._switch_callbacks:
            cb(value)

    # ── State queries ──

    @property
    def motor_speeds(self) -> dict[MotorID, int]:
        return dict(self._motor_speeds)

    @property
    def servo_angles(self) -> dict[ServoID, int]:
        return dict(self._servo_angles)

    def get_state(self) -> dict:
        """Get complete ThingBot state."""
        return {
            "motors": {f"M{m}": s for m, s in self._motor_speeds.items()},
            "servos": {f"S{s}": a for s, a in self._servo_angles.items()},
            "buzzer": self._buzzer_freq,
            "leds": {f"LED{led}": b for led, b in self._led_states.items()},
            "switch": self._switch_state,
        }

    # ── Lifecycle ──

    def shutdown(self) -> None:
        """Stop everything and release connection."""
        self.stop_all_motors()
        self.buzzer_off()
        for led_id in LedID:
            self.led(led_id, 0)
        self._backend.cleanup()
        logger.info("ThingBot shut down")
