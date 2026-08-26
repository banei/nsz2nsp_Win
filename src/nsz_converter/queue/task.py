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


def status_label_for(task_status: TaskStatus) -> str:
    from nsz_converter.i18n import status_label

    return status_label(task_status.value)


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
