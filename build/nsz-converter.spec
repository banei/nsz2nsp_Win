# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH).parent
src = root / "src"

ctk_datas, ctk_binaries, ctk_hidden = collect_all("customtkinter")
dnd_datas, dnd_binaries, dnd_hidden = collect_all("tkinterdnd2")

theme_file = src / "nsz_converter" / "ui" / "assets" / "soft_theme.json"
extra_datas = [(str(theme_file), "nsz_converter/ui/assets")]

a = Analysis(
    [str(src / "nsz_converter" / "launcher.py")],
    pathex=[str(src)],
    binaries=ctk_binaries + dnd_binaries,
    datas=ctk_datas + dnd_datas + extra_datas,
    hiddenimports=[
        "customtkinter",
        "tkinterdnd2",
        "nsz_converter",
        "nsz_converter.ui.app",
        "nsz_converter.ui.theme",
        "nsz_converter.ui.dialogs",
        "nsz_converter.ui.components.drop_zone",
        "nsz_converter.ui.components.queue_panel",
        "nsz_converter.ui.components.log_panel",
        "nsz_converter.core.converter",
        "nsz_converter.core.keyset",
        "nsz_converter.core.nsz_runner",
        "nsz_converter.queue.worker",
        "nsz_converter.queue.task",
        "nsz_converter.config.settings",
        *ctk_hidden,
        *dnd_hidden,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="NSZ-Converter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
