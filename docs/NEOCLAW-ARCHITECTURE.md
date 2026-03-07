# NeoClaw — Kiến Trúc Hệ Thống

## Tổng quan

NeoClaw là nền tảng giáo dục Python + IoT, sử dụng claw machine (máy gắp) làm thiết bị học tập. Hỗ trợ cả Raspberry Pi Pico W (legacy) và NEO One SBC.

## Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────┐
│                      CLI / Web UI                        │
│  neoclaw control | neoclaw teach | FastAPI Dashboard     │
├──────────────┬──────────────┬───────────────────────────┤
│   Agent      │  Education   │        IoT                │
│  ┌────────┐  │ ┌──────────┐ │ ┌──────────┐ ┌─────────┐ │
│  │ClawAgent│  │ │Curriculum│ │ │   MQTT   │ │WebSocket│ │
│  │LLMClient│  │ │ Progress │ │ │Telemetry │ │ Control │ │
│  │NL Interp│  │ │  Hints   │ │ │ Registry │ │   OTA   │ │
│  └────┬───┘  │ └────┬─────┘ │ └────┬─────┘ └────┬────┘ │
│       │      │      │       │      │             │      │
├───────┴──────┴──────┴───────┴──────┴─────────────┴──────┤
│                    Hardware Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ClawMachine│  │MotorCtrl │  │SensorMgr │  │ Safety  │ │
│  └─────┬────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│        │            │             │              │       │
│  ┌─────┴────────────┴─────────────┴──────────────┴────┐ │
│  │              IGPIOBackend (Protocol)                 │ │
│  ├────────────────────┬───────────────────────────────┤ │
│  │   GpiozeroBackend  │     SimulatorBackend          │ │
│  └────────────────────┘───────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                    EventBus + Config                     │
│              TOML Settings | i18n | Debouncer           │
└─────────────────────────────────────────────────────────┘
```

## Design Patterns

### 1. Protocol-based GPIO Backend
- `IGPIOBackend`: Python Protocol cho GPIO abstraction
- `GpiozeroBackend`: Real hardware via gpiozero
- `SimulatorBackend`: Software simulation cho học không cần hardware

### 2. Command Proxy (từ NEO_CODE)
- Student code import `claw` module → proxy captures calls
- Output `__NEO_CLAW__:{json}` trên stdout
- Sandbox process parse và execute trên hardware thật

### 3. Event-Driven Architecture
- `EventBus`: Pure-Python pub/sub (thay thế PyQt signals)
- Hardware callbacks → EventBus → UI/Agent/IoT
- Loose coupling giữa mọi component

### 4. TOML Configuration
- `defaults.toml`: Default settings
- `~/.neoclaw/config.toml`: User overrides
- Deep merge pattern

### 5. LLM Fallback Chain
- Gemini API (primary) → Ollama (local) → Offline rules
- Lazy initialization, availability caching

### 6. Progressive Hint System
- 4 levels: NUDGE → GUIDANCE → EXPLICIT → SOLUTION
- Tự động escalate khi học sinh gặp khó khăn

## Modules

### hardware/
Core hardware abstraction. Chuyển từ polling (PicoClaw) sang event-driven (gpiozero callbacks).

### agent/
AI assistant giúp học Python qua claw machine. 4 modes: TEACH, FREE_PLAY, VOICE_CONTROL, CHALLENGE.

### education/
6 bài học progressive từ "Hello Claw!" đến "Full Grab Sequence".

### iot/
MQTT telemetry, WebSocket real-time control, device fleet management.

### analytics/
SQLite time-series logging, student progress tracking, data visualization.

### web/
FastAPI dashboard cho monitoring và control từ browser.

### cli/
Click-based CLI: init, control, teach, deploy, monitor.
