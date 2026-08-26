from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from nsz_converter.config.settings import AppSettings
from nsz_converter.ui.theme import Palette, apply_theme


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, settings: AppSettings, on_save) -> None:
        super().__init__(master)
        apply_theme()
        self.title("设置")
        self.geometry("520x360")
        self.resizable(False, False)
        self._settings = settings
        self._on_save = on_save
        self.transient(master)
        self.grab_set()

        self.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text="密钥文件路径 (prod.keys):",
            text_color=Palette.TEXT,
        ).grid(row=0, column=0, padx=12, pady=(16, 8), sticky="w")
        self.keyset_var = ctk.StringVar(value=settings.keyset_path)
        self.keyset_entry = ctk.CTkEntry(self, textvariable=self.keyset_var)
        self.keyset_entry.grid(row=0, column=1, padx=12, pady=(16, 8), sticky="ew")
        ctk.CTkButton(
            self,
            text="浏览",
            width=60,
            command=self._browse_keyset,
            fg_color=Palette.BTN_SECONDARY,
            hover_color=Palette.BTN_SECONDARY_HOVER,
            text_color=Palette.BTN_SECONDARY_TEXT,
        ).grid(row=0, column=2, padx=(0, 12), pady=(16, 8))

        self.native_progress_var = ctk.BooleanVar(value=settings.show_native_progress)
        ctk.CTkCheckBox(
            self,
            text="显示 nsz 原生进度输出",
            variable=self.native_progress_var,
        ).grid(row=1, column=0, columnspan=3, padx=12, pady=8, sticky="w")

        ctk.CTkLabel(
            self,
            text="留空密钥路径时将自动查找 ~/.switch/prod.keys 等默认位置",
            text_color=Palette.TEXT_MUTED,
        ).grid(row=2, column=0, columnspan=3, padx=12, pady=4, sticky="w")

        ctk.CTkLabel(
            self,
            text="最近转换历史",
            font=ctk.CTkFont(weight="bold"),
            text_color=Palette.TEXT,
        ).grid(row=3, column=0, columnspan=3, padx=12, pady=(16, 4), sticky="w")
        history_box = ctk.CTkTextbox(
            self,
            height=120,
            fg_color=Palette.SURFACE_ALT,
            border_color=Palette.BORDER,
            text_color=Palette.TEXT_MUTED,
        )
        history_box.grid(row=4, column=0, columnspan=3, padx=12, pady=4, sticky="nsew")
        if settings.history:
            for item in settings.history[:20]:
                history_box.insert(
                    "end",
                    f"[{item.status}] {item.file} ({item.duration:.1f}s) — {item.time}\n",
                )
        else:
            history_box.insert("end", "暂无历史记录\n")
        history_box.configure(state="disabled")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=5, column=0, columnspan=3, pady=16)
        ctk.CTkButton(
            btn_row,
            text="保存",
            command=self._save,
            fg_color=Palette.BTN_PRIMARY,
            hover_color=Palette.BTN_PRIMARY_HOVER,
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_row,
            text="取消",
            command=self.destroy,
            fg_color=Palette.BTN_SECONDARY,
            hover_color=Palette.BTN_SECONDARY_HOVER,
            text_color=Palette.BTN_SECONDARY_TEXT,
        ).pack(side="left", padx=8)

    def _browse_keyset(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 prod.keys",
            filetypes=[("Key files", "*.keys"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.keyset_var.set(path)

    def _save(self) -> None:
        self._settings.keyset_path = self.keyset_var.get().strip()
        self._settings.show_native_progress = bool(self.native_progress_var.get())
        self._on_save(self._settings)
        self.destroy()
