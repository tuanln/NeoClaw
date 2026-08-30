# ClawBot Setup Guide — Huong Dan Lap Rap & Cai Dat

## Gioi thieu

ClawBot la robot di dong voi tay gap, xay dung tren nen tang NeoClaw.
Robot su dung mach MEO ThingBot (ESP32-C3 + PCA9685) lam bo dieu khien I/O,
ket noi voi NEO One SBC (hoac PC) qua USB Serial.

```
┌─────────────────────────────────┐
│   M1(FL) ╲         ╱ M2(FR)    │  ← 4 banh omni
│            ╲       ╱            │
│             [ARM]               │  ← Tay robot 4-DOF
│            ╱       ╲            │
│   M3(RL) ╱         ╲ M4(RR)    │
│                       [SWEEP]   │  ← Can gat
└─────────────────────────────────┘
```

**Thanh phan:**
- **Base**: 4 banh omni/mecanum + 4 DC motor (M1-M4) — di ngang, doc, xoay 360°
- **Arm**: Tay robot 4-DOF + 4 servo (S1-S4) — base/shoulder/elbow/gripper
- **Sweeper**: Can gat 1 servo (S5) — day vat the
- **Brain**: NEO One SBC chay Python + AI Agent

---

## Phan 1: Phan cung can thiet

### 1.1 Danh sach linh kien

| STT | Linh kien | So luong | Ghi chu |
|:---:|-----------|:--------:|---------|
| 1 | MEO ThingBot board | 1 | ESP32-C3 + PCA9685 PWM driver |
| 2 | DC Motor (6V/12V) | 4 | Kem banh omni/mecanum |
| 3 | Banh omni hoac mecanum | 4 | 48mm hoac 60mm |
| 4 | Servo SG90 / MG90S | 5 | S1-S4 cho tay, S5 cho can gat |
| 5 | Khung xe (chassis) | 1 | Acrylic/3D print, 15x15cm |
| 6 | Khung tay robot | 1 | 3D print hoac mua san (4-DOF arm kit) |
| 7 | Can gat (sweeper) | 1 | 3D print hoac thanh nhua |
| 8 | NEO One SBC | 1 | Hoac Raspberry Pi / PC |
| 9 | Cap USB-C | 1 | NEO One ↔ ThingBot |
| 10 | Pin / Nguon | 1 | 7.4V LiPo hoac 6xAA holder |
| 11 | Day noi, oc vit | — | — |

### 1.2 So do noi day

#### DC Motor → ThingBot

```
ThingBot Motor Port    Banh xe
─────────────────────────────
M1                     Front-Left  (banh truoc trai)
M2                     Front-Right (banh truoc phai)
M3                     Rear-Left   (banh sau trai)
M4                     Rear-Right  (banh sau phai)
```

> **Luu y**: Kiem tra chieu quay. Khi goi `forward()`, tat ca 4 banh phai quay
> cung chieu tien. Neu banh quay nguoc, dao 2 day cua motor do tren ThingBot.

#### Servo → ThingBot

```
ThingBot Servo Port    Khop tay robot
─────────────────────────────────────
S1                     Base (xoay de tay, 0-180°)
S2                     Shoulder (vai, 0-180°)
S3                     Elbow (khuyu, 0-180°)
S4                     Gripper (kep, 0=mo / 90=dong)
S5                     Sweeper (can gat, 0-180°)
```

#### Nguon dien

```
Pin 7.4V LiPo ──→ ThingBot VIN (7-12V)
                   ThingBot cap nguon cho motor + servo qua PCA9685

NEO One ─── USB-C ──→ ThingBot (data + 5V backup)
```

> **Quan trong**: Motor can nguon rieng (7-12V). USB 5V khong du dong cho 4 motor.

### 1.3 Lap rap

1. **Gan 4 motor** vao chassis, lap banh omni
2. **Gan khung tay robot** o giua chassis
3. **Lap 4 servo** (S1-S4) vao khung tay theo thu tu base → shoulder → elbow → gripper
4. **Gan servo S5** (sweeper) o canh chassis
5. **Noi day motor** M1-M4 vao cong motor tren ThingBot
6. **Noi day servo** S1-S5 vao cong servo tren ThingBot
7. **Noi pin** vao ThingBot VIN
8. **Noi cap USB-C** tu NEO One den ThingBot

---

## Phan 2: Nap firmware ThingBot

### 2.1 Cai dat PlatformIO

```bash
# Cai PlatformIO CLI
pip3 install platformio

# Hoac dung VS Code extension: PlatformIO IDE
```

