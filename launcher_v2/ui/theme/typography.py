# -*- coding: utf-8 -*-
"""
Typography loader and exact pixel-size helpers for Stella Sora Việt Hóa PC Launcher v2.0.

Loads all 4 Be Vietnam Pro OFL weights (400/500/600/700), applies NFC Unicode
normalization for Vietnamese diacritics, enables OpenType tabular numerals ('tnum')
on demand, and eliminates v1.3.4's '+2px' font size offset bug.
"""
from __future__ import annotations

import logging
import unicodedata
from enum import Enum
from pathlib import Path
from typing import Iterable

from PySide6.QtGui import QFont, QFontDatabase

logger = logging.getLogger(__name__)

PRIMARY_FONT_FAMILY = "Be Vietnam Pro"
FALLBACK_FONT_FAMILY = "Segoe UI"
MONO_FONT_FAMILIES = ["Cascadia Mono", "Consolas", "Courier New"]

FONT_FILES: tuple[str, ...] = (
    "BeVietnamPro-Regular.ttf",
    "BeVietnamPro-Medium.ttf",
    "BeVietnamPro-SemiBold.ttf",
    "BeVietnamPro-Bold.ttf",
)

# Canonical Preview r5 pixel scale (exact DIP pixel sizes)
FS_MICRO: float = 10.5
FS_CAPTION: float = 11.0
FS_META: float = 11.5
FS_BODY_SM: float = 12.0
FS_BODY: float = 12.5
FS_SUBTITLE: float = 13.0
FS_CTA_SM: float = 13.5
FS_CTA: float = 14.0
FS_MODAL_HERO: float = 16.0
FS_HEADER: float = 16.5
FS_DETAIL_TITLE: float = 18.0


class FontRole(str, Enum):
    MICRO = "micro"
    CAPTION = "caption"
    META = "meta"
    BODY_SM = "body_sm"
    BODY = "body"
    SUBTITLE = "subtitle"
    CTA_SM = "cta_sm"
    CTA = "cta"
    MODAL_HERO = "modal_hero"
    HEADER = "header"
    DETAIL_TITLE = "detail_title"
    MONO = "mono"


_ROLE_PIXEL_SIZES: dict[FontRole, float] = {
    FontRole.MICRO: FS_MICRO,
    FontRole.CAPTION: FS_CAPTION,
    FontRole.META: FS_META,
    FontRole.BODY_SM: FS_BODY_SM,
    FontRole.BODY: FS_BODY,
    FontRole.SUBTITLE: FS_SUBTITLE,
    FontRole.CTA_SM: FS_CTA_SM,
    FontRole.CTA: FS_CTA,
    FontRole.MODAL_HERO: FS_MODAL_HERO,
    FontRole.HEADER: FS_HEADER,
    FontRole.DETAIL_TITLE: FS_DETAIL_TITLE,
    FontRole.MONO: FS_META,
}

_LOADED_FAMILIES: list[str] = []


def nfc(text: str | None) -> str:
    """Normalize Vietnamese UI text to Unicode NFC form."""
    if not text:
        return ""
    return unicodedata.normalize("NFC", str(text))


def _default_resource_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "resources"


def register_fonts(resource_dir: Path | str | None = None) -> list[str]:
    """Load Be Vietnam Pro weights 400/500/600/700 into QFontDatabase.

    Returns the list of registered Qt font family names (or fallback info).
    Non-fatal when a font file is missing: logs warning and falls back to Segoe UI.
    """
    global _LOADED_FAMILIES
    base = Path(resource_dir) if resource_dir is not None else _default_resource_dir()
    fonts_dir = base / "fonts"
    loaded: list[str] = []

    for filename in FONT_FILES:
        path = fonts_dir / filename
        if not path.is_file():
            logger.warning("Missing bundled font file: %s", path)
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id < 0:
            logger.warning("Failed to register font with QFontDatabase: %s", path)
            continue
        for fam in QFontDatabase.applicationFontFamilies(font_id):
            if fam not in loaded:
                loaded.append(fam)

    if loaded:
        _LOADED_FAMILIES = loaded
    else:
        # Check if system/prior registration already made PRIMARY_FONT_FAMILY available
        if PRIMARY_FONT_FAMILY in QFontDatabase.families():
            _LOADED_FAMILIES = [PRIMARY_FONT_FAMILY]
        else:
            logger.warning("Falling back to %s (Be Vietnam Pro unavailable)", FALLBACK_FONT_FAMILY)
            _LOADED_FAMILIES = []
    return list(_LOADED_FAMILIES)


def active_ui_family() -> str:
    """Return the active primary UI font family name."""
    if PRIMARY_FONT_FAMILY in _LOADED_FAMILIES:
        return PRIMARY_FONT_FAMILY
    if PRIMARY_FONT_FAMILY in QFontDatabase.families():
        return PRIMARY_FONT_FAMILY
    return FALLBACK_FONT_FAMILY


def _map_qfont_weight(weight: int) -> QFont.Weight:
    if weight <= 400:
        return QFont.Weight.Normal
    if weight <= 500:
        return QFont.Weight.Medium
    if weight <= 600:
        return QFont.Weight.DemiBold
    return QFont.Weight.Bold


def _apply_tabular_numerals(font: QFont) -> None:
    try:
        font.setFeature(QFont.Tag("tnum"), 1)
    except Exception:  # noqa: BLE001
        pass


def ui_font(px: float, weight: int = 400, *, tabular: bool = False) -> QFont:
    """Create a crisp QFont with exact pixelSize (NO +2px offset hack)."""
    family = active_ui_family()
    font = QFont()
    font.setFamilies([family, FALLBACK_FONT_FAMILY])
    font.setPixelSize(max(1, round(float(px))))
    font.setWeight(_map_qfont_weight(int(weight)))
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setStyleStrategy(
        QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality
    )
    if tabular:
        _apply_tabular_numerals(font)
    return font


def mono_font(px: float = FS_META, weight: int = 400, *, tabular: bool = True) -> QFont:
    """Create a monospace QFont for paths, SHA256s, error codes, and numeric metrics."""
    font = QFont()
    font.setFamilies(list(MONO_FONT_FAMILIES))
    font.setPixelSize(max(1, round(float(px))))
    font.setWeight(_map_qfont_weight(int(weight)))
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setStyleStrategy(
        QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality
    )
    if tabular:
        _apply_tabular_numerals(font)
    return font


def role_font(
    role: FontRole,
    *,
    weight: int | None = None,
    tabular: bool = False,
) -> QFont:
    """Create a QFont directly from a canonical FontRole."""
    px = _ROLE_PIXEL_SIZES[role]
    if role is FontRole.MONO:
        return mono_font(px, weight=400 if weight is None else weight, tabular=True)
    default_weight = {
        FontRole.HEADER: 700,
        FontRole.DETAIL_TITLE: 700,
        FontRole.MODAL_HERO: 700,
        FontRole.CTA: 700,
        FontRole.CTA_SM: 700,
        FontRole.SUBTITLE: 600,
        FontRole.BODY: 400,
        FontRole.BODY_SM: 400,
        FontRole.META: 500,
        FontRole.CAPTION: 500,
        FontRole.MICRO: 500,
    }.get(role, 400)
    return ui_font(px, default_weight if weight is None else weight, tabular=tabular)


def loaded_font_families() -> list[str]:
    """Return a copy of currently loaded application font families."""
    return list(_LOADED_FAMILIES)
