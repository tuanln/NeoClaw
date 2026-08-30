"""Operator acceptance for the DC reverse fix — Milestone B demo criteria.

Each wheel is driven forward, then reverse, then stopped. You watch and
answer. Ten clean rounds = acceptance passed.

    pip install thingbot-telemetrix
    export THINGBOT_PORT=/dev/cu.usbmodem1101   # macOS; /dev/ttyUSB0 on Linux
    python examples/verify_reverse.py

Motor rail needs its own 7–12V supply — USB alone will not turn the wheels.
Lift the chassis onto a stand first so it cannot drive off the table.
"""
from __future__ import annotations

import os
import sys
import time

ROUNDS = 10
SPEED = 60
DWELL = 1.0


def main() -> int:
    port = os.environ.get("THINGBOT_PORT")
    if not port:
        print("THINGBOT_PORT is not set — see the docstring at the top of this file.")
        return 2

    from neoclaw.hardware.telemetrix_backend import TelemetrixBackend

    backend = TelemetrixBackend(com_port=port)
    passed = 0

    try:
        for round_no in range(1, ROUNDS + 1):
            print(f"\n── Round {round_no}/{ROUNDS} ──")
            for motor in (1, 2, 3, 4):
                print(f"  M{motor}: forward {SPEED}% ...", flush=True)
                backend.control_dc(motor, SPEED)
                time.sleep(DWELL)
                backend.control_dc(motor, 0)
                time.sleep(0.3)

                print(f"  M{motor}: reverse {SPEED}% ...", flush=True)
                backend.control_dc(motor, -SPEED)
                time.sleep(DWELL)
                backend.control_dc(motor, 0)
                time.sleep(0.3)

            answer = input("  Did all four wheels reverse direction? [y/N] ").strip().lower()
            if answer == "y":
                passed += 1
            else:
                print("  Marked as FAIL.")
    finally:
        for motor in (1, 2, 3, 4):
            backend.control_dc(motor, 0)
        backend.shutdown()

    print(f"\nAcceptance: {passed}/{ROUNDS} rounds passed.")
    return 0 if passed == ROUNDS else 1


if __name__ == "__main__":
    sys.exit(main())