### 2.2 Clone firmware

```bash
git clone https://github.com/tuanln/thingbot-telemetrix-arduino.git
cd thingbot-telemetrix-arduino
```

### 2.3 Kiem tra cau hinh

Firmware mac dinh ho tro day du ClawBot. Kiem tra `src/main.cpp`:

```cpp
#define THINGBOT_EXTENDED 1   // Bat tinh nang DC/Servo/Buzzer/LED
#define ARDUINO_ID 1          // ID board (mac dinh 1)
```

### 2.4 Nap firmware

```bash
# Cam ThingBot vao may tinh qua USB-C

# Build va upload
pio run --target upload

# Xem serial monitor (kiem tra)
pio device monitor --baud 115200
```

> **Loi thuong gap:**
> - `No device found`: Kiem tra cap USB, thu cong COM khac
> - `Upload failed`: Giu nut BOOT tren ESP32-C3 khi nap
> - Tren macOS: cai driver CP2102/CH340 neu can

### 2.5 Kiem tra firmware

Sau khi nap, ThingBot se san sang nhan lenh Telemetrix qua Serial 115200 baud.
LED tren board nhay 1 lan khi khoi dong thanh cong.

---

## Phan 3: Cai dat NeoClaw (phan mem Python)

### 3.1 Clone va cai dat

```bash
git clone https://github.com/tuanln/NeoClaw.git
cd NeoClaw

# Cai dat tat ca dependencies
pip3 install -e ".[all]"
```

### 3.2 Cai dat thu vien ThingBot Python

```bash
pip3 install thingbot-telemetrix
```

### 3.3 Cau hinh

Tao file cau hinh user (tuy chon):

```bash
mkdir -p ~/.neoclaw
```

Tao `~/.neoclaw/config.toml`:

```toml
[hardware]
robot_profile = "claw_robot"
gpio_library = "telemetrix"
com_port = ""                 # de trong = tu dong tim USB serial
arduino_instance_id = 1

[ai]
provider = "gemini"
model = "gemini-2.5-flash"
api_key = ""                  # hoac set GEMINI_API_KEY env var
```

### 3.4 Kiem tra ket noi

```bash
# Cam ThingBot vao NEO One / PC qua USB-C
# Thu ngay bang Python:

python3 -c "
from neoclaw.hardware.thingbot import ThingBot
from neoclaw.hardware.models import MotorID, ServoID

bot = ThingBot.connect()
print('ThingBot connected!')
print(bot.get_state())
bot.shutdown()
"
```

Neu thanh cong, ban se thay `ThingBot connected!` va trang thai cua board.

---

## Phan 4: Su dung ClawBot

### 4.1 Dieu khien co ban (Python)

```python
from neoclaw.hardware.claw_robot import ClawRobot
from neoclaw.hardware.models import JointName, LedID

# Ket noi
robot = ClawRobot.create()

# === DI CHUYEN ===
robot.forward(speed=60, duration=1.0)      # tien 1 giay
robot.backward(speed=60, duration=1.0)     # lui
robot.strafe_left(speed=50, duration=0.5)  # di ngang trai
robot.strafe_right(speed=50, duration=0.5) # di ngang phai
robot.turn_left(speed=40, duration=0.3)    # xoay trai
robot.turn_right(speed=40, duration=0.3)   # xoay phai
robot.stop()                                # dung

# === TAY ROBOT ===
robot.arm.home()                            # ve vi tri home
robot.arm.move_to(base=45, shoulder=60, elbow=120)  # di chuyen tay
robot.arm.grip()                            # dong kep
robot.arm.release()                         # mo kep
robot.arm.pose("carry")                     # tu the mang do
robot.arm.pose("reach_down")                # tu the voi xuong

# === HANH DONG KET HOP ===
robot.pick_up()                             # ha tay + gap + nang
robot.forward(speed=40, duration=2.0)       # mang di
robot.put_down()                            # ha tay + tha

# === CAN GAT ===
robot.arm.sweep()                           # gat 1 lan
robot.arm.set_sweeper(45)                   # dat can gat goc 45°

# === PHAN HOI ===
robot.beep(100, 0.2)                        # keu beep
robot.set_led(LedID.LED1, 100)              # bat LED

# === TAT ===
robot.shutdown()
```

### 4.2 Dieu khien bang CLI

```bash
# Che do dieu khien truc tiep
neoclaw control --robot claw_robot

# Che do simulator (khong can hardware)
neoclaw control --simulator
```

### 4.3 Dieu khien truc tiep ThingBot (low-level)

