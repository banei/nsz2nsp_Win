from __future__ import annotations

from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from nsz_converter.config.settings import AppSettings
from nsz_converter.i18n import t
from nsz_converter.ui.theme import FONT_SIZE, FONT_SIZE_LG, LABEL_HEIGHT, Palette, create_button, label_font


class SettingsOverlay(ctk.CTkFrame):
    """In-app settings panel — avoids CTkToplevel + Tk grab issues on Windows."""

    def __init__(
        self,
        master,
        settings: AppSettings,
        on_save: Callable[[AppSettings], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=Palette.BG, **kwargs)
        self._on_save = on_save
        self._settings = settings
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()

        self.panel = ctk.CTkFrame(self, fg_color=Palette.SURFACE, width=520, height=400)
        self.panel.place(relx=0.5, rely=0.5, anchor="center")
        self.panel.grid_propagate(False)
        self.panel.columnconfigure(1, weight=1)

        self._title_label: ctk.CTkLabel | None = None
        self._keyset_label: ctk.CTkLabel | None = None
        self._keyset_hint_label: ctk.CTkLabel | None = None
        self._history_title: ctk.CTkLabel | None = None
        self._browse_btn = None
        self._save_btn = None
        self._cancel_btn = None

        self._build_widgets(settings)
        self.place_forget()

    def _build_widgets(self, settings: AppSettings) -> None:
        header = ctk.CTkFrame(self.panel, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=12, pady=(16, 8))
        self._title_label = ctk.CTkLabel(
            header,
            text=t("settings_title"),
            font=label_font(FONT_SIZE_LG, bold=True),
            text_color=Palette.TEXT,
        )
        self._title_label.pack(side="left")

        self._keyset_label = ctk.CTkLabel(
            self.panel,
            text=t("keyset_path"),
            text_color=Palette.TEXT,
        )
        self._keyset_label.grid(row=1, column=0, padx=12, pady=(8, 8), sticky="w")
        self.keyset_var = ctk.StringVar(value=settings.keyset_path)
        self.keyset_entry = ctk.CTkEntry(self.panel, textvariable=self.keyset_var)
        self.keyset_entry.grid(row=1, column=1, padx=12, pady=(8, 8), sticky="ew")
        self._browse_btn = create_button(self.panel, t("browse"), self._browse_keyset, compact=True)
        self._browse_btn.grid(row=1, column=2, padx=(0, 12), pady=(8, 8))

        self.native_progress_var = ctk.BooleanVar(value=settings.show_native_progress)
        self.native_progress_cb = ctk.CTkCheckBox(
            self.panel,
            text=t("show_native_progress"),
            variable=self.native_progress_var,
            font=label_font(FONT_SIZE),
            height=LABEL_HEIGHT,
            checkbox_width=18,
            checkbox_height=18,
        )
        self.native_progress_cb.grid(row=2, column=0, columnspan=3, padx=12, pady=8, sticky="w")

        self._keyset_hint_label = ctk.CTkLabel(
            self.panel,
            text=t("keyset_hint"),
            text_color=Palette.TEXT_MUTED,
        )
        self._keyset_hint_label.grid(row=3, column=0, columnspan=3, padx=12, pady=4, sticky="w")

        self._history_title = ctk.CTkLabel(
            self.panel,
            text=t("recent_history"),
            font=label_font(13, bold=True),
            text_color=Palette.TEXT,
        )
        self._history_title.grid(row=4, column=0, columnspan=3, padx=12, pady=(12, 4), sticky="w")

        self.history_box = ctk.CTkTextbox(
            self.panel,
            height=120,
            fg_color=Palette.SURFACE_ALT,
            border_color=Palette.BORDER,
            text_color=Palette.TEXT_MUTED,
        )
        self.history_box.grid(row=5, column=0, columnspan=3, padx=12, pady=4, sticky="ew")

        btn_row = ctk.CTkFrame(self.panel, fg_color="transparent")
        btn_row.grid(row=6, column=0, columnspan=3, pady=16)
        self._save_btn = create_button(btn_row, t("save"), self._save, primary=True)
        self._save_btn.pack(side="left", padx=8)
        self._cancel_btn = create_button(btn_row, t("cancel"), self.hide)
        self._cancel_btn.pack(side="left", padx=8)

        self._fill_history(settings)

    def refresh_text(self) -> None:
        if self._title_label:
            self._title_label.configure(text=t("settings_title"))
        if self._keyset_label:
            self._keyset_label.configure(text=t("keyset_path"))
        if self._keyset_hint_label:
            self._keyset_hint_label.configure(text=t("keyset_hint"))
        if self._history_title:
            self._history_title.configure(text=t("recent_history"))
        if self._browse_btn:
            self._browse_btn.configure(text=t("browse"))
        if self._save_btn:
            self._save_btn.configure(text=t("save"))
        if self._cancel_btn:
            self._cancel_btn.configure(text=t("cancel"))
        self.native_progress_cb.configure(text=t("show_native_progress"))
        self._fill_history(self._settings)

    def show(self, settings: AppSettings) -> None:
        self._settings = settings
        self.keyset_var.set(settings.keyset_path)
        self.native_progress_var.set(settings.show_native_progress)
        self._fill_history(settings)
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self.keyset_entry.focus_set()

    def hide(self) -> None:
        self.place_forget()
        self.master.focus_set()

    def _fill_history(self, settings: AppSettings) -> None:
        self.history_box.configure(state="normal")
        self.history_box.delete("1.0", "end")
        if settings.history:
            for item in settings.history[:20]:
                self.history_box.insert(
                    "end",
                    f"[{item.status}] {item.file} ({item.duration:.1f}s) — {item.time}\n",
                )
        else:
            self.history_box.insert("end", t("no_history") + "\n")
        self.history_box.configure(state="disabled")

    def _browse_keyset(self) -> None:
        path = filedialog.askopenfilename(
            title=t("dlg_pick_keyset"),
            filetypes=[("Key files", "*.keys"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.keyset_var.set(path)

    def _save(self) -> None:
        self._settings.keyset_path = self.keyset_var.get().strip()
        self._settings.show_native_progress = bool(self.native_progress_var.get())
        self._on_save(self._settings)
        self.hide()


# Backward-compatible alias
SettingsDialog = SettingsOverlay
