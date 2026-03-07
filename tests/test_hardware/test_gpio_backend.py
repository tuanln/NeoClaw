"""Tests for GPIO backend."""
from neoclaw.hardware.gpio_backend import SimulatorBackend


def test_simulator_output():
    backend = SimulatorBackend()
    backend.setup_output(1)
    assert backend.get_output_state(1) is False

    backend.write(1, True)
    assert backend.get_output_state(1) is True

    backend.write(1, False)
    assert backend.get_output_state(1) is False


def test_simulator_input_pull_up():
    backend = SimulatorBackend()
    backend.setup_input(8, pull_up=True)
    assert backend.read(8) is True  # Pull-up: default HIGH


def test_simulator_button_press():
    backend = SimulatorBackend()
    backend.setup_input(8, pull_up=True)

    pressed = []
    backend.set_callback(8, lambda pin, val: pressed.append((pin, val)))

    backend.simulate_press(8)
    assert backend.read(8) is False  # Active LOW
    assert len(pressed) == 1
    assert pressed[0] == (8, True)

    backend.simulate_release(8)
    assert backend.read(8) is True


def test_simulator_pwm():
    backend = SimulatorBackend()
    backend.setup_output(1)
    backend.pwm_start(1, 1000, 0.5)
    assert backend.get_pwm_value(1) == 0.5

    backend.pwm_stop(1)
    assert backend.get_pwm_value(1) == 0.0


def test_simulator_cleanup():
    backend = SimulatorBackend()
    backend.setup_output(1)
    backend.setup_input(2)
    backend.cleanup()
    assert backend.get_output_state(1) is False
