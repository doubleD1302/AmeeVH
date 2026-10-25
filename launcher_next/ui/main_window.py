"""Main application window for Stella Sora Launcher (Starlit Glass)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QPoint, QSize, Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from launcher_next.core.config import ConfigManager, PathManager
from launcher_next.core.game_detection import GameDetector
from launcher_next.core.installer import PatchInstaller
from launcher_next.core.network import NetworkService
from launcher_next.core.rollback import RollbackEngine
from launcher_next.core.types import GameInfo, NotificationItem, OperationEvent, OperationPhase
from launcher_next.ui.assets import AssetManager
from launcher_next.ui.components.title_bar import TitleBar
from launcher_next.ui.theme import Theme
from launcher_next.ui.views.advanced_tools_modal import AdvancedToolsModal
from launcher_next.ui.views.confirmation_dialog import ConfirmationDialog
from launcher_next.ui.views.guide_modal import GuideModal
from launcher_next.ui.views.notifications_modal import NotificationsModal
from launcher_next.ui.views.overview_view import OverviewView
from launcher_next.ui.views.settings_modal import SettingsModal
from launcher_next.ui.views.support_modal import SupportModal

logger = logging.getLogger("launcher.main_window")


class AsyncOperationWorker(QThread):
    """Background worker for long-running install and rollback tasks."""

    event_emitted = Signal(OperationEvent)
    finished = Signal(bool, str)

    def __init__(self, target_callable: Callable, *args, **kwargs):
        super().__init__()
        self.target_callable = target_callable
        self.args = args
        self.kwargs = kwargs

    def run(self):
        def callback(event: OperationEvent):
            self.event_emitted.emit(event)

        try:
            # Inject callback into kwargs
            self.kwargs["event_cb"] = callback
            res = self.target_callable(*self.args, **self.kwargs)
            self.finished.emit(True, "Hoàn tất thành công.")
        except Exception as e:
            logger.exception("Async operation worker crashed")
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """Frameless Starlit Glass Main Window."""

    def __init__(self, path_manager: PathManager, config_manager: ConfigManager):
        super().__init__()
        self.path_manager = path_manager
        self.config_manager = config_manager
        self.network_service = NetworkService()
        self.active_worker: Optional[AsyncOperationWorker] = None
        self.current_game_info = GameInfo()

        self._init_window()
        self._init_ui()
        self._load_data()
        self._refresh_game_status()

    def _init_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setWindowTitle("Stella Sora - Bản Việt Hóa")
        self.setWindowIcon(AssetManager.get().get_app_icon())

        # Base canvas dimensions per UI Spec
        self.resize(1280, 860)
        self.setMinimumSize(1024, 680)

    def _init_ui(self):
        # Central root widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        root_layout = QVBoxLayout(self.central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Frameless Title Bar
        self.title_bar = TitleBar(self)
        self.title_bar.navigate_requested.connect(self._handle_navigation)
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.close_requested.connect(self.close)
        root_layout.addWidget(self.title_bar)

        # Overview View (Main Dashboard)
        self.overview_view = OverviewView(self)
        self.overview_view.install_requested.connect(self._on_install_clicked)
        self.overview_view.rollback_requested.connect(self._on_rollback_clicked)
        self.overview_view.launch_requested.connect(self._on_launch_clicked)
        self.overview_view.view_notifications_requested.connect(lambda: self._handle_navigation("notifications"))
        root_layout.addWidget(self.overview_view, 1)

    def _load_data(self):
        # Notifications
        notif_file = self.path_manager.resource_dir / "resources" / "ui" / "notifications.json"
        self.notifications = self.network_service.fetch_notifications(str(notif_file))
        if self.notifications:
            self.overview_view.update_notification(self.notifications[0])

    def _refresh_game_status(self):
        configured_path = self.config_manager.get("game_path", "")
        detector = GameDetector(self.path_manager.backup_root)
        self.current_game_info = detector.detect_info(configured_path)

        # Update config if auto-detected and not configured
        if self.current_game_info.installed and not configured_path and self.current_game_info.game_path:
            self.config_manager.set("game_path", str(self.current_game_info.game_path))
            self.config_manager.save()

        is_patched = self.path_manager.receipt_file.is_file()
        self.overview_view.update_game_status(self.current_game_info, is_patched)

    def _handle_navigation(self, destination: str):
        if destination == "overview":
            self.title_bar.set_active_tab("overview")
        elif destination == "notifications":
            modal = NotificationsModal(self.notifications, self)
            modal.exec()
            self.title_bar.set_active_tab("overview")
        elif destination == "guide":
            modal = GuideModal(self)
            modal.exec()
            self.title_bar.set_active_tab("overview")
        elif destination == "support":
            data = self.network_service.get_supporter_data()
            modal = SupportModal(data, self)
            modal.exec()
            self.title_bar.set_active_tab("overview")
        elif destination == "tools":
            modal = AdvancedToolsModal(self.path_manager, self.current_game_info, self)
            modal.exec()
            self.title_bar.set_active_tab("overview")
        elif destination == "settings":
            modal = SettingsModal(self.config_manager, self.network_service, self)
            modal.game_path_changed.connect(lambda _: self._refresh_game_status())
            modal.exec()
            self.title_bar.set_active_tab("overview")

    def _on_install_clicked(self):
        if not self.current_game_info.installed or not self.current_game_info.game_path:
            return

        if self.current_game_info.is_running:
            return

        installer = PatchInstaller(self.path_manager.backup_root, self.path_manager.journals_dir)
        patch_dir = self.path_manager.patch_store_dir
        if not patch_dir.is_dir():
            # If no patch store folder found, warn user
            self.overview_view.show_progress(True, "Không tìm thấy thư mục tệp Việt Hóa (Patch Store).", 0)
            return

        self.active_worker = AsyncOperationWorker(
            installer.install,
            self.current_game_info.game_path,
            patch_dir,
        )
        self.active_worker.event_emitted.connect(self.overview_view.handle_operation_event)
        self.active_worker.finished.connect(self._on_operation_finished)
        self.active_worker.start()

    def _on_rollback_clicked(self):
        if not self.current_game_info.installed or not self.current_game_info.game_path:
            return

        if self.current_game_info.is_running:
            return

        dialog = ConfirmationDialog(
            title="XÁC NHẬN KHÔI PHỤC GỐC",
            message=(
                "Bạn có chắc chắn muốn khôi phục tệp game gốc?\n\n"
                "Toàn bộ các tệp Việt Hóa sẽ được hoàn trả nguyên trạng từ bản sao lưu ban đầu. "
                "Quá trình này an toàn và có thể cài đặt lại bất cứ lúc nào."
            ),
            confirm_label="Khôi phục ngay",
            is_danger=True,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            engine = RollbackEngine(self.path_manager)
            self.active_worker = AsyncOperationWorker(
                engine.rollback,
                self.current_game_info.game_path,
            )
            self.active_worker.event_emitted.connect(self.overview_view.handle_operation_event)
            self.active_worker.finished.connect(self._on_operation_finished)
            self.active_worker.start()

    def _on_launch_clicked(self):
        if not self.current_game_info.installed:
            return
        detector = GameDetector(self.path_manager.backup_root)
        detector.launch(self.current_game_info)

    def _on_operation_finished(self, success: bool, message: str):
        self._refresh_game_status()
        self.active_worker = None

    def paintEvent(self, event):
        """Paint background artwork with darkening overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        bg_pixmap = AssetManager.get().get_background()
        if not bg_pixmap.isNull():
            # Scale background to cover window, keeping aspect ratio
            scaled_bg = bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Center crop
            x = (self.width() - scaled_bg.width()) // 2
            y = (self.height() - scaled_bg.height()) // 2
            painter.drawPixmap(x, y, scaled_bg)

        # Subtle dark gradient overlay to ensure UI cards pop and text is legible
        painter.fillRect(self.rect(), QColor(6, 24, 47, 110))
