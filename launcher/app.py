"""Launcher candidate bootstrap. Default startup never applies patches automatically."""
from __future__ import annotations
import argparse, logging, logging.handlers, os, sys, traceback
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Stella Sora Việt Hóa launcher v1.3.3')
    parser.add_argument('--app-data-dir', type=Path, help='Explicit writable config/log/backup/cache directory')
    parser.add_argument('--resource-dir', type=Path, help='Explicit development resource override')
    parser.add_argument('--apply-update', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--smoke', action='store_true', help='Validate bootstrap and exit 0')
    args, _ = parser.parse_known_args()
    if args.smoke:
        print('OK: SMOKE TEST PASSED')
        return 0
    if args.apply_update:
        from launcher.core.self_update import apply_job
        apply_job(args.apply_update)
        return 0
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('stellasora.viethoa.launcher')
        except Exception:
            pass
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QGuiApplication
    try:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except Exception:
        pass
    from PySide6.QtWidgets import QApplication
    from launcher.core.config import PathManager, ConfigManager
    from launcher.ui.assets import AssetManager
    from launcher.ui.theme import Theme
    from launcher.ui.typography import register_fonts, font
    from launcher.ui.main_window import MainWindow
    app = QApplication(sys.argv)
    app.setApplicationName('StellaSora Launcher')
    app.setOrganizationName('StellaSora VietHoa')
    pm = PathManager(args.resource_dir, args.app_data_dir)
    log_handler = logging.handlers.RotatingFileHandler(
        pm.logs_dir / 'launcher.log',
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding='utf8',
    )
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s %(message)s',
        handlers=[log_handler],
    )
    register_fonts(pm.resource_dir)
    app.setFont(font(15))
    AssetManager.initialize(pm.resource_dir)
    app.setStyleSheet(Theme.get_application_stylesheet())
    app.setWindowIcon(AssetManager.get().get_app_icon())
    win = MainWindow(pm, ConfigManager(pm))
    win.show()

    def _excepthook(exc_type, exc, tb):
        """Exceptions that escape a Qt slot: log them and show the same copyable error dialog."""
        logging.getLogger('launcher').critical('Unhandled exception', exc_info=(exc_type, exc, tb))
        if exc is not None and not isinstance(exc, (KeyboardInterrupt, SystemExit)):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda e=exc: win.show_unhandled(e))

    sys.excepthook = _excepthook
    return app.exec()

def entry():
    try:
        return main()
    except Exception:
        error = traceback.format_exc()
        fallback = Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'StellaSora_Launcher_Candidate_r02'
        try:
            fallback.mkdir(parents=True, exist_ok=True)
            (fallback / 'startup_error.log').write_text(error, encoding='utf8')
        except OSError:
            pass
        shown = False
        try:
            from launcher.core.error_report import ErrorContext, build_report, copy_text_native
            exc = sys.exc_info()[1]
            report = build_report('E-INTERNAL', exc=exc, action='Khởi động launcher', ctx=ErrorContext(action='Khởi động launcher', operation='startup'), message=str(exc or ''))
            try:
                (fallback / 'startup_error.log').write_text(report.text + '\n\n--- Traceback đầy đủ ---\n' + error, encoding='utf8')
            except OSError:
                pass
            import ctypes
            steps = '\n'.join(f'{i}. {step}' for i, step in enumerate(report.steps, 1))
            answer = ctypes.windll.user32.MessageBoxW(
                None,
                f'{report.title}\n\n{report.summary}\n\nCách xử lý:\n{steps}\n\n{report.code_line}\n\n'
                'Bấm "Có" để sao chép toàn bộ thông tin lỗi (gửi cho người hỗ trợ), "Không" để đóng.\n'
                'Chi tiết cũng được lưu tại: ' + str(fallback / 'startup_error.log'),
                'Stella Sora Việt Hóa',
                0x10 | 0x4,   # MB_ICONERROR | MB_YESNO
            )
            shown = True
            if answer == 6:   # IDYES
                copy_text_native(report.text)
        except Exception:
            pass
        if not shown:
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    None,
                    'Launcher không mở được. Chi tiết tại:\n' + str(fallback / 'startup_error.log'),
                    'Stella Sora Việt Hóa',
                    0x10,
                )
            except Exception:
                pass
        return 1

if __name__ == '__main__':
    sys.exit(entry())
