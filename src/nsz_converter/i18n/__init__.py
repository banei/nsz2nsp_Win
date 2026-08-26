"""Internationalization — system locale default with user override."""

from __future__ import annotations

import locale
import os
from typing import Callable

from .catalog import LANGUAGE_NAMES, STATUS_KEYS, SUPPORTED_LANGUAGES, TRANSLATIONS

DEFAULT_LANGUAGE = "en"
SYSTEM_LANGUAGE_SENTINEL = ""

_current_language: str = DEFAULT_LANGUAGE
_listeners: list[Callable[[], None]] = []


def _windows_ui_language() -> str | None:
    if os.name != "nt":
        return None
    try:
        import ctypes

        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        primary = lang_id & 0x3FF
        if primary == 0x04:
            sub = (lang_id >> 10) & 0x3F
            if sub in (0x01, 0x03, 0x0F):
                return "zh_TW"
            return "zh_CN"
        mapping = {
            0x09: "en",
            0x11: "ja",
            0x12: "ko",
            0x0C: "fr",
            0x07: "de",
            0x0A: "es",
            0x16: "pt",
            0x19: "ru",
            0x10: "it",
        }
        return mapping.get(primary)
    except Exception:
        return None


def detect_system_language() -> str:
    """Map OS locale to a supported language code."""
    win_lang = _windows_ui_language()
    if win_lang:
        return win_lang

    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        raw = os.environ.get(var)
        if raw:
            code = _normalize_locale(raw.split(".")[0])
            if code:
                return code

    for getter_name in ("getlocale",):
        try:
            if getter_name == "getlocale":
                result = locale.getlocale()
            else:
                continue
            if result and result[0]:
                code = _normalize_locale(result[0])
                if code:
                    return code
        except Exception:
            continue

    return DEFAULT_LANGUAGE


def _normalize_locale(raw: str) -> str | None:
    if not raw:
        return None
    tag = raw.replace("-", "_")
    lower = tag.lower()

    if lower.startswith("zh"):
        if any(part in lower for part in ("tw", "hk", "hant", "mo")):
            return "zh_TW"
        return "zh_CN"

    base = lower.split("_")[0]
    if base in SUPPORTED_LANGUAGES:
        return base
    return None


def resolve_language(stored: str = "") -> str:
    """Resolve persisted setting ('' = follow system)."""
    if stored and stored in SUPPORTED_LANGUAGES:
        return stored
    return detect_system_language()


def init_language(stored: str = "") -> str:
    """Initialize active language from settings."""
    global _current_language
    _current_language = resolve_language(stored)
    return _current_language


def get_language() -> str:
    return _current_language


def set_language(code: str) -> None:
    """Switch active language and notify listeners."""
    global _current_language
    resolved = resolve_language(code) if code else detect_system_language()
    if resolved == _current_language:
        return
    _current_language = resolved
    for listener in list(_listeners):
        listener()


def add_language_listener(callback: Callable[[], None]) -> None:
    _listeners.append(callback)


def t(key: str, **kwargs: object) -> str:
    """Translate *key* for the active language, with optional format args."""
    table = TRANSLATIONS.get(_current_language) or TRANSLATIONS[DEFAULT_LANGUAGE]
    text = table.get(key) or TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def status_label(status_value: str) -> str:
    key = STATUS_KEYS.get(status_value, status_value)
    return t(key)


def language_option_label(code: str) -> str:
    if code == SYSTEM_LANGUAGE_SENTINEL:
        sys_lang = detect_system_language()
        return t("language_system", name=LANGUAGE_NAMES.get(sys_lang, sys_lang))
    return LANGUAGE_NAMES.get(code, code)


def language_choices() -> list[tuple[str, str]]:
    """Return (stored_value, display_label) pairs for the language selector."""
    choices: list[tuple[str, str]] = [(SYSTEM_LANGUAGE_SENTINEL, language_option_label(SYSTEM_LANGUAGE_SENTINEL))]
    for code in SUPPORTED_LANGUAGES:
        choices.append((code, LANGUAGE_NAMES[code]))
    return choices


__all__ = [
    "DEFAULT_LANGUAGE",
    "LANGUAGE_NAMES",
    "SUPPORTED_LANGUAGES",
    "SYSTEM_LANGUAGE_SENTINEL",
    "add_language_listener",
    "detect_system_language",
    "get_language",
    "init_language",
    "language_choices",
    "language_option_label",
    "resolve_language",
    "set_language",
    "status_label",
    "t",
]
