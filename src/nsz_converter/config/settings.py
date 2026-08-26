from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def get_config_dir() -> str:
    if os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        path = os.path.join(base, "nsz-converter")
    else:
        path = os.path.join(os.path.expanduser("~"), ".config", "nsz-converter")
    os.makedirs(path, exist_ok=True)
    return path


def _config_path() -> str:
    return os.path.join(get_config_dir(), "config.json")


@dataclass
class HistoryEntry:
    file: str
    status: str
    time: str
    duration: float = 0.0
    message: str = ""


@dataclass
class AppSettings:
    keyset_path: str = ""
    window_geometry: str = "960x720"
    show_native_progress: bool = False
    max_history: int = 50
    history: list[HistoryEntry] = field(default_factory=list)

    def add_history(self, file: str, status: str, duration: float = 0.0, message: str = "") -> None:
        entry = HistoryEntry(
            file=file,
            status=status,
            time=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            duration=duration,
            message=message,
        )
        self.history.insert(0, entry)
        if len(self.history) > self.max_history:
            self.history = self.history[: self.max_history]


def _history_from_dict(data: dict[str, Any]) -> HistoryEntry:
    return HistoryEntry(
        file=data.get("file", ""),
        status=data.get("status", ""),
        time=data.get("time", ""),
        duration=float(data.get("duration", 0.0)),
        message=data.get("message", ""),
    )


def load_settings() -> AppSettings:
    path = _config_path()
    if not os.path.exists(path):
        return AppSettings()
    try:
        with open(path, encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return AppSettings()

    history = [_history_from_dict(item) for item in raw.get("history", [])]
    return AppSettings(
        keyset_path=raw.get("keyset_path", ""),
        window_geometry=raw.get("window_geometry", "960x720"),
        show_native_progress=bool(raw.get("show_native_progress", False)),
        max_history=int(raw.get("max_history", 50)),
        history=history,
    )


def save_settings(settings: AppSettings) -> None:
    payload = {
        "keyset_path": settings.keyset_path,
        "window_geometry": settings.window_geometry,
        "show_native_progress": settings.show_native_progress,
        "max_history": settings.max_history,
        "history": [asdict(item) for item in settings.history],
    }
    with open(_config_path(), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
