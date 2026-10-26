"""Notifications & Announcements Modal (View 01)."""

from __future__ import annotations

from typing import List, Optional
import html
from urllib.parse import urlparse
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from launcher_next_r03.core.types import NotificationItem
from launcher_next_r03.ui.components.glass_card import GlassCard
from launcher_next_r03.ui.components.starlit_button import StarlitButton
from launcher_next_r03.ui.theme import Theme


class NotificationsModal(QDialog):
    """View 01: Multi-column notification center."""

    def __init__(self, notifications: List[NotificationItem], parent=None):
        super().__init__(parent)
        self.notifications = notifications
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(920, 620)
        self._setup_ui()
        self._populate_list()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Card container
        self.container = GlassCard(bg_color="rgba(8, 26, 48, 0.94)", border_color="#2b6b9e")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(24, 20, 24, 24)
        container_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("BẢNG TIN & THÔNG BÁO")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                letter-spacing: 1px;
                color: {Theme.PRIMARY_CYAN};
            }}
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 32)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_MUTED};
                border: none;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {Theme.DANGER_RED};
            }}
        """)
        btn_close.clicked.connect(self.accept)
        header_layout.addWidget(btn_close)
        container_layout.addLayout(header_layout)

        # Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm kiếm thông báo...")
        self.search_input.textChanged.connect(self._filter_items)
        search_layout.addWidget(self.search_input)
        self.category_filter=QComboBox();self.category_filter.addItem("Tất cả",None)
        for category in sorted({n.category for n in self.notifications}):self.category_filter.addItem(category,category)
        self.category_filter.currentIndexChanged.connect(self._populate_list);search_layout.addWidget(self.category_filter)
        container_layout.addLayout(search_layout)

        # Content Splitter (Left: List, Right: Details)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: rgba(31, 86, 138, 0.4);
                width: 2px;
            }
        """)

        # Left list widget
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_item_selected)
        splitter.addWidget(self.list_widget)

        # Right detail widget
        detail_container = QWidget()
        detail_layout = QVBoxLayout(detail_container)
        detail_layout.setContentsMargins(16, 0, 0, 0)
        detail_layout.setSpacing(12)

        self.detail_category = QLabel("THÔNG BÁO")
        self.detail_category.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: bold;
                color: {Theme.PRIMARY_CYAN};
                background: rgba(98, 212, 255, 0.12);
                border: 1px solid rgba(98, 212, 255, 0.3);
                border-radius: 4px;
                padding: 2px 6px;
            }}
        """)
        detail_layout.addWidget(self.detail_category, alignment=Qt.AlignmentFlag.AlignLeft)

        self.detail_title = QLabel("Tiêu đề thông báo")
        self.detail_title.setWordWrap(True)
        self.detail_title.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {Theme.TEXT_WHITE};
            }}
        """)
        detail_layout.addWidget(self.detail_title)

        self.detail_date = QLabel("2026-10-25")
        self.detail_date.setStyleSheet(f"QLabel {{ font-size: 12px; color: {Theme.TEXT_MUTED}; }}")
        detail_layout.addWidget(self.detail_date)

        self.detail_body = QTextBrowser()
        self.detail_body.setOpenExternalLinks(False)
        self.detail_body.setOpenLinks(False)
        self.detail_body.anchorClicked.connect(lambda u: QDesktopServices.openUrl(u) if u.scheme() in ("http","https") and u.host() else None)
        self.detail_body.setStyleSheet(f"""
            QTextBrowser {{
                background-color: rgba(6, 20, 38, 0.6);
                border: 1px solid rgba(31, 86, 138, 0.4);
                border-radius: 6px;
                padding: 12px;
                color: {Theme.TEXT_WHITE};
                font-size: 14px;
                line-height: 1.5;
            }}
        """)
        detail_layout.addWidget(self.detail_body, 1)

        splitter.addWidget(detail_container)
        splitter.setSizes([340, 520])

        container_layout.addWidget(splitter, 1)
        main_layout.addWidget(self.container)

    def _populate_list(self):
        self.list_widget.clear()
        query = self.search_input.text().strip().lower()
        self._filtered_indices = []

        for idx, item in enumerate(self.notifications):
            category=self.category_filter.currentData()
            if category and item.category!=category:continue
            if query and (query not in item.title.lower() and query not in item.summary.lower()):
                continue

            self._filtered_indices.append(idx)
            list_item = QListWidgetItem()
            # Custom text display
            badge = "★ " if item.is_unread else ""
            list_item.setText(f"{badge}{item.title}\n{item.date} • {item.badge}")
            self.list_widget.addItem(list_item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        else:
            self._show_empty_detail()

    def _filter_items(self):
        self._populate_list()

    def _on_item_selected(self, row: int):
        if 0 <= row < len(self._filtered_indices):
            original_idx = self._filtered_indices[row]
            item = self.notifications[original_idx]
            self.detail_category.setText(item.category.upper())
            self.detail_title.setText(item.title)
            self.detail_date.setText(item.date)
            # Format content with paragraphs
            formatted_text = html.escape(item.content).replace("\n", "<br>")
            if item.link_url and urlparse(item.link_url).scheme in ("http","https"):
                formatted_text += "<p><a href=\""+html.escape(item.link_url,quote=True)+"\">Mở liên kết chính thức</a></p>"
            self.detail_body.setHtml(f"<div style='font-family: Segoe UI, sans-serif; font-size: 14px; color: #f0f7ff;'>{formatted_text}</div>")

    def _show_empty_detail(self):
        self.detail_category.setText("TRỐNG")
        self.detail_title.setText("Không tìm thấy thông báo phù hợp")
        self.detail_date.setText("")
        self.detail_body.setHtml("<p style='color: #a4c9e7;'>Không có nội dung hiển thị.</p>")
