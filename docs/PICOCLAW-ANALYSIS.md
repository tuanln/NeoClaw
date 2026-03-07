# PicoClaw — Phân Tích Tổng Quan

## 1. Tổng quan

PicoClaw là dự án DIY claw machine (máy gắp) chạy trên Raspberry Pi Pico W, sử dụng MicroPython. Source code gồm 97 dòng trong file `main.py` duy nhất, điều khiển 3 trục XYZ với nam châm điện (electromagnet) thay vì kẹp cơ học.

**Ngôn ngữ gốc:** Tiếng Pháp (tên biến: gauche=trái, droite=phải, haut=lên, bas=xuống, pince=kẹp/nam châm)

## 2. Kiến trúc phần cứng

### 2.1 Hệ thống trục Cartesian 3 trục

| Trục | Chức năng | Motor | Limit Switch |
|------|-----------|-------|--------------|
| X | Di chuyển ngang (trái/phải) | 2 motor (gauche/droite) | 1 (limitX_gauche) |
| Y | Di chuyển dọc (tiến/lùi) | 2 motor (gauche/droite = tiến/lùi) | 2 (limitY_haut, limitY_bas) |
| Z | Di chuyển lên/xuống (pince) | 2 motor (haut/bas) | 2 (limitZ_haut, limitZ_bas) |

### 2.2 Bộ phận gắp

- **Electromagnet** (pince): GPIO pin 1, ON/OFF đơn giản
- Không có cơ chế PWM, không điều chỉnh lực hút
- Bật khi nhấn nút, tắt khi thả

### 2.3 Tổng hợp thiết bị

| Loại | Số lượng | Chi tiết |
|------|----------|----------|
| DC Motor | 6 | 2 per axis (mỗi hướng 1 motor) |
| Limit Switch | 5 | X:1, Y:2, Z:2 |
| Nút bấm | 7 | 3 cho pince (up/down/catch), 4 cho grue (L/R/U/D) |
| Electromagnet | 1 | Thay thế kẹp cơ học |
| LED | 1 | Onboard LED, indicator hoạt động |

## 3. Pin Mapping

### 3.1 Bảng pin Raspberry Pi Pico W

| GPIO | Chức năng | Loại | Ghi chú |
|------|-----------|------|---------|
| LED | Status LED | OUTPUT | Onboard LED |
| 1 | Electromagnet (pince) | OUTPUT | Bật/tắt nam châm |
| 2 | Motor X trái | OUTPUT | motorX_gauche |
| 3 | Motor X phải | OUTPUT | motorX_droite |
| 4 | Motor Y tiến | OUTPUT | motorY_gauche |
| 5 | Motor Y lùi | OUTPUT | motorY_droite |
| 6 | Motor Z lên | OUTPUT | motorZ_haut |
| 7 | Motor Z xuống | OUTPUT | motorZ_bas |
| 8 | Nút pince lên | INPUT PULL_UP | btn_pince_haut |
| 9 | Nút pince xuống | INPUT PULL_UP | btn_pince_bas |
| 10 | Nút pince bắt | INPUT PULL_UP | btn_pince_catch |
| 11 | Nút grue trái | INPUT PULL_UP | btn_grue_gauche |
| 12 | Nút grue phải | INPUT PULL_UP | btn_grue_droite |
| 13 | Nút grue tiến | INPUT PULL_UP | btn_grue_haut |
| 14 | Nút grue lùi | INPUT PULL_UP | btn_grue_bas |
| 15 | *(không dùng)* | — | — |
| 16 | Limit switch X trái | INPUT PULL_UP | limitX_gauche |
| 17 | Limit switch Y tiến | INPUT PULL_UP | limitY_haut |
| 18 | Limit switch Y lùi | INPUT PULL_UP | limitY_bas |
| 19 | Limit switch Z lên | INPUT PULL_UP | limitZ_haut |
| 20 | Limit switch Z xuống | INPUT PULL_UP | limitZ_bas |

### 3.2 Đặc điểm

- Tất cả input dùng **PULL_UP** → active LOW (nhấn = 0, thả = 1)
- Motor dùng ON/OFF đơn giản, không PWM
- GPIO 15 không sử dụng (gap giữa button và limit switch)

## 4. Luồng điều khiển

### 4.1 Polling Loop

