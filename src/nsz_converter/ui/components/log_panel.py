from __future__ import annotations

import customtkinter as ctk

from nsz_converter.i18n import t
from nsz_converter.ui.theme import Palette, create_button, label_font


class LogPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 4))

        self.title_label = ctk.CTkLabel(
            header,
            text=t("log_title"),
            font=label_font(14, bold=True),
            text_color=Palette.TEXT,
        )
        self.title_label.pack(side="left")

        self.copy_btn = create_button(header, t("copy"), self.copy_all, compact=True)
        self.copy_btn.pack(side="right", padx=4)
        self.clear_btn = create_button(header, t("clear"), self.clear, compact=True)
        self.clear_btn.pack(side="right")

        self.text = ctk.CTkTextbox(
            self,
            height=160,
            wrap="word",
            font=label_font(12),
            fg_color=Palette.SURFACE_ALT,
            border_color=Palette.BORDER,
            text_color=Palette.TEXT,
        )
        self.text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.text.configure(state="disabled")

    def refresh_text(self) -> None:
        self.title_label.configure(text=t("log_title"))
        self.copy_btn.configure(text=t("copy"))
        self.clear_btn.configure(text=t("clear"))

    def append(self, message: str) -> None:
        self.text.configure(state="normal")
        self.text.insert("end", message + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def copy_all(self) -> None:
        content = self.text.get("1.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(content)
