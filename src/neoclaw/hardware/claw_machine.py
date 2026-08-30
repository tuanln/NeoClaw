"""LEGACY — arcade claw machine (3-axis gantry + electromagnet).

Not part of the ClawBot product path. Nothing in the app imports this module
any more: the web API, CLI, AI agent and telemetry all drive
`neoclaw.hardware.claw_robot.ClawRobot` through `neoclaw.hardware.dispatch`.

Kept only as a reference for the first prototype (see docs/PICOCLAW-ANALYSIS.md).
Deleting it is a one-line change once the owner confirms it is not needed —
tracked as open question 4 in docs/PROGRESS.md.
"""
from __future__ import annotations

import logging
import time

from neoclaw.config.pin_maps import PinMap, get_pin_map
from neoclaw.config.settings import get_settings
from neoclaw.hardware.gpio_backend import IGPIOBackend, SimulatorBackend
from neoclaw.hardware.models import Axis, ClawState
from neoclaw.hardware.motor_controller import DCMotorController, create_motor_controllers
from neoclaw.hardware.safety import SafetyManager
from neoclaw.hardware.sensor_manager import SensorManager

logger = logging.getLogger(__name__)


class ClawMachine:
    """High-level API for controlling the claw machine.

    Usage:
        claw = ClawMachine.create()  # auto-detect backend
        claw.move_left(duration=1.0, speed=0.8)
        claw.grab()
        claw.move_up(duration=2.0)
        claw.release()
        claw.shutdown()
    """

    def __init__(
        self,
        backend: IGPIOBackend,
        pin_map: PinMap,
        motors: dict[Axis, DCMotorController],
        sensors: SensorManager,
        safety: SafetyManager,
    ):
        self._backend = backend
        self._pin_map = pin_map
        self._motors = motors
        self._sensors = sensors
        self._safety = safety
        self._magnet_active = False

        # Setup electromagnet
        backend.setup_output(pin_map.electromagnet)

        # Setup buttons
        for pin in pin_map.button_pins():
            backend.setup_input(pin, pull_up=True)

        # Start safety manager
        safety.start()

    @classmethod
    def create(cls, simulator: bool = False, board: str | None = None) -> ClawMachine:
        """Factory method to create a ClawMachine with appropriate backend."""
        settings = get_settings()
        board = board or settings.hardware.board

        if simulator:
            backend: IGPIOBackend = SimulatorBackend()
        elif settings.hardware.gpio_library == "telemetrix":
            from neoclaw.hardware.telemetrix_backend import TelemetrixBackend
            backend = TelemetrixBackend(
                com_port=settings.hardware.com_port or None,
                arduino_instance_id=settings.hardware.arduino_instance_id,
            )
        else:
            from neoclaw.hardware.gpio_backend import GpiozeroBackend
            backend = GpiozeroBackend()

        pin_map = get_pin_map(board)
        motors = create_motor_controllers(
            backend, pin_map, settings.hardware.pwm_frequency
        )
        sensors = SensorManager(backend, pin_map)
        safety = SafetyManager(
            motors, sensors,
            watchdog_timeout=settings.hardware.watchdog_timeout,
            max_motor_runtime=settings.safety.max_motor_runtime,
        )

        return cls(backend, pin_map, motors, sensors, safety)

    # ── Movement commands ──

    def move_left(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        """Move claw left for duration seconds. Returns False if blocked by limit."""
        return self._move(Axis.X, "positive", duration, speed)

    def move_right(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        """Move claw right for duration seconds."""
        return self._move(Axis.X, "negative", duration, speed)

    def move_forward(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        """Move claw forward for duration seconds."""
        return self._move(Axis.Y, "positive", duration, speed)

    def move_backward(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        """Move claw backward for duration seconds."""
        return self._move(Axis.Y, "negative", duration, speed)

    def move_up(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        """Move claw up for duration seconds."""
        return self._move(Axis.Z, "positive", duration, speed)

    def move_down(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        """Move claw down for duration seconds."""
        return self._move(Axis.Z, "negative", duration, speed)

    def _move(self, axis: Axis, direction: str, duration: float, speed: float) -> bool:
        """Execute a timed movement."""
        if self._safety.is_emergency_stopped:
            logger.warning("Movement blocked: emergency stop active")
            return False

        if not self._safety.check_limit(axis, direction):
            return False

        self._safety.reset_watchdog()
        motor = self._motors[axis]

        if direction == "positive":
            motor.run_positive(speed)
        else:
            motor.run_negative(speed)

        # Wait for duration, checking limits periodically
        start = time.monotonic()
        while time.monotonic() - start < duration:
            if not self._safety.check_limit(axis, direction):
                motor.stop_all()
                return False
            time.sleep(0.01)

        motor.stop_all()
        return True

    # ── Electromagnet commands ──

    def grab(self) -> None:
        """Activate electromagnet to grab an object."""
        self._safety.reset_watchdog()
        self._backend.write(self._pin_map.electromagnet, True)
        self._magnet_active = True
        logger.info("Magnet ON — grabbing")

    def release(self) -> None:
        """Deactivate electromagnet to release object."""
        self._backend.write(self._pin_map.electromagnet, False)
        self._magnet_active = False
        logger.info("Magnet OFF — released")

    # ── State queries ──

    def get_state(self) -> ClawState:
        """Get complete machine state."""
        state = ClawState()
        state.magnet_active = self._magnet_active
        state.limits = self._sensors.get_all_limits()

        for axis, motor in self._motors.items():
            pos, neg = motor.get_states()
            state.motors[f"{axis.name}_pos"] = pos
            state.motors[f"{axis.name}_neg"] = neg

        # Read buttons
        pm = self._pin_map
        state.buttons = {
            "claw_up": not self._backend.read(pm.btn_claw_up),
            "claw_down": not self._backend.read(pm.btn_claw_down),
            "claw_grab": not self._backend.read(pm.btn_claw_grab),
            "crane_left": not self._backend.read(pm.btn_crane_left),
            "crane_right": not self._backend.read(pm.btn_crane_right),
            "crane_forward": not self._backend.read(pm.btn_crane_forward),
            "crane_backward": not self._backend.read(pm.btn_crane_backward),
        }

        state.at_x_left = state.limits.get("x_left", False)
        state.at_y_forward = state.limits.get("y_forward", False)
        state.at_y_backward = state.limits.get("y_backward", False)
        state.at_z_up = state.limits.get("z_up", False)
        state.at_z_down = state.limits.get("z_down", False)
        state.led_on = state.any_motor_active() or self._magnet_active

        return state

    # ── Lifecycle ──

    def emergency_stop(self) -> None:
        """Stop everything immediately."""
        self._safety.emergency_stop()
        self.release()

    def shutdown(self) -> None:
        """Clean shutdown: stop motors, release magnet, cleanup GPIO."""
        for motor in self._motors.values():
            motor.stop_all()
        self.release()
        self._safety.stop()
        self._backend.cleanup()
        logger.info("ClawMachine shut down")
