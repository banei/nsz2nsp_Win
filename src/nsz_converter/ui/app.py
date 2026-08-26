from __future__ import annotations

import tkinter.messagebox as messagebox

import customtkinter as ctk
from tkinterdnd2 import TkinterDnD

from nsz_converter.config.settings import AppSettings, load_settings, save_settings
from nsz_converter.core.nsz_runner import is_nsz_available
from nsz_converter.queue.task import Task, TaskStatus
from nsz_converter.queue.worker import QueueWorker

from .components.drop_zone import DropZone
from .components.log_panel import LogPanel
from .components.queue_panel import QueuePanel
from .dialogs import SettingsDialog
from .theme import Palette, apply_theme, window_bg


class NszConverterApp(TkinterDnD.Tk):
    def __init__(self) -> None:
        super().__init__()
        apply_theme()
        self.configure(bg=window_bg())

        self.settings = load_settings()
        self.title("NSZ Converter")
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

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if not is_nsz_available():
            messagebox.showwarning(
                "缺少依赖",
                "未检测到 nsz 工具。\n\n请运行:\n  pip install nsz",
            )
            self.start_btn.configure(state="disabled")

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text="NSZ → NSP 转换工具",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=Palette.TEXT,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            top,
            text="设置",
            width=70,
            command=self._open_settings,
            fg_color=Palette.BTN_SECONDARY,
            hover_color=Palette.BTN_SECONDARY_HOVER,
            text_color=Palette.BTN_SECONDARY_TEXT,
        ).grid(row=0, column=1, sticky="e")

        self.drop_zone = DropZone(self, on_paths=self._add_paths, height=120)
        self.drop_zone.grid(row=1, column=0, sticky="ew", padx=16, pady=8)

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 4))
        self.start_btn = self._make_button(controls, "开始", self._start, primary=True)
        self.start_btn.pack(side="left", padx=4)
        self.pause_btn = self._make_button(controls, "暂停", self._toggle_pause)
        self.pause_btn.pack(side="left", padx=4)
        self.cancel_btn = self._make_button(controls, "取消当前", self._cancel_current)
        self.cancel_btn.pack(side="left", padx=4)
        self.clear_btn = self._make_button(controls, "清空队列", self._clear_queue)
        self.clear_btn.pack(side="left", padx=4)
        self.clear_done_btn = self._make_button(controls, "清除已完成", self._clear_completed)
        self.clear_done_btn.pack(side="left", padx=4)

        self.queue_panel = QueuePanel(self, on_retry=self._retry_task, fg_color=Palette.SURFACE)
        self.queue_panel.grid(row=3, column=0, sticky="nsew", padx=16, pady=8)

        self.log_panel = LogPanel(self, fg_color=Palette.SURFACE)
        self.log_panel.grid(row=4, column=0, sticky="nsew", padx=16, pady=(0, 16))

        self.log_panel.append("就绪。拖拽或选择 NSZ 文件开始。")

    @staticmethod
    def _make_button(parent, text: str, command, *, primary: bool = False) -> ctk.CTkButton:
        if primary:
            return ctk.CTkButton(
                parent,
                text=text,
                width=80,
                command=command,
                fg_color=Palette.BTN_PRIMARY,
                hover_color=Palette.BTN_PRIMARY_HOVER,
            )
        return ctk.CTkButton(
            parent,
            text=text,
            width=90,
            command=command,
            fg_color=Palette.BTN_SECONDARY,
            hover_color=Palette.BTN_SECONDARY_HOVER,
            text_color=Palette.BTN_SECONDARY_TEXT,
        )

    def _add_paths(self, paths: list[str]) -> None:
        self.worker.add_paths(paths)
        self._refresh_queue()
        self.worker.start()

    def _start(self) -> None:
        if self._paused:
            self._paused = False
            self.pause_btn.configure(text="暂停")
            self.worker.resume()
        else:
            self.worker.start()
        self._refresh_queue()

    def _toggle_pause(self) -> None:
        if self._paused:
            self._paused = False
            self.pause_btn.configure(text="暂停")
            self.worker.resume()
        else:
            self._paused = True
            self.pause_btn.configure(text="继续")
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
        SettingsDialog(self, self.settings, on_save=self._apply_settings)

    def _apply_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        self.worker.configure(
            configured_keyset=settings.keyset_path,
            show_native_progress=settings.show_native_progress,
        )
        save_settings(settings)
        self.log_panel.append("设置已保存")

    def _on_task_update_threadsafe(self, task: Task) -> None:
        self.after(0, lambda: self._on_task_update(task))

    def _on_log_threadsafe(self, message: str) -> None:
        self.after(0, lambda: self.log_panel.append(message))

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
        self.log_panel.append("队列处理完成")
        self._refresh_queue()

    def _refresh_queue(self) -> None:
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
