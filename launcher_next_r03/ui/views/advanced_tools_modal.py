"""Advanced Tools Modal: System Diagnostics and safe ADB discovery (View 06)."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from launcher_next_r03.core.config import PathManager
from launcher_next_r03.core.diagnostics import AdbBridge, DiagnosticsCollector
from launcher_next_r03.core.types import GameInfo
from launcher_next_r03.ui.components.glass_card import GlassCard
from launcher_next_r03.ui.components.starlit_button import StarlitButton
from launcher_next_r03.ui.theme import Theme


class AdvancedToolsModal(QDialog):
    """View 06: Diagnostics & safe ADB bridge tools."""

    def __init__(self, path_manager: PathManager, game_info: GameInfo, parent=None):
        super().__init__(parent)
        self.path_manager = path_manager
        self.game_info = game_info
        self.adb_bridge = AdbBridge()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(840, 600)
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
        title = QLabel("CÔNG CỤ NÂNG CAO & CHẨN ĐOÁN")
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

        # Tab Widget
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid rgba(31, 86, 138, 0.5);
                border-radius: 6px;
                background: rgba(6, 20, 38, 0.5);
                padding: 12px;
            }}
            QTabBar::tab {{
                background: rgba(16, 48, 86, 0.4);
                color: {Theme.TEXT_MUTED};
                border: 1px solid rgba(31, 86, 138, 0.3);
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background: rgba(30, 80, 138, 0.7);
                color: {Theme.PRIMARY_CYAN};
                border: 1px solid {Theme.PRIMARY_CYAN};
                border-bottom: none;
            }}
        """)

        # Tab 1: Diagnostics
        tab_diag = QWidget()
        diag_layout = QVBoxLayout(tab_diag)
        diag_layout.setContentsMargins(0, 0, 0, 0)
        diag_layout.setSpacing(10)

        self.diag_text = QPlainTextEdit()
        self.diag_text.setReadOnly(True)
        self.diag_text.setStyleSheet("""
            QPlainTextEdit {
                font-family: Consolas, monospace;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        diag_layout.addWidget(self.diag_text, 1)

        diag_actions = QHBoxLayout()
        btn_refresh_diag = StarlitButton("Làm mới chẩn đoán", variant="secondary")
        btn_refresh_diag.clicked.connect(self._run_diagnostics)
        diag_actions.addWidget(btn_refresh_diag)

        btn_copy_diag = StarlitButton("Sao chép vào Clipboard", variant="secondary")
        btn_copy_diag.clicked.connect(self._copy_diagnostics)
        diag_actions.addWidget(btn_copy_diag)
        diag_actions.addStretch()

        self.diag_status_label = QLabel("")
        self.diag_status_label.setStyleSheet(f"QLabel {{ color: {Theme.SUCCESS_GREEN}; font-size: 12px; }}")
        diag_actions.addWidget(self.diag_status_label)
        diag_layout.addLayout(diag_actions)

        tabs.addTab(tab_diag, "Chẩn đoán hệ thống")

        # Tab 2: ADB Bridge
        tab_adb = QWidget()
        adb_layout = QVBoxLayout(tab_adb)
        adb_layout.setContentsMargins(0, 0, 0, 0)
        adb_layout.setSpacing(10)

        self.adb_info_label = QLabel("Đang kiểm tra trình quản lý ADB...")
        self.adb_info_label.setStyleSheet(f"QLabel {{ font-size: 13px; color: {Theme.TEXT_WHITE}; }}")
        adb_layout.addWidget(self.adb_info_label)

        self.device_table = QTableWidget()
        self.device_table.setColumnCount(3)
        self.device_table.setHorizontalHeaderLabels(["Mã thiết bị (Serial)", "Trạng thái", "Chi tiết nhận diện"])
        self.device_table.horizontalHeader().setStretchLastSection(True)
        self.device_table.setStyleSheet(f"""
            QTableWidget {{
                background: rgba(6, 20, 38, 0.6);
                border: 1px solid rgba(31, 86, 138, 0.4);
                color: {Theme.TEXT_WHITE};
            }}
            QHeaderView::section {{
                background-color: rgba(16, 48, 86, 0.8);
                color: {Theme.PRIMARY_CYAN};
                font-weight: bold;
                border: 1px solid rgba(31, 86, 138, 0.3);
                padding: 6px;
            }}
        """)
        adb_layout.addWidget(self.device_table, 1)

        adb_actions = QHBoxLayout()
        btn_scan_devices = StarlitButton("Quét thiết bị / Giả lập", variant="secondary")
        btn_scan_devices.clicked.connect(self._scan_adb_devices)
        adb_actions.addWidget(btn_scan_devices)
        adb_actions.addStretch()

        adb_note = QLabel("Chế độ chỉ đọc an toàn. Không tự ý đẩy file vào máy ảo.")
        adb_note.setStyleSheet(f"QLabel {{ font-size: 12px; color: {Theme.TEXT_MUTED}; }}")
        adb_actions.addWidget(adb_note)
        adb_layout.addLayout(adb_actions)

        tabs.addTab(tab_adb, "Cầu nối ADB (MuMu / LDPlayer)")

        container_layout.addWidget(tabs, 1)
        main_layout.addWidget(container)

        self._run_diagnostics()
        self.adb_info_label.setText("Chọn Quét thiết bị để kiểm tra ADB (chỉ đọc).")
        recovery = StarlitButton("Phục hồi thao tác bị ngắt", variant="secondary")
        updater = StarlitButton("Kiểm tra cập nhật launcher", variant="secondary")
        recovery.clicked.connect(self._recover_operation)
        updater.clicked.connect(self._update_launcher)
        container_layout.addWidget(recovery)
        container_layout.addWidget(updater)

    def _run_diagnostics(self):
        report = DiagnosticsCollector.collect(self.path_manager, self.game_info)
        self.diag_text.setPlainText(report.to_text())
        self.diag_status_label.setText("Đã cập nhật.")

    def _copy_diagnostics(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.diag_text.toPlainText())
        self.diag_status_label.setText("Đã sao chép vào bộ nhớ tạm!")

    def _scan_adb_devices(self):
        if not self.adb_bridge.is_available():
            self.adb_info_label.setText("Không tìm thấy adb.exe trong hệ thống hoặc các trình giả lập phổ biến.")
            self.device_table.setRowCount(0)
            return

        self.adb_info_label.setText(f"ADB thực thi: {self.adb_bridge.adb_path}")
        devices = self.adb_bridge.list_devices()
        self.device_table.setRowCount(len(devices))

        for row, dev in enumerate(devices):
            self.device_table.setItem(row, 0, QTableWidgetItem(dev.get("serial", "")))
            self.device_table.setItem(row, 1, QTableWidgetItem(dev.get("state", "")))
            self.device_table.setItem(row, 2, QTableWidgetItem(dev.get("details", "")))

    def _recover_operation(self):
        parent=self.parentWidget();self.accept()
        if parent and hasattr(parent,'_recover'):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0,parent._recover)
    def _update_launcher(self):
        parent=self.parentWidget();self.accept()
        if parent and hasattr(parent,'_check_update'):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0,parent._check_update)
