"""Modal Confirmation Dialog (View 05)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from launcher_next_r03.ui.components.glass_card import GlassCard
from launcher_next_r03.ui.components.starlit_button import StarlitButton
from launcher_next_r03.ui.theme import Theme


class ConfirmationDialog(QDialog):
    """View 05: Action confirmation modal."""

    def __init__(
        self,
        title: str,
        message: str,
        confirm_label: str = "Xác nhận",
        cancel_label: str = "Hủy bỏ",
        is_danger: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(520, 280)
        self._setup_ui(title, message, confirm_label, cancel_label, is_danger)

    def _setup_ui(self, title: str, message: str, confirm_label: str, cancel_label: str, is_danger: bool):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        border_color = Theme.DANGER_RED if is_danger else "#2b6b9e"
        container = GlassCard(bg_color="rgba(8, 24, 46, 0.96)", border_color=border_color)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(28, 24, 28, 24)
        container_layout.setSpacing(18)

        # Title Row
        title_label = QLabel(title)
        title_color = Theme.DANGER_RED if is_danger else Theme.PRIMARY_CYAN
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 0.5px;
                color: {title_color};
            }}
        """)
        container_layout.addWidget(title_label)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {Theme.TEXT_WHITE};
                line-height: 1.5;
            }}
        """)
        container_layout.addWidget(msg_label, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        btn_cancel = StarlitButton(cancel_label, variant="secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_confirm = StarlitButton(confirm_label, variant="danger" if is_danger else "primary")
        btn_confirm.clicked.connect(self.accept)
        btn_layout.addWidget(btn_confirm)

        container_layout.addLayout(btn_layout)
        main_layout.addWidget(container)