```python
from neoclaw.hardware.thingbot import ThingBot
from neoclaw.hardware.models import MotorID, ServoID, LedID

bot = ThingBot.connect()

# Motor
bot.dc(MotorID.M1, 80)      # M1 tien 80%
bot.dc(MotorID.M1, -60)     # M1 lui 60%
bot.dc(MotorID.M1, 0)       # dung

# Servo
bot.servo(ServoID.S1, 90)   # S1 goc 90°
bot.servo(ServoID.S4, 70)   # S4 (gripper) dong

# Buzzer + LED
bot.buzzer(100)
bot.led(LedID.LED1, 100)

bot.shutdown()
```

### 4.4 Omni Base chi tiet

```python
from neoclaw.hardware.thingbot import ThingBot
from neoclaw.hardware.omni_base import OmniBase

bot = ThingBot.connect()
base = OmniBase(bot)

# Di chuyen co ban
base.forward(speed=60, duration=1.0)
base.strafe_right(speed=50, duration=0.5)
base.rotate_cw(speed=40, duration=0.3)

# Di cheo
base.diagonal_forward_right(speed=60, duration=1.0)
base.diagonal_backward_left(speed=50, duration=0.5)

# Vector drive (di chuyen tu do)
# vx = tien/lui, vy = trai/phai, omega = xoay
base.drive(vx=0.5, vy=0.3, omega=0.1, speed=60)

base.stop()
bot.shutdown()
```

### 4.5 Robot Arm chi tiet

```python
from neoclaw.hardware.thingbot import ThingBot
from neoclaw.hardware.robot_arm import RobotArm
from neoclaw.hardware.models import JointName

bot = ThingBot.connect()
arm = RobotArm(bot, smooth=True)  # smooth=True: di chuyen muot

# Dieu khien tung khop
arm.set_joint(JointName.BASE, 45)       # xoay de 45°
arm.set_joint(JointName.SHOULDER, 60)   # nang vai
arm.set_joint(JointName.ELBOW, 120)     # gap khuyu
arm.set_joint(JointName.GRIPPER, 70)    # dong kep (0=mo, 90=dong)

# Preset poses
arm.home()                    # ve giua
arm.pose("reach_forward")    # voi toi truoc
arm.pose("reach_down")       # voi xuong
arm.pose("carry")            # tu the mang
arm.pose("rest")             # nghi

# Grip / Release
arm.grip(force=70)            # dong kep luc 70
arm.release()                 # mo kep

# Sweeper
arm.sweep()                   # gat 1 lan (0° → 180°)
arm.set_sweeper(90)           # dat goc

# Doc goc hien tai
print(arm.get_angles())
# {'BASE': 45, 'SHOULDER': 60, 'ELBOW': 120, 'GRIPPER': 70, 'SWEEPER': 90}

bot.shutdown()
```

---

## Phan 5: AI Agent — Tro ly thong minh

NeoClaw tich hop AI Agent giup hoc sinh hoc Python qua dieu khien robot.

### 5.1 Cau hinh AI

**Cach 1: Gemini API (khuyen nghi)**

```bash
# Lay API key tai: https://aistudio.google.com/app/apikey
export GEMINI_API_KEY="your-api-key-here"
```

**Cach 2: Ollama (local, mien phi)**

```bash
# Cai Ollama: https://ollama.com
ollama pull gemma2:2b    # model nho, chay nhanh

# Cau hinh trong ~/.neoclaw/config.toml:
# [ai]
# provider = "ollama"
# model = "gemma2:2b"
```

**Cach 3: Offline (khong can internet)**

```toml
# ~/.neoclaw/config.toml
[ai]
provider = "offline"
# Se dung rule-based hints thay vi LLM
```

### 5.2 Cac che do AI Agent

| Che do | Mo ta | Lenh |
|--------|-------|------|
| **TEACH** | Hoc Python qua bai tap + hint | `neoclaw teach` |
| **FREE_PLAY** | Tu do dieu khien + AI ho tro | `neoclaw control --ai` |
| **VOICE_CONTROL** | Noi tieng Viet/Anh → robot thuc hien | `neoclaw control --voice` |
| **CHALLENGE** | Thu thach game hoa | `neoclaw teach --challenge` |

### 5.3 Hoc Python voi AI Tutor

```bash
# Bat dau bai hoc (co simulator, khong can hardware)
neoclaw teach --simulator

# Hoac voi hardware that
neoclaw teach
```

AI Tutor se:
1. Huong dan tung buoc, tu co ban den nang cao
2. Cho bai tap va kiem tra code
3. Goi y 4 cap do: Nudge → Guidance → Explicit → Solution
4. Danh gia va theo doi tien do

