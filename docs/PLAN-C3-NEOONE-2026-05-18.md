# Plan: đảm bảo C3 + NEO One chạy tốt — 2026-05-18

> **Goal**: Robot 4 bánh + tay gắp do **NEO One SBC** (Python, NeoClaw) điều khiển qua **USB Serial Telemetrix** xuống **mạch ThingBot ESP32-C3** chạy mượt, có demo end-to-end, có CI bảo vệ regression.

**Phạm vi**: không thêm tính năng mới. Chỉ **làm cho đường ống hiện có chạy tin cậy** + viết lưới an toàn (tests + CI + safety code).

---

## Kiến trúc

```
┌────────────────────────────────┐         ┌──────────────────────────────┐
│   NEO One SBC (Linux/macOS)    │         │   Mạch ThingBot (ESP32-C3)   │
│                                │         │                              │
│   NeoClaw (Python)             │  USB-C  │   thingbot-telemetrix-arduino│
│   ┌──────────────────────┐     │ Serial  │   ┌──────────────────────┐   │
│   │ ClawRobot            │     │ 115200  │   │ Telemetrix4Arduino   │   │
│   │   ├ OmniBase         │ ◄──┼─────────┼──►│   + ThingBot extras  │   │
│   │   └ RobotArm         │     │         │   │   (DC/Servo/Buzzer) │   │
│   │ ↓                    │     │         │   └─────────┬────────────┘   │
│   │ TelemetrixBackend    │     │         │             │                │
│   └──────────────────────┘     │         │   PCA9685 (I2C)             │
└────────────────────────────────┘         │     ├ 4 DC motors           │
                                           │     └ 5 servos              │
                                           └──────────────────────────────┘
```

---

## Hiện trạng (2026-05-18)

| Repo | Trạng thái | Đánh giá |
|---|---|---|
| `tuanln/NeoClaw` (Python brain) | 3 commits, 7 module, 33 tests (đều dùng SimulatorBackend), pyproject + ruff sẵn | 7/10 production, 9/10 simulator. Cấu trúc tốt nhưng chưa CI, chưa test với phần cứng thật. |
| `tuanln/thingbot-telemetrix-arduino` (firmware C3) | PlatformIO, ESP32-C3 USB-CDC native, command table đầy đủ tới `LED_WRITE=10`, dùng Adafruit PWM Servo Driver | Last push **2026-02-08** (3 tháng trước). Lib stub trống `.cpp` (38 byte) — code thực ở `src/main.cpp` (15.6KB). |
| `tuanln/thingvui` (cloud variant) | **PAUSED** từ 2026-05-18 | Code scaffold + PCA9685 driver giữ làm tham chiếu. |

**Pytest baseline**: chưa chạy được — `pytest` không có trong Python 3.14 system env. Bước 0 trong plan dưới giải quyết.

---

## Top 5 risk cần xử lý

| # | Risk | Mức độ | Ảnh hưởng |
|---|---|:---:|---|
| 1 | TelemetrixBackend chưa từng test với mạch thật — chỉ qua SimulatorBackend | 🔴 High | Lỗi serial / baud / timeout chỉ lộ khi flash. Demo có thể fail bất ngờ. |
| 2 | Threading race trong safety watchdog + sensor callback (cùng truy cập `_pin_values`) | 🟠 Med | Hành vi rối khi nhiều input đồng thời (limit switch + lệnh motion). |
| 3 | `thingbot-telemetrix-arduino` lib stub trống — code dồn vào `main.cpp` 15KB | 🟠 Med | Khó maintain, khó share thư viện giữa các project. |
| 4 | Không CI/CD — ruff + pytest phải chạy tay | 🟡 Low | Code drift, PR có thể merge khi tests gãy mà không ai biết. |
| 5 | OmniBase mecanum kinematics + RobotArm IK chưa có unit test logic | 🟡 Low | Bánh có thể quay sai chiều khi tải; tay gắp có thể overshoot. |

---

## Plan 3 milestone

### Milestone A · Foundation (1 ngày) — "chạy được pytest, có CI"

**A0. Python dev env**
- Tạo virtualenv: `python3 -m venv .venv && source .venv/bin/activate`.
- `pip install -e ".[dev]"` (đã có extras trong pyproject).
- Chạy `pytest -q` → ghi baseline số PASS/FAIL/SKIP.

**A1. GitHub Actions workflow `.github/workflows/ci.yml`**
- Triggers: push + pull_request lên `main`.
- Steps: setup-python 3.11+, install dev deps, `ruff check .`, `pytest --cov=src/neoclaw --cov-report=term`.
- Mục tiêu: 33 test PASS trên CI sau commit đầu tiên.

