"""End-to-end demo: ClawRobot pick-and-drop sequence.

Demonstrates the canonical 6-step flow:

    1. home arm
    2. forward 1 second
    3. pick up an object
    4. strafe left 1 second
    5. put down the object
    6. home arm

Run modes:

    # Default — uses simulator (no hardware needed)
    python examples/demo_pick_drop.py

    # With real ThingBot connected
    NEOCLAW_USE_HARDWARE=1 python examples/demo_pick_drop.py

    # With explicit COM port
    NEOCLAW_USE_HARDWARE=1 NEOCLAW_COM_PORT=/dev/cu.usbserial-XXXX \
        python examples/demo_pick_drop.py

Demo criteria (Milestone C3): script finishes without exception, prints
each step, leaves robot in a safe (homed, stopped) state.
"""
from __future__ import annotations

import logging
import os
import sys
import time

# Allow running from repo root without `pip install -e .`
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from neoclaw.hardware.claw_robot import ClawRobot  # noqa: E402


def step(label: str) -> None:
    print(f"  ▶ {label}")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    use_hw = os.environ.get("NEOCLAW_USE_HARDWARE", "").lower() in ("1", "true", "yes")
    com_port = os.environ.get("NEOCLAW_COM_PORT")

    mode = "HARDWARE" if use_hw else "SIMULATOR"
    print(f"\n=== ClawRobot demo · {mode} mode ===\n")

    robot = ClawRobot.create(simulator=not use_hw, com_port=com_port)

    try:
        step("1. Home arm")
        robot.arm.home()
        time.sleep(0.3)

        step("2. Move forward 1 second @ 60% speed")
        robot.forward(speed=60, duration=1.0)

        step("3. Pick up (lower → grip → carry)")
        robot.pick_up()

        step("4. Strafe left 1 second @ 50% speed")
        robot.strafe_left(speed=50, duration=1.0)

        step("5. Put down (lower → release → home)")
        robot.put_down()

        step("6. Home arm")
        robot.arm.home()

        print("\n✓ Demo completed successfully.")
        return 0
    except KeyboardInterrupt:
        print("\n! Interrupted — running emergency stop")
        robot.emergency_stop()
        return 130
    except Exception as exc:
        print(f"\n✗ Demo failed: {type(exc).__name__}: {exc}")
        robot.emergency_stop()
        raise
    finally:
        robot.shutdown()
        print("Robot shut down.")


if __name__ == "__main__":
    sys.exit(main())
