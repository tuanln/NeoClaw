# Progress Log

> Running log of what's been done, in reverse chronological order. Each session
> adds an entry on top. Next time you (or Claude) start work, **read the top
> entry first** to know the current state and where to pick up.

---

## 2026-08-30 — Sửa PROTOCOL-BUG đảo chiều động cơ + NeoClaw vào canon ThingEdu

### Bối cảnh

Rà lại dự án phát hiện lỗi giao thức đã ghi nhận ngày 21/05 ("track riêng, không thuộc scope
refactor") thực ra là **lỗi chặn đường**: mọi thao tác omni cần bánh quay ngược — `backward`,
`strafe_left/right`, `rotate_cw/ccw`, toàn bộ `diagonal_*` — đều không chạy được trên mạch thật.
Nghĩa là demo criteria Milestone B (`demo_pick_drop.py` có bước `strafe_left`) không thể pass
trước khi sửa. Phiên này sửa dứt điểm cả hai đầu dây, và xử lý luôn việc NeoClaw không có mặt
trong canon ThingEdu.

### Đã làm

**1 · Giao thức speed có dấu (TDD, 3 repo)**

- Chẩn đoán: firmware đọc `speed` là `uint8_t` rồi kiểm tra `if (speed >= 0)` — luôn đúng, nhánh
  đảo chiều là mã chết. Firmware **tự nó không bao giờ lùi được**, bất kể client gửi gì.
- **Đính chính (kiểm chứng cuối phiên, sau khi tải được thư viện pip)**: triệu chứng ở phía host
  không phải "chạy tới thay vì lùi". `thingbot_telemetrix` đóng gói bằng `bytes(command)`, mà
  `bytes()` **ném `ValueError` với số âm** — nên lệnh lùi không bao giờ rời khỏi máy tính. Hai lỗi
  độc lập, cả hai đều thật, và cùng được đóng bởi hợp đồng byte có dấu:
  host trước đây không gửi đi được, firmware nhận được cũng không giải mã được.
  Kịch bản "chạy tới ~96% với duty không xác định" chỉ xảy ra với client nào tự mask byte
  (`map()` của Arduino không kẹp dải nên 196 → 8026, vượt thanh ghi 12-bit) — nay đã kẹp trong
  `speedToDuty`.
- Chốt wire format: `speed_byte` là **bù hai của số có dấu -100..100**. Giá trị 0..100 mã hóa ra
  chính nó → mạch chạy firmware cũ giữ nguyên hành vi tiến.
- `NeoClaw`: thêm `encode_speed_byte()` trong `telemetrix_backend.py`, `control_dc` gọi qua hàm
  này. 22 test mới (`tests/test_hardware/test_dc_protocol.py`) — RED trước, GREEN sau, gồm round
  trip qua phép cast `int8_t` và bất biến "byte lạ không bao giờ ra duty ngoài dải".
- `thingbot-telemetrix-arduino`: tách phần toán thuần ra `lib/ThingBotTelemetrixArduino/ThingBotMotorMath.h`
  (namespace `tbmath`, không phụ thuộc `<Arduino.h>` nên test được trên máy) — `decodeSpeedByte`,
  `speedToDuty` (có clamp), `motorDuty`. `controlDc` đổi sang `int8_t` và dùng `motorDuty`;
  `main.cpp` decode byte trước khi dispatch. `mapSpeedToPwm` nay clamp qua `speedToDuty`.
- Host test không cần toolchain Arduino: `host-tests/` + Makefile, `make -C host-tests` → 7 PASS.
- Nghiệm thu phần cứng: `tests/test_hardware/test_telemetrix_integration.py` (marker `hardware`,
  gate bằng `THINGBOT_PORT`, mặc định deselect) + `examples/verify_reverse.py` — kịch bản 10 vòng
  tiến/lùi cho người vận hành quan sát, đúng demo criteria B.

**2 · Đưa NeoClaw vào canon ThingEdu** (`thingedu-canon`)

- `PRODUCT_CATALOG.md`: thêm mục **2.1 Ngoài Bảng 2 — nền tảng robot** (NeoClaw/ClawBot, firmware
  ThingBot, ThingVui paused); dòng NEO Sport (C.4) nay ghi rõ robot thi đấu chưa chốt nguồn.
- `DECISIONS.md`: thêm điểm treo **P-10** — NeoClaw không có WS/PIC trong Bảng 2 và chồng lấn
  C.4 NEO Sport; 3 phương án, người chốt anh Tuấn + Hùng. Không tự quyết.
- `GLOSSARY.md`: thêm tên chuẩn **NeoClaw** và **ClawBot**.

### Metrics

| | Đầu phiên | Cuối phiên |
|---|:---:|:---:|
| pytest (NeoClaw) | 70 | **92** (+22), 9 deselected (hardware) |
| Host test firmware | 0 | **7 PASS** (`make -C host-tests`) |
| Ruff | 0 lỗi | 0 lỗi |
| PlatformIO build | SUCCESS | SUCCESS — RAM 5.1% / Flash 21.2% (không đổi) |
| Đảo chiều động cơ | mã chết | chạy được, chờ nghiệm thu mạch thật |

### 🔴 Phát hiện cuối phiên — chặn đường lớn hơn lỗi vừa sửa

Tải được `thingbot-telemetrix` 2.2 từ PyPI (thư viện mà README + setup guide bảo người dùng cài)
và đọc mã. Hai điều:

1. **Mã lệnh không khớp nhau.** Thư viện gửi `DC_WRITE = 101`, `SERVO_WRITE = 102`,
   `BUZZER_WRITE = 103`, `LED_WRITE = 104` (`private_constants.py`). Firmware `tuanln/thingbot-telemetrix-arduino`
   — bản mà tài liệu NeoClaw trỏ tới, và là bản vừa sửa — dùng **7 / 8 / 9 / 10** (`main.cpp`).
   Nghĩa là **NeoClaw + thư viện pip + firmware này chưa từng chạy được với nhau**, chưa nói tới
   chuyện lùi.
2. **Không kiểm biên chỉ số lệnh.** `main.cpp:137` làm `command_entry = command_table[command];`
   trên bảng 11 phần tử, không chặn `command` (lấy từ gói tin, 0-255). Gửi lệnh 101 vào firmware
   này là đọc con trỏ hàm rác rồi nhảy vào đó — treo hoặc reset, không phải "lệnh bị bỏ qua".

Đối chiếu thêm: fork **`MEO-3/thingbot-telemetrix-arduino`** (push gần nhất 12/08/2026, có bản
BLE + release 3.0, khớp mã lệnh 101-104 của thư viện pip) mang **đúng lỗi `byte speed` +
`if (speed >= 0)`** ở `ThingBotExtended.cpp` — tức bản firmware nhiều khả năng đang nằm trên kit
thật vẫn chưa được sửa.

### ✅ Đã chốt bằng bằng chứng: đối chiếu `ThingEdu/neo-code`

Đọc `ThingEdu/neo-code` (IDE Python trên NEO One, push gần nhất 23/07/2026) — đây là nơi giữ lớp
giao tiếp thiết bị mới nhất của hệ:

- `features/arm/backends.py` dùng **`thingbot-telemetrix`**, gọi `board.thingbot().control_servo()`
  — đúng API mà NeoClaw đang dùng.
- `pyproject.toml`: `thingbot-telemetrix>=2.2`; `scripts/build_deb.sh` ghim `TELEMETRIX_VERSION=2.2`
  và vendor sẵn vào `.deb` (apt không có gói tương ứng).
- `_vendor/README.md` ghi rõ upstream: **`github.com/MEO-3/thingbot-telemetrix`**, giấy phép
  **AGPL-3.0-or-later** — `neo-code` (MIT) khai cả hai trong `debian/copyright`.

Vậy **chuẩn hiện hành của hệ = thư viện `thingbot-telemetrix` 2.2 + firmware MEO-3** (mã lệnh
101-104). Không còn là câu hỏi mở. Đã cập nhật NeoClaw theo chuẩn đó:

- `pyproject.toml`: thêm `thingbot-telemetrix>=2.2` vào extra `hardware`, kèm ghi chú giấy phép.
- Sửa khối comment mã lệnh trong `telemetrix_backend.py` (đang ghi 7/8/9/10 — sai từ đầu; mã lệnh
  do thư viện quyết định, không do file này).
- README + setup guide: firmware bản chính là `MEO-3/thingbot-telemetrix-arduino`, giải thích vì
  sao fork `tuanln` không dùng được với thư viện, thêm mục giấy phép AGPL, link sang `neo-code`.

**Ghi chú kiến trúc đáng học từ neo-code**: mã học sinh chạy trong QProcess riêng và **không giữ
cổng serial** — mọi lệnh robot ghi ra stdout dạng dòng có tiền tố `\x1e@@ARM ` kèm JSON, tiến trình
chính đọc rồi mới chạm phần cứng (`features/arm/protocol.py`). NeoClaw đang cho sandbox học sinh
sinh lệnh theo kiểu tương tự nhưng chưa tách quyền giữ cổng — đáng cân nhắc khi nối `ClawRobot` vào
sandbox.

### 🔻 Việc còn treo sau khi chốt

- **Firmware MEO-3 vẫn mang lỗi byte speed chưa sửa** (`ThingBotExtended.cpp`, `byte speed` +
  `if (speed >= 0)`). Bản vá đã có ở fork `tuanln` nhưng **chưa port sang MEO-3**, và tôi không có
  quyền push lên org MEO-3 (`push=false`). Nghĩa là lùi/đi ngang **vẫn chưa chạy được trên board
  thật** dù phía Python đã đúng. Cần anh Tuấn mở đường: hoặc cấp quyền, hoặc fork + PR chéo, hoặc
  chuyển yêu cầu cho đội giữ MEO-3.
- Thư viện `thingbot-telemetrix` cũng nên nhận cùng bản vá (`bytes()` ném `ValueError` với số âm) —
  NeoClaw đã tự mã hoá trước khi gọi nên không chặn, nhưng client khác thì vẫn vướng.
- Fork `tuanln` (mã lệnh 7-10, thiếu kiểm biên chỉ số lệnh ở `main.cpp:137`) nay là **bản tham
  chiếu**, không phải bản chạy. MEO-3 dùng `lookup_command` quét bảng id→hàm, trả `nullptr` nếu
  lệnh lạ — không có lỗi nhảy con trỏ rác.
- Giấy phép: NeoClaw MIT phụ thuộc thư viện AGPL-3.0-or-later. Cùng họ vấn đề với P-09 (ThingBlock).

### Còn lại

- **Nghiệm thu 10/10 trên mạch thật** — vẫn cần phần cứng: 1 ThingBot ESP32-C3, cáp USB-C, nguồn
  LiPo 7,4V cho motor rail, giá kê xe. Nạp firmware (`pio run -t upload`) rồi chạy
  `THINGBOT_PORT=... python examples/verify_reverse.py`.
- ~~Kiểm tra thư viện pip `thingbot-telemetrix`~~ — đã đọc mã (v2.2): không kẹp giá trị, nhưng
  đóng gói bằng `bytes(command)` nên **số âm ném `ValueError`**; và mã lệnh lệch hẳn với firmware
  này (xem mục phát hiện ở trên).

### Lưu ý kỹ thuật phát hiện trong phiên

- **Xung đột tên**: `main.cpp` có biến toàn cục `thingbot`, nên namespace toán phải đặt tên khác
  (`tbmath`) — C++ không cho namespace và biến trùng tên ở cùng phạm vi.
- **`buzzer()` lệch dải**: `thingbot.py` cho phép 0..255 nhưng firmware map theo thang 0..100.
  Trước đây freq > 100 tràn thanh ghi 12-bit; nay bị clamp ở mức đầy. Nên siết dải phía Python
  xuống 0..100 — chưa làm, ngoài phạm vi phiên này.
- `site/` của canon đang **chậm hơn** tài liệu: chưa có P-09, và nay chưa có P-10 (đã bổ sung
  trong cùng phiên; bản Artifact đã publish thì chưa cập nhật lại).
- **CI đỏ vì lệch phiên bản ruff, không phải vì code**: `pyproject.toml` ghi `ruff>=0.4` nên CI kéo
  bản mới nhất — 0.16.5 — trong khi máy dev chạy 0.15.x. Ruff 0.16 mở rộng bộ rule mặc định, ra 78
  lỗi trên mã cũ (`UP045` 30, `BLE001` 18, `I001` 9, `S110` 6…); các file mới của phiên này sạch
  dưới cả hai bản. Đã ghim `ruff>=0.15,<0.16` để CI xác định được. **Việc tồn**: một đợt dọn riêng
  để lên 0.16 — phần lớn là sửa máy móc (`Optional[X]` → `X | None`, sắp xếp import), nhưng
  `BLE001` (bắt Exception trần) và `S110` (try/except/pass) thì phải đọc từng chỗ.

---

## 2026-05-21 — Milestone A + B (build) + C complete, pivot from ThingVui locked in

### Bối cảnh

Phiên này pivot từ "ThingVui standalone trên ESP32-C3" (xiaozhi cloud + voice trực tiếp trên MCU) sang **kiến trúc chính C3 (ThingBot Telemetrix) + NEO One (Python brain + py-xiaozhi)**. Quyết định 2026-05-18: ESP32-C3 không đủ sức gánh Xiaozhi + motion cùng lúc; NEO One có sẵn Linux + py-xiaozhi chạy được — bộ não đặt ở đây thay vì firmware.

Plan 5 ngày → A/B/C milestones ở [`PLAN-C3-NEOONE-2026-05-18.md`](PLAN-C3-NEOONE-2026-05-18.md). Brief sản phẩm v2.1 ở [`PRODUCT-BRIEF-NEOONE.md`](PRODUCT-BRIEF-NEOONE.md). Bản voice-cloud standalone (`tuanln/thingvui`) **PAUSED**.

### Đã làm

**Milestone A · Foundation (NeoClaw repo)**
- venv-first dev workflow + `pip install -e ".[dev]"`.
- Ruff baseline cleanup: **44 errors → 0** (33 auto-fixed unused imports + manual: rename biến `l`, remove unused `result=`, TODO comment cho `pin_mode` dead-assignment, per-file-ignores E402 cho `cli/main.py`).
- GitHub Actions CI: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) — matrix Python 3.11+3.12, cache pip, run ruff + pytest with coverage. Upload coverage-xml artifact.
- Pre-commit hook: [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) — ruff + trailing-whitespace/end-of-file-fixer/check-yaml/check-toml + local pytest --collect-only.
- Fix: thêm `pytest-cov` vào dev deps (CI fail 26194798126 → green 26195555163).

