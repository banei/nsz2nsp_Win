from __future__ import annotations

import tkinter.messagebox as messagebox

import customtkinter as ctk
from tkinterdnd2 import TkinterDnD

from nsz_converter.config.settings import AppSettings, load_settings, save_settings
from nsz_converter.core.nsz_runner import is_nsz_available
from nsz_converter.i18n import init_language, t
from nsz_converter.queue.task import Task, TaskStatus
from nsz_converter.queue.worker import QueueWorker

from .components.drop_zone import DropZone
from .components.language_selector import LanguageSelector
from .components.log_panel import LogPanel
from .components.queue_panel import QueuePanel
from .dialogs import SettingsOverlay
from .theme import FONT_SIZE_LG, Palette, apply_theme, btn_height, create_button, label_font, window_bg


class NszConverterApp(TkinterDnD.Tk):
    def __init__(self) -> None:
        super().__init__()
        apply_theme()
        self.configure(bg=window_bg())

        self.settings = load_settings()
        init_language(self.settings.language)
        self.title(t("app_title"))
        self.geometry(self.settings.window_geometry)
        self.minsize(820, 620)

        self._paused = False
        self.worker = QueueWorker(
            configured_keyset=self.settings.keyset_path,
            show_native_progress=self.settings.show_native_progress,
            on_task_update=self._on_task_update_threadsafe,
            on_log=self._on_log_threadsafe,
            on_idle=self._on_worker_idle_threadsafe,
        )

        self._heading_label: ctk.CTkLabel | None = None
        self._settings_btn = None
        self.lang_selector: LanguageSelector | None = None
        self._controls: ctk.CTkFrame | None = None
        self.drop_zone: DropZone | None = None
        self.queue_panel: QueuePanel | None = None
        self.log_panel: LogPanel | None = None
        self.settings_overlay: SettingsOverlay | None = None
        self.start_btn: ctk.CTkButton | None = None
        self.pause_btn: ctk.CTkButton | None = None
        self.cancel_btn: ctk.CTkButton | None = None
        self.clear_btn: ctk.CTkButton | None = None
        self.clear_done_btn: ctk.CTkButton | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self._build_header()
        self._build_content()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if not is_nsz_available():
            messagebox.showwarning(t("missing_nsz_title"), t("missing_nsz_body"))
            if self.start_btn:
                self.start_btn.configure(state="disabled")

    def _build_header(self) -> None:
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        top.grid_columnconfigure(0, weight=1)

        self._heading_label = ctk.CTkLabel(
            top,
            text=t("app_heading"),
            font=label_font(FONT_SIZE_LG, bold=True),
            text_color=Palette.TEXT,
        )
        self._heading_label.grid(row=0, column=0, sticky="w")

        right = ctk.CTkFrame(top, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")

        self.lang_selector = LanguageSelector(
            right,
            stored_language=self.settings.language,
            on_change=self._on_language_changed,
        )
        self.lang_selector.pack(side="left", padx=(0, 12))

        self._settings_btn = create_button(right, t("settings"), self._open_settings)
        self._settings_btn.pack(side="left")

    def _build_content(self) -> None:
        self.drop_zone = DropZone(self, on_paths=self._add_paths, height=140)
        self.drop_zone.grid(row=1, column=0, sticky="ew", padx=16, pady=8)

        self._controls = ctk.CTkFrame(self, fg_color="transparent", height=btn_height() + 4)
        self._controls.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 8))
        self._controls.grid_propagate(False)

        self.start_btn = create_button(self._controls, t("start"), self._start, primary=True)
        self.start_btn.pack(side="left", padx=4)
        self.pause_btn = create_button(self._controls, t("pause"), self._toggle_pause)
        self.pause_btn.pack(side="left", padx=4)
        self.cancel_btn = create_button(self._controls, t("cancel_current"), self._cancel_current)
        self.cancel_btn.pack(side="left", padx=4)
        self.clear_btn = create_button(self._controls, t("clear_queue"), self._clear_queue)
        self.clear_btn.pack(side="left", padx=4)
        self.clear_done_btn = create_button(
            self._controls, t("clear_completed"), self._clear_completed
        )
        self.clear_done_btn.pack(side="left", padx=4)

        self.queue_panel = QueuePanel(self, on_retry=self._retry_task, fg_color=Palette.SURFACE)
        self.queue_panel.grid(row=3, column=0, sticky="nsew", padx=16, pady=8)

        self.log_panel = LogPanel(self, fg_color=Palette.SURFACE)
        self.log_panel.grid(row=4, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.log_panel.append(t("log_ready"))

        self.settings_overlay = SettingsOverlay(
            self,
            self.settings,
            on_save=self._apply_settings,
        )

    def _capture_log_lines(self) -> list[str]:
        if not self.log_panel:
            return []
        raw = self.log_panel.text.get("1.0", "end").strip()
        return [line for line in raw.splitlines() if line]

    def _tear_down_content(self) -> None:
        widgets = (
            self.drop_zone,
            self._controls,
            self.queue_panel,
            self.log_panel,
            self.settings_overlay,
        )
        for widget in widgets:
            if widget is not None and widget.winfo_exists():
                widget.destroy()
        self.drop_zone = None
        self._controls = None
        self.queue_panel = None
        self.log_panel = None
        self.settings_overlay = None
        self.start_btn = None
        self.pause_btn = None
        self.cancel_btn = None
        self.clear_btn = None
        self.clear_done_btn = None

    def _reload_ui(self, *, log_lines: list[str] | None = None, overlay_open: bool = False) -> None:
        start_disabled = (
            self.start_btn is not None and str(self.start_btn.cget("state")) == "disabled"
        )
        if log_lines is None:
            log_lines = self._capture_log_lines()

        self._tear_down_content()

        self.title(t("app_title"))
        if self._heading_label:
            self._heading_label.configure(text=t("app_heading"))
        if self._settings_btn:
            self._settings_btn.configure(text=t("settings"))
        if self.lang_selector:
            self.lang_selector.refresh_text()

        self._build_content()

        if self._paused and self.pause_btn:
            self.pause_btn.configure(text=t("resume"))
        if start_disabled and self.start_btn:
            self.start_btn.configure(state="disabled")

        if self.queue_panel:
            self.queue_panel.sync_tasks(self.worker.tasks)

        if self.log_panel:
            if log_lines:
                for line in log_lines:
                    self.log_panel.append(line)
            else:
                self.log_panel.append(t("log_ready"))

        if overlay_open and self.settings_overlay:
            self.settings_overlay.show(self.settings)

    def _on_language_changed(self, stored: str) -> None:
        if stored == self.settings.language:
            return
        self.settings.language = stored
        init_language(stored)
        save_settings(self.settings)
        self._reload_ui()

    def _add_paths(self, paths: list[str]) -> None:
        self.worker.add_paths(paths)
        self._refresh_queue()
        self.worker.start()

    def _start(self) -> None:
        if self._paused:
            self._paused = False
            if self.pause_btn:
                self.pause_btn.configure(text=t("pause"))
            self.worker.resume()
        else:
            self.worker.start()
        self._refresh_queue()

    def _toggle_pause(self) -> None:
        if self._paused:
            self._paused = False
            if self.pause_btn:
                self.pause_btn.configure(text=t("pause"))
            self.worker.resume()
        else:
            self._paused = True
            if self.pause_btn:
                self.pause_btn.configure(text=t("resume"))
            self.worker.pause()

    def _cancel_current(self) -> None:
        self.worker.cancel_current()

    def _clear_queue(self) -> None:
        self.worker.clear(completed_only=False)
        self._refresh_queue()

    def _clear_completed(self) -> None:
        self.worker.clear(completed_only=True)
        self._refresh_queue()

    def _retry_task(self, task_id: str) -> None:
        self.worker.retry_task(task_id)
        if self._paused:
            self._toggle_pause()
        else:
            self.worker.start()
        self._refresh_queue()

    def _open_settings(self) -> None:
        if self.settings_overlay:
            self.settings_overlay.show(self.settings)

    def _apply_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        self.worker.configure(
            configured_keyset=settings.keyset_path,
            show_native_progress=settings.show_native_progress,
        )
        save_settings(settings)
        if self.log_panel:
            self.log_panel.append(t("settings_saved"))

    def _on_task_update_threadsafe(self, task: Task) -> None:
        self.after(0, lambda: self._on_task_update(task))

    def _on_log_threadsafe(self, message: str) -> None:
        self.after(0, lambda: self._append_log(message))

    def _append_log(self, message: str) -> None:
        if self.log_panel:
            self.log_panel.append(message)

    def _on_worker_idle_threadsafe(self) -> None:
        self.after(0, self._on_worker_idle)

    def _on_task_update(self, task: Task) -> None:
        self._refresh_queue()
        if task.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.SKIPPED,
            TaskStatus.CANCELLED,
        ):
            self.settings.add_history(
                file=task.file_name,
                status=task.status.value,
                duration=task.duration,
                message=task.progress or task.error,
            )
            save_settings(self.settings)

    def _on_worker_idle(self) -> None:
        self._append_log(t("queue_idle"))
        self._refresh_queue()

    def _refresh_queue(self) -> None:
        if self.queue_panel:
            self.queue_panel.sync_tasks(self.worker.tasks)

    def _on_close(self) -> None:
        self.settings.window_geometry = self.geometry()
        save_settings(self.settings)
        self.destroy()


def main() -> None:
    app = NszConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
