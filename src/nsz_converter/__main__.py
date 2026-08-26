from __future__ import annotations

import argparse
import os
import sys

from nsz_converter.config.settings import load_settings, save_settings
from nsz_converter.core.converter import ConversionStatus, convert_file, discover_nsz_files
from nsz_converter.i18n import init_language, t


def _run_cli(directory: str, *, show_progress: bool = False) -> int:
    settings = load_settings()
    init_language(settings.language)
    if not os.path.isdir(directory):
        print(t("cli_invalid_dir", path=directory))
        return 1

    files = discover_nsz_files([directory])
    if not files:
        print(t("cli_no_files"))
        return 1

    failures = 0
    for nsz_path in files:
        print(t("cli_converting", name=os.path.basename(nsz_path)))

        def on_progress(line: str) -> None:
            print(line)

        result = convert_file(
            nsz_path,
            configured_keyset=settings.keyset_path,
            show_native_progress=show_progress,
            on_progress=on_progress,
        )
        print(result.message)
        settings.add_history(
            file=os.path.basename(nsz_path),
            status=result.status.value,
            duration=result.duration,
            message=result.message,
        )
        if result.status == ConversionStatus.FAILED:
            failures += 1

    save_settings(settings)
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> None:
    settings = load_settings()
    init_language(settings.language)

    parser = argparse.ArgumentParser(description=t("app_description"))
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("gui", help=t("cli_gui_help"))

    convert_parser = subparsers.add_parser("convert", help=t("cli_convert_help"))
    convert_parser.add_argument("directory", help=t("cli_directory_help"))
    convert_parser.add_argument(
        "--progress",
        action="store_true",
        help=t("cli_progress_help"),
    )

    args = parser.parse_args(argv)

    if args.command == "convert":
        raise SystemExit(_run_cli(args.directory, show_progress=args.progress))

    from nsz_converter.ui.app import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
