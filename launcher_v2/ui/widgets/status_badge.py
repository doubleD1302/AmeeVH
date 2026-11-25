# -*- coding: utf-8 -*-
"""
Compact inline platform/version tags, header status tags, and left-accented banners.

Replaces glowing pill clutter with crisp flat tags matching Preview r5.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..theme.tokens import OV_TOKENS, PORCELAIN_TOKENS, rgba_qcolor
from ..theme.typography import FS_BODY_SM, FS_CAPTION, FS_META, nfc, ui_font
from .asset_renderer import AssetRenderer, get_asset_renderer


class PlatformTag(QLabel):
    """Compact 3px-radius platform badge ('Yostar' or 'Steam')."""

    def __init__(
        self,
        text: str = "Yostar",
        *,
        surface: str = "dark",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(nfc(text), parent)
        self._surface = surface
        self.setObjectName("platformTag")
        self.setFont(ui_font(FS_CAPTION if surface == "light" else FS_META, 700))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_style()

    def set_surface(self, surface: str) -> None:
        self._surface = surface
        self.setFont(ui_font(FS_CAPTION if surface == "light" else FS_META, 700))
        self._apply_style()

    def _apply_style(self) -> None:
        if self._surface == "light":
            bg = PORCELAIN_TOKENS.NAVY_SOLID
            fg = "#FFFFFF"
        else:
            bg = OV_TOKENS.PLATFORM_TAG_BG
            fg = OV_TOKENS.CYAN_ACCENT
        self.setStyleSheet(
            f"QLabel#platformTag {{ background: {bg}; color: {fg}; "
            f"border-radius: 3px; padding: 2px 7px; border: none; }}"
        )


class HeaderStatusTag(QLabel):
    """Subtle Navy-header status tag (e.g., 'Tạm đóng' in #FDE68A)."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(nfc(text), parent)
        self.setObjectName("headerStatusTag")
        self.setFont(ui_font(FS_CAPTION, 700))
        self.setStyleSheet(
            f"QLabel#headerStatusTag {{ background: rgba(255, 255, 255, 0.14); "
            f"color: {PORCELAIN_TOKENS.HEADER_STATUS_TEXT}; border-radius: 3px; "
            f"padding: 2px 8px; border: none; }}"
        )


class StatusInline(QWidget):
    """Inline 12x12 sprite + status text ('Đã cài v...', 'Chưa cài', 'Bản gốc EN')."""

    def __init__(
        self,
        text: str = "",
        *,
        tone: str = "muted",
        surface: str = "dark",
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer or get_asset_renderer()
        self._tone = tone
        self._surface = surface

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(12, 12)
        lay.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.text_label = QLabel(nfc(text), self)
        self.text_label.setFont(ui_font(FS_META, 600, tabular=True))
        lay.addWidget(self.text_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.set_status(text, tone=tone)

    def set_status(self, text: str, *, tone: str | None = None, surface: str | None = None) -> None:
        if tone is not None:
            self._tone = tone
        if surface is not None:
            self._surface = surface

        self.text_label.setText(nfc(text))
        dpr = max(1.0, float(self.devicePixelRatioF()))

        if self._tone == "ok":
            color = PORCELAIN_TOKENS.OK_TEXT if self._surface == "light" else OV_TOKENS.OK_GREEN
            tint = PORCELAIN_TOKENS.OK_TEXT if self._surface == "light" else OV_TOKENS.OK_GREEN
            pix = self._renderer.get_icon_pixmap("game/btn_icon_tick.png", (12, 12), dpr, tint=tint)
            self.icon_label.setPixmap(pix)
            self.icon_label.setVisible(not pix.isNull())
        elif self._tone == "warn":
            color = PORCELAIN_TOKENS.WARN_ICON if self._surface == "light" else OV_TOKENS.WARN_AMBER
            pix = self._renderer.get_icon_pixmap("game/zs_stage_warning_icon_s.png", (12, 12), dpr)
            self.icon_label.setPixmap(pix)
            self.icon_label.setVisible(not pix.isNull())
        elif self._tone == "danger":
            color = PORCELAIN_TOKENS.DANGER_TEXT if self._surface == "light" else OV_TOKENS.CORAL_TEXT_LIGHT
            pix = self._renderer.get_icon_pixmap("game/zs_stage_warning_icon_s.png", (12, 12), dpr)
            self.icon_label.setPixmap(pix)
            self.icon_label.setVisible(not pix.isNull())
        else:
            color = PORCELAIN_TOKENS.SLATE_MUTED if self._surface == "light" else OV_TOKENS.TEXT_MUTED
            self.icon_label.setVisible(False)

        self.text_label.setStyleSheet(f"color: {color}; background: transparent;")


class AccentBannerStrip(QFrame):
    """Flat left-accented notice strip (ok, warn, info, danger) with zero rounded border boxes."""

    def __init__(
        self,
        title: str = "",
        body: str = "",
        *,
        tone: str = "info",
        icon_path: str | None = None,
        icon_tint: QColor | str | None = None,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer or get_asset_renderer()
        self._tone = tone
        self._icon_path = icon_path
        self._icon_tint = icon_tint
        self.setObjectName("accentBannerStrip")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 10, 18, 10)
        lay.setSpacing(10)

        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(16, 16)
        self.icon_label.setVisible(False)
        lay.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        self.title_label = QLabel(nfc(title), self)
        self.title_label.setFont(ui_font(FS_BODY_SM, 700))
        self.title_label.setWordWrap(True)
        self.title_label.setVisible(bool(title))
        text_col.addWidget(self.title_label)

        self.body_label = QLabel(nfc(body), self)
        self.body_label.setFont(ui_font(FS_BODY_SM, 400))
        self.body_label.setWordWrap(True)
        self.body_label.setVisible(bool(body))
        text_col.addWidget(self.body_label)

        lay.addLayout(text_col, 1)

        self._right_slot = QHBoxLayout()
        self._right_slot.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self._right_slot, 0)
        self._right_widget: QWidget | None = None

        self.set_tone(tone)

    def _palette(self) -> tuple[str, str, str, str, str]:
        p = PORCELAIN_TOKENS
        if self._tone == "ok":
            return p.OK_TINT, p.OK_ACCENT, p.OK_BORDER, p.OK_TEXT, p.OK_SUB
        if self._tone == "warn":
            return p.WARN_TINT, p.WARN_ACCENT, p.WARN_BORDER, p.WARN_STRONG, p.WARN_TEXT
        if self._tone == "danger":
            return "#FFF1F2", p.CORAL_DANGER, "#FECDD3", p.DANGER_TEXT, p.SLATE_BODY
        return p.ICE_ROW_ALT, p.CYAN_ACCENT, p.HAIRLINE, p.NAVY_TEXT, p.SLATE_BODY

    def set_tone(self, tone: str) -> None:
        self._tone = tone
        _, _, _, title_fg, body_fg = self._palette()
        self.title_label.setStyleSheet(f"color: {title_fg}; background: transparent;")
        self.body_label.setStyleSheet(f"color: {body_fg}; background: transparent;")
        self._refresh_icon()
        self.update()

    def set_content(self, title: str = "", body: str = "", *, tone: str | None = None) -> None:
        if tone is not None:
            self._tone = tone
        t = nfc(title)
        b = nfc(body)
        self.title_label.setText(t)
        self.title_label.setVisible(bool(t))
        self.body_label.setText(b)
        self.body_label.setVisible(bool(b))
        self.set_tone(self._tone)

    def set_right_widget(self, widget: QWidget | None) -> None:
        if self._right_widget is not None:
            self._right_slot.removeWidget(self._right_widget)
            self._right_widget.setParent(None)
        self._right_widget = widget
        if widget is not None:
            self._right_slot.addWidget(widget)

    def _refresh_icon(self) -> None:
        if not self._icon_path:
            self.icon_label.setVisible(False)
            return
        dpr = max(1.0, float(self.devicePixelRatioF()))
        pix = self._renderer.get_icon_pixmap(self._icon_path, (16, 16), dpr, tint=self._icon_tint)
        self.icon_label.setPixmap(pix)
        self.icon_label.setVisible(not pix.isNull())

    def paintEvent(self, event) -> None:  # noqa: N802
        bg, accent, bottom_border, _, _ = self._palette()
        painter = QPainter(self)
        r = self.rect()
        painter.fillRect(r, QColor(bg))
        painter.fillRect(0, 0, 4, r.height(), QColor(accent))
        painter.fillRect(0, r.height() - 1, r.width(), 1, QColor(bottom_border))
        painter.end()


# Convenience alias exported in ui.widgets.__all__
StatusBadge = StatusInline
