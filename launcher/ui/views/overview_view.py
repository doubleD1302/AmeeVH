"""Faithful art-first overview composition with widely separated typed cards."""
from PySide6.QtCore import Qt,Signal,QRectF
from PySide6.QtWidgets import QWidget,QLabel,QVBoxLayout,QHBoxLayout,QSizePolicy,QGraphicsDropShadowEffect
from ..assets import AssetManager
from ..components.glass_card import GlassCard
from ..components.starlit_button import StarlitButton
from ..components.branding_mark import BrandingMark
from ..components.path_display import PathDisplay
from ..typography import font as ui_font
from PySide6.QtGui import QFont,QColor
from ..components.art_controls import AssetImage,ArtInput,ArtDivider,ArtProgress,Spinner,StatusPill,text_label
class OverviewView(QWidget):
    auto_detect_requested=Signal();install_requested=Signal();rollback_requested=Signal();launch_requested=Signal();verify_requested=Signal();browse_requested=Signal();view_notifications_requested=Signal();navigate_requested=Signal(str);notification_selected=Signal(str);check_translation_requested=Signal()
    def __init__(self,parent=None):
        super().__init__(parent);self._busy=False;self._game=None;self._install_allowed=False;self.notifications=[]
        self.flag_mark=BrandingMark(self)
        self.nav_widget=QWidget(self);nav=QHBoxLayout(self.nav_widget);nav.setContentsMargins(0,0,0,0);nav.setSpacing(4);self.nav_buttons={}
        for title,dest in [('Tổng quan','overview'),('Hướng dẫn','guide'),('Ủng hộ','support')]:
            b=StarlitButton(title,variant='tab');b.setCheckable(True);b.setChecked(dest=='overview');b.setFixedHeight(46);b.setMinimumWidth(0);b.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed);b.stretch_background=True;b.caption_wrap=True;b.setFont(ui_font(15,QFont.Weight.DemiBold));b.clicked.connect(lambda checked=False,d=dest:self._navigate(d));nav.addWidget(b,1);self.nav_buttons[dest]=b
        # Retain the status API for the controller without showing text or dot.
        self.connection_label=StatusPill(parent=self);self.connection_label.hide()
        self.card_notif=GlassCard(self,asset_id='panels/notification');nl=QVBoxLayout(self.card_notif);nl.setContentsMargins(36,28,36,30);nl.setSpacing(4)
        header=QHBoxLayout();header.setSpacing(9);header.addWidget(AssetImage('icons/bell_white',24));header.addWidget(text_label('Thông báo',17,bold=True));header.addStretch();allb=StarlitButton('Tất cả',variant='ghost',icon='external_link');allb.icon_side='right';allb.setFont(ui_font(13));allb.setFixedHeight(32);allb.setMinimumHeight(32);allb.clicked.connect(self.view_notifications_requested.emit);header.addWidget(allb);nl.addLayout(header);line=ArtDivider();line.setFixedHeight(8);nl.addWidget(line)
        self.notif_rows=[]
        for i in range(3):
            row=QWidget();rl=QHBoxLayout(row);rl.setContentsMargins(0,0,0,0);rl.setSpacing(7);dot=AssetImage('status/online' if i==0 else 'status/offline',13);rl.addWidget(dot);b=StarlitButton('Chưa có thông báo' if i==0 else '',variant='ghost',icon='chevron_right');b.setMinimumHeight(36);b.setFixedHeight(36);b.setFont(ui_font(15));b.icon_side='far_right';b.text_alignment='left';b.clicked.connect(lambda checked=False,n=i:self._row_clicked(n));rl.addWidget(b,1);nl.addWidget(row);self.notif_rows.append((row,b))
        nl.addStretch();self.notif_title=self.notif_rows[0][1];self.notif_summary=text_label('',12);self.notif_summary.hide();self.notif_date=QLabel();self.notif_date.hide()
        self.card_action=GlassCard(self,asset_id='panels/install');al=QVBoxLayout(self.card_action);al.setContentsMargins(33,28,33,32);al.setSpacing(5)
        self.patch_status_badge=text_label('Chưa cài đặt',13,'#b2cde3');self.patch_status_badge.setWordWrap(False);self.patch_status_badge.setAlignment(Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignCenter)
        pathrow=QHBoxLayout();pathrow.setSpacing(4);self.path_display=PathDisplay();self.path_display.auto_detect_requested.connect(self.auto_detect_requested.emit);self.path_display.setFixedHeight(40);pathrow.addWidget(self.path_display,1);self.btn_browse=StarlitButton('…',variant='ghost');self.btn_browse.setFixedSize(27,29);self.btn_browse.setToolTip('Chọn thư mục game');self.btn_browse.clicked.connect(self.browse_requested.emit);pathrow.addWidget(self.btn_browse);al.addLayout(pathrow)
        row=QHBoxLayout();row.setSpacing(8);self.btn_install=StarlitButton('Cài Việt hoá',variant='primary',icon='download');self.btn_install.setFixedHeight(48);self.btn_install.clicked.connect(self.install_requested.emit);row.addWidget(self.btn_install,1);self.btn_folder=StarlitButton('',variant='square',icon='folder');self.btn_folder.setFixedSize(48,48);self.btn_folder.setToolTip('Chọn thư mục game');self.btn_folder.setAccessibleName('Chọn thư mục game');self.btn_folder.clicked.connect(self.browse_requested.emit);row.addWidget(self.btn_folder);al.addLayout(row)
        self.btn_check_translation=StarlitButton('Kiểm tra phiên bản Việt hoá',variant='secondary');self.btn_check_translation.setFont(ui_font(14,QFont.Weight.DemiBold));self.btn_check_translation.setFixedHeight(42);self.btn_check_translation.setToolTip('Kiểm tra bản Việt hoá trên GitHub');self.btn_check_translation.clicked.connect(self.check_translation_requested.emit);al.addWidget(self.btn_check_translation)
        row=QHBoxLayout();row.setSpacing(8);self.btn_verify=StarlitButton('Kiểm tra tệp',variant='ghost',icon='file_check');self.btn_verify.setFont(ui_font(15));self.btn_verify.setFixedHeight(38);self.btn_verify.clicked.connect(self.verify_requested.emit);row.addWidget(self.btn_verify,1);separator=text_label('│',14,'#5283a6');row.addWidget(separator);self.btn_rollback=StarlitButton('Khôi phục',variant='ghost',icon='restore');self.btn_rollback.setFont(ui_font(15));self.btn_rollback.setFixedHeight(38);self.btn_rollback.clicked.connect(self.rollback_requested.emit);row.addWidget(self.btn_rollback,1);al.addLayout(row);al.addWidget(self.patch_status_badge)
        self.game_status_label=text_label('',10,'#9ec4df',wrap=True);self.game_status_label.setMaximumHeight(26);al.addWidget(self.game_status_label);self.game_status_label.hide()
        self.progress_container=QWidget();self.progress_container.setMaximumHeight(55);pl=QVBoxLayout(self.progress_container);pl.setContentsMargins(0,0,0,0);pl.setSpacing(3);row=QHBoxLayout();self.spinner=Spinner();row.addWidget(self.spinner);self.progress_label=text_label('',11,'#bce4fc',wrap=True);self.progress_label.setMaximumHeight(38);row.addWidget(self.progress_label,1);pl.addLayout(row);self.progress_bar=ArtProgress();pl.addWidget(self.progress_bar);al.addWidget(self.progress_container);self.progress_container.hide()
        self.footer=QWidget(self);fl=QHBoxLayout(self.footer);fl.setContentsMargins(0,0,0,0);fl.addWidget(text_label('Phi thương mại',11));fl.addStretch();fl.addWidget(text_label('VI',11,bold=True));self._layout_geometry()
    def set_active_tab(self,destination):
        for key,button in self.nav_buttons.items():button.setChecked(key==destination)
    def _navigate(self,destination):self.set_active_tab(destination);self.navigate_requested.emit(destination)
    def _row_clicked(self,index):
        if index<len(self.notifications):self.notification_selected.emit(self.notifications[index].id)
        else:self.view_notifications_requested.emit()
    def set_notifications(self,items):
        self.notifications=list(items)
        for i,(row,b) in enumerate(self.notif_rows):
            b.setText(items[i].title if i<len(items) else ('Chưa có thông báo' if i==0 else ''));b.setToolTip(items[i].title if i<len(items) else 'Hiện chưa có dữ liệu thông báo.');b.setEnabled(i<len(items));row.setVisible(i<len(items) or i==0)
    def update_notification(self,item):self.set_notifications([item])
    def _layout_geometry(self):
        w=self.width();h=self.height();compact=w<1000
        cardheight=355 if self.progress_container.isVisible() else 295
        brandmargin=25 if compact else 46
        previous_marksize=min(310,max(120,(w-2*brandmargin-28)//2))
        marksize=int(previous_marksize*0.75+0.5)
        # Reserve the smaller flag and the nav row above the cards, including
        # stacked cards when the viewport is narrow. The outer view can scroll.
        flagbottom=18+marksize
        minheight=max(920,flagbottom+144+2*cardheight) if compact else max(680,flagbottom+26+cardheight+66)
        if self.minimumHeight()!=minheight:self.setMinimumHeight(minheight)
        h=max(h,minheight)
        self.flag_mark.setGeometry(brandmargin,18,marksize,marksize)
        footer_y=h-43;self.footer.setGeometry(26,footer_y,max(100,w-52),28)
        width=min(466,max(400,round(w*.355)))
        cardwidth=max(340,w-50) if compact else width
        if compact:
            self.card_notif.setGeometry(25,h-cardheight*2-80,cardwidth,cardheight)
            self.card_action.setGeometry(25,h-cardheight-66,cardwidth,cardheight)
        else:
            top=h-cardheight-66
            self.card_notif.setGeometry(25,top,width,cardheight)
            self.card_action.setGeometry(w-width-25,top,width,cardheight)
        self.nav_widget.setGeometry(self.card_notif.x(),self.card_notif.y()-56,self.card_notif.width(),46)
        for card,aid in [(self.card_notif,'panels/notification'),(self.card_action,'panels/install')]:
            if card.width()>0 and card.height()>0:card.layout().setContentsMargins(AssetManager.get().content_margins(aid,card.width(),card.height()))
    def _safe_card_height(self,asset_id,width,body_height,minimum):
        m=AssetManager.get().meta(asset_id);box=m['content_rect'];s=min(1,width/m['width']);return max(minimum,round(body_height+(box[1]+m['height']-box[1]-box[3])*s))
    def resizeEvent(self,e):self._layout_geometry();super().resizeEvent(e)
    def update_game_status(self,info,is_patched=False):
        self._game=info;self.path_display.setText(str(info.game_path or ''));self.path_display.setToolTip(self.path_display.text());receipt=info.installed_receipt
        self.game_status_label.setText(('Steam' if info.platform=='steam' else 'Yostar')+' · '+info.version+' / '+info.resource_version if info.installed else 'Chọn đúng thư mục có StellaSora.exe')
        if info.is_running:self.game_status_label.setText('Game đang chạy hoặc chưa xác minh được tiến trình.')
        self.patch_status_badge.setText('Đã cài Việt hoá' if receipt else 'Chưa cài đặt');self.patch_status_badge.setToolTip(f"Bản Việt hoá v{receipt.get('version', '')} ({receipt.get('files_count', '')} tệp)" if receipt else 'Chưa có bản cài đặt của launcher này');self.set_translation_update(False)
        if info.is_running:self.patch_status_badge.setText('Game đang chạy')
        self.path_display.setToolTip(self.path_display.text()+'\n'+self.game_status_label.text());self.set_busy(self._busy)
    def set_busy(self,busy,reduced_motion=None):
        if reduced_motion is not None:self._reduced_motion=reduced_motion
        self._busy=busy;self.path_display.set_busy(busy);g=self._game;idle=bool(g and g.installed and not g.is_running and not busy);self.btn_install.setEnabled(idle and self._install_allowed);self.btn_folder.setEnabled(not busy);self.btn_browse.setEnabled(not busy);self.btn_check_translation.setEnabled(not busy)
        reason='Đang có thao tác, hãy chờ hoàn tất.' if busy else ('Hãy chọn đúng thư mục game.' if not g or not g.installed else ('Hãy đóng game trước.' if g.is_running else ('Chưa cài bản Việt hoá bằng launcher này.' if not g.installed_receipt else '')))
        for b in (self.btn_verify,self.btn_rollback):b.setEnabled(not busy);b.setToolTip(reason or ('Đối chiếu SHA256 với biên bản đã cài.' if b is self.btn_verify else 'Khôi phục từ backup gắn với thư mục này.'))
        self.spinner.start(getattr(self,'_reduced_motion',False)) if busy else self.spinner.stop()
    def set_translation_update(self,available):
        if available:
            self.btn_install.setText('Cập nhật Việt hoá')
        elif getattr(self, '_game', None) and getattr(self._game, 'installed_receipt', None):
            self.btn_install.setText('Cài lại Việt hoá')
        else:
            self.btn_install.setText('Cài Việt hoá')
        self.btn_install.setAccessibleName(self.btn_install.text())
    def set_install_allowed(self,allowed,reason=''):
        self._install_allowed=bool(allowed);self.btn_install.setToolTip(reason);self.set_busy(self._busy)
    def show_progress(self,show=True,label='',percent=0):
        self.progress_container.setVisible(show);self.spinner.setVisible(show);self.progress_bar.setVisible(show);self.progress_label.setText(label)
        if show:self.progress_bar.setRange(0,100);self.progress_bar.setValue(percent)
        self._layout_geometry()
    def show_completed(self,message):
        self.progress_container.setVisible(True);self.spinner.stop();self.spinner.setVisible(False);self.progress_bar.setVisible(False);self.progress_label.setText(message);self._layout_geometry()
    def handle_operation_event(self,e):
        self.progress_container.show();self.spinner.show();self.progress_bar.show();self.progress_label.setText(e.message)
        if e.total>0:self.progress_bar.setRange(0,100);self.progress_bar.setValue(int(e.percentage))
        else:self.progress_bar.setRange(0,0)
        self._layout_geometry()