**Milestone B1 · Firmware build verify (thingbot-telemetrix-arduino repo)**
- PlatformIO build SUCCESS trong 64.73s. RAM 5.1% (16632 B / 327680). Flash 21.2% (277330 B / 1310720). Toolchain + lib deps đều OK.

**Milestone B2 · Lib refactor (thingbot-telemetrix-arduino repo)**
- `src/main.cpp`: **575 → 395 dòng** (-31%). Chỉ còn Telemetrix protocol + GPIO + DHT + 4 wrapper mỏng.
- `lib/ThingBotTelemetrixArduino/`: stub trống (8B `.h` + 0B `.cpp`) → **208 dòng** lib hoàn chỉnh với API class:
  - `controlDc(motor, speed)`, `controlServo(servo, angle)`, `controlBuzzer(frequency)`, `controlLed(led, state)`
  - `begin()`, `setupSwInput()`, `mapSpeedToPwm()`, `mapAngleToPwm()`
  - Public constants `M1-M4`, `S1-S5`, `SW_PIN`
- Verify: PIO build PASS sau refactor — không regression.
- **PROTOCOL-BUG preserved** (documented inline): `byte speed; if (speed >= 0)` luôn true → branch negative unreachable. Fix riêng khi đổi protocol Python+Arduino sang `int8_t`.