**A2. Pre-commit hook đơn giản**
- File `.pre-commit-config.yaml` chạy ruff + pytest --collect-only (kiểm broken imports).

**Demo criteria A**: PR mới mở → CI tự chạy → green checkmark. Coverage báo cáo trên PR.

---

### Milestone B · Hardware bring-up (2 ngày) — "NEO One nói chuyện được với mạch ThingBot"

**B1. Refresh firmware `thingbot-telemetrix-arduino`**
- Clone về local, kiểm `platformio.ini`, update lib (`Adafruit PWM Servo Driver` mới nhất).
- Build → flash lên 1 mạch ThingBot mẫu, verify USB-CDC enumerate trên macOS (`ls /dev/cu.usbmodem*`).
- Test "are you there" loopback bằng Telemetrix Python client.

**B2. Refactor lib stub**
- Move các function ThingBot-specific (control_dc, control_servo, control_buzzer, control_led) từ `src/main.cpp` vào `lib/ThingBotTelemetrixArduino/ThingBotTelemetrixArduino.{h,cpp}`.
- `main.cpp` giảm còn entry point + serial loop.
- Mục tiêu: lib reusable cho project khác.

**B3. Integration smoke test trong NeoClaw**
- File mới: `tests/test_hardware/test_telemetrix_integration.py` — marked `@pytest.mark.hardware` (skip mặc định, chạy khi `THINGBOT_PORT` env var có).
- Sequence test: connect → digital_write LED → analog_write motor 100ms low duty → servo center → disconnect. Verify không exception.
- Document cách chạy trong `docs/CLAWBOT-SETUP-GUIDE.md`.

**Demo criteria B**: chạy 1 lệnh Python `python -c "from neoclaw.hardware import ThingBot; b=ThingBot.connect(); b.dc(1, 50); b.stop()"` → motor M1 quay 50% 1 giây rồi dừng. Lặp 10 lần, 10/10 thành công.

---

### Milestone C · Reliability & demo (2 ngày) — "robot làm trick được, không hang"

**C1. Thread safety**
- Audit `TelemetrixBackend._pin_values`, `SensorManager._callbacks`, `SafetyWatchdog._state` — thêm `threading.Lock` ở chỗ shared mutable state.
- Test: chạy 100 lệnh đồng thời từ 4 thread, không race.

**C2. Unit test logic OmniBase + RobotArm**
- `tests/test_hardware/test_omni_kinematics.py` — verify ma trận mecanum (vx/vy/omega → fl/fr/rl/rr) với 6 case kinh điển.
- `tests/test_hardware/test_robot_arm.py` — verify `JOINT_LIMITS` clamp, `ARM_POSES` lookup, smooth motion step count.

**C3. End-to-end demo script**
- `examples/demo_pick_drop.py`: kết nối → home arm → forward 1s → pick_up → strafe_left 1s → put_down → home. 
- Chạy với simulator first, sau đó hardware. Cùng script, switch backend qua env var.

**C4. README quick-start update**
- Thêm section "5-phút bắt đầu với ThingBot thật" — flash firmware, connect USB, chạy demo script.

**Demo criteria C**: chạy `python examples/demo_pick_drop.py` → robot diễn đủ chuỗi 6 bước → no error. Repeat 5 lần.

---

## Câu hỏi mở (cần user trả lời)

1. **Có sẵn mạch ThingBot vật lý + NEO One SBC ngay không?** Quyết định B + C có cần block chờ phần cứng không.
2. **NEO One SBC OS**: Linux Yocto? Raspbian? hay PC Linux/macOS cũng OK cho MVP?
3. **Demo trên Làng Maker khi nào?** Có deadline → ưu tiên milestone B trước A.
4. **Có cần giữ tương thích PicoClaw backend (raspberry pi pico) không?** Hiện code có cả Pico — nếu drop được thì giảm bề mặt test.

---

## Kế hoạch dự phòng nếu không có phần cứng

- A milestones chạy được hoàn toàn không cần hardware.
- B1 + B2 vẫn refactor được (build firmware, không flash).
- B3 viết test nhưng đánh dấu skip — khi có hardware mới enable.
- C1 + C2 + C3 phần simulator chạy được.
- C3 phần hardware demo chờ.

---

**Last updated**: 2026-05-18 · Người viết: Claude (controller agent) · Sẽ commit vào NeoClaw repo.
