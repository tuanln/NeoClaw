"""Bilingual Vietnamese/English internationalization."""
from __future__ import annotations

from neoclaw.config.settings import get_settings

_MESSAGES: dict[str, dict[str, str]] = {
    # General
    "welcome": {
        "vi": "Chào mừng đến với NeoClaw!",
        "en": "Welcome to NeoClaw!",
    },
    "goodbye": {
        "vi": "Tạm biệt!",
        "en": "Goodbye!",
    },
    "error": {
        "vi": "Lỗi",
        "en": "Error",
    },

    # Hardware
    "motor_started": {
        "vi": "Motor đã bật",
        "en": "Motor started",
    },
    "motor_stopped": {
        "vi": "Motor đã tắt",
        "en": "Motor stopped",
    },
    "magnet_on": {
        "vi": "Nam châm BẬT — đang gắp",
        "en": "Magnet ON — grabbing",
    },
    "magnet_off": {
        "vi": "Nam châm TẮT — đã thả",
        "en": "Magnet OFF — released",
    },
    "limit_triggered": {
        "vi": "Công tắc giới hạn đã kích hoạt",
        "en": "Limit switch triggered",
    },
    "emergency_stop": {
        "vi": "DỪNG KHẨN CẤP!",
        "en": "EMERGENCY STOP!",
    },
    "watchdog_timeout": {
        "vi": "Hết thời gian chờ — motor tự động tắt",
        "en": "Watchdog timeout — motors auto-stopped",
    },

    # Education
    "lesson_start": {
        "vi": "Bắt đầu bài học",
        "en": "Starting lesson",
    },
    "exercise_passed": {
        "vi": "Tuyệt vời! Bài tập đã hoàn thành!",
        "en": "Excellent! Exercise completed!",
    },
    "exercise_failed": {
        "vi": "Chưa đúng, hãy thử lại!",
        "en": "Not quite right, try again!",
    },
    "hint_available": {
        "vi": "Gợi ý có sẵn. Gõ 'hint' để xem.",
        "en": "Hint available. Type 'hint' to see it.",
    },

    # IoT
    "device_connected": {
        "vi": "Thiết bị đã kết nối",
        "en": "Device connected",
    },
    "device_disconnected": {
        "vi": "Thiết bị đã ngắt kết nối",
        "en": "Device disconnected",
    },
}


def t(key: str, lang: str | None = None) -> str:
    """Translate a message key.

    Args:
        key: Message key
        lang: Language code ("vi" or "en"). Auto-detects from settings if None.
    """
    if lang is None:
        lang = get_settings().language

    messages = _MESSAGES.get(key)
    if messages is None:
        return key

    return messages.get(lang, messages.get("en", key))
