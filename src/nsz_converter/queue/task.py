from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


STATUS_LABELS = {
    TaskStatus.PENDING: "等待",
    TaskStatus.RUNNING: "转换中",
    TaskStatus.COMPLETED: "完成",
    TaskStatus.FAILED: "失败",
    TaskStatus.SKIPPED: "跳过",
    TaskStatus.CANCELLED: "已取消",
}


@dataclass
class Task:
    file_path: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    status: TaskStatus = TaskStatus.PENDING
    progress: str = ""
    duration: float = 0.0
    error: str = ""
    retries: int = 0

    @property
    def file_name(self) -> str:
        import os

        return os.path.basename(self.file_path)
