from __future__ import annotations

from tkinter import filedialog
from typing import Callable

import customtkinter as ctk
from tkinterdnd2 import DND_FILES

from nsz_converter.ui.theme import Palette


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

        self.label = ctk.CTkLabel(
            self,
            text="拖拽 .nsz 文件或文件夹到此处",
            font=ctk.CTkFont(size=15),
            text_color=Palette.TEXT_MUTED,
        )
        self.label.pack(expand=True, pady=(24, 8))

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=(0, 24))

        self.folder_btn = ctk.CTkButton(
            button_row,
            text="选择文件夹",
            command=self._pick_folder,
            width=120,
            fg_color=Palette.BTN_SECONDARY,
            hover_color=Palette.BTN_SECONDARY_HOVER,
            text_color=Palette.BTN_SECONDARY_TEXT,
        )
        self.folder_btn.pack(side="left", padx=8)

        self.file_btn = ctk.CTkButton(
            button_row,
            text="选择文件",
            command=self._pick_files,
            width=120,
            fg_color=Palette.BTN_SECONDARY,
            hover_color=Palette.BTN_SECONDARY_HOVER,
            text_color=Palette.BTN_SECONDARY_TEXT,
        )
        self.file_btn.pack(side="left", padx=8)

        self._register_dnd()

    def _register_dnd(self) -> None:
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
            self.label.drop_target_register(DND_FILES)
            self.label.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            self.label.configure(text="拖拽不可用，请使用下方按钮选择文件")

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
        path = filedialog.askdirectory(title="选择包含 NSZ 的文件夹")
        if path:
            self._on_paths([path])

    def _pick_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="选择 NSZ 文件",
            filetypes=[("NSZ files", "*.nsz"), ("All files", "*.*")],
        )
        if paths:
            self._on_paths(list(paths))
