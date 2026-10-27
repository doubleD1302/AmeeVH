"""Shared decorated shell and a blurred snapshot of the actual parent scene."""
from PySide6.QtCore import Qt,QRectF,QSize
from PySide6.QtGui import QPainter,QColor,QFont
from PySide6.QtWidgets import QDialog,QWidget,QVBoxLayout,QHBoxLayout,QGraphicsBlurEffect,QApplication,QLayout
from ..assets import AssetManager
from ..typography import font as ui_font
from .starlit_button import StarlitButton
from .art_controls import AssetImage,ArtDivider,text_label,scroll_area
class ModalScrim(QWidget):
    def __init__(self,parent,reduced=False):
        image=parent.grab();super().__init__(parent);self.image=image;self.setGeometry(parent.rect());self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,False)
        if not reduced:blur=QGraphicsBlurEffect(self);blur.setBlurRadius(9);self.setGraphicsEffect(blur)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing,True);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,True);p.drawPixmap(self.rect(),self.image);AssetManager.get().paint(p,'controls/modal_scrim',QRectF(self.rect()),'stretch')
class ArtDialog(QDialog):
    def __init__(self,title,subtitle='',icon='star_small',parent=None,width=1160,height=780,panel='panels/modal'):
        super().__init__(parent);self.panel=panel;self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.Dialog);self.setWindowModality(Qt.WindowModality.WindowModal);self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True);self.setWindowTitle(title);self.resize(width,height)
        self.root=QVBoxLayout(self);self.root.setContentsMargins(48,42,48,64);self.root.setSpacing(12)
        header=QHBoxLayout();self.header=header;header.setSpacing(15)
        if icon:header.addWidget(AssetImage('icons/'+icon+'_white' if icon!='star_small' else 'decor/star_small',36))
        text=QVBoxLayout();text.setSpacing(3);self.heading=text_label(title,29,bold=True);self.heading.setFont(ui_font(29,QFont.Weight.Bold));text.addWidget(self.heading);self.subtitle=text_label(subtitle,14,'#a9cdea',wrap=True);text.addWidget(self.subtitle);header.addLayout(text,1);self.header_extra=QHBoxLayout();header.addLayout(self.header_extra)
        close=StarlitButton('',variant='ghost',icon='close');close.setFixedSize(36,36);close.setToolTip('Đóng');close.setAccessibleName('Đóng hộp thoại');close.clicked.connect(self.reject);header.addWidget(close,0,Qt.AlignmentFlag.AlignTop);self.root.addLayout(header);self.root.addWidget(ArtDivider())
        self.body_widget=QWidget();self.body_widget.setMinimumWidth(0);self.body=QVBoxLayout(self.body_widget);self.body.setContentsMargins(0,0,0,0);self.body.setSpacing(12);self.body_scroll=scroll_area(self.body_widget);self.root.addWidget(self.body_scroll,1);self.root.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.footer=QHBoxLayout();self.footer.setSpacing(12);self.root.addWidget(ArtDivider());self.root.addLayout(self.footer)
    def compact_layout(self,width):
        if width<900 and not getattr(self,'_compact',False):
            self._compact=True;self.root.setContentsMargins(28,30,28,60)
            self.header.removeItem(self.header_extra);self.header_extra.setParent(None);self.root.insertLayout(2,self.header_extra)
            f=self.heading.font();f.setPixelSize(23);self.heading.setFont(f)
    def _can_close(self):
        p=self.parentWidget()
        return not (p and getattr(p,'active_worker',None) and getattr(p,'operation_kind','') in ('install','rollback','recover','apply_self_update'))
    def reject(self):
        if self._can_close():super().reject()
        else:self.subtitle.setText('Thao tác đang ghi dữ liệu. Hãy chờ đến điểm hoàn tất an toàn.')
    def accept(self):
        if self._can_close():super().accept()
        else:self.subtitle.setText('Thao tác đang ghi dữ liệu. Hãy chờ đến điểm hoàn tất an toàn.')
    def closeEvent(self,e):
        if self._can_close():e.accept()
        else:e.ignore()
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing,True);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,True);p.setRenderHint(QPainter.RenderHint.TextAntialiasing,True);a=AssetManager.get();r=QRectF(self.rect()).adjusted(16,16,-16,-16);a.paint(p,self.panel,r)
        if a.meta(self.panel).get('avoid_r04_ornament_overlays'):return
        a.paint(p,'supplemental/decor/glass_luminance',r,'stretch')
        a.paint(p,'supplemental/decor/header_wash',QRectF(18,18,self.width()-36,116),'stretch')
        a.paint(p,'supplemental/decor/crown_top_left',QRectF(0,0,248,136),'contain')
        a.paint(p,'supplemental/decor/header_trail_right',QRectF(self.width()-322,18,300,114),'contain')
        a.paint(p,'supplemental/decor/petal_sweep_left',QRectF(18,self.height()-196,280,175),'contain')
        a.paint(p,'supplemental/decor/petal_sweep_right',QRectF(self.width()-360,self.height()-234,340,212),'contain')
