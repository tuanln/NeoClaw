"""Shared test fixtures."""
from __future__ import annotations

import pytest

from neoclaw.config.pin_maps import PICOCLAW_PINS
from neoclaw.config.settings import reset_settings
from neoclaw.hardware.gpio_backend import SimulatorBackend
from neoclaw.hardware.motor_controller import create_motor_controllers
from neoclaw.hardware.sensor_manager import SensorManager


@pytest.fixture(autouse=True)
def _reset_settings():
    """Reset settings before each test."""
    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def sim_backend():
    """Create a fresh SimulatorBackend."""
    return SimulatorBackend()


@pytest.fixture
def pin_map():
    """Default pin map for testing."""
    return PICOCLAW_PINS


@pytest.fixture
def motors(sim_backend, pin_map):
    """Create motor controllers with simulator backend."""
    return create_motor_controllers(sim_backend, pin_map)


@pytest.fixture
def sensors(sim_backend, pin_map):
    """Create sensor manager with simulator backend."""
    return SensorManager(sim_backend, pin_map)
