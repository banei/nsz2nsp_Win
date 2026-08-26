from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sysconfig
import threading
import time
from typing import Callable, Optional


def find_nsz_binary() -> Optional[str]:
    path_bin = shutil.which("nsz")

    def bad_interpreter(script_path: str) -> bool:
        try:
            if not script_path or not os.path.exists(script_path):
                return True
            with open(script_path, "rb") as handle:
                first = handle.readline().decode("utf-8", errors="ignore").strip()
            if first.startswith("#!"):
                interp = first[2:].split()[0]
                return not os.path.exists(interp)
            return False
        except OSError:
            return True

    if path_bin and not bad_interpreter(path_bin):
        return path_bin

    scripts_dir = sysconfig.get_path("scripts")
    if scripts_dir:
        candidate = os.path.join(scripts_dir, "nsz")
        if os.name == "nt":
            candidate = candidate + ".exe" if not candidate.endswith(".exe") else candidate
            alt = os.path.join(scripts_dir, "nsz.exe")
            for item in (candidate, alt, os.path.join(scripts_dir, "nsz")):
                if os.path.exists(item) and os.access(item, os.X_OK) and not bad_interpreter(item):
                    return item
        elif os.path.exists(candidate) and os.access(candidate, os.X_OK) and not bad_interpreter(candidate):
            return candidate

    if importlib.util.find_spec("nsz") is not None and path_bin:
        return path_bin
    return None


def is_nsz_available() -> bool:
    return find_nsz_binary() is not None or importlib.util.find_spec("nsz") is not None


ProgressCallback = Callable[[str], None]


class NszRunner:
    def __init__(
        self,
        nsz_path: str,
        home_override: str,
        show_native_progress: bool = False,
    ) -> None:
        self._nsz_path = nsz_path
        self._home_override = home_override
        self._show_native_progress = show_native_progress
        self._process: Optional[subprocess.Popen[str]] = None
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def run(
        self,
        nsz_file: str,
        on_progress: Optional[ProgressCallback] = None,
    ) -> tuple[int, float, str]:
        self._cancelled = False
        env = os.environ.copy()
        env["HOME"] = self._home_override
        cmd = [self._nsz_path, "-D", nsz_file]
        start = time.time()
        last_line = ""

        stop_timer = threading.Event()

        def tick() -> None:
            while not stop_timer.wait(1):
                pass

        timer = threading.Thread(target=tick, daemon=True)
        timer.start()

        try:
            if self._show_native_progress:
                self._process = subprocess.Popen(cmd, env=env)
                rc = self._process.wait()
            else:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                    text=True,
                    bufsize=1,
                )
                assert self._process.stdout is not None
                for line in self._process.stdout:
                    stripped = line.strip()
                    if stripped.startswith("Decompress"):
                        last_line = stripped
                        if on_progress:
                            on_progress(stripped)
                rc = self._process.wait()
        except (FileNotFoundError, OSError) as exc:
            stop_timer.set()
            from nsz_converter.i18n import t

            raise RuntimeError(t("err_nsz_start", error=exc)) from exc
        finally:
            stop_timer.set()
            self._process = None

        duration = time.time() - start
        if self._cancelled:
            return -1, duration, last_line
        return rc, duration, last_line
