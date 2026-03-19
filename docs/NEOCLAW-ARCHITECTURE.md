# NeoClaw — Kien Truc He Thong

## Tong quan

NeoClaw la nen tang giao duc Python + IoT, su dung robot lam thiet bi hoc tap.
Ho tro nhieu loai robot: Claw Machine (may gap), Claw Robot (xe omni + tay robot), va mo rong them.

**Phan cung chinh**: MEO ThingBot (ESP32-C3 + PCA9685 PWM driver)
**Giao tiep**: NEO One SBC ↔ ThingBot qua USB Serial (Telemetrix protocol, 115200 baud)

## Kien truc tong the

```
+--------------------------------------------------------------------+
|                        CLI / Web UI / AI Agent                      |
|    neoclaw control | neoclaw teach | FastAPI Dashboard              |
+-------------------+--------------------+---------------------------+
|   ClawRobot       |    ClawMachine     |   (Future: OttoBiped)     |
|   (xe omni +      |    (may gap 3 truc |   (robot nhay 4 servo)    |
|    tay robot)      |     + electromagnet)|                          |
+--------+----------+--------+-----------+--------------------------+
|        |                   |                                       |
|  +-----+------+    +-------+-------+                               |
|  | OmniBase   |    | MotorController|   ← Tang dieu phoi          |
|  | (4 banh)   |    | (per-axis PWM) |                              |
|  +-----+------+    +-------+-------+                               |
|        |                   |                                       |
|  +-----+------+            |                                       |
|  | RobotArm   |            |                                       |
|  | (4-DOF +   |            |                                       |
|  |  sweeper)  |            |                                       |
|  +-----+------+            |                                       |
|        |                   |                                       |
+--------+-------------------+---------------------------------------+
|                     ThingBot                                       |
|    dc(M1-M4) | servo(S1-S5) | buzzer | led | switch               |
+---------------------------+----------------------------------------+
|                   IGPIOBackend (Protocol)                          |
+------------------+-------------------+----------------------------+
| TelemetrixBackend| GpiozeroBackend   | SimulatorBackend           |
| (NEO One →       | (direct GPIO,     | (testing,                  |
|  ThingBot serial)|  no ThingBot)     |  no hardware)              |
+------------------+-------------------+----------------------------+
        |
   USB/Serial to MEO ThingBot (ESP32-C3 + PCA9685)
```

## MEO ThingBot — Thiet bi I/O

### Phan cung

| Thanh phan | Chi tiet |
|------------|----------|
| **MCU** | ESP32-C3-DevKitM-1 |
| **PWM Driver** | PCA9685 (I2C, 16 kenh, 12-bit) |
| **DC Motor** | 4 cai (M1-M4), bidirectional, speed 0-100 |
| **Servo** | 5 cai (S1-S5), angle 0-180° |
| **Buzzer** | 1 (PCA9685 ch14) |
| **LED** | 2 (LED1=ch15, LED2=ch13) |
| **Switch** | 1 (SW3, ESP32-C3 GPIO 3, INPUT_PULLUP) |
| **Serial** | USB CDC 115200 baud |

### PCA9685 Channel Mapping

```
PCA9685 Channel:  0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15
                 M4B M4A M1A M1B M2A M2B  -  M3A M3B/S5 S4  S3  S2  S1 LED2 BUZ LED1
                 └─M4─┘ └─M1─┘ └─M2─┘     └─M3─┘
```

| ID | PCA9685 ch(A/B) | Chuc nang |
|----|----------------|-----------|
| M1 | 2 / 3 | DC Motor 1 (A=tien, B=lui) |
| M2 | 4 / 5 | DC Motor 2 |
| M3 | 7 / 8 | DC Motor 3 |
| M4 | 1 / 0 | DC Motor 4 |
| S1 | 12 | Servo 1 |
| S2 | 11 | Servo 2 |
| S3 | 10 | Servo 3 |
| S4 | 9 | Servo 4 |
| S5 | 8 | Servo 5 |
| BUZZER | 14 | Buzzer |
| LED1 | 15 | LED 1 |
| LED2 | 13 | LED 2 |

### Telemetrix Protocol

Giao thuc nhi phan qua Serial 115200 baud:

