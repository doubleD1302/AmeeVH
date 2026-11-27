# -*- coding: utf-8 -*-
"""
AppController, AsyncOperationWorker, and launch_gui() entrypoint for Launcher v2.0.

Satisfies:
- app.py:224-231 launch_gui(...) contract (registers Be Vietnam Pro, sets font/QSS/icon,
  attaches controller + shell, shows shell, schedules initial loads, does NOT call app.exec())
- Thread-safe QueuedConnection signal bridging for 3-tier BackgroundSyncService & net_probe
- Zero 'QThread: Destroyed' on exit (unparented tracked workers + clean shutdown_workers)
- SUPPORT_DONATION_ENABLED=False -> SupportLockedDialog; True -> SupportScreen
- Full v1.3.4 functional parity + all 8 SmartErrorDialog quick_fix actions
"""
from __future__ import annotations

import hashlib
import inspect
import json
import logging
import os
import subprocess
import sys
import threading
import time
import uuid
import weakref
from pathlib import Path
from typing import Any, Callable, Optional

from PySide6.QtCore import QCoreApplication, QObject, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog

from ..core import config as core_config
from ..core.bg_sync import BackgroundFrame, BackgroundSyncService
from ..core.config import (
    DEFAULT_GITHUB_BRANCH,
    DEFAULT_GITHUB_REPO,
    LAUNCHER_VERSION,
    ConfigManager,
    PathManager,
    derived_github_endpoints,
)
from ..core.diagnostics import DiagnosticsCollector, is_process_admin, probe_dir_writability
from ..core.error_catalog import INTERNAL_MAP, classify_text, diagnose, lookup
from ..core.error_report import ErrorContext, ErrorReport, build_report, copy_text_native, new_report_id, redact
from ..core.game_detection import (
    GAME_EXE_NAME,
    GameDetector,
    find_all_potential_game_installations,
    find_game_exe_hint,
    is_game_process_running,
)
from ..core.game_guard import (
    GameLogWatcher,
    GameUpdateSignal,
    close_game_gracefully_or_force,
    minimize_game_windows,
    set_windows_autostart,
)
from ..core.installer import PatchInstaller
from ..core.net_probe import run_probe
from ..core.network import NetworkService
from ..core.official_resources import CancelledError, OfficialClient
from ..core.official_restore import check_official_update
from ..core.quick_fix import QuickFixAction
from ..core.rollback import RollbackEngine
from ..core.safety import InstallerError, manifest_sha256
from ..core.self_update import cleanup_update_artifacts, schedule_update
from ..core.shortcut import create_game_shortcut
from ..core.types import GameInfo, NotificationItem, OperationEvent, OperationPhase
from ..core.update_notice import (
    detect_new_publisher_version,
    newer,
    translation_state,
    version_parts,
)
from .dialogs import (
    ConfirmationDialog,
    GameSelectionDialog,
    InstallCompletedDialog,
    SmartErrorDialog,
    UpdateGuardDialog,
    UpdateNoticeDialog,
)
from .main_shell import MainShell
from .screens.tools_screen import purge_temp_cache
from .theme import FS_BODY, build_application_qss, nfc, register_fonts, ui_font
from .widgets import get_asset_renderer

try:
    from shiboken6 import isValid as _qt_is_valid
except ImportError:  # pragma: no cover
    def _qt_is_valid(_obj: object) -> bool:
        return True

logger = logging.getLogger("launcher_v2.ui.controller")

_WRITABILITY_ERROR_CODES = {
    "E-FILE-DENIED",
    "E-CFA-BLOCKED",
    "E-STORAGE",
    "E-VERIFY-WRITE",
    "E-BACKUP",
    "E-JOURNAL",
    "E-CONFIG-SAVE",
}

_ACTION_TITLES = {
    "install": "Cài Việt hoá",
    "rollback": "Khôi phục dữ liệu gốc",
    "verify": "Kiểm tra tệp",
    "launch": "Mở game",
    "scan": "Quét thư mục game",
    "select_root": "Chọn thư mục game",
    "discover": "Tìm game tự động",
    "self_update": "Kiểm tra cập nhật launcher",
    "apply_self_update": "Cập nhật launcher",
    "publisher_vanilla_restore": "Khôi phục dữ liệu gốc của nhà phát hành",
    "recover": "Phục hồi thao tác bị ngắt",
    "startup": "Khởi động launcher",
}


_NON_MUTATING_OPS = frozenset({"scan", "discover", "select_root", "launch"})
_ORPHANED_QTHREADS: set[Any] = set()
_ORPHAN_QTHREAD_LOCK = threading.Lock()


class AsyncOperationWorker(QThread):
    """Background QThread worker for cancellable launcher operations with error probing."""

    event_emitted = Signal(object)
    result_ready = Signal(str, bool, object)

    def __init__(
        self,
        op_id: str,
        target: Callable[..., Any],
        parent: QObject | None = None,
        *,
        probe_on_error: bool = True,
        writability_target: Path | str | None = None,
    ) -> None:
        super().__init__(parent)
        self.op_id = op_id
        self.op = op_id
        self.target = target
        self.probe_on_error = bool(probe_on_error)
        self.writability_target = Path(writability_target) if writability_target else None
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def _accepts_cancel_arg(self) -> bool:
        try:
            sig = inspect.signature(self.target)
            positional = [
                p
                for p in sig.parameters.values()
                if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            has_varargs = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in sig.parameters.values())
            return has_varargs or len(positional) >= 3
        except (TypeError, ValueError):
            return False

    def run(self) -> None:  # noqa: N802
        try:
            if self._accepts_cancel_arg():
                res = self.target(self.event_emitted.emit, self.op_id, self.cancel_event)
            else:
                res = self.target(self.event_emitted.emit, self.op_id)
            self.result_ready.emit(self.op_id, True, res)
        except Exception as exc:  # noqa: BLE001
            err_code = str(getattr(exc, "code", "") or "")
            diag = diagnose(exc)
            is_cancel = (
                err_code == "CANCELLED"
                or diag.code == "E-CANCELLED"
                or isinstance(exc, CancelledError)
            )
            if not is_cancel:
                logger.exception("Operation %s failed", self.op_id)
            payload: dict[str, Any] = {
                "message": str(exc),
                "error_code": err_code or "OPERATION_ERROR",
                "diagnosed_code": diag.code,
                "exc": exc,
            }
            if not is_cancel and self.probe_on_error and diag.info.network:
                try:
                    payload["probe"] = run_probe()
                except Exception:  # noqa: BLE001
                    logger.exception("Connectivity probe failed")
            if (
                not is_cancel
                and self.writability_target is not None
                and (diag.code in _WRITABILITY_ERROR_CODES or isinstance(exc, PermissionError))
            ):
                try:
                    payload["writability"] = probe_dir_writability(self.writability_target)
                except Exception:  # noqa: BLE001
                    pass
            self.result_ready.emit(self.op_id, False, payload)


class _OperationSignalBridge(QObject):
    """Unparented GUI-thread signal bridge for daemon-thread non-mutating probes."""

    event_emitted = Signal(object)
    result_ready = Signal(str, bool, object)
    finished = Signal()


class _DaemonOperationWorker:
    """Daemon-thread worker for non-mutating probes (scan/discover/select_root/launch).

    Avoids QThread so stalled I/O (e.g. GameDetector.detect_info) exits cleanly on
    MainShell.closeEvent without QThread::~QThread() 0xc0000409 aborts.
    """

    def __init__(
        self,
        op_id: str,
        target: Callable[..., Any],
        *,
        probe_on_error: bool = True,
        writability_target: Path | str | None = None,
    ) -> None:
        self.op_id = op_id
        self.op = op_id
        self.target = target
        self.probe_on_error = bool(probe_on_error)
        self.writability_target = Path(writability_target) if writability_target else None
        self.cancel_event = threading.Event()
        self.shutdown_event = threading.Event()
        self.bridge = _OperationSignalBridge()
        self._thread: Optional[threading.Thread] = None

    def cancel(self) -> None:
        self.cancel_event.set()

    def isRunning(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _accepts_cancel_arg(self) -> bool:
        try:
            sig = inspect.signature(self.target)
            positional = [
                p
                for p in sig.parameters.values()
                if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            ]
            has_varargs = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in sig.parameters.values())
            return has_varargs or len(positional) >= 3
        except (TypeError, ValueError):
            return False

    def start(self) -> None:
        bridge_ref = weakref.ref(self.bridge)
        cancel_ev = self.cancel_event
        shutdown_ev = self.shutdown_event
        op_id = self.op_id
        target = self.target
        accepts_cancel = self._accepts_cancel_arg()
        probe_on_error = self.probe_on_error
        writability_target = self.writability_target

        def _emit_event(evt: Any) -> None:
            if sys is None or sys.is_finalizing() or shutdown_ev.is_set():
                return
            br = bridge_ref()
            if br is not None and _qt_is_valid(br) and QCoreApplication.instance() is not None:
                try:
                    br.event_emitted.emit(evt)
                except RuntimeError:
                    pass

        def _runner() -> None:
            try:
                try:
                    if accepts_cancel:
                        res = target(_emit_event, op_id, cancel_ev)
                    else:
                        res = target(_emit_event, op_id)
                    if not (sys is None or sys.is_finalizing() or shutdown_ev.is_set()):
                        br = bridge_ref()
                        if br is not None and _qt_is_valid(br) and QCoreApplication.instance() is not None:
                            try:
                                br.result_ready.emit(op_id, True, res)
                            except RuntimeError:
                                pass
                except Exception as exc:  # noqa: BLE001
                    if not (sys is None or sys.is_finalizing() or shutdown_ev.is_set()):
                        err_code = str(getattr(exc, "code", "") or "")
                        diag = diagnose(exc)
                        is_cancel = (
                            err_code == "CANCELLED"
                            or diag.code == "E-CANCELLED"
                            or isinstance(exc, CancelledError)
                        )
                        if not is_cancel:
                            logger.exception("Operation %s failed", op_id)
                        payload: dict[str, Any] = {
                            "message": str(exc),
                            "error_code": err_code or "OPERATION_ERROR",
                            "diagnosed_code": diag.code,
                            "exc": exc,
                        }
                        if not is_cancel and probe_on_error and diag.info.network:
                            try:
                                payload["probe"] = run_probe()
                            except Exception:  # noqa: BLE001
                                logger.exception("Connectivity probe failed")
                        if (
                            not is_cancel
                            and writability_target is not None
                            and (diag.code in _WRITABILITY_ERROR_CODES or isinstance(exc, PermissionError))
                        ):
                            try:
                                payload["writability"] = probe_dir_writability(writability_target)
                            except Exception:  # noqa: BLE001
                                pass
                        br = bridge_ref()
                        if br is not None and _qt_is_valid(br) and QCoreApplication.instance() is not None:
                            try:
                                br.result_ready.emit(op_id, False, payload)
                            except RuntimeError:
                                pass
            finally:
                if not (sys is None or sys.is_finalizing() or shutdown_ev.is_set()):
                    br = bridge_ref()
                    if br is not None and _qt_is_valid(br) and QCoreApplication.instance() is not None:
                        try:
                            br.finished.emit()
                        except RuntimeError:
                            pass

        self._thread = threading.Thread(
            target=_runner,
            name=f"launcher_v2_probe_{op_id[:8]}",
            daemon=True,
        )
        self._thread.start()


def _detect_game_snapshot(backup_root: Path, raw_path: str, auto_detect: bool) -> GameInfo:
    raw = raw_path
    if not raw:
        if not auto_detect:
            return GameInfo()
        found = find_all_potential_game_installations()
        if not found:
            return GameInfo()
        raw = next(
            (
                item["path"]
                for item in found
                if (Path(item["path"]) / ".vietnamese_patch_receipt.json").is_file()
            ),
            found[0]["path"],
        )
    return GameDetector(backup_root).detect_info(raw)


def _terminate_game_process_by_path(expected_game_root: Optional[Path]) -> tuple[bool, str]:
    """Close verified StellaSora.exe process cleanly (WM_CLOSE) with TerminateProcess/taskkill fallback."""
    return close_game_gracefully_or_force(expected_game_root, wait_seconds=2.5)


