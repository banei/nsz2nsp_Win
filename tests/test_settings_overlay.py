from __future__ import annotations

import tkinter as tk

import pytest

from nsz_converter.config.settings import AppSettings
from nsz_converter.i18n import init_language, t
from nsz_converter.ui.app import NszConverterApp


def _grab_holder(root: tk.Misc) -> str | None:
    current = root.grab_current()
    return str(current) if current else None


@pytest.fixture(scope="module")
def app():
    application = NszConverterApp()
    application.update_idletasks()
    yield application
    try:
        application.destroy()
    except tk.TclError:
        pass


def test_language_selector_on_main_page(app: NszConverterApp) -> None:
    assert app.lang_selector is not None
    assert app.lang_selector.winfo_ismapped()


def test_language_change_reloads_ui(app: NszConverterApp) -> None:
    init_language("en")
    app.settings.language = "en"
    app._reload_ui(log_lines=["test log"])
    app.update_idletasks()

    assert t("start") == "Start"
    assert str(app.start_btn.cget("text")) == "Start"

    app.lang_selector._handle_change(app.lang_selector._lang_var.get())
    app.settings.language = "zh_CN"
    app._on_language_changed("zh_CN")
    app.update_idletasks()

    init_language("zh_CN")
    assert str(app.start_btn.cget("text")) == "开始"
    log_text = app.log_panel.text.get("1.0", "end")
    assert "test log" in log_text


def test_settings_open_and_cancel_restores_main_window(app: NszConverterApp) -> None:
    assert not app.settings_overlay.winfo_ismapped()

    app._open_settings()
    app.update_idletasks()
    assert app.settings_overlay.winfo_ismapped()
    assert _grab_holder(app) is None

    app.settings_overlay.hide()
    app.update_idletasks()

    assert not app.settings_overlay.winfo_ismapped()
    assert _grab_holder(app) is None
    assert str(app.start_btn.cget("state")) == "normal"
    assert str(app.focus_displayof()) != ""


def test_settings_save_closes_overlay(app: NszConverterApp) -> None:
    app._open_settings()
    app.update_idletasks()
    app.settings_overlay._save()
    app.update_idletasks()

    assert not app.settings_overlay.winfo_ismapped()
    assert _grab_holder(app) is None


def test_main_content_stays_visible_after_cancel(app: NszConverterApp) -> None:
    app._open_settings()
    app.update_idletasks()
    app.settings_overlay.hide()
    app.update_idletasks()

    assert app.drop_zone.winfo_ismapped()
    assert app.queue_panel.winfo_ismapped()
    assert app.log_panel.winfo_ismapped()
