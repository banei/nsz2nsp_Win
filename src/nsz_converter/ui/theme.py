from __future__ import annotations

import sys
from pathlib import Path

import customtkinter as ctk

if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys._MEIPASS)
    _THEME_PATH = _BASE_DIR / "nsz_converter" / "ui" / "assets" / "soft_theme.json"
else:
    _THEME_PATH = Path(__file__).parent / "assets" / "soft_theme.json"


class Palette:
    BG = ("#EDF1F5", "#2A2D32")
    SURFACE = ("#F7F9FB", "#34383E")
    SURFACE_ALT = ("#FFFFFF", "#3A3E45")
    BORDER = ("#D8E0E8", "#4A5058")
    ROW = ("#F3F6F9", "#383C42")
    ROW_ACTIVE = ("#E8F0F7", "#404650")
    TEXT = ("#4A5568", "#C8CDD3")
    TEXT_MUTED = ("#8B97A5", "#9AA0A8")
    BTN_PRIMARY = ("#8FAFC9", "#6E8FA8")
    BTN_PRIMARY_HOVER = ("#7A9DB8", "#5E7F98")
    BTN_SECONDARY = ("#E2E9F0", "#454A52")
    BTN_SECONDARY_HOVER = ("#D4DDE6", "#505660")
    BTN_SECONDARY_TEXT = ("#5A6573", "#D0D4D8")
    STATUS_OK = ("#6B9080", "#7FA896")
    STATUS_RUN = ("#7A9DB8", "#8FAFC9")
    STATUS_FAIL = ("#C08888", "#C89898")
    STATUS_WAIT = ("#9AA5B1", "#8A9098")


def apply_theme() -> None:
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme(str(_THEME_PATH))


def window_bg() -> str:
    mode = ctk.get_appearance_mode()
    return Palette.BG[1] if mode == "Dark" else Palette.BG[0]


def pick(pair: tuple[str, str]) -> str:
    mode = ctk.get_appearance_mode()
    return pair[1] if mode == "Dark" else pair[0]
