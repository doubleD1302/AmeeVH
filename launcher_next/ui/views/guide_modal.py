"""Installation and Usage Guide Modal (View 02)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from launcher_next.ui.components.glass_card import GlassCard
from launcher_next.ui.components.starlit_button import StarlitButton
from launcher_next.ui.theme import Theme


class GuideModal(QDialog):
    """View 02: Visual step-by-step installation guide and FAQ."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(860, 620)
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
        title = QLabel("HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG")
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

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 12, 0)
        content_layout.setSpacing(18)

        # Step 1
        content_layout.addWidget(
            self._create_step_card(
                step_num="01",
                title="Chuẩn bị & Tắt hoàn toàn game",
                desc=(
                    "Đảm bảo game Stella Sora không đang chạy trong nền trước khi cài đặt. "
                    "Launcher có hệ thống tự động phát hiện tiến trình và sẽ khóa nút cài đặt "
                    "nếu phát hiện game đang mở để tránh làm hỏng tệp đang nạp."
                ),
            )
        )

        # Step 2
        content_layout.addWidget(
            self._create_step_card(
                step_num="02",
                title="Nhấn CÀI ĐẶT VIỆT HÓA",
                desc=(
                    "Tại màn hình Tổng quan, nhấn nút 'CÀI ĐẶT VIỆT HÓA'.\n"
                    "- Hệ thống sẽ kiểm tra chữ ký và chụp ảnh tệp gốc (Preimage snapshot).\n"
                    "- Tự động sao lưu các tệp cần thiết vào thư mục sao lưu an toàn.\n"
                    "- Áp dụng các tệp bản dịch tiếng Việt bằng cơ chế Atomic Staging hai pha, "
                    "đảm bảo không bao giờ để lại trạng thái dở dang nếu xảy ra sự cố đột ngột."
                ),
            )
        )

        # Step 3
        content_layout.addWidget(
            self._create_step_card(
                step_num="03",
                title="Khởi chạy và trải nghiệm game",
                desc=(
                    "Sau khi quá trình cài đặt báo 'Hoàn tất', bạn có thể nhấn nút "
                    "'KHỞI CHẠY GAME' trực tiếp từ launcher hoặc mở game thông qua Steam / Yostar Launcher. "
                    "Toàn bộ giao diện, kỹ năng và cốt truyện sẽ hiển thị tiếng Việt chuẩn xác."
                ),
            )
        )

        # Notice Card
        notice_box = GlassCard(bg_color="rgba(16, 44, 76, 0.6)", border_color="#ffce79")
        notice_box_layout = QVBoxLayout(notice_box)
        notice_box_layout.setContentsMargins(18, 14, 18, 14)
        notice_box_layout.setSpacing(6)

        notice_title = QLabel("LƯU Ý QUAN TRỌNG KHI CẬP NHẬT GAME CHÍNH THỨC")
        notice_title.setStyleSheet(f"QLabel {{ font-size: 13px; font-weight: bold; color: {Theme.WARNING_AMBER}; }}")
        notice_box_layout.addWidget(notice_title)

        notice_text = QLabel(
            "Khi Steam hoặc Yostar Launcher phát hành bản vá game mới, bạn nên mở Stella Sora Launcher "
            "và nhấn 'Khôi phục gốc' trước khi để client chính thức cập nhật. Sau khi cập nhật xong, "
            "hãy mở lại Launcher để kiểm tra và cài đặt phiên bản Việt Hóa tương thích mới nhất."
        )
        notice_text.setWordWrap(True)
        notice_text.setStyleSheet(f"QLabel {{ font-size: 13px; color: {Theme.TEXT_WHITE}; line-height: 1.4; }}")
        notice_box_layout.addWidget(notice_text)
        content_layout.addWidget(notice_box)

        scroll.setWidget(content_widget)
        container_layout.addWidget(scroll, 1)

        main_layout.addWidget(container)

    def _create_step_card(self, step_num: str, title: str, desc: str) -> GlassCard:
        card = GlassCard(bg_color="rgba(12, 34, 60, 0.7)", border_color="#205380")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(16)

        num_label = QLabel(step_num)
        num_label.setFixedWidth(42)
        num_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: bold;
                color: {Theme.PRIMARY_CYAN};
                background: rgba(98, 212, 255, 0.1);
                border: 1px solid rgba(98, 212, 255, 0.3);
                border-radius: 6px;
                padding: 6px;
                qproperty-alignment: AlignCenter;
            }}
        """)
        card_layout.addWidget(num_label, alignment=Qt.AlignmentFlag.AlignTop)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        step_title = QLabel(title)
        step_title.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: bold; color: {Theme.TEXT_WHITE}; }}")
        info_layout.addWidget(step_title)

        step_desc = QLabel(desc)
        step_desc.setWordWrap(True)
        step_desc.setStyleSheet(f"QLabel {{ font-size: 13px; color: {Theme.TEXT_MUTED}; line-height: 1.4; }}")
        info_layout.addWidget(step_desc)

        card_layout.addLayout(info_layout, 1)
        return card