```
┌──────────────────────────────────────┐
│            while True:               │
│                                      │
│  ┌─ Reset led_state = False          │
│  │                                   │
│  ├─ Check X axis (trái/phải)        │
│  │   ├─ btn + limit → motor ON/OFF  │
│  │   └─ Chỉ trái có limit check     │
│  │                                   │
│  ├─ Check Y axis (tiến/lùi)        │
│  │   └─ Cả 2 hướng có limit check   │
│  │                                   │
│  ├─ Check Z axis (lên/xuống)       │
│  │   └─ Cả 2 hướng có limit check   │
│  │                                   │
│  ├─ Check Electromagnet             │
│  │   └─ btn → pince ON/OFF          │
│  │                                   │
│  ├─ Update LED                       │
│  │                                   │
│  └─ Sleep 10ms (100Hz polling)       │
└──────────────────────────────────────┘
```

### 4.2 Logic điều khiển motor

Mỗi motor tuân theo pattern:
```python
if not button.value() and not limit_switch.value():
    motor.on()     # Nhấn nút VÀ chưa chạm limit → chạy
else:
    motor.off()    # Thả nút HOẶC chạm limit → dừng
```

**Ngoại lệ:**
- `motorX_droite` (X phải): **Không có limit switch** → chạy tự do khi nhấn nút
- `pince` (electromagnet): **Không có limit switch** → bật/tắt theo nút

### 4.3 Timing

- **Polling rate:** 100Hz (sleep 10ms)
- **Latency:** tối đa 10ms từ nhấn nút đến motor phản hồi
- Không có debounce phần mềm (phụ thuộc hardware debounce)

## 5. Điểm mạnh

1. **Đơn giản, dễ hiểu:** 97 dòng, logic rõ ràng
2. **Real-time control:** 100Hz polling đủ responsive
3. **Safety cơ bản:** Limit switch ngăn quá tầm
4. **Reliable:** Không có state phức tạp, không crash
5. **Chi phí thấp:** Pico W + motor relay + nút bấm

## 6. Điểm yếu

1. **Không có PWM:** Motor chỉ ON/OFF, không điều chỉnh tốc độ
2. **Thiếu limit switch:** X phải không có limit → nguy cơ cơ khí
3. **Polling thay vì interrupt:** Tốn CPU, khó mở rộng
4. **Không có networking:** Pico W có WiFi nhưng không sử dụng
5. **Monolithic:** Tất cả trong 1 file, không tái sử dụng
6. **Không có state machine:** Không theo dõi vị trí, không có sequence
7. **Không debounce phần mềm:** Phụ thuộc hardware
8. **Không có error handling:** Motor stall, sensor fail → không xử lý

## 7. Cơ hội mở rộng cho NeoClaw

### 7.1 PWM Speed Control
- Thêm PWM cho motor → điều chỉnh tốc độ (0-100%)
- Acceleration/deceleration curve cho chuyển động mượt
- Khác biệt tốc độ cho positioning chính xác

### 7.2 Event-Driven Architecture
- Chuyển từ polling sang interrupt-based (gpiozero callbacks)
- Giảm CPU usage, tăng responsiveness
- EventBus cho loose coupling giữa components

### 7.3 State Machine
- Track vị trí (X, Y, Z) dựa trên limit switch + timing
- Pre-programmed sequences (auto-grab, return-to-home)
- Error recovery (stall detection, retry logic)

### 7.4 Networking (NEO One)
- WiFi/BLE control từ phone/tablet
- MQTT telemetry cho IoT monitoring
- WebSocket real-time control từ browser
- OTA firmware update

### 7.5 AI Integration
- Natural language control: "gắp vật ở góc trái"
- Python education: học lập trình qua điều khiển claw
- Computer vision: camera detect vật thể (future)

### 7.6 Safety Enhancements
- Watchdog timer: auto-stop nếu không có input 30s
- Emergency stop: dừng tất cả motor ngay lập tức
- Current sensing: detect motor stall
- Full limit switch coverage cho mọi hướng

## 8. So sánh Pico W vs NEO One

| Tính năng | Pico W | NEO One |
|-----------|--------|---------|
| CPU | RP2040 dual-core 133MHz | Quad-core ARM |
| RAM | 264KB | 512MB+ |
| Storage | 2MB Flash | 8GB+ eMMC |
| OS | MicroPython (bare metal) | Linux + Python 3.9+ |
| GPIO | 26 pins | 40+ pins |
| WiFi | 2.4GHz | 2.4/5GHz |
| BLE | Yes | Yes |
| USB | Micro-USB | USB-C |
| PWM | Hardware (8 channels) | Software + Hardware |
| Libraries | machine, utime | gpiozero, RPi.GPIO, full Python |
| AI | Không khả thi | Ollama, API calls |
| Web Server | Minimal (microdot) | FastAPI, Flask |

**Kết luận:** NEO One cho phép chạy full Python stack, hỗ trợ AI local, web dashboard, và IoT - biến claw machine thành nền tảng giáo dục hoàn chỉnh.
