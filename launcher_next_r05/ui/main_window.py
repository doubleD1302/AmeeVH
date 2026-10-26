"""Queued operation controller; all resource mutation lives in manifest services."""
from __future__ import annotations
import json,logging,uuid
from pathlib import Path
from PySide6.QtCore import Qt,QThread,Signal,QTimer,QRectF,QRect,QEvent
from PySide6.QtGui import QPainter,QColor,QGuiApplication,QLinearGradient
from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QScrollArea,QDialog,QFileDialog,QMessageBox,QGraphicsBlurEffect
from ..core.config import PathManager,ConfigManager,LAUNCHER_VERSION
from ..core.game_detection import GameDetector
from ..core.installer import PatchInstaller
from ..core.rollback import RollbackEngine
from ..core.network import NetworkService
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
from .views.message_dialog import MessageDialog
from .components.modal_shell import ModalScrim
logger=logging.getLogger('launcher.controller')
class AsyncOperationWorker(QThread):
    event_emitted=Signal(object);result_ready=Signal(str,bool,object)
    def __init__(self,op,target,parent=None):super().__init__(parent);self.op=op;self.target=target
    def run(self):
        try:self.result_ready.emit(self.op,True,self.target(self.event_emitted.emit,self.op))
        except Exception as e:logger.exception('Operation failed');self.result_ready.emit(self.op,False,{'message':str(e),'error_code':getattr(e,'code','OPERATION_ERROR')})