**Milestone C1 · Thread safety (NeoClaw repo)**
- `sensor_manager.py`: `_callbacks` list giờ có `threading.Lock`, dispatch dùng snapshot pattern (gọi callback ngoài lock — không deadlock nếu callback gọi lại `on_change`).
- `telemetrix_backend.py`: gộp + đổi tên `_pin_lock` → `_state_lock`, cover thêm `_callbacks`, `_output_pins`, `_input_pins`, `_pwm_pins`. Compound writes (`setup_output`, `setup_input`, `pwm_start/stop`, `set_callback`, `cleanup`) đều có lock. User callback fire ngoài lock.
- 3 test mới ở [`tests/test_hardware/test_thread_safety.py`](../tests/test_hardware/test_thread_safety.py):
  - 100 callback register từ 4 threads + concurrent event firer → no race
  - Callback gọi lại `on_change` → không deadlock
  - Smoke test attribute rename `_pin_lock` → `_state_lock`

**Milestone C2 · Unit tests kinematics + arm (NeoClaw repo)**
- [`tests/test_hardware/test_omni_kinematics.py`](../tests/test_hardware/test_omni_kinematics.py) — **12 test**: 6 mecanum pattern kinh điển (forward/backward/strafe L+R/rotate CW+CCW), 2 diagonal, stop, state, 2 vector drive (pure forward + clamp).
- [`tests/test_hardware/test_robot_arm.py`](../tests/test_hardware/test_robot_arm.py) — **22 test**: 12 parametrize cho `JOINT_LIMITS` clamp, `ARM_POSES` bảng 5 preset, home/carry/unknown pose, grip/release state, 3 smooth motion case (ascending/descending/noop), `move_to`.
- `StubThingBot` ghi nhận `dc()`/`servo()` calls — test không cần hardware.

