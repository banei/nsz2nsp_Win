from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class KeysetInfo:
    path: str
    home_override: str


def resolve_keyset(base_dir: str, configured_path: str = "") -> Optional[KeysetInfo]:
    candidates: list[str] = []
    if configured_path:
        candidates.append(os.path.expanduser(configured_path))
    env_path = os.environ.get("NSZ_KEYSET")
    if env_path:
        candidates.append(os.path.expanduser(env_path))
    candidates.extend(
        [
            os.path.expanduser("~/.switch/prod.keys"),
            os.path.join(os.getcwd(), ".switch", "prod.keys"),
            os.path.join(base_dir, "keys.txt"),
            os.path.join(os.getcwd(), "keys.txt"),
        ]
    )
    for path in candidates:
        if path and os.path.exists(path):
            return _prepare_keyset(path)
    return None


def _prepare_keyset(keyset: str) -> KeysetInfo:
    normalized = keyset.replace("\\", "/")
    if normalized.endswith("/.switch/prod.keys"):
        home_override = os.path.dirname(os.path.dirname(keyset))
        return KeysetInfo(path=keyset, home_override=home_override)

    home_override = os.getcwd()
    switch_dir = os.path.join(home_override, ".switch")
    os.makedirs(switch_dir, exist_ok=True)
    dest = os.path.join(switch_dir, "prod.keys")
    if os.path.abspath(keyset) != os.path.abspath(dest):
        shutil.copyfile(keyset, dest)
    return KeysetInfo(path=keyset, home_override=home_override)
