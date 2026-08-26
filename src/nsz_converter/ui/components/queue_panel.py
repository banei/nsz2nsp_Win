from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from nsz_converter.queue.task import STATUS_LABELS, Task, TaskStatus
from nsz_converter.ui.theme import Palette, pick


class QueuePanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_retry: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_retry = on_retry
        self._rows: dict[str, ctk.CTkFrame] = {}
        self._task_map: dict[str, Task] = {}

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            header,
            text="转换队列",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=Palette.TEXT,
        ).pack(side="left")
        self.count_label = ctk.CTkLabel(header, text="0 项", text_color=Palette.TEXT_MUTED)
        self.count_label.pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, height=220, fg_color=Palette.SURFACE_ALT)
        self.scroll.pack(fill="both", expand=True, padx=8, pady=8)

        col_header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        col_header.pack(fill="x", pady=(0, 4))
        for text, width in (("状态", 70), ("文件名", 220), ("进度", 260), ("用时", 70), ("", 60)):
            ctk.CTkLabel(
                col_header,
                text=text,
                width=width,
                anchor="w",
                text_color=Palette.TEXT_MUTED,
                font=ctk.CTkFont(size=12),
            ).pack(side="left", padx=2)

        self.empty_label = ctk.CTkLabel(
            self.scroll,
            text="队列为空，请添加文件",
            text_color=Palette.TEXT_MUTED,
        )
        self.empty_label.pack(pady=24)

    def sync_tasks(self, tasks: list[Task]) -> None:
        self.count_label.configure(text=f"{len(tasks)} 项")
        if not tasks:
            if not self.empty_label.winfo_ismapped():
                self.empty_label.pack(pady=24)
            for frame in self._rows.values():
                frame.destroy()
            self._rows.clear()
            self._task_map.clear()
            return

        if self.empty_label.winfo_ismapped():
            self.empty_label.pack_forget()

        seen = set()
        for task in tasks:
            seen.add(task.id)
            self._task_map[task.id] = task
            if task.id in self._rows:
                self._update_row(task)
            else:
                self._create_row(task)

        for task_id in list(self._rows):
            if task_id not in seen:
                self._rows[task_id].destroy()
                del self._rows[task_id]
                self._task_map.pop(task_id, None)

    def _row_color(self, task: Task) -> str:
        if task.status == TaskStatus.RUNNING:
            return pick(Palette.ROW_ACTIVE)
        return pick(Palette.ROW)

    def _status_color(self, task: Task) -> str:
        if task.status == TaskStatus.COMPLETED:
            return pick(Palette.STATUS_OK)
        if task.status == TaskStatus.RUNNING:
            return pick(Palette.STATUS_RUN)
        if task.status == TaskStatus.FAILED:
            return pick(Palette.STATUS_FAIL)
        return pick(Palette.STATUS_WAIT)

    def _create_row(self, task: Task) -> None:
        row = ctk.CTkFrame(self.scroll, fg_color=self._row_color(task), corner_radius=6)
        row.pack(fill="x", pady=2)

        status_label = ctk.CTkLabel(
            row,
            text=self._status_text(task),
            width=70,
            anchor="w",
            text_color=self._status_color(task),
        )
        status_label.pack(side="left", padx=4)

        name_label = ctk.CTkLabel(
            row,
            text=task.file_name,
            width=220,
            anchor="w",
            text_color=Palette.TEXT,
        )
        name_label.pack(side="left", padx=4)

        progress_label = ctk.CTkLabel(
            row,
            text=self._progress_text(task),
            width=260,
            anchor="w",
            text_color=Palette.TEXT_MUTED,
        )
        progress_label.pack(side="left", padx=4)

        duration_label = ctk.CTkLabel(
            row,
            text=self._duration_text(task),
            width=70,
            anchor="w",
            text_color=Palette.TEXT_MUTED,
        )
        duration_label.pack(side="left", padx=4)

        action_frame = ctk.CTkFrame(row, fg_color="transparent", width=60)
        action_frame.pack(side="left", padx=4)
        retry_btn = ctk.CTkButton(
            action_frame,
            text="重试",
            width=50,
            height=24,
            command=lambda tid=task.id: self._on_retry(tid),
            fg_color=Palette.BTN_SECONDARY,
            hover_color=Palette.BTN_SECONDARY_HOVER,
            text_color=Palette.BTN_SECONDARY_TEXT,
        )
        if task.status in (TaskStatus.FAILED, TaskStatus.CANCELLED):
            retry_btn.pack()
        else:
            retry_btn.pack_forget()

        row._widgets = {
            "status": status_label,
            "progress": progress_label,
            "duration": duration_label,
            "retry": retry_btn,
        }
        self._rows[task.id] = row

    def _update_row(self, task: Task) -> None:
        row = self._rows.get(task.id)
        if not row:
            self._create_row(task)
            return
        row.configure(fg_color=self._row_color(task))
        widgets = row._widgets
        widgets["status"].configure(text=self._status_text(task), text_color=self._status_color(task))
        widgets["progress"].configure(text=self._progress_text(task))
        widgets["duration"].configure(text=self._duration_text(task))
        retry_btn = widgets["retry"]
        if task.status in (TaskStatus.FAILED, TaskStatus.CANCELLED):
            if not retry_btn.winfo_ismapped():
                retry_btn.pack()
        elif retry_btn.winfo_ismapped():
            retry_btn.pack_forget()

    @staticmethod
    def _status_text(task: Task) -> str:
        icons = {
            TaskStatus.COMPLETED: "✓",
            TaskStatus.RUNNING: "▶",
            TaskStatus.PENDING: "○",
            TaskStatus.FAILED: "✗",
            TaskStatus.SKIPPED: "−",
            TaskStatus.CANCELLED: "⊘",
        }
        return f"{icons.get(task.status, '?')} {STATUS_LABELS.get(task.status, task.status.value)}"

    @staticmethod
    def _progress_text(task: Task) -> str:
        if task.status == TaskStatus.RUNNING and task.progress:
            return task.progress
        if task.error:
            return task.error
        if task.progress:
            return task.progress
        return "—"

    @staticmethod
    def _duration_text(task: Task) -> str:
        if task.duration <= 0:
            return "—"
        return f"{task.duration:.1f}s"
