from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from nsz_converter.i18n import (
    SYSTEM_LANGUAGE_SENTINEL,
    language_choices,
    language_option_label,
    t,
)
from nsz_converter.ui.theme import FONT_SIZE, Palette, btn_height, label_font


class LanguageSelector(ctk.CTkFrame):
    def __init__(
        self,
        master,
        stored_language: str,
        on_change: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_change = on_change
        self._lang_display_to_code: dict[str, str] = {}
        self._updating = False

        self._label = ctk.CTkLabel(
            self,
            text=t("language"),
            font=label_font(FONT_SIZE),
            text_color=Palette.TEXT_MUTED,
        )
        self._label.pack(side="left", padx=(0, 6))

        self._lang_var = ctk.StringVar()
        self._menu = ctk.CTkOptionMenu(
            self,
            variable=self._lang_var,
            values=self._menu_values(),
            command=self._handle_change,
            font=label_font(FONT_SIZE),
            height=btn_height(compact=True),
            dropdown_font=label_font(FONT_SIZE),
            width=180,
        )
        self._menu.pack(side="left")
        self.set_stored_language(stored_language)

    def _menu_values(self) -> list[str]:
        self._lang_display_to_code = {}
        values: list[str] = []
        for code, _ in language_choices():
            display = language_option_label(code)
            self._lang_display_to_code[display] = code
            values.append(display)
        return values

    def _handle_change(self, choice: str) -> None:
        if self._updating:
            return
        stored = self.get_stored_language()
        self._on_change(stored)

    def get_stored_language(self) -> str:
        code = self._lang_display_to_code.get(self._lang_var.get(), SYSTEM_LANGUAGE_SENTINEL)
        return "" if code == SYSTEM_LANGUAGE_SENTINEL else code

    def set_stored_language(self, stored: str) -> None:
        self._updating = True
        try:
            self._menu.configure(values=self._menu_values())
            self._lang_var.set(language_option_label(stored or SYSTEM_LANGUAGE_SENTINEL))
        finally:
            self._updating = False

    def refresh_text(self) -> None:
        current = self._lang_display_to_code.get(self._lang_var.get(), SYSTEM_LANGUAGE_SENTINEL)
        self._updating = True
        try:
            self._label.configure(text=t("language"))
            self._menu.configure(values=self._menu_values())
            self._lang_var.set(language_option_label(current))
        finally:
            self._updating = False
