from __future__ import annotations

import os
from pathlib import Path

import pytest

from nsz_converter.core.keyset import resolve_keyset


def test_resolve_keyset_prefers_configured_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    key_file = tmp_path / "custom.keys"
    key_file.write_text("key=value", encoding="utf-8")
    monkeypatch.delenv("NSZ_KEYSET", raising=False)
    monkeypatch.chdir(tmp_path)

    info = resolve_keyset(str(tmp_path), configured_path=str(key_file))
    assert info is not None
    assert info.path == str(key_file)


def test_resolve_keyset_falls_back_to_keys_txt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    keys = tmp_path / "keys.txt"
    keys.write_text("key=value", encoding="utf-8")
    monkeypatch.delenv("NSZ_KEYSET", raising=False)
    monkeypatch.chdir(tmp_path)

    info = resolve_keyset(str(tmp_path))
    assert info is not None
    assert os.path.exists(info.path)


def test_resolve_keyset_returns_none_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    empty_home = tmp_path / "home"
    empty_home.mkdir()
    monkeypatch.delenv("NSZ_KEYSET", raising=False)
    monkeypatch.setenv("USERPROFILE" if os.name == "nt" else "HOME", str(empty_home))
    monkeypatch.chdir(tmp_path)

    assert resolve_keyset(str(tmp_path)) is None