class MainWindow(QMainWindow):
    def __init__(self,path_manager,config_manager):
        super().__init__();self.path_manager=path_manager;self.config_manager=config_manager;self.active_worker=None;self.active_operation_id=None;self.operation_kind='';self.current_game_info=GameInfo();self.notifications=[]
        c=config_manager;api=c.get('github_api_url') or f"https://api.github.com/repos/{c.get('github_repo')}/releases/latest";ann=c.get('custom_announcements_url') or c.get('remote_notifications_url')
        self.network_service=NetworkService(api,ann,path_manager.app_data_dir/'network_cache');self.setWindowTitle('Stella Sora Việt Hóa · Candidate r05');self.setWindowIcon(AssetManager.get().get_app_icon());self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.Window)
        area=QGuiApplication.primaryScreen().availableGeometry();self.setMinimumSize(min(480,area.width()),min(320,area.height()));self.resize(min(1280,area.width()-24),min(900,area.height()-24));self.move(area.center()-self.rect().center())
        central=QWidget();central.setObjectName('launcherRoot');central.setStyleSheet('#launcherRoot{background:transparent;}');self.setCentralWidget(central);l=QVBoxLayout(central);l.setContentsMargins(0,0,0,0);l.setSpacing(0)
        self.title_bar=TitleBar(self);self.title_bar.navigate_requested.connect(self._handle_navigation);self.title_bar.minimize_requested.connect(self.showMinimized);self.title_bar.close_requested.connect(self.close);self.setMenuWidget(self.title_bar)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.Shape.NoFrame);scroll.setStyleSheet('QScrollArea{background:transparent;border:0;}QScrollArea>QWidget>QWidget{background:transparent;}');self.overview_view=OverviewView();self.overview_view.setMinimumHeight(650);scroll.setWidget(self.overview_view);l.addWidget(scroll,1)
        v=self.overview_view;v.install_requested.connect(self._on_install_clicked);v.rollback_requested.connect(self._on_rollback_clicked);v.verify_requested.connect(self._on_verify_clicked);v.browse_requested.connect(self._browse);v.launch_requested.connect(self._on_launch_clicked);v.navigate_requested.connect(self._handle_navigation);v.view_notifications_requested.connect(lambda:self._handle_navigation('notifications'));v.notification_selected.connect(self._open_notifications)
        self.overview_view.update_game_status(self.current_game_info)
        QTimer.singleShot(0,self._clamp_to_screen);QTimer.singleShot(0,self._initial_load)
    def _detected(self):
        raw=self.config_manager.get('game_path','')
        if not raw and not self.config_manager.get('auto_detect_game',True):return GameInfo()
        return GameDetector(self.path_manager.backup_root).detect_info(raw)
    def _initial_load(self):
        def work(cb,op):
            game=self._detected();items=self.network_service.fetch_notifications(str(self.path_manager.resource_dir/'ui'/'notifications.json'))
            update=self.network_service.check_for_updates(LAUNCHER_VERSION) if self.config_manager.get('check_updates_on_start',True) else None
            return {'game':game,'notifications':items,'update':update}
        self._start('startup',work)
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
        if getattr(self,'_close_after_worker',False):self._close_after_worker=False;QTimer.singleShot(0,self.close)
    def _finish(self,op,success,result):
        if op!=self.active_operation_id:return
        if not success:
            msg=result.get('message','Lỗi chưa xác định');self.overview_view.show_progress(True,msg,0);self.overview_view.progress_bar.setRange(0,100)
            self._show(MessageDialog('Không thể hoàn tất thao tác',msg,'Mã lỗi: '+result.get('error_code','')+'\nNhật ký: '+str(self.path_manager.logs_dir/'launcher.log'),parent=self,is_error=True));return

        if isinstance(result,dict):
            if 'game' in result:self.current_game_info=result['game'];self.overview_view.update_game_status(self.current_game_info)
            if 'notifications' in result:
                self.notifications=result['notifications']
                if self.notifications:self.overview_view.set_notifications(self.notifications)
                else:self.overview_view.set_notifications([])
            source=self.network_service.notification_status
            label,state={'online':('Trực tuyến','online'),'empty':('Chưa có thông báo','warning'),'cached':('Bản lưu ngoại tuyến','offline'),'bundled':('Ngoại tuyến','offline'),'error':('Lỗi kết nối','error')}.get(source,('Chưa kiểm tra kết nối','offline'))
            if isinstance(result.get('update'),dict) and result['update'].get('status')=='error':label,state='Lỗi kiểm tra cập nhật','error'
            self.overview_view.connection_label.set_status(label,state);self.overview_view.connection_label.setToolTip(self.network_service.notification_message)
            if self.operation_kind=='startup':
                warnings='\n'.join(self.config_manager.warnings)
                if warnings:self.overview_view.show_progress(True,warnings,0)
                else:self.overview_view.show_progress(False)
            elif self.operation_kind=='verify':self.overview_view.show_progress(True,'Đã đối chiếu SHA256 '+str(result.get('files'))+' tệp với biên bản '+str(result.get('version'))+'.',100)
            elif self.operation_kind=='launch':self.overview_view.show_progress(True,result.get('message','Đã gửi lệnh mở game.'),100)
            elif self.operation_kind=='self_update':
                data=result
                if not data.get('has_update') or not data.get('download_url'):self._show(MessageDialog('Cập nhật launcher',data.get('message','Chưa có bản update xác minh.'),parent=self))
                else:QTimer.singleShot(0,lambda:self._confirm_update(data))
            elif self.operation_kind=='apply_self_update':self._close_after_worker=True
            elif self.operation_kind!='scan':self.overview_view.show_progress(True,result.get('message','Đã hoàn tất thao tác.'),100)
    def _scan(self):self._start('scan',lambda cb,op:{'game':self._detected()})
    def _browse(self):
        if self.active_worker:return
        path=QFileDialog.getExistingDirectory(self,'Chọn thư mục có StellaSora.exe',str(self.current_game_info.game_path or 'C:/'))
        if path:
            self.config_manager.set('game_path',path)
            if not self.config_manager.save():QMessageBox.warning(self,'Chưa lưu được cấu hình','\n'.join(self.config_manager.warnings))
            self._scan()
    def _engine(self):return PatchInstaller(self.path_manager.backup_root,self.path_manager.journals_dir)
    def _valid_target(self):return bool(self.current_game_info.installed and self.current_game_info.game_path and not self.current_game_info.is_running and not self.active_worker)
    def _confirm(self,title,msg,label='Tiếp tục'):
        d=ConfirmationDialog(title,msg,label,parent=self);return self._show(d)==QDialog.DialogCode.Accepted
    def _on_install_clicked(self):
        if not self._valid_target():return
        root=self.current_game_info.game_path
        if not self._confirm('CÀI / CẬP NHẬT VIỆT HÓA','Thư mục: '+str(root)+'\n\nTải hoặc đọc gói đã chọn, đối chiếu phiên bản, sao lưu và cài đúng các tệp trong manifest. Gói chỉ gồm texture sẽ chỉ cài texture.','Cài bản dịch'):return
        local=self.config_manager.get('payload_path','')
        def work(cb,op):
            payload=Path(local) if local else self.network_service.prepare_payload(self.path_manager.payload_root,self.config_manager.get('custom_manifest_url') or None,cb,op)
            r=self._engine().install(root,payload,operation_id=op,event_cb=cb);return {'game':self._detected(),'message':f"Đã cài {r['files_count']} tệp theo manifest {r['version']}."}
        self._start('install',work)
    def _on_rollback_clicked(self):
        if not self._valid_target():return
        root=self.current_game_info.game_path;r=self.current_game_info.installed_receipt or {}
        if self._confirm('KHÔI PHỤC TRẠNG THÁI TRƯỚC CÀI','Thư mục: '+str(root)+'\nBackup: '+str(r.get('backup_dir','Chưa xác định'))+'\n\nChỉ phục hồi khi các tệp hiện tại còn khớp bản đã cài. Nếu game đã cập nhật, thao tác sẽ báo xung đột.','Khôi phục'):
            def work(cb,op):
                RollbackEngine(self.path_manager.backup_root,self.path_manager.journals_dir).rollback(root,operation_id=op,event_cb=cb);return {'game':self._detected(),'message':'Đã khôi phục trạng thái trước lần cài được chọn.'}
            self._start('rollback',work)
    def _on_verify_clicked(self):
        if self._valid_target():self._start('verify',lambda cb,op:self._engine().verify_installed(self.current_game_info.game_path,cb,op))
    def _on_launch_clicked(self):
        if not self._valid_target():return
        info=self.current_game_info
        def work(cb,op):
            ok,msg=GameDetector(self.path_manager.backup_root).launch(info)
            if not ok:raise RuntimeError(msg)
            return {'message':msg}
        self._start('launch',work)
    def _check_update(self):self._start('self_update',lambda cb,op:self.network_service.check_for_updates(LAUNCHER_VERSION))
    def _confirm_update(self,data):
        if not self._confirm('CẬP NHẬT LAUNCHER','Tải launcher '+data['latest_version']+' đã có SHA256 từ kênh cấu hình. Launcher hiện tại sẽ đóng sau khi chuẩn bị helper.','Tải và cập nhật'):return
        def work(cb,op):
            a=data['asset'];dest=self.path_manager.app_data_dir/'updates'/'StellaSora_Launcher.exe';self.network_service.download(data['download_url'],dest,a['size'],data['sha256'],cb,op);schedule_update(dest,data['sha256'],self.path_manager.app_data_dir);return {'message':'Đã chuẩn bị helper cập nhật.'}
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
        if dest=='notifications':self._show(NotificationsModal(self.notifications,self))
        elif dest=='guide':self._show(GuideModal(self))
        elif dest=='support':self._show(SupportModal(self.network_service.get_supporter_data(),self))
        elif dest=='settings':
            if self.active_worker:return
            d=SettingsModal(self.config_manager,self.network_service,self);d.game_path_changed.connect(lambda _:QTimer.singleShot(0,self._scan));self._show(d)
        elif dest=='tools':
            if self.active_worker:return
            d=AdvancedToolsModal(self.path_manager,self.current_game_info,self);self._show(d)
    def closeEvent(self,e):
        if self.active_worker is not None:
            self.overview_view.show_progress(True,'Đang có thao tác chạy. Hãy chờ thao tác hoàn tất trước khi đóng.',0);e.ignore();return
        e.accept()
    def _clamp_to_screen(self):
        if self.isMaximized() or self.isFullScreen():return
        area=self.screen().availableGeometry();width=min(self.width(),max(320,area.width()-16));height=min(self.height(),max(280,area.height()-16));x=max(area.left(),min(self.x(),area.right()-width+1));y=max(area.top(),min(self.y(),area.bottom()-height+1));self.setGeometry(x,y,width,height)
    def _screen_changed(self,*args):
        self.update();self.overview_view.update();self.overview_view.logo_label.update();self._clamp_to_screen()
    def showEvent(self,event):
        super().showEvent(event)
        if not getattr(self,'_screen_hooked',False) and self.windowHandle():self.windowHandle().screenChanged.connect(self._screen_changed);self._screen_hooked=True
    def event(self,event):
        result=super().event(event)
        if event.type()==getattr(QEvent.Type,'DevicePixelRatioChange',None):
            self.update()
            if hasattr(self,'overview_view'):self.overview_view.logo_label.update()
        return result
    def resizeEvent(self,e):super().resizeEvent(e)
    def paintEvent(self,e):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);master=AssetManager.get().get_background()
        if not master.isNull():
            # QPainter applies the paint-device DPR to this single master-to-device draw.
            # There is no logical-sized pixmap that the OS must enlarge again.
            scale=max(self.width()/master.width(),self.height()/master.height());sw=self.width()/scale;sh=self.height()/scale;source=QRectF((master.width()-sw)/2,(master.height()-sh)/2,sw,sh);painter.drawPixmap(QRectF(self.rect()),master,source)
        # Local bottom readability only; the main artwork is never blurred or fogged.
        gradient=QLinearGradient(0,self.height()*.86,0,self.height());gradient.setColorAt(0,QColor(3,15,30,0));gradient.setColorAt(1,QColor(3,15,30,65));painter.fillRect(QRectF(0,self.height()*.86,self.width(),self.height()*.14),gradient)
