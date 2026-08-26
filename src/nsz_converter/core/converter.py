from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from nsz_converter.i18n import t

from .keyset import KeysetInfo, resolve_keyset
from .nsz_runner import NszRunner, find_nsz_binary, is_nsz_available


class ConversionStatus(Enum):
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ConversionResult:
    status: ConversionStatus
    message: str
    duration: float = 0.0
    nsz_path: str = ""
    nsp_path: str = ""


ProgressCallback = Callable[[str], None]


def _stash_root() -> str:
    root = os.path.join(os.getcwd(), "nsz_sources")
    os.makedirs(root, exist_ok=True)
    return root


def move_to_stash(src_path: str, base_dir: str) -> str:
    try:
        rel = os.path.relpath(src_path, base_dir)
        if rel.startswith(".."):
            rel = os.path.basename(src_path)
    except ValueError:
        rel = os.path.basename(src_path)
    dest = os.path.join(_stash_root(), rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    final_dest = dest
    if os.path.exists(dest):
        base, ext = os.path.splitext(dest)
        idx = 1
        final_dest = f"{base}.dup{idx}{ext}"
        while os.path.exists(final_dest):
            idx += 1
            final_dest = f"{base}.dup{idx}{ext}"
    shutil.move(src_path, final_dest)
    return final_dest


def discover_nsz_files(paths: list[str]) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for raw in paths:
        path = os.path.abspath(raw)
        if os.path.isfile(path) and path.lower().endswith(".nsz"):
            if path not in seen:
                seen.add(path)
                found.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for name in files:
                    if name.lower().endswith(".nsz"):
                        full = os.path.join(root, name)
                        if full not in seen:
                            seen.add(full)
                            found.append(full)
    return sorted(found)


def convert_file(
    nsz_path: str,
    *,
    configured_keyset: str = "",
    show_native_progress: bool = False,
    on_progress: Optional[ProgressCallback] = None,
    runner: Optional[NszRunner] = None,
) -> ConversionResult:
    from nsz_converter.i18n import t

    nsz_path = os.path.abspath(nsz_path)
    nsp_path = os.path.splitext(nsz_path)[0] + ".nsp"
    base_dir = os.path.dirname(nsz_path)

    if not is_nsz_available():
        return ConversionResult(
            status=ConversionStatus.FAILED,
            message=t("err_nsz_missing"),
            nsz_path=nsz_path,
            nsp_path=nsp_path,
        )

    keyset = resolve_keyset(base_dir, configured_keyset)
    if not keyset:
        return ConversionResult(
            status=ConversionStatus.FAILED,
            message=t("err_keyset_missing"),
            nsz_path=nsz_path,
            nsp_path=nsp_path,
        )

    if os.path.exists(nsp_path):
        stash = move_to_stash(nsz_path, base_dir)
        return ConversionResult(
            status=ConversionStatus.SKIPPED,
            message=t("msg_nsp_exists", stash=stash),
            nsz_path=nsz_path,
            nsp_path=nsp_path,
        )

    nsz_bin = find_nsz_binary()
    if not nsz_bin:
        return ConversionResult(
            status=ConversionStatus.FAILED,
            message=t("err_nsz_bin"),
            nsz_path=nsz_path,
            nsp_path=nsp_path,
        )

    active_runner = runner or NszRunner(
        nsz_bin,
        keyset.home_override,
        show_native_progress=show_native_progress,
    )

    try:
        rc, duration, _ = active_runner.run(nsz_path, on_progress=on_progress)
    except RuntimeError as exc:
        return ConversionResult(
            status=ConversionStatus.FAILED,
            message=str(exc),
            nsz_path=nsz_path,
            nsp_path=nsp_path,
        )

    if active_runner.cancelled:
        return ConversionResult(
            status=ConversionStatus.CANCELLED,
            message=t("msg_cancelled"),
            duration=duration,
            nsz_path=nsz_path,
            nsp_path=nsp_path,
        )

    if rc != 0:
        return ConversionResult(
            status=ConversionStatus.FAILED,
            message=t("err_nsz_rc", code=rc),
            duration=duration,
            nsz_path=nsz_path,
            nsp_path=nsp_path,
        )

    if not os.path.exists(nsp_path):
        return ConversionResult(
            status=ConversionStatus.FAILED,
            message=t("err_no_nsp_output"),
            duration=duration,
            nsz_path=nsz_path,
            nsp_path=nsp_path,
        )

    stash = move_to_stash(nsz_path, base_dir)
    return ConversionResult(
        status=ConversionStatus.COMPLETED,
        message=t("msg_completed", stash=stash),
        duration=duration,
        nsz_path=nsz_path,
        nsp_path=nsp_path,
    )
