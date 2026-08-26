from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from nsz_converter.i18n import t
from nsz_converter.queue.task import Task, TaskStatus, status_label_for
from nsz_converter.ui.theme import (
    COL_ACTION,
    COL_DURATION,
    COL_FILENAME,
    COL_PROGRESS,
    COL_STATUS,
    FONT_SIZE,
    LABEL_HEIGHT,
    FixedCTkLabel,
    Palette,
    ROW_HEIGHT,
    create_button,
    create_fixed_label,
    label_font,
    pick,
    update_fixed_label,
)


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
        self._col_headers: list[ctk.CTkLabel] = []

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 4))

        self.title_label = ctk.CTkLabel(
            header,
            text=t("queue_title"),
            font=label_font(14, bold=True),
            text_color=Palette.TEXT,
        )
        self.title_label.pack(side="left")
        self.count_label = ctk.CTkLabel(
            header,
            text=t("queue_count", count=0),
            text_color=Palette.TEXT_MUTED,
            font=label_font(FONT_SIZE),
        )
        self.count_label.pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self, height=220, fg_color=Palette.SURFACE_ALT)
        self.scroll.pack(fill="both", expand=True, padx=8, pady=8)

        self.col_header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.col_header.pack(fill="x", pady=(0, 4))
        for key, width in (
            ("col_status", COL_STATUS),
            ("col_filename", COL_FILENAME),
            ("col_progress", COL_PROGRESS),
            ("col_duration", COL_DURATION),
            (None, COL_ACTION),
        ):
            label = FixedCTkLabel(
                self.col_header,
                text=t(key) if key else "",
                width=width,
                height=LABEL_HEIGHT,
                anchor="w",
                text_color=Palette.TEXT_MUTED,
                font=label_font(FONT_SIZE),
                fg_color="transparent",
            )
            label.pack(side="left", padx=2)
            if key:
                self._col_headers.append(label)

        self.empty_label = ctk.CTkLabel(
            self.scroll,
            text=t("queue_empty"),
            text_color=Palette.TEXT_MUTED,
            font=label_font(FONT_SIZE),
        )
        self.empty_label.pack(pady=24)

    def refresh_text(self) -> None:
        self.title_label.configure(text=t("queue_title"))
        self.empty_label.configure(text=t("queue_empty"))
        keys = ("col_status", "col_filename", "col_progress", "col_duration")
        for label, key in zip(self._col_headers, keys):
            label.configure(text=t(key))
        self.sync_tasks(list(self._task_map.values()))

    def sync_tasks(self, tasks: list[Task]) -> None:
        self.count_label.configure(text=t("queue_count", count=len(tasks)))
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
        row = ctk.CTkFrame(
            self.scroll,
            fg_color=self._row_color(task),
            corner_radius=6,
            height=ROW_HEIGHT,
        )
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent", height=ROW_HEIGHT)
        inner.pack(fill="both", expand=True, padx=2, pady=2)
        inner.pack_propagate(False)

        status_label = create_fixed_label(
            inner,
            self._status_text(task),
            COL_STATUS,
            size=FONT_SIZE,
            text_color=self._status_color(task),
        )
        status_label.pack(side="left", padx=2)

        name_label = create_fixed_label(inner, task.file_name, COL_FILENAME, size=FONT_SIZE)
        name_label.pack(side="left", padx=2)

        progress_label = create_fixed_label(
            inner,
            self._progress_text(task),
            COL_PROGRESS,
            size=FONT_SIZE,
            text_color=Palette.TEXT_MUTED,
        )
        progress_label.pack(side="left", padx=2)

        duration_label = create_fixed_label(
            inner,
            self._duration_text(task),
            COL_DURATION,
            size=FONT_SIZE,
            text_color=Palette.TEXT_MUTED,
        )
        duration_label.pack(side="left", padx=2)

        action_frame = ctk.CTkFrame(inner, fg_color="transparent", width=COL_ACTION, height=LABEL_HEIGHT)
        action_frame.pack(side="left", padx=2)
        action_frame.pack_propagate(False)
        retry_btn = create_button(
            action_frame,
            t("retry"),
            lambda tid=task.id: self._on_retry(tid),
            compact=True,
        )
        if task.status in (TaskStatus.FAILED, TaskStatus.CANCELLED):
            retry_btn.place(relx=0.5, rely=0.5, anchor="center")
        else:
            retry_btn.place_forget()

        row._widgets = {
            "status": status_label,
            "name": name_label,
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
        update_fixed_label(
            widgets["status"],
            self._status_text(task),
            COL_STATUS,
            size=FONT_SIZE,
        )
        widgets["status"].configure(text_color=self._status_color(task))
        update_fixed_label(widgets["name"], task.file_name, COL_FILENAME, size=FONT_SIZE)
        update_fixed_label(
            widgets["progress"],
            self._progress_text(task),
            COL_PROGRESS,
            size=FONT_SIZE,
        )
        update_fixed_label(widgets["duration"], self._duration_text(task), COL_DURATION, size=FONT_SIZE)
        retry_btn = widgets["retry"]
        retry_btn.configure(text=t("retry"))
        if task.status in (TaskStatus.FAILED, TaskStatus.CANCELLED):
            retry_btn.place(relx=0.5, rely=0.5, anchor="center")
        else:
            retry_btn.place_forget()

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
        return f"{icons.get(task.status, '?')} {status_label_for(task.status)}"

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
