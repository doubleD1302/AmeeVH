"""Queued operation controller; all resource mutation lives in manifest services."""
from __future__ import annotations
import json,logging,uuid
from pathlib import Path
from PySide6.QtCore import Qt,QThread,Signal,QTimer
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
logger=logging.getLogger('launcher.controller')
class AsyncOperationWorker(QThread):
    event_emitted=Signal(object);result_ready=Signal(str,bool,object)
    def __init__(self,op,target,parent=None):super().__init__(parent);self.op=op;self.target=target
    def run(self):
        try:self.result_ready.emit(self.op,True,self.target(self.event_emitted.emit,self.op))
        except Exception as e:logger.exception('Operation failed');self.result_ready.emit(self.op,False,{'message':str(e),'error_code':getattr(e,'code','OPERATION_ERROR')})
class MainWindow(QMainWindow):
    def __init__(self,path_manager,config_manager):
        super().__init__();self.path_manager=path_manager;self.config_manager=config_manager;self.active_worker=None;self.active_operation_id=None;self.operation_kind='';self.current_game_info=GameInfo();self.notifications=[];self._bg_cache=None
        c=config_manager;api=c.get('github_api_url') or f"https://api.github.com/repos/{c.get('github_repo')}/releases/latest";ann=c.get('custom_announcements_url') or c.get('remote_notifications_url')
        self.network_service=NetworkService(api,ann,path_manager.app_data_dir/'network_cache');self.setWindowTitle('Stella Sora Việt Hóa · Candidate r03');self.setWindowIcon(AssetManager.get().get_app_icon());self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.Window)
        area=QGuiApplication.primaryScreen().availableGeometry();self.setMinimumSize(min(480,area.width()),min(320,area.height()));self.resize(min(1280,area.width()-24),min(900,area.height()-24));self.move(area.center()-self.rect().center())
        central=QWidget();central.setObjectName('launcherRoot');central.setStyleSheet('#launcherRoot{background:transparent;}');self.setCentralWidget(central);l=QVBoxLayout(central);l.setContentsMargins(0,0,0,0);l.setSpacing(0)
        self.title_bar=TitleBar(self);self.title_bar.navigate_requested.connect(self._handle_navigation);self.title_bar.minimize_requested.connect(self.showMinimized);self.title_bar.close_requested.connect(self.close);l.addWidget(self.title_bar)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.Shape.NoFrame);scroll.setStyleSheet('QScrollArea{background:transparent;border:0;}QScrollArea>QWidget>QWidget{background:transparent;}');self.overview_view=OverviewView();self.overview_view.setMinimumHeight(650);scroll.setWidget(self.overview_view);l.addWidget(scroll,1)
        v=self.overview_view;v.install_requested.connect(self._on_install_clicked);v.rollback_requested.connect(self._on_rollback_clicked);v.verify_requested.connect(self._on_verify_clicked);v.browse_requested.connect(self._browse);v.launch_requested.connect(self._on_launch_clicked);v.navigate_requested.connect(self._handle_navigation);v.view_notifications_requested.connect(lambda:self._handle_navigation('notifications'))
        self.overview_view.update_game_status(self.current_game_info)
        QTimer.singleShot(0,self._initial_load)
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
        op=uuid.uuid4().hex;self.active_operation_id=op;self.operation_kind=kind;self.overview_view.set_busy(True);self.overview_view.show_progress(True,'Đang xử lý…',0)
        worker=AsyncOperationWorker(op,target,self);self.active_worker=worker;worker.event_emitted.connect(self._event);worker.result_ready.connect(self._finish);worker.finished.connect(lambda:self._release_worker(worker));worker.start();return True
    def _event(self,e):
        if e.operation_id==self.active_operation_id:self.overview_view.handle_operation_event(e)
    def _release_worker(self,w):
        if self.active_worker is w:self.active_worker=None;self.active_operation_id=None;self.overview_view.set_busy(False)
        w.deleteLater()
        if getattr(self,'_close_after_worker',False):self._close_after_worker=False;QTimer.singleShot(0,self.close)
    def _finish(self,op,success,result):
        if op!=self.active_operation_id:return
        if not success:
            msg=result.get('message','Lỗi chưa xác định');self.overview_view.show_progress(True,msg,0);self.overview_view.progress_bar.setRange(0,100)
            box=QMessageBox(self);box.setWindowTitle('Không thể hoàn tất thao tác');box.setIcon(QMessageBox.Icon.Warning);box.setText(msg);box.setDetailedText('Mã lỗi: '+result.get('error_code','')+'\nNhật ký: '+str(self.path_manager.logs_dir/'launcher.log'));box.setStandardButtons(QMessageBox.StandardButton.Ok);copy=box.addButton('Sao chép lỗi',QMessageBox.ButtonRole.ActionRole);copy.clicked.connect(lambda:QGuiApplication.clipboard().setText(msg+'\n'+str(self.path_manager.logs_dir/'launcher.log')));box.exec();return
        if isinstance(result,dict):
            if 'game' in result:self.current_game_info=result['game'];self.overview_view.update_game_status(self.current_game_info)
            if 'notifications' in result:
                self.notifications=result['notifications']
                if self.notifications:self.overview_view.update_notification(self.notifications[0])
                else:self.overview_view.notif_title.setText('Chưa có thông báo');self.overview_view.notif_summary.setText(self.network_service.notification_message)
            self.overview_view.connection_label.setText(self.network_service.notification_message)
            if self.operation_kind=='startup':
                warnings='\n'.join(self.config_manager.warnings)
                if warnings:self.overview_view.show_progress(True,warnings,0)
                else:self.overview_view.show_progress(False)
            elif self.operation_kind=='verify':self.overview_view.show_progress(True,'Đã đối chiếu SHA256 '+str(result.get('files'))+' tệp với biên bản '+str(result.get('version'))+'.',100)
            elif self.operation_kind=='launch':self.overview_view.show_progress(True,result.get('message','Đã gửi lệnh mở game.'),100)
            elif self.operation_kind=='self_update':
                data=result
                if not data.get('has_update') or not data.get('download_url'):QMessageBox.information(self,'Cập nhật launcher',data.get('message','Chưa có bản update xác minh.'))
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
        d=ConfirmationDialog(title,msg,label,parent=self);self._fit(d);return d.exec()==QDialog.DialogCode.Accepted
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
        area=self.screen().availableGeometry()
        if d.layout() is not None and (d.width()>area.width()-20 or d.height()>area.height()-20):
            item=d.layout().takeAt(0)
            if item and item.widget():
                content=item.widget();scroll=QScrollArea(d);scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.Shape.NoFrame);scroll.setWidget(content);d.layout().addWidget(scroll)
        d.setMinimumSize(0,0);d.resize(min(d.width(),area.width()-20),min(d.height(),area.height()-20));d.move(area.center()-d.rect().center())
    def _show(self,d):
        self._fit(d);focused=self.focusWidget();effect=QGraphicsBlurEffect();effect.setBlurRadius(5 if not self.config_manager.get('reduced_motion') else 0);self.overview_view.setGraphicsEffect(effect)
        try:d.exec()
        finally:self.overview_view.setGraphicsEffect(None)
        if focused:focused.setFocus()
    def _handle_navigation(self,dest):
        if dest=='overview':return
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
    def resizeEvent(self,e):self._bg_cache=None;super().resizeEvent(e)
    def paintEvent(self,e):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self._bg_cache is None:self._bg_cache=AssetManager.get().get_background().scaled(self.size(),Qt.AspectRatioMode.KeepAspectRatioByExpanding,Qt.TransformationMode.SmoothTransformation)
        b=self._bg_cache;painter.drawPixmap((self.width()-b.width())//2,(self.height()-b.height())//2,b)
        gradient=QLinearGradient(0,0,0,self.height());gradient.setColorAt(0,QColor(6,24,47,40));gradient.setColorAt(.45,QColor(6,24,47,0));gradient.setColorAt(1,QColor(6,24,47,150));painter.fillRect(self.rect(),gradient)