**6 bai hoc:**

| Bai | Ten | Khai niem Python |
|:---:|-----|-----------------|
| 1 | Hello ClawBot! | import, goi ham |
| 2 | Di chuyen | tham so (speed, duration) |
| 3 | Lap di lap lai | vong lap for |
| 4 | Ra quyet dinh | if/else |
| 5 | Viet ham rieng | def, function |
| 6 | Gap va tha | ket hop tat ca |

### 5.4 Dieu khien bang tieng Viet

```bash
neoclaw control --voice --simulator
```

Noi hoac go:
- "di tien" → `robot.forward()`
- "sang trai 2 giay" → `robot.strafe_left(duration=2.0)`
- "gap" → `robot.arm.grip()`
- "tha" → `robot.arm.release()`
- "ha xuong roi gap" → `robot.arm.pose("reach_down")` + `robot.arm.grip()`
- "dung lai" → `robot.emergency_stop()`

AI Agent hieu ca tieng Viet khong dau va tieng Anh.

### 5.5 Student Code Sandbox

Hoc sinh viet code Python, code chay trong sandbox an toan:

```python
# Bai tap: Di chuyen robot va gap vat
from claw import *

# Di tien
forward(speed=60, duration=1.0)

# Ha tay xuong
arm_pose("reach_down")

# Gap
grip()

# Nang len
arm_pose("carry")

# Di lui
backward(speed=40, duration=1.5)

# Tha
release()
```

**An toan:**
- Code chay trong subprocess rieng biet
- Co timeout (mac dinh 30 giay)
- Gioi han so lenh (mac dinh 5000)
- Khong truy cap truc tiep hardware — chi qua proxy

---

## Phan 6: Che do Simulator

Khong co hardware? Dung simulator de hoc va test:

```python
from neoclaw.hardware.claw_robot import ClawRobot

# Tao robot simulator
robot = ClawRobot.create(simulator=True)

# Dung nhu binh thuong — moi lenh duoc log thay vi gui den hardware
robot.forward(speed=60, duration=1.0)
robot.arm.grip()
print(robot.get_state().to_dict())

robot.shutdown()
```

```bash
# CLI simulator
neoclaw control --simulator
neoclaw teach --simulator
```

---

## Phan 7: Xu ly su co

### Ket noi ThingBot

| Van de | Nguyen nhan | Cach xu ly |
|--------|-------------|------------|
| `No device found` | Cap USB / driver | Thu cap khac. Cai driver CP2102/CH340 |
| `Permission denied` (Linux) | Quyen serial port | `sudo usermod -a -G dialout $USER` roi logout/login |
| `Board not responding` | Firmware chua nap | Nap lai firmware theo Phan 2 |
| `Timeout connecting` | Sai baud rate | Dam bao 115200. Kiem tra `platformio.ini` |

### Motor

| Van de | Nguyen nhan | Cach xu ly |
|--------|-------------|------------|
| Motor khong quay | Thieu nguon | Kiem tra pin VIN (7-12V). USB khong du dong |
| Motor quay nguoc | Dao day | Doi 2 day cua motor do tren ThingBot |
| Robot di lech | Toc do khong deu | Chinh speed tung banh trong code |
| **Di tien duoc nhung khong lui / khong di ngang** | **Firmware cu truoc 30/08/2026** | **Nap lai firmware**: `cd thingbot-telemetrix-arduino && pio run -t upload`. Xem muc "Giao thuc speed co dau" ben duoi |
| `strafe_left` / `rotate_cw` chay nhu di tien | Nhu tren — byte speed doc la unsigned | Nhu tren. Kiem chung: `python examples/verify_reverse.py` |

#### Giao thuc speed co dau

Lenh DC_WRITE mang `speed` trong **mot byte, ma hoa bu hai** cho so co dau -100..100. Firmware giai
ma bang `tbmath::decodeSpeedByte`, Python ma hoa bang
`neoclaw.hardware.telemetrix_backend.encode_speed_byte`.

Truoc 30/08/2026 firmware doc byte nay la `uint8_t` roi kiem tra `if (speed >= 0)` — luon dung voi
kieu khong dau, nen nhanh dao chieu la ma chet. Hau qua tren mach that: `backward`, `strafe_left`,
`strafe_right`, `rotate_cw`, `rotate_ccw` va moi `diagonal_*` deu **chay toi** thay vi lui/ngang,
voi duty khong xac dinh (gia tri am tran qua thanh ghi 12-bit cua PCA9685).