**Milestone C3 · End-to-end demo (NeoClaw repo)**
- [`examples/demo_pick_drop.py`](../examples/demo_pick_drop.py) — 6 bước canonical: home arm → forward 1s → pick_up → strafe_left 1s → put_down → home.
- Mode switch qua env var: default `SimulatorBackend`; bật real hardware bằng `NEOCLAW_USE_HARDWARE=1`.
- Simulator chạy: full chuỗi, in từng step, finish với `✓ Demo completed successfully.`

**Milestone C4 · README quick-start update (NeoClaw repo)**
- 3 badge: CI status, Python 3.11+, MIT License.
- 2 đường quick-start tách rõ: 5-phút simulator (venv → install → demo) + 5-phút hardware (firmware upload → USB → smoke test).
- Bảng tài liệu thêm `PRODUCT-BRIEF-NEOONE.md` + `PLAN-C3-NEOONE-2026-05-18.md`.
- Phát triển section: venv workflow, ruff commands, pre-commit install, link CI workflow + thread-safety test file.

### Metrics

| | Đầu phiên | Cuối phiên |
|---|:---:|:---:|
| pytest tests | 33 | **70** (+37) |
| Pass rate | 33/33 | 70/70 in ~1.2s |
| Ruff errors | 44 | 0 |
| CI status | — | ✅ green |
| Coverage tổng | — | 31% |
| `main.cpp` dòng (firmware) | 575 | 395 (-31%) |
| Lib stub | 8B `.h` + 0B `.cpp` | 208 dòng lib hoàn chỉnh |
| Public docs | brief v2.0 | brief v2.1 + plan + handoff |

