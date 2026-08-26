from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from typing import Any, Callable

import customtkinter as ctk

if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys._MEIPASS)
    _THEME_PATH = _BASE_DIR / "nsz_converter" / "ui" / "assets" / "soft_theme.json"
else:
    _THEME_PATH = Path(__file__).parent / "assets" / "soft_theme.json"

FONT_FAMILY = "Microsoft YaHei UI"
FONT_SIZE = 12
FONT_SIZE_SM = 11
FONT_SIZE_LG = 13
BTN_HEIGHT = 44
BTN_HEIGHT_SM = 38
ROW_HEIGHT = 44
LABEL_HEIGHT = 34

# Queue table column widths (pixels)
COL_STATUS = 96
COL_FILENAME = 220
COL_PROGRESS = 248
COL_DURATION = 68
COL_ACTION = 68

LABEL_INSET = 8
BTN_PAD_COMPACT = 30
BTN_PAD_NORMAL = 36


class Palette:
    BG = ("#EDF1F5", "#2A2D32")
    SURFACE = ("#F7F9FB", "#34383E")
    SURFACE_ALT = ("#FFFFFF", "#3A3E45")
    BORDER = ("#D8E0E8", "#4A5058")
    ROW = ("#F3F6F9", "#383C42")
    ROW_ACTIVE = ("#E8F0F7", "#404650")
    TEXT = ("#2F3A45", "#D8DCE0")
    TEXT_MUTED = ("#5A6573", "#A8ADB3")
    BTN_PRIMARY = ("#7A9DB8", "#6E8FA8")
    BTN_PRIMARY_HOVER = ("#6A8DA8", "#5E7F98")
    BTN_PRIMARY_TEXT = ("#FFFFFF", "#FFFFFF")
    BTN_SECONDARY = ("#E2E9F0", "#454A52")
    BTN_SECONDARY_HOVER = ("#D4DDE6", "#505660")
    BTN_SECONDARY_TEXT = ("#2F3A45", "#E8ECF0")
    STATUS_OK = ("#4F7A66", "#7FA896")
    STATUS_RUN = ("#4A7390", "#8FAFC9")
    STATUS_FAIL = ("#9E5A5A", "#C89898")
    STATUS_WAIT = ("#5A6573", "#8A9098")


def apply_theme() -> None:
    ctk.set_appearance_mode("light")
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)
    ctk.set_default_color_theme(str(_THEME_PATH))


def window_bg() -> str:
    mode = ctk.get_appearance_mode()
    return Palette.BG[1] if mode == "Dark" else Palette.BG[0]


def pick(pair: tuple[str, str]) -> str:
    mode = ctk.get_appearance_mode()
    return pair[1] if mode == "Dark" else pair[0]


def _char_width(char: str, size: int, *, bold: bool = False) -> float:
    bold_factor = 1.06 if bold else 1.0
    if ord(char) < 128:
        return size * 0.58 * bold_factor
    return size * 1.05 * bold_factor


def text_width(text: str, size: int = 13, *, bold: bool = False) -> int:
    if not text:
        return 0
    return int(sum(_char_width(char, size, bold=bold) for char in text))


def btn_font(size: int = 13) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="normal")


def label_font(size: int = 13, *, bold: bool = False) -> ctk.CTkFont:
    weight = "bold" if bold else "normal"
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def btn_width(text: str, *, compact: bool = False) -> int:
    size = FONT_SIZE_SM if compact else FONT_SIZE
    padding = BTN_PAD_COMPACT if compact else BTN_PAD_NORMAL
    minimum = 68 if compact else 76
    return max(minimum, text_width(text, size) + padding)


def btn_height(*, compact: bool = False) -> int:
    size = FONT_SIZE_SM if compact else FONT_SIZE
    minimum = BTN_HEIGHT_SM if compact else BTN_HEIGHT
    return max(minimum, size + 30)


