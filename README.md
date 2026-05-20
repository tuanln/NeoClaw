# NeoClaw — Agentic Robot Education Platform

[![CI](https://github.com/tuanln/NeoClaw/actions/workflows/ci.yml/badge.svg)](https://github.com/tuanln/NeoClaw/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Hoc Python bang cach dieu khien robot that. Xay dung tren MEO ThingBot + NEO One SBC.

```
┌──────────────────────────────────┐
│   M1(FL) ╲          ╱ M2(FR)    │   4 banh omni (di moi huong)
│            ╲        ╱            │
│              [ARM]               │   Tay robot 4-DOF
│            ╱        ╲            │   (base + shoulder + elbow + gripper)
│   M3(RL) ╱          ╲ M4(RR)    │
│                        [SWEEP]   │   Can gat
└──────────────────────────────────┘
     NEO One (Python + AI)
         ↕ USB Serial
     ThingBot (ESP32-C3 + PCA9685)
         ↕ PWM
     4 DC Motor + 5 Servo + Buzzer + LED
```

## NeoClaw la gi?

NeoClaw la nen tang day lap trinh Python cho hoc sinh thong qua dieu khien robot.
Thay vi hoc tren man hinh, hoc sinh viet code Python de robot **di chuyen, gap do, gat vat** — nhin thay ket qua ngay ngoai doi that.

**3 dieu lam NeoClaw khac biet:**

1. **Robot that** — Xe 4 banh omni + tay robot 4 bac tu do, khong phai simulator
2. **AI Tutor** — Tro ly AI (Gemini/Ollama) huong dan tung buoc, hieu tieng Viet
3. **Ma nguon mo** — MIT license, tu do chinh sua, phu hop truong hoc va makerspace

## Tinh nang

| | Tinh nang | Mo ta |
|---|---|---|
| **Robot** | ClawBot | Xe omni 4 banh (M1-M4) + tay robot 4-DOF (S1-S4) + can gat (S5) |
| **AI** | Tutor thong minh | 4 che do: Teach / Free Play / Voice Control / Challenge |
| **Giao duc** | 6 bai hoc | Tu "Hello ClawBot!" den viet function tu dong gap |
| **Ngon ngu** | Tieng Viet + Anh | Dieu khien bang giong noi: "di tien", "sang trai 2 giay", "gap" |
| **Simulator** | Khong can hardware | Hoc va test day du chi voi laptop |
| **IoT** | MQTT + WebSocket | Dieu khien tu xa, theo doi sensor real-time |
| **Phan tich** | Progress tracking | SQLite log, theo doi tien do hoc sinh |

## Quick Start

### 5 phut bat dau (simulator — khong can hardware)

```bash
git clone https://github.com/tuanln/NeoClaw.git
cd NeoClaw

# Tao venv + cai package
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Smoke test: chay demo end-to-end trong simulator
python examples/demo_pick_drop.py
# Expect: 6 buoc (home → forward → pick_up → strafe_left → put_down → home),
# ket thuc voi "✓ Demo completed successfully."

# Hoc Python voi AI tutor
neoclaw teach --simulator
```

### 5 phut bat dau voi hardware (ThingBot + robot)

```bash
# 1. Nap firmware ThingBot (mot lan)
git clone https://github.com/tuanln/thingbot-telemetrix-arduino.git
cd thingbot-telemetrix-arduino && pio run --target upload && cd ..

# 2. Cai NeoClaw (neu chua)
cd NeoClaw && source .venv/bin/activate
pip install thingbot-telemetrix

# 3. Cam USB-C tu NEO One/PC vao ThingBot — verify cong serial
ls /dev/cu.usbmodem* /dev/ttyUSB*  # macOS / Linux

# 4. Smoke test ket noi thuc
NEOCLAW_USE_HARDWARE=1 python examples/demo_pick_drop.py
# Expect: robot di tien 1s → gap → strafe trai 1s → tha → home.
# Neu motor khong quay: kiem tra nguon LiPo + dau noi PCA9685.

# 5. Mo che do hoc
export GEMINI_API_KEY="your-key"   # tuy chon, cho AI tutor
neoclaw teach
```

> **Chua co AI key?** `neoclaw teach --simulator` van chay duoc — chi mat AI tutor, van co content bai hoc + bai tap.

## Code vi du

### Dieu khien ClawBot

```python
from neoclaw.hardware.claw_robot import ClawRobot

robot = ClawRobot.create()            # ket noi hardware
# robot = ClawRobot.create(simulator=True)  # hoac simulator

# Di chuyen (xe omni — di duoc moi huong)
robot.forward(speed=60, duration=1.0)
robot.strafe_right(speed=50, duration=0.5)
robot.turn_left(speed=40, duration=0.3)

# Tay robot
robot.arm.move_to(base=45, shoulder=60, elbow=120)
robot.arm.grip()
robot.arm.pose("carry")

# Hanh dong ket hop
robot.pick_up()      # ha tay + gap + nang
robot.forward(speed=40, duration=2.0)
robot.put_down()     # ha tay + tha

# Can gat
robot.arm.sweep()

robot.shutdown()
```

### Dieu khien ThingBot truc tiep

```python
from neoclaw.hardware.thingbot import ThingBot
from neoclaw.hardware.models import MotorID, ServoID

bot = ThingBot.connect()          # auto-detect USB
bot.dc(MotorID.M1, 80)           # motor 1 tien 80%
bot.servo(ServoID.S1, 90)        # servo 1 goc 90 do
bot.buzzer(100)                   # keu beep
bot.shutdown()
```

### Hoc sinh viet code (sandbox)

```python
# Bai tap: Di chuyen va gap vat
from claw import *

forward(speed=60, duration=1.0)
arm_pose("reach_down")
grip()
arm_pose("carry")
backward(speed=40, duration=1.5)
release()
```

## Kien truc

```
┌────────────────────────────────────────────────────────┐
│              CLI / Web UI / AI Agent                    │
│         neoclaw teach | control | monitor               │
├──────────────┬─────────────────────────────────────────┤
│  ClawRobot   │    ClawMachine (legacy may gap)          │
├──────┬───────┤                                         │
│OmniBase│RobotArm│                                      │
│(M1-M4)│(S1-S5) │                                       │
├──────┴───────┤                                         │
│           ThingBot                                      │
│  dc() | servo() | buzzer() | led() | switch()          │
├────────────────────────────────────────────────────────┤
│         TelemetrixBackend (USB Serial)                  │
├────────────────────────────────────────────────────────┤
│    ESP32-C3  +  PCA9685 (16ch PWM)                     │
│    4 DC Motor | 5 Servo | Buzzer | 2 LED | Switch      │
└────────────────────────────────────────────────────────┘
```

**Phan tang:**

| Tang | File | Vai tro |
|------|------|---------|
| **API** | `claw_robot.py` | ClawRobot = OmniBase + RobotArm. pick_up(), put_down() |
| **Omni** | `omni_base.py` | Mecanum kinematics: forward, strafe, rotate, vector drive |
| **Arm** | `robot_arm.py` | 4-DOF + sweeper. Smooth servo, preset poses |
| **ThingBot** | `thingbot.py` | Hardware truc tiep: dc(M1-M4), servo(S1-S5), buzzer, led |
| **Backend** | `telemetrix_backend.py` | Bridge Python ↔ ThingBot qua USB Serial |
| **Agent** | `agent/` | AI tutor (Gemini/Ollama), NL interpreter, code sandbox |
| **Education** | `education/` | 6 bai hoc, 14 bai tap, hint system, progress tracking |
| **IoT** | `iot/` | MQTT telemetry, WebSocket, device fleet management |

## Phan cung

### MEO ThingBot

| Thanh phan | Chi tiet |
|------------|----------|
| MCU | ESP32-C3-DevKitM-1 |
| PWM | PCA9685 I2C (16 kenh, 12-bit) |
| DC Motor | 4 (M1-M4), bidirectional, speed 0-100 |
| Servo | 5 (S1-S5), angle 0-180 do |
| Buzzer | 1 (PCA9685 ch14) |
| LED | 2 (PCA9685 ch15, ch13) |
| Switch | SW3 (ESP32-C3 GPIO 3) |
| Giao tiep | USB Serial 115200 baud (Telemetrix protocol) |

### Noi day ClawBot

```
ThingBot M1 → Front-Left wheel      ThingBot S1 → Arm base (yaw)
ThingBot M2 → Front-Right wheel     ThingBot S2 → Shoulder
ThingBot M3 → Rear-Left wheel       ThingBot S3 → Elbow
ThingBot M4 → Rear-Right wheel      ThingBot S4 → Gripper
                                     ThingBot S5 → Sweeper
```

## Tai lieu

| Tai lieu | Mo ta |
|----------|-------|
| [CLAWBOT-SETUP-GUIDE.md](docs/CLAWBOT-SETUP-GUIDE.md) | **Huong dan day du**: linh kien, lap rap, nap firmware, cai dat, su dung, AI, troubleshooting |
| [NEOCLAW-ARCHITECTURE.md](docs/NEOCLAW-ARCHITECTURE.md) | Kien truc he thong, PCA9685 channel map, Telemetrix protocol, robot profiles |
| [PROGRESS.md](docs/PROGRESS.md) | **Progress log** — running session-by-session, doc moi nhat tren cung. Xem TRUOC khi bat dau phien moi. |
| [PRODUCT-BRIEF-NEOONE.md](docs/PRODUCT-BRIEF-NEOONE.md) | **Brief san pham v2.1** (2026-05-18) — kien truc NEO One + ThingBot, MCP tools, lo trinh |
| [PLAN-C3-NEOONE-2026-05-18.md](docs/PLAN-C3-NEOONE-2026-05-18.md) | **Plan dev 5 ngay** — 3 milestone, risk, demo criteria |
| [PICOCLAW-ANALYSIS.md](docs/PICOCLAW-ANALYSIS.md) | Phan tich PicoClaw goc (prototype dau tien) |
| [OPENSOURCE-CLAW-COMPARISON.md](docs/OPENSOURCE-CLAW-COMPARISON.md) | So sanh OpenClaw / PicoClaw / ZeroClaw |

## Cau truc thu muc

```
NeoClaw/
├── src/neoclaw/
│   ├── hardware/          # ThingBot, OmniBase, RobotArm, ClawRobot
│   ├── agent/             # AI Tutor, NL interpreter, code sandbox
│   ├── education/         # 6 bai hoc, bai tap, hint, progress
│   ├── iot/               # MQTT, WebSocket, device registry
│   ├── analytics/         # SQLite logging, student tracking
│   ├── web/               # FastAPI dashboard
│   ├── cli/               # CLI commands (teach, control, deploy)
│   └── config/            # TOML settings, pin maps
├── tests/                 # 70 unit tests (100% pass, < 2s)
├── examples/              # Demo scripts (demo_pick_drop.py)
├── docs/                  # Tai lieu kien truc + huong dan
├── picoclaw-source/       # PicoClaw firmware goc (tham khao)
└── defaults.toml          # Cau hinh mac dinh
```

## Phat trien

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Test suite (70 tests, ~1s)
pytest -q

# Lint
ruff check .

# Auto-fix
ruff check . --fix

# Pre-commit hook (tuy chon)
pip install pre-commit && pre-commit install
```

**CI:** moi push/PR len main tu dong chay `ruff check` + `pytest --cov` tren Python 3.11 va 3.12 (xem [.github/workflows/ci.yml](.github/workflows/ci.yml)).

**Thread safety:** `SensorManager` va `TelemetrixBackend` co lock + snapshot pattern cho callback dispatch — xem [tests/test_hardware/test_thread_safety.py](tests/test_hardware/test_thread_safety.py).

## Giay phep

MIT — Tu do su dung, chinh sua, phan phoi.

## Lien ket

- **ThingBot Firmware**: https://github.com/tuanln/thingbot-telemetrix-arduino
- **Otto DIY** (tuong lai): https://www.ottodiy.com/
