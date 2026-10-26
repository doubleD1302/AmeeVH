"""Faithful art-first overview composition with widely separated typed cards."""
from PySide6.QtCore import Qt,Signal,QRectF
from PySide6.QtWidgets import QWidget,QLabel,QVBoxLayout,QHBoxLayout,QSizePolicy
from ..assets import AssetManager
from ..components.glass_card import GlassCard
from ..components.starlit_button import StarlitButton
from ..components.art_controls import AssetImage,ArtInput,ArtDivider,ArtProgress,Spinner,StatusPill,text_label
class OverviewView(QWidget):
    install_requested=Signal();rollback_requested=Signal();launch_requested=Signal();verify_requested=Signal();browse_requested=Signal();view_notifications_requested=Signal();navigate_requested=Signal(str);notification_selected=Signal(str)
    def __init__(self,parent=None):
        super().__init__(parent);self._busy=False;self._game=None;self.notifications=[]
        self.brand=QWidget(self);bl=QVBoxLayout(self.brand);bl.setContentsMargins(0,0,0,0);bl.setSpacing(2);self.logo_label=QLabel();self.logo_label.setPixmap(AssetManager.get().get_logo().scaled(300,120,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));bl.addWidget(self.logo_label);sub=text_label('D Ự  Á N  V I Ệ T  H O Á',11);bl.addWidget(sub);bl.addSpacing(12)
        nav=QHBoxLayout();nav.setSpacing(4);self.nav_buttons={}
        for title,dest in [('Tổng quan','overview'),('Hướng dẫn','guide'),('Ủng hộ','support')]:
            b=StarlitButton(title,variant='tab');b.setCheckable(True);b.setChecked(dest=='overview');b.setFixedSize(128,42);b.clicked.connect(lambda checked=False,d=dest:self._navigate(d));nav.addWidget(b);self.nav_buttons[dest]=b
        nav.addStretch();bl.addLayout(nav)
        self.connection_label=StatusPill(parent=self)
        self.card_notif=GlassCard(self,asset_id='panels/notification');nl=QVBoxLayout(self.card_notif);nl.setContentsMargins(36,28,36,30);nl.setSpacing(4)
        header=QHBoxLayout();header.setSpacing(9);header.addWidget(AssetImage('icons/bell_white',22));header.addWidget(text_label('Thông báo',17,bold=True));header.addStretch();allb=StarlitButton('Tất cả',variant='ghost',icon='external_link');allb.setFixedHeight(28);allb.setMinimumHeight(28);allb.clicked.connect(self.view_notifications_requested.emit);header.addWidget(allb);nl.addLayout(header);line=ArtDivider();line.setFixedHeight(8);nl.addWidget(line)
        self.notif_rows=[]
        for i in range(3):
            row=QWidget();rl=QHBoxLayout(row);rl.setContentsMargins(0,0,0,0);rl.setSpacing(7);dot=AssetImage('status/online' if i==0 else 'status/offline',13);rl.addWidget(dot);b=StarlitButton('Chưa có thông báo' if i==0 else '',variant='ghost',icon='chevron_right');b.setMinimumHeight(26);b.setFixedHeight(30);b.setFont(text_label('',12).font());b.clicked.connect(lambda checked=False,n=i:self._row_clicked(n));rl.addWidget(b,1);nl.addWidget(row);self.notif_rows.append((row,b))
        nl.addStretch();self.notif_title=self.notif_rows[0][1];self.notif_summary=text_label('',12);self.notif_summary.hide();self.notif_date=QLabel();self.notif_date.hide()
        self.card_action=GlassCard(self,asset_id='panels/install');al=QVBoxLayout(self.card_action);al.setContentsMargins(33,28,33,32);al.setSpacing(5)
        header=QHBoxLayout();header.setSpacing(8);header.addWidget(AssetImage('icons/download_white',23));header.addWidget(text_label('Bản Việt hoá',17,bold=True));header.addStretch();self.patch_status_badge=text_label('Chưa cài đặt',10,'#b0c9df');self.patch_status_badge.setMaximumWidth(110);self.patch_status_badge.setWordWrap(True);header.addWidget(self.patch_status_badge);al.addLayout(header);line=ArtDivider();line.setFixedHeight(7);al.addWidget(line)
        pathrow=QHBoxLayout();pathrow.setSpacing(4);self.path_display=ArtInput(placeholder='Chọn thư mục game',icon='folder');self.path_display.setReadOnly(True);self.path_display.setMinimumHeight(31);self.path_display.setFixedHeight(33);pathrow.addWidget(self.path_display,1);self.btn_browse=StarlitButton('…',variant='ghost');self.btn_browse.setFixedSize(27,29);self.btn_browse.setToolTip('Chọn thư mục game');self.btn_browse.clicked.connect(self.browse_requested.emit);pathrow.addWidget(self.btn_browse);al.addLayout(pathrow)
        row=QHBoxLayout();row.setSpacing(8);self.btn_install=StarlitButton('Cài Việt hoá',variant='primary',icon='download');self.btn_install.setFixedHeight(44);self.btn_install.clicked.connect(self.install_requested.emit);row.addWidget(self.btn_install,1);self.btn_launch=StarlitButton('',variant='square',icon='play');self.btn_launch.setFixedSize(44,44);self.btn_launch.setToolTip('Khởi chạy game');self.btn_launch.setAccessibleName('Khởi chạy game');self.btn_launch.clicked.connect(self.launch_requested.emit);row.addWidget(self.btn_launch);al.addLayout(row)
        row=QHBoxLayout();row.setSpacing(8);self.btn_verify=StarlitButton('Kiểm tra tệp',variant='ghost',icon='file_check');self.btn_verify.setFont(text_label('',12).font());self.btn_verify.setFixedHeight(30);self.btn_verify.clicked.connect(self.verify_requested.emit);row.addWidget(self.btn_verify,1);separator=text_label('│',14,'#5283a6');row.addWidget(separator);self.btn_rollback=StarlitButton('Khôi phục',variant='ghost',icon='restore');self.btn_rollback.setFont(text_label('',12).font());self.btn_rollback.setFixedHeight(30);self.btn_rollback.clicked.connect(self.rollback_requested.emit);row.addWidget(self.btn_rollback,1);al.addLayout(row)
        self.game_status_label=text_label('',10,'#9ec4df',wrap=True);self.game_status_label.setMaximumHeight(26);al.addWidget(self.game_status_label);self.game_status_label.hide()
        self.progress_container=QWidget();pl=QVBoxLayout(self.progress_container);pl.setContentsMargins(0,0,0,0);pl.setSpacing(3);row=QHBoxLayout();self.spinner=Spinner();row.addWidget(self.spinner);self.progress_label=text_label('',11,'#bce4fc',wrap=True);row.addWidget(self.progress_label,1);pl.addLayout(row);self.progress_bar=ArtProgress();pl.addWidget(self.progress_bar);al.addWidget(self.progress_container);self.progress_container.hide()
        self.footer=QWidget(self);fl=QHBoxLayout(self.footer);fl.setContentsMargins(0,0,0,0);fl.addWidget(text_label('Dự án Việt hoá   •   Phi thương mại',11));fl.addStretch();fl.addWidget(text_label('VI',11,bold=True));self._layout_geometry()
    def set_active_tab(self,destination):
        for key,button in self.nav_buttons.items():button.setChecked(key==destination)
    def _navigate(self,destination):self.set_active_tab(destination);self.navigate_requested.emit(destination)
    def _row_clicked(self,index):
        if index<len(self.notifications):self.notification_selected.emit(self.notifications[index].id)
        else:self.view_notifications_requested.emit()
    def set_notifications(self,items):
        self.notifications=list(items)
        for i,(row,b) in enumerate(self.notif_rows):
            b.setText(items[i].title if i<len(items) else ('Chưa có thông báo' if i==0 else ''));b.setEnabled(i<len(items));row.setVisible(i<len(items) or i==0)
    def update_notification(self,item):self.set_notifications([item])
    def _layout_geometry(self):
        w=self.width();h=self.height();compact=w<1000;minheight=920 if compact else 680
        if self.minimumHeight()!=minheight:self.setMinimumHeight(minheight)
        self.brand.setGeometry(46,22,min(440,w-70),190);self.connection_label.setGeometry(max(46,w-248),22,218,32)
        footer_y=h-43;self.footer.setGeometry(26,footer_y,max(100,w-52),28)
        ah=326 if self.progress_container.isVisible() else 262;nh=234
        if compact:
            cardwidth=max(340,w-50);self.card_notif.setGeometry(25,h-ah-nh-78,cardwidth,nh);self.card_action.setGeometry(25,h-ah-65,cardwidth,ah)
        else:
            left=min(466,round(w*.365));right=min(412,round(w*.315));top=h-max(nh,ah)-64;self.card_notif.setGeometry(25,top,left,nh);self.card_action.setGeometry(w-right-25,top,right,ah)
        for card,aid in [(self.card_notif,'panels/notification'),(self.card_action,'panels/install')]:
            if card.width()>0 and card.height()>0:card.layout().setContentsMargins(AssetManager.get().content_margins(aid,card.width(),card.height()))
    def resizeEvent(self,e):self._layout_geometry();super().resizeEvent(e)
    def update_game_status(self,info,is_patched=False):
        self._game=info;self.path_display.setText(str(info.game_path or ''));self.path_display.setToolTip(self.path_display.text());receipt=info.installed_receipt
        self.game_status_label.setText(('Steam' if info.platform=='steam' else 'Yostar')+' · '+info.version+' / '+info.resource_version if info.installed else 'Chọn đúng thư mục có StellaSora.exe')
        if info.is_running:self.game_status_label.setText('Game đang chạy hoặc chưa xác minh được tiến trình.')
        self.patch_status_badge.setText('Có biên bản '+str(receipt.get('version')) if receipt else 'Chưa cài đặt');self.patch_status_badge.setToolTip('Biên bản cần kiểm tra tệp để xác minh lại' if receipt else 'Chưa có biên bản của launcher này');self.btn_install.setText('Cập nhật Việt hoá' if receipt else 'Cài Việt hoá')
        if info.is_running:self.patch_status_badge.setText('Game đang chạy')
        self.path_display.setToolTip(self.path_display.text()+'\n'+self.game_status_label.text());self.set_busy(self._busy)
    def set_busy(self,busy,reduced_motion=None):
        if reduced_motion is not None:self._reduced_motion=reduced_motion
        self._busy=busy;g=self._game;idle=bool(g and g.installed and not g.is_running and not busy);self.btn_install.setEnabled(idle);self.btn_launch.setEnabled(idle);self.btn_browse.setEnabled(not busy)
        for b in (self.btn_verify,self.btn_rollback):b.setEnabled(idle and bool(g.installed_receipt))
        self.spinner.start(getattr(self,'_reduced_motion',False)) if busy else self.spinner.stop()
    def show_progress(self,show=True,label='',percent=0):self.progress_container.setVisible(show);self.progress_label.setText(label);self.progress_bar.setRange(0,100);self.progress_bar.setValue(percent);self._layout_geometry()
    def handle_operation_event(self,e):
        self.progress_container.show();self.progress_label.setText(e.message)
        if e.total>0:self.progress_bar.setRange(0,100);self.progress_bar.setValue(int(e.percentage))
        else:self.progress_bar.setRange(0,0)
        self._layout_geometry()
