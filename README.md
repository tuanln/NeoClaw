# NeoClaw — Agentic Robot Education Platform

Learn Python by controlling a real claw machine. Built for NEO One SBC with Raspberry Pi Pico W compatibility.

## Features

- **Hardware Abstraction**: Control DC motors, limit switches, and electromagnets via a clean Python API
- **AI Tutor**: Agentic assistant helps students learn Python through claw machine challenges
- **Education**: 6 progressive lessons from "Hello Claw!" to full grab sequences
- **IoT**: MQTT telemetry, WebSocket real-time control, device fleet management
- **Simulator**: Full software simulation for learning without hardware
- **Analytics**: Track student progress, visualize sensor data, export reports

## Quick Start

```bash
pip install -e ".[all]"

# Run with simulator (no hardware needed)
neoclaw control --simulator

# Start a learning session
neoclaw teach --simulator

# Launch web dashboard
neoclaw monitor --web
```

## Architecture

See [docs/NEOCLAW-ARCHITECTURE.md](docs/NEOCLAW-ARCHITECTURE.md) for full architecture documentation.

## Hardware

See [docs/PICOCLAW-ANALYSIS.md](docs/PICOCLAW-ANALYSIS.md) for original PicoClaw analysis.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
