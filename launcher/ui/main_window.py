"""Queued operation controller; all resource mutation lives in manifest services."""
from __future__ import annotations
import hashlib, json, logging, time, uuid
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QRectF, QEvent
from PySide6.QtGui import QPainter, QColor, QGuiApplication, QLinearGradient
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QDialog, QFileDialog
from ..core.config import LAUNCHER_VERSION, DEFAULT_GITHUB_REPO, derived_github_endpoints
from ..core.game_detection import GameDetector, find_all_potential_game_installations, is_game_process_running, find_game_exe_hint
from ..core.installer import PatchInstaller
from ..core.rollback import RollbackEngine
from ..core.network import NetworkService
from ..core.safety import manifest_sha256, InstallerError
from ..core.error_catalog import diagnose, lookup, INTERNAL_MAP, classify_text
from ..core.error_report import ErrorContext, build_report
from ..core.net_probe import run_probe
from ..core.update_notice import translation_state, newer, version_parts, detect_new_publisher_version
from ..core.official_resources import OfficialClient
from ..core.official_restore import check_official_update
from ..core.types import GameInfo
from ..core.self_update import schedule_update
from .assets import AssetManager
from .components.title_bar import TitleBar
from .views.overview_view import OverviewView
from .views.notifications_modal import NotificationsModal
from .views.guide_modal import GuideModal
from .views.settings_modal import SettingsModal
from .views.advanced_tools_modal import AdvancedToolsModal
from .views.confirmation_dialog import ConfirmationDialog
from .views.install_completed_dialog import InstallCompletedDialog
from ..core.shortcut import create_game_shortcut
from .views.message_dialog import MessageDialog
from .views.update_notice_dialog import UpdateNoticeDialog
from .views.game_selection_dialog import GameSelectionDialog
from .components.modal_shell import ModalScrim

logger = logging.getLogger('launcher.controller')


class AsyncOperationWorker(QThread):
    event_emitted = Signal(object)
    result_ready = Signal(str, bool, object)

    def __init__(self, op, target, parent=None, probe_on_error=True):
        super().__init__(parent)
        self.op = op
        self.target = target
        self.probe_on_error = probe_on_error

    def run(self):
        try:
            self.result_ready.emit(self.op, True, self.target(self.event_emitted.emit, self.op))
        except Exception as e:
            logger.exception('Operation failed')
            payload = {'message': str(e), 'error_code': getattr(e, 'code', 'OPERATION_ERROR'), 'exc': e}
            if self.probe_on_error:
                try:
                    if diagnose(e).info.network:
                        payload['probe'] = run_probe()   # bounded (~8 s) DNS/TCP check, runs off the UI thread
                except Exception:
                    logger.exception('Connectivity probe failed')
            self.result_ready.emit(self.op, False, payload)


