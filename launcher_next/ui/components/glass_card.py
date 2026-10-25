"""Glass container card for Starlit Glass theme."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFrame, QVBoxLayout

from launcher_next.ui.theme import Theme


class GlassCard(QFrame):
    """Semi-transparent glass panel with border and corner highlights."""

    def __init__(self, parent=None, border_color: str = "#1f568a", bg_color: str = "rgba(10, 32, 60, 0.82)"):
        super().__init__(parent)
        self.border_color = border_color
        self.bg_color = bg_color
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(f"""
            GlassCard {{
                background-color: {self.bg_color};
                border: 1px solid {self.border_color};
                border-radius: 10px;
            }}
        """)