class AppController(QObject):
    """Coordinates Core services, background workers, MainShell navigation, and Porcelain dialogs."""

    bg_frame_changed = Signal(object)
    game_info_changed = Signal(object, bool)
    github_sync_changed = Signal(object)
    translation_state_changed = Signal(object)
    official_update_changed = Signal(object)
    notifications_changed = Signal(list)
    operation_started = Signal(str, str)
    operation_progress = Signal(object)
    operation_finished = Signal(str, bool, object)
    toast_requested = Signal(str, str)
    busy_changed = Signal(bool)

    _bg_raw_signal = Signal(object)
    _sync_thread_done_signal = Signal(str, bool, object)
    _official_thread_done_signal = Signal(bool, object)
    _probe_ready_signal = Signal(object, object)

    def __init__(
        self,
        path_manager: PathManager,
        config_manager: ConfigManager,
        *,
        software_rendering: bool = False,
        startup_warnings: Optional[list[Exception]] = None,
        start_in_tray: bool = False,
        launch_guard_notice: Optional[dict[str, Any]] = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.pm = path_manager
        self.cm = config_manager
        self.software_rendering = bool(software_rendering)
        self.startup_warnings: list[Exception] = list(startup_warnings or [])
        self._start_in_tray: bool = bool(start_in_tray)
        self._pending_launch_guard_notice: Optional[dict[str, Any]] = (
            dict(launch_guard_notice) if launch_guard_notice else None
        )

        self.shell: Optional[MainShell] = None
        self._alive: bool = True
        self._closing: bool = False
        self._showing_unhandled: bool = False

        self.bg_service = BackgroundSyncService(
            self.pm.app_data_dir,
            self.pm.resource_dir,
            reduced_motion=bool(self.cm.get("reduced_motion", False)),
        )
        self.current_bg_frame: BackgroundFrame = self.bg_service.load_initial()

        self.current_game_info = GameInfo()
        self.notifications: list[NotificationItem] = []

        self.active_worker: Optional[Any] = None
        self.active_operation_id: Optional[str] = None
        self.operation_kind: str = ""
        self._tracked_qthreads: set[AsyncOperationWorker] = set()
        self._tracked_daemon_workers: set[_DaemonOperationWorker] = set()
        self._bg_sync_running: bool = False
        self._official_running: bool = False

        self._pending_sync: bool = False
        self._pending_discoveries: Optional[list[dict]] = None
        self._pending_post_op_modal: bool = False
        self._pending_create_shortcut: bool = bool(self.cm.get("create_desktop_shortcut", True))
        self._manual_translation_check: bool = False
        self._manual_translation_next: bool = False
        self._notice_seen: set[str] = set()
        self._official_update: Optional[dict] = (
            dict(launch_guard_notice) if launch_guard_notice else None
        )
        self._official_checked_at: float = 0.0
        self._official_prompted: set[str] = set()
        self._log_watcher = GameLogWatcher()
        self._guard_alerted_fingerprints: set[str] = set()
        self._guard_dialog_open: bool = False
        self._close_after_worker: bool = False
        self._last_progress_message: str = ""
        self._last_report: Optional[ErrorReport] = None
        self._github_sync_state: dict[str, Any] = {"message": "Chưa đồng bộ GitHub.", "fresh": False}
        self._channel: dict[str, Any] = {}
        self._channel_error: str = ""
        self._github_identity: Optional[str] = None
        self.network_service = NetworkService()

        # Thread-safe Qt signal connections
        self._bg_raw_signal.connect(self._on_bg_frame_ready, Qt.ConnectionType.QueuedConnection)
        self._sync_thread_done_signal.connect(self._background_finish, Qt.ConnectionType.QueuedConnection)
        self._official_thread_done_signal.connect(self._official_check_finished, Qt.ConnectionType.QueuedConnection)
        self._probe_ready_signal.connect(self._on_async_probe_ready, Qt.ConnectionType.QueuedConnection)

        self._configure_network()

        # Periodic timers (stopped cleanly on shutdown; weakref slots prevent GC cycles)
        self_ref = weakref.ref(self)

        def _on_release_tick() -> None:
            c = self_ref()
            if c is not None and c._alive and _qt_is_valid(c):
                c.sync_github(automatic=True)
                c._start_official_check()

        def _on_proc_tick() -> None:
            c = self_ref()
            if c is not None and c._alive and _qt_is_valid(c):
                c._poll_game_running()

        def _on_snooze_tick() -> None:
            c = self_ref()
            if c is not None and c._alive and _qt_is_valid(c):
                c._maybe_show_release_notice()

        self._release_timer = QTimer(self)
        self._release_timer.setInterval(30 * 60 * 1000)
        self._release_timer.timeout.connect(_on_release_tick)

        self._proc_timer = QTimer(self)
        self._proc_timer.setInterval(1500)
        self._proc_timer.timeout.connect(_on_proc_tick)

        self._snooze_timer = QTimer(self)
        self._snooze_timer.setSingleShot(True)
        self._snooze_timer.timeout.connect(_on_snooze_tick)

        app_inst = QCoreApplication.instance()
        if app_inst is not None:

            def _on_quit() -> None:
                ctrl = self_ref()
                if ctrl is not None and _qt_is_valid(ctrl):
                    ctrl.shutdown_workers()

            app_inst.aboutToQuit.connect(_on_quit)

    def attach_shell(self, shell: MainShell) -> None:
        self.shell = shell
        shell.set_controller(self)

        self_ref = weakref.ref(self)
        shell_ref = weakref.ref(shell)

        ov = shell.overview_screen
        ov.install_requested.connect(self.install_patch)
        ov.launch_requested.connect(self.launch_game)
        ov.verify_requested.connect(self.verify_files)
        ov.rollback_requested.connect(self.rollback_official)
        ov.check_updates_requested.connect(self.check_translation_version)
        ov.cancel_operation_requested.connect(self.cancel_active_operation)
        ov.detect_games_requested.connect(self.auto_detect_game)
        ov.browse_game_requested.connect(self.browse_game_folder)
        ov.open_notifications_requested.connect(self.open_notifications)
        ov.open_error_requested.connect(self._explain_blocker_code)
        ov.official_restore_requested.connect(self._on_overview_official_restore)
        ov.support_requested.connect(self.open_support)
        ov.path_copied.connect(
            lambda _p, r=self_ref: (
                r().show_toast("Đã sao chép đường dẫn thư mục game.", "info")
                if r() is not None and _qt_is_valid(r())
                else None
            )
        )
        # Note: PathSelector._on_open_folder() already calls os.startfile(target),
        # so do NOT duplicate os.startfile on ov.open_folder_requested.

        nt = shell.notifications_screen
        nt.open_guide_requested.connect(
            lambda r=shell_ref: (
                r().navigate_to("guide") if r() is not None and _qt_is_valid(r()) else None
            )
        )
        nt.toast_requested.connect(self.show_toast)

        st = shell.settings_screen
        st.browse_game_requested.connect(self.browse_game_folder)
        st.save_and_sync_requested.connect(self.on_settings_saved)
        st.reset_defaults_requested.connect(self.on_settings_reset)
        st.preserve_corrupt_requested.connect(self.on_corrupt_preserved)
        st.reduced_motion_toggled.connect(self._on_reduced_motion_changed)
        st.auto_sync_bg_toggled.connect(self._on_auto_sync_bg_changed)
        st.error_raised.connect(self._on_screen_error_raised)
        st.toast_requested.connect(self.show_toast)

        tl = shell.tools_screen
        tl.official_check_requested.connect(
            lambda r=self_ref: (
                r()._start_official_check(force=True, manual=True)
                if r() is not None and _qt_is_valid(r())
                else None
            )
        )
        tl.official_restore_requested.connect(self.rollback_official)
        tl.verify_requested.connect(self.verify_files)
        tl.recover_requested.connect(self.recover_journals)
        tl.create_shortcut_requested.connect(self.create_shortcut_now)
        tl.clean_temp_requested.connect(self.clean_temp_cache)
        tl.copy_diagnostics_requested.connect(self.copy_diagnostics_report)
        tl.toast_requested.connect(self.show_toast)

        self.toast_requested.connect(shell.show_toast)
        shell.set_background_frame(self.current_bg_frame)
        self._apply_game_info(self.current_game_info)

    def is_busy(self) -> bool:
        return self.active_worker is not None

    def is_mutating_busy(self) -> bool:
        return self.active_worker is not None and self.operation_kind not in _NON_MUTATING_OPS

    def defer_close_for_background(self) -> bool:
        """Background sync/official checks use daemon threads and do not block window close."""
        return False

    def shutdown_workers(self) -> None:
        self._closing = True
        self._alive = False
        self._pending_post_op_modal = False
        self._pending_discoveries = None
        for timer in (self._release_timer, self._proc_timer, self._snooze_timer):
            try:
                if _qt_is_valid(timer):
                    timer.stop()
            except RuntimeError:
                pass

        self.active_worker = None
        self.active_operation_id = None

        for dw in list(self._tracked_daemon_workers):
            self._tracked_daemon_workers.discard(dw)
            try:
                dw.shutdown_event.set()
                dw.cancel()
            except Exception:  # noqa: BLE001
                pass
            br = getattr(dw, "bridge", None)
            if br is not None and _qt_is_valid(br):
                for sig_name in ("event_emitted", "result_ready", "finished"):
                    try:
                        getattr(br, sig_name).disconnect()
                    except (RuntimeError, TypeError):
                        pass
                try:
                    br.deleteLater()
                except RuntimeError:
                    pass

        for w in list(self._tracked_qthreads):
            self._tracked_qthreads.discard(w)
            if not _qt_is_valid(w):
                continue
            try:
                w.cancel()
            except RuntimeError:
                pass
            for sig_name in ("event_emitted", "result_ready"):
                try:
                    getattr(w, sig_name).disconnect()
                except (RuntimeError, TypeError):
                    pass
            try:
                w.quit()
                if w.isRunning():
                    w.wait(3000)
            except RuntimeError:
                continue
            if _qt_is_valid(w) and w.isRunning():
                # Never clear/destroy a still-running QThread (QThread::~QThread aborts 0xc0000409)
                with _ORPHAN_QTHREAD_LOCK:
                    _ORPHANED_QTHREADS.add(w)
                w_ref = weakref.ref(w)

                def _cleanup_orphan() -> None:
                    obj = w_ref()
                    if obj is not None:
                        with _ORPHAN_QTHREAD_LOCK:
                            _ORPHANED_QTHREADS.discard(obj)
                        if _qt_is_valid(obj):
                            try:
                                obj.deleteLater()
                            except RuntimeError:
                                pass

                try:
                    w.finished.connect(_cleanup_orphan, Qt.ConnectionType.QueuedConnection)
                except RuntimeError:
                    pass
            else:
                try:
                    w.finished.disconnect()
                except (RuntimeError, TypeError):
                    pass
                if _qt_is_valid(w):
                    try:
                        w.deleteLater()
                    except RuntimeError:
                        pass

    def show_toast(self, message: str, tone: str = "info") -> None:
        if self.shell is not None and _qt_is_valid(self.shell):
            self.shell.show_toast(message, tone=tone)

    # ---------------- Initial Load & 3-Tier Background Sync ----------------

    def start_initial_loads(self) -> None:
        if not self._alive:
            return
        try:
            cleanup_update_artifacts(self.pm.exe_dir)
            cleanup_update_artifacts(self.pm.app_data_dir / "update_helper")
        except Exception:  # noqa: BLE001
            pass

        # Instant Tier 3 / cached frame + bundled notifications
        self.current_bg_frame = self.bg_service.load_initial()
        if self.shell is not None:
            self.shell.set_background_frame(self.current_bg_frame)
        self.bg_frame_changed.emit(self.current_bg_frame)

        self._load_bundled_notifications_initial()

        # Start timers once initial load begins
        self._release_timer.start()
        self._proc_timer.start()

        # Non-blocking Tier 1 -> Tier 2 -> Tier 3 background sync
        self._trigger_bg_sync()

        # Surface startup warnings cleanly after window has painted
        if self.startup_warnings or getattr(self.cm, "_corrupt", False):
            QTimer.singleShot(250, self._surface_startup_warnings)

        # Initial game detection & GitHub channel sync
        self._scan_game()
        self.sync_github(automatic=True)

    def _load_bundled_notifications_initial(self) -> None:
        fallback_path = self.pm.resource_dir / "notifications.json"
        if not fallback_path.is_file():
            return
        try:
            svc = NetworkService()
            items = svc.fetch_notifications(str(fallback_path))
            self._set_notifications(items, status=svc.notification_status or "bundled")
        except Exception:  # noqa: BLE001
            pass

    def _trigger_bg_sync(self) -> None:
        self_ref = weakref.ref(self)

        def _on_ready(frame: BackgroundFrame) -> None:
            ctrl = self_ref()
            if ctrl is not None and ctrl._alive and _qt_is_valid(ctrl):
                try:
                    ctrl._bg_raw_signal.emit(frame)
                except RuntimeError:
                    pass

        self.bg_service.sync_async(
            _on_ready,
            auto_sync_enabled=bool(self.cm.get("auto_sync_official_bg", True)),
            reduced_motion=bool(self.cm.get("reduced_motion", False)),
        )

    def _on_bg_frame_ready(self, frame: BackgroundFrame) -> None:
        if not self._alive or frame is None:
            return
        self.current_bg_frame = frame
        if self.shell is not None:
            self.shell.set_background_frame(frame)
        self.bg_frame_changed.emit(frame)
        if getattr(frame, "warning_code", None) == "E-BG-SYNC":
            logger.info("Background sync fell back to bundled master (E-BG-SYNC)")

    def _can_open_modal(self) -> bool:
        return bool(
            self._alive
            and not self._closing
            and _qt_is_valid(self)
            and self.shell is not None
            and _qt_is_valid(self.shell)
            and self.shell.isVisible()
            and self.shell._active_modal is None
            and not bool(getattr(self.shell, "_modal_stack", None))
        )

    def _surface_startup_warnings(self) -> None:
        if not self._alive or self._closing or not _qt_is_valid(self) or self.shell is None or not _qt_is_valid(self.shell):
            return
        warnings = list(self.startup_warnings)
        self.startup_warnings.clear()

        for warn in warnings:
            code = getattr(warn, "code", "")
            if code == "GPU_RENDER":
                self.show_toast("Đã bật chế độ đồ họa tương thích sau sự cố lần trước.", "warn")
            elif code == "MIGRATION":
                if self._can_open_modal():
                    self.show_error(
                        "Di trú dữ liệu từ v1.3.4",
                        code="E-MIGRATION",
                        exc=warn,
                        message=str(warn),
                    )
            else:
                if self._can_open_modal():
                    self.show_error("Cảnh báo khởi động", exc=warn, message=str(warn))

        if getattr(self.cm, "_corrupt", False) and self._can_open_modal():
            self.show_error(
                "Đọc cấu hình launcher",
                code="E-CONFIG-SAVE",
                message="Tệp config.json bị hỏng nên launcher giữ nguyên bản gốc và dùng cài đặt tạm an toàn.",
                extra={"tệp cấu hình": str(self.pm.config_file)},
            )

    # ---------------- Network Channel & GitHub Sync ----------------

    def _configure_network(self) -> bool:
        try:
            channel = self.cm.channel()
            self._channel_error = ""
        except (ValueError, TypeError) as exc:
            self._channel_error = str(exc)
            channel = {
                "repo": str(self.cm.get("github_repo", "")),
                "branch": str(self.cm.get("github_branch", "")),
                "release_url": None,
                "notifications_url": None,
                "manifest_url": None,
                "configuration_error": self._channel_error,
            }

        identity = json.dumps(channel, sort_keys=True, ensure_ascii=False)
        previous = self._github_identity
        self._github_identity = identity
        self._channel = channel
        if previous is not None and previous != identity:
            self.notifications = []
            if self.shell is not None:
                self.shell.overview_screen.set_notifications([])
                self.shell.notifications_screen.set_notifications([], status="bundled")
            self._github_sync_state = {
                "message": "Đã đổi kênh. Chưa đọc thông tin của nguồn mới.",
                "fresh": False,
            }
            self.github_sync_changed.emit(self._github_sync_state)

        cache_dir = (
            self.pm.app_data_dir
            / "network_cache"
            / hashlib.sha256(identity.encode("utf8")).hexdigest()[:16]
        )
        self.network_service = NetworkService(
            channel["release_url"],
            channel["notifications_url"],
            cache_dir,
        )
        if self._channel_error:
            self._github_sync_state = {
                "message": f"Nguồn GitHub chưa hợp lệ: {self._channel_error}. Mở Cài đặt để sửa tên kho hoặc nhánh.",
                "fresh": False,
                "configuration_error": self._channel_error,
            }
            self.github_sync_changed.emit(self._github_sync_state)
            self._set_titlebar_sync("Kênh chưa hợp lệ", "warn")
        return not bool(self._channel_error)

    def _set_titlebar_sync(self, text: str, tone: str) -> None:
        if self.shell is not None:
            self.shell.title_bar.set_sync_status(text, tone=tone)

    def _set_notifications(self, items: list[NotificationItem], status: str = "bundled") -> None:
        self.notifications = list(items or [])
        unread = sum(1 for it in self.notifications if getattr(it, "is_unread", False))
        if unread == 0 and self.notifications:
            unread = min(3, len(self.notifications))
        if self.shell is not None:
            self.shell.overview_screen.set_notifications(self.notifications)
            self.shell.notifications_screen.set_notifications(self.notifications, status=status)
            self.shell.nav_rail.set_unread_count(unread)
        self.notifications_changed.emit(self.notifications)

    def sync_github(self, automatic: bool = False) -> None:
        if not self._configure_network():
            self._pending_sync = False
            return
        if self._bg_sync_running:
            self._pending_sync = True
            return

        network = NetworkService(
            self.network_service.update_url,
            self.network_service.notifications_url,
            self.network_service.cache_dir,
            self.network_service.timeout,
        )
        identity = str(self._github_identity or "")
        manifest_url = self._channel["manifest_url"]
        check_launcher = not automatic or bool(self.cm.get("check_updates_on_start", True))
        default_notif = derived_github_endpoints(DEFAULT_GITHUB_REPO, DEFAULT_GITHUB_BRANCH)[
            "remote_notifications_url"
        ]
        fallback = (
            str(self.pm.resource_dir / "notifications.json")
            if network.notifications_url == default_notif
            else None
        )

        self._bg_sync_running = True
        self._set_titlebar_sync("Đang đồng bộ...", "busy")
        self._github_sync_state = {
            "message": "Đang đọc thông báo và bản phát hành từ GitHub...",
            "fresh": False,
        }
        self.github_sync_changed.emit(self._github_sync_state)

        self_ref = weakref.ref(self)

        def _worker() -> None:
            try:
                result = network.sync_channel(fallback, LAUNCHER_VERSION, manifest_url, check_launcher)
                result["source_identity"] = identity
                if result.get("release_status") != "online":
                    try:
                        result["probe"] = run_probe()
                    except Exception:  # noqa: BLE001
                        logger.exception("Connectivity probe failed")
                ok = True
                payload: Any = result
            except Exception as exc:  # noqa: BLE001
                ok = False
                payload = {"message": str(exc), "exc": exc}

            ctrl = self_ref()
            if ctrl is not None and ctrl._alive and _qt_is_valid(ctrl):
                try:
                    ctrl._sync_thread_done_signal.emit(identity, ok, payload)
                except RuntimeError:
                    pass

        threading.Thread(target=_worker, name="launcher_v2_github_sync", daemon=True).start()

    def _background_finish(self, identity: str, success: bool, result: dict[str, Any]) -> None:
        self._bg_sync_running = False
        if not self._alive:
            return
        if identity == self._github_identity:
            if not success:
                exc = result.get("exc")
                d = diagnose(exc) if exc is not None else None
                self._github_sync_state = {
                    "message": "Không đồng bộ được GitHub: " + str(result.get("message", "Lỗi kết nối.")),
                    "fresh": False,
                    "error_code": d.code if d else (classify_text(result.get("message", "")) or "E-NET"),
                    "error_detail": result.get("message", ""),
                }
                self._set_titlebar_sync("GitHub: Ngoại tuyến", "warn")
                if self.shell is not None:
                    self.shell.tools_screen.set_network_status(False)
            else:
                self._github_sync_state = result
                items = result.get("notifications", [])
                notif_status = str(result.get("notification_status") or "bundled")
                self._set_notifications(items, status=notif_status)
                self.network_service.notification_status = notif_status
                self.network_service.notification_message = str(result.get("notification_message") or "")
                self.network_service.notification_version = result.get("notification_version")
                self._record_release_observation(result)
                online_ok = result.get("release_status") == "online"
                self._set_titlebar_sync(
                    "GitHub: Sẵn sàng" if online_ok else "GitHub: Ngoại tuyến",
                    "ok" if online_ok else "warn",
                )
                if self.shell is not None:
                    self.shell.tools_screen.set_network_status(online_ok)

            self._refresh_translation_state()
            self.github_sync_changed.emit(self._github_sync_state)

            if self._manual_translation_check:
                self._manual_translation_check = False
                state = self._refresh_translation_state()
                message = state["message"]
                if self.cm.get("payload_path", ""):
                    message += "\nLauncher đang dùng gói cục bộ đã chọn để cài đặt."
                blocker = state.get("blocker_code")
                ctrl_ref = weakref.ref(self)
                if not success or (blocker and blocker != "E-NO-GAME-FOLDER"):
                    code = blocker or self._github_sync_state.get("error_code") or "E-NET"
                    detail = state.get("blocker_detail") or self._github_sync_state.get("error_detail") or ""
                    self._pending_post_op_modal = True
                    QTimer.singleShot(
                        0,
                        lambda r=ctrl_ref, c=code, d=detail: (
                            r()._show_manual_sync_error(c, d)
                            if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                            else None
                        ),
                    )
                else:
                    self._pending_post_op_modal = True
                    QTimer.singleShot(
                        0,
                        lambda r=ctrl_ref, m=message: (
                            r()._show_info_confirm("Kiểm tra phiên bản Việt hoá", m)
                            if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                            else None
                        ),
                    )
            else:
                ctrl_ref = weakref.ref(self)
                QTimer.singleShot(
                    1200,
                    lambda r=ctrl_ref: (
                        r()._maybe_show_release_notice()
                        if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                        else None
                    ),
                )

        if self._pending_sync:
            self._pending_sync = False
            if self._manual_translation_next:
                self._manual_translation_check = True
                self._manual_translation_next = False
            ctrl_ref = weakref.ref(self)
            QTimer.singleShot(
                0,
                lambda r=ctrl_ref: (
                    r().sync_github(automatic=not r()._manual_translation_check)
                    if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                    else None
                ),
            )

    def _show_manual_sync_error(self, code: str, detail: str) -> None:
        self._pending_post_op_modal = False
        if not self._can_open_modal():
            return
        self.show_error("Kiểm tra phiên bản Việt hoá", code=code, message=detail)

    def _show_info_confirm(self, title: str, message: str) -> None:
        self._pending_post_op_modal = False
        if not self._can_open_modal():
            return
        assert self.shell is not None
        dlg = ConfirmationDialog(
            title,
            message,
            confirm_label="Đã hiểu",
            cancel_label="Đóng",
            asset_renderer=self.shell._renderer,
            parent=self.shell,
        )
        dlg.btn_cancel.setVisible(False)
        self.shell.show_modal(dlg)

    # ---------------- Game Detection & Process Polling ----------------

    def _detected(self) -> GameInfo:
        return _detect_game_snapshot(
            self.pm.backup_root,
            self.cm.get("game_path", ""),
            bool(self.cm.get("auto_detect_game", True)),
        )

    def _apply_game_info(self, info: GameInfo) -> None:
        self.current_game_info = info
        has_pending = False
        if info and info.installed and info.game_path:
            try:
                has_pending = bool(self._engine().pending(info.game_path))
            except Exception:  # noqa: BLE001
                has_pending = False

        if self.shell is not None:
            self.shell.overview_screen.set_game_info(info, has_pending_recovery=has_pending)
            self.shell.overview_screen.set_official_notice(self._official_notice())
            self.shell.settings_screen.set_game_path(info.game_path if info.game_path else "")
            self.shell.tools_screen.set_game_info(info)
        self.game_info_changed.emit(info, has_pending)

    def _poll_game_running(self) -> None:
        if (
            not self._alive
            or self._closing
            or self.active_worker is not None
            or not self.current_game_info.installed
        ):
            return
        info = self.current_game_info
        was_running = bool(info.is_running)
        running = is_game_process_running()
        if running != was_running:
            info.is_running = running
            self._apply_game_info(info)
            self._refresh_translation_state()
            if running:
                # Player just opened Stella Sora (even outside launcher)
                self._guard_alerted_fingerprints.clear()
                if self._is_realtime_guard_active(info):
                    self._log_watcher.arm(game_info=info, from_end=True)
                    known_notice = self._official_notice()
                    if known_notice is not None:
                        self._trigger_realtime_update_guard(notice=known_notice)
                    self._start_official_check(force=True, manual=False, from_game_launch=True)
            else:
                self._log_watcher.disarm()

        if running and self._is_realtime_guard_active(info):
            if not self._log_watcher.is_armed:
                self._log_watcher.arm(game_info=info, from_end=True)
            sig = self._log_watcher.poll()
            if sig is not None:
                self._trigger_realtime_update_guard(signal=sig, notice=self._official_notice())

    def _is_realtime_guard_active(self, info: Optional[GameInfo] = None) -> bool:
        gi = info or self.current_game_info
        return bool(
            gi
            and gi.installed
            and (gi.installed_receipt or gi.has_vietnamese)
            and bool(self.cm.get("guard_watch_game_updates", True))
        )

    def _scan_game(self) -> None:
        if getattr(type(self), "_detected", None) is AppController._detected and "_detected" not in self.__dict__:
            backup_root = self.pm.backup_root
            raw_path = self.cm.get("game_path", "")
            auto_detect = bool(self.cm.get("auto_detect_game", True))
            self._start_operation(
                "scan",
                lambda cb, op, *, br=backup_root, rp=raw_path, ad=auto_detect: {
                    "game": _detect_game_snapshot(br, rp, ad)
                },
            )
        else:
            ctrl_ref = weakref.ref(self)

            def _scan_custom(cb, op):
                c = ctrl_ref()
                return {"game": c._detected() if c is not None else GameInfo()}

            self._start_operation("scan", _scan_custom)

    def auto_detect_game(self) -> None:
        if self.active_worker is not None:
            return
        self._start_operation("discover", lambda cb, op: {"installations": find_all_potential_game_installations()})

    def browse_game_folder(self) -> None:
        if self.active_worker is not None or self.shell is None:
            return
        start = str(self.current_game_info.game_path or "C:/")
        chosen = QFileDialog.getExistingDirectory(self.shell, nfc("Chọn thư mục có StellaSora.exe"), start)
        if chosen:
            self.select_game_root(chosen)

    def select_game_root(self, path: str | Path) -> None:
        backup_root = self.pm.backup_root
        self._start_operation(
            "select_root",
            lambda cb, op, *, br=backup_root, p=path: {"game": GameDetector(br).detect_info(p)},
        )

    def _choose_discovered(self, found: list[dict]) -> None:
        if not self._alive or self._closing or not _qt_is_valid(self) or self.active_worker is not None:
            return
        if not found:
            if self._can_open_modal():
                self.show_error("Tìm game tự động", code="E-GAME-NOT-FOUND")
            return
        if len(found) == 1:
            self.select_game_root(found[0]["path"])
            return
        if not self._can_open_modal():
            return
        assert self.shell is not None
        dlg = GameSelectionDialog(
            found,
            parent=self.shell,
            backup_root=self.pm.backup_root,
            asset_renderer=self.shell._renderer,
        )
        if self.shell.show_modal(dlg) == QDialog.DialogCode.Accepted and dlg.selected_path:
            self.select_game_root(dlg.selected_path)

    # ---------------- Foreground Worker Orchestration ----------------

    def _engine(self) -> PatchInstaller:
        return PatchInstaller(self.pm.backup_root, self.pm.journals_dir)

    def _start_operation(
        self,
        kind: str,
        target: Callable[..., Any],
        *,
        initial_message: str = "Đang xử lý...",
        probe_on_error: bool = True,
        writability_target: Path | str | None = None,
    ) -> bool:
        if self.active_worker is not None:
            return False
        op_id = uuid.uuid4().hex
        self.active_operation_id = op_id
        self.operation_kind = kind
        self._last_progress_message = initial_message

        if self.shell is not None and _qt_is_valid(self.shell):
            if kind in ("install", "rollback", "verify", "recover", "publisher_vanilla_restore", "apply_self_update"):
                self.shell.overview_screen.set_operation_active(
                    True, cancellable=True, initial_message=initial_message
                )
            else:
                self.shell.overview_screen._op_active = True
                self.shell.overview_screen._sync_action_states()

        self.operation_started.emit(kind, initial_message)
        self.busy_changed.emit(True)

        w_target = writability_target or (
            self.current_game_info.game_path if self.current_game_info.game_path else self.pm.app_data_dir
        )
        use_daemon = kind in _NON_MUTATING_OPS
        if use_daemon:
            worker: Any = _DaemonOperationWorker(
                op_id,
                target,
                probe_on_error=probe_on_error,
                writability_target=w_target,
            )
            self._tracked_daemon_workers.add(worker)
            sig_source: Any = worker.bridge
        else:
            worker = AsyncOperationWorker(
                op_id,
                target,
                parent=None,
                probe_on_error=probe_on_error,
                writability_target=w_target,
            )
            self._tracked_qthreads.add(worker)
            sig_source = worker

        self.active_worker = worker
        ctrl_ref = weakref.ref(self)
        worker_ref = weakref.ref(worker)

        def _on_evt(evt: Any) -> None:
            c = ctrl_ref()
            if c is not None and c._alive and _qt_is_valid(c):
                c._on_worker_event(evt)

        def _on_res(res_op_id: str, ok: bool, res: Any) -> None:
            c = ctrl_ref()
            if c is not None and c._alive and _qt_is_valid(c):
                c._on_worker_finish(res_op_id, ok, res)

        def _on_done() -> None:
            c = ctrl_ref()
            w = worker_ref()
            if c is not None and _qt_is_valid(c):
                c._release_worker(w)
            elif w is not None:
                if isinstance(w, _DaemonOperationWorker):
                    if _qt_is_valid(w.bridge):
                        w.bridge.deleteLater()
                elif _qt_is_valid(w):
                    w.deleteLater()

        sig_source.event_emitted.connect(_on_evt, Qt.ConnectionType.QueuedConnection)
        sig_source.result_ready.connect(_on_res, Qt.ConnectionType.QueuedConnection)
        sig_source.finished.connect(_on_done, Qt.ConnectionType.QueuedConnection)
        worker.start()
        return True

    def cancel_active_operation(self) -> None:
        if self.active_worker is not None:
            self.active_worker.cancel()
            self.show_toast("Đang hủy thao tác...", "warn")

    def _on_worker_event(self, evt: OperationEvent) -> None:
        if not self._alive or not _qt_is_valid(self) or evt.operation_id != self.active_operation_id:
            return
        self._last_progress_message = evt.message or ""
        if self.shell is not None and _qt_is_valid(self.shell):
            self.shell.overview_screen.set_operation_event(evt)
        self.operation_progress.emit(evt)

    def _release_worker(self, worker: Any) -> None:
        try:
            if worker is not None:
                if isinstance(worker, _DaemonOperationWorker):
                    self._tracked_daemon_workers.discard(worker)
                    if _qt_is_valid(worker.bridge):
                        worker.bridge.deleteLater()
                else:
                    self._tracked_qthreads.discard(worker)
                    if _qt_is_valid(worker):
                        worker.deleteLater()
        finally:
            if not self._alive or not _qt_is_valid(self):
                if _qt_is_valid(self) and getattr(self, "active_worker", None) is worker:
                    self.active_worker = None
                    self.active_operation_id = None
                return

        if self.active_worker is worker:
            self.active_worker = None
            self.active_operation_id = None
            self.busy_changed.emit(False)
            if self.shell is not None and _qt_is_valid(self.shell):
                self.shell.overview_screen.set_operation_active(False)

        ctrl_ref = weakref.ref(self)
        if self._close_after_worker:
            self._close_after_worker = False
            self._closing = True
            self._pending_post_op_modal = False
            self.shutdown_workers()
            QTimer.singleShot(20, lambda: QApplication.instance() and QApplication.instance().quit())
        elif self._closing:
            self._pending_post_op_modal = False
        elif self._pending_discoveries is not None:
            found = self._pending_discoveries
            self._pending_discoveries = None
            QTimer.singleShot(
                0,
                lambda r=ctrl_ref, f=found: (
                    r()._choose_discovered(f)
                    if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                    else None
                ),
            )
        elif self._pending_post_op_modal:
            pass
        else:
            QTimer.singleShot(
                0,
                lambda r=ctrl_ref: (
                    r()._maybe_show_release_notice()
                    if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                    else None
                ),
            )

    def _on_worker_finish(self, op_id: str, success: bool, result: Any) -> None:
        if not self._alive or not _qt_is_valid(self) or op_id != self.active_operation_id:
            return
        kind = self.operation_kind

        if not success:
            payload = result if isinstance(result, dict) else {"message": str(result)}
            msg = str(payload.get("message") or "Lỗi chưa xác định")
            err_code = str(payload.get("error_code") or "")
            diag_code = str(payload.get("diagnosed_code") or "")
            exc_obj = payload.get("exc")
            mapped = INTERNAL_MAP.get(err_code) or diag_code or None
            worker = self.active_worker
            worker_cancelled = bool(
                worker is not None
                and getattr(worker, "cancel_event", None) is not None
                and worker.cancel_event.is_set()
            )
            is_cancelled = (
                err_code == "CANCELLED"
                or diag_code == "E-CANCELLED"
                or mapped == "E-CANCELLED"
                or isinstance(exc_obj, CancelledError)
                or (worker_cancelled and "CANCEL" in err_code.upper())
            )
            if self.shell is not None and _qt_is_valid(self.shell):
                self.shell.overview_screen.set_operation_active(False)
            if is_cancelled:
                cancel_msg = msg or "Đã hủy thao tác."
                self.show_toast("Đã hủy thao tác.", "info")
                self.operation_finished.emit(kind, False, cancel_msg)
                return
            self.operation_finished.emit(kind, False, msg)
            self.show_error(
                _ACTION_TITLES.get(kind, kind or "Thao tác"),
                code=mapped,
                exc=exc_obj,
                message=msg,
                probe=payload.get("probe"),
                writability=payload.get("writability"),
                operation=kind,
            )
            return

        if not isinstance(result, dict):
            self.operation_finished.emit(kind, True, None)
            return

        if kind == "discover":
            self._pending_discoveries = result.get("installations", [])
            self.operation_finished.emit(kind, True, None)
            return

        if kind == "select_root":
            info: GameInfo = result["game"]
            if not info.installed:
                hint = find_game_exe_hint(info.game_path) if info.game_path else None
                if hint is not None and self._can_open_modal():
                    assert self.shell is not None
                    found = find_all_potential_game_installations()
                    dlg = GameSelectionDialog(
                        found,
                        parent=self.shell,
                        wrong_path=info.game_path,
                        hint_path=hint,
                        backup_root=self.pm.backup_root,
                        asset_renderer=self.shell._renderer,
                    )
                    if self.shell.show_modal(dlg) == QDialog.DialogCode.Accepted and dlg.selected_path:
                        ctrl_ref = weakref.ref(self)
                        QTimer.singleShot(
                            0,
                            lambda r=ctrl_ref, p=dlg.selected_path: (
                                r().select_game_root(p)
                                if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                                else None
                            ),
                        )
                    return
                if hint is not None:
                    return
                self.show_error(
                    "Chọn thư mục game",
                    code="E-NO-EXE",
                    message=f"Không tìm thấy StellaSora.exe tại: {info.game_path or '(không rõ)'}",
                    target_file=str(info.game_path or ""),
                )
                return

            prev = self.cm.get("game_path", "")
            self.cm.set("game_path", str(info.game_path))
            if not self.cm.save():
                self.cm.set("game_path", prev)
                self.show_error(
                    "Lưu thư mục game",
                    code="E-CONFIG-SAVE",
                    message="\n".join(self.cm.warnings),
                )
                return

        if "game" in result:
            self._apply_game_info(result["game"])
            self._refresh_translation_state()

        ctrl_ref = weakref.ref(self)
        if kind in ("scan", "select_root"):
            if self._pending_launch_guard_notice is not None and self.current_game_info.installed:
                pending_n = self._pending_launch_guard_notice
                self._pending_launch_guard_notice = None
                self._official_update = pending_n
                self._apply_game_info(self.current_game_info)
                self._pending_post_op_modal = True
                QTimer.singleShot(
                    50,
                    lambda r=ctrl_ref, n=pending_n: (
                        r()._show_launch_guard_on_startup(n)
                        if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                        else None
                    ),
                )
            else:
                QTimer.singleShot(
                    800,
                    lambda r=ctrl_ref: (
                        r()._start_official_check()
                        if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                        else None
                    ),
                )
        elif kind == "verify":
            v_msg = (
                f"Đã đối chiếu {result.get('files', 0)} tệp của bản dịch "
                f"{result.get('version', '')} toàn vẹn."
            )
            self.show_toast(v_msg, "success")
        elif kind == "launch":
            self.show_toast(str(result.get("message") or "Đã gửi lệnh mở game."), "success")
            QTimer.singleShot(
                1500,
                lambda r=ctrl_ref: (
                    r()._poll_game_running()
                    if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                    else None
                ),
            )
        elif kind == "publisher_vanilla_restore":
            self.show_toast(str(result.get("message") or "Đã khôi phục dữ liệu gốc."), "success")
            pub_reason = str(result.get("pub_reason") or "")
            if result.get("launch_after"):
                self._pending_post_op_modal = True
                QTimer.singleShot(
                    50,
                    lambda r=ctrl_ref: (
                        r()._launch_after_pub_restore()
                        if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                        else None
                    ),
                )
            else:
                self._pending_post_op_modal = True
                QTimer.singleShot(
                    50,
                    lambda r=ctrl_ref, pr=pub_reason: (
                        r()._prompt_launch_after_pub_restore(pr)
                        if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                        else None
                    ),
                )
        elif kind == "self_update":
            if result.get("status") != "online":
                self.show_error(
                    "Kiểm tra cập nhật launcher",
                    code=result.get("error_code")
                    or ("E-CONFIG-CHANNEL" if result.get("status") == "unavailable" else "E-NET"),
                    message=str(result.get("message") or "Không thể kết nối GitHub."),
                )
            elif not result.get("has_update"):
                self._show_info_confirm(
                    "Cập nhật launcher",
                    f"Bạn đang dùng phiên bản mới nhất (v{LAUNCHER_VERSION}).\nKhông có bản cập nhật mới trên GitHub.",
                )
            elif not result.get("download_url"):
                self._show_info_confirm(
                    "Cập nhật launcher",
                    str(result.get("message") or "Chưa có tệp cập nhật tự động được xác minh."),
                )
            else:
                self._pending_post_op_modal = True
                QTimer.singleShot(
                    0,
                    lambda r=ctrl_ref, d=result: (
                        r()._confirm_update(d)
                        if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                        else None
                    ),
                )
        elif kind == "apply_self_update":
            self.show_toast("Đã tải bản cập nhật. Launcher sẽ khởi động lại ngay...", "success")
            self._close_after_worker = True
        elif kind == "install":
            sc_ok = False
            if self._pending_create_shortcut and self.current_game_info.game_path:
                ok, _sc_msg = create_game_shortcut(
                    self.current_game_info.game_path,
                    launcher_exe=Path(sys.executable) if self.pm.is_frozen else None,
                    app_data_dir=self.pm.app_data_dir if self.pm.is_custom_app_data else None,
                )
                sc_ok = ok
            self.show_toast(str(result.get("message") or "Hoàn tất cài đặt Việt hoá!"), "success")
            self._pending_post_op_modal = True
            QTimer.singleShot(
                120,
                lambda r=ctrl_ref, res=result, s=sc_ok: (
                    r()._show_install_completed(res, s)
                    if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                    else None
                ),
            )
        elif kind == "rollback":
            self.show_toast(str(result.get("message") or "Hoàn tất khôi phục dữ liệu gốc!"), "success")
            upd = self._official_update or {}
            if upd.get("update_available"):
                reason = (
                    f"tài nguyên game {upd.get('local_resource_version')} → "
                    f"{upd.get('latest_resource_version')}"
                )
                self._pending_post_op_modal = True
                QTimer.singleShot(
                    50,
                    lambda r=ctrl_ref, pr=reason: (
                        r()._prompt_launch_after_pub_restore(pr)
                        if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                        else None
                    ),
                )
        elif kind == "recover":
            self.show_toast(str(result.get("message") or "Đã phục hồi nhật ký thao tác."), "success")
        else:
            if result.get("message"):
                self.show_toast(str(result["message"]), "success")

        self.operation_finished.emit(kind, True, result.get("message"))

    # ---------------- Core User Flows (v1.3.4 Parity) ----------------

    def _confirm(self, title: str, message: str, confirm_label: str = "Tiếp tục", *, is_danger: bool = False) -> bool:
        if (
            not self._alive
            or self._closing
            or not _qt_is_valid(self)
            or self.shell is None
            or not _qt_is_valid(self.shell)
            or self.shell._active_modal is not None
            or bool(getattr(self.shell, "_modal_stack", None))
        ):
            return False
        dlg = ConfirmationDialog(
            title,
            message,
            confirm_label=confirm_label,
            is_danger=is_danger,
            asset_renderer=self.shell._renderer,
            parent=self.shell,
        )
        return self.shell.show_modal(dlg) == QDialog.DialogCode.Accepted

    def _check_ready_or_explain(self, action_title: str) -> bool:
        if self.active_worker is not None:
            self.show_error(
                action_title,
                code="E-BUSY",
                message=f"Thao tác đang chạy: {self.operation_kind or '?'}",
            )
            return False
        info = self.current_game_info
        if not info.installed or not info.game_path:
            self.show_error(action_title, code="E-NO-GAME-FOLDER")
            return False
        running_now = is_game_process_running()
        if running_now != info.is_running:
            info.is_running = running_now
            self._apply_game_info(info)
            self._refresh_translation_state()
        if info.is_running:
            self.show_error(action_title, code="E-GAME-RUNNING")
            return False
        return True

    def _action_target(self, action: str, *, require_receipt: bool = True) -> Optional[Path]:
        if not self._check_ready_or_explain(action):
            return None
        info = self.current_game_info
        if require_receipt and not info.installed_receipt:
            receipt_file = Path(info.game_path) / ".vietnamese_patch_receipt.json"
            present = receipt_file.is_file()
            restored = bool(getattr(info, "official_restore", None))
            self.show_error(
                action,
                code="E-RECEIPT-MISMATCH" if present else "E-NO-RECEIPT",
                message=(
                    "Tệp biên bản có trong thư mục game nhưng không dùng được."
                    if present
                    else "Không có tệp .vietnamese_patch_receipt.json trong thư mục game."
                ),
                extra={"tệp biên bản tồn tại": "có" if present else "không"},
                extra_summary=(
                    'Bạn vừa khôi phục dữ liệu gốc của nhà phát hành nên game đang ở bản gốc, chưa có bản dịch để kiểm tra. Bấm "Cài Việt hoá" khi muốn dùng lại bản dịch.'
                )
                if (restored and not present)
                else "",
            )
            return None
        return Path(info.game_path)

    def _refresh_translation_state(self) -> dict[str, Any]:
        local = str(self.cm.get("payload_path", "") or "").strip()
        if local:
            try:
                path = Path(local) / "patch_manifest.json"
                if not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
                    raise ValueError("Thiếu bảng kê hoặc bảng kê quá lớn.")
                manifest = self.network_service._windows_manifest(
                    json.loads(path.read_text(encoding="utf8"))
                )
                local_state = {
                    "release_status": "online",
                    "manifest_status": "online",
                    "translation_version": manifest["version"],
                    "translation_game": manifest["client_game_version"],
                    "translation_resource": manifest["resource_version"],
                    "manifest_sha256": manifest_sha256(manifest),
                }
                state = translation_state(local_state, self.current_game_info)
                state["translation_game"] = local_state["translation_game"]
                state["translation_resource"] = local_state["translation_resource"]
                state["message"] = "Gói cục bộ: " + state["message"]
            except Exception as exc:  # noqa: BLE001
                code = "E-LOCAL-PAYLOAD"
                state = {
                    "available": False,
                    "can_install": False,
                    "message": lookup(code).title + " — " + str(exc) + f" [{code}]",
                    "blocker_code": code,
                    "blocker_detail": f"Gói cục bộ ({local}): {exc}",
                }
        else:
            state = translation_state(self._github_sync_state, self.current_game_info)

        if self.shell is not None:
            self.shell.overview_screen.set_translation_state(state)
        self.translation_state_changed.emit(state)
        return state

    def install_patch(self) -> None:
        self._pending_post_op_modal = False
        if not self._alive or self._closing or not _qt_is_valid(self):
            return
        if self.shell is not None and (
            not _qt_is_valid(self.shell)
            or self.shell._active_modal is not None
            or bool(getattr(self.shell, "_modal_stack", None))
        ):
            return
        if not self._check_ready_or_explain("Cài đặt Việt hoá"):
            return
        root = Path(self.current_game_info.game_path)
        info = self.current_game_info
        state = self._refresh_translation_state()
        if not state.get("can_install"):
            self.show_error(
                "Cài đặt Việt hoá",
                code=state.get("blocker_code") or "E-UNKNOWN",
                message=state.get("blocker_detail") or state.get("message", ""),
            )
            return

        manifest_meta = {
            "client_game_version": state.get("translation_game")
            or self._github_sync_state.get("translation_game", "2.1.0"),
            "resource_version": state.get("translation_resource")
            or self._github_sync_state.get("translation_resource", "*"),
        }
        has_new_pub, pub_reason = detect_new_publisher_version(info, manifest_meta)
        if has_new_pub:
            if not self._confirm(
                "PHÁT HIỆN BẢN CẬP NHẬT GAME MỚI",
                f"{pub_reason}.\n\nLauncher sẽ tự tải dữ liệu gốc của nhà phát hành về (cần mạng) "
                "để game cập nhật an toàn trước khi cài Việt hoá. Tiếp tục?",
                "Khôi phục gốc",
            ):
                return
            self._start_official_restore(root, pub_reason)
            return

        is_update = bool(state.get("available"))
        local = str(self.cm.get("payload_path", "") or "").strip()
        channel_valid = self._configure_network()
        if not local and not channel_valid:
            self.show_error(
                "Cài đặt Việt hoá",
                code="E-CONFIG-CHANNEL",
                message=self._channel_error or self._github_sync_state.get("message", ""),
            )
            return

        if self.shell is None:
            return
        pref_shortcut = bool(self.cm.get("create_desktop_shortcut", True))
        cd = ConfirmationDialog(
            "CÀI / CẬP NHẬT VIỆT HÓA",
            f"Thư mục: {root}\n\n{state['message']}\n\n"
            "Tải hoặc đọc gói đã chọn, sao lưu và cài đúng các tệp trong manifest. "
            "Gói chỉ gồm texture sẽ chỉ cài texture.",
            confirm_label="Cài bản dịch",
            show_shortcut_option=True,
            shortcut_default=pref_shortcut,
            asset_renderer=self.shell._renderer,
            parent=self.shell,
        )
        if self.shell.show_modal(cd) != QDialog.DialogCode.Accepted:
            return

        self._pending_create_shortcut = cd.create_shortcut_requested()
        self.cm.set("create_desktop_shortcut", self._pending_create_shortcut)
        self.cm.save()

        network = self.network_service
        manifest_url = self._channel["manifest_url"]

        def work(cb, op, cancel_ev):
            with network.payload_for_install(
                self.pm.payload_root,
                local,
                manifest_url,
                cb,
                op,
                cancel_event=cancel_ev,
                should_cancel=cancel_ev.is_set,
            ) as payload:
                if is_update:
                    manifest = json.loads((payload / "patch_manifest.json").read_text(encoding="utf8"))
                    rechecked = translation_state(
                        {
                            "release_status": "online",
                            "manifest_status": "online",
                            "translation_version": manifest.get("version"),
                            "translation_game": manifest.get("client_game_version"),
                            "translation_resource": manifest.get("resource_version"),
                            "manifest_sha256": manifest_sha256(manifest),
                        },
                        info,
                    )
                    if not rechecked.get("available"):
                        raise RuntimeError("Không còn bản Việt hoá mới hơn: " + str(rechecked.get("message")))
                r = self._engine().install(root, payload, operation_id=op, event_cb=cb)
                return {
                    "game": self._detected(),
                    "version": r.get("version"),
                    "files_count": r.get("files_count"),
                    "message": f"Đã nạp thành công {r['files_count']} tệp bản dịch ({r['version']}).",
                }

        self._start_operation(
            "install",
            work,
            initial_message="Đang chuẩn bị gói bản dịch...",
            writability_target=root,
        )

    def _show_install_completed(self, result: dict[str, Any], shortcut_created: bool = False) -> None:
        self._pending_post_op_modal = False
        if not self._can_open_modal():
            return
        assert self.shell is not None
        dlg = InstallCompletedDialog(
            self.current_game_info,
            result,
            shortcut_created_initially=shortcut_created,
            shortcut_preference=self._pending_create_shortcut,
            parent=self.shell,
            asset_renderer=self.shell._renderer,
        )
        self.shell.show_modal(dlg)
        if dlg.launch_game_clicked and self._alive and not self._closing:
            self.launch_game()

    def rollback_official(self, *, confirm: bool = True) -> None:
        root = self._action_target("Khôi phục gốc", require_receipt=False)
        if root is None:
            return
        if confirm and not self._confirm(
            "KHÔI PHỤC DỮ LIỆU GỐC NGUYÊN BẢN",
            f"Thư mục: {root}\n\n"
            "Launcher sẽ tự tải dữ liệu ngôn ngữ (data.arcx, lua.arcx và các gói ảnh) "
            "mới nhất từ máy chủ chính thức của nhà phát hành, kiểm tra mã băm rồi cài vào game.\n\n"
            "Cần kết nối mạng, có thể tải vài trăm MB. Nếu lỗi giữa chừng, game được giữ nguyên.",
            "Tải và khôi phục gốc",
        ):
            return

        def work(cb, op, cancel_ev):
            engine = RollbackEngine(
                self.pm.backup_root,
                self.pm.journals_dir,
                cache_dir=self.pm.app_data_dir / "official_cache",
            )
            r = engine.rollback(
                root,
                operation_id=op,
                event_cb=cb,
                source="official",
                should_cancel=cancel_ev.is_set,
            )
            return {
                "game": self._detected(),
                "message": r.get(
                    "message",
                    "Hoàn tất khôi phục dữ liệu gốc mới nhất của nhà phát hành.",
                ),
            }

        self._start_operation(
            "rollback",
            work,
            initial_message="Đang tải dữ liệu gốc từ Yostar...",
            writability_target=root,
        )

    def _start_official_restore(self, root: Path, pub_reason: str = "", launch_after: bool = False) -> None:
        def work(cb, op, cancel_ev):
            engine = RollbackEngine(
                self.pm.backup_root,
                self.pm.journals_dir,
                cache_dir=self.pm.app_data_dir / "official_cache",
            )
            r = engine.rollback(
                root,
                operation_id=op,
                event_cb=cb,
                source="official",
                should_cancel=cancel_ev.is_set,
            )
            return {
                "game": self._detected(),
                "pub_reason": pub_reason,
                "launch_after": launch_after,
                "message": r.get("message", "Đã khôi phục dữ liệu gốc để game cập nhật an toàn."),
            }

        self._start_operation(
            "publisher_vanilla_restore",
            work,
            initial_message="Đang khôi phục dữ liệu gốc từ Yostar...",
            writability_target=root,
        )

    def _on_overview_official_restore(self) -> None:
        notice = self._official_notice()
        if notice:
            self._prompt_restore_before_update(notice)
        else:
            self.rollback_official()

    def _launch_after_pub_restore(self) -> None:
        self._pending_post_op_modal = False
        if self._closing or not self._alive or not _qt_is_valid(self):
            return
        if not self._can_open_modal():
            return
        self.launch_game()

    def _prompt_launch_after_pub_restore(self, pub_reason: str) -> None:
        self._pending_post_op_modal = False
        if not self._can_open_modal():
            return
        if self._confirm(
            "Game mới cập nhật tài nguyên mới",
            f"Phát hiện game có bản cập nhật mới từ nhà phát hành ({pub_reason}).\n\n"
            "Launcher đã tải và cài lại dữ liệu gốc của nhà phát hành để game cập nhật an toàn.\n\n"
            "Vui lòng mở game để cập nhật tài nguyên mới trước khi cài lại Việt hoá!",
            "Mở Game ngay",
        ):
            if self._alive and not self._closing:
                self.launch_game()

    def verify_files(self) -> None:
        root = self._action_target("Kiểm tra tệp")
        if root is None:
            return
        self._start_operation(
            "verify",
            lambda cb, op: self._engine().verify_installed(root, cb, op),
            initial_message="Đang đối chiếu SHA256 các tệp Việt hoá...",
            writability_target=root,
        )

    def recover_journals(self) -> None:
        if not self._check_ready_or_explain("Phục hồi thao tác"):
            return
        root = Path(self.current_game_info.game_path)
        if not self._confirm(
            "PHỤC HỒI THAO TÁC BỊ NGẮT",
            f"Thư mục: {root}\n\n"
            "Đọc nhật ký và đưa các tệp dở dang về trạng thái trước thao tác bị ngắt. "
            "Các tệp đã được nhà phát hành cập nhật sẽ được giữ nguyên an toàn.",
            "Phục hồi",
        ):
            return

        def work(cb, op):
            r = self._engine().recover(root, cb, op)
            msg = (
                f"Đã phục hồi và đồng bộ {r['journals']} nhật ký cũ (giữ nguyên tệp game mới)."
                if r.get("superseded")
                else f"Đã phục hồi {r['journals']} nhật ký."
            )
            return {"game": self._detected(), "message": msg}

        self._start_operation(
            "recover",
            work,
            initial_message="Đang quét và phục hồi nhật ký...",
            writability_target=root,
        )

    def launch_game(self) -> None:
        if not self._alive or self._closing or not _qt_is_valid(self):
            return
        if self.shell is not None and (
            not _qt_is_valid(self.shell)
            or self.shell._active_modal is not None
            or bool(getattr(self.shell, "_modal_stack", None))
        ):
            return
        if not self._check_ready_or_explain("Mở game"):
            return
        info = self.current_game_info
        notice = self._official_notice()
        if notice:
            reason = (
                f"tài nguyên game {notice.get('local_resource_version')} → "
                f"{notice.get('latest_resource_version')}"
            )
            if bool(self.cm.get("auto_restore_before_game_update", False)):
                self._start_official_restore(Path(info.game_path), reason, launch_after=True)
                return
            assert self.shell is not None
            self.shell.bring_to_front_urgent()
            dlg = UpdateGuardDialog(
                notice=notice,
                game_running=False,
                launch_after_restore=True,
                always_on_top=False,
                asset_renderer=self.shell._renderer,
                parent=self.shell,
            )
            if self.shell.show_modal(dlg) == QDialog.DialogCode.Accepted:
                self._start_official_restore(Path(info.game_path), reason, launch_after=True)
            else:
                # Hard-block: NEVER bypass and open modified game when official update exists
                self.show_toast(
                    "Đã chặn mở game vì Yostar có bản cập nhật mới. Hãy khôi phục dữ liệu gốc trước.",
                    "warn",
                )
            return

        backup_root = self.pm.backup_root
        snapshot = GameInfo(**{k: getattr(info, k) for k in info.__dataclass_fields__})

        def work(cb, op, *, br=backup_root, gi=snapshot):
            ok, msg = GameDetector(br).launch(gi)
            if not ok:
                if "chưa được chọn" in msg:
                    kind = "NO_GAME_FOLDER"
                elif "đang chạy" in msg:
                    kind = "GAME_RUNNING"
                elif "Không tìm thấy file" in msg:
                    kind = "INVALID_ROOT"
                else:
                    kind = "LAUNCH_FAILED"
                raise InstallerError(msg, kind)
            return {"message": msg}

        self._start_operation("launch", work, initial_message="Đang khởi động Stella Sora...")

    # ---------------- Official Update Check & Real-Time Guard ----------------

    def _official_notice(self) -> Optional[dict[str, Any]]:
        upd = self._official_update
        info = self.current_game_info
        if not upd or not info or not info.installed or not upd.get("update_available"):
            return None
        if (
            upd.get("source") != "player_log"
            and str(upd.get("local_resource_version")) != str(info.resource_version)
        ):
            return None
        if not (info.installed_receipt or info.has_vietnamese):
            return None
        return upd

    def _start_official_check(
        self,
        force: bool = False,
        manual: bool = False,
        *,
        from_game_launch: bool = False,
    ) -> None:
        info = self.current_game_info
        if self._official_running or not info.installed or not info.game_path:
            if manual and (not info.installed or not info.game_path):
                self.show_error("Kiểm tra bản vá Yostar", code="E-NO-GAME-FOLDER")
            return
        if not force and not bool(self.cm.get("check_official_on_start", True)):
            return
        if not force and (time.time() - self._official_checked_at) < 600:
            return

        self._official_checked_at = time.time()
        self._official_running = True
        cache_file = self.pm.official_check_file
        snapshot = GameInfo(**{k: getattr(info, k) for k in info.__dataclass_fields__})
        self_ref = weakref.ref(self)

        def _worker() -> None:
            try:
                res = check_official_update(OfficialClient("EN", timeout=15, retries=2), snapshot, cache_file)
                res["_manual"] = manual
                res["_from_game_launch"] = from_game_launch
                ok = True
                payload: Any = res
            except Exception as exc:  # noqa: BLE001
                ok = False
                payload = {
                    "message": str(exc),
                    "exc": exc,
                    "_manual": manual,
                    "_from_game_launch": from_game_launch,
                }

            ctrl = self_ref()
            if ctrl is not None and ctrl._alive and _qt_is_valid(ctrl):
                try:
                    ctrl._official_thread_done_signal.emit(ok, payload)
                except RuntimeError:
                    pass

        threading.Thread(target=_worker, name="launcher_v2_official_check", daemon=True).start()

    def _official_check_finished(self, success: bool, result: dict[str, Any]) -> None:
        self._official_running = False
        if not self._alive or self._closing:
            return
        manual = bool(result.get("_manual", False))
        from_game_launch = bool(result.get("_from_game_launch", False))
        if not success:
            logger.info("Official version check skipped: %s", result.get("message"))
            if manual:
                self.show_error(
                    "Kiểm tra bản vá Yostar",
                    exc=result.get("exc"),
                    message=str(result.get("message") or ""),
                )
            return

        self._official_update = result
        self.official_update_changed.emit(result)
        self._apply_game_info(self.current_game_info)

        if manual and not result.get("update_available"):
            self.show_toast(
                f"Tài nguyên game đang ở phiên bản mới nhất ({result.get('latest_resource_version', '—')}).",
                "success",
            )
            return

        notice = self._official_notice()
        if not notice or self.active_worker is not None:
            return

        info = self.current_game_info
        # Real-time alert if player is ALREADY inside the game when official update is detected!
        if info.is_running and self._is_realtime_guard_active(info):
            self._trigger_realtime_update_guard(notice=notice, force=from_game_launch)
            return

        if (
            not self._can_open_modal()
            or self._pending_post_op_modal
            or self._pending_discoveries is not None
        ):
            return
        reason = f"tài nguyên game {notice['local_resource_version']} → {notice['latest_resource_version']}"
        if bool(self.cm.get("auto_restore_before_game_update", False)):
            self.show_toast("Game có bản cập nhật mới — đang tự khôi phục dữ liệu gốc...", "info")
            self._start_official_restore(Path(info.game_path), reason)
            return
        latest = str(notice.get("latest_resource_version"))
        if latest in self._official_prompted and not manual:
            return
        self._official_prompted.add(latest)
        ctrl_ref = weakref.ref(self)
        QTimer.singleShot(
            0,
            lambda r=ctrl_ref, n=notice: (
                r()._prompt_restore_before_update(n)
                if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                else None
            ),
        )

    def _show_launch_guard_on_startup(self, notice: dict[str, Any]) -> None:
        self._pending_post_op_modal = False
        if not self._alive or self._closing or not _qt_is_valid(self) or self.shell is None:
            return
        self.shell.bring_to_front_urgent()
        if self._guard_dialog_open or self.active_worker is not None or not self.current_game_info.installed:
            return
        self._prompt_restore_before_update(notice, launch_after=True, always_on_top=True)

    def _prompt_restore_before_update(
        self,
        notice: dict[str, Any],
        *,
        launch_after: bool = False,
        always_on_top: bool = False,
    ) -> None:
        if (
            not self._alive
            or self._closing
            or not _qt_is_valid(self)
            or self._guard_dialog_open
            or self.active_worker is not None
            or self._pending_post_op_modal
            or self._pending_discoveries is not None
            or not self.current_game_info.installed
            or self.shell is None
            or not _qt_is_valid(self.shell)
            or not self.shell.isVisible()
            or self.shell._active_modal is not None
            or bool(getattr(self.shell, "_modal_stack", None))
        ):
            return
        self._guard_dialog_open = True
        try:
            dlg = UpdateGuardDialog(
                notice=notice,
                game_running=bool(self.current_game_info.is_running),
                launch_after_restore=launch_after,
                always_on_top=always_on_top,
                asset_renderer=self.shell._renderer,
                parent=self.shell,
            )
            accepted = self.shell.show_modal(dlg) == QDialog.DialogCode.Accepted
        finally:
            self._guard_dialog_open = False

        if accepted and self._alive and not self._closing and self.current_game_info.game_path:
            self._start_official_restore(
                Path(self.current_game_info.game_path),
                f"tài nguyên game {notice.get('local_resource_version')} → {notice.get('latest_resource_version')}",
                launch_after=launch_after,
            )

    def _trigger_realtime_update_guard(
        self,
        *,
        signal: Optional[GameUpdateSignal] = None,
        notice: Optional[dict[str, Any]] = None,
        force: bool = False,
    ) -> None:
        """Immediately warn player when Stella Sora shows an update prompt or Yostar has a patch."""
        if (
            not self._alive
            or self._closing
            or not _qt_is_valid(self)
            or self._guard_dialog_open
            or self.active_worker is not None
            or not self.current_game_info.installed
            or self.shell is None
            or not _qt_is_valid(self.shell)
        ):
            return

        if signal is not None:
            fp = signal.fingerprint()
        elif notice is not None:
            fp = f"server|{notice.get('latest_resource_version')}|{notice.get('latest_game_version')}"
        else:
            return

        if not force and fp in self._guard_alerted_fingerprints:
            return
        self._guard_alerted_fingerprints.add(fp)

        info = self.current_game_info
        game_path = Path(info.game_path) if info.game_path else None
        auto_close = bool(self.cm.get("guard_auto_close_game_on_update", False))

        if auto_close and is_game_process_running():
            close_game_gracefully_or_force(game_path, wait_seconds=2.5)
        elif is_game_process_running():
            minimize_game_windows(game_path)

        still_running = is_game_process_running()
        if still_running != info.is_running:
            info.is_running = still_running
            self._apply_game_info(info)

        tray_body = (
            signal.detail
            if signal is not None
            else (
                f"Yostar đã phát hành tài nguyên {notice.get('latest_resource_version')} "
                "(bản trên máy đã cài Việt hóa). Hãy khôi phục gốc trước khi cập nhật!"
            )
        )
        self.shell.show_tray_notification(
            "DỪNG LẠI — Stella Sora có bản cập nhật!",
            tray_body,
            urgent=True,
        )
        self.shell.bring_to_front_urgent()

        if self.shell._active_modal is not None or bool(getattr(self.shell, "_modal_stack", None)):
            self.show_toast("PHÁT HIỆN CẬP NHẬT GAME — Hãy khôi phục dữ liệu gốc ngay!", "warn")
            return

        self._guard_dialog_open = True
        try:
            dlg = UpdateGuardDialog(
                notice=notice,
                signal=signal,
                game_running=still_running,
                launch_after_restore=True,
                always_on_top=True,
                asset_renderer=self.shell._renderer,
                parent=self.shell,
            )
            accepted = self.shell.show_modal(dlg) == QDialog.DialogCode.Accepted
        finally:
            self._guard_dialog_open = False

        if not accepted or not self._alive or self._closing or game_path is None:
            if self._alive and not self._closing:
                self.show_toast(
                    "KHÔNG bấm cập nhật trong game trước khi khôi phục dữ liệu gốc!",
                    "warn",
                )
            return

        # Close StellaSora.exe cleanly before starting OfficialRestoreEngine
        if is_game_process_running():
            ok_close, close_msg = close_game_gracefully_or_force(game_path, wait_seconds=3.0)
            info.is_running = is_game_process_running()
            self._apply_game_info(info)
            if not ok_close or info.is_running:
                self.show_error(
                    "Đóng game trước khi khôi phục gốc",
                    code="E-GAME-RUNNING",
                    message=close_msg,
                )
                return

        reason = (
            signal.detail
            if signal is not None
            else f"tài nguyên game {notice.get('local_resource_version')} → {notice.get('latest_resource_version')}"
        )
        self._start_official_restore(game_path, reason, launch_after=True)

    # ---------------- Translation / Launcher Update & Notice ----------------

    def check_translation_version(self) -> None:
        if self.active_worker is not None:
            return
        if not self._configure_network():
            self.show_error(
                "Kiểm tra phiên bản Việt hoá",
                code="E-CONFIG-CHANNEL",
                message=self._channel_error,
            )
            return
        if self._bg_sync_running:
            self._manual_translation_next = True
            self._pending_sync = True
            return
        self._manual_translation_check = True
        self.sync_github(automatic=False)

    def check_launcher_update(self) -> None:
        if not self._configure_network():
            self.show_error(
                "Kiểm tra cập nhật launcher",
                code="E-CONFIG-CHANNEL",
                message=self._channel_error,
            )
            return
        network = self.network_service
        self._start_operation(
            "self_update",
            lambda cb, op: network.check_for_updates(LAUNCHER_VERSION),
            initial_message="Đang kiểm tra bản cập nhật launcher...",
        )

    def _record_release_observation(self, sync: dict[str, Any]) -> None:
        if sync.get("release_status") != "online":
            return
        version = sync.get("release_version")
        if version_parts(version) is None:
            return
        key = hashlib.sha256(str(self._github_identity or "").encode("utf8")).hexdigest()
        baselines = self.cm.get("release_notice_baselines", {})
        pending = self.cm.get("release_notice_pending", {})
        baselines = dict(baselines) if isinstance(baselines, dict) else {}
        pending = dict(pending) if isinstance(pending, dict) else {}
        previous = baselines.get(key)
        if previous and newer(version, previous):
            pending[key] = version
        if not previous or not newer(previous, version):
            baselines[key] = version
        self.cm.update({"release_notice_baselines": baselines, "release_notice_pending": pending})
        self.cm.save()

    def _maybe_show_release_notice(self) -> None:
        if (
            not self._alive
            or self._closing
            or not _qt_is_valid(self)
            or self.active_worker is not None
            or self._bg_sync_running
            or self._manual_translation_check
            or self._pending_post_op_modal
            or self._pending_discoveries is not None
            or self.shell is None
            or not _qt_is_valid(self.shell)
            or not self.shell.isVisible()
            or self.shell._active_modal is not None
            or bool(getattr(self.shell, "_modal_stack", None))
        ):
            return
        sync = self._github_sync_state
        if sync.get("release_status") != "online":
            return
        version = sync.get("release_version")
        channel_key = hashlib.sha256(str(self._github_identity or "").encode("utf8")).hexdigest()
        pending = self.cm.get("release_notice_pending", {})
        pending = dict(pending) if isinstance(pending, dict) else {}
        has_t_update = bool(translation_state(sync, self.current_game_info).get("available"))
        if version_parts(version) is None or not (
            pending.get(channel_key) == version
            or sync.get("update", {}).get("has_update")
            or has_t_update
        ):
            return
        key = f"{self._github_identity}|{version}|{sync.get('manifest_sha256') or ''}"
        try:
            snooze_until = float(self.cm.get("release_notice_snooze_until", 0) or 0)
        except (ValueError, TypeError):
            snooze_until = 0.0
        if key in self._notice_seen:
            return
        remaining = snooze_until - time.time()
        if remaining > 0:
            self._snooze_timer.start(min(2147483647, max(1, int(remaining * 1000) + 1)))
            return

        has_l_update = bool(
            sync.get("update", {}).get("has_update") and sync.get("update", {}).get("download_url")
        )
        dlg = UpdateNoticeDialog(
            str(version),
            str(sync.get("release_notes", "")),
            parent=self.shell,
            has_launcher_update=has_l_update,
            has_translation_update=has_t_update,
            asset_renderer=self.shell._renderer,
        )
        result = self.shell.show_modal(dlg)
        ctrl_ref = weakref.ref(self)
        if result == 3:
            self._notice_seen.add(key)
            if pending.get(channel_key) == version:
                pending.pop(channel_key, None)
                self.cm.set("release_notice_pending", pending)
                self.cm.save()
            if has_l_update:
                self._pending_post_op_modal = True
                QTimer.singleShot(
                    50,
                    lambda r=ctrl_ref, u=sync["update"]: (
                        r()._confirm_update(u)
                        if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                        else None
                    ),
                )
        elif result == 4:
            self._notice_seen.add(key)
            if pending.get(channel_key) == version:
                pending.pop(channel_key, None)
                self.cm.set("release_notice_pending", pending)
                self.cm.save()
            self._pending_post_op_modal = True
            QTimer.singleShot(
                50,
                lambda r=ctrl_ref: (
                    r().install_patch()
                    if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                    else None
                ),
            )
        elif result == 2:
            self.cm.set("release_notice_snooze_until", time.time() + 24 * 60 * 60)
            if not self.cm.save():
                self.show_error(
                    "Lưu lựa chọn thông báo",
                    code="E-CONFIG-SAVE",
                    message="\n".join(self.cm.warnings),
                )
            self._snooze_timer.start(24 * 60 * 60 * 1000)
        else:
            self._notice_seen.add(key)
            if pending.get(channel_key) == version:
                pending.pop(channel_key, None)
                self.cm.set("release_notice_pending", pending)
                self.cm.save()

    def _confirm_update(self, data: dict[str, Any]) -> None:
        self._pending_post_op_modal = False
        if not self._can_open_modal():
            return
        latest = str(data.get("latest_version") or "")
        body = (
            f"Đã có phiên bản launcher mới: {latest} (hiện tại: v{LAUNCHER_VERSION}).\n\n"
            "Bạn có muốn tải và tự động cập nhật ngay bây giờ không?"
        )
        cl = str(data.get("changelog") or "").strip()
        if cl:
            cl_lines = [ln for ln in cl.splitlines() if ln.strip()][:5]
            if cl_lines:
                body += "\n\nNội dung mới:\n" + "\n".join(cl_lines)
        if not self._confirm(f"CẬP NHẬT LAUNCHER {latest}", body, "Cập nhật ngay"):
            return

        def work(cb, op, cancel_ev):
            a = data["asset"]
            dest = self.pm.app_data_dir / "updates" / f"StellaSora_Launcher_{latest}.exe"
            self.network_service.download(
                data["download_url"],
                dest,
                a["size"],
                data["sha256"],
                cb,
                op,
                cancel_event=cancel_ev,
                should_cancel=cancel_ev.is_set,
            )
            schedule_update(dest, data["sha256"], self.pm.app_data_dir)
            return {"message": "Đã chuẩn bị bản cập nhật."}

        self._start_operation(
            "apply_self_update",
            work,
            initial_message=f"Đang tải bản cập nhật launcher {latest}...",
        )

    # ---------------- Support, Settings, Tools & Shortcuts ----------------

    def open_support(self) -> None:
        if self.shell is None:
            return
        if bool(getattr(core_config, "SUPPORT_DONATION_ENABLED", False)):
            self.shell.navigate_to("support")
        else:
            self.shell.show_support_locked_dialog()

    def open_notifications(self, notif_id: Optional[str] = None) -> None:
        if self.shell is not None:
            self.shell.navigate_to("notifications", notification_id=notif_id)

    def _sync_windows_autostart_from_config(self) -> None:
        if os.environ.get("QT_QPA_PLATFORM", "").lower() in ("offscreen", "minimal"):
            return
        try:
            if QGuiApplication.platformName().lower() in ("offscreen", "minimal"):
                return
        except Exception:  # noqa: BLE001
            pass
        enabled = bool(self.cm.get("guard_start_with_windows", False))
        ok, msg = set_windows_autostart(
            enabled,
            exe_path=Path(sys.executable) if self.pm.is_frozen else None,
            app_data_dir=self.pm.app_data_dir if self.pm.is_custom_app_data else None,
        )
        if not ok:
            logger.warning("Autostart update skipped/failed: %s", msg)

    def on_settings_saved(self, vals: dict[str, Any]) -> None:
        if self.shell is not None:
            self.shell.set_reduced_motion(bool(vals.get("reduced_motion", False)))
        if "guard_start_with_windows" in vals:
            self._sync_windows_autostart_from_config()
        self._trigger_bg_sync()
        self.sync_github(automatic=True)
        if vals.get("game_path") and str(vals["game_path"]) != str(self.current_game_info.game_path or ""):
            ctrl_ref = weakref.ref(self)
            QTimer.singleShot(
                0,
                lambda r=ctrl_ref, p=vals["game_path"]: (
                    r().select_game_root(p)
                    if r() is not None and r()._alive and _qt_is_valid(r())
                    else None
                ),
            )

    def on_settings_reset(self) -> None:
        if self.shell is not None:
            self.shell.set_reduced_motion(bool(self.cm.get("reduced_motion", False)))
        self._sync_windows_autostart_from_config()
        self.sync_github(automatic=True)

    def on_corrupt_preserved(self) -> None:
        self._configure_network()
        self.sync_github(automatic=True)

    def _on_reduced_motion_changed(self, enabled: bool) -> None:
        if self.shell is not None:
            self.shell.set_reduced_motion(bool(enabled))

    def _on_auto_sync_bg_changed(self, enabled: bool) -> None:
        if enabled:
            self._trigger_bg_sync()

    def _on_screen_error_raised(self, action: str, code: str, exc: object) -> None:
        e = exc if isinstance(exc, BaseException) else None
        self.show_error(action, code=code, exc=e, message=str(exc or ""))

    def create_shortcut_now(self) -> None:
        if not self.current_game_info.installed or not self.current_game_info.game_path:
            self.show_error("Tạo lối tắt vào game", code="E-NO-GAME-FOLDER")
            return
        ok, msg = create_game_shortcut(
            self.current_game_info.game_path,
            launcher_exe=Path(sys.executable) if self.pm.is_frozen else None,
            app_data_dir=self.pm.app_data_dir if self.pm.is_custom_app_data else None,
        )
        if ok:
            self.show_toast("Đã tạo lối tắt 'Stella Sora Việt Hóa' trên Desktop (có bảo vệ cập nhật).", "success")
        else:
            self.show_error("Tạo lối tắt vào game", code="E-SHORTCUT", message=msg)

    def clean_temp_cache(self) -> None:
        freed = purge_temp_cache(self.pm)
        if self.shell is not None:
            self.shell.tools_screen.refresh_live_metrics()
        self.show_toast(f"Đã dọn {freed / (1024.0 * 1024.0):.1f} MB tệp tạm.", "success")

    def copy_diagnostics_report(self) -> None:
        report = DiagnosticsCollector.collect(
            self.pm,
            self.current_game_info,
            refresh_running=True,
            config_data=self.cm.data,
        )
        txt = report.to_text()
        copy_text_native(txt)
        cb = QGuiApplication.clipboard()
        if cb is not None:
            cb.setText(txt)
        if self.shell is not None:
            self.shell.tools_screen.refresh_live_metrics()
        self.show_toast("Đã sao chép báo cáo chẩn đoán hệ thống.", "success")

    # ---------------- Smart Error Assistant & 8 Quick-Fix Handlers ----------------

    def _explain_blocker_code(self, blocker_code: str) -> None:
        info = self.current_game_info
        if not info.installed or not info.game_path:
            self.show_error("Cài đặt Việt hoá", code="E-NO-GAME-FOLDER")
        elif info.is_running:
            self.show_error("Cài đặt Việt hoá", code="E-GAME-RUNNING")
        else:
            state = self._refresh_translation_state()
            self.show_error(
                "Cài đặt Việt hoá",
                code=blocker_code or state.get("blocker_code") or "E-SYNC-PENDING",
                message=state.get("blocker_detail") or state.get("message", ""),
            )

    def _build_healthy_diagnostics_report(
        self,
        action: str,
        message: str,
        ctx: ErrorContext,
    ) -> ErrorReport:
        rid = new_report_id()
        title = "Hệ thống bình thường — Không phát hiện lỗi"
        steps = (
            'Bấm "Kiểm tra kết nối & DNS" để kiểm tra DNS, cổng 443 và TLS tới GitHub.',
            'Bấm "Mở thư mục game" nếu cần mở nhanh thư mục cài đặt Stella Sora.',
            'Bấm "Sao chép báo lỗi" hoặc "Xuất báo cáo" nếu cần gửi thông tin hệ thống.',
        )

        dns_val, dns_tone = "Chưa đo (bấm Kiểm tra kết nối)", "neutral"
        probe = ctx.probe if isinstance(ctx.probe, dict) else None
        verdict = str(probe.get("verdict") or "") if probe else ""
        if verdict:
            dns_val = {
                "ok": "GitHub: Kết nối tốt",
                "offline": "Mất Internet hoàn toàn",
                "dns_blocked": "Lỗi DNS GitHub · 1.1.1.1 OK",
                "dns_broken": "DNS hỏng · IP trực tiếp OK",
                "blocked": "Kết nối tới GitHub bị chặn",
                "captive_portal": "Captive Portal (cần đăng nhập Wi-Fi)",
            }.get(verdict, redact(verdict))
            dns_tone = "ok" if verdict == "ok" else ("warn" if verdict in ("dns_blocked", "dns_broken") else "danger")

        sys_rep = ctx.system_report
        disk_parts: list[str] = []
        disk_low = False
        app_gb = getattr(sys_rep, "disk_free_gb", 0.0) if sys_rep is not None else 0.0
        game_gb = getattr(sys_rep, "game_disk_free_gb", 0.0) if sys_rep is not None else 0.0
        if isinstance(app_gb, (int, float)) and app_gb > 0:
            disk_parts.append(f"AppData: {app_gb:.1f} GB")
            if app_gb < 1.0:
                disk_low = True
        if isinstance(game_gb, (int, float)) and game_gb > 0:
            disk_parts.append(f"Game: {game_gb:.1f} GB")
            if game_gb < 1.0:
                disk_low = True
        disk_val = " · ".join(disk_parts) if disk_parts else "Không đọc được"
        disk_tone = "warn" if disk_low else ("ok" if disk_parts else "neutral")

        gpath = str(self.current_game_info.game_path or "")
        context_rows = (
            {"label": "Thao tác", "value": redact(action), "tone": "neutral"},
            {"label": "Mã hệ thống", "value": "Không có lỗi hệ thống", "tone": "ok"},
            {"label": "DNS / Kết nối", "value": dns_val, "tone": dns_tone},
            {"label": "Ổ đĩa trống", "value": disk_val, "tone": disk_tone},
            {"label": "Tiến trình game", "value": "Đã đóng", "tone": "ok"},
            {"label": "Quyền ghi thư mục", "value": "Chưa kiểm tra", "tone": "neutral"},
            {"label": "Thư mục game", "value": redact(gpath) if gpath else "(không có)", "tone": "mono"},
        )

        sys_text = ""
        if sys_rep is not None and hasattr(sys_rep, "to_text"):
            try:
                sys_text = sys_rep.to_text()
            except Exception:  # noqa: BLE001
                sys_text = ""
        header_lines = [
            f"STELLA SORA VIỆT HOÁ — CHẨN ĐOÁN HỆ THỐNG OK (#{rid})",
            f"Nền tảng: Windows PC · Launcher v{LAUNCHER_VERSION}",
            f"Tiêu đề: {title}",
            f"Tóm tắt: {message}",
        ]
        if sys_text:
            header_lines.extend(["", sys_text])
        report_text = redact("\n".join(header_lines))

        return ErrorReport(
            code="OK",
            report_id=rid,
            title=title,
            summary=message,
            steps=steps,
            level="info",
            message=message,
            text=report_text,
            context_rows=context_rows,
            payload={
                "code": "OK",
                "report_id": rid,
                "level": "info",
                "title": title,
                "action": redact(action),
            },
        )

    def open_diagnostics_dialog(self) -> ErrorReport:
        """Open SmartErrorDialog proactively from the header 'Kiểm tra lỗi' button."""
        info = self.current_game_info
        state = self._refresh_translation_state()
        action = "Kiểm tra hệ thống & chẩn đoán"
        healthy_msg = (
            "Chưa phát hiện lỗi nghiêm trọng. Bạn có thể chạy kiểm tra kết nối, "
            "mở thư mục game hoặc sao chép báo cáo."
        )
        if not info.installed or not info.game_path:
            return self.show_error(
                action,
                code="E-NO-GAME-FOLDER",
                message="Chưa chọn thư mục cài đặt Stella Sora.",
            )
        if info.is_running:
            return self.show_error(
                action,
                code="E-GAME-RUNNING",
                message="Tiến trình StellaSora.exe đang chạy.",
            )
        if getattr(self.cm, "_corrupt", False):
            return self.show_error(
                action,
                code="E-MIGRATION",
                message="Tệp cấu hình trước đó bị lỗi định dạng và đang được giữ nguyên để tham chiếu.",
            )
        try:
            if self._engine().pending(info.game_path):
                return self.show_error(
                    action,
                    code="E-RECOVERY-REQUIRED",
                    message="Phát hiện nhật ký cài đặt hoặc khôi phục chưa hoàn tất.",
                )
        except Exception:  # noqa: BLE001
            pass
        blocker = str(state.get("blocker_code") or "").strip()
        if blocker and blocker != "E-SYNC-PENDING":
            return self.show_error(
                action,
                code=blocker,
                message=str(state.get("blocker_detail") or state.get("message") or healthy_msg),
            )
        if getattr(self.current_bg_frame, "warning_code", None) == "E-BG-SYNC":
            return self.show_error(
                action,
                code="E-BG-SYNC",
                message="Đồng bộ hình nền từ Official Launcher không thành công, đang dùng ảnh dự phòng.",
            )

        ctx = self._error_context(action)
        report = self._build_healthy_diagnostics_report(action, healthy_msg, ctx)
        self._last_report = report
        if self.shell is not None and self._alive and not self._closing and _qt_is_valid(self.shell):
            if self.shell._active_modal is not None or bool(getattr(self.shell, "_modal_stack", None)):
                self.shell.show_toast(
                    f"{report.title} [{report.code}]",
                    tone="info",
                )
            else:
                dlg = SmartErrorDialog(
                    report,
                    ctx,
                    controller=self,
                    parent=self.shell,
                    asset_renderer=self.shell._renderer,
                )
                self.shell.show_modal(dlg)
        return report

    def _error_context(
        self,
        action: str = "",
        *,
        probe: Any = None,
        extra: Optional[dict[str, Any]] = None,
        operation: str = "",
        win32_error: Optional[int] = None,
        http_status: Optional[int] = None,
        target_file: str = "",
        target_url: str = "",
        writability: Any = None,
    ) -> ErrorContext:
        sync = dict(self._github_sync_state) if isinstance(self._github_sync_state, dict) else {}
        info_extra: dict[str, Any] = {
            "tuỳ chọn": (
                f"tự kiểm tra cập nhật={self.cm.get('check_updates_on_start', True)}, "
                f"tự kiểm tra bản gốc={self.cm.get('check_official_on_start', True)}, "
                f"tự khôi phục trước khi game cập nhật={self.cm.get('auto_restore_before_game_update', False)}"
            ),
            "gói cục bộ": "có" if self.cm.get("payload_path", "") else "không",
            "bảng kê tuỳ chỉnh": "có" if self.cm.get("custom_manifest_url", "") else "không",
            "graphics_mode": self.cm.get("graphics_mode", "auto"),
            "reduced_motion": bool(self.cm.get("reduced_motion", False)),
        }
        try:
            g = self.current_game_info
            if g and g.installed and g.game_path:
                info_extra["nhật ký chưa hoàn tất"] = "CÓ" if self._engine().pending(g.game_path) else "không"
        except Exception:  # noqa: BLE001
            info_extra["nhật ký chưa hoàn tất"] = "không đọc được"
        if extra:
            info_extra.update(extra)

        cfg_data = dict(self.cm.data)
        cfg_data["_corrupt"] = bool(getattr(self.cm, "_corrupt", False))

        sys_report = DiagnosticsCollector.collect(
            self.pm,
            self.current_game_info,
            win32_error_code=win32_error,
            http_status=http_status,
            target_file=target_file,
            target_url=target_url,
            check_writability=False,
            refresh_running=False,
            config_data=cfg_data,
        )

        return ErrorContext(
            action=action,
            operation=operation,
            progress=self._last_progress_message,
            path_manager=self.pm,
            game=self.current_game_info,
            sync=sync,
            channel=self._channel,
            probe=probe or sync.get("probe"),
            extra=info_extra,
            win32_error=win32_error,
            http_status=http_status,
            target_file=target_file,
            target_url=target_url,
            system_report=sys_report,
            config=cfg_data,
            writability=writability,
        )

    def show_error(
        self,
        action: str,
        *,
        code: Optional[str] = None,
        exc: Optional[BaseException] = None,
        message: str = "",
        probe: Any = None,
        extra: Optional[dict[str, Any]] = None,
        extra_summary: str = "",
        operation: str = "",
        target_file: str = "",
        target_url: str = "",
        win32_error: Optional[int] = None,
        http_status: Optional[int] = None,
        writability: Any = None,
        show: bool = True,
    ) -> ErrorReport:
        # Auto-probe writability for file/permission codes if not yet provided
        resolved_writability = writability
        if resolved_writability is None and code in _WRITABILITY_ERROR_CODES:
            check_dir = (
                Path(target_file).parent
                if target_file
                else (
                    Path(self.current_game_info.game_path)
                    if self.current_game_info.game_path
                    else self.pm.app_data_dir
                )
            )
            try:
                resolved_writability = probe_dir_writability(check_dir)
            except Exception:  # noqa: BLE001
                resolved_writability = None

        ctx = self._error_context(
            action,
            probe=probe,
            extra=extra,
            operation=operation,
            win32_error=win32_error,
            http_status=http_status,
            target_file=target_file,
            target_url=target_url,
            writability=resolved_writability,
        )
        report = build_report(
            code,
            exc=exc,
            message=message,
            action=action,
            ctx=ctx,
            extra_summary=extra_summary,
        )
        self._last_report = report

        if show and self.shell is not None and self._alive and not self._closing and _qt_is_valid(self.shell):
            if self.shell._active_modal is not None or bool(getattr(self.shell, "_modal_stack", None)):
                logger.warning(
                    "Active modal open; surfacing error %s (%s) via toast instead of stacking SmartErrorDialog",
                    report.code,
                    action,
                )
                self.shell.show_toast(
                    f"{report.title or action} [{report.code}]",
                    tone="error" if report.is_error else "warn",
                )
            else:
                dlg = SmartErrorDialog(
                    report,
                    ctx,
                    controller=self,
                    parent=self.shell,
                    asset_renderer=self.shell._renderer,
                )
                self.shell.show_modal(dlg)
        return report

    def show_unhandled(self, exc: BaseException) -> None:
        if self._showing_unhandled:
            return
        self._showing_unhandled = True
        try:
            self.show_error("Lỗi không mong đợi", exc=exc, message=str(exc))
        except Exception:  # noqa: BLE001
            logger.exception("Could not display unhandled error")
        finally:
            self._showing_unhandled = False

    def execute_quick_fix(
        self,
        action: QuickFixAction,
        dialog: Optional[SmartErrorDialog] = None,
    ) -> None:
        aid = action.action_id

        if aid == "copy_report":
            if dialog is not None:
                dialog._on_copy_clicked()
            elif self._last_report is not None:
                copy_text_native(self._last_report.text)
                cb = QGuiApplication.clipboard()
                if cb is not None:
                    cb.setText(self._last_report.text)
                self.show_toast("Đã sao chép gói báo lỗi.", "success")
            return

        if aid == "probe_network":
            if dialog is not None:
                dialog.set_probe_running()
            self._run_async_probe(dialog)
            return

        if aid == "open_game_dir":
            raw_target = action.params.get("target_dir") if isinstance(action.params, dict) else None
            cand = (
                Path(raw_target)
                if raw_target
                else (
                    Path(self.current_game_info.game_path)
                    if self.current_game_info.game_path
                    else self.pm.app_data_dir
                )
            )
            target = cand
            while target and not target.exists() and target.parent != target:
                target = target.parent
            if target.exists() and hasattr(os, "startfile"):
                try:
                    os.startfile(str(target))
                    self.show_toast(f"Đã mở thư mục: {target.name or target}", "info")
                except OSError as exc:
                    self.show_toast(f"Không mở được thư mục: {exc}", "warn")
            else:
                self.show_toast("Không tìm thấy thư mục đích trên đĩa.", "warn")
            return

        if aid == "close_game":
            if dialog is not None:
                dialog.accept()
                self._pending_post_op_modal = True
                ctrl_ref = weakref.ref(self)
                QTimer.singleShot(
                    0,
                    lambda r=ctrl_ref: (
                        r()._deferred_close_game_quick_fix()
                        if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                        else None
                    ),
                )
                return
            self._run_close_game_quick_fix()
            return

        if aid == "relaunch_admin":
            if is_process_admin():
                self.show_toast("Launcher đã chạy với quyền Quản trị.", "info")
                return
            if self._relaunch_self(runas=True):
                if dialog is not None:
                    dialog.accept()
                if self.shell is not None:
                    self.shell.request_real_quit()
                if QApplication.instance() is not None:
                    QTimer.singleShot(50, QApplication.instance().quit)
            else:
                self.show_toast("Không thể mở lại bằng quyền Quản trị (người dùng hủy UAC).", "warn")
            return

        if aid == "switch_safe_graphics":
            if not getattr(self.cm, "_corrupt", False):
                self.cm.set("graphics_mode", "software")
                self.cm.set("reduced_motion", True)
                self.cm.save()
            if self.shell is not None:
                self.shell.set_reduced_motion(True)
            if self._relaunch_self(runas=False, safe_graphics=True):
                if dialog is not None:
                    dialog.accept()
                if self.shell is not None:
                    self.shell.request_real_quit()
                if QApplication.instance() is not None:
                    QTimer.singleShot(50, QApplication.instance().quit)
            else:
                self.show_toast("Đã lưu chế độ đồ họa tương thích — hãy mở lại launcher.", "info")
            return

        if aid == "reset_config":
            if dialog is not None:
                dialog.accept()
                self._pending_post_op_modal = True
                ctrl_ref = weakref.ref(self)
                QTimer.singleShot(
                    0,
                    lambda r=ctrl_ref: (
                        r()._deferred_reset_config_quick_fix()
                        if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                        else None
                    ),
                )
                return
            self._run_reset_config_quick_fix()
            return

        if aid == "restore_official":
            if dialog is not None:
                dialog.accept()
            self._pending_post_op_modal = True
            ctrl_ref = weakref.ref(self)
            QTimer.singleShot(
                0,
                lambda r=ctrl_ref: (
                    r()._deferred_restore_official()
                    if r() is not None and r()._alive and not r()._closing and _qt_is_valid(r())
                    else None
                ),
            )
            return

    def _run_close_game_quick_fix(self) -> None:
        if not self._confirm(
            "Đóng tiến trình StellaSora.exe",
            "Launcher sẽ đóng game Stella Sora đang chạy để mở khóa tệp game. "
            "Hãy lưu tiến trình chơi trước khi tiếp tục.",
            "Đóng game",
            is_danger=True,
        ):
            return
        ok, msg = _terminate_game_process_by_path(self.current_game_info.game_path)
        self._poll_game_running()
        self.show_toast(msg, "success" if ok else "warn")

    def _deferred_close_game_quick_fix(self) -> None:
        self._pending_post_op_modal = False
        if not self._alive or self._closing or not _qt_is_valid(self) or not self._can_open_modal():
            return
        self._run_close_game_quick_fix()

    def _run_reset_config_quick_fix(self) -> None:
        if not self._confirm(
            "Khôi phục cấu hình mặc định",
            "Launcher sẽ đổi tên tệp config.json cũ/hỏng để lưu giữ nguyên vẹn "
            "và tạo cấu hình mặc định mới an toàn.",
            "Khôi phục mặc định",
        ):
            return
        self.cm.preserve_corrupt_and_reset()
        self._configure_network()
        if self.shell is not None:
            self.shell.settings_screen.refresh_from_config()
            self.shell.set_reduced_motion(bool(self.cm.get("reduced_motion", False)))
        self.sync_github(automatic=True)
        self.show_toast("Đã khôi phục cấu hình mặc định.", "success")

    def _deferred_reset_config_quick_fix(self) -> None:
        self._pending_post_op_modal = False
        if not self._alive or self._closing or not _qt_is_valid(self) or not self._can_open_modal():
            return
        self._run_reset_config_quick_fix()

    def _deferred_restore_official(self) -> None:
        self._pending_post_op_modal = False
        if not self._alive or self._closing or not _qt_is_valid(self) or not self._can_open_modal():
            return
        self.rollback_official(confirm=True)

    def _run_async_probe(self, dialog: Optional[SmartErrorDialog]) -> None:
        self_ref = weakref.ref(self)
        dlg_ref = weakref.ref(dialog) if dialog is not None else None

        def _worker() -> None:
            try:
                probe = run_probe()
            except Exception as exc:  # noqa: BLE001
                probe = {"verdict": "error", "verdict_text": f"Lỗi đo kết nối: {exc}", "hosts": {}, "control": {}}
            ctrl = self_ref()
            d_obj = dlg_ref() if dlg_ref is not None else None
            if ctrl is not None and ctrl._alive and _qt_is_valid(ctrl):
                try:
                    ctrl._probe_ready_signal.emit(d_obj, probe)
                except RuntimeError:
                    pass

        threading.Thread(target=_worker, name="launcher_v2_net_probe", daemon=True).start()

    def _on_async_probe_ready(self, dialog: object, probe: dict[str, Any]) -> None:
        if not self._alive:
            return
        if isinstance(dialog, SmartErrorDialog) and _qt_is_valid(dialog):
            dialog.set_probe_result(probe)

    def _relaunch_self(self, *, runas: bool, safe_graphics: bool = False) -> bool:
        args: list[str] = []
        if not getattr(sys, "frozen", False):
            app_py = Path(__file__).resolve().parents[1] / "app.py"
            args.append(str(app_py))
        if self.pm.is_custom_app_data:
            args.extend(["--app-data-dir", str(self.pm.app_data_dir)])
        if safe_graphics or self.software_rendering:
            args.append("--safe-graphics")

        try:
            if runas and sys.platform == "win32":
                import ctypes

                params = subprocess.list2cmdline(args)
                rc = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    sys.executable,
                    params,
                    str(self.pm.exe_dir),
                    1,
                )
                return int(rc) > 32
            subprocess.Popen(
                [sys.executable, *args],
                cwd=str(self.pm.exe_dir),
                creationflags=subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Relaunch failed: %s", exc)
            return False


def launch_gui(
    *,
    app: QApplication,
    path_manager: PathManager,
    config_manager: ConfigManager,
    software_rendering: bool = False,
    startup_warnings: Optional[list[Exception]] = None,
    start_in_tray: bool = False,
    launch_guard_notice: Optional[dict[str, Any]] = None,
) -> MainShell:
    """Create AppController + MainShell, register fonts/QSS/icon, show window, and return MainShell.

    Must NOT call app.exec() so app.py retains ownership of the event loop and
    its QTimer.singleShot(3000, _clear_sentinel) graphics crash guard.
    """
    register_fonts(path_manager.resource_dir)
    app.setFont(ui_font(FS_BODY, 400))
    app.setStyleSheet(build_application_qss(path_manager.resource_dir))

    renderer = get_asset_renderer(path_manager.resource_dir)
    for rel in ("branding/app_icon.ico", "branding/app_icon.png"):
        icon_path = renderer.resolve_path(rel)
        if icon_path.is_file():
            app.setWindowIcon(QIcon(str(icon_path)))
            break

    controller = AppController(
        path_manager,
        config_manager,
        software_rendering=software_rendering,
        startup_warnings=startup_warnings or [],
        start_in_tray=start_in_tray,
        launch_guard_notice=launch_guard_notice,
    )
    shell = MainShell(
        path_manager,
        config_manager,
        controller=controller,
        software_rendering=software_rendering,
        asset_renderer=renderer,
    )
    controller.attach_shell(shell)
    if start_in_tray and launch_guard_notice is None and shell.is_tray_active():
        shell.hide()
    else:
        shell.show()
    QTimer.singleShot(0, controller.start_initial_loads)
    return shell
