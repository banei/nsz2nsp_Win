from __future__ import annotations

from tkinter import filedialog
from typing import Callable

import customtkinter as ctk
from tkinterdnd2 import DND_FILES

from nsz_converter.i18n import t
from nsz_converter.ui.theme import Palette, create_button, label_font


class DropZone(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_paths: Callable[[list[str]], None],
        **kwargs,
    ) -> None:
        kwargs.setdefault("fg_color", Palette.SURFACE_ALT)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", Palette.BORDER)
        super().__init__(master, **kwargs)
        self._on_paths = on_paths
        self._dnd_available = True

        self.label = ctk.CTkLabel(
            self,
            text=t("drop_hint"),
            font=label_font(14),
            text_color=Palette.TEXT_MUTED,
        )
        self.label.pack(expand=True, pady=(24, 8))

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=(0, 24))

        self.folder_btn = create_button(button_row, t("pick_folder"), self._pick_folder)
        self.folder_btn.pack(side="left", padx=8)

        self.file_btn = create_button(button_row, t("pick_files"), self._pick_files)
        self.file_btn.pack(side="left", padx=8)

        self._register_dnd()

    def refresh_text(self) -> None:
        hint = t("drop_unavailable") if not self._dnd_available else t("drop_hint")
        self.label.configure(text=hint)
        self.folder_btn.configure(text=t("pick_folder"))
        self.file_btn.configure(text=t("pick_files"))

    def _register_dnd(self) -> None:
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
            self.label.drop_target_register(DND_FILES)
            self.label.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            self._dnd_available = False
            self.label.configure(text=t("drop_unavailable"))

    def _on_drop(self, event) -> None:
        paths = self._parse_drop(event.data)
        if paths:
            self._on_paths(paths)

    @staticmethod
    def _parse_drop(data: str) -> list[str]:
        items: list[str] = []
        current = ""
        in_brace = False
        for char in data:
            if char == "{":
                in_brace = True
                current = ""
            elif char == "}":
                in_brace = False
                if current:
                    items.append(current)
                current = ""
            elif char == " " and not in_brace:
                if current:
                    items.append(current)
                    current = ""
            else:
                current += char
        if current:
            items.append(current)
        return items

    def _pick_folder(self) -> None:
        path = filedialog.askdirectory(title=t("dlg_pick_folder"))
        if path:
            self._on_paths([path])

    def _pick_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title=t("dlg_pick_files"),
            filetypes=[("NSZ files", "*.nsz"), ("All files", "*.*")],
        )
        if paths:
            self._on_paths(list(paths))
