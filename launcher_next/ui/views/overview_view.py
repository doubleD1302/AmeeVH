"""Main overview dashboard view (View 00)."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from launcher_next.core.types import GameInfo, NotificationItem, OperationEvent, OperationPhase
from launcher_next.ui.assets import AssetManager
from launcher_next.ui.components.glass_card import GlassCard
from launcher_next.ui.components.starlit_button import StarlitButton
from launcher_next.ui.theme import Theme


class OverviewView(QWidget):
    """View 00: Main interactive dashboard."""

    install_requested = Signal()
    rollback_requested = Signal()
    launch_requested = Signal()
    view_notifications_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        assets = AssetManager.get()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 24, 40, 36)
        main_layout.setSpacing(20)

        # Top Section: Logo & Subtitle
        top_layout = QHBoxLayout()
        top_layout.setSpacing(16)

        logo_pixmap = assets.get_logo()
        self.logo_label = QLabel()
        if not logo_pixmap.isNull():
            scaled_logo = logo_pixmap.scaledToHeight(64, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(scaled_logo)
        top_layout.addWidget(self.logo_label)

        sub_layout = QVBoxLayout()
        sub_layout.setSpacing(4)
        subtitle = QLabel("DỰ ÁN VIỆT HÓA CỘNG ĐỒNG")
        subtitle.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 2px;
                color: {Theme.PRIMARY_CYAN};
            }}
        """)
        slogan = QLabel("Trải nghiệm cốt truyện hoàn chỉnh & giao diện sắc nét")
        slogan.setStyleSheet(f"QLabel {{ font-size: 13px; color: {Theme.TEXT_MUTED}; }}")
        sub_layout.addWidget(subtitle)
        sub_layout.addWidget(slogan)
        top_layout.addLayout(sub_layout)

        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # Center spacer (allows character art on background to be visible)
        main_layout.addStretch(1)

        # Bottom Section: Two Glass Cards side by side
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(28)

        # Left Card: Latest Notification
        self.card_notif = GlassCard()
        self.card_notif.setFixedWidth(460)
        card_notif_layout = QVBoxLayout(self.card_notif)
        card_notif_layout.setContentsMargins(22, 20, 22, 20)
        card_notif_layout.setSpacing(10)

        notif_header_layout = QHBoxLayout()
        notif_badge = QLabel("BẢNG TIN MỚI")
        notif_badge.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: bold;
                color: {Theme.PRIMARY_CYAN};
                background: rgba(98, 212, 255, 0.15);
                border: 1px solid rgba(98, 212, 255, 0.35);
                border-radius: 4px;
                padding: 3px 8px;
            }}
        """)
        notif_header_layout.addWidget(notif_badge)

        self.notif_date = QLabel("2026-10-25")
        self.notif_date.setStyleSheet(f"QLabel {{ font-size: 12px; color: {Theme.TEXT_MUTED}; }}")
        notif_header_layout.addWidget(self.notif_date)
        notif_header_layout.addStretch()

        self.btn_all_notifs = StarlitButton("Xem tất cả >", variant="ghost")
        self.btn_all_notifs.setStyleSheet(f"""
            QPushButton {{
                color: {Theme.PRIMARY_CYAN};
                border: none;
                font-size: 12px;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                color: #ffffff;
                text-decoration: underline;
            }}
        """)
        self.btn_all_notifs.clicked.connect(self.view_notifications_requested.emit)
        notif_header_layout.addWidget(self.btn_all_notifs)
        card_notif_layout.addLayout(notif_header_layout)

        self.notif_title = QLabel("Bản Việt Hóa Stella Sora v0.9.8")
        self.notif_title.setWordWrap(True)
        self.notif_title.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: bold;
                color: {Theme.TEXT_WHITE};
            }}
        """)
        card_notif_layout.addWidget(self.notif_title)

        self.notif_summary = QLabel(
            "Cập nhật giao diện Starlit Glass hoàn toàn mới, đồng bộ dữ liệu cốt truyện & thẻ nhân vật."
        )
        self.notif_summary.setWordWrap(True)
        self.notif_summary.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {Theme.TEXT_MUTED};
                line-height: 1.4;
            }}
        """)
        card_notif_layout.addWidget(self.notif_summary)
        card_notif_layout.addStretch()

        bottom_layout.addWidget(self.card_notif)

        # Right Card: Patch Actions & Status
        self.card_action = GlassCard()
        card_action_layout = QVBoxLayout(self.card_action)
        card_action_layout.setContentsMargins(24, 20, 24, 20)
        card_action_layout.setSpacing(12)

        # Game status line
        status_line = QHBoxLayout()
        status_line.setSpacing(10)

        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(f"QLabel {{ color: {Theme.SUCCESS_GREEN}; font-size: 16px; }}")
        status_line.addWidget(self.status_indicator)

        self.game_status_label = QLabel("Đang kiểm tra trạng thái game...")
        self.game_status_label.setStyleSheet(f"QLabel {{ font-size: 14px; font-weight: 600; color: {Theme.TEXT_WHITE}; }}")
        status_line.addWidget(self.game_status_label)
        status_line.addStretch()

        self.patch_status_badge = QLabel("Chưa cài đặt Việt Hóa")
        self.patch_status_badge.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {Theme.TEXT_MUTED};
                background: rgba(16, 48, 86, 0.4);
                border: 1px solid {Theme.GLASS_CARD_BORDER};
                border-radius: 4px;
                padding: 3px 8px;
            }}
        """)
        status_line.addWidget(self.patch_status_badge)
        card_action_layout.addLayout(status_line)

        # Progress bar & detail message (hidden when idle)
        self.progress_container = QWidget()
        prog_layout = QVBoxLayout(self.progress_container)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(6)

        self.progress_label = QLabel("Đang chuẩn bị...")
        self.progress_label.setStyleSheet(f"QLabel {{ font-size: 12px; color: {Theme.PRIMARY_CYAN}; }}")
        prog_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        prog_layout.addWidget(self.progress_bar)
        card_action_layout.addWidget(self.progress_container)
        self.progress_container.setVisible(False)

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)

        self.btn_rollback = StarlitButton("Khôi phục gốc", variant="secondary")
        self.btn_rollback.setToolTip("Khôi phục tệp game gốc nguyên vẹn từ bản sao lưu an toàn")
        self.btn_rollback.clicked.connect(self.rollback_requested.emit)
        btn_layout.addWidget(self.btn_rollback)

        self.btn_launch = StarlitButton("Khởi chạy game", variant="secondary")
        self.btn_launch.setToolTip("Khởi chạy game Stella Sora")
        self.btn_launch.clicked.connect(self.launch_requested.emit)
        btn_layout.addWidget(self.btn_launch)

        self.btn_install = StarlitButton("CÀI ĐẶT VIỆT HÓA", variant="primary")
        self.btn_install.setToolTip("Cài đặt bản dịch tiếng Việt vào game")
        self.btn_install.setFixedHeight(44)
        self.btn_install.clicked.connect(self.install_requested.emit)
        btn_layout.addWidget(self.btn_install, 1)

        card_action_layout.addLayout(btn_layout)
        bottom_layout.addWidget(self.card_action, 1)

        main_layout.addLayout(bottom_layout)

    def update_notification(self, item: NotificationItem):
        self.notif_title.setText(item.title)
        self.notif_date.setText(item.date)
        self.notif_summary.setText(item.summary)

    def update_game_status(self, game_info: GameInfo, is_patched: bool):
        if not game_info.installed:
            self.status_indicator.setStyleSheet(f"QLabel {{ color: {Theme.WARNING_AMBER}; font-size: 16px; }}")
            self.game_status_label.setText("Chưa tìm thấy game (Hãy cấu hình đường dẫn trong Cài đặt)")
            self.btn_install.setEnabled(False)
            self.btn_rollback.setEnabled(False)
            self.btn_launch.setEnabled(False)
            return

        if game_info.is_running:
            self.status_indicator.setStyleSheet(f"QLabel {{ color: {Theme.DANGER_RED}; font-size: 16px; }}")
            self.game_status_label.setText("Game đang chạy! Hãy tắt game trước khi thao tác.")
            self.btn_install.setEnabled(False)
            self.btn_rollback.setEnabled(False)
            self.btn_launch.setEnabled(False)
            return

        # Game is found and idle
        self.status_indicator.setStyleSheet(f"QLabel {{ color: {Theme.SUCCESS_GREEN}; font-size: 16px; }}")
        source_name = "Steam" if game_info.platform == "steam" else ("Yostar" if game_info.platform == "standalone" else "Tùy chỉnh")
        self.game_status_label.setText(f"{source_name}: Sẵn sàng")
        self.btn_launch.setEnabled(True)

        if is_patched or game_info.has_vietnamese:
            self.patch_status_badge.setText("Đã cài bản Việt Hóa v0.9.8")
            self.patch_status_badge.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {Theme.PRIMARY_CYAN};
                    background: rgba(98, 212, 255, 0.15);
                    border: 1px solid rgba(98, 212, 255, 0.4);
                    border-radius: 4px;
                    padding: 3px 8px;
                }}
            """)
            self.btn_install.setText("CẬP NHẬT LẠI")
            self.btn_rollback.setEnabled(True)
        else:
            self.patch_status_badge.setText("Bản game gốc (Chưa cài Việt Hóa)")
            self.patch_status_badge.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {Theme.TEXT_MUTED};
                    background: rgba(16, 48, 86, 0.4);
                    border: 1px solid {Theme.GLASS_CARD_BORDER};
                    border-radius: 4px;
                    padding: 3px 8px;
                }}
            """)
            self.btn_install.setText("CÀI ĐẶT VIỆT HÓA")
            self.btn_rollback.setEnabled(False)

        self.btn_install.setEnabled(True)

    def show_progress(self, show: bool = True, label: str = "", percent: int = 0):
        self.progress_container.setVisible(show)
        if show:
            self.progress_label.setText(label)
            self.progress_bar.setValue(percent)
            self.btn_install.setEnabled(False)
            self.btn_rollback.setEnabled(False)
            self.btn_launch.setEnabled(False)

    def handle_operation_event(self, event: OperationEvent):
        pct = int(event.percentage)
        if event.phase == OperationPhase.DONE:
            self.show_progress(True, event.message, 100)
        elif event.phase == OperationPhase.ERROR:
            self.show_progress(True, f"Thất bại: {event.message}", 0)
        else:
            self.show_progress(True, event.message, pct)
