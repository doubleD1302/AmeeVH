# -*- coding: utf-8 -*-
"""
ToolsScreen — Light Porcelain 2-column 4+4 flat hairline diagnostics & utilities grid.

Features:
- DỮ LIỆU GAME: Yostar check, Official vanilla restore, SHA256 verify, pending journal scan
- TIỆN ÍCH & CHẨN ĐOÁN: Unicode Desktop shortcut, live temp cache cleanup (payload_root + stale
  bg_cache + updates/ only — NEVER touching backup_root or journals_dir), DiagnosticsCollector
  summary & PII-redacted copy, and non-blocking async AdbBridge().list_devices() scan via daemon worker thread
"""
from __future__ import annotations

import atexit
import json
import shutil
import sys
import threading
import weakref
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt, SIGNAL, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

try:
    from shiboken6 import isValid as _qt_is_valid
except ImportError:  # pragma: no cover
    def _qt_is_valid(_obj: object) -> bool:
        return True

from ...core import tls
from ...core.config import PathManager
from ...core.diagnostics import AdbBridge, DiagnosticsCollector
from ...core.error_report import copy_text_native
from ...core.installer import PatchInstaller
from ...core.types import GameInfo
from ..theme.tokens import LAYOUT_TOKENS, PORCELAIN_TOKENS
from ..theme.typography import FS_BODY_SM, FS_CTA_SM, nfc, ui_font
from ..widgets import (
    ActionButton,
    AssetRenderer,
    PorcelainSectionBar,
    PorcelainWindowFrame,
    get_asset_renderer,
)


def _dir_size_bytes(path: Path) -> int:
    total = 0
    if not path.is_dir():
        return 0
    try:
        for p in path.rglob("*"):
            try:
                if p.is_file() and not p.is_symlink():
                    total += p.stat().st_size
            except OSError:
                continue
    except OSError:
        pass
    return total


def _active_bg_cache_files(bg_cache_dir: Path) -> set[Path]:
    protected: set[Path] = set()
    meta_file = bg_cache_dir / "meta.json"
    if meta_file.is_file():
        protected.add(meta_file.resolve())
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            if isinstance(meta, dict):
                for key in ("image_path", "still_fallback_path"):
                    val = meta.get(key)
                    if isinstance(val, str) and val:
                        protected.add(Path(val).resolve())
        except (OSError, ValueError):
            pass
    return protected


def compute_temp_cache_bytes(pm: PathManager | None) -> int:
    """Compute reclaimable bytes across payload_root, stale bg_cache, and updates/.

    Strictly NEVER reads or deletes backup_root or journals_dir.
    """
    if pm is None:
        return 0
    total = _dir_size_bytes(pm.payload_root)
    updates_dir = pm.app_data_dir / "updates"
    total += _dir_size_bytes(updates_dir)

    bg_dir = pm.bg_cache_dir
    if bg_dir.is_dir():
        protected = _active_bg_cache_files(bg_dir)
        try:
            for item in bg_dir.iterdir():
                try:
                    if item.is_file() and not item.is_symlink() and item.resolve() not in protected:
                        total += item.stat().st_size
                except OSError:
                    continue
        except OSError:
            pass
    return total


def purge_temp_cache(pm: PathManager | None) -> int:
    """Delete reclaimable temp files while preserving backup_root, journals_dir, and active BG."""
    if pm is None:
        return 0
    freed = 0
    if pm.payload_root.is_dir():
        for child in list(pm.payload_root.iterdir()):
            try:
                if child.is_symlink():
                    continue
                if child.is_dir():
                    freed += _dir_size_bytes(child)
                    shutil.rmtree(child, ignore_errors=True)
                elif child.is_file():
                    freed += child.stat().st_size
                    child.unlink(missing_ok=True)
            except OSError:
                continue

    updates_dir = pm.app_data_dir / "updates"
    if updates_dir.is_dir():
        for child in list(updates_dir.iterdir()):
            try:
                if child.is_file() and not child.is_symlink():
                    freed += child.stat().st_size
                    child.unlink(missing_ok=True)
            except OSError:
                continue

    bg_dir = pm.bg_cache_dir
    if bg_dir.is_dir():
        protected = _active_bg_cache_files(bg_dir)
        for child in list(bg_dir.iterdir()):
            try:
                if child.is_file() and not child.is_symlink() and child.resolve() not in protected:
                    freed += child.stat().st_size
                    child.unlink(missing_ok=True)
            except OSError:
                continue
    return freed


