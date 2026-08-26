from __future__ import annotations

import threading
from typing import Callable, Optional

from nsz_converter.core.converter import convert_file, discover_nsz_files
from nsz_converter.core.converter import ConversionStatus
from nsz_converter.core.nsz_runner import NszRunner, find_nsz_binary
from nsz_converter.core.keyset import resolve_keyset

from .task import Task, TaskStatus


TaskCallback = Callable[[Task], None]
LogCallback = Callable[[str], None]


class QueueWorker:
    def __init__(
        self,
        *,
        configured_keyset: str = "",
        show_native_progress: bool = False,
        on_task_update: Optional[TaskCallback] = None,
        on_log: Optional[LogCallback] = None,
        on_idle: Optional[Callable[[], None]] = None,
    ) -> None:
        self._configured_keyset = configured_keyset
        self._show_native_progress = show_native_progress
        self._on_task_update = on_task_update
        self._on_log = on_log
        self._on_idle = on_idle

        self._tasks: list[Task] = []
        self._lock = threading.Lock()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._current_runner: Optional[NszRunner] = None
        self._running = False
        self._cancel_current = False

    @property
    def tasks(self) -> list[Task]:
        with self._lock:
            return list(self._tasks)

    def configure(self, *, configured_keyset: str, show_native_progress: bool) -> None:
        self._configured_keyset = configured_keyset
        self._show_native_progress = show_native_progress

    def add_paths(self, paths: list[str]) -> list[Task]:
        files = discover_nsz_files(paths)
        new_tasks: list[Task] = []
        with self._lock:
            existing = {task.file_path for task in self._tasks}
            for file_path in files:
                if file_path in existing:
                    continue
                task = Task(file_path=file_path)
                self._tasks.append(task)
                new_tasks.append(task)
                self._emit(task)
        if new_tasks:
            self._log(f"已添加 {len(new_tasks)} 个文件到队列")
        elif paths:
            self._log("未找到 .nsz 文件")
        return new_tasks

    def retry_task(self, task_id: str) -> None:
        with self._lock:
            for task in self._tasks:
                if task.id == task_id and task.status in (TaskStatus.FAILED, TaskStatus.CANCELLED):
                    task.status = TaskStatus.PENDING
                    task.progress = ""
                    task.error = ""
                    task.retries += 1
                    self._emit(task)
                    self._log(f"重试: {task.file_name}")
                    break
        self._ensure_worker()

    def clear(self, *, completed_only: bool = False) -> None:
        with self._lock:
            if completed_only:
                self._tasks = [
                    task
                    for task in self._tasks
                    if task.status
                    in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.FAILED, TaskStatus.CANCELLED)
                ]
            else:
                self._tasks = [task for task in self._tasks if task.status == TaskStatus.RUNNING]
        self._log("队列已清空" if not completed_only else "已完成项已清除")

    def start(self) -> None:
        self._pause_event.set()
        self._ensure_worker()

    def pause(self) -> None:
        self._pause_event.clear()
        self._log("已暂停（当前文件完成后停止）")

    def resume(self) -> None:
        self._pause_event.set()
        self._ensure_worker()
        self._log("已继续")

    def cancel_current(self) -> None:
        self._cancel_current = True
        if self._current_runner:
            self._current_runner.cancel()
        self._log("正在取消当前转换…")

    def _ensure_worker(self) -> None:
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()

    def _run_loop(self) -> None:
        self._running = True
        try:
            while not self._stop_event.is_set():
                self._pause_event.wait()
                task = self._next_pending()
                if not task:
                    break
                self._process_task(task)
                if self._cancel_current:
                    self._cancel_current = False
                if not self._pause_event.is_set():
                    break
        finally:
            self._running = False
            if self._on_idle:
                self._on_idle()

    def _next_pending(self) -> Optional[Task]:
        with self._lock:
            for task in self._tasks:
                if task.status == TaskStatus.PENDING:
                    return task
        return None

    def _process_task(self, task: Task) -> None:
        task.status = TaskStatus.RUNNING
        task.progress = "准备中…"
        self._emit(task)
        self._log(f"开始转换: {task.file_name}")

        nsz_bin = find_nsz_binary()
        keyset = resolve_keyset(
            __import__("os").path.dirname(task.file_path),
            self._configured_keyset,
        )
        runner = None
        if nsz_bin and keyset:
            runner = NszRunner(
                nsz_bin,
                keyset.home_override,
                show_native_progress=self._show_native_progress,
            )
            self._current_runner = runner

        def on_progress(line: str) -> None:
            task.progress = line
            self._emit(task)

        result = convert_file(
            task.file_path,
            configured_keyset=self._configured_keyset,
            show_native_progress=self._show_native_progress,
            on_progress=on_progress,
            runner=runner,
        )

        self._current_runner = None
        task.duration = result.duration
        task.progress = result.message

        status_map = {
            ConversionStatus.COMPLETED: TaskStatus.COMPLETED,
            ConversionStatus.SKIPPED: TaskStatus.SKIPPED,
            ConversionStatus.FAILED: TaskStatus.FAILED,
            ConversionStatus.CANCELLED: TaskStatus.CANCELLED,
        }
        task.status = status_map[result.status]
        if result.status == ConversionStatus.FAILED:
            task.error = result.message
        self._emit(task)
        self._log(f"{task.file_name}: {result.message}")

    def _emit(self, task: Task) -> None:
        if self._on_task_update:
            self._on_task_update(task)

    def _log(self, message: str) -> None:
        if self._on_log:
            self._on_log(message)