### Commit Hashes

| Repo | HEAD | Commit message |
|---|---|---|
| `tuanln/NeoClaw` | `3c1acf9` | `fix(ci): add pytest-cov to [dev] deps` |
| `tuanln/thingbot-telemetrix-arduino` | `e162774` | `refactor: extract ThingBot-specific code to lib stub (Milestone B2)` |
| `tuanln/thingvui` (paused) | `1138ae5` | `docs: PAUSE ThingVui standalone, pivot C3 + NEO One` |

### Còn lại trong plan 5 ngày

**B1 hardware flash + B3 integration smoke test** — đều cần phần cứng vật lý:
- 1 mạch ThingBot ESP32-C3 + USB-C cáp
- Loa + mic USB (cho audio sau)
- Pin 7.4V LiPo cho motor rail
- NEO One SBC (hoặc tạm dùng macOS/Linux PC)

Bước cụ thể:
1. Clone `thingbot-telemetrix-arduino`, cắm USB, `pio run --target upload` (~1 phút).
2. macOS: `ls /dev/cu.usbmodem*` để biết port. Linux: `ls /dev/ttyUSB*`.
3. `cd NeoClaw && source .venv/bin/activate`.
4. `pip install thingbot-telemetrix`.
5. `NEOCLAW_USE_HARDWARE=1 python examples/demo_pick_drop.py` → verify motor M1 quay 60% 1s, tay home, gắp, strafe trái, thả, home.
6. Lặp 10 lần — 10/10 phải PASS (demo criteria B).

