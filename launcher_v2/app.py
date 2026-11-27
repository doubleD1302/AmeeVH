"""Pre-Qt entry point, CLI fast paths, crash sentinel, and GUI bootstrap for Launcher v2.0."""
from __future__ import annotations

import argparse
import faulthandler
import logging
import logging.handlers
import os
import sys
import traceback
from pathlib import Path
from typing import Any, IO, Optional

if not getattr(sys, 'frozen', False):
    _PKG_PARENT = str(Path(__file__).resolve().parents[1])
    if _PKG_PARENT not in sys.path:
        sys.path.insert(0, _PKG_PARENT)

_FAULT_LOG_HANDLE: Optional[IO[str]] = None


def _default_local_app_data_base() -> Path:
    return Path(os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or Path.home())


def _resolve_early_app_data(app_data_arg: Optional[Path] = None) -> Path:
    if app_data_arg is not None:
        return Path(app_data_arg)
    return _default_local_app_data_base() / 'StellaSora_VietHoa_Launcher'


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Stella Sora Việt Hóa launcher v2.0')
    parser.add_argument('--app-data-dir', type=Path, help='Explicit writable config/log/backup/cache directory')
    parser.add_argument('--resource-dir', type=Path, help='Explicit development resource override')
    parser.add_argument('--apply-update', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--smoke', action='store_true', help='Validate bootstrap and exit 0')
    parser.add_argument('--tls-check', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--safe-graphics', action='store_true', help='Force software OpenGL rendering')
    parser.add_argument('--tray', action='store_true', help='Start minimized in system tray to watch for game updates')
    parser.add_argument('--launch-game', action='store_true', help='Check for official updates before launching Stella Sora')
    return parser


def _close_native_faulthandler() -> None:
    global _FAULT_LOG_HANDLE
    fh = _FAULT_LOG_HANDLE
    _FAULT_LOG_HANDLE = None
    if fh is not None:
        try:
            faulthandler.disable()
        except Exception:  # noqa: BLE001
            pass
        try:
            fh.close()
        except OSError:
            pass


def _enable_native_faulthandler(app_data_dir: Path) -> Optional[IO[str]]:
    """Open native_crash.log and keep the handle open for the process lifetime."""
    global _FAULT_LOG_HANDLE
    _close_native_faulthandler()
    try:
        logs_dir = app_data_dir / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
        fh = (logs_dir / 'native_crash.log').open('a', encoding='utf-8')
        faulthandler.enable(file=fh, all_threads=True)
        _FAULT_LOG_HANDLE = fh
        return fh
    except OSError:
        return None


def _configure_win32_process() -> None:
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:  # noqa: BLE001
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:  # noqa: BLE001
            pass
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('stellasora.viethoa.launcher')
    except Exception:  # noqa: BLE001
        pass


def _safe_bool(value: Any, default: bool = False) -> bool:
    try:
        return bool(value)
    except Exception:  # noqa: BLE001
        return default


def prepare_graphics_mode(pm: Any, cm: Any, *, safe_graphics: bool = False) -> tuple[bool, bool, list[Exception]]:
    """Evaluate pre-Qt graphics compatibility and `.graphics_boot_pending` crash sentinel.

    Returns ``(software_rendering, sentinel_was_present, warnings)``.
    Must run BEFORE any ``PySide6`` import.
    """
    from launcher_v2.core.safety import InstallerError

    warnings: list[Exception] = []
    sentinel_path = Path(pm.graphics_sentinel_file)
    sentinel_triggered = sentinel_path.exists()
    safe_gfx_flag = _safe_bool(safe_graphics, False)
    try:
        cm_soft = _safe_bool(cm.get('graphics_mode') == 'software', False)
    except Exception:  # noqa: BLE001
        cm_soft = False
    software_rendering = bool(safe_gfx_flag or cm_soft or sentinel_triggered)

    if software_rendering:
        os.environ['QT_OPENGL'] = 'software'
        os.environ['QSG_RHI_BACKEND'] = 'software'
        if sentinel_triggered:
            if not _safe_bool(getattr(cm, '_corrupt', False), False):
                cm.set('graphics_mode', 'software')
                cm.save()
            warnings.append(
                InstallerError(
                    'Lần khởi chạy trước gặp sự cố đồ họa; đã chuyển sang chế độ tương thích phần mềm.',
                    'GPU_RENDER',
                )
            )

    return software_rendering, sentinel_triggered, warnings


def _write_graphics_sentinel(sentinel_path: Path) -> None:
    try:
        from datetime import datetime, timezone
        sentinel_path.parent.mkdir(parents=True, exist_ok=True)
        sentinel_path.write_text(
            f'pid={os.getpid()}\nutc={datetime.now(timezone.utc).isoformat()}\n',
            encoding='utf-8',
        )
    except OSError:
        pass


def _remove_graphics_sentinel(sentinel_path: Path) -> None:
    try:
        sentinel_path.unlink(missing_ok=True)
    except OSError:
        pass


def run_gui(
    pm: Any,
    cm: Any,
    software_rendering: bool,
    startup_warnings: list[Exception],
    *,
    sentinel_already_present: bool = False,
    start_in_tray: bool = False,
    launch_guard_notice: Optional[dict[str, Any]] = None,
) -> int:
    """Lazy-import PySide6 and launch the modular v2.0 UI shell."""
    from launcher_v2.core import tls
    from launcher_v2.core.config import LAUNCHER_VERSION
    from launcher_v2.core.safety import InstallerError

    use_software = _safe_bool(software_rendering, False)
    had_sentinel = _safe_bool(sentinel_already_present, False)
    sentinel_path = Path(pm.graphics_sentinel_file)
    _write_graphics_sentinel(sentinel_path)

    try:
        from PySide6.QtCore import QCoreApplication, Qt, QTimer
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtWidgets import QApplication
    except (ImportError, OSError) as exc:
        if not had_sentinel:
            _remove_graphics_sentinel(sentinel_path)
        raise InstallerError(f'Không nạp được thư viện giao diện Qt: {exc}', 'STARTUP_DLL') from exc

    entered_event_loop = False
    try:
        if use_software:
            try:
                QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)
            except Exception:  # noqa: BLE001
                pass

        try:
            QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        except Exception:  # noqa: BLE001
            pass

        app = QApplication(sys.argv)
        app.setApplicationName('StellaSora Launcher')
        app.setOrganizationName('StellaSora VietHoa')
        app.setApplicationVersion(LAUNCHER_VERSION)

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
            force=True,
        )

        try:
            tls.install()
        except Exception:  # noqa: BLE001
            logging.getLogger('launcher_v2').exception('Could not install the fallback CA bundle')

        # Lazy UI import so M4 CLI fast paths and pure-core imports never require launcher_v2.ui
        try:
            from launcher_v2.ui import app_controller as ui_controller_mod
        except (ImportError, OSError) as exc:
            raise InstallerError(f'Không nạp được giao diện launcher_v2.ui: {exc}', 'STARTUP_DLL') from exc

        controller = None
        win = None
        if hasattr(ui_controller_mod, 'launch_gui'):
            win = ui_controller_mod.launch_gui(
                app=app,
                path_manager=pm,
                config_manager=cm,
                software_rendering=use_software,
                startup_warnings=startup_warnings,
                start_in_tray=start_in_tray,
                launch_guard_notice=launch_guard_notice,
            )
        else:
            from launcher_v2.ui.main_shell import MainShell

            controller = ui_controller_mod.AppController(
                pm,
                cm,
                software_rendering=use_software,
                startup_warnings=startup_warnings,
            )
            win = MainShell(pm, cm, controller=controller)
            win.show()

        def _clear_sentinel() -> None:
            _remove_graphics_sentinel(sentinel_path)

        QTimer.singleShot(3000, _clear_sentinel)

        def _excepthook(exc_type, exc, tb) -> None:
            logging.getLogger('launcher_v2').critical('Unhandled exception', exc_info=(exc_type, exc, tb))
            if exc is not None and not isinstance(exc, (KeyboardInterrupt, SystemExit)):
                handler = getattr(win, 'show_unhandled', None) or getattr(controller, 'show_unhandled', None)
                if callable(handler):
                    QTimer.singleShot(0, lambda e=exc: handler(e))

        sys.excepthook = _excepthook
        entered_event_loop = True
        return int(app.exec())
    finally:
        if entered_event_loop or not had_sentinel:
            _remove_graphics_sentinel(sentinel_path)


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args, _ = parser.parse_known_args(argv)

    # 1. Strict Pre-Qt CLI fast paths (ZERO PySide6 imports)
    if args.smoke:
        if args.app_data_dir is not None or args.resource_dir is not None:
            from launcher_v2.core.config import ConfigManager, PathManager

            pm = PathManager(args.resource_dir, args.app_data_dir)
            ConfigManager(pm)
        print('OK: SMOKE TEST PASSED')
        return 0

    if args.tls_check:
        from launcher_v2.core import tls

        info_text = repr(tls.info())
        if sys.stdout is not None:
            enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
            safe_out = info_text.encode(enc, 'replace').decode(enc, 'replace')
            sys.stdout.write(safe_out + '\n')
        return 0

    if args.apply_update is not None:
        from launcher_v2.core.self_update import apply_job

        apply_job(args.apply_update)
        return 0

    # 2. Pre-Qt faulthandler -> <app_data_dir>/logs/native_crash.log
    early_app_data = _resolve_early_app_data(args.app_data_dir)
    _enable_native_faulthandler(early_app_data)

    # 3. Cleanup, non-destructive r02 migration, and config bootstrap (pure Python)
    from launcher_v2.core.config import ConfigManager, PathManager
    from launcher_v2.core.migration import migrate_from_r02_if_needed, migration_warning_error
    from launcher_v2.core.self_update import cleanup_all_update_artifacts

    pm = PathManager(args.resource_dir, args.app_data_dir)
    try:
        cleanup_all_update_artifacts(pm)
    except Exception:  # noqa: BLE001
        pass

    startup_warnings: list[Exception] = []
    try:
        mig_res = migrate_from_r02_if_needed(pm)
        mig_err = migration_warning_error(mig_res)
        if mig_err is not None:
            startup_warnings.append(mig_err)
    except Exception as exc:  # noqa: BLE001
        startup_warnings.append(exc)

    cm = ConfigManager(pm)

    # 3b. Pre-Qt `--launch-game` fast-path guard (ZERO PySide6 import when safe to launch)
    launch_guard_notice: Optional[dict[str, Any]] = None
    if args.launch_game:
        from launcher_v2.core import tls
        from launcher_v2.core.game_detection import GameDetector
        from launcher_v2.core.game_guard import evaluate_fast_launch_guard

        try:
            tls.install()
        except Exception:  # noqa: BLE001
            pass

        guard_res = evaluate_fast_launch_guard(pm, cm)
        action = guard_res.get('action')
        if action == 'launch':
            ok, _msg = GameDetector(pm.backup_root).launch(guard_res['game'])
            if ok:
                return 0
        elif action == 'already_running':
            return 0
        elif action == 'block':
            launch_guard_notice = dict(guard_res.get('notice') or {})
            launch_guard_notice['_launch_after_restore'] = True

    # 4. Pre-Qt graphics compatibility & `.graphics_boot_pending` sentinel check
    software_rendering, sentinel_triggered, gfx_warnings = prepare_graphics_mode(
        pm, cm, safe_graphics=bool(args.safe_graphics)
    )
    startup_warnings.extend(gfx_warnings)

    # 5. Win32 Per-Monitor V2 DPI awareness & AppUserModelID before PySide6 import
    _configure_win32_process()

    # 6. Enter Qt UI
    return run_gui(
        pm,
        cm,
        software_rendering,
        startup_warnings,
        sentinel_already_present=sentinel_triggered,
        start_in_tray=bool(args.tray) and launch_guard_notice is None,
        launch_guard_notice=launch_guard_notice,
    )


