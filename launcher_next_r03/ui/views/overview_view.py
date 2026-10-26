"""Overview using supplied art, editable controls and responsive lower cards."""
from PySide6.QtCore import Qt,Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QBoxLayout,QLabel,QLineEdit,QProgressBar,QSizePolicy
from ..assets import AssetManager
from ..components.glass_card import GlassCard
from ..components.starlit_button import StarlitButton
from ...core.types import OperationPhase
class OverviewView(QWidget):
    install_requested=Signal();rollback_requested=Signal();launch_requested=Signal();verify_requested=Signal();browse_requested=Signal();view_notifications_requested=Signal();navigate_requested=Signal(str)
    def __init__(self,parent=None):
        super().__init__(parent);self._busy=False;self._game=None
        root=QVBoxLayout(self);root.setContentsMargins(28,8,28,18);root.setSpacing(10)
        logo=QLabel();logo.setPixmap(AssetManager.get().get_logo().scaled(245,98,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));root.addWidget(logo,0,Qt.AlignmentFlag.AlignLeft)
        nav=QHBoxLayout();nav.setSpacing(2)
        for label,dest in [('Tổng quan','overview'),('Hướng dẫn','guide'),('Ủng hộ','support')]:
            b=StarlitButton(label,'tab');b.setMinimumHeight(44);b.clicked.connect(lambda checked=False,d=dest:self.navigate_requested.emit(d));nav.addWidget(b)
        nav.addStretch();root.addLayout(nav)
        self.connection_label=QLabel('Chưa kiểm tra kết nối');self.connection_label.setStyleSheet('color:#a4c9e7;font-size:11px');root.addWidget(self.connection_label)
        root.addStretch(1)
        self.bottom=QBoxLayout(QBoxLayout.Direction.LeftToRight);self.bottom.setSpacing(18)
        self.card_notif=GlassCard();nl=QVBoxLayout(self.card_notif);nl.setContentsMargins(30,28,30,30);nl.setSpacing(10)
        header=QHBoxLayout();h=QLabel('THÔNG BÁO');h.setStyleSheet('font-weight:bold;color:#62d4ff;letter-spacing:2px');header.addWidget(h);header.addStretch();allbtn=StarlitButton('Xem tất cả ›','ghost');allbtn.clicked.connect(self.view_notifications_requested.emit);header.addWidget(allbtn);nl.addLayout(header)
        self.notif_date=QLabel('');self.notif_date.setStyleSheet('color:#a4c9e7;font-size:11px');nl.addWidget(self.notif_date)
        self.notif_title=QLabel('Đang tải thông báo…');self.notif_title.setWordWrap(True);self.notif_title.setStyleSheet('font-weight:600;font-size:16px;color:#f0f7ff');nl.addWidget(self.notif_title)
        self.notif_summary=QLabel('');self.notif_summary.setWordWrap(True);self.notif_summary.setStyleSheet('font-size:12px;color:#a4c9e7');nl.addWidget(self.notif_summary);nl.addStretch();self.bottom.addWidget(self.card_notif,5)
        self.card_action=GlassCard();al=QVBoxLayout(self.card_action);al.setContentsMargins(30,28,30,30);al.setSpacing(10)
        title=QLabel('BẢN VIỆT HÓA');title.setStyleSheet('font-weight:bold;color:#62d4ff;letter-spacing:2px');al.addWidget(title)
        self.game_status_label=QLabel('Đang nhận diện game…');self.game_status_label.setWordWrap(True);al.addWidget(self.game_status_label)
        self.patch_status_badge=QLabel('Chưa xác minh bản đã cài');self.patch_status_badge.setWordWrap(True);self.patch_status_badge.setStyleSheet('color:#a4c9e7;font-size:12px');al.addWidget(self.patch_status_badge)
        pathrow=QHBoxLayout();self.path_display=QLineEdit();self.path_display.setReadOnly(True);self.path_display.setPlaceholderText('Chọn thư mục Stella Sora');pathrow.addWidget(self.path_display,1);self.btn_browse=StarlitButton('Chọn…','secondary');self.btn_browse.clicked.connect(self.browse_requested.emit);pathrow.addWidget(self.btn_browse);al.addLayout(pathrow)
        self.btn_install=StarlitButton('CÀI / CẬP NHẬT VIỆT HÓA','primary');self.btn_install.clicked.connect(self.install_requested.emit);al.addWidget(self.btn_install)
        actions=QHBoxLayout();self.btn_verify=StarlitButton('Kiểm tra tệp','secondary');self.btn_verify.clicked.connect(self.verify_requested.emit);actions.addWidget(self.btn_verify);self.btn_rollback=StarlitButton('Khôi phục','secondary');self.btn_rollback.clicked.connect(self.rollback_requested.emit);actions.addWidget(self.btn_rollback);self.btn_launch=StarlitButton('Mở game','secondary');self.btn_launch.clicked.connect(self.launch_requested.emit);actions.addWidget(self.btn_launch);al.addLayout(actions)
        self.progress_container=QWidget();pl=QVBoxLayout(self.progress_container);pl.setContentsMargins(0,0,0,0);self.progress_label=QLabel('');self.progress_label.setWordWrap(True);self.progress_label.setStyleSheet('font-size:11px;color:#a4c9e7');pl.addWidget(self.progress_label);self.progress_bar=QProgressBar();self.progress_bar.setMaximumHeight(9);self.progress_bar.setTextVisible(False);pl.addWidget(self.progress_bar);al.addWidget(self.progress_container);self.progress_container.hide()
        self.bottom.addWidget(self.card_action,6);root.addLayout(self.bottom)
        footer=QHBoxLayout();note=QLabel('Bản dịch cộng đồng · Phi thương mại · Launcher candidate r03');note.setStyleSheet('font-size:10px;color:#a4c9e7');note.setWordWrap(True);footer.addWidget(note);footer.addStretch();tools=StarlitButton('Công cụ nâng cao','ghost');tools.clicked.connect(lambda:self.navigate_requested.emit('tools'));footer.addWidget(tools);root.addLayout(footer)
    def resizeEvent(self,e):
        self.bottom.setDirection(QBoxLayout.Direction.TopToBottom if self.width()<930 else QBoxLayout.Direction.LeftToRight);super().resizeEvent(e)
    def update_notification(self,item):self.notif_title.setText(item.title);self.notif_date.setText(item.date);self.notif_summary.setText(item.summary)
    def update_game_status(self,game_info,is_patched=False):
        self._game=game_info;self.path_display.setText(str(game_info.game_path or ''));self.path_display.setToolTip(self.path_display.text())
        self.game_status_label.setText(('Steam' if game_info.platform=='steam' else 'Yostar')+f' · Game {game_info.version}' if game_info.installed else 'Chưa chọn đúng thư mục có StellaSora.exe')
        if game_info.is_running:self.game_status_label.setText('Game đang chạy hoặc chưa xác minh được tiến trình. Hãy đóng game.')
        r=game_info.installed_receipt
        self.patch_status_badge.setText(('Có biên bản '+str(r.get('version'))+' · Chưa kiểm tra lại tệp') if r else 'Chưa có biên bản cài đã xác minh của launcher này')
        self.set_busy(self._busy)
    def set_busy(self,busy):
        self._busy=busy;g=self._game;idle=bool(g and g.installed and not g.is_running and not busy)
        self.btn_install.setEnabled(idle);self.btn_launch.setEnabled(idle);self.btn_browse.setEnabled(not busy)
        for b in (self.btn_verify,self.btn_rollback):b.setEnabled(idle and bool(g.installed_receipt))
    def show_progress(self,show=True,label='',percent=0):
        self.progress_container.setVisible(show);self.progress_label.setText(label);self.progress_bar.setRange(0,100);self.progress_bar.setValue(percent)
    def handle_operation_event(self,e):
        self.progress_container.show();self.progress_label.setText(e.message)
        if e.total>0:self.progress_bar.setRange(0,100);self.progress_bar.setValue(int(e.percentage))
        else:self.progress_bar.setRange(0,0)
