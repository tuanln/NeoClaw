"""Hardware-gated acceptance for the ThingBot DC wire protocol (Milestone B3).

Deselected by default. To run with a board attached:

    pip install thingbot-telemetrix
    export THINGBOT_PORT=/dev/cu.usbmodem1101     # macOS; /dev/ttyUSB0 on Linux
    pytest -m hardware tests/test_hardware/test_telemetrix_integration.py -s

Motor rail needs its own 7–12V supply; USB alone will not turn the wheels.

These checks prove the wire path end to end. Physical direction still needs a
human eye — run examples/verify_reverse.py for the observed 10/10 acceptance.
"""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.hardware

PORT = os.environ.get("THINGBOT_PORT")

@pytest.fixture
def board():
    if not PORT:
        pytest.skip("THINGBOT_PORT not set — no board attached")
    from neoclaw.hardware.telemetrix_backend import TelemetrixBackend

    backend = TelemetrixBackend(com_port=PORT)
    yield backend
    for motor in (1, 2, 3, 4):
        backend.control_dc(motor, 0)
    backend.shutdown()


@pytest.mark.parametrize("motor", [1, 2, 3, 4])
def test_reverse_command_is_accepted_by_the_board(board, motor):
    """Before the int8_t fix a negative speed either raised or ran full forward."""
    board.control_dc(motor, -60)
    board.control_dc(motor, 0)


@pytest.mark.parametrize("motor", [1, 2, 3, 4])
def test_forward_command_is_accepted_by_the_board(board, motor):
    board.control_dc(motor, 60)
    board.control_dc(motor, 0)


def test_full_scale_speeds_do_not_error(board):
    for speed in (100, -100, 0):
        board.control_dc(1, speed)
    board.control_dc(1, 0)
