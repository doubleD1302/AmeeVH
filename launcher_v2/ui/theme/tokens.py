# -*- coding: utf-8 -*-
"""
Preview r5 semantic design tokens for Stella Sora Việt Hóa PC Launcher v2.0.

Separates Overview Dark Translucent HUD tokens from Light Porcelain + Navy Header
subscreen/modal tokens (eliminating v1.3.4's contradictory TEXT_WHITE=#304679).
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor


def rgba_qcolor(rgba: tuple[int, int, int, int]) -> QColor:
    """Convert an (R, G, B, A) 0..255 tuple into a QColor."""
    r, g, b, a = rgba
    return QColor(int(r), int(g), int(b), int(a))


def rgba_css(rgba: tuple[int, int, int, int]) -> str:
    """Convert an (R, G, B, A) 0..255 tuple into a QSS rgba(...) string."""
    r, g, b, a = rgba
    return f"rgba({int(r)}, {int(g)}, {int(b)}, {a / 255.0:.3f})"


@dataclass(frozen=True)
class OverviewTokens:
    """Overview dark translucent chrome, dock, and HUD tokens."""

    WINDOW_BG: str = "#081224"
    WINDOW_BORDER: str = "rgba(255, 255, 255, 0.18)"
    WINDOW_BORDER_RGBA: tuple[int, int, int, int] = (255, 255, 255, 46)
    WINDOW_RADIUS: int = 8

    TEXT_PRIMARY: str = "#F8FAFC"
    TEXT_SECONDARY: str = "#CBD5E1"
    TEXT_MUTED: str = "#94A3B8"
    TEXT_NOTICE_ROW: str = "#F1F5F9"

    CHROME_LIGHT: tuple[int, int, int, int] = (11, 22, 44, 219)
    CHROME_DARK: tuple[int, int, int, int] = (10, 19, 38, 199)
    NAV_LIGHT: tuple[int, int, int, int] = (11, 22, 44, 184)
    NAV_DARK: tuple[int, int, int, int] = (10, 19, 38, 168)
    PANEL_LIGHT: tuple[int, int, int, int] = (12, 24, 46, 204)
    PANEL_DARK: tuple[int, int, int, int] = (12, 24, 46, 194)
    DOCK_LIGHT: tuple[int, int, int, int] = (12, 24, 46, 219)
    DOCK_DARK: tuple[int, int, int, int] = (12, 24, 46, 214)

    CYAN_ACCENT: str = "#25C8CE"
    CYAN_BADGE_BG: str = "#12B8C4"
    CYAN_BADGE_TEXT: str = "#082032"
    CTA_CYAN_TEXT: str = "#0B253A"
    CTA_ICE_TEXT: str = "#1E3254"

    LINK_SKY: str = "#7DD3FC"
    LINK_SKY_HOVER: str = "#BAE6FD"
    CAT_SKY: str = "#38BDF8"
    PLATFORM_TAG_BG: str = "#1E3A6E"

    OK_GREEN: str = "#6EE7B7"
    SYNC_DOT: str = "#34D399"
    WARN_AMBER: str = "#FDE68A"
    CORAL_DANGER: str = "#E11D48"
    CORAL_TEXT_LIGHT: str = "#FECDD3"
    CORAL_CANCEL_BG_RGBA: tuple[int, int, int, int] = (225, 29, 72, 56)
    CORAL_CANCEL_HOVER_RGBA: tuple[int, int, int, int] = (225, 29, 72, 97)

    RECESSED_PATH_BG: str = "rgba(6, 14, 28, 0.50)"
    RECESSED_PATH_RGBA: tuple[int, int, int, int] = (6, 14, 28, 128)
    RECESSED_DL_BG: str = "rgba(6, 14, 28, 0.56)"
    RECESSED_DL_RGBA: tuple[int, int, int, int] = (6, 14, 28, 143)

    PANEL_BORDER_RGBA: tuple[int, int, int, int] = (255, 255, 255, 36)
    HAIRLINE_ROW_RGBA: tuple[int, int, int, int] = (255, 255, 255, 26)
    TOOLBAR_DIVIDER_RGBA: tuple[int, int, int, int] = (255, 255, 255, 31)
    PATH_BORDER_RGBA: tuple[int, int, int, int] = (255, 255, 255, 41)
    ROW_HOVER_RGBA: tuple[int, int, int, int] = (37, 200, 206, 31)
    TOOLBAR_HOVER_RGBA: tuple[int, int, int, int] = (255, 255, 255, 23)
    PROGRESS_TRACK_RGBA: tuple[int, int, int, int] = (255, 255, 255, 36)
    DL_PHASE_TEXT: str = "#E0F2FE"
    DL_ACTIVE_SEG: str = "#BAE6FD"
    PROGRESS_END_GREEN: str = "#34D399"

    PANEL_RADIUS: int = 6
    CONTROL_RADIUS: int = 4
    BADGE_RADIUS: int = 3
    PANEL_TOP_BORDER: int = 2


@dataclass(frozen=True)
class PorcelainTokens:
    """Light Porcelain + Navy Header + Hairline surface tokens (Screens 04-08, Modals)."""

    NAVY_HEADER_TOP_LEFT: str = "#264278"
    NAVY_HEADER_BOTTOM_RIGHT: str = "#1B3260"
    NAVY_SOLID: str = "#264278"
    NAVY_HOVER: str = "#1E386A"
    NAVY_BORDER: str = "#1B3260"
    NAVY_BOTTOM_EDGE: str = "#122244"

    NAVY_TEXT: str = "#1E3254"
    SLATE_BODY: str = "#334155"
    SLATE_MUTED: str = "#526580"

    PORCELAIN_BG: str = "#F6F9FD"
    WHITE: str = "#FFFFFF"

    ICE_ZEBRA: str = "#EEF4FA"
    ICE_ROW_ALT: str = "#F8FBFE"
    ICE_HOVER: str = "#E1F3F8"
    ICE_SELECTED: str = "#D7F1F6"

    HAIRLINE: str = "#D5E0EE"
    HAIRLINE_CELL: str = "#DCE5F0"
    HAIRLINE_INPUT: str = "#B8C7DC"
    HAIRLINE_STRONG: str = "#CBD5E1"
    HAIRLINE_SEG: str = "#C8D6E8"
    BTN_SEC_BOTTOM: str = "#9FB3CE"

    CYAN_ACCENT: str = "#12B8C4"
    CYAN_CTA: str = "#1FD3D9"
    CYAN_CTA_BORDER: str = "#0EA5B0"
    CYAN_CTA_BOTTOM: str = "#0B8B95"
    CYAN_TEXT_DEEP: str = "#0E7490"

    CORAL_DANGER: str = "#E11D48"
    CORAL_BORDER: str = "#BE123C"
    CORAL_BOTTOM: str = "#9F1239"
    DANGER_TEXT: str = "#B91C1C"

    OK_TINT: str = "#E8F8F2"
    OK_TEXT: str = "#065F46"
    OK_SUB: str = "#047857"
    OK_BORDER: str = "#A7F3D0"
    OK_ACCENT: str = "#059669"

    WARN_TINT: str = "#FFF8E1"
    WARN_TEXT: str = "#92400E"
    WARN_STRONG: str = "#78350F"
    WARN_BORDER: str = "#FDE68A"
    WARN_ACCENT: str = "#D97706"
    WARN_ICON: str = "#B45309"

    HIGHLIGHT_STRIP_BG: str = "#EBF7FA"
    MODAL_SCRIM_RGBA: tuple[int, int, int, int] = (6, 14, 30, 143)

    TOAST_BG: str = "#065F46"
    TOAST_BORDER: str = "#34D399"
    TOAST_TEXT: str = "#ECFDF5"
    TOAST_INFO_BG: str = "#1E3A6E"
    TOAST_INFO_BORDER: str = "#25C8CE"
    TOAST_INFO_TEXT: str = "#F0FDFA"
    TOAST_WARN_BG: str = "#92400E"
    TOAST_WARN_BORDER: str = "#FBBF24"
    TOAST_WARN_TEXT: str = "#FEF3C7"
    TOAST_ERR_BG: str = "#991B1B"
    TOAST_ERR_BORDER: str = "#FB7185"
    TOAST_ERR_TEXT: str = "#FFE4E6"

    HEADER_MIN_HEIGHT: int = 48
    ERROR_HEADER_MIN_HEIGHT: int = 56
    HEADER_BORDER_BOTTOM: int = 2
    ERROR_HEADER_BORDER_LEFT: int = 5
    HEADER_DIVIDER_RGBA: tuple[int, int, int, int] = (255, 255, 255, 46)
    HEADER_CLOSE_HOVER_RGBA: tuple[int, int, int, int] = (255, 255, 255, 41)
    HEADER_STATUS_BG_RGBA: tuple[int, int, int, int] = (255, 255, 255, 36)
    HEADER_STATUS_TEXT: str = "#FDE68A"

    WINDOW_RADIUS: int = 6
    CONTROL_RADIUS: int = 4
    BADGE_RADIUS: int = 3
    WINDOW_BORDER_RGBA: tuple[int, int, int, int] = (30, 50, 84, 56)
    MODAL_BORDER_RGBA: tuple[int, int, int, int] = (30, 50, 84, 71)

    MODAL_WIDTH_ERROR: int = 820
    MODAL_WIDTH_GAME_SELECT: int = 760
    MODAL_WIDTH_SUPPORT_LOCKED: int = 552
    MODAL_WIDTH_CONFIRM: int = 640
    MODAL_WIDTH_COMPLETED: int = 620
    MODAL_WIDTH_UPDATE_NOTICE: int = 680


@dataclass(frozen=True)
class LayoutTokens:
    """Shared DIP window dimensions, chrome heights, and responsive breakpoints."""

    DEFAULT_WIN_W: int = 1200
    DEFAULT_WIN_H: int = 740
    TITLEBAR_HEIGHT: int = 42
    NAV_RAIL_HEIGHT: int = 44
    VIEWPORT_PAD_X: int = 18
    VIEWPORT_PAD_Y: int = 14
    COMPACT_WIDTH_THRESHOLD: int = 1000
    COMPACT_HEIGHT_THRESHOLD: int = 620
    SINGLE_COL_MODAL_THRESHOLD: int = 780
    TWO_COL_COLLAPSE_THRESHOLD: int = 900


@dataclass(frozen=True)
class ThemeTokens:
    """Combined namespace holding Overview, Porcelain, and Layout tokens."""

    overview: OverviewTokens = OverviewTokens()
    porcelain: PorcelainTokens = PorcelainTokens()
    layout: LayoutTokens = LayoutTokens()


OV_TOKENS = OverviewTokens()
PORCELAIN_TOKENS = PorcelainTokens()
LAYOUT_TOKENS = LayoutTokens()
THEME_TOKENS = ThemeTokens()
