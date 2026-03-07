"""GPIO backend abstraction using Python Protocol."""
from __future__ import annotations

import logging
from typing import Callable, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class IGPIOBackend(Protocol):
    """Protocol for GPIO hardware abstraction."""

    def setup_output(self, pin: int) -> None:
        """Configure a pin as digital output."""
        ...

    def setup_input(self, pin: int, pull_up: bool = True) -> None:
        """Configure a pin as digital input with optional pull-up."""
        ...

    def write(self, pin: int, value: bool) -> None:
        """Set a digital output pin HIGH or LOW."""
        ...

    def read(self, pin: int) -> bool:
        """Read a digital input pin. Returns True if HIGH."""
        ...

    def pwm_start(self, pin: int, frequency: int, duty_cycle: float) -> None:
        """Start PWM on a pin. duty_cycle: 0.0 to 1.0."""
        ...

    def pwm_stop(self, pin: int) -> None:
        """Stop PWM on a pin."""
        ...

    def set_callback(self, pin: int, callback: Callable[[int, bool], None]) -> None:
        """Register a callback for pin state changes. callback(pin, value)."""
        ...

    def cleanup(self) -> None:
        """Release all GPIO resources."""
        ...


class GpiozeroBackend:
    """GPIO backend using gpiozero library."""

    def __init__(self):
        self._outputs: dict[int, object] = {}
        self._inputs: dict[int, object] = {}
        self._pwm: dict[int, object] = {}

    def setup_output(self, pin: int) -> None:
        from gpiozero import DigitalOutputDevice
        self._outputs[pin] = DigitalOutputDevice(pin)

    def setup_input(self, pin: int, pull_up: bool = True) -> None:
        from gpiozero import Button
        self._inputs[pin] = Button(pin, pull_up=pull_up, bounce_time=0.005)

    def write(self, pin: int, value: bool) -> None:
        device = self._outputs.get(pin)
        if device is None:
            return
        if value:
            device.on()  # type: ignore[attr-defined]
        else:
            device.off()  # type: ignore[attr-defined]

    def read(self, pin: int) -> bool:
        device = self._inputs.get(pin)
        if device is None:
            return False
        return bool(device.is_pressed)  # type: ignore[attr-defined]

    def pwm_start(self, pin: int, frequency: int, duty_cycle: float) -> None:
        from gpiozero import PWMOutputDevice
        if pin in self._pwm:
            self._pwm[pin].value = duty_cycle  # type: ignore[attr-defined]
        else:
            device = PWMOutputDevice(pin, frequency=frequency)
            device.value = duty_cycle  # type: ignore[attr-defined]
            self._pwm[pin] = device

    def pwm_stop(self, pin: int) -> None:
        device = self._pwm.pop(pin, None)
        if device is not None:
            device.off()  # type: ignore[attr-defined]
            device.close()  # type: ignore[attr-defined]

    def set_callback(self, pin: int, callback: Callable[[int, bool], None]) -> None:
        device = self._inputs.get(pin)
        if device is None:
            return
        device.when_pressed = lambda: callback(pin, True)  # type: ignore[attr-defined]
        device.when_released = lambda: callback(pin, False)  # type: ignore[attr-defined]

    def cleanup(self) -> None:
        for device in self._outputs.values():
            device.close()  # type: ignore[attr-defined]
        for device in self._inputs.values():
            device.close()  # type: ignore[attr-defined]
        for device in self._pwm.values():
            device.close()  # type: ignore[attr-defined]
        self._outputs.clear()
        self._inputs.clear()
        self._pwm.clear()


class SimulatorBackend:
    """In-memory GPIO simulator for testing without hardware."""

    def __init__(self):
        self._pin_values: dict[int, bool] = {}
        self._pwm_values: dict[int, float] = {}
        self._callbacks: dict[int, Callable[[int, bool], None]] = {}
        self._pin_modes: dict[int, str] = {}  # "input" or "output"

    def setup_output(self, pin: int) -> None:
        self._pin_modes[pin] = "output"
        self._pin_values[pin] = False

    def setup_input(self, pin: int, pull_up: bool = True) -> None:
        self._pin_modes[pin] = "input"
        self._pin_values[pin] = True if pull_up else False

    def write(self, pin: int, value: bool) -> None:
        self._pin_values[pin] = value

    def read(self, pin: int) -> bool:
        return self._pin_values.get(pin, False)

    def pwm_start(self, pin: int, frequency: int, duty_cycle: float) -> None:
        self._pwm_values[pin] = duty_cycle
        self._pin_values[pin] = duty_cycle > 0

    def pwm_stop(self, pin: int) -> None:
        self._pwm_values.pop(pin, None)
        self._pin_values[pin] = False

    def set_callback(self, pin: int, callback: Callable[[int, bool], None]) -> None:
        self._callbacks[pin] = callback

    def cleanup(self) -> None:
        self._pin_values.clear()
        self._pwm_values.clear()
        self._callbacks.clear()
        self._pin_modes.clear()

    # Simulator-specific methods

    def simulate_press(self, pin: int) -> None:
        """Simulate a button press (active LOW)."""
        old = self._pin_values.get(pin, True)
        self._pin_values[pin] = False
        if pin in self._callbacks and old:
            self._callbacks[pin](pin, True)

    def simulate_release(self, pin: int) -> None:
        """Simulate a button release."""
        old = self._pin_values.get(pin, True)
        self._pin_values[pin] = True
        if pin in self._callbacks and not old:
            self._callbacks[pin](pin, False)

    def get_output_state(self, pin: int) -> bool:
        """Get current output pin state."""
        return self._pin_values.get(pin, False)

    def get_pwm_value(self, pin: int) -> float:
        """Get current PWM duty cycle for a pin."""
        return self._pwm_values.get(pin, 0.0)
