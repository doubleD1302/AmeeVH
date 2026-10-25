"""Launcher Settings Modal (View 04)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from launcher_next.core.config import ConfigManager
from launcher_next.core.network import NetworkService
from launcher_next.ui.components.glass_card import GlassCard
from launcher_next.ui.components.starlit_button import StarlitButton
from launcher_next.ui.theme import Theme


class SettingsModal(QDialog):
    """View 04: Launcher configuration, game path selection, update checker."""

    game_path_changed = Signal(str)

    def __init__(self, config_manager: ConfigManager, network_service: NetworkService, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.network_service = network_service
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(760, 560)
        self._setup_ui()
        self._load_current_values()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container = GlassCard(bg_color="rgba(8, 26, 48, 0.95)", border_color="#2b6b9e")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(28, 24, 28, 24)
        container_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("CÀI ĐẶT LAUNCHER")
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

        # Game Path Section
        path_group = GlassCard(bg_color="rgba(12, 36, 66, 0.6)", border_color="#1f568a")
        path_layout = QVBoxLayout(path_group)
        path_layout.setContentsMargins(18, 16, 18, 16)
        path_layout.setSpacing(10)

        path_title = QLabel("ĐƯỜNG DẪN THƯ MỤC CÀI ĐẶT GAME")
        path_title.setStyleSheet(f"QLabel {{ font-size: 13px; font-weight: bold; color: {Theme.TEXT_WHITE}; }}")
        path_layout.addWidget(path_title)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Ví dụ: C:\\Program Files (x86)\\Steam\\steamapps\\common\\StellaSora")
        self.path_input.textChanged.connect(self._validate_path)
        input_row.addWidget(self.path_input, 1)

        btn_browse = StarlitButton("Duyệt...", variant="secondary")
        btn_browse.clicked.connect(self._browse_path)
        input_row.addWidget(btn_browse)
        path_layout.addLayout(input_row)

        self.path_status_label = QLabel("")
        self.path_status_label.setStyleSheet("QLabel { font-size: 12px; }")
        path_layout.addWidget(self.path_status_label)

        container_layout.addWidget(path_group)

        # General Options Section
        opts_group = GlassCard(bg_color="rgba(12, 36, 66, 0.6)", border_color="#1f568a")
        opts_layout = QVBoxLayout(opts_group)
        opts_layout.setContentsMargins(18, 16, 18, 16)
        opts_layout.setSpacing(12)

        opts_title = QLabel("TÙY CHỌN LAUNCHER")
        opts_title.setStyleSheet(f"QLabel {{ font-size: 13px; font-weight: bold; color: {Theme.TEXT_WHITE}; }}")
        opts_layout.addWidget(opts_title)

        self.chk_auto_detect = QCheckBox("Tự động dò tìm thư mục game khi khởi động")
        self.chk_auto_detect.setStyleSheet(f"QCheckBox {{ color: {Theme.TEXT_WHITE}; font-size: 13px; }}")
        opts_layout.addWidget(self.chk_auto_detect)

        self.chk_reduced_motion = QCheckBox("Chế độ tiết kiệm hiệu năng (Giảm hiệu ứng đồ họa)")
        self.chk_reduced_motion.setStyleSheet(f"QCheckBox {{ color: {Theme.TEXT_WHITE}; font-size: 13px; }}")
        opts_layout.addWidget(self.chk_reduced_motion)

        # Check updates row
        update_row = QHBoxLayout()
        update_row.setSpacing(12)
        btn_check_update = StarlitButton("Kiểm tra bản cập nhật Launcher", variant="secondary")
        btn_check_update.clicked.connect(self._check_update)
        update_row.addWidget(btn_check_update)

        self.update_status_label = QLabel("")
        self.update_status_label.setStyleSheet(f"QLabel {{ font-size: 12px; color: {Theme.TEXT_MUTED}; }}")
        update_row.addWidget(self.update_status_label, 1)
        opts_layout.addLayout(update_row)

        container_layout.addWidget(opts_group)

        container_layout.addStretch()

        # Bottom actions row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        info_version = QLabel("Stella Sora Launcher v0.9.8 • Giao diện Starlit Glass")
        info_version.setStyleSheet(f"QLabel {{ font-size: 12px; color: #5d819e; }}")
        bottom_row.addWidget(info_version)
        bottom_row.addStretch()

        btn_cancel = StarlitButton("Đóng", variant="secondary")
        btn_cancel.clicked.connect(self.reject)
        bottom_row.addWidget(btn_cancel)

        btn_save = StarlitButton("Lưu cài đặt", variant="primary")
        btn_save.clicked.connect(self._save_settings)
        bottom_row.addWidget(btn_save)

        container_layout.addLayout(bottom_row)

        main_layout.addWidget(container)

    def _load_current_values(self):
        saved_path = self.config_manager.get("game_path", "")
        self.path_input.setText(saved_path)
        self.chk_auto_detect.setChecked(self.config_manager.get("auto_detect_game", True))
        self.chk_reduced_motion.setChecked(self.config_manager.get("reduced_motion", False))
        self._validate_path(saved_path)

    def _browse_path(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Chọn thư mục cài đặt game Stella Sora",
            self.path_input.text() or "C:\\",
        )
        if directory:
            self.path_input.setText(directory)

    def _validate_path(self, path_str: str):
        if not path_str:
            self.path_status_label.setText("Chưa nhập đường dẫn.")
            self.path_status_label.setStyleSheet(f"QLabel {{ color: {Theme.TEXT_MUTED}; }}")
            return

        p = Path(path_str)
        if not p.is_dir():
            self.path_status_label.setText("Thư mục không tồn tại.")
            self.path_status_label.setStyleSheet(f"QLabel {{ color: {Theme.DANGER_RED}; }}")
            return

        exe_path = p / "StellaSora.exe"
        if exe_path.is_file():
            self.path_status_label.setText("✓ Đã tìm thấy tệp StellaSora.exe hợp lệ.")
            self.path_status_label.setStyleSheet(f"QLabel {{ color: {Theme.SUCCESS_GREEN}; }}")
        else:
            self.path_status_label.setText("⚠ Không tìm thấy StellaSora.exe trong thư mục này.")
            self.path_status_label.setStyleSheet(f"QLabel {{ color: {Theme.WARNING_AMBER}; }}")

    def _check_update(self):
        self.update_status_label.setText("Đang kiểm tra kết nối...")
        res = self.network_service.check_for_updates("0.9.8")
        self.update_status_label.setText(res.get("message", "Đã kiểm tra."))

    def _save_settings(self):
        new_path = self.path_input.text().strip()
        self.config_manager.set("game_path", new_path)
        self.config_manager.set("auto_detect_game", self.chk_auto_detect.isChecked())
        self.config_manager.set("reduced_motion", self.chk_reduced_motion.isChecked())
        self.config_manager.save()
        self.game_path_changed.emit(new_path)
        self.accept()