Khi xong, viết integration test ở `tests/test_hardware/test_telemetrix_integration.py` với `@pytest.mark.hardware` marker, gated bằng `THINGBOT_PORT` env var. Tests này skip mặc định, chỉ chạy khi user export env.

### Open questions cần user trả lời

(Trùng với plan §10 + brief §10, ưu tiên cao:)

1. **Có sẵn mạch ThingBot + NEO One ngay không?** Quyết định lịch B1/B3.
2. **NEO One SBC OS gì?** Linux Yocto / Raspbian / PC Linux+macOS đều OK cho MVP — cần biết cụ thể.
3. **Demo Làng Maker deadline khi nào?** Có deadline → ưu tiên B trước phần lý thuyết.
4. **PicoClaw backend có cần giữ không?** Hiện code có cả Pico — nếu drop được thì giảm bề mặt test.

### Lưu ý kỹ thuật phát hiện trong phiên

- **PROTOCOL-BUG ở firmware**: `controlDc` đọc `speed` như `byte` (unsigned), `if (speed >= 0)` luôn true → reverse direction unreachable. Track riêng — không phải refactor scope. Fix yêu cầu đồng bộ Python + Arduino đổi sang `int8_t` cho speed byte.
- **`telemetrix_backend.setup_input`**: `pin_mode` được compute nhưng không dùng. Cả `INPUT_PULLUP` lẫn `INPUT` branch đều gọi cùng method `set_pin_mode_digital_input`. TODO trong code; track ở Milestone B follow-up.
- **GitHub Actions deprecation warning**: `actions/checkout@v4`, `setup-python@v5`, `upload-artifact@v4` dùng Node 20 — deprecated tháng 6/2026. Bump version trước deadline.
- **Token gh OAuth scopes**: cần `workflow` scope để push file trong `.github/workflows/`. User-facing: `gh auth refresh -h github.com -s workflow` (interactive, browser confirm).

### Files quan trọng nhất (cho phiên sau)

| File | Mục đích |
|---|---|
| `docs/PRODUCT-BRIEF-NEOONE.md` | Brief sản phẩm v2.1 — source of truth |
| `docs/PLAN-C3-NEOONE-2026-05-18.md` | Plan 5 ngày, 3 milestone, demo criteria |
| `docs/PROGRESS.md` | (file này) running log |
| `examples/demo_pick_drop.py` | Smoke test E2E |
| `tests/test_hardware/test_thread_safety.py` | Lock pattern reference |
| `tests/test_hardware/test_omni_kinematics.py` | Mecanum math invariants |
| `tests/test_hardware/test_robot_arm.py` | Joint limits + poses invariants |
| `.github/workflows/ci.yml` | CI workflow |
| `pyproject.toml` | Deps + ruff config |

---

## Cách dùng file này

**Khi bắt đầu phiên mới:**
1. Đọc entry trên cùng (gần nhất) để biết bối cảnh.
2. Kiểm tra commit hash thực tế bằng `git log -1` ở mỗi repo.
3. Đối chiếu với plan ở `PLAN-C3-NEOONE-*.md` — milestone nào đang dở.
4. Trả lời open questions (nếu có) hoặc đi tiếp.

**Khi kết thúc phiên:**
1. Tạo entry mới trên đầu file này (ngày + tóm tắt + commit hash + open questions).
2. Update brief / plan nếu có thay đổi chiến lược.
3. Commit log này cùng với code changes.

**Format entry**: `## YYYY-MM-DD — <Title ngắn>`, sau đó các section: Bối cảnh, Đã làm, Metrics, Commit Hashes, Còn lại, Open questions, Files quan trọng.