Gia tri tien 0..100 khong doi tren day. Vi vay mach chay firmware cu van di tien binh thuong —
day la ly do trieu chung de bi bo qua khi chi thu `forward()`.

Nghiem thu sau khi nap lai:

```bash
export THINGBOT_PORT=/dev/cu.usbmodem1101   # macOS; /dev/ttyUSB0 tren Linux
python examples/verify_reverse.py           # 10 vong, tung banh tien roi lui
```

### Servo

| Van de | Nguyen nhan | Cach xu ly |
|--------|-------------|------------|
| Servo rung / giat | Thieu dong | Dung nguon rieng cho servo (5V 2A+) |
| Servo khong quay het | Vuot goc | Kiem tra JOINT_LIMITS trong models.py |
| Tay robot run | smooth=False | Dat `smooth=True` khi tao RobotArm |

### AI Agent

| Van de | Nguyen nhan | Cach xu ly |
|--------|-------------|------------|
| "AI not available" | Thieu API key | Set `GEMINI_API_KEY` hoac cai Ollama |
| Tra loi cham | Model lon | Doi sang model nho: gemini-2.0-flash hoac gemma2:2b |
| Khong hieu tieng Viet | Input co dau | Viet khong dau cung OK: "di tien", "sang trai" |

---

## Phan 8: Ma nguon mo

### Repository chinh

| Repo | Mo ta | Link |
|------|-------|------|
| **NeoClaw** | Phan mem Python (AI, Education, IoT) | https://github.com/tuanln/NeoClaw |
| **ThingBot Firmware** | Arduino firmware cho ESP32-C3 | https://github.com/tuanln/thingbot-telemetrix-arduino |
| **ThingBot Python** | Thu vien Python giao tiep serial | `pip install thingbot-telemetrix` |

### Cau truc du an NeoClaw

```
NeoClaw/
├── src/neoclaw/
│   ├── hardware/
│   │   ├── thingbot.py          # ThingBot direct: dc, servo, buzzer, led
│   │   ├── omni_base.py         # 4-wheel omni kinematics
│   │   ├── robot_arm.py         # 4-DOF arm + sweeper
│   │   ├── claw_robot.py        # ClawRobot = OmniBase + RobotArm
│   │   ├── claw_machine.py      # Legacy: may gap 3 truc
│   │   ├── gpio_backend.py      # GPIO abstraction protocol
│   │   ├── telemetrix_backend.py # Bridge → ThingBot serial
│   │   ├── models.py            # Enums, dataclasses
│   │   ├── motor_controller.py  # Legacy: per-axis motor
│   │   ├── sensor_manager.py    # Limit switches
│   │   ├── safety.py            # Watchdog, emergency stop
│   │   └── simulator.py         # Physics simulator
│   ├── agent/                   # AI Agent (LLM, NL, code executor)
│   ├── education/               # 6 bai hoc, bai tap, hint system
│   ├── iot/                     # MQTT, WebSocket, device registry
│   ├── analytics/               # SQLite logging, progress tracking
│   ├── web/                     # FastAPI dashboard
│   ├── cli/                     # Click CLI commands
│   ├── config/                  # TOML settings, pin maps
│   └── utils/                   # EventBus, debouncer, i18n
├── tests/                       # 33 unit tests
├── docs/                        # Tai lieu kien truc
├── picoclaw-source/             # Reference: PicoClaw firmware goc
├── defaults.toml                # Cau hinh mac dinh
└── pyproject.toml               # Python project config
```

### Dong gop

```bash
# Fork + clone
git clone https://github.com/YOUR_USERNAME/NeoClaw.git
cd NeoClaw

# Cai dev dependencies
pip3 install -e ".[dev]"

# Chay tests
pytest

# Tao branch, code, push, tao PR
```

### License

MIT — Tu do su dung, chinh sua, phan phoi.

---

## Quick Start (tom tat)

```bash
# 1. Nap firmware ThingBot
git clone https://github.com/tuanln/thingbot-telemetrix-arduino.git
cd thingbot-telemetrix-arduino
pio run --target upload

# 2. Cai NeoClaw
git clone https://github.com/tuanln/NeoClaw.git
cd NeoClaw
pip3 install -e ".[all]"
pip3 install thingbot-telemetrix

# 3. Set API key (tuy chon, cho AI)
export GEMINI_API_KEY="your-key"

# 4. Chay!
neoclaw teach --simulator        # hoc voi simulator
neoclaw teach                    # hoc voi hardware that
neoclaw control --simulator      # dieu khien tu do
```
