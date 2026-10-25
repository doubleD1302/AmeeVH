"""Custom styled buttons for Starlit Glass theme."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QCursor, QFont, QIcon, QPainter, QPen
from PySide6.QtCore import QRectF
from .glass_card import nine_patch
from ..assets import AssetManager
from PySide6.QtWidgets import QPushButton

from launcher_next_r02.ui.theme import Theme


class StarlitButton(QPushButton):
    """Button implementing Starlit Glass styling variants."""

    def __init__(
        self,
        text: str = "",
        variant: str = "primary",  # primary, secondary, danger, ghost, tab
        icon: Optional[QIcon] = None,
        parent=None,
    ):
        super().__init__(text, parent)
        self.variant = variant
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(18, 18))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._apply_style()

    def set_variant(self, variant: str):
        self.variant = variant
        self._apply_style()

    def _apply_style(self):
        base_style = """
            QPushButton {
                font-family: Segoe UI, Arial, sans-serif;
                font-weight: 600;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
            }
        """

        if self.variant == "primary":
            style = f"""
                {base_style}
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4bbfe8, stop:1 {Theme.PRIMARY_CYAN});
                    color: {Theme.TEXT_DARK};
                    border: 1px solid #7fe5ff;
                    font-size: 15px;
                    font-weight: bold;
                    min-height: 24px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6ce2ff, stop:1 {Theme.PRIMARY_CYAN_HOVER});
                    border: 1px solid #ffffff;
                }}
                QPushButton:pressed {{
                    background: {Theme.PRIMARY_CYAN_PRESSED};
                    border: 1px solid #3296c0;
                }}
                QPushButton:disabled {{
                    background: #173852;
                    color: #5d819e;
                    border: 1px solid #1c4566;
                }}
            """
        elif self.variant == "secondary":
            style = f"""
                {base_style}
                QPushButton {{
                    background-color: {Theme.SECONDARY_BTN_BG};
                    color: {Theme.TEXT_WHITE};
                    border: 1px solid {Theme.SECONDARY_BTN_BORDER};
                    min-height: 22px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.SECONDARY_BTN_BG_HOVER};
                    border: 1px solid {Theme.PRIMARY_CYAN};
                    color: #ffffff;
                }}
                QPushButton:pressed {{
                    background-color: rgba(18, 48, 85, 0.9);
                    border: 1px solid #235885;
                }}
                QPushButton:disabled {{
                    background-color: rgba(14, 34, 58, 0.4);
                    color: #4a6c8a;
                    border: 1px solid #193652;
                }}
            """
        elif self.variant == "danger":
            style = f"""
                {base_style}
                QPushButton {{
                    background-color: {Theme.DANGER_RED_BG};
                    color: #fff0f3;
                    border: 1px solid {Theme.DANGER_RED};
                }}
                QPushButton:hover {{
                    background-color: rgba(220, 40, 70, 0.8);
                    border: 1px solid {Theme.DANGER_RED_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: rgba(150, 20, 50, 0.9);
                    border: 1px solid #991530;
                }}
                QPushButton:disabled {{
                    background-color: rgba(60, 20, 30, 0.4);
                    color: #8a4a55;
                    border: 1px solid #551a24;
                }}
            """
        elif self.variant == "tab":
            style = f"""
                {base_style}
                QPushButton {{
                    background-color: transparent;
                    color: {Theme.TEXT_MUTED};
                    border: none;
                    border-bottom: 2px solid transparent;
                    border-radius: 0px;
                    padding: 8px 14px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    color: {Theme.TEXT_WHITE};
                    border-bottom: 2px solid rgba(98, 212, 255, 0.5);
                }}
                QPushButton:checked {{
                    color: {Theme.PRIMARY_CYAN};
                    border-bottom: 2px solid {Theme.PRIMARY_CYAN};
                    font-weight: bold;
                }}
            """
        else:  # ghost
            style = f"""
                {base_style}
                QPushButton {{
                    background-color: transparent;
                    color: {Theme.TEXT_WHITE};
                    border: 1px solid transparent;
                }}
                QPushButton:hover {{
                    background-color: rgba(98, 212, 255, 0.15);
                    border: 1px solid rgba(98, 212, 255, 0.3);
                }}
                QPushButton:pressed {{
                    background-color: rgba(98, 212, 255, 0.25);
                }}
            """

        self.setStyleSheet(style)

    def paintEvent(self,event):
        state='disabled' if not self.isEnabled() else ('pressed' if self.isDown() else ('selected' if self.isChecked() else ('hover' if self.underMouse() else ('focus' if self.hasFocus() else 'normal'))))
        category='tab' if self.variant=='tab' else self.variant
        if category=='ghost':
            return super().paintEvent(event)
        a=AssetManager.get();pm=a.get_component_pixmap('buttons',category+'_'+state,2)
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        nine_patch(painter,QRectF(self.rect()),pm,(24,24,24,24),2)
        color='#06243b' if self.variant=='primary' and self.isEnabled() else ('#f0f7ff' if self.isEnabled() else '#5d819e')
        painter.setPen(QColor(color));painter.setFont(self.font());painter.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,self.text())
