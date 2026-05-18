"""Pin mapping registry for supported boards."""
from __future__ import annotations

from dataclasses import dataclass

# Arduino analog pin aliases (for MEO ThingBot)
A0, A1, A2, A3, A4, A5, A6, A7 = 14, 15, 16, 17, 18, 19, 20, 21


@dataclass(frozen=True)
class PinMap:
    """Pin assignments for a specific board."""

    name: str

    # Electromagnet
    electromagnet: int = 1

    # Motors (output)
    motor_x_left: int = 2
    motor_x_right: int = 3
    motor_y_forward: int = 4
    motor_y_backward: int = 5
    motor_z_up: int = 6
    motor_z_down: int = 7

    # Buttons (input, active LOW)
    btn_claw_up: int = 8
    btn_claw_down: int = 9
    btn_claw_grab: int = 10
    btn_crane_left: int = 11
    btn_crane_right: int = 12
    btn_crane_forward: int = 13
    btn_crane_backward: int = 14

    # Limit switches (input, active LOW)
    limit_x_left: int = 16
    limit_y_forward: int = 17
    limit_y_backward: int = 18
    limit_z_up: int = 19
    limit_z_down: int = 20

    # PWM pins (optional, -1 = disabled → ON/OFF mode)
    pwm_x_left: int = -1
    pwm_x_right: int = -1
    pwm_y_forward: int = -1
    pwm_y_backward: int = -1
    pwm_z_up: int = -1
    pwm_z_down: int = -1

    # Status LED
    led: int = -1  # -1 means use board default (e.g. "LED" on Pico)

    def motor_pins(self) -> list[int]:
        """Return all motor output pins."""
        return [
            self.motor_x_left, self.motor_x_right,
            self.motor_y_forward, self.motor_y_backward,
            self.motor_z_up, self.motor_z_down,
        ]

    def button_pins(self) -> list[int]:
        """Return all button input pins."""
        return [
            self.btn_claw_up, self.btn_claw_down, self.btn_claw_grab,
            self.btn_crane_left, self.btn_crane_right,
            self.btn_crane_forward, self.btn_crane_backward,
        ]

    def limit_pins(self) -> list[int]:
        """Return all limit switch pins."""
        return [
            self.limit_x_left,
            self.limit_y_forward, self.limit_y_backward,
            self.limit_z_up, self.limit_z_down,
        ]


# Original PicoClaw pin mapping (Raspberry Pi Pico W)
PICOCLAW_PINS = PinMap(name="pico_w")

# NEO One pin mapping (remapped for NEO One GPIO header)
NEO_ONE_PINS = PinMap(
    name="neo_one",
    electromagnet=5,
    motor_x_left=6,
    motor_x_right=13,
    motor_y_forward=19,
    motor_y_backward=26,
    motor_z_up=12,
    motor_z_down=16,
    btn_claw_up=17,
    btn_claw_down=27,
    btn_claw_grab=22,
    btn_crane_left=23,
    btn_crane_right=24,
    btn_crane_forward=25,
    btn_crane_backward=8,
    limit_x_left=7,
    limit_y_forward=11,
    limit_y_backward=9,
    limit_z_up=10,
    limit_z_down=4,
    pwm_x_left=18,
    pwm_x_right=15,
    pwm_y_forward=14,
    pwm_y_backward=2,
    pwm_z_up=3,
    pwm_z_down=21,
    led=20,
)

# MEO ThingBot pin mapping (Arduino-based via Telemetrix serial protocol)
# MEO is the first supported external hardware device.
# Pin numbers map to Arduino digital pins on the ThingBot board.
MEO_THINGBOT_PINS = PinMap(
    name="meo_thingbot",
    electromagnet=A5,
    motor_x_left=2,
    motor_x_right=3,
    motor_y_forward=4,
    motor_y_backward=5,
    motor_z_up=6,
    motor_z_down=7,
    btn_claw_up=8,
    btn_claw_down=9,
    btn_claw_grab=10,
    btn_crane_left=11,
    btn_crane_right=12,
    btn_crane_forward=A0,
    btn_crane_backward=A1,
    limit_x_left=A2,
    limit_y_forward=A3,
    limit_y_backward=A4,
    limit_z_up=A6,
    limit_z_down=A7,
    # ThingBot uses analog_write PWM on same motor pins
    pwm_x_left=2,
    pwm_x_right=3,
    pwm_y_forward=4,
    pwm_y_backward=5,
    pwm_z_up=6,
    pwm_z_down=7,
    led=13,
)

PIN_MAPS: dict[str, PinMap] = {
    "pico_w": PICOCLAW_PINS,
    "neo_one": NEO_ONE_PINS,
    "meo_thingbot": MEO_THINGBOT_PINS,
}


def get_pin_map(board: str = "neo_one") -> PinMap:
    """Get pin mapping for the specified board."""
    if board not in PIN_MAPS:
        raise ValueError(f"Unknown board '{board}'. Available: {list(PIN_MAPS.keys())}")
    return PIN_MAPS[board]