_ADB_SHUTTING_DOWN = False
_ACTIVE_ADB_LOCK = threading.Lock()
_ACTIVE_ADB_CANCELS: weakref.WeakSet[threading.Event] = weakref.WeakSet()


@atexit.register
def _mark_adb_shutdown() -> None:
    global _ADB_SHUTTING_DOWN
    _ADB_SHUTTING_DOWN = True
    with _ACTIVE_ADB_LOCK:
        for ev in list(_ACTIVE_ADB_CANCELS):
            ev.set()


class _AdbSignalBridge(QObject):
    """Unparented GUI-thread signal bridge for daemon ADB scan threads."""

    devices_ready = Signal(int, bool, list)  # scan_gen, adb_available, devices


class _ToolRow(QFrame):
    """Flat hairline zebra row with title + description on left, ActionButton on right."""

    def __init__(
        self,
        title: str,
        description: str,
        button_label: str,
        *,
        icon_path: str,
        icon_size: tuple[int, int] = (14, 14),
        icon_tint: str | None = PORCELAIN_TOKENS.NAVY_TEXT,
        is_odd: bool,
        is_last: bool,
        asset_renderer: AssetRenderer,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        p = PORCELAIN_TOKENS
        bg = p.ICE_ROW_ALT if is_odd else p.WHITE
        bottom = "none" if is_last else f"1px solid {p.HAIRLINE_CELL}"
        self.setObjectName("toolsFlatRow")
        self.setStyleSheet(
            f"QFrame#toolsFlatRow {{ background: {bg}; border: none; border-bottom: {bottom}; }}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(12)

        info_col = QVBoxLayout()
        info_col.setContentsMargins(0, 0, 0, 0)
        info_col.setSpacing(4)

        self.title_label = QLabel(nfc(title), self)
        self.title_label.setFont(ui_font(FS_CTA_SM, 700))
        self.title_label.setStyleSheet(f"color: {p.NAVY_TEXT}; background: transparent;")
        info_col.addWidget(self.title_label)

        self.desc_label = QLabel(nfc(description), self)
        self.desc_label.setFont(ui_font(FS_BODY_SM, 400))
        self.desc_label.setWordWrap(True)
        self.desc_label.setTextFormat(Qt.TextFormat.RichText)
        self.desc_label.setStyleSheet(f"color: {p.SLATE_BODY}; background: transparent;")
        info_col.addWidget(self.desc_label)
        lay.addLayout(info_col, 1)

        self.action_button = ActionButton(
            button_label,
            variant="light_secondary",
            icon_path=icon_path,
            icon_size=icon_size,
            icon_tint=icon_tint,
            height=32,
            asset_renderer=asset_renderer,
            parent=self,
        )
        lay.addWidget(self.action_button, 0, Qt.AlignmentFlag.AlignVCenter)

    def set_description_html(self, html_text: str) -> None:
        self.desc_label.setText(nfc(html_text))


class ToolsScreen(QWidget):
    """Porcelain 2-column 4+4 Advanced Tools & Diagnostics screen."""

    close_requested = Signal()
    official_check_requested = Signal()
    official_restore_requested = Signal()
    verify_requested = Signal()
    recover_requested = Signal()
    create_shortcut_requested = Signal()
    clean_temp_requested = Signal()
    copy_diagnostics_requested = Signal()
    adb_scan_completed = Signal(list)
    toast_requested = Signal(str, str)

    def __init__(
        self,
        *,
        path_manager: PathManager | None = None,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._pm = path_manager
        self._renderer = asset_renderer or get_asset_renderer(
            path_manager.resource_dir if path_manager is not None else None
        )
        self._game_info = GameInfo()
        self._github_ok: Optional[bool] = None
        self._adb_lock = threading.Lock()
        self._adb_gen_box: list[int] = [0]
        self._adb_alive_box: list[bool] = [True]
        self._adb_scanning: bool = False
        self._adb_cancel_box: list[Optional[threading.Event]] = [None]
        self._adb_bridge = _AdbSignalBridge()
        self._adb_bridge.devices_ready.connect(
            self._on_adb_devices_ready,
            Qt.ConnectionType.QueuedConnection,
        )
        self._last_adb_desc_html: str = (
            f"<span style='color:{PORCELAIN_TOKENS.SLATE_MUTED};'>0 thiết bị kết nối</span> · Chỉ đọc qua USB / Wi-Fi."
        )

        app_inst = QCoreApplication.instance()
        if app_inst is not None:
            self_ref = weakref.ref(self)

            def _on_app_about_to_quit() -> None:
                screen = self_ref()
                if screen is not None and _qt_is_valid(screen):
                    try:
                        screen.shutdown_workers()
                    except RuntimeError:
                        pass

            app_inst.aboutToQuit.connect(_on_app_about_to_quit)
            about_to_quit_cb = _on_app_about_to_quit
            app_ref: Optional[weakref.ReferenceType[QCoreApplication]] = weakref.ref(app_inst)
        else:
            about_to_quit_cb = None
            app_ref = None

        lock = self._adb_lock
        alive_box = self._adb_alive_box
        cancel_box = self._adb_cancel_box
        bridge_ref = weakref.ref(self._adb_bridge)

        def _on_screen_destroyed(_obj: object = None) -> None:
            with lock:
                alive_box[0] = False
                if cancel_box[0] is not None:
                    cancel_box[0].set()
                    cancel_box[0] = None
            bridge = bridge_ref()
            if bridge is not None and _qt_is_valid(bridge):
                try:
                    bridge.deleteLater()
                except RuntimeError:
                    pass
            if about_to_quit_cb is not None and app_ref is not None:
                app_obj = app_ref()
                if app_obj is not None and _qt_is_valid(app_obj):
                    try:
                        app_obj.aboutToQuit.disconnect(about_to_quit_cb)
                    except (RuntimeError, TypeError):
                        pass

        self.destroyed.connect(_on_screen_destroyed)

        self.setObjectName("toolsScreen")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
        )
        outer.setSpacing(0)

        self.frame = PorcelainWindowFrame(
            "Công cụ",
            meta="Kiểm tra dữ liệu, khôi phục bản gốc và chẩn đoán",
            icon_path="game/btn_menu_s_toolbox_light.png",
            icon_size=(22, 22),
            asset_renderer=self._renderer,
            parent=self,
        )
        self.frame.close_requested.connect(self.close_requested.emit)
        outer.addWidget(self.frame)

        p = PORCELAIN_TOKENS
        self.scroll_area = QScrollArea(self.frame)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"background: {p.WHITE}; border: none;")

        grid_host = QWidget(self.scroll_area)
        grid_host.setStyleSheet(f"background: {p.WHITE};")
        self._grid_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, grid_host)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(0)

        # Column 1: DỮ LIỆU GAME (4 rows)
        self.col_game = QFrame(grid_host)
        self.col_game.setObjectName("toolsGameCol")
        self.col_game.setStyleSheet(
            f"QFrame#toolsGameCol {{ background: {p.WHITE}; border: none; border-right: 1px solid {p.HAIRLINE}; }}"
        )
        g_lay = QVBoxLayout(self.col_game)
        g_lay.setContentsMargins(0, 0, 0, 0)
        g_lay.setSpacing(0)

        g_lay.addWidget(PorcelainSectionBar("Dữ liệu game", self.col_game))

        self.row_official_check = _ToolRow(
            "Kiểm tra bản vá Yostar",
            "So sánh phiên bản tài nguyên hiện tại (<code>—</code>) với máy chủ Yostar.",
            "Kiểm tra",
            icon_path="game/btn_common_refresh.png",
            icon_tint=p.NAVY_TEXT,
            is_odd=True,
            is_last=False,
            asset_renderer=self._renderer,
            parent=self.col_game,
        )
        self.row_official_check.action_button.clicked.connect(self.official_check_requested.emit)
        g_lay.addWidget(self.row_official_check, 1)

        self.row_official_restore = _ToolRow(
            "Tải lại bản gốc từ Yostar",
            "Khôi phục tệp gốc sạch từ máy chủ Yostar và gỡ bản Việt hoá.",
            "Khôi phục gốc",
            icon_path="game/btn_icon_back.png",
            icon_tint=p.NAVY_TEXT,
            is_odd=False,
            is_last=False,
            asset_renderer=self._renderer,
            parent=self.col_game,
        )
        self.row_official_restore.action_button.clicked.connect(self.official_restore_requested.emit)
        g_lay.addWidget(self.row_official_restore, 1)

        self.row_verify_files = _ToolRow(
            "Kiểm tra tệp Việt hoá",
            "Đối chiếu mã SHA256 các tệp <code>.arcx</code> đã cài.",
            "Kiểm tra",
            icon_path="game/btn_common_check.png",
            icon_size=(18, 18),
            icon_tint=None,
            is_odd=True,
            is_last=False,
            asset_renderer=self._renderer,
            parent=self.col_game,
        )
        self.row_verify_files.action_button.clicked.connect(self.verify_requested.emit)
        g_lay.addWidget(self.row_verify_files, 1)

        self.row_recover_journals = _ToolRow(
            "Phục hồi cài đặt dang dở",
            f"Trạng thái: <b style='color:{p.OK_TEXT};'>Sạch</b> (không có thao tác treo).",
            "Quét nhật ký",
            icon_path="game/btn_login_repair.png",
            icon_tint=None,
            is_odd=False,
            is_last=True,
            asset_renderer=self._renderer,
            parent=self.col_game,
        )
        self.row_recover_journals.action_button.clicked.connect(self.recover_requested.emit)
        g_lay.addWidget(self.row_recover_journals, 1)

        self._grid_layout.addWidget(self.col_game, 1)

        # Column 2: TIỆN ÍCH & CHẨN ĐOÁN (4 rows)
        self.col_utils = QFrame(grid_host)
        self.col_utils.setObjectName("toolsUtilsCol")
        self.col_utils.setStyleSheet(f"QFrame#toolsUtilsCol {{ background: {p.WHITE}; border: none; }}")
        u_lay = QVBoxLayout(self.col_utils)
        u_lay.setContentsMargins(0, 0, 0, 0)
        u_lay.setSpacing(0)

        u_lay.addWidget(PorcelainSectionBar("Tiện ích & Chẩn đoán", self.col_utils))

        self.row_shortcut = _ToolRow(
            "Tạo lối tắt vào game",
            "Tạo shortcut trên Desktop (hỗ trợ tên thư mục tiếng Việt).",
            "Tạo lối tắt",
            icon_path="game/asar_path_navy.svg",
            icon_tint=None,
            is_odd=True,
            is_last=False,
            asset_renderer=self._renderer,
            parent=self.col_utils,
        )
        self.row_shortcut.action_button.clicked.connect(self.create_shortcut_requested.emit)
        u_lay.addWidget(self.row_shortcut, 1)

        self.row_clean_temp = _ToolRow(
            "Dọn tệp tạm",
            f"Giải phóng <b style='color:{p.NAVY_SOLID};'>0.0 MB</b> tệp tải tạm &amp; ảnh nền cũ (không xóa bản sao lưu).",
            "Dọn ngay",
            icon_path="game/btn_icon_reset.png",
            icon_tint=p.NAVY_TEXT,
            is_odd=False,
            is_last=False,
            asset_renderer=self._renderer,
            parent=self.col_utils,
        )
        self.row_clean_temp.action_button.clicked.connect(self._on_clean_temp_clicked)
        u_lay.addWidget(self.row_clean_temp, 1)

        self.row_diagnostics = _ToolRow(
            "Kiểm tra hệ thống & Mạng",
            "Chứng chỉ TLS: <b>—</b> · Kết nối GitHub: <b>Chưa kiểm tra</b>",
            "Sao chép báo cáo",
            icon_path="game/btn_icon_copy.png",
            icon_tint=p.NAVY_TEXT,
            is_odd=True,
            is_last=False,
            asset_renderer=self._renderer,
            parent=self.col_utils,
        )
        self.row_diagnostics.action_button.clicked.connect(self._on_copy_diag_clicked)
        u_lay.addWidget(self.row_diagnostics, 1)

        self.row_adb = _ToolRow(
            "Kết nối Android (ADB)",
            f"<span style='color:{p.SLATE_MUTED};'>0 thiết bị kết nối</span> · Chỉ đọc qua USB / Wi-Fi.",
            "Quét thiết bị",
            icon_path="game/asar_proxy_navy.svg",
            icon_tint=None,
            is_odd=False,
            is_last=True,
            asset_renderer=self._renderer,
            parent=self.col_utils,
        )
        self.row_adb.action_button.clicked.connect(self.scan_adb_devices)
        u_lay.addWidget(self.row_adb, 1)

        self._grid_layout.addWidget(self.col_utils, 1)

        self.scroll_area.setWidget(grid_host)
        self.frame.set_body(self.scroll_area)

        self.refresh_live_metrics()

    def bind_path_manager(self, path_manager: PathManager) -> None:
        self._pm = path_manager
        self.refresh_live_metrics()

    def set_game_info(self, game_info: GameInfo) -> None:
        self._game_info = game_info
        self.refresh_live_metrics()

    def set_network_status(self, github_ok: Optional[bool]) -> None:
        self._github_ok = github_ok
        self._refresh_diagnostics_summary()

    def refresh_live_metrics(self) -> None:
        p = PORCELAIN_TOKENS
        res_ver = (
            self._game_info.resource_version
            if self._game_info.resource_version and self._game_info.resource_version != "unknown"
            else "—"
        )
        self.row_official_check.set_description_html(
            f"So sánh phiên bản tài nguyên hiện tại (<code>{res_ver}</code>) với máy chủ Yostar."
        )

        # Pending journal count (never throws into UI)
        pending_count = self._count_pending_journals()
        if pending_count == 0:
            self.row_recover_journals.set_description_html(
                f"Trạng thái: <b style='color:{p.OK_TEXT};'>Sạch</b> (không có thao tác treo)."
            )
        else:
            self.row_recover_journals.set_description_html(
                f"Trạng thái: <b style='color:{p.WARN_ICON};'>Phát hiện {pending_count} thao tác dang dở</b>."
            )

        temp_mb = compute_temp_cache_bytes(self._pm) / (1024.0 * 1024.0)
        self.row_clean_temp.set_description_html(
            f"Giải phóng <b style='color:{p.NAVY_SOLID};'>{temp_mb:.1f} MB</b> tệp tải tạm &amp; ảnh nền cũ (không xóa bản sao lưu)."
        )

        self._refresh_diagnostics_summary()

    def _count_pending_journals(self) -> int:
        if self._pm is None:
            return 0
        try:
            if self._game_info.game_path is not None:
                installer = PatchInstaller(self._pm.backup_root, self._pm.journals_dir)
                return len(installer.pending(self._game_info.game_path))
            count = 0
            for jf in self._pm.journals_dir.glob("*.json"):
                try:
                    data = json.loads(jf.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and data.get("state") not in (
                        "done",
                        "rolled_back",
                        "restored",
                        "superseded",
                    ):
                        count += 1
                except (OSError, ValueError):
                    continue
            return count
        except Exception:  # noqa: BLE001
            return 0

    def _refresh_diagnostics_summary(self) -> None:
        p = PORCELAIN_TOKENS
        tls_ok_txt = f"<b style='color:{p.OK_TEXT};'>OK</b>"
        try:
            t_info = tls.info()
            if not t_info or int(t_info.get("trusted_roots", 0)) <= 0:
                tls_ok_txt = f"<b style='color:{p.WARN_ICON};'>Thiếu gốc</b>"
        except Exception:  # noqa: BLE001
            tls_ok_txt = f"<b style='color:{p.DANGER_TEXT};'>Lỗi</b>"

        if self._github_ok is True:
            net_txt = f"<b style='color:{p.OK_TEXT};'>OK</b>"
        elif self._github_ok is False:
            net_txt = f"<b style='color:{p.DANGER_TEXT};'>Lỗi</b>"
        else:
            net_txt = f"<b style='color:{p.SLATE_MUTED};'>Chờ đồng bộ</b>"

        drive_txt = "C:"
        free_gb = 0.0
        try:
            target = (
                Path(self._game_info.game_path)
                if self._game_info.game_path
                else (self._pm.app_data_dir if self._pm is not None else Path.cwd())
            )
            drive_txt = (target.drive or "C:").rstrip("\\/") or "C:"
            free_gb = shutil.disk_usage(target if target.exists() else target.anchor).free / (1024 ** 3)
        except Exception:  # noqa: BLE001
            pass

        self.row_diagnostics.set_description_html(
            f"Chứng chỉ TLS: {tls_ok_txt} · Kết nối GitHub: {net_txt} · Ổ {drive_txt} còn {free_gb:.1f} GB"
        )

    def _on_clean_temp_clicked(self) -> None:
        self.clean_temp_requested.emit()
        if self.receivers(SIGNAL("clean_temp_requested()")) <= 0 and self._pm is not None:
            freed = purge_temp_cache(self._pm)
            self.refresh_live_metrics()
            self.toast_requested.emit(
                nfc(f"Đã dọn {freed / (1024.0 * 1024.0):.1f} MB tệp tạm."),
                "success",
            )

    def _on_copy_diag_clicked(self) -> None:
        self.copy_diagnostics_requested.emit()
        if self.receivers(SIGNAL("copy_diagnostics_requested()")) <= 0 and self._pm is not None:
            report = DiagnosticsCollector.collect(
                self._pm, self._game_info, refresh_running=False
            )
            txt = report.to_text()
            copy_text_native(txt)
            cb = QGuiApplication.clipboard()
            if cb is not None:
                cb.setText(txt)
            self.refresh_live_metrics()
            self.toast_requested.emit(nfc("Đã sao chép báo cáo chẩn đoán hệ thống"), "success")

    def scan_adb_devices(self) -> None:
        with self._adb_lock:
            if self._adb_scanning or not self._adb_alive_box[0]:
                return
            self._adb_gen_box[0] += 1
            my_gen = self._adb_gen_box[0]
            self._adb_scanning = True
            cancel_ev = threading.Event()
            self._adb_cancel_box[0] = cancel_ev

        with _ACTIVE_ADB_LOCK:
            _ACTIVE_ADB_CANCELS.add(cancel_ev)

        self.row_adb.action_button.setEnabled(False)
        self.row_adb.set_description_html("Đang quét thiết bị Android qua ADB...")

        lock = self._adb_lock
        gen_box = self._adb_gen_box
        alive_box = self._adb_alive_box
        bridge_ref = weakref.ref(self._adb_bridge)

        def _worker() -> None:
            available = False
            devices: list = []
            try:
                if not cancel_ev.is_set() and not _ADB_SHUTTING_DOWN:
                    bridge = AdbBridge()
                    available = bool(bridge.is_available())
                    if available and not cancel_ev.is_set() and not _ADB_SHUTTING_DOWN:
                        devices = list(bridge.list_devices() or [])
            except Exception:  # noqa: BLE001
                available = False
                devices = []
            finally:
                with _ACTIVE_ADB_LOCK:
                    _ACTIVE_ADB_CANCELS.discard(cancel_ev)

            if _ADB_SHUTTING_DOWN or sys is None or sys.is_finalizing():
                return

            with lock:
                if not alive_box[0] or gen_box[0] != my_gen or cancel_ev.is_set():
                    return
                sig_bridge = bridge_ref()
                if sig_bridge is None or not _qt_is_valid(sig_bridge):
                    return
                try:
                    sig_bridge.devices_ready.emit(my_gen, available, devices)
                except RuntimeError:
                    pass

        threading.Thread(
            target=_worker,
            name="StellaSoraAdbScan",
            daemon=True,
        ).start()

    def _on_adb_devices_ready(self, scan_gen: int, adb_available: bool, devices: list) -> None:
        with self._adb_lock:
            if not self._adb_alive_box[0] or scan_gen != self._adb_gen_box[0]:
                return
            self._adb_scanning = False
            self._adb_cancel_box[0] = None

        self.row_adb.action_button.setEnabled(True)
        p = PORCELAIN_TOKENS
        if not adb_available:
            self._last_adb_desc_html = (
                f"<span style='color:{p.SLATE_MUTED};'>Chưa tìm thấy adb.exe</span> · Chỉ đọc qua USB / Wi-Fi."
            )
            self.row_adb.set_description_html(self._last_adb_desc_html)
            self.toast_requested.emit(nfc("Chưa tìm thấy adb.exe trên máy."), "info")
        else:
            count = len(devices)
            color = p.OK_TEXT if count > 0 else p.SLATE_MUTED
            self._last_adb_desc_html = (
                f"<b style='color:{color};'>{count} thiết bị kết nối</b> · Chỉ đọc qua USB / Wi-Fi."
            )
            self.row_adb.set_description_html(self._last_adb_desc_html)
            self.toast_requested.emit(nfc(f"Đã quét ADB: {count} thiết bị."), "success" if count else "info")
        self.adb_scan_completed.emit(list(devices))

    def shutdown_workers(self) -> None:
        with self._adb_lock:
            self._adb_gen_box[0] += 1
            self._adb_scanning = False
            if self._adb_cancel_box[0] is not None:
                self._adb_cancel_box[0].set()
                self._adb_cancel_box[0] = None
        if _qt_is_valid(self) and _qt_is_valid(self.row_adb):
            self.row_adb.action_button.setEnabled(True)
            self.row_adb.set_description_html(self._last_adb_desc_html)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.shutdown_workers()
        super().closeEvent(event)

    def refresh_dpr(self) -> None:
        self.frame.refresh_dpr()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.compact_layout(self.width(), self.height())

    def compact_layout(self, width: int, height: int | None = None) -> None:
        p = PORCELAIN_TOKENS
        if int(width) < LAYOUT_TOKENS.TWO_COL_COLLAPSE_THRESHOLD:
            self._grid_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self.col_game.setStyleSheet(
                f"QFrame#toolsGameCol {{ background: {p.WHITE}; border: none; "
                f"border-bottom: 1px solid {p.HAIRLINE}; }}"
            )
        else:
            self._grid_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self.col_game.setStyleSheet(
                f"QFrame#toolsGameCol {{ background: {p.WHITE}; border: none; "
                f"border-right: 1px solid {p.HAIRLINE}; }}"
            )
