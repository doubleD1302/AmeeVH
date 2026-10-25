"""Custom draggable frameless title bar with navigation tabs and window controls."""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QWidget,
)

from launcher_next.ui.assets import AssetManager
from launcher_next.ui.components.starlit_button import StarlitButton
from launcher_next.ui.theme import Theme


class TitleBar(QWidget):
    """Custom title bar for frameless window."""

    navigate_requested = Signal(str)  # 'overview', 'notifications', 'guide', 'support', 'tools', 'settings'
    minimize_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent_window: QWidget):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self._drag_pos: Optional[QPoint] = None
        self.setFixedHeight(54)
        self.setStyleSheet(f"""
            TitleBar {{
                background-color: rgba(6, 24, 47, 0.88);
                border-bottom: 1px solid rgba(31, 86, 138, 0.6);
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        assets = AssetManager.get()

        # Branding: App Icon + Title + Version Badge
        self.icon_label = QLabel()
        icon_pixmap = assets.get_pixmap("app_icon.png")
        if not icon_pixmap.isNull():
            self.icon_label.setPixmap(icon_pixmap.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.icon_label)

        self.title_label = QLabel("STELLA SORA")
        self.title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
                color: {Theme.TEXT_WHITE};
            }}
        """)
        layout.addWidget(self.title_label)

        self.version_badge = QLabel("v0.9.8")
        self.version_badge.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: bold;
                color: {Theme.PRIMARY_CYAN};
                background: rgba(98, 212, 255, 0.15);
                border: 1px solid rgba(98, 212, 255, 0.4);
                border-radius: 4px;
                padding: 2px 6px;
            }}
        """)
        layout.addWidget(self.version_badge)

        layout.addSpacing(24)

        # Navigation Tabs
        self.tab_overview = StarlitButton("Tổng quan", variant="tab")
        self.tab_overview.setCheckable(True)
        self.tab_overview.setChecked(True)
        self.tab_overview.clicked.connect(lambda: self._select_tab("overview"))
        layout.addWidget(self.tab_overview)

        self.tab_notif = StarlitButton("Bảng tin", variant="tab")
        self.tab_notif.setCheckable(True)
        self.tab_notif.clicked.connect(lambda: self._select_tab("notifications"))
        layout.addWidget(self.tab_notif)

        self.tab_guide = StarlitButton("Hướng dẫn", variant="tab")
        self.tab_guide.setCheckable(True)
        self.tab_guide.clicked.connect(lambda: self._select_tab("guide"))
        layout.addWidget(self.tab_guide)

        self.tab_support = StarlitButton("Ủng hộ", variant="tab")
        self.tab_support.setCheckable(True)
        self.tab_support.clicked.connect(lambda: self._select_tab("support"))
        layout.addWidget(self.tab_support)

        self.tab_tools = StarlitButton("Công cụ / ADB", variant="tab")
        self.tab_tools.setCheckable(True)
        self.tab_tools.clicked.connect(lambda: self._select_tab("tools"))
        layout.addWidget(self.tab_tools)

        self._tabs = {
            "overview": self.tab_overview,
            "notifications": self.tab_notif,
            "guide": self.tab_guide,
            "support": self.tab_support,
            "tools": self.tab_tools,
        }

        layout.addStretch()

        # Settings Button
        self.btn_settings = QPushButton()
        self.btn_settings.setToolTip("Cài đặt launcher")
        self.btn_settings.setFixedSize(36, 36)
        settings_icon = assets.get_icon("settings")
        self.btn_settings.setIcon(settings_icon)
        self.btn_settings.setIconSize(QSize(18, 18))
        self.btn_settings.setStyleSheet(self._window_btn_style())
        self.btn_settings.clicked.connect(lambda: self.navigate_requested.emit("settings"))
        layout.addWidget(self.btn_settings)

        # Minimize Button
        self.btn_minimize = QPushButton("—")
        self.btn_minimize.setToolTip("Thu nhỏ")
        self.btn_minimize.setFixedSize(36, 36)
        self.btn_minimize.setStyleSheet(self._window_btn_style())
        self.btn_minimize.clicked.connect(self.minimize_requested.emit)
        layout.addWidget(self.btn_minimize)

        # Close Button
        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Đóng")
        self.btn_close.setFixedSize(36, 36)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                border-radius: 4px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 84, 112, 0.8);
                color: #ffffff;
            }}
        """)
        self.btn_close.clicked.connect(self.close_requested.emit)
        layout.addWidget(self.btn_close)

    def set_active_tab(self, tab_key: str):
        for key, tab_btn in self._tabs.items():
            tab_btn.setChecked(key == tab_key)

    def _select_tab(self, tab_key: str):
        self.set_active_tab(tab_key)
        self.navigate_requested.emit(tab_key)

    def _window_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(98, 212, 255, 0.18);
                color: {Theme.TEXT_WHITE};
            }}
            QPushButton:pressed {{
                background-color: rgba(98, 212, 255, 0.3);
            }}
        """

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.parent_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        event.accept()
