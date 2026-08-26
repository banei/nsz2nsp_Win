from __future__ import annotations

import customtkinter as ctk

from nsz_converter.ui.theme import Palette


class LogPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, **kwargs)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            header,
            text="日志",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Palette.TEXT,
        ).pack(side="left")

        self.copy_btn = ctk.CTkButton(
            header,
            text="复制",
            width=60,
            command=self.copy_all,
            fg_color=Palette.BTN_SECONDARY,
            hover_color=Palette.BTN_SECONDARY_HOVER,
            text_color=Palette.BTN_SECONDARY_TEXT,
        )
        self.copy_btn.pack(side="right", padx=4)
        self.clear_btn = ctk.CTkButton(
            header,
            text="清空",
            width=60,
            command=self.clear,
            fg_color=Palette.BTN_SECONDARY,
            hover_color=Palette.BTN_SECONDARY_HOVER,
            text_color=Palette.BTN_SECONDARY_TEXT,
        )
        self.clear_btn.pack(side="right")

        self.text = ctk.CTkTextbox(
            self,
            height=160,
            wrap="word",
            fg_color=Palette.SURFACE_ALT,
            border_color=Palette.BORDER,
            text_color=Palette.TEXT_MUTED,
        )
        self.text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.text.configure(state="disabled")

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