class TextButton(tk.Frame):
    """Native tk button — CTkFrame/CTkButton canvas layers hide child labels on Windows."""

    def __init__(
        self,
        master,
        text: str,
        command: Callable[[], None] | None,
        *,
        primary: bool = False,
        compact: bool = False,
        width: int | None = None,
        height: int | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.pop("fg_color", None)
        kwargs.pop("hover_color", None)
        kwargs.pop("text_color", None)
        kwargs.pop("corner_radius", None)

        self._command = command
        self._primary = primary
        self._compact = compact
        self._enabled = True
        self._normal_fg = Palette.BTN_PRIMARY if primary else Palette.BTN_SECONDARY
        self._hover_fg = Palette.BTN_PRIMARY_HOVER if primary else Palette.BTN_SECONDARY_HOVER
        self._text_pair = Palette.BTN_PRIMARY_TEXT if primary else Palette.BTN_SECONDARY_TEXT
        self._disabled_text = Palette.TEXT_MUTED

        size = FONT_SIZE_SM if compact else FONT_SIZE
        frame_width = width if width is not None else btn_width(text, compact=compact)
        frame_height = height if height is not None else btn_height(compact=compact)
        bg = pick(self._normal_fg)

        super().__init__(
            master,
            bg=bg,
            width=frame_width,
            height=frame_height,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._label = tk.Label(
            self,
            text=text,
            font=(FONT_FAMILY, size),
            fg=pick(self._text_pair),
            bg=bg,
            cursor="hand2",
            borderwidth=0,
            padx=8,
            pady=4,
            anchor="center",
        )
        self._label.place(relx=0.5, rely=0.5, anchor="center")

        for widget in (self, self._label):
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _set_bg(self, color: str) -> None:
        self.configure(bg=color)
        self._label.configure(bg=color)

    def _on_click(self, _event=None) -> None:
        if self._enabled and self._command:
            self._command()

    def _on_enter(self, _event=None) -> None:
        if not self._enabled:
            return
        self._set_bg(pick(self._hover_fg))

    def _on_leave(self, _event=None) -> None:
        if not self._enabled:
            return
        self._set_bg(pick(self._normal_fg))

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        if cnf:
            kwargs.update(cnf)
        if "text" in kwargs:
            self._label.configure(text=kwargs.pop("text"))
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "state" in kwargs:
            state = kwargs.pop("state")
            self._enabled = state != "disabled"
            normal = pick(self._normal_fg)
            self._set_bg(normal)
            if self._enabled:
                self._label.configure(fg=pick(self._text_pair), cursor="hand2")
            else:
                self._label.configure(fg=pick(self._disabled_text), cursor="arrow")
        if kwargs:
            super().configure(**kwargs)

    def cget(self, key):  # type: ignore[override]
        if key == "text":
            return self._label.cget("text")
        if key == "state":
            return "normal" if self._enabled else "disabled"
        return super().cget(key)


class FixedCTkLabel(ctk.CTkLabel):
    """CTkLabel with tk label kept above the background canvas."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.after_idle(self._lift_label)

    def _lift_label(self) -> None:
        label = getattr(self, "_label", None)
        if label is not None:
            label.lift()

    def _draw(self, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)
        self._lift_label()

    def _update_font(self) -> None:
        super()._update_font()
        self._lift_label()


def truncate_text(text: str, max_width: int, size: int = 12, *, bold: bool = False) -> str:
    if not text:
        return ""
    if text_width(text, size, bold=bold) <= max_width:
        return text
    ellipsis = "…"
    if text_width(ellipsis, size, bold=bold) > max_width:
        return ellipsis
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = text[:mid] + ellipsis
        if text_width(candidate, size, bold=bold) <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + ellipsis if lo > 0 else ellipsis


def fit_label_text(text: str, column_width: int, size: int = 12, *, bold: bool = False) -> str:
    return truncate_text(text, max(0, column_width - LABEL_INSET), size, bold=bold)


def create_button(
    master,
    text: str,
    command: Callable[[], None],
    *,
    primary: bool = False,
    compact: bool = False,
    **kwargs: Any,
) -> TextButton:
    width = kwargs.pop("width", btn_width(text, compact=compact))
    height = kwargs.pop("height", btn_height(compact=compact))
    return TextButton(
        master,
        text,
        command,
        primary=primary,
        compact=compact,
        width=width,
        height=height,
        **kwargs,
    )


def create_fixed_label(
    master,
    text: str,
    column_width: int,
    *,
    size: int = 12,
    bold: bool = False,
    text_color=Palette.TEXT,
    anchor: str = "w",
    **kwargs: Any,
) -> FixedCTkLabel:
    return FixedCTkLabel(
        master,
        text=fit_label_text(text, column_width, size, bold=bold),
        width=column_width,
        height=LABEL_HEIGHT,
        anchor=anchor,
        font=label_font(size, bold=bold),
        text_color=text_color,
        fg_color="transparent",
        **kwargs,
    )


def update_fixed_label(
    label: FixedCTkLabel,
    text: str,
    column_width: int,
    *,
    size: int = 12,
    bold: bool = False,
) -> None:
    label.configure(text=fit_label_text(text, column_width, size, bold=bold))