```
NEO One (Python)  --->  [length, command_id, param1, param2, ...]  --->  ThingBot (ESP32-C3)
NEO One (Python)  <---  [length, report_id,  data1,  data2, ...]  <---  ThingBot (ESP32-C3)
```

#### Commands (NEO One → ThingBot)

| Command | ID | Params | Mo ta |
|---------|---:|--------|-------|
| SERIAL_LOOP_BACK | 0 | [data] | Kiem tra ket noi |
| SET_PIN_MODE | 1 | [pin, mode, report] | Cau hinh GPIO pin |
| DIGITAL_WRITE | 2 | [pin, value] | Ghi digital 0/1 |
| DIGITAL_READ | 3 | [pin] | Doc digital |
| ANALOG_WRITE | 4 | [pin, msb, lsb] | Ghi PWM |
| ANALOG_READ | 5 | [pin] | Doc analog |
| ARE_YOU_THERE | 6 | — | Ping board |
| **DC_WRITE** | **7** | **[motor, speed]** | **Dieu khien DC motor (M1-M4, speed 0-100)** |
| **SERVO_WRITE** | **8** | **[servo, angle]** | **Dieu khien servo (S1-S5, angle 0-180)** |
| **BUZZER_WRITE** | **9** | **[frequency]** | **Buzzer (0=off)** |
| **LED_WRITE** | **10** | **[led, state]** | **LED (0-100 brightness)** |

#### Reports (ThingBot → NEO One)

| Report | ID | Data | Mo ta |
|--------|---:|------|-------|
| DIGITAL_REPORT | 2 | [pin, value] | Thay doi pin digital |
| ANALOG_REPORT | 4 | [pin, msb, lsb] | Gia tri analog |
| I_AM_HERE | 6 | [board_id] | Phan hoi ping |
| DHT_REPORT | 11 | [pin, hum_hi, hum_lo, temp_hi, temp_lo] | Nhiet do & do am |
| **THINGBOT_SW_REPORT** | **12** | **[pin, value]** | **Switch thay doi (SW3)** |

### PCA9685 Value Mapping (trong firmware)

```c
// Motor speed: 0-100 → PCA9685 duty 0-4095
uint16_t map_speed_to_pwm(int value) {
    return map(value, 0, 100, 0, 4095);
}

// Servo angle: 0-180° → PCA9685 pulse 150-600
uint16_t map_angle_to_pwm(int angle) {
    return map(angle, 0, 180, 150, 600);
}
```

## Robot Profiles

### 1. Claw Robot (phien ban chinh — xe omni + tay robot)

```
┌─────────────────────────────────┐
│   M1(FL) ╲         ╱ M2(FR)    │  ← 4 banh omni (DC motor)
│            ╲       ╱            │
│             [ARM]               │  ← Tay robot 4-DOF (servo)
│            ╱       ╲            │     S1=base, S2=shoulder
│   M3(RL) ╱         ╲ M4(RR)    │     S3=elbow, S4=gripper
│                       [SWEEP]   │  ← Can gat (S5)
└─────────────────────────────────┘
```

| Thanh phan | ThingBot | Chuc nang |
|------------|----------|-----------|
| **OmniBase** | M1-M4 | Xe 4 banh omni — di ngang, doc, xoay |
| **RobotArm** | S1-S4 | Tay robot 4-DOF: base(yaw) + shoulder + elbow + gripper |
| **Sweeper** | S5 | Can gat — day vat the |
| **Buzzer** | Buzzer | Phan hoi am thanh |
| **LEDs** | LED1, LED2 | Trang thai |
| **Switch** | SW3 | Emergency stop |

#### OmniBase Kinematics (banh mecanum)

```
Forward:     M1+ M2+ M3+ M4+     Strafe R:    M1+ M2- M3- M4+
Backward:    M1- M2- M3- M4-     Strafe L:    M1- M2+ M3+ M4-
Rotate CW:   M1+ M2- M3+ M4-     Diag FR:     M1+ M2= M3= M4+
Rotate CCW:  M1- M2+ M3- M4+     Diag FL:     M1= M2+ M3+ M4=
```

#### RobotArm Joints

```
Side view:
         S2 (shoulder, 0-180°)
          ╲
           ╲ upper arm
            ╲
             S3 (elbow, 0-180°)
             ╱
            ╱ forearm
           ╱
        S4 [gripper, 0-90°]

Top view: S1 (base, 0-180°) rotates toan bo tay
```

