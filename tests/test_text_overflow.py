from nsz_converter.i18n import SUPPORTED_LANGUAGES, init_language, t
from nsz_converter.queue.task import TaskStatus, status_label_for
from nsz_converter.ui.theme import (
    BTN_PAD_COMPACT,
    BTN_PAD_NORMAL,
    COL_FILENAME,
    COL_PROGRESS,
    COL_STATUS,
    FONT_SIZE,
    FONT_SIZE_SM,
    btn_width,
    fit_label_text,
    text_width,
    truncate_text,
)

BUTTON_KEYS: list[tuple[str, bool]] = [
    ("settings", False),
    ("start", False),
    ("pause", False),
    ("resume", False),
    ("cancel_current", False),
    ("clear_queue", False),
    ("clear_completed", False),
    ("pick_folder", False),
    ("pick_files", False),
    ("copy", True),
    ("clear", True),
    ("browse", True),
    ("save", False),
    ("cancel", False),
    ("retry", True),
]

STATUS_ICONS = {
    TaskStatus.COMPLETED: "✓",
    TaskStatus.RUNNING: "▶",
    TaskStatus.PENDING: "○",
    TaskStatus.FAILED: "✗",
    TaskStatus.SKIPPED: "−",
    TaskStatus.CANCELLED: "⊘",
}


def test_all_buttons_have_enough_width() -> None:
    for lang in SUPPORTED_LANGUAGES:
        init_language(lang)
        for key, compact in BUTTON_KEYS:
            text = t(key)
            size = FONT_SIZE_SM if compact else FONT_SIZE
            padding = BTN_PAD_COMPACT if compact else BTN_PAD_NORMAL
            required = text_width(text, size) + padding
            assert btn_width(text, compact=compact) >= required, f"{lang}:{text}"


def test_button_height_covers_font() -> None:
    from nsz_converter.ui.theme import btn_height

    assert btn_height(compact=False) >= FONT_SIZE + 28
    assert btn_height(compact=True) >= FONT_SIZE_SM + 26


def test_button_text_fits_inside_frame() -> None:
    from nsz_converter.ui.theme import btn_height

    # Leave enough frame height for YaHei label metrics (ascent + descent + padding).
    assert btn_height(compact=False) >= FONT_SIZE + 24
    assert btn_height(compact=True) >= FONT_SIZE_SM + 22


def test_row_and_label_heights() -> None:
    from nsz_converter.ui.theme import LABEL_HEIGHT, ROW_HEIGHT

    assert ROW_HEIGHT >= LABEL_HEIGHT + 6


def test_all_status_labels_fit_column() -> None:
    for lang in SUPPORTED_LANGUAGES:
        init_language(lang)
        for status, icon in STATUS_ICONS.items():
            text = f"{icon} {status_label_for(status)}"
            fitted = fit_label_text(text, COL_STATUS, FONT_SIZE)
            assert text_width(fitted, FONT_SIZE) <= COL_STATUS - 8, f"{lang}:{text}"


def test_long_filename_truncates() -> None:
    long_name = "塞尔达传说王国之泪完整版超长文件名测试" + "x" * 20 + ".nsz"
    fitted = fit_label_text(long_name, COL_FILENAME, FONT_SIZE)
    assert fitted.endswith("…")
    assert text_width(fitted, FONT_SIZE) <= COL_FILENAME - 8


def test_long_progress_truncates() -> None:
    long_progress = "Decompress " + ("x" * 80) + " 99%"
    fitted = fit_label_text(long_progress, COL_PROGRESS, FONT_SIZE)
    assert fitted.endswith("…")
    assert text_width(fitted, FONT_SIZE) <= COL_PROGRESS - 8


def test_truncate_preserves_short_text() -> None:
    init_language("zh_CN")
    short = t("status_completed")
    assert truncate_text(short, 200, FONT_SIZE) == short
