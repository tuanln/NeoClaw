"""Application settings management using TOML configuration."""
from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_DEFAULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "defaults.toml"
_USER_CONFIG_DIR = Path.home() / ".neoclaw"
_USER_CONFIG_PATH = _USER_CONFIG_DIR / "config.toml"


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@dataclass
class SafetySettings:
    enable_watchdog: bool = True
    emergency_stop_pin: int = -1
    max_motor_runtime: int = 60
    limit_switch_debounce_ms: int = 5


@dataclass
class HardwareSettings:
    board: str = "meo_thingbot"      # "meo_thingbot" (v1), "neo_one", "pico_w"
    enable_gpio: bool = False
    gpio_library: str = "telemetrix" # "telemetrix" (NEO One -> ThingBot) or "gpiozero"
    pwm_frequency: int = 1000
    watchdog_timeout: int = 30
    com_port: str = ""               # Serial port for Telemetrix (empty = auto-detect)
    arduino_instance_id: int = 1     # Telemetrix board instance ID


@dataclass
class ExecutionSettings:
    timeout_seconds: int = 30
    max_memory_mb: int = 256
    max_claw_commands: int = 5000


@dataclass
class AIContextSettings:
    max_history_turns: int = 6
    max_code_lines: int = 200


@dataclass
class AISettings:
    provider: str = "gemini"
    model: str = "gemini-2.5-flash"
    fallback_model: str = "gemini-2.0-flash"
    api_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    api_key: str = ""
    ollama_host: str = "http://localhost:11434"
    max_response_tokens: int = 512
    temperature: float = 0.3
    hint_level: str = "guidance"
    context: AIContextSettings = field(default_factory=AIContextSettings)


@dataclass
class EducationSettings:
    default_phase: int = 1


@dataclass
class IoTSettings:
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic_prefix: str = "neoclaw"
    ws_host: str = "0.0.0.0"
    ws_port: int = 8765
    telemetry_interval: int = 5


@dataclass
class AnalyticsSettings:
    database_path: str = "~/.neoclaw/neoclaw.db"
    export_path: str = "~/.neoclaw/exports"


@dataclass
class WebSettings:
    host: str = "0.0.0.0"
    port: int = 8080


@dataclass
class AppSettings:
    """Root settings container."""
    name: str = "NeoClaw"
    version: str = "0.1.0"
    language: str = "vi"
    hardware: HardwareSettings = field(default_factory=HardwareSettings)
    safety: SafetySettings = field(default_factory=SafetySettings)
    execution: ExecutionSettings = field(default_factory=ExecutionSettings)
    ai: AISettings = field(default_factory=AISettings)
    education: EducationSettings = field(default_factory=EducationSettings)
    iot: IoTSettings = field(default_factory=IoTSettings)
    analytics: AnalyticsSettings = field(default_factory=AnalyticsSettings)
    web: WebSettings = field(default_factory=WebSettings)


def _apply_dict_to_dataclass(obj: Any, data: dict) -> None:
    """Apply dict values to a dataclass instance."""
    for key, value in data.items():
        if hasattr(obj, key):
            attr = getattr(obj, key)
            if isinstance(value, dict) and hasattr(attr, "__dataclass_fields__"):
                _apply_dict_to_dataclass(attr, value)
            else:
                setattr(obj, key, value)


def load_settings() -> AppSettings:
    """Load settings from defaults.toml, merged with user config if exists."""
    if tomllib is None:
        return AppSettings()

    settings = AppSettings()

    if _DEFAULTS_PATH.exists():
        with open(_DEFAULTS_PATH, "rb") as f:
            defaults = tomllib.load(f)
    else:
        defaults = {}

    config = defaults
    if _USER_CONFIG_PATH.exists():
        with open(_USER_CONFIG_PATH, "rb") as f:
            user_config = tomllib.load(f)
        config = _deep_merge(defaults, user_config)

    app_config = config.get("application", {})
    settings.name = app_config.get("name", settings.name)
    settings.version = app_config.get("version", settings.version)
    settings.language = app_config.get("language", settings.language)

    for section_name in [
        "hardware", "safety", "execution", "ai", "education", "iot", "analytics", "web",
    ]:
        if section_name in config:
            _apply_dict_to_dataclass(getattr(settings, section_name), config[section_name])

    return settings


_settings: AppSettings | None = None


def get_settings() -> AppSettings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reset_settings() -> None:
    """Reset settings to force reload."""
    global _settings
    _settings = None
