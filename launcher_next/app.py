"""Application entry point for Stella Sora Launcher."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from launcher_next.core.config import ConfigManager, PathManager
from launcher_next.ui.assets import AssetManager
from launcher_next.ui.main_window import MainWindow
from launcher_next.ui.theme import Theme


def setup_logging(path_manager: PathManager):
    log_dir = path_manager.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "launcher.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(str(log_file), encoding="utf-8", mode="a"),
        ],
    )


def capture_all_screens(main_window: MainWindow, output_dir: Path):
    """Capture full fidelity PNG screenshots of all views for verification."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Overview Screen (View 00)
    main_window.repaint()
    QApplication.processEvents()
    pix = main_window.grab()
    pix.save(str(output_dir / "00_overview.png"), "PNG")
    logging.info("Saved screenshot: 00_overview.png")

    # Helper to capture dialogs
    def snap_dialog(dialog, filename: str):
        dialog.show()
        QApplication.processEvents()
        time.sleep(0.05)
        d_pix = dialog.grab()
        d_pix.save(str(output_dir / filename), "PNG")
        logging.info(f"Saved screenshot: {filename}")
        dialog.close()
        QApplication.processEvents()

    # 2. Notifications Modal (View 01)
    from launcher_next.ui.views.notifications_modal import NotificationsModal
    dlg_notif = NotificationsModal(main_window.notifications, main_window)
    snap_dialog(dlg_notif, "01_notifications.png")

    # 3. Guide Modal (View 02)
    from launcher_next.ui.views.guide_modal import GuideModal
    dlg_guide = GuideModal(main_window)
    snap_dialog(dlg_guide, "02_guide.png")

    # 4. Support Modal (View 03)
    from launcher_next.ui.views.support_modal import SupportModal
    data = main_window.network_service.get_supporter_data()
    dlg_support = SupportModal(data, main_window)
    snap_dialog(dlg_support, "03_support.png")

    # 5. Settings Modal (View 04)
    from launcher_next.ui.views.settings_modal import SettingsModal
    dlg_settings = SettingsModal(main_window.config_manager, main_window.network_service, main_window)
    snap_dialog(dlg_settings, "04_settings.png")

    # 6. Confirmation Dialog (View 05)
    from launcher_next.ui.views.confirmation_dialog import ConfirmationDialog
    dlg_confirm = ConfirmationDialog(
        title="XÁC NHẬN KHÔI PHỤC GỐC",
        message="Bạn có chắc chắn muốn khôi phục tệp game gốc nguyên trạng?",
        confirm_label="Khôi phục",
        is_danger=True,
        parent=main_window,
    )
    snap_dialog(dlg_confirm, "05_confirmation.png")

    # 7. Advanced Tools Modal (View 06)
    from launcher_next.ui.views.advanced_tools_modal import AdvancedToolsModal
    dlg_tools = AdvancedToolsModal(main_window.path_manager, main_window.current_game_info, main_window)
    snap_dialog(dlg_tools, "06_advanced_tools.png")


def main():
    parser = argparse.ArgumentParser(description="Stella Sora Launcher (Starlit Glass)")
    parser.add_argument("--smoke", action="store_true", help="Run automated GUI smoke test and exit cleanly")
    parser.add_argument("--screenshot-all", type=str, help="Capture screenshots of all views to directory and exit")
    parser.add_argument("--resource-dir", type=str, help="Custom resource directory override")
    parser.add_argument("--app-data-dir", type=str, help="Custom app data directory override")
    args = parser.parse_args()

    # High DPI
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("StellaSora_Launcher")
    app.setOrganizationName("StellaSora_VietHoa")

    # Init Managers
    res_dir = Path(args.resource_dir) if args.resource_dir else None
    app_data_dir = Path(args.app_data_dir) if args.app_data_dir else None

    path_manager = PathManager(resource_dir=res_dir, app_data_dir=app_data_dir)
    config_manager = ConfigManager(path_manager)
    setup_logging(path_manager)

    AssetManager.initialize(path_manager.resource_dir)
    app.setStyleSheet(Theme.get_application_stylesheet())
    app.setWindowIcon(AssetManager.get().get_app_icon())

    main_win = MainWindow(path_manager, config_manager)
    main_win.show()

    if args.screenshot_all:
        out_dir = Path(args.screenshot_all)
        # Give window a moment to layout and render
        QTimer.singleShot(200, lambda: [capture_all_screens(main_win, out_dir), app.quit()])
        return app.exec()

    if args.smoke:
        # Verify startup and close cleanly after 500ms
        logging.info("Smoke test: Window launched successfully.")
        QTimer.singleShot(500, app.quit)
        return app.exec()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
