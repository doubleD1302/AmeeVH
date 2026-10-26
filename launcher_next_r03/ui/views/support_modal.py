"""Support and Contributor Modal (View 03)."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from launcher_next_r03.core.types import SupporterData
from launcher_next_r03.ui.components.glass_card import GlassCard
from launcher_next_r03.ui.theme import Theme


class SupportModal(QDialog):
    """View 03: Supporter listing and project support info."""

    def __init__(self, supporter_data: SupporterData, parent=None):
        super().__init__(parent)
        self.supporter_data = supporter_data
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(860, 600)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container = GlassCard(bg_color="rgba(8, 26, 48, 0.95)", border_color="#2b6b9e")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(28, 24, 28, 24)
        container_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("ỦNG HỘ DỰ ÁN VIỆT HÓA")
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

        # Overview banner
        banner = GlassCard(bg_color="rgba(12, 36, 66, 0.7)", border_color="#1f568a")
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(20, 16, 20, 16)
        banner_layout.setSpacing(6)

        banner_title = QLabel("Lời tri ân từ Đội ngũ Stella Sora Việt Hóa")
        banner_title.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: bold; color: {Theme.TEXT_WHITE}; }}")
        banner_layout.addWidget(banner_title)

        banner_desc = QLabel(
            "Bản dịch được thực hiện hoàn toàn phi thương mại nhằm phục vụ cộng đồng người chơi Việt Nam. "
            "Mọi đóng góp, hỗ trợ và động viên từ cộng đồng là nguồn động lực to lớn giúp dự án duy trì "
            "và hoàn thiện chất lượng bản dịch tốt nhất."
        )
        banner_desc.setWordWrap(True)
        banner_desc.setStyleSheet(f"QLabel {{ font-size: 13px; color: {Theme.TEXT_MUTED}; line-height: 1.4; }}")
        banner_layout.addWidget(banner_desc)
        container_layout.addWidget(banner)

        # Supporter Status / Table Section
        section_label = QLabel("DANH SÁCH NGƯỜI ỦNG HỘ")
        section_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 1px;
                color: {Theme.TEXT_WHITE};
            }}
        """)
        container_layout.addWidget(section_label)

        # Render status placeholder (Unavailable state per Engineering Spec)
        status_box = GlassCard(bg_color="rgba(10, 28, 52, 0.5)", border_color="#18426b")
        status_box_layout = QVBoxLayout(status_box)
        status_box_layout.setContentsMargins(24, 32, 24, 32)
        status_box_layout.setSpacing(12)
        status_box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        badge_status = QLabel("TRẠNG THÁI: CHƯA ĐỒNG BỘ API")
        badge_status.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: bold;
                color: {Theme.WARNING_AMBER};
                background: rgba(255, 206, 121, 0.12);
                border: 1px solid rgba(255, 206, 121, 0.35);
                border-radius: 4px;
                padding: 4px 10px;
            }}
        """)
        status_box_layout.addWidget(badge_status, alignment=Qt.AlignmentFlag.AlignCenter)

        msg_label = QLabel(self.supporter_data.qr_placeholder_text)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"QLabel {{ font-size: 14px; color: {Theme.TEXT_MUTED}; line-height: 1.5; }}")
        status_box_layout.addWidget(msg_label)

        sub_msg = QLabel("Mọi thông tin đóng góp thực tế sẽ được cập nhật khi hệ thống máy chủ chính thức được kích hoạt.")
        sub_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_msg.setStyleSheet(f"QLabel {{ font-size: 12px; color: #6287aa; }}")
        status_box_layout.addWidget(sub_msg)

        container_layout.addWidget(status_box, 1)

        main_layout.addWidget(container)