#### Preset Poses

| Pose | S1 (base) | S2 (shoulder) | S3 (elbow) | S4 (gripper) |
|------|:---------:|:-------------:|:----------:|:------------:|
| home | 90° | 90° | 90° | open |
| reach_forward | 90° | 45° | 135° | open |
| reach_down | 90° | 30° | 60° | open |
| carry | 90° | 120° | 60° | grip |
| rest | 90° | 150° | 30° | open |

### 2. Claw Machine (legacy — may gap 3 truc)

```
+---------------------+          USB/Serial          +-------------------+
|     NEO One SBC     | <=========================>  |   MEO ThingBot    |
|  (Linux + Python)   |      Telemetrix Protocol     |   (ESP32-C3)      |
|                     |                              |                   |
|  ClawMachine API    |    [len, cmd, param1, ...]   |  PCA9685 PWM      |
|  - 3-axis gantry    |  ========================>   |  - DC motors      |
|  - Electromagnet    |  <========================   |  - Limit switches |
|  - Limit switches   |    [len, report, data...]    |                   |
+---------------------+                              +-------------------+
```

Van tuong thich nguoc voi code cu. ClawMachine dung IGPIOBackend truc tiep.

### 3. Otto Biped (tuong lai)

| Servo | Vai tro |
|-------|---------|
| S1 | Chan trai (hip) |
| S2 | Chan phai (hip) |
| S3 | Ban chan trai |
| S4 | Ban chan phai |

4 servo dieu khien di bo kieu biped. Tham khao: https://www.ottodiy.com/
Can port oscillator algorithm tu OttoDIYLib de servo di muot.

## Tang phan mem chi tiet

### hardware/ — Hardware Abstraction

| File | Mo ta | Phu thuoc |
|------|-------|-----------|
| **thingbot.py** | ThingBot truc tiep: dc(M1-M4), servo(S1-S5), buzzer, led, switch | TelemetrixBackend |
| **omni_base.py** | OmniBase: 4 banh omni, mecanum kinematics, vector drive | ThingBot |
| **robot_arm.py** | RobotArm: 4-DOF + sweeper, preset poses, smooth movement | ThingBot |
| **claw_robot.py** | ClawRobot: OmniBase + RobotArm + feedback. High-level API | OmniBase, RobotArm, ThingBot |
| **claw_machine.py** | ClawMachine: legacy may gap 3 truc | IGPIOBackend |
| **gpio_backend.py** | IGPIOBackend protocol + GpiozeroBackend + SimulatorBackend | — |
| **telemetrix_backend.py** | TelemetrixBackend: bridge IGPIOBackend → ThingBot serial | thingbot-telemetrix |
| **motor_controller.py** | DCMotorController: legacy per-axis PWM motor | IGPIOBackend |
| **sensor_manager.py** | SensorManager: limit switch monitoring | IGPIOBackend |
| **safety.py** | SafetyManager: watchdog, limit enforce, emergency stop | MotorController, SensorManager |
| **simulator.py** | ClawSimulator: 3D physics simulation | ClawMachine |
| **models.py** | Enums & dataclasses cho tat ca robot profiles | — |

### Phan tang dependency

```
ClawRobot (claw_robot.py)
├── OmniBase (omni_base.py)
│   └── ThingBot.dc(M1-M4)
├── RobotArm (robot_arm.py)
│   └── ThingBot.servo(S1-S5)
└── ThingBot (thingbot.py)
    └── TelemetrixBackend (telemetrix_backend.py)
        └── thingbot-telemetrix (pip package)
            └── USB Serial → ESP32-C3 + PCA9685

ClawMachine (claw_machine.py)  ← legacy, doc lap
├── MotorController (motor_controller.py)
├── SensorManager (sensor_manager.py)
├── SafetyManager (safety.py)
└── IGPIOBackend
    ├── TelemetrixBackend
    ├── GpiozeroBackend
    └── SimulatorBackend
```

## Cach su dung

### Claw Robot (moi)

