"""Internationalization module — language switching with persistence.

Supports: English (en), Chinese (zh).
Config persisted to %APPDATA%/ssaHdrify/config.json (Windows)
or ~/.config/ssaHdrify/config.json (macOS/Linux).
"""

from __future__ import annotations

import json
import locale
import os
import platform

_STRINGS: dict[str, dict[str, str]] = {
    "window_title": {
        "en": "Convert subtitle from SDR to HDR colorspace",
        "zh": "SDR \u5b57\u5e55\u8f6c HDR \u8272\u5f69\u7a7a\u95f4",
    },
    "options": {"en": "Options", "zh": "\u9009\u9879"},
    "message": {"en": "Message", "zh": "\u6d88\u606f"},
    "eotf_label": {"en": "Content EOTF curve:", "zh": "\u5185\u5bb9 EOTF \u66f2\u7ebf\uff1a"},
    "brightness_label": {
        "en": "Target subtitle brightness (nits):",
        "zh": "\u76ee\u6807\u5b57\u5e55\u4eae\u5ea6\uff08\u5c3c\u7279\uff09\uff1a",
    },
    "select_convert": {"en": "Select file and convert", "zh": "\u9009\u62e9\u6587\u4ef6\u5e76\u8f6c\u6362"},
    "invalid_brightness": {"en": "Invalid brightness", "zh": "\u4eae\u5ea6\u503c\u65e0\u6548"},
    "brightness_error_msg": {
        "en": "Please enter a target brightness value (1\u201310000 nits).",
        "zh": "\u8bf7\u8f93\u5165\u76ee\u6807\u4eae\u5ea6\u503c\uff081\u201310000 \u5c3c\u7279\uff09\u3002",
    },
    "converting": {"en": "Converting file: {0}", "zh": "\u6b63\u5728\u8f6c\u6362\uff1a{0}"},
    "cancelled": {"en": "Conversion cancelled.", "zh": "\u8f6c\u6362\u5df2\u53d6\u6d88\u3002"},
    "confirm_close_title": {"en": "Conversion in progress", "zh": "\u8f6c\u6362\u8fdb\u884c\u4e2d"},
    "confirm_close_msg": {
        "en": "A conversion is still running.\nWait for it to finish before closing?",
        "zh": "\u8f6c\u6362\u4ecd\u5728\u8fdb\u884c\u3002\n\u7b49\u5f85\u5b8c\u6210\uff1f",
    },
    "ready": {
        "en": "Please select input files to convert",
        "zh": "\u8bf7\u9009\u62e9\u8981\u8f6c\u6362\u7684\u5b57\u5e55\u6587\u4ef6",
    },
    "eotf_pq_desc": {
        "en": "Absolute brightness, up to 10,000 nits. For HDR10 / Dolby Vision streaming and disc content.",
        "zh": "\u7edd\u5bf9\u4eae\u5ea6\u6620\u5c04\uff0c\u6700\u9ad8\u4e00\u4e07\u5c3c\u7279\u3002\u9002\u7528\u4e8e HDR10/\u675c\u6bd4\u89c6\u754c\u6d41\u5a92\u4f53\u53ca\u84dd\u5149\u5185\u5bb9\u3002",
    },
    "eotf_hlg_desc": {
        "en": "Relative brightness, adapts to display. For broadcast HDR and SDR-compatible content.",
        "zh": "\u76f8\u5bf9\u4eae\u5ea6\u6620\u5c04\uff0c\u9002\u5e94\u663e\u793a\u5668\u3002\u9002\u7528\u4e8e\u5e7f\u64ad HDR \u53ca\u9700\u517c\u5bb9 SDR \u7684\u5185\u5bb9\u3002",
    },
    "ass_filter": {"en": "ASS files", "zh": "ASS \u5b57\u5e55\u6587\u4ef6"},
    "all_filter": {"en": "all files", "zh": "\u6240\u6709\u6587\u4ef6"},
    "brightness_rec_pq": {
        "en": "Recommended: 100\u2013300 nits (BT.2408 standard: 203)",
        "zh": "\u63a8\u8350\uff1a100\u2013300 \u5c3c\u7279\uff08BT.2408 \u6807\u51c6\u503c 203\uff09",
    },
    "brightness_rec_hlg": {
        "en": "Recommended: 100\u2013400 nits (display-adaptive)",
        "zh": "\u63a8\u8350\uff1a100\u2013400 \u5c3c\u7279\uff08\u968f\u663e\u793a\u5668\u81ea\u9002\u5e94\uff09",
    },
}

SUPPORTED_LANGUAGES = ("en", "zh")
_current_lang: str = "en"


def _config_dir() -> str:
    """Platform-appropriate config directory."""
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    return os.path.join(base, "ssaHdrify")


def _config_path() -> str:
    return os.path.join(_config_dir(), "config.json")


def _detect_system_language() -> str:
    """Detect system language; return 'zh' for Chinese locales, 'en' otherwise."""
    try:
        lang = locale.getlocale()[0] or os.environ.get("LANG", "") or ""
    except (ValueError, TypeError):
        lang = ""
    return "zh" if lang.lower().startswith("zh") else "en"


def _load_config() -> dict:
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def _save_config(data: dict) -> None:
    try:
        path = _config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # Best-effort persistence


def init() -> None:
    """Initialize language from config or system detection."""
    global _current_lang
    cfg = _load_config()
    lang = cfg.get("language")
    if lang in SUPPORTED_LANGUAGES:
        _current_lang = lang
    else:
        _current_lang = _detect_system_language()
        _save_config({**cfg, "language": _current_lang})


def get(key: str) -> str:
    """Get localized string for current language."""
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(_current_lang, entry.get("en", key))


def current() -> str:
    """Return current language code."""
    return _current_lang


def set_language(lang: str) -> str:
    """Set language explicitly, save to config, return the language set."""
    global _current_lang
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"
    _current_lang = lang
    cfg = _load_config()
    cfg["language"] = _current_lang
    _save_config(cfg)
    return _current_lang


def toggle() -> str:
    """Toggle between en/zh, save to config, return new language."""
    return set_language("zh" if _current_lang == "en" else "en")
