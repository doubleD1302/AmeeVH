"""Queued operation controller; all resource mutation lives in manifest services."""
from __future__ import annotations
import json,logging,uuid,hashlib,time
from pathlib import Path
from PySide6.QtCore import Qt,QThread,Signal,QTimer,QRectF,QRect,QEvent
from PySide6.QtGui import QPainter,QColor,QGuiApplication,QLinearGradient
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QScrollArea,QDialog,QFileDialog,QMessageBox,QGraphicsBlurEffect
from ..core.config import PathManager,ConfigManager,LAUNCHER_VERSION,DEFAULT_GITHUB_REPO,derived_github_endpoints
from ..core.game_detection import GameDetector,find_all_potential_game_installations
from ..core.installer import PatchInstaller
from ..core.rollback import RollbackEngine
from ..core.network import NetworkService
from ..core.update_notice import translation_state,newer,version_parts,detect_new_publisher_version
from ..core.vanilla_restore import VanillaRestoreEngine
from ..core.types import GameInfo,OperationEvent
from ..core.self_update import schedule_update
from .assets import AssetManager
from .components.title_bar import TitleBar
from .views.overview_view import OverviewView
from .views.notifications_modal import NotificationsModal
from .views.guide_modal import GuideModal
from .views.support_modal import SupportModal
from .views.settings_modal import SettingsModal
from .views.advanced_tools_modal import AdvancedToolsModal
from .views.confirmation_dialog import ConfirmationDialog
from .views.install_completed_dialog import InstallCompletedDialog
from ..core.shortcut import create_game_shortcut, create_desktop_shortcut
from .views.message_dialog import MessageDialog
from .views.update_notice_dialog import UpdateNoticeDialog
from .views.game_selection_dialog import GameSelectionDialog
from .components.modal_shell import ModalScrim
logger=logging.getLogger('launcher.controller')
class AsyncOperationWorker(QThread):
    event_emitted=Signal(object);result_ready=Signal(str,bool,object)
    def __init__(self,op,target,parent=None):super().__init__(parent);self.op=op;self.target=target
    def run(self):
        try:self.result_ready.emit(self.op,True,self.target(self.event_emitted.emit,self.op))
        except Exception as e:logger.exception('Operation failed');self.result_ready.emit(self.op,False,{'message':str(e),'error_code':getattr(e,'code','OPERATION_ERROR')})
