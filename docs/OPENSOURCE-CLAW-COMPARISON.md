# Phan Tich So Sanh: OpenClaw vs PicoClaw vs ZeroClaw

> Bao cao R&D — Cap nhat: 2026-03-13

## 1. Tong quan

Ba du an ma nguon mo thuoc "Claw Family" — he sinh thai AI Agent tu host (self-hosted personal AI assistant). Tat ca deu MIT license va chia se triet ly "AI ca nhan, chay tren may cua ban".

| Tieu chi | OpenClaw | PicoClaw | ZeroClaw |
|----------|----------|----------|----------|
| **Website** | openclaw.ai | picoclaw.net | zeroclawlabs.ai |
| **GitHub** | github.com/openclaw/openclaw | github.com/sipeed/picoclaw | github.com/zeroclaw-labs/zeroclaw |
| **GitHub Stars** | ~247,000 | ~8,500 | ~14,900 |
| **Ngon ngu** | TypeScript (Node.js) | Go | Rust |
| **Nguoi tao** | Peter Steinberger | Sipeed / Cong dong | ZeroClaw Labs |
| **Ra mat** | 11/2025 (ten cu: Clawdbot) | 02/2026 | 01/2026 |
| **License** | MIT | MIT | MIT |
| **Triet ly** | Full-featured, nhieu kenh | Ultra-lightweight, embedded | Zero-compromise, production |

## 2. So sanh ky thuat chi tiet

### 2.1 Hieu nang & Tai nguyen

| Chi so | OpenClaw | PicoClaw | ZeroClaw |
|--------|----------|----------|----------|
| **RAM Runtime** | >1 GB | <10 MB | <5 MB |
| **Binary/Install Size** | ~500 MB (node_modules) | ~8 MB (single binary) | ~8.8 MB (single binary) |
| **Thoi gian khoi dong** | Vai giay | <1 giay | <10 ms |
| **Dependencies** | 70+ npm packages | 0 (single binary) | 0 (single binary) |
| **Lines of Code** | ~500,000 | ~15,000 | ~40,000 |
| **Config Files** | 53 | 1 (config.json) | 1 (config.toml) |

### 2.2 Yeu cau he thong (Cai dat)

#### OpenClaw

```
Runtime:        Node.js >= 22
OS:             macOS, Linux, Windows (WSL2)
RAM:            >= 2 GB (khuyen nghi 4 GB+)
Disk:           >= 1 GB
Package Mgr:    npm, pnpm, hoac bun
```

**Cach cai:**
```bash
npm install -g openclaw@latest
openclaw onboard --install-daemon
```

- Wizard tu dong cau hinh Gateway daemon (launchd/macOS, systemd/Linux)
- Can API key tu LLM provider (Claude, OpenAI, DeepSeek, v.v.)

#### PicoClaw

```
Runtime:        Khong can (single binary)
OS:             Linux (RISC-V, ARM64, AMD64), Windows (AMD64)
RAM:            >= 32 MB (runtime chi dung <10 MB)
Disk:           >= 20 MB
Build (tu source): Go >= 1.21, make
```

**Cach cai:**
```bash
# Tai binary san
wget https://github.com/sipeed/picoclaw/releases/latest/download/picoclaw-linux-arm64
chmod +x picoclaw-linux-arm64
mv picoclaw-linux-arm64 /usr/local/bin/picoclaw

# Hoac build tu source
git clone https://github.com/sipeed/picoclaw.git
cd picoclaw
make deps && make build && make install
```

- Cau hinh: `~/.picoclaw/config.json`
- Can API key: OpenRouter hoac Zhipu (LLM), Brave Search (tuy chon)

#### ZeroClaw

```
Runtime:        Khong can (single binary)
OS:             macOS (Intel/Apple Silicon), Linux (x86_64, ARM64, ARMv7), Windows (x86_64)
RAM toi thieu:  64 MB (runtime chi dung <5 MB)
Disk:           >= 50 MB
Build (tu source): Rust toolchain, 4 GB RAM, 6-10 GB disk
```

**Cach cai:**
```bash
# macOS/Linux via Homebrew
brew install zeroclaw

# One-click bootstrap
curl -fsSL https://raw.githubusercontent.com/zeroclaw-labs/zeroclaw/master/install.sh | bash

# Build tu source
git clone https://github.com/zeroclaw-labs/zeroclaw.git
cd zeroclaw
cargo build --release --locked
cargo install --path . --force --locked
```

- Can API key: OpenAI, Anthropic, hoac OpenRouter

### 2.3 Tinh nang

| Tinh nang | OpenClaw | PicoClaw | ZeroClaw |
|-----------|----------|----------|----------|
| **Kenh nhan tin** | 20+ (WhatsApp, Telegram, Slack, Discord, iMessage, Teams, Signal, ...) | Telegram | 70+ tich hop (Telegram, Discord, Slack, ...) |
| **Voice** | Wake-word + continuous voice | Khong | Khong |
| **Live Canvas / UI** | Co (A2UI) | Khong | Khong |
| **Browser Automation** | Co (Chrome/Chromium) | Khong | Co |
| **Memory / Nho** | Co (nhieu backend) | Co (persistent) | Co (SQLite hybrid: vector + full-text) |
| **Cron Jobs** | Co | Khong | Co |
| **Webhooks** | Co | Khong | Co |
| **Plugin/Skill** | Co (platform + workspace) | Co (skill system) | Co (swappable traits) |
| **LLM Providers** | Claude, GPT, DeepSeek, nhieu khac | OpenRouter, Zhipu | OpenAI, Anthropic, OpenRouter, custom |
| **Mobile App** | Co (iOS/Android companion) | Khong | Khong |
| **Tailscale** | Co (Serve/Funnel) | Khong | Khong |
| **Multi-agent** | Co | Gioi han | Co |
| **Migration tu OpenClaw** | — | Khong | Co (built-in tool) |

