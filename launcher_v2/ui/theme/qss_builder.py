# -*- coding: utf-8 -*-
"""
Clean flat QSS generator from Preview r5 Porcelain & Overview tokens.

Zero silent hex rewriting, zero global forced dark-blue text color, and zero
nested rounded card borders on lists/tables.
"""
from __future__ import annotations

from pathlib import Path

from .tokens import PORCELAIN_TOKENS
from .typography import active_ui_family


def build_porcelain_qss(
    *,
    checkbox_icon_path: Path | str | None = None,
) -> str:
    """Generate clean flat QSS for Light Porcelain inputs, menus, scrollbars, and tooltips."""
    p = PORCELAIN_TOKENS
    ui_fam = active_ui_family()

    if checkbox_icon_path is not None:
        icon_url = Path(checkbox_icon_path).resolve().as_posix()
        checked_rule = (
            f"background: {p.NAVY_SOLID}; "
            f"border-color: {p.NAVY_SOLID}; "
            f'image: url("{icon_url}");'
        )
    else:
        checked_rule = (
            f"background: {p.NAVY_SOLID}; "
            f"border-color: {p.NAVY_SOLID};"
        )

    return f"""
QWidget {{
    font-family: "{ui_fam}", "Segoe UI";
    outline: none;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 2px 0 2px 0;
}}
QScrollBar::handle:vertical {{
    background: {p.HAIRLINE_INPUT};
    min-height: 28px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: #8FA6C4;
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    height: 0px;
    background: transparent;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0 2px 0 2px;
}}
QScrollBar::handle:horizontal {{
    background: {p.HAIRLINE_INPUT};
    min-width: 28px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #8FA6C4;
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    width: 0px;
    background: transparent;
}}

QToolTip {{
    background-color: {p.WHITE};
    color: {p.NAVY_TEXT};
    border: 1px solid {p.HAIRLINE_INPUT};
    border-radius: 4px;
    padding: 5px 9px;
    font-size: 12px;
}}

QLineEdit#porcelainInput,
QLineEdit#porcelainSearch {{
    background-color: {p.WHITE};
    color: {p.NAVY_TEXT};
    border: 1px solid {p.HAIRLINE_INPUT};
    border-radius: 4px;
    padding: 4px 10px;
    selection-background-color: {p.ICE_SELECTED};
    selection-color: {p.NAVY_TEXT};
}}
QLineEdit#porcelainInput:focus,
QLineEdit#porcelainSearch:focus {{
    border: 1px solid {p.CYAN_ACCENT};
}}
QLineEdit#porcelainInput:read-only {{
    background-color: {p.ICE_ROW_ALT};
    color: {p.SLATE_BODY};
}}
QLineEdit#porcelainInput:disabled {{
    background-color: {p.ICE_ZEBRA};
    color: {p.SLATE_MUTED};
}}

QPlainTextEdit#porcelainNotes {{
    background-color: {p.WHITE};
    color: {p.SLATE_BODY};
    border: 1px solid {p.HAIRLINE};
    border-radius: 4px;
    padding: 8px 10px;
    selection-background-color: {p.ICE_SELECTED};
    selection-color: {p.NAVY_TEXT};
}}

QMenu#porcelainMenu {{
    background-color: {p.WHITE};
    color: {p.NAVY_TEXT};
    border: 1px solid {p.HAIRLINE_STRONG};
    padding: 4px 0px;
}}
QMenu#porcelainMenu::item {{
    padding: 7px 16px;
    background: transparent;
}}
QMenu#porcelainMenu::item:selected {{
    background-color: {p.ICE_HOVER};
    color: {p.NAVY_TEXT};
}}
QMenu#porcelainMenu::separator {{
    height: 1px;
    background: {p.HAIRLINE};
    margin: 4px 8px;
}}

QCheckBox#porcelainCheck {{
    spacing: 8px;
    color: {p.NAVY_TEXT};
}}
QCheckBox#porcelainCheck:disabled {{
    color: {p.SLATE_MUTED};
}}
QCheckBox#porcelainCheck::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #94A3B8;
    border-radius: 3px;
    background-color: {p.WHITE};
}}
QCheckBox#porcelainCheck::indicator:hover {{
    border-color: {p.NAVY_SOLID};
}}
QCheckBox#porcelainCheck::indicator:checked {{
    {checked_rule}
}}
QCheckBox#porcelainCheck::indicator:disabled {{
    background-color: {p.ICE_ZEBRA};
    border-color: {p.HAIRLINE_STRONG};
}}
"""


def build_application_qss(resource_dir: Path | str | None = None) -> str:
    """Build the application-wide flat QSS stylesheet."""
    checkbox_path: Path | None = None
    if resource_dir is not None:
        candidate = Path(resource_dir) / "game" / "asar_checkbox.svg"
        if candidate.is_file():
            checkbox_path = candidate
    else:
        candidate = Path(__file__).resolve().parents[2] / "resources" / "game" / "asar_checkbox.svg"
        if candidate.is_file():
            checkbox_path = candidate
    return build_porcelain_qss(checkbox_icon_path=checkbox_path)