class MainWindow(QMainWindow):
    github_sync_changed=Signal(object)
    def __init__(self,path_manager,config_manager):
        super().__init__();self.path_manager=path_manager;self.config_manager=config_manager;self.active_worker=None;self.active_operation_id=None;self.operation_kind='';self.current_game_info=GameInfo();self.notifications=[];self.background_worker=None;self._close_after_background=False;self._pending_sync=False;self._pending_discoveries=None;self._github_sync_state={'message':'Chưa đồng bộ GitHub.','fresh':False};self._manual_translation_check=False;self._manual_translation_next=False;self._notice_seen=set()
        self._configure_network();self.setWindowTitle('Stella Sora Việt Hóa');self.setWindowIcon(AssetManager.get().get_app_icon());self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.Window)
        area=QGuiApplication.primaryScreen().availableGeometry();self.setMinimumSize(min(480,area.width()),min(320,area.height()));self.resize(min(1280,area.width()-24),min(900,area.height()-24));self.move(area.center()-self.rect().center())
        central=QWidget();central.setObjectName('launcherRoot');central.setStyleSheet('#launcherRoot{background:transparent;}');self.setCentralWidget(central);l=QVBoxLayout(central);l.setContentsMargins(0,0,0,0);l.setSpacing(0)
        self.title_bar=TitleBar(self);self.title_bar.navigate_requested.connect(self._handle_navigation);self.title_bar.minimize_requested.connect(self.showMinimized);self.title_bar.close_requested.connect(self.close);self.setMenuWidget(self.title_bar)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);scroll.setFrameShape(QScrollArea.Shape.NoFrame);scroll.setStyleSheet('QScrollArea{background:transparent;border:0;}QScrollArea>QWidget>QWidget{background:transparent;}');self.overview_view=OverviewView();self.overview_view.setMinimumHeight(650);scroll.setWidget(self.overview_view);l.addWidget(scroll,1)
        v=self.overview_view;v.auto_detect_requested.connect(self._auto_detect);v.install_requested.connect(self._on_install_clicked);v.rollback_requested.connect(self._on_rollback_clicked);v.verify_requested.connect(self._on_verify_clicked);v.browse_requested.connect(self._browse);v.launch_requested.connect(self._on_launch_clicked);v.navigate_requested.connect(self._handle_navigation);v.view_notifications_requested.connect(lambda:self._handle_navigation('notifications'));v.notification_selected.connect(self._open_notifications);v.check_translation_requested.connect(self._check_translation_version)
        self.overview_view.update_game_status(self.current_game_info)
        self._release_timer=QTimer(self);self._release_timer.setInterval(30*60*1000);self._release_timer.timeout.connect(lambda:self._sync_github(automatic=True));self._release_timer.start()
        self._snooze_timer=QTimer(self);self._snooze_timer.setSingleShot(True);self._snooze_timer.timeout.connect(self._maybe_show_release_notice)
        QTimer.singleShot(0,self._clamp_to_screen);QTimer.singleShot(0,self._initial_load)
    def _configure_network(self):
        try:
            channel=self.config_manager.channel();self._channel_error=''
        except (ValueError,TypeError) as exc:
            # Preserve the invalid local values for correction in Settings; never
            # fall back silently to another repository or contact its endpoints.
            self._channel_error=str(exc)
            channel={'repo':str(self.config_manager.get('github_repo','')),'branch':str(self.config_manager.get('github_branch','')),'release_url':None,'notifications_url':None,'manifest_url':None,'configuration_error':self._channel_error}
        identity=json.dumps(channel,sort_keys=True,ensure_ascii=False)
        previous=getattr(self,'_github_identity',None);self._github_identity=identity;self._channel=channel
        if previous is not None and previous!=identity:
            self.notifications=[]
            if hasattr(self,'overview_view'):self.overview_view.set_notifications([])
            self._github_sync_state={'message':'Đã đổi kênh. Chưa đọc thông tin của nguồn mới.','fresh':False};self.github_sync_changed.emit(self._github_sync_state)
            if hasattr(self,'overview_view'):self.overview_view.set_translation_update(False);self.overview_view.set_install_allowed(False,'Kênh vừa thay đổi; cần kiểm tra lại.')
        cache=self.path_manager.app_data_dir/'network_cache'/hashlib.sha256(identity.encode('utf8')).hexdigest()[:16]
        self.network_service=NetworkService(channel['release_url'],channel['notifications_url'],cache)
        if self._channel_error:
            self._github_sync_state={'message':'Nguồn GitHub chưa hợp lệ: '+self._channel_error+' Mở Cài đặt launcher để sửa tên kho hoặc nhánh.','fresh':False,'configuration_error':self._channel_error}
            self.github_sync_changed.emit(self._github_sync_state)
        return not bool(self._channel_error)
    def _detected(self):
        raw=self.config_manager.get('game_path','')
        if not raw:
            if not self.config_manager.get('auto_detect_game',True):return GameInfo()
            found=find_all_potential_game_installations()
            if len(found)!=1:return GameInfo()
            raw=found[0]['path']
        return GameDetector(self.path_manager.backup_root).detect_info(raw)
    def _initial_load(self):
        try:
            from ..core.self_update import cleanup_update_artifacts
            cleanup_update_artifacts(self.path_manager.exe_dir)
            cleanup_update_artifacts(self.path_manager.app_data_dir / 'update_helper')
        except Exception:
            pass
        self._start('scan',lambda cb,op:{'game':self._detected()})
        self._sync_github(automatic=True)
    def _sync_github(self,automatic=False):
        if not self._configure_network():self._pending_sync=False;return
        if self.background_worker is not None:
            self._pending_sync=True;self._github_sync_state={'message':'Đang hoàn tất lần đọc trước. Sẽ đồng bộ lại kênh đã chọn.','fresh':False};self.github_sync_changed.emit(self._github_sync_state);return
        self.overview_view.set_translation_update(False);self.overview_view.set_install_allowed(False,'Đang kiểm tra bảng kê mới.')
        network=NetworkService(self.network_service.update_url,self.network_service.notifications_url,self.network_service.cache_dir,self.network_service.timeout)
        identity=self._github_identity;manifest_url=self._channel['manifest_url'];check_launcher=not automatic or self.config_manager.get('check_updates_on_start',True)
        fallback=str(self.path_manager.resource_dir/'ui'/'notifications.json') if network.notifications_url==derived_github_endpoints(DEFAULT_GITHUB_REPO,'main')['remote_notifications_url'] else None
        def work(cb,op):
            result=network.sync_channel(fallback,LAUNCHER_VERSION,manifest_url,check_launcher);result['source_identity']=identity;return result
        self._github_sync_state={'message':'Đang đọc thông báo và bản phát hành từ GitHub…','fresh':False};self.github_sync_changed.emit(self._github_sync_state)
        worker=AsyncOperationWorker(identity,work,self);self.background_worker=worker
        worker.result_ready.connect(self._background_finish);worker.finished.connect(lambda:self._release_background(worker));worker.start()
    def _background_finish(self,identity,success,result):
        # A response from an old repo/branch/custom URL must not replace the
        # current channel's display. Cache is also namespaced by this identity.
        if identity!=self._github_identity:return
        if not success:
            self._github_sync_state={'message':'Không đồng bộ được GitHub: '+result.get('message','Lỗi kết nối.'),'fresh':False}
        else:
            self._github_sync_state=result;self.notifications=result.get('notifications',[]);self.overview_view.set_notifications(self.notifications)
            self.network_service.notification_status=result['notification_status'];self.network_service.notification_message=result['notification_message'];self.network_service.notification_version=result.get('notification_version')
            self._record_release_observation(result)
        self._refresh_translation_state()
        self.github_sync_changed.emit(self._github_sync_state)
        if self._manual_translation_check:
            self._manual_translation_check=False
            self._refresh_translation_state();state=translation_state(self._github_sync_state,self.current_game_info)
            message=state['message']
            if self.config_manager.get('payload_path',''):message+='\nLauncher đang dùng gói cục bộ đã chọn để cài đặt.'
            if not success:message=self._github_sync_state['message']
            elif result.get('manifest_status')!='online':message+='\n'+str(result.get('manifest_error') or result.get('release_error') or '')
            QTimer.singleShot(0,lambda m=message:self._show(MessageDialog('Kiểm tra phiên bản Việt hoá',m,parent=self)))
        else:QTimer.singleShot(1200,self._maybe_show_release_notice)
    def _release_background(self,worker):
        if self.background_worker is worker:self.background_worker=None
        worker.deleteLater()
        if self._close_after_background:self._close_after_background=False;QTimer.singleShot(0,self.close)
        elif self._pending_sync:
            self._pending_sync=False
            if self._manual_translation_next:self._manual_translation_check=True;self._manual_translation_next=False
            QTimer.singleShot(0,self._sync_github)
    def _start(self,kind,target):
        if self.active_worker is not None:return False
        op=uuid.uuid4().hex;self.active_operation_id=op;self.operation_kind=kind;
        if kind in ('startup','self_update'):self.overview_view.connection_label.set_status('Đang kết nối','busy')
        self.overview_view.set_busy(True,self.config_manager.get('reduced_motion',False));self.overview_view.show_progress(True,'Đang xử lý…',0)
        worker=AsyncOperationWorker(op,target,self);self.active_worker=worker;worker.event_emitted.connect(self._event);worker.result_ready.connect(self._finish);worker.finished.connect(lambda:self._release_worker(worker));worker.start();return True
    def _event(self,e):
        if e.operation_id==self.active_operation_id:self.overview_view.handle_operation_event(e)
    def _release_worker(self,w):
        if self.active_worker is w:self.active_worker=None;self.active_operation_id=None;self.overview_view.set_busy(False,self.config_manager.get('reduced_motion',False))
        w.deleteLater()
        if getattr(self,'_close_after_worker',False):self._close_after_worker=False;QTimer.singleShot(150,lambda:QApplication.instance().quit())
        elif self._pending_discoveries is not None:
            found=self._pending_discoveries;self._pending_discoveries=None;QTimer.singleShot(0,lambda:self._choose_discovered(found))
        else:QTimer.singleShot(0,self._maybe_show_release_notice)
    def _finish(self,op,success,result):
        if op!=self.active_operation_id:return
        if not success:
            msg=result.get('message','Lỗi chưa xác định');self.overview_view.show_completed('⚠ Lỗi: '+msg)
            self._show(MessageDialog('Không thể hoàn tất thao tác',msg,'Mã lỗi: '+result.get('error_code','')+'\nNhật ký: '+str(self.path_manager.logs_dir/'launcher.log'),parent=self,is_error=True));return
        if not isinstance(result,dict):return
        if self.operation_kind=='discover':
            self._pending_discoveries=result.get('installations',[]);self.overview_view.show_progress(False);return
        if self.operation_kind=='select_root':
            info=result['game']
            if not info.installed:
                self.overview_view.show_progress(False);self._show(MessageDialog('Chưa chọn được thư mục','Không tìm thấy StellaSora.exe tại thư mục này. Đường dẫn đang dùng được giữ nguyên.',parent=self));return
            previous=self.config_manager.get('game_path','');self.config_manager.set('game_path',str(info.game_path))
            if not self.config_manager.save():
                self.config_manager.set('game_path',previous);self._show(MessageDialog('Chưa lưu được thư mục','Đường dẫn đang dùng được giữ nguyên.','\n'.join(self.config_manager.warnings),parent=self,is_error=True));return
        if 'game' in result:self.current_game_info=result['game'];self.overview_view.update_game_status(self.current_game_info);self._refresh_translation_state()
        if self.operation_kind in ('scan','select_root'):self.overview_view.show_progress(False)
        elif self.operation_kind=='verify':self.overview_view.show_completed('✓ Hoàn tất kiểm tra! Đã đối chiếu '+str(result.get('files',0))+' tệp của bản dịch v'+str(result.get('version',''))+' toàn vẹn.')
        elif self.operation_kind=='launch':self.overview_view.show_completed(result.get('message','✓ Đã gửi lệnh mở game.'))
        elif self.operation_kind=='self_update':
            if result.get('status')!='online':
                self._show(MessageDialog('Không kiểm tra được cập nhật',result.get('message','Không thể kết nối GitHub.'),parent=self,is_error=True))
            elif not result.get('has_update'):
                self._show(MessageDialog('Cập nhật launcher',f'Bạn đang dùng phiên bản mới nhất ({LAUNCHER_VERSION}).\nKhông có bản cập nhật mới trên GitHub.',parent=self))
            elif not result.get('download_url'):
                self._show(MessageDialog('Cập nhật launcher',result.get('message','Chưa có tệp cập nhật tự động được xác minh.'),parent=self))
            else:QTimer.singleShot(0,lambda:self._confirm_update(result))
        elif self.operation_kind=='apply_self_update':
            self.overview_view.show_completed('✓ Cập nhật hoàn tất! Đang khởi động lại launcher…')
            self._close_after_worker=True
        elif self.operation_kind=='install':
            msg=result.get('message','')
            if not msg.startswith('✓') and not msg.startswith('Hoàn tất'):msg=f'✓ Hoàn tất cài đặt! {msg}'
            sc_ok = False
            if getattr(self, '_pending_create_shortcut', False) and getattr(self.current_game_info, 'game_path', None):
                ok, sc_msg = create_game_shortcut(self.current_game_info.game_path)
                sc_ok = ok
                if ok:
                    msg += '\n✓ Đã thêm lối tắt "Stella Sora Việt Hóa" vào màn hình chính.'
            self.overview_view.show_completed(msg)
            QTimer.singleShot(150, lambda r=result, s=sc_ok: self._show_install_completed(r, s))
        elif self.operation_kind=='rollback':
            msg=result.get('message','')
            if not msg.startswith('✓') and not msg.startswith('Hoàn tất'):msg=f'✓ Hoàn tất khôi phục! {msg}'
            self.overview_view.show_completed(msg)
        else:self.overview_view.show_completed(result.get('message','✓ Hoàn tất thao tác.'))
    def _auto_detect(self):
        if self.active_worker is not None:return
        self._start('discover',lambda cb,op:{'installations':find_all_potential_game_installations()})
    def _choose_discovered(self,found):
        if self.active_worker is not None:return
        if not found:
            self._show(MessageDialog('Chưa tìm thấy game','Không tìm thấy Stella Sora trong thư viện Steam hoặc vị trí Yostar thông dụng. Bấm biểu tượng thư mục để chọn thủ công nơi có StellaSora.exe. Thư mục hiện tại được giữ nguyên.',parent=self));return
        if len(found)==1:self._select_game_root(found[0]['path']);return
        dialog=GameSelectionDialog(found,self)
        if self._show(dialog)==QDialog.DialogCode.Accepted and dialog.selected_path:self._select_game_root(dialog.selected_path)
    def _select_game_root(self,path):
        self._start('select_root',lambda cb,op:{'game':GameDetector(self.path_manager.backup_root).detect_info(path)})
    def _scan(self):self._start('scan',lambda cb,op:{'game':self._detected()})
    def _browse(self):
        if self.active_worker:return
        path=QFileDialog.getExistingDirectory(self,'Chọn thư mục có StellaSora.exe',str(self.current_game_info.game_path or 'C:/'))
        if path:self._select_game_root(path)
    def _engine(self):return PatchInstaller(self.path_manager.backup_root,self.path_manager.journals_dir)
    def _valid_target(self):return bool(self.current_game_info.installed and self.current_game_info.game_path and not self.current_game_info.is_running and not self.active_worker)
    def _confirm(self,title,msg,label='Tiếp tục'):
        d=ConfirmationDialog(title,msg,label,parent=self);return self._show(d)==QDialog.DialogCode.Accepted
    def _on_install_clicked(self):
        if not self._valid_target():return
        root=self.current_game_info.game_path
        info=self.current_game_info;state=self._refresh_translation_state()
        if not state['can_install']:
            self._show(MessageDialog('Chưa thể cài Việt hoá',state['message'],parent=self,is_error=True));return

        # Kiểm tra nếu nhà phát hành có bản cập nhật mới
        manifest_meta = {
            'client_game_version': self._github_sync_state.get('translation_game', '2.0.1'),
            'resource_version': self._github_sync_state.get('translation_resource', '2610291554')
        }
        has_new_pub, pub_reason = detect_new_publisher_version(info, manifest_meta)
        if has_new_pub:
            v_engine = VanillaRestoreEngine(self.path_manager.backup_root, self.path_manager.journals_dir)
            try:
                v_engine.restore_vanilla(root)
            except Exception:
                pass
            self.current_game_info = self._detected()
            self._render_game_info(self.current_game_info)
            self._refresh_translation_state()

            dialog = ConfirmationDialog(
                'Game mới cập nhật tài nguyên mới',
                f'Phát hiện game có bản cập nhật mới từ nhà phát hành ({pub_reason}).\n\n'
                f'Launcher đã lập tức khôi phục toàn bộ dữ liệu gốc nguyên bản (chưa Việt hoá) để bảo toàn tệp game.\n\n'
                f'Vui lòng mở game để cập nhật tài nguyên mới trước khi cài Việt hoá!',
                'Mở Game ngay',
                parent=self
            )
            if self._show(dialog) == QDialog.DialogCode.Accepted:
                self._on_launch_clicked()
            return

        is_update=state['available']
        local=self.config_manager.get('payload_path','');channel_valid=self._configure_network()
        if not local and not channel_valid:
            self._show(MessageDialog('Chưa thể tải bản dịch',self._github_sync_state['message'],parent=self));return
        pref_shortcut = self.config_manager.get('create_desktop_shortcut', True)
        cd = ConfirmationDialog('CÀI / CẬP NHẬT VIỆT HÓA','Thư mục: '+str(root)+'\n\n'+state['message']+'\n\nTải hoặc đọc gói đã chọn, sao lưu và cài đúng các tệp trong manifest. Gói chỉ gồm texture sẽ chỉ cài texture.','Cài bản dịch',show_shortcut_option=True,shortcut_default=pref_shortcut,parent=self)
        if self._show(cd) != QDialog.DialogCode.Accepted:return
        self._pending_create_shortcut = cd.create_shortcut_requested()
        self.config_manager.set('create_desktop_shortcut', self._pending_create_shortcut)
        self.config_manager.save()
        network=self.network_service;manifest_url=self._channel['manifest_url']
        def work(cb,op):
            payload=Path(local) if local else network.prepare_payload(self.path_manager.payload_root,manifest_url,cb,op)
            if is_update:
                # The release can change while the user reads the confirmation.
                # Re-check the actual freshly downloaded manifest before writing.
                manifest=json.loads((payload/'patch_manifest.json').read_text(encoding='utf8'))
                state=translation_state({'release_status':'online','manifest_status':'online','translation_version':manifest.get('version'),'translation_game':manifest.get('client_game_version'),'translation_resource':manifest.get('resource_version')},info)
                if not state['available']:raise RuntimeError('Không còn bản Việt hoá mới hơn: '+state['message'])
            r=self._engine().install(root,payload,operation_id=op,event_cb=cb);return {'game':self._detected(),'message':f"✓ Hoàn tất cài đặt! Đã nạp thành công {r['files_count']} tệp bản dịch (v{r['version']})."}
        self._start('install',work)
    def _action_target(self,action,require_receipt=True):
        if self.active_worker is not None:
            self._show(MessageDialog(action,'Đang có thao tác chạy. Hãy chờ hoàn tất rồi thử lại.',parent=self));return None
        info=self.current_game_info
        if not info.installed or not info.game_path:
            self._show(MessageDialog(action,'Hãy chọn đúng thư mục có StellaSora.exe bằng nút thư mục, rồi thử lại.',parent=self));return None
        if info.is_running:
            self._show(MessageDialog(action,'Hãy đóng game trước khi '+action.lower()+'. Nếu game đã đóng, chọn lại thư mục để cập nhật trạng thái.',parent=self));return None
        if require_receipt and not info.installed_receipt:
            self._show(MessageDialog(action,'Thư mục này chưa có biên bản cài đặt hợp lệ của launcher.',
                'Kiểm tra tệp cần danh sách SHA256 đã cài. Khôi phục cần bản sao lưu gắn với đúng thư mục game.\n'
                'Nếu bạn cài bản dịch bằng công cụ khác, launcher chưa thể xác minh hoặc khôi phục bản đó.\n'
                'Sau khi cài bằng launcher này, hai thao tác sẽ dùng biên bản và bản sao lưu được tạo trong lần cài.',parent=self));return None
        return info.game_path
    def _on_rollback_clicked(self):
        root=self._action_target('Khôi phục', require_receipt=False)
        if root is None:return
        if self._confirm(
            'KHÔI PHỤC DỮ LIỆU GỐC NGUYÊN BẢN',
            'Thư mục: '+str(root)+'\n\n'
            'Thao tác này sẽ gỡ bỏ hoàn toàn bản Việt hóa và phục hồi toàn bộ dữ liệu game về trạng thái gốc nguyên bản từ nhà phát hành (bản hoàn chỉnh, chưa Việt hóa).\n\n'
            'Bạn có chắc chắn muốn khôi phục dữ liệu gốc?',
            'Khôi phục dữ liệu gốc'
        ):
            def work(cb,op):
                r = RollbackEngine(self.path_manager.backup_root,self.path_manager.journals_dir).rollback(root,operation_id=op,event_cb=cb)
                return {'game':self._detected(),'message':r.get('message','✓ Hoàn tất khôi phục! Đã đưa game về dữ liệu gốc nguyên bản của nhà phát hành.')}
            self._start('rollback',work)
    def _on_verify_clicked(self):
        root=self._action_target('Kiểm tra tệp')
        if root is not None:self._start('verify',lambda cb,op:self._engine().verify_installed(root,cb,op))
    def _on_launch_clicked(self):
        if not self._valid_target():return
        info=self.current_game_info
        def work(cb,op):
            ok,msg=GameDetector(self.path_manager.backup_root).launch(info)
            if not ok:raise RuntimeError(msg)
            return {'message':msg}
        self._start('launch',work)
    def _check_update(self):
        if not self._configure_network():
            self._show(MessageDialog('Chưa thể kiểm tra cập nhật',self._github_sync_state['message'],parent=self));return
        network=self.network_service;self._start('self_update',lambda cb,op:network.check_for_updates(LAUNCHER_VERSION))
    def _check_translation_version(self):
        if self.active_worker is not None:return
        if not self._configure_network():
            self._show(MessageDialog('Chưa thể kiểm tra',self._github_sync_state['message'],parent=self,is_error=True));return
        if self.background_worker is not None:
            self._manual_translation_next=True;self._pending_sync=True;return
        self._manual_translation_check=True;self._sync_github()
    def _refresh_translation_state(self):
        local=self.config_manager.get('payload_path','')
        if local:
            try:
                path=Path(local)/'patch_manifest.json'
                if not path.is_file() or path.stat().st_size>4*1024*1024:raise ValueError('Thiếu bảng kê hoặc bảng kê quá lớn.')
                manifest=self.network_service._windows_manifest(json.loads(path.read_text(encoding='utf8')))
                local_state={'release_status':'online','manifest_status':'online','translation_version':manifest['version'],'translation_game':manifest['client_game_version'],'translation_resource':manifest['resource_version']}
                state=translation_state(local_state,self.current_game_info)
                state['message']='Gói cục bộ: '+state['message']
            except Exception as exc:state={'available':False,'can_install':False,'message':'Không đọc được bảng kê của gói cục bộ: '+str(exc)}
        else:state=translation_state(self._github_sync_state,self.current_game_info)
        if hasattr(self,'overview_view'):
            self.overview_view.set_translation_update(state['available'])
            self.overview_view.btn_check_translation.setToolTip(state['message'])
            self.overview_view.set_install_allowed(state['can_install'],state['message'])
        return state
    def _record_release_observation(self,sync):
        if sync.get('release_status')!='online':return
        version=sync.get('release_version')
        if version_parts(version) is None:return
        key=hashlib.sha256(self._github_identity.encode('utf8')).hexdigest()
        baselines=self.config_manager.get('release_notice_baselines',{})
        pending=self.config_manager.get('release_notice_pending',{})
        baselines=dict(baselines) if isinstance(baselines,dict) else {}
        pending=dict(pending) if isinstance(pending,dict) else {}
        previous=baselines.get(key)
        if previous and newer(version,previous):pending[key]=version
        if not previous or not newer(previous,version):baselines[key]=version
        self.config_manager.update({'release_notice_baselines':baselines,'release_notice_pending':pending});self.config_manager.save()
    def _maybe_show_release_notice(self):
        if self.active_worker is not None or self.background_worker is not None or self._manual_translation_check or not self.isVisible():return
        sync=self._github_sync_state
        if sync.get('release_status')!='online':return
        version=sync.get('release_version')
        channel_key=hashlib.sha256(self._github_identity.encode('utf8')).hexdigest()
        pending=self.config_manager.get('release_notice_pending',{})
        pending=dict(pending) if isinstance(pending,dict) else {}
        if version_parts(version) is None or not (pending.get(channel_key)==version or sync.get('update',{}).get('has_update') or translation_state(sync,self.current_game_info)['available']):return
        key=self._github_identity+'|'+version
        try:snooze_until=float(self.config_manager.get('release_notice_snooze_until',0) or 0)
        except (ValueError,TypeError):snooze_until=0
        if key in self._notice_seen:return
        remaining=snooze_until-time.time()
        if remaining>0:
            self._snooze_timer.start(min(2147483647,max(1,int(remaining*1000)+1)));return
        has_l_update=bool(sync.get('update',{}).get('has_update') and sync.get('update',{}).get('download_url'))
        result=self._show(UpdateNoticeDialog(version,sync.get('release_notes',''),self,has_launcher_update=has_l_update))
        if result==3:
            self._notice_seen.add(key)
            if pending.get(channel_key)==version:
                pending.pop(channel_key,None);self.config_manager.set('release_notice_pending',pending);self.config_manager.save()
            if has_l_update:
                QTimer.singleShot(50,lambda:self._confirm_update(sync['update']))
        elif result==2:
            self.config_manager.set('release_notice_snooze_until',time.time()+24*60*60)
            if not self.config_manager.save():self._show(MessageDialog('Chưa lưu được lựa chọn','Không thể lưu thời gian tắt thông báo. Thông báo có thể xuất hiện lại khi mở launcher.',parent=self,is_error=True))
            self._snooze_timer.start(24*60*60*1000)
        else:
            self._notice_seen.add(key)
            if pending.get(channel_key)==version:
                pending.pop(channel_key,None);self.config_manager.set('release_notice_pending',pending);self.config_manager.save()
    def _prompt_auto_update(self,update):
        if self.active_worker is not None:return
        self._confirm_update(update)
    def _confirm_update(self,data):
        latest=data.get('latest_version','')
        body=f'Đã có phiên bản launcher mới: {latest} (hiện tại: v{LAUNCHER_VERSION}).\n\nBạn có muốn tải và tự động cập nhật ngay bây giờ không?'
        cl=data.get('changelog','').strip()
        if cl:
            cl_lines=[l for l in cl.splitlines() if l.strip()][:5]
            if cl_lines:body+='\n\nNội dung mới:\n'+('\n'.join(cl_lines))
        if not self._confirm(f'CẬP NHẬT LAUNCHER {latest}',body,'Cập nhật ngay'):return
        def work(cb,op):
            a=data['asset'];dest=self.path_manager.app_data_dir/'updates'/f'StellaSora_Launcher_{latest}.exe';self.network_service.download(data['download_url'],dest,a['size'],data['sha256'],cb,op);schedule_update(dest,data['sha256'],self.path_manager.app_data_dir);return {'message':'Đã chuẩn bị bản cập nhật.'}
        self._start('apply_self_update',work)
    def _recover(self):
        if not self._valid_target():return
        root=self.current_game_info.game_path
        if self._confirm('PHỤC HỒI THAO TÁC BỊ NGẮT','Đọc nhật ký và đưa các tệp về trạng thái trước thao tác bị ngắt tại '+str(root)+'. Tệp thay đổi ngoài thao tác sẽ được giữ và báo xung đột.','Phục hồi'):
            def work(cb,op):
                r=self._engine().recover(root,cb,op);return {'game':self._detected(),'message':'Đã phục hồi '+str(r['journals'])+' nhật ký.'}
            self._start('recover',work)
    def _fit(self,d):
        area=self.screen().availableGeometry();width=min(d.width(),max(280,area.width()-24));height=min(d.height(),max(260,area.height()-24))
        if hasattr(d,'compact_layout'):d.compact_layout(width)
        d.setMinimumSize(0,0);d.resize(width,height);d.move(area.center()-d.rect().center())
    def _show(self,d):
        self._fit(d);focused=self.focusWidget();scrim=ModalScrim(self,self.config_manager.get('reduced_motion',False));scrim.show();scrim.raise_()
        try:return d.exec()
        finally:
            scrim.hide();scrim.deleteLater();self.overview_view.set_active_tab('overview')
            if focused:focused.setFocus()
    def _open_notifications(self,identity):
        modal=NotificationsModal(self.notifications,self);modal.select_id(identity);self._show(modal)
    def _handle_navigation(self,dest):
        if dest=='overview':return
        if dest=='launch':self._on_launch_clicked();return
        if dest=='check_update':self._check_update();return
        if dest=='notifications':self._show(NotificationsModal(self.notifications,self))
        elif dest=='guide':self._show(GuideModal(self))
        elif dest=='support':self._show(SupportModal(self.network_service.get_supporter_data(),self))
        elif dest=='settings':
            if self.active_worker:return
            d=SettingsModal(self.config_manager,self.network_service,self);d.game_path_changed.connect(lambda _:QTimer.singleShot(0,self._scan));d.github_sync_requested.connect(self._sync_github);d.channel_changed.connect(self._sync_github);self._show(d)
        elif dest=='tools':
            if self.active_worker:return
            d=AdvancedToolsModal(self.path_manager,self.current_game_info,self);self._show(d)
    def closeEvent(self,e):
        if self.active_worker is not None:
            self.overview_view.show_progress(True,'Đang có thao tác chạy. Hãy chờ thao tác hoàn tất trước khi đóng.',0);e.ignore();return
        if self.background_worker is not None:
            self._close_after_background=True;self.hide();e.ignore();return
        e.accept()
    def _clamp_to_screen(self):
        if self.isMaximized() or self.isFullScreen():return
        area=self.screen().availableGeometry();width=min(self.width(),max(320,area.width()-16));height=min(self.height(),max(280,area.height()-16));x=max(area.left(),min(self.x(),area.right()-width+1));y=max(area.top(),min(self.y(),area.bottom()-height+1));self.setGeometry(x,y,width,height)
    def _screen_changed(self,*args):
        self.update();self.overview_view.update();self.overview_view.flag_mark.update();self._clamp_to_screen()
    def showEvent(self,event):
        super().showEvent(event)
        if not getattr(self,'_screen_hooked',False) and self.windowHandle():self.windowHandle().screenChanged.connect(self._screen_changed);self._screen_hooked=True
    def event(self,event):
        result=super().event(event)
        if event.type()==getattr(QEvent.Type,'DevicePixelRatioChange',None):
            self.update()
            if hasattr(self,'overview_view'):self.overview_view.flag_mark.update()
        return result
    def resizeEvent(self,e):super().resizeEvent(e)
    def paintEvent(self,e):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing,True);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,True);master=AssetManager.get().get_background()
        if not master.isNull():
            # QPainter applies the paint-device DPR to this single master-to-device draw.
            # There is no logical-sized pixmap that the OS must enlarge again.
            scale=max(self.width()/master.width(),self.height()/master.height());sw=self.width()/scale;sh=self.height()/scale;source=QRectF((master.width()-sw)/2,(master.height()-sh)/2,sw,sh);painter.drawPixmap(QRectF(self.rect()),master,source)
        # Local bottom readability only; the main artwork is never blurred or fogged.
        gradient=QLinearGradient(0,self.height()*.86,0,self.height());gradient.setColorAt(0,QColor(3,15,30,0));gradient.setColorAt(1,QColor(3,15,30,65));painter.fillRect(QRectF(0,self.height()*.86,self.width(),self.height()*.14),gradient)

    def _show_install_completed(self, result, shortcut_created=False):
        d = InstallCompletedDialog(self.current_game_info, result, shortcut_created_initially=shortcut_created, parent=self)
        self._show(d)
        if getattr(d, 'launch_game_clicked', False):
            self._on_launch_clicked()
