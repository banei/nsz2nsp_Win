from __future__ import annotations

import pytest

from nsz_converter.i18n import (
    SUPPORTED_LANGUAGES,
    detect_system_language,
    init_language,
    resolve_language,
    set_language,
    t,
)


def test_supported_languages_include_mainstream() -> None:
    expected = {"en", "zh_CN", "zh_TW", "ja", "ko", "fr", "de", "es", "pt", "ru", "it"}
    assert expected.issubset(set(SUPPORTED_LANGUAGES))


def test_init_language_uses_system_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("nsz_converter.i18n.detect_system_language", lambda: "ja")
    assert init_language("") == "ja"
    assert t("settings") == "設定"


def test_set_language_switches_strings() -> None:
    init_language("en")
    assert t("start") == "Start"
    set_language("zh_CN")
    assert t("start") == "开始"


def test_resolve_language_prefers_stored() -> None:
    assert resolve_language("fr") == "fr"
    assert resolve_language("unknown") != "unknown"


def test_format_interpolation() -> None:
    init_language("en")
    assert t("queue_count", count=3) == "3 items"