def _write_startup_error_log(early_dir: Path, text: str) -> Path:
    safe_text = str(text).encode('utf-8', 'replace').decode('utf-8')
    for candidate in (early_dir / 'logs' / 'startup_error.log', early_dir / 'startup_error.log'):
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_text(safe_text, encoding='utf-8', errors='replace')
            return candidate
        except (OSError, UnicodeError):
            continue
    return early_dir / 'logs' / 'startup_error.log'


def entry(argv: Optional[list[str]] = None) -> int:
    parsed_args, _ = _build_parser().parse_known_args(argv)
    is_cli_fast_path = bool(parsed_args.smoke or parsed_args.tls_check or parsed_args.apply_update is not None)
    early_app_data = _resolve_early_app_data(parsed_args.app_data_dir)

    try:
        return main(argv)
    except Exception as exc:  # noqa: BLE001
        try:
            exc_str = str(exc) if exc is not None else ''
        except Exception:  # noqa: BLE001
            exc_str = f'<{type(exc).__name__}>'
        try:
            error_tb = traceback.format_exc()
        except Exception:  # noqa: BLE001
            error_tb = f'{type(exc).__name__}: {exc_str}'
        try:
            log_path = _write_startup_error_log(early_app_data, error_tb)
        except Exception:  # noqa: BLE001
            log_path = early_app_data / 'logs' / 'startup_error.log'

        if is_cli_fast_path:
            try:
                if sys.stderr is not None:
                    enc = getattr(sys.stderr, 'encoding', None) or 'utf-8'
                    raw_msg = f'Launcher CLI error: {exc_str}\nLog: {log_path}\n'
                    safe_msg = raw_msg.encode(enc, 'replace').decode(enc, 'replace')
                    sys.stderr.write(safe_msg)
            except Exception:  # noqa: BLE001
                pass
            return 1

        shown = False
        try:
            from launcher_v2.core.config import PathManager
            from launcher_v2.core.error_report import ErrorContext, build_report, copy_text_native

            pm = None
            try:
                pm = PathManager(parsed_args.resource_dir, parsed_args.app_data_dir)
            except Exception:  # noqa: BLE001
                pass

            fallback_code = 'E-STARTUP-DLL' if isinstance(exc, (ImportError, OSError)) else 'E-INTERNAL'
            report = build_report(
                fallback_code,
                exc=exc,
                action='Khởi động launcher',
                ctx=ErrorContext(
                    action='Khởi động launcher',
                    operation='startup',
                    path_manager=pm,
                ),
                message=exc_str,
            )
            log_path = _write_startup_error_log(
                early_app_data,
                report.text + '\n\n--- Traceback đầy đủ ---\n' + error_tb,
            )

            if sys.platform == 'win32':
                import ctypes

                steps = '\n'.join(f'{i}. {step}' for i, step in enumerate(report.steps, 1))
                answer = ctypes.windll.user32.MessageBoxW(
                    None,
                    f'{report.title}\n\n{report.summary}\n\nCách xử lý:\n{steps}\n\n{report.code_line}\n\n'
                    'Bấm "Có" để sao chép toàn bộ thông tin lỗi (gửi cho người hỗ trợ), "Không" để đóng.\n'
                    f'Chi tiết cũng được lưu tại: {log_path}',
                    'Stella Sora Việt Hóa',
                    0x10 | 0x4,  # MB_ICONERROR | MB_YESNO
                )
                shown = True
                if answer == 6:  # IDYES
                    copy_text_native(report.text)
        except Exception:  # noqa: BLE001
            pass

        if not shown and sys.platform == 'win32':
            try:
                import ctypes

                ctypes.windll.user32.MessageBoxW(
                    None,
                    f'Launcher không mở được (E-STARTUP-DLL / E-INTERNAL). Chi tiết tại:\n{log_path}',
                    'Stella Sora Việt Hóa',
                    0x10,
                )
            except Exception:  # noqa: BLE001
                pass
        return 1
    finally:
        _close_native_faulthandler()


if __name__ == '__main__':
    sys.exit(entry())