class MainWindow(QMainWindow):
    github_sync_changed = Signal(object)

    def __init__(self, path_manager, config_manager):
        super().__init__()
        self.path_manager = path_manager
        self.config_manager = config_manager
        self.active_worker = None
        self.active_operation_id = None
        self.operation_kind = ''
        self.current_game_info = GameInfo()
        self.notifications = []
        self.background_worker = None
        self._close_after_background = False
        self._pending_sync = False
        self._pending_discoveries = None
        self._github_sync_state = {'message': 'Chưa đồng bộ GitHub.', 'fresh': False}
        self._manual_translation_check = False
        self._manual_translation_next = False
        self._notice_seen = set()
        self._official_update = None       # last check_official_update() result
        self._official_worker = None
        self._official_checked_at = 0.0
        self._official_prompted = set()    # latest_resource_version values already asked about this session
        self._launch_guard_declined = None

        self._configure_network()
        self.setWindowTitle(f'Stella Sora Việt Hóa v{LAUNCHER_VERSION}')
        self.setWindowIcon(AssetManager.get().get_app_icon())
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

        area = QGuiApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(min(480, area.width()), min(320, area.height()))
        self.resize(min(1280, area.width() - 24), min(900, area.height() - 24))
        self.move(area.center() - self.rect().center())

        central = QWidget()
        central.setObjectName('launcherRoot')
        central.setStyleSheet('#launcherRoot{background:transparent;}')
        self.setCentralWidget(central)
        l = QVBoxLayout(central)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)

        self.title_bar = TitleBar(self)
        self.title_bar.navigate_requested.connect(self._handle_navigation)
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.close_requested.connect(self.close)
        self.setMenuWidget(self.title_bar)

        from .components.overview_viewport import OverviewViewport
        self.overview_view = OverviewView()
        self.overview_viewport = OverviewViewport(self.overview_view)
        l.addWidget(self.overview_viewport, 1)

        v = self.overview_view
        v.auto_detect_requested.connect(self._auto_detect)
        v.install_requested.connect(self._on_install_clicked)
        v.rollback_requested.connect(self._on_rollback_clicked)
        v.verify_requested.connect(self._on_verify_clicked)
        v.browse_requested.connect(self._browse)
        v.launch_requested.connect(self._on_launch_clicked)
        v.navigate_requested.connect(self._handle_navigation)
        v.view_notifications_requested.connect(lambda: self._handle_navigation('notifications'))
        v.notification_selected.connect(self._open_notifications)
        v.check_translation_requested.connect(self._check_translation_version)
        v.blocker_requested.connect(self._explain_install_blocker)
        self._apply_game_info(self.current_game_info)

        self._release_timer = QTimer(self)
        self._release_timer.setInterval(30 * 60 * 1000)
        self._release_timer.timeout.connect(lambda: self._sync_github(automatic=True))
        self._release_timer.timeout.connect(self._start_official_check)
        self._release_timer.start()

        self._proc_timer = QTimer(self)
        self._proc_timer.setInterval(3000)
        self._proc_timer.timeout.connect(self._poll_game_running)
        self._proc_timer.start()

        self._snooze_timer = QTimer(self)
        self._snooze_timer.setSingleShot(True)
        self._snooze_timer.timeout.connect(self._maybe_show_release_notice)

        QTimer.singleShot(0, self._clamp_to_screen)
        QTimer.singleShot(0, self._initial_load)

    def _apply_game_info(self, info: GameInfo):
        self.current_game_info = info
        has_pending = False
        if info and info.installed and info.game_path:
            try:
                has_pending = bool(self._engine().pending(info.game_path))
            except Exception:
                has_pending = False
        self.overview_view.update_game_status(info, has_pending_recovery=has_pending)
        self.overview_view.set_official_update_notice(self._official_notice())
        self.title_bar.update_game_state(info, busy=(self.active_worker is not None))

    def _poll_game_running(self):
        if self.active_worker is not None or not self.current_game_info.installed or not self.isVisible():
            return
        running = is_game_process_running()
        if running != self.current_game_info.is_running:
            self.current_game_info.is_running = running
            self._apply_game_info(self.current_game_info)
            self._refresh_translation_state()

    def _configure_network(self):
        try:
            channel = self.config_manager.channel()
            self._channel_error = ''
        except (ValueError, TypeError) as exc:
            self._channel_error = str(exc)
            channel = {
                'repo': str(self.config_manager.get('github_repo', '')),
                'branch': str(self.config_manager.get('github_branch', '')),
                'release_url': None,
                'notifications_url': None,
                'manifest_url': None,
                'configuration_error': self._channel_error,
            }
        identity = json.dumps(channel, sort_keys=True, ensure_ascii=False)
        previous = getattr(self, '_github_identity', None)
        self._github_identity = identity
        self._channel = channel
        if previous is not None and previous != identity:
            self.notifications = []
            if hasattr(self, 'overview_view'):
                self.overview_view.set_notifications([])
            self._github_sync_state = {'message': 'Đã đổi kênh. Chưa đọc thông tin của nguồn mới.', 'fresh': False}
            self.github_sync_changed.emit(self._github_sync_state)
            if hasattr(self, 'overview_view'):
                self.overview_view.set_translation_update(False)
                self.overview_view.set_install_allowed(False, 'Kênh vừa thay đổi; cần kiểm tra lại.')
        cache = self.path_manager.app_data_dir / 'network_cache' / hashlib.sha256(identity.encode('utf8')).hexdigest()[:16]
        self.network_service = NetworkService(channel['release_url'], channel['notifications_url'], cache)
        if self._channel_error:
            self._github_sync_state = {
                'message': 'Nguồn GitHub chưa hợp lệ: ' + self._channel_error + ' Mở Cài đặt launcher để sửa tên kho hoặc nhánh.',
                'fresh': False,
                'configuration_error': self._channel_error,
            }
            self.github_sync_changed.emit(self._github_sync_state)
        return not bool(self._channel_error)

    def _detected(self):
        raw = self.config_manager.get('game_path', '')
        if not raw:
            if not self.config_manager.get('auto_detect_game', True):
                return GameInfo()
            found = find_all_potential_game_installations()
            if not found:
                return GameInfo()
            # Prefer an already-patched installation when multiple clients (Steam + Yostar) exist
            raw = next(
                (item['path'] for item in found if (Path(item['path']) / '.vietnamese_patch_receipt.json').is_file()),
                found[0]['path'],
            )
        return GameDetector(self.path_manager.backup_root).detect_info(raw)

    def _initial_load(self):
        try:
            from ..core.self_update import cleanup_update_artifacts
            cleanup_update_artifacts(self.path_manager.exe_dir)
            cleanup_update_artifacts(self.path_manager.app_data_dir / 'update_helper')
        except Exception:
            pass
        self._start('scan', lambda cb, op: {'game': self._detected()})
        self._sync_github(automatic=True)

    def _sync_github(self, automatic=False):
        if not self._configure_network():
            self._pending_sync = False
            return
        if self.background_worker is not None:
            self._pending_sync = True
            self._github_sync_state = {'message': 'Đang hoàn tất lần đọc trước. Sẽ đồng bộ lại kênh đã chọn.', 'fresh': False}
            self.github_sync_changed.emit(self._github_sync_state)
            return
        self.overview_view.set_translation_update(False)
        self.overview_view.set_install_allowed(False, 'Đang kiểm tra bảng kê mới.')
        network = NetworkService(
            self.network_service.update_url,
            self.network_service.notifications_url,
            self.network_service.cache_dir,
            self.network_service.timeout,
        )
        identity = self._github_identity
        manifest_url = self._channel['manifest_url']
        check_launcher = not automatic or self.config_manager.get('check_updates_on_start', True)
        fallback = (
            str(self.path_manager.resource_dir / 'ui' / 'notifications.json')
            if network.notifications_url == derived_github_endpoints(DEFAULT_GITHUB_REPO, 'main')['remote_notifications_url']
            else None
        )

        def work(cb, op):
            result = network.sync_channel(fallback, LAUNCHER_VERSION, manifest_url, check_launcher)
            result['source_identity'] = identity
            if result.get('release_status') != 'online':
                try:
                    result['probe'] = run_probe()
                except Exception:
                    logger.exception('Connectivity probe failed')
            return result

        self._github_sync_state = {'message': 'Đang đọc thông báo và bản phát hành từ GitHub…', 'fresh': False}
        self.github_sync_changed.emit(self._github_sync_state)
        worker = AsyncOperationWorker(identity, work, self, probe_on_error=False)
        self.background_worker = worker
        worker.result_ready.connect(self._background_finish)
        worker.finished.connect(lambda: self._release_background(worker))
        worker.start()

    def _background_finish(self, identity, success, result):
        if identity != self._github_identity:
            return
        if not success:
            exc = result.get('exc')
            d = diagnose(exc) if exc is not None else None
            self._github_sync_state = {
                'message': 'Không đồng bộ được GitHub: ' + result.get('message', 'Lỗi kết nối.'),
                'fresh': False,
                'error_code': d.code if d else (classify_text(result.get('message', '')) or 'E-NET'),
                'error_detail': result.get('message', ''),
            }
        else:
            self._github_sync_state = result
            self.notifications = result.get('notifications', [])
            self.overview_view.set_notifications(self.notifications)
            self.network_service.notification_status = result['notification_status']
            self.network_service.notification_message = result['notification_message']
            self.network_service.notification_version = result.get('notification_version')
            self._record_release_observation(result)
        self._refresh_translation_state()
        self.github_sync_changed.emit(self._github_sync_state)
        if self._manual_translation_check:
            self._manual_translation_check = False
            self._refresh_translation_state()
            state = translation_state(self._github_sync_state, self.current_game_info)
            message = state['message']
            if self.config_manager.get('payload_path', ''):
                message += '\nLauncher đang dùng gói cục bộ đã chọn để cài đặt.'
            blocker = state.get('blocker_code')
            if not success or (blocker and blocker != 'E-NO-GAME-FOLDER'):
                code = blocker or self._github_sync_state.get('error_code') or 'E-NET'
                detail = state.get('blocker_detail') or self._github_sync_state.get('error_detail') or ''
                QTimer.singleShot(0, lambda c=code, d=detail: self._show_error('Kiểm tra phiên bản Việt hoá', code=c, message=d))
            else:
                QTimer.singleShot(0, lambda m=message: self._show(MessageDialog('Kiểm tra phiên bản Việt hoá', m, parent=self)))
        else:
            QTimer.singleShot(1200, self._maybe_show_release_notice)

    def _release_background(self, worker):
        if self.background_worker is worker:
            self.background_worker = None
        worker.deleteLater()
        if self._close_after_background:
            self._close_after_background = False
            QTimer.singleShot(0, self.close)
        elif self._pending_sync:
            self._pending_sync = False
            if self._manual_translation_next:
                self._manual_translation_check = True
                self._manual_translation_next = False
            QTimer.singleShot(0, self._sync_github)

    def _start(self, kind, target):
        if self.active_worker is not None:
            return False
        op = uuid.uuid4().hex
        self.active_operation_id = op
        self.operation_kind = kind
        if kind in ('startup', 'self_update'):
            self.overview_view.connection_label.set_status('Đang kết nối', 'busy')
        self.overview_view.set_busy(True, self.config_manager.get('reduced_motion', False))
        self.overview_view.show_progress(True, 'Đang xử lý…', 0)
        worker = AsyncOperationWorker(op, target, self)
        self.active_worker = worker
        self.title_bar.update_game_state(self.current_game_info, busy=True)
        worker.event_emitted.connect(self._event)
        worker.result_ready.connect(self._finish)
        worker.finished.connect(lambda: self._release_worker(worker))
        worker.start()
        return True

    def _event(self, e):
        if e.operation_id == self.active_operation_id:
            self.overview_view.handle_operation_event(e)

    def _release_worker(self, w):
        if self.active_worker is w:
            self.active_worker = None
            self.active_operation_id = None
            self.overview_view.set_busy(False, self.config_manager.get('reduced_motion', False))
            self.title_bar.update_game_state(self.current_game_info, busy=False)
        w.deleteLater()
        if getattr(self, '_close_after_worker', False):
            self._close_after_worker = False
            self._proc_timer.stop()
            self._release_timer.stop()
            QTimer.singleShot(20, lambda: QApplication.instance().quit())
        elif self._pending_discoveries is not None:
            found = self._pending_discoveries
            self._pending_discoveries = None
            QTimer.singleShot(0, lambda: self._choose_discovered(found))
        else:
            QTimer.singleShot(0, self._maybe_show_release_notice)

    def _finish(self, op, success, result):
        if op != self.active_operation_id:
            return
        if not success:
            msg = result.get('message', 'Lỗi chưa xác định')
            err_code = result.get('error_code', '')
            report = self._show_error(
                self._action_title(self.operation_kind),
                exc=result.get('exc'),
                code=INTERNAL_MAP.get(err_code),
                message=msg,
                probe=result.get('probe'),
                show=False,
                operation=self.operation_kind or '',
            )
            self.overview_view.show_completed('⚠ ' + report.title + ' [' + report.code + ']')
            self._show(MessageDialog(self._action_title(self.operation_kind), '', parent=self, report=report))
            return
        if not isinstance(result, dict):
            return
        if self.operation_kind == 'discover':
            self._pending_discoveries = result.get('installations', [])
            self.overview_view.show_progress(False)
            return
        if self.operation_kind == 'select_root':
            info = result['game']
            if not info.installed:
                self.overview_view.show_progress(False)
                hint = find_game_exe_hint(info.game_path) if info.game_path else None
                self._show_error(
                    'Chọn thư mục game',
                    code='E-NO-EXE',
                    message='Không tìm thấy StellaSora.exe tại: ' + str(info.game_path or '(không rõ)'),
                    extra={'thư mục vừa chọn': str(info.game_path or ''), 'gợi ý thư mục có StellaSora.exe': str(hint) if hint else 'không thấy'},
                    extra_summary=('Gợi ý: tệp StellaSora.exe nằm trong thư mục ' + str(hint) + '. Hãy chọn thư mục đó.') if hint else '',
                )
                return
            previous = self.config_manager.get('game_path', '')
            self.config_manager.set('game_path', str(info.game_path))
            if not self.config_manager.save():
                self.config_manager.set('game_path', previous)
                self._show_error('Lưu thư mục game', code='E-CONFIG-SAVE', message='\n'.join(self.config_manager.warnings))
                return
        if 'game' in result:
            self._apply_game_info(result['game'])
            self._refresh_translation_state()
        if self.operation_kind in ('scan', 'select_root'):
            self.overview_view.show_progress(False)
            QTimer.singleShot(800, self._start_official_check)
        elif self.operation_kind == 'verify':
            self.overview_view.show_completed(
                '✓ Hoàn tất kiểm tra! Đã đối chiếu ' + str(result.get('files', 0)) + ' tệp của bản dịch ' + str(result.get('version', '')) + ' toàn vẹn.'
            )
        elif self.operation_kind == 'launch':
            self.overview_view.show_completed(result.get('message', '✓ Đã gửi lệnh mở game.'))
            QTimer.singleShot(1500, self._poll_game_running)
        elif self.operation_kind == 'publisher_vanilla_restore':
            self.overview_view.show_completed(result.get('message', '✓ Đã khôi phục dữ liệu gốc.'))
            pub_reason = result.get('pub_reason', '')
            if result.get('launch_after'):
                QTimer.singleShot(50, self._on_launch_clicked)
            else:
                QTimer.singleShot(50, lambda r=pub_reason: self._prompt_launch_after_pub_restore(r))
        elif self.operation_kind == 'self_update':
            if result.get('status') != 'online':
                self._show_error(
                    'Kiểm tra cập nhật launcher',
                    code=result.get('error_code') or ('E-CONFIG-CHANNEL' if result.get('status') == 'unavailable' else 'E-NET'),
                    message=result.get('message', 'Không thể kết nối GitHub.'),
                )
            elif not result.get('has_update'):
                self._show(
                    MessageDialog(
                        'Cập nhật launcher',
                        f'Bạn đang dùng phiên bản mới nhất (v{LAUNCHER_VERSION}).\nKhông có bản cập nhật mới trên GitHub.',
                        parent=self,
                    )
                )
            elif not result.get('download_url'):
                self._show(MessageDialog('Cập nhật launcher', result.get('message', 'Chưa có tệp cập nhật tự động được xác minh.'), parent=self))
            else:
                QTimer.singleShot(0, lambda: self._confirm_update(result))
        elif self.operation_kind == 'apply_self_update':
            self.overview_view.show_completed('Đã tải bản cập nhật. Launcher sẽ khởi động lại ngay…')
            self._close_after_worker = True
        elif self.operation_kind == 'install':
            msg = result.get('message', '')
            if not msg.startswith('✓') and not msg.startswith('Hoàn tất'):
                msg = f'✓ Hoàn tất cài đặt! {msg}'
            sc_ok = False
            if getattr(self, '_pending_create_shortcut', False) and getattr(self.current_game_info, 'game_path', None):
                ok, sc_msg = create_game_shortcut(self.current_game_info.game_path)
                sc_ok = ok
                if ok:
                    msg += '\n✓ Đã thêm lối tắt "Stella Sora Việt Hóa" vào màn hình chính.'
            self.overview_view.show_completed(msg)
            QTimer.singleShot(150, lambda r=result, s=sc_ok: self._show_install_completed(r, s))
        elif self.operation_kind == 'rollback':
            msg = result.get('message', '')
            if not msg.startswith('✓') and not msg.startswith('Hoàn tất'):
                msg = f'✓ Hoàn tất khôi phục! {msg}'
            self.overview_view.show_completed(msg)
            upd = self._official_update or {}
            if upd.get('update_available'):
                reason = f"tài nguyên game {upd.get('local_resource_version')} → {upd.get('latest_resource_version')}"
                QTimer.singleShot(50, lambda r=reason: self._prompt_launch_after_pub_restore(r))
        else:
            self.overview_view.show_completed(result.get('message', '✓ Hoàn tất thao tác.'))

    def _prompt_launch_after_pub_restore(self, pub_reason: str):
        dialog = ConfirmationDialog(
            'Game mới cập nhật tài nguyên mới',
            f'Phát hiện game có bản cập nhật mới từ nhà phát hành ({pub_reason}).\n\n'
            f'Launcher đã tải và cài lại dữ liệu gốc của nhà phát hành (chưa Việt hoá) để game cập nhật được an toàn.\n\n'
            f'Vui lòng mở game để cập nhật tài nguyên mới trước khi cài lại Việt hoá!',
            'Mở Game ngay',
            parent=self,
        )
        if self._show(dialog) == QDialog.DialogCode.Accepted:
            self._on_launch_clicked()

    def _auto_detect(self):
        if self.active_worker is not None:
            return
        self._start('discover', lambda cb, op: {'installations': find_all_potential_game_installations()})

    def _choose_discovered(self, found):
        if self.active_worker is not None:
            return
        if not found:
            self._show_error('Tìm game tự động', code='E-GAME-NOT-FOUND')
            return
        if len(found) == 1:
            self._select_game_root(found[0]['path'])
            return
        dialog = GameSelectionDialog(found, self)
        if self._show(dialog) == QDialog.DialogCode.Accepted and dialog.selected_path:
            self._select_game_root(dialog.selected_path)

    def _select_game_root(self, path):
        self._start('select_root', lambda cb, op: {'game': GameDetector(self.path_manager.backup_root).detect_info(path)})

    def _scan(self):
        self._start('scan', lambda cb, op: {'game': self._detected()})

    def _browse(self):
        if self.active_worker:
            return
        path = QFileDialog.getExistingDirectory(self, 'Chọn thư mục có StellaSora.exe', str(self.current_game_info.game_path or 'C:/'))
        if path:
            self._select_game_root(path)

    def _engine(self):
        return PatchInstaller(self.path_manager.backup_root, self.path_manager.journals_dir)

    def _valid_target(self):
        return bool(
            self.current_game_info.installed
            and self.current_game_info.game_path
            and not self.current_game_info.is_running
            and not self.active_worker
        )

    def _check_ready_or_explain(self, action_title: str) -> bool:
        if self.active_worker is not None:
            self._show_error(action_title, code='E-BUSY', message='Thao tác đang chạy: ' + (self.operation_kind or '?'))
            return False
        info = self.current_game_info
        if not info.installed or not info.game_path:
            self._show_error(action_title, code='E-NO-GAME-FOLDER')
            return False
        running_now = is_game_process_running()
        if running_now != info.is_running:
            info.is_running = running_now
            self._apply_game_info(info)
            self._refresh_translation_state()
        if info.is_running:
            self._show_error(action_title, code='E-GAME-RUNNING')
            return False
        return True

    def _confirm(self, title, msg, label='Tiếp tục'):
        d = ConfirmationDialog(title, msg, label, parent=self)
        return self._show(d) == QDialog.DialogCode.Accepted

    def _on_install_clicked(self):
        if not self._check_ready_or_explain('Cài đặt Việt hoá'):
            return
        root = self.current_game_info.game_path
        info = self.current_game_info
        state = self._refresh_translation_state()
        if not state['can_install']:
            self._show_error(
                'Cài đặt Việt hoá',
                code=state.get('blocker_code') or 'E-UNKNOWN',
                message=state.get('blocker_detail') or state['message'],
            )
            return

        manifest_meta = {
            'client_game_version': state.get('translation_game') or self._github_sync_state.get('translation_game', '2.1.0'),
            'resource_version': state.get('translation_resource') or self._github_sync_state.get('translation_resource', '*'),
        }
        has_new_pub, pub_reason = detect_new_publisher_version(info, manifest_meta)
        if has_new_pub:
            if not self._confirm(
                'PHÁT HIỆN BẢN CẬP NHẬT GAME MỚI',
                f'{pub_reason}.\n\nLauncher sẽ tự tải dữ liệu gốc của nhà phát hành về (cần mạng) để game cập nhật an toàn trước khi cài Việt hoá. Tiếp tục?',
                'Khôi phục gốc',
            ):
                return
            self._start_official_restore(root, pub_reason)
            return

        is_update = state['available']
        local = self.config_manager.get('payload_path', '')
        channel_valid = self._configure_network()
        if not local and not channel_valid:
            self._show_error('Cài đặt Việt hoá', code='E-CONFIG-CHANNEL', message=self._channel_error or self._github_sync_state.get('message', ''))
            return
        pref_shortcut = self.config_manager.get('create_desktop_shortcut', True)
        cd = ConfirmationDialog(
            'CÀI / CẬP NHẬT VIỆT HÓA',
            'Thư mục: ' + str(root) + '\n\n' + state['message'] + '\n\nTải hoặc đọc gói đã chọn, sao lưu và cài đúng các tệp trong manifest. Gói chỉ gồm texture sẽ chỉ cài texture.',
            'Cài bản dịch',
            show_shortcut_option=True,
            shortcut_default=pref_shortcut,
            parent=self,
        )
        if self._show(cd) != QDialog.DialogCode.Accepted:
            return
        self._pending_create_shortcut = cd.create_shortcut_requested()
        self.config_manager.set('create_desktop_shortcut', self._pending_create_shortcut)
        self.config_manager.save()
        network = self.network_service
        manifest_url = self._channel['manifest_url']

        def work(cb, op):
            with network.payload_for_install(self.path_manager.payload_root, local, manifest_url, cb, op) as payload:
                if is_update:
                    manifest = json.loads((payload / 'patch_manifest.json').read_text(encoding='utf8'))
                    rechecked = translation_state(
                        {
                            'release_status': 'online',
                            'manifest_status': 'online',
                            'translation_version': manifest.get('version'),
                            'translation_game': manifest.get('client_game_version'),
                            'translation_resource': manifest.get('resource_version'),
                            'manifest_sha256': manifest_sha256(manifest),
                        },
                        info,
                    )
                    if not rechecked['available']:
                        raise RuntimeError('Không còn bản Việt hoá mới hơn: ' + rechecked['message'])
                r = self._engine().install(root, payload, operation_id=op, event_cb=cb)
                return {
                    'game': self._detected(),
                    'message': f"✓ Hoàn tất cài đặt! Đã nạp thành công {r['files_count']} tệp bản dịch ({r['version']}).",
                }

        self._start('install', work)

    def _action_target(self, action, require_receipt=True):
        if not self._check_ready_or_explain(action):
            return None
        info = self.current_game_info
        if require_receipt and not info.installed_receipt:
            receipt_file = Path(info.game_path) / '.vietnamese_patch_receipt.json'
            present = receipt_file.is_file()
            restored = bool(getattr(info, 'official_restore', None))
            self._show_error(
                action,
                code='E-RECEIPT-MISMATCH' if present else 'E-NO-RECEIPT',
                message='Tệp biên bản có trong thư mục game nhưng không dùng được.' if present else 'Không có tệp .vietnamese_patch_receipt.json trong thư mục game.',
                extra={'tệp biên bản tồn tại': 'có' if present else 'không'},
                extra_summary=('Bạn vừa khôi phục dữ liệu gốc của nhà phát hành nên game đang ở bản gốc, chưa có bản dịch để kiểm tra. Bấm "Cài Việt hoá" khi muốn dùng lại bản dịch.') if (restored and not present) else '',
            )
            return None
        return info.game_path

    def _on_rollback_clicked(self):
        root = self._action_target('Khôi phục', require_receipt=False)
        if root is None:
            return
        if self._confirm(
            'KHÔI PHỤC DỮ LIỆU GỐC NGUYÊN BẢN',
            'Thư mục: '
            + str(root)
            + '\n\nLauncher sẽ tự tải dữ liệu ngôn ngữ (data.arcx, lua.arcx và các gói ảnh đã Việt hoá) mới nhất từ máy chủ chính thức của nhà phát hành, kiểm tra mã băm rồi cài vào game. Không dùng lại bản sao lưu cũ vì có thể là bản Việt hoá hoặc phiên bản cũ.\n\nCần kết nối mạng, có thể tải vài trăm MB. Nếu lỗi giữa chừng, game được giữ nguyên.\n\nBạn có muốn tiếp tục?',
            'Tải và khôi phục gốc',
        ):
            def work(cb, op):
                r = RollbackEngine(self.path_manager.backup_root, self.path_manager.journals_dir).rollback(root, operation_id=op, event_cb=cb)
                return {
                    'game': self._detected(),
                    'message': r.get('message', '✓ Hoàn tất khôi phục! Đã cài dữ liệu gốc mới nhất của nhà phát hành.'),
                }
            self._start('rollback', work)

    def _start_official_restore(self, root, pub_reason='', launch_after=False):
        """Download + install fresh official data (used by the update guard and the install flow)."""
        def restore_work(cb, op):
            r = RollbackEngine(self.path_manager.backup_root, self.path_manager.journals_dir).rollback(root, operation_id=op, event_cb=cb)
            return {
                'game': self._detected(),
                'pub_reason': pub_reason,
                'launch_after': launch_after,
                'message': r.get('message', '✓ Đã khôi phục dữ liệu gốc để game cập nhật an toàn.'),
            }
        return self._start('publisher_vanilla_restore', restore_work)

    # ---- game (publisher) update awareness -------------------------------------------------
    def _official_notice(self):
        upd = self._official_update
        info = self.current_game_info
        if not upd or not info or not info.installed or not upd.get('update_available'):
            return None
        if str(upd.get('local_resource_version')) != str(info.resource_version):
            return None  # stale result: the game changed since the check
        if not (info.installed_receipt or info.has_vietnamese):
            return None
        return upd

    def _start_official_check(self, force=False):
        info = self.current_game_info
        if self._official_worker is not None or not info.installed or not info.game_path:
            return
        if not force and not self.config_manager.get('check_official_on_start', True):
            return
        if not force and time.time() - self._official_checked_at < 600:
            return
        self._official_checked_at = time.time()
        cache_file = self.path_manager.app_data_dir / 'official_check.json'
        snapshot = GameInfo(**{k: getattr(info, k) for k in info.__dataclass_fields__})

        def work(cb, op):
            return check_official_update(OfficialClient('EN', timeout=15, retries=2), snapshot, cache_file)

        worker = AsyncOperationWorker('official_check', work, self, probe_on_error=False)
        self._official_worker = worker
        worker.result_ready.connect(self._official_check_finished)
        worker.finished.connect(lambda: self._release_official_worker(worker))
        worker.start()

    def _release_official_worker(self, worker):
        if self._official_worker is worker:
            self._official_worker = None
        worker.deleteLater()
        if getattr(self, '_close_after_official', False):
            self._close_after_official = False
            QTimer.singleShot(0, self.close)

    def _official_check_finished(self, _op, success, result):
        if not success:
            logger.info('Official version check skipped: %s', result.get('message'))
            return  # offline is normal; never bother the player
        self._official_update = result
        self._apply_game_info(self.current_game_info)
        notice = self._official_notice()
        if not notice or self.active_worker is not None or not self.isVisible():
            return
        info = self.current_game_info
        if info.is_running:
            return
        reason = f"tài nguyên game {notice['local_resource_version']} → {notice['latest_resource_version']}"
        if self.config_manager.get('auto_restore_before_game_update', False):
            self.overview_view.show_completed('Game có bản cập nhật mới — đang tự khôi phục dữ liệu gốc…')
            self._start_official_restore(info.game_path, reason)
            return
        latest = str(notice.get('latest_resource_version'))
        if latest in self._official_prompted:
            return
        self._official_prompted.add(latest)
        QTimer.singleShot(0, lambda n=notice: self._prompt_restore_before_update(n))

    def _prompt_restore_before_update(self, notice):
        if self.active_worker is not None or not self.current_game_info.installed:
            return
        if self._confirm(
            'GAME CÓ BẢN CẬP NHẬT — NÊN KHÔI PHỤC GỐC TRƯỚC',
            f"Game đang ở tài nguyên {notice.get('local_resource_version')}, nhà phát hành đã có {notice.get('latest_resource_version')}.\n\n"
            'Bản Việt hoá đã sửa tệp của game nên cập nhật của game sẽ báo lỗi. Launcher sẽ tải dữ liệu gốc về (cần mạng, có thể vài trăm MB) để game cập nhật bình thường. Sau khi game cập nhật xong, bấm Cập nhật Việt hoá để cài lại.\n\nKhôi phục dữ liệu gốc ngay?',
            'Khôi phục gốc',
        ):
            self._start_official_restore(
                self.current_game_info.game_path,
                f"tài nguyên game {notice.get('local_resource_version')} → {notice.get('latest_resource_version')}",
            )

    def _on_verify_clicked(self):
        root = self._action_target('Kiểm tra tệp')
        if root is not None:
            self._start('verify', lambda cb, op: self._engine().verify_installed(root, cb, op))

    def _on_launch_clicked(self):
        if not self._check_ready_or_explain('Mở game'):
            return
        info = self.current_game_info
        notice = self._official_notice()
        if notice and self._launch_guard_declined != str(notice.get('latest_resource_version')):
            reason = f"tài nguyên game {notice['local_resource_version']} → {notice['latest_resource_version']}"
            if self.config_manager.get('auto_restore_before_game_update', False):
                self._start_official_restore(info.game_path, reason, launch_after=True)
                return
            if self._confirm(
                'GAME CÓ BẢN CẬP NHẬT — KHÔI PHỤC GỐC TRƯỚC KHI MỞ',
                f"Game đang ở tài nguyên {notice.get('local_resource_version')}, nhà phát hành đã có {notice.get('latest_resource_version')}. Mở game lúc này với bản Việt hoá sẽ làm cập nhật của game báo lỗi.\n\nLauncher sẽ tải dữ liệu gốc về rồi mở game để bạn cập nhật. Tiếp tục?",
                'Khôi phục rồi mở game',
            ):
                self._start_official_restore(info.game_path, reason, launch_after=True)
            else:
                self._launch_guard_declined = str(notice.get('latest_resource_version'))
                self.overview_view.show_completed('Chưa mở game vì game có bản cập nhật. Bấm Mở game lần nữa nếu vẫn muốn mở không khôi phục.')
            return

        def work(cb, op):
            ok, msg = GameDetector(self.path_manager.backup_root).launch(info)
            if not ok:
                if 'chưa được chọn' in msg:
                    kind = 'NO_GAME_FOLDER'
                elif 'đang chạy' in msg:
                    kind = 'GAME_RUNNING'
                elif 'Không tìm thấy file' in msg:
                    kind = 'INVALID_ROOT'
                else:
                    kind = 'LAUNCH_FAILED'
                raise InstallerError(msg, kind)
            return {'message': msg}

        self._start('launch', work)

    def _check_update(self):
        if not self._configure_network():
            self._show_error('Kiểm tra cập nhật launcher', code='E-CONFIG-CHANNEL', message=self._channel_error)
            return
        network = self.network_service
        self._start('self_update', lambda cb, op: network.check_for_updates(LAUNCHER_VERSION))

    def _check_translation_version(self):
        if self.active_worker is not None:
            return
        if not self._configure_network():
            self._show_error('Kiểm tra phiên bản Việt hoá', code='E-CONFIG-CHANNEL', message=self._channel_error)
            return
        if self.background_worker is not None:
            self._manual_translation_next = True
            self._pending_sync = True
            return
        self._manual_translation_check = True
        self._sync_github()

    def _refresh_translation_state(self):
        local = self.config_manager.get('payload_path', '')
        if local:
            try:
                path = Path(local) / 'patch_manifest.json'
                if not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
                    raise ValueError('Thiếu bảng kê hoặc bảng kê quá lớn.')
                manifest = self.network_service._windows_manifest(json.loads(path.read_text(encoding='utf8')))
                local_state = {
                    'release_status': 'online',
                    'manifest_status': 'online',
                    'translation_version': manifest['version'],
                    'translation_game': manifest['client_game_version'],
                    'translation_resource': manifest['resource_version'],
                    'manifest_sha256': manifest_sha256(manifest),
                }
                state = translation_state(local_state, self.current_game_info)
                state['translation_game'] = local_state['translation_game']
                state['translation_resource'] = local_state['translation_resource']
                state['message'] = 'Gói cục bộ: ' + state['message']
            except Exception as exc:
                code = 'E-LOCAL-PAYLOAD'
                state = {
                    'available': False,
                    'can_install': False,
                    'message': lookup(code).title + ' — ' + str(exc) + ' [' + code + ']',
                    'blocker_code': code,
                    'blocker_detail': 'Gói cục bộ (' + str(local) + '): ' + str(exc),
                }
        else:
            state = translation_state(self._github_sync_state, self.current_game_info)
        if hasattr(self, 'overview_view'):
            self.overview_view.set_translation_update(state['available'])
            self.overview_view.btn_check_translation.setToolTip(state['message'])
            self.overview_view.set_install_allowed(state['can_install'], state['message'], state.get('blocker_code', ''))
        return state

    def _record_release_observation(self, sync):
        if sync.get('release_status') != 'online':
            return
        version = sync.get('release_version')
        if version_parts(version) is None:
            return
        key = hashlib.sha256(self._github_identity.encode('utf8')).hexdigest()
        baselines = self.config_manager.get('release_notice_baselines', {})
        pending = self.config_manager.get('release_notice_pending', {})
        baselines = dict(baselines) if isinstance(baselines, dict) else {}
        pending = dict(pending) if isinstance(pending, dict) else {}
        previous = baselines.get(key)
        if previous and newer(version, previous):
            pending[key] = version
        if not previous or not newer(previous, version):
            baselines[key] = version
        self.config_manager.update({'release_notice_baselines': baselines, 'release_notice_pending': pending})
        self.config_manager.save()

    def _maybe_show_release_notice(self):
        if self.active_worker is not None or self.background_worker is not None or self._manual_translation_check or not self.isVisible():
            return
        sync = self._github_sync_state
        if sync.get('release_status') != 'online':
            return
        version = sync.get('release_version')
        channel_key = hashlib.sha256(self._github_identity.encode('utf8')).hexdigest()
        pending = self.config_manager.get('release_notice_pending', {})
        pending = dict(pending) if isinstance(pending, dict) else {}
        has_t_update = bool(translation_state(sync, self.current_game_info)['available'])
        if version_parts(version) is None or not (
            pending.get(channel_key) == version or sync.get('update', {}).get('has_update') or has_t_update
        ):
            return
        key = self._github_identity + '|' + str(version) + '|' + str(sync.get('manifest_sha256') or '')
        try:
            snooze_until = float(self.config_manager.get('release_notice_snooze_until', 0) or 0)
        except (ValueError, TypeError):
            snooze_until = 0
        if key in self._notice_seen:
            return
        remaining = snooze_until - time.time()
        if remaining > 0:
            self._snooze_timer.start(min(2147483647, max(1, int(remaining * 1000) + 1)))
            return
        has_l_update = bool(sync.get('update', {}).get('has_update') and sync.get('update', {}).get('download_url'))
        result = self._show(
            UpdateNoticeDialog(
                version,
                sync.get('release_notes', ''),
                self,
                has_launcher_update=has_l_update,
                has_translation_update=has_t_update,
            )
        )
        if result == 3:
            self._notice_seen.add(key)
            if pending.get(channel_key) == version:
                pending.pop(channel_key, None)
                self.config_manager.set('release_notice_pending', pending)
                self.config_manager.save()
            if has_l_update:
                QTimer.singleShot(50, lambda: self._confirm_update(sync['update']))
        elif result == 4:
            self._notice_seen.add(key)
            if pending.get(channel_key) == version:
                pending.pop(channel_key, None)
                self.config_manager.set('release_notice_pending', pending)
                self.config_manager.save()
            QTimer.singleShot(50, self._on_install_clicked)
        elif result == 2:
            self.config_manager.set('release_notice_snooze_until', time.time() + 24 * 60 * 60)
            if not self.config_manager.save():
                self._show_error('Lưu lựa chọn thông báo', code='E-CONFIG-SAVE', message='\n'.join(self.config_manager.warnings))
            self._snooze_timer.start(24 * 60 * 60 * 1000)
        else:
            self._notice_seen.add(key)
            if pending.get(channel_key) == version:
                pending.pop(channel_key, None)
                self.config_manager.set('release_notice_pending', pending)
                self.config_manager.save()

    def _prompt_auto_update(self, update):
        if self.active_worker is not None:
            return
        self._confirm_update(update)

    def _confirm_update(self, data):
        latest = data.get('latest_version', '')
        body = f'Đã có phiên bản launcher mới: {latest} (hiện tại: v{LAUNCHER_VERSION}).\n\nBạn có muốn tải và tự động cập nhật ngay bây giờ không?'
        cl = data.get('changelog', '').strip()
        if cl:
            cl_lines = [l for l in cl.splitlines() if l.strip()][:5]
            if cl_lines:
                body += '\n\nNội dung mới:\n' + ('\n'.join(cl_lines))
        if not self._confirm(f'CẬP NHẬT LAUNCHER {latest}', body, 'Cập nhật ngay'):
            return

        def work(cb, op):
            a = data['asset']
            dest = self.path_manager.app_data_dir / 'updates' / f'StellaSora_Launcher_{latest}.exe'
            self.network_service.download(data['download_url'], dest, a['size'], data['sha256'], cb, op)
            schedule_update(dest, data['sha256'], self.path_manager.app_data_dir)
            return {'message': 'Đã chuẩn bị bản cập nhật.'}

        self._start('apply_self_update', work)

    def _recover(self):
        if not self._check_ready_or_explain('Phục hồi thao tác'):
            return
        root = self.current_game_info.game_path
        if self._confirm(
            'PHỤC HỒI THAO TÁC BỊ NGẮT',
            'Thư mục: '
            + str(root)
            + '\n\nĐọc nhật ký và đưa các tệp dở dang về trạng thái trước thao tác bị ngắt. Các tệp đã được nhà phát hành cập nhật sẽ được giữ nguyên an toàn.',
            'Phục hồi',
        ):
            def work(cb, op):
                r = self._engine().recover(root, cb, op)
                msg = (
                    '✓ Đã phục hồi và đồng bộ ' + str(r['journals']) + ' nhật ký cũ (giữ nguyên các tệp game đã cập nhật).'
                    if r.get('superseded')
                    else '✓ Đã phục hồi ' + str(r['journals']) + ' nhật ký.'
                )
                return {'game': self._detected(), 'message': msg}
            self._start('recover', work)

    def _fit(self, d):
        area = self.screen().availableGeometry()
        width = min(d.width(), max(280, area.width() - 24))
        height = min(d.height(), max(260, area.height() - 24))
        if hasattr(d, 'compact_layout'):
            d.compact_layout(width)
        d.setMinimumSize(0, 0)
        d.resize(width, height)
        d.move(area.center() - d.rect().center())

    _ACTION_TITLES = {
        'install': 'Cài Việt hoá',
        'rollback': 'Khôi phục dữ liệu gốc',
        'verify': 'Kiểm tra tệp',
        'launch': 'Mở game',
        'scan': 'Quét thư mục game',
        'select_root': 'Chọn thư mục game',
        'discover': 'Tìm game tự động',
        'self_update': 'Kiểm tra cập nhật launcher',
        'apply_self_update': 'Cập nhật launcher',
        'publisher_vanilla_restore': 'Khôi phục dữ liệu gốc của nhà phát hành',
        'recover': 'Phục hồi thao tác bị ngắt',
        'startup': 'Khởi động launcher',
    }

    def _action_title(self, kind):
        return self._ACTION_TITLES.get(kind, kind or 'Thao tác')

    def _error_context(self, action='', probe=None, extra=None, operation=''):
        sync = dict(self._github_sync_state) if isinstance(self._github_sync_state, dict) else {}
        info = {
            'tuỳ chọn': 'tự kiểm tra cập nhật={}, tự kiểm tra bản gốc={}, tự khôi phục trước khi game cập nhật={}'.format(
                self.config_manager.get('check_updates_on_start', True),
                self.config_manager.get('check_official_on_start', True),
                self.config_manager.get('auto_restore_before_game_update', False),
            ),
            'gói cục bộ': 'có' if self.config_manager.get('payload_path', '') else 'không',
            'bảng kê tuỳ chỉnh': 'có' if self.config_manager.get('custom_manifest_url', '') else 'không',
        }
        try:
            game = self.current_game_info
            if game and game.installed and game.game_path:
                info['nhật ký chưa hoàn tất'] = 'CÓ' if self._engine().pending(game.game_path) else 'không'
        except Exception:
            info['nhật ký chưa hoàn tất'] = 'không đọc được'
        if extra:
            info.update(extra)
        return ErrorContext(
            action=action,
            operation=operation,
            progress=getattr(self.overview_view, '_progress_message', ''),
            path_manager=self.path_manager,
            game=self.current_game_info,
            sync=sync,
            channel=getattr(self, '_channel', None),
            probe=probe or sync.get('probe'),
            extra=info,
        )

    def build_error_report(self, action, code=None, exc=None, message='', probe=None, extra=None, extra_summary='', operation=''):
        report = build_report(
            code,
            exc=exc,
            message=message,
            action=action,
            ctx=self._error_context(action, probe=probe, extra=extra, operation=operation),
            extra_summary=extra_summary,
        )
        self._last_report = report
        return report

    def _show_error(self, action, code=None, exc=None, message='', probe=None, extra=None, extra_summary='', show=True, operation=''):
        """Build the plain-language report for a failure and (by default) show it. Returns the report."""
        report = self.build_error_report(action, code=code, exc=exc, message=message, probe=probe, extra=extra, extra_summary=extra_summary, operation=operation)
        if show:
            self._show(MessageDialog(action, '', parent=self, report=report))
        return report

    def show_unhandled(self, exc):
        """Called from sys.excepthook for exceptions that escaped a Qt slot."""
        if getattr(self, '_showing_unhandled', False):
            return
        self._showing_unhandled = True
        try:
            self._show_error('Lỗi không mong đợi', exc=exc)
        except Exception:
            logger.exception('Could not display unhandled error')
        finally:
            self._showing_unhandled = False

    def _explain_install_blocker(self):
        """Explain why the install button is greyed out (clicked from the "why?" link under the button)."""
        info = self.current_game_info
        if not info.installed or not info.game_path:
            self._show_error('Cài đặt Việt hoá', code='E-NO-GAME-FOLDER')
        elif info.is_running:
            self._show_error('Cài đặt Việt hoá', code='E-GAME-RUNNING')
        else:
            state = self._refresh_translation_state()
            self._show_error(
                'Cài đặt Việt hoá',
                code=state.get('blocker_code') or 'E-SYNC-PENDING',
                message=state.get('blocker_detail') or state.get('message', ''),
            )

    def _show(self, d):
        self._fit(d)
        focused = self.focusWidget()
        scrim = ModalScrim(self, self.config_manager.get('reduced_motion', False))
        scrim.show()
        scrim.raise_()
        try:
            return d.exec()
        finally:
            scrim.hide()
            scrim.deleteLater()
            self.overview_view.set_active_tab('overview')
            if focused:
                focused.setFocus()

    def _open_notifications(self, identity):
        modal = NotificationsModal(self.notifications, self)
        modal.select_id(identity)
        self._show(modal)

    def _handle_navigation(self, dest):
        if dest == 'overview':
            return
        if dest == 'launch':
            self._on_launch_clicked()
            return
        if dest == 'check_update':
            self._check_update()
            return
        if dest == 'notifications':
            self._show(NotificationsModal(self.notifications, self))
        elif dest == 'guide':
            self._show(GuideModal(self))
        elif dest == 'support':
            self._show(MessageDialog('Tính năng đang bảo trì', 'Tính năng đang bảo trì. Bản Việt hoá luôn luôn miễn phí.', parent=self))
        elif dest == 'settings':
            if self.active_worker:
                return
            d = SettingsModal(self.config_manager, self.network_service, self)
            d.game_path_changed.connect(lambda _: QTimer.singleShot(0, self._scan))
            d.github_sync_requested.connect(self._sync_github)
            d.channel_changed.connect(self._sync_github)
            self._show(d)
        elif dest == 'tools':
            if self.active_worker:
                return
            d = AdvancedToolsModal(self.path_manager, self.current_game_info, self)
            self._show(d)

    def closeEvent(self, e):
        if self.active_worker is not None:
            self.overview_view.show_progress(True, 'Đang có thao tác chạy. Hãy chờ thao tác hoàn tất trước khi đóng.', 0)
            e.ignore()
            return
        if self.background_worker is not None:
            self._close_after_background = True
            self.hide()
            e.ignore()
            return
        if self._official_worker is not None:
            self._close_after_official = True
            self.hide()
            e.ignore()
            return
        self._proc_timer.stop()
        self._release_timer.stop()
        e.accept()

    def _clamp_to_screen(self):
        if self.isMaximized() or self.isFullScreen():
            return
        area = self.screen().availableGeometry()
        width = min(self.width(), max(320, area.width() - 16))
        height = min(self.height(), max(280, area.height() - 16))
        x = max(area.left(), min(self.x(), area.right() - width + 1))
        y = max(area.top(), min(self.y(), area.bottom() - height + 1))
        self.setGeometry(x, y, width, height)

    def _screen_changed(self, *args):
        self.update()
        self.overview_view.update()
        self.overview_view.flag_mark.update()
        self._clamp_to_screen()

    def showEvent(self, event):
        super().showEvent(event)
        if not getattr(self, '_screen_hooked', False) and self.windowHandle():
            self.windowHandle().screenChanged.connect(self._screen_changed)
            self._screen_hooked = True

    def event(self, event):
        result = super().event(event)
        if event.type() == getattr(QEvent.Type, 'DevicePixelRatioChange', None):
            self.update()
            if hasattr(self, 'overview_view'):
                self.overview_view.flag_mark.update()
        return result

    def resizeEvent(self, e):
        super().resizeEvent(e)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        master = AssetManager.get().get_background()
        if not master.isNull():
            scale = max(self.width() / master.width(), self.height() / master.height())
            sw = self.width() / scale
            sh = self.height() / scale
            source = QRectF((master.width() - sw) / 2, (master.height() - sh) / 2, sw, sh)
            painter.drawPixmap(QRectF(self.rect()), master, source)
        gradient = QLinearGradient(0, self.height() * 0.86, 0, self.height())
        gradient.setColorAt(0, QColor(3, 15, 30, 0))
        gradient.setColorAt(1, QColor(3, 15, 30, 65))
        painter.fillRect(QRectF(0, self.height() * 0.86, self.width(), self.height() * 0.14), gradient)

    def _show_install_completed(self, result, shortcut_created=False):
        pref = getattr(self, '_pending_create_shortcut', shortcut_created)
        d = InstallCompletedDialog(
            self.current_game_info,
            result,
            shortcut_created_initially=shortcut_created,
            shortcut_preference=pref,
            parent=self,
        )
        self._show(d)
        if getattr(d, 'launch_game_clicked', False):
            self._on_launch_clicked()