### 2.4 Bao mat

| Tieu chi | OpenClaw | PicoClaw | ZeroClaw |
|----------|----------|----------|----------|
| **Pairing Code** | Co | Khong | Co |
| **Allowlist** | Co | Khong | Co |
| **Sandbox** | Co | Khong | Co |
| **Rate Limiting** | Co | Khong | Co |
| **Data local** | Co | Co | Co |

## 3. Kien truc so sanh

### OpenClaw
```
[Messaging Channels] --> [Gateway (WebSocket)] --> [RPC Agent Runtime]
                              |                          |
                         [Session Mgr]            [LLM Provider]
                         [Tool Registry]          [Memory Store]
                         [Skill Platform]         [Browser Agent]
```
- Kien truc day du nhat, nhieu layer
- Gateway lam trung tam dieu phoi
- Heavy, nhieu dependency

### PicoClaw
```
[Telegram/CLI] --> [PicoClaw Binary] --> [LLM API]
                        |
                   [Config JSON]
                   [Skill Files]
```
- Kien truc don gian nhat
- Single binary, it lop trung gian
- Thich hop embedded/IoT

### ZeroClaw
```
[Channels (70+)] --> [ZeroClaw Binary] --> [LLM Providers]
                          |
                    [Trait System]
                    [SQLite Memory]
                    [Plugin System]
                    [Sandbox]
```
- Can bang giua don gian va tinh nang
- Moi thanh phan la "swappable trait"
- Tiep can module hoa trong Rust

## 4. So sanh voi NeoClaw

| Tieu chi | OpenClaw / PicoClaw / ZeroClaw | NeoClaw |
|----------|-------------------------------|---------|
| **Muc dich** | AI chatbot ca nhan, da kenh | Giao duc Python + IoT qua claw machine |
| **Phan cung** | Khong (phan mem thuan tuy) | Co (NEO One SBC + MEO ThingBot + motor/sensor) |
| **Doi tuong** | Developer, power user | Hoc sinh, giao vien |
| **AI Role** | Tro ly AI da nang | AI Tutor day Python |
| **IoT** | Gioi han (webhook, API) | MQTT, WebSocket, telemetry, fleet mgmt |
| **Ngon ngu** | TypeScript/Go/Rust | Python |

### 4.1 Co hoi tich hop

NeoClaw co the tan dung cac du an *Claw de:

1. **PicoClaw lam inspiration cho embedded agent**: PicoClaw chay tren hardware gia re tuong tu — co the hoc cach toi uu binary size va memory cho NEO One
2. **OpenClaw Skills Platform**: Mo hinh skill/plugin cua OpenClaw co the ap dung cho he thong bai hoc cua NeoClaw
3. **ZeroClaw Memory System**: SQLite hybrid search (vector + full-text) co the dung cho analytics va student progress tracking
4. **Multi-channel**: Tich hop Telegram/Discord de hoc sinh tuong tac voi claw machine tu xa

### 4.2 Khong nen tich hop

- **Gateway architecture cua OpenClaw**: Qua nang cho embedded education platform
- **Rust/Go rewrite**: Python la ngon ngu giao duc chinh, khong nen doi

## 5. Huong dan chon

| Ban can... | Chon |
|------------|------|
| Day du tinh nang, nhieu kenh, co mobile app | **OpenClaw** |
| Chay tren hardware gia re (<$10), IoT/embedded | **PicoClaw** |
| Production deployment, bao mat cao, hieu nang | **ZeroClaw** |
| Giao duc Python + dieu khien phan cung thuc | **NeoClaw** |

## 6. Trang thai cac du an (03/2026)

| Du an | Version | Trang thai |
|-------|---------|------------|
| OpenClaw | Stable (nhieu release) | Production-ready, cong dong lon nhat |
| PicoClaw | Pre-v1.0 | Early development, chua nen dung production |
| ZeroClaw | Stable | Production-ready, dang tang truong nhanh |
| NeoClaw | v1 | Development, phien ban dau tien |

## 7. Tai lieu tham khao

- OpenClaw Docs: https://openclaw.ai/docs
- PicoClaw GitHub: https://github.com/sipeed/picoclaw
- ZeroClaw Docs: https://www.zeroclawlabs.ai/docs
- Claw Family Guide: https://github.com/CCAgentOrg/claw-family
- So sanh chi tiet: https://sonusahani.com/blogs/openclaw-vs-picoclaw-vs-nullclaw-vs-zeroclaw-vs-nanobot-tinyclaw

---

*Bao cao nay phuc vu muc dich R&D noi bo cua du an NeoClaw. Thong tin co the thay doi theo cac phien ban moi cua tung du an.*
