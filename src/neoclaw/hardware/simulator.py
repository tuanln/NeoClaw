"""Full claw machine simulator for learning without hardware."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from neoclaw.hardware.claw_machine import ClawMachine

logger = logging.getLogger(__name__)


@dataclass
class SimulatorState:
    """3D position and state of the simulated claw."""
    x: float = 50.0   # 0 (left limit) to 100 (right)
    y: float = 50.0   # 0 (forward limit) to 100 (backward)
    z: float = 100.0   # 0 (bottom) to 100 (top limit)
    magnet: bool = False
    holding_object: bool = False
    speed_x: float = 20.0  # units per second
    speed_y: float = 20.0
    speed_z: float = 15.0

    def to_dict(self) -> dict:
        return {
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "z": round(self.z, 1),
            "magnet": self.magnet,
            "holding_object": self.holding_object,
        }


@dataclass
class SimObject:
    """An object on the play field that can be picked up."""
    x: float
    y: float
    name: str = "object"
    picked_up: bool = False


class ClawSimulator:
    """Simulates a claw machine without real hardware.

    Wraps ClawMachine with a SimulatorBackend and tracks 3D position.
    """

    def __init__(self):
        self._sim_state = SimulatorState()
        self._objects: list[SimObject] = [
            SimObject(x=30.0, y=30.0, name="teddy_bear"),
            SimObject(x=70.0, y=60.0, name="rubber_duck"),
            SimObject(x=50.0, y=50.0, name="keychain"),
        ]
        self._claw = ClawMachine.create(simulator=True)
        self._log: list[str] = []

    @property
    def machine(self) -> ClawMachine:
        return self._claw

    @property
    def position(self) -> tuple[float, float, float]:
        return (self._sim_state.x, self._sim_state.y, self._sim_state.z)

    def move_left(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        result = self._claw.move_left(duration, speed)
        if result:
            self._sim_state.x = max(0, self._sim_state.x - self._sim_state.speed_x * speed * duration)
        self._log.append(f"move_left(d={duration}, s={speed}) → pos={self._sim_state.x:.1f}")
        return result

    def move_right(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        result = self._claw.move_right(duration, speed)
        if result:
            self._sim_state.x = min(100, self._sim_state.x + self._sim_state.speed_x * speed * duration)
        self._log.append(f"move_right(d={duration}, s={speed}) → pos={self._sim_state.x:.1f}")
        return result

    def move_forward(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        result = self._claw.move_forward(duration, speed)
        if result:
            self._sim_state.y = max(0, self._sim_state.y - self._sim_state.speed_y * speed * duration)
        return result

    def move_backward(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        result = self._claw.move_backward(duration, speed)
        if result:
            self._sim_state.y = min(100, self._sim_state.y + self._sim_state.speed_y * speed * duration)
        return result

    def move_up(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        result = self._claw.move_up(duration, speed)
        if result:
            self._sim_state.z = min(100, self._sim_state.z + self._sim_state.speed_z * speed * duration)
        return result

    def move_down(self, duration: float = 0.5, speed: float = 1.0) -> bool:
        result = self._claw.move_down(duration, speed)
        if result:
            self._sim_state.z = max(0, self._sim_state.z - self._sim_state.speed_z * speed * duration)
        return result

    def grab(self) -> bool:
        """Activate magnet and check if near an object."""
        self._claw.grab()
        self._sim_state.magnet = True

        # Check proximity to objects (only when Z is low enough)
        if self._sim_state.z > 10:
            self._log.append("grab() → too high, nothing grabbed")
            return False

        for obj in self._objects:
            if not obj.picked_up:
                dx = abs(self._sim_state.x - obj.x)
                dy = abs(self._sim_state.y - obj.y)
                if dx < 10 and dy < 10:
                    obj.picked_up = True
                    self._sim_state.holding_object = True
                    self._log.append(f"grab() → grabbed {obj.name}!")
                    return True

        self._log.append("grab() → nothing nearby")
        return False

    def release(self) -> None:
        """Release magnet and drop any held object."""
        self._claw.release()
        self._sim_state.magnet = False
        if self._sim_state.holding_object:
            self._sim_state.holding_object = False
            self._log.append("release() → object dropped")
        else:
            self._log.append("release() → nothing held")

    def get_state(self) -> dict:
        """Get full simulator state."""
        return {
            "claw": self._sim_state.to_dict(),
            "objects": [
                {"name": o.name, "x": o.x, "y": o.y, "picked_up": o.picked_up}
                for o in self._objects
            ],
            "hardware": self._claw.get_state().to_dict(),
        }

    def get_log(self) -> list[str]:
        return list(self._log)

    def shutdown(self) -> None:
        self._claw.shutdown()