```python
from neoclaw.hardware.claw_robot import ClawRobot

# Ket noi hardware
robot = ClawRobot.create()
# Hoac simulator
robot = ClawRobot.create(simulator=True)

# Di chuyen xe
robot.forward(speed=60, duration=1.0)
robot.strafe_right(speed=50, duration=0.5)
robot.turn_left(speed=40, duration=0.3)

# Dieu khien tay
robot.arm.move_to(base=45, shoulder=60, elbow=120)
robot.arm.grip()
robot.arm.pose("carry")

# Hanh dong ket hop
robot.pick_up()    # ha tay + gap + nang
robot.forward(speed=40, duration=2.0)
robot.put_down()   # ha tay + tha + ve home

# Can gat
robot.arm.sweep()

# Phan hoi
robot.beep(100, 0.2)
robot.set_led(LedID.LED1, 100)

robot.shutdown()
```

### ThingBot truc tiep (low-level)

```python
from neoclaw.hardware.thingbot import ThingBot
from neoclaw.hardware.models import MotorID, ServoID, LedID

bot = ThingBot.connect()  # auto-detect USB

bot.dc(MotorID.M1, 80)      # motor 1 tien, toc do 80%
bot.dc(MotorID.M1, -60)     # motor 1 lui, toc do 60%
bot.servo(ServoID.S1, 90)   # servo 1 goc 90°
bot.buzzer(440)              # buzzer note A4
bot.led(LedID.LED1, 100)    # LED 1 sang max
bot.shutdown()
```

### Claw Machine (legacy, tuong thich nguoc)

```python
from neoclaw.hardware.claw_machine import ClawMachine

claw = ClawMachine.create(board="meo_thingbot")
claw.move_left(duration=1.0)
claw.grab()
claw.shutdown()
```

## Cau hinh

### defaults.toml

```toml
[hardware]
board = "meo_thingbot"
robot_profile = "claw_robot"    # "claw_robot", "claw_machine", "otto_biped"
gpio_library = "telemetrix"
com_port = ""                   # empty = auto-detect
arduino_instance_id = 1

[hardware.arm]
smooth_movement = true
step_delay_ms = 20              # delay per degree khi smooth movement

[hardware.base]
max_speed = 80                  # max speed cho safety (0-100)
```

## Design Patterns

### 1. ThingBot Layer (moi)
- `ThingBot` class la abstraction truc tiep cua phan cung
- Dung motor/servo number thay vi GPIO pin
- Map 1:1 voi firmware commands (DC_WRITE, SERVO_WRITE, ...)
- Ho tro simulator mode (khong can hardware)

### 2. Composition over Inheritance
- `ClawRobot` = `OmniBase` + `RobotArm` (composition)
- Moi component co the dung doc lap
- `OmniBase` chi biet ve banh xe, `RobotArm` chi biet ve khop

### 3. Protocol-based GPIO Backend (legacy)
- `IGPIOBackend`: Python Protocol cho GPIO truc tiep
- Van ho tro cho `ClawMachine` (may gap cu)
- `ThingBot` class thay the vai tro nay cho robot moi

### 4. Smooth Servo Movement
- Di chuyen servo tung do mot (20ms/step)
- Tranh giat khi servo snap tu goc nay sang goc khac
- Quan trong cho robot arm va Otto biped

### 5. Factory Pattern
- `ClawRobot.create(simulator=True/False)`
- `ThingBot.connect(com_port=...)` hoac `ThingBot.create_simulator()`
- Tu dong chon backend dua tren settings

## Lo trinh

### Da hoan thanh
- [x] ThingBot hardware abstraction (thingbot.py)
- [x] OmniBase 4-wheel omni kinematics (omni_base.py)
- [x] RobotArm 4-DOF + sweeper (robot_arm.py)
- [x] ClawRobot combined API (claw_robot.py)
- [x] Models: MotorID, ServoID, JointName, RobotProfile, States
- [x] TelemetrixBackend enhanced documentation

### Tiep theo
- [ ] Otto Biped profile (4 servo, oscillator algorithm)
- [ ] ClawRobot simulator voi physics
- [ ] Agent integration: them commands cho robot moi
- [ ] Education: bai hoc cho Claw Robot
- [ ] Web dashboard cho Claw Robot

## Tai lieu tham khao

- ThingBot Arduino firmware: https://github.com/tuanln/thingbot-telemetrix-arduino
- ThingBot Python driver: pip install thingbot-telemetrix
- Otto DIY: https://www.ottodiy.com/
- PCA9685 datasheet: NXP Semiconductors
- Mecanum wheel kinematics: https://research.ijcaonline.org/volume113/number3/pxc3901586.pdf
