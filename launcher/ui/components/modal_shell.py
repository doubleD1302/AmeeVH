"""Shared decorated shell and a blurred snapshot of the actual parent scene."""
from PySide6.QtCore import Qt,QRectF,QSize,QTimer
from PySide6.QtGui import QPainter,QColor,QFont
from PySide6.QtWidgets import QDialog,QWidget,QVBoxLayout,QHBoxLayout,QGraphicsBlurEffect,QApplication,QLayout,QBoxLayout
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
        super().__init__(parent);self.panel=panel;self.panel_kind={'panels/guide':'guide','panels/support':'support','panels/update':'update','panels/confirm':'confirm','panels/dialog':'confirm'}.get(panel,'guide');self._large_panel_art=panel=='panels/modal' and width>=980 and height>=700;self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.Dialog);self.setWindowModality(Qt.WindowModality.WindowModal);self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True);self.setWindowTitle(title);self.resize(width,height)
        self.root=QVBoxLayout(self);self.root.setContentsMargins(52,64,52,64);self.root.setSpacing(12)
        header=QHBoxLayout();self.header=header;header.setSpacing(15)
        if icon and icon!='star_small':header.addWidget(AssetImage('icons/'+icon+'_white',32))
        text=QVBoxLayout();text.setSpacing(3);self.heading=text_label(title,27,bold=True,wrap=True);self.heading.setFont(ui_font(27,QFont.Weight.Bold));text.addWidget(self.heading);self.subtitle=text_label(subtitle,14,'#5f7094',wrap=True);text.addWidget(self.subtitle);header.addLayout(text,1);self.header_extra=QHBoxLayout();header.addLayout(self.header_extra)
        close=StarlitButton('',variant='ghost',icon='close');close.setFixedSize(36,36);close.setToolTip('Đóng');close.setAccessibleName('Đóng hộp thoại');close.clicked.connect(self.reject);header.addWidget(close,0,Qt.AlignmentFlag.AlignTop);self.root.addLayout(header);self.root.addWidget(ArtDivider())
        self.body_widget=QWidget();self.body_widget.setMinimumWidth(0);self.body=QVBoxLayout(self.body_widget);self.body.setContentsMargins(0,0,0,0);self.body.setSpacing(12);self.body_scroll=scroll_area(self.body_widget);self.root.addWidget(self.body_scroll,1);self.root.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.footer=QHBoxLayout();self.footer.setSpacing(12);self.root.addWidget(ArtDivider());self.root.addLayout(self.footer)
    def compact_layout(self,width):
        if width<900 and not getattr(self,'_compact',False):
            self._compact=True
            self.header.removeItem(self.header_extra);self.root.insertLayout(2,self.header_extra)
            f=self.heading.font();f.setPixelSize(23);self.heading.setFont(f)
        self._apply_panel_layout()
    def _apply_panel_layout(self):
        from ..panel_geometry import panel_content_rect
        import math
        safe=panel_content_rect(QRectF(self.rect()).adjusted(12,12,-12,-12),self.panel_kind)
        self.root.setContentsMargins(math.ceil(safe.left()),math.ceil(safe.top()),math.ceil(self.width()-safe.right()),math.ceil(self.height()-safe.bottom()))
        self.footer.setDirection(QBoxLayout.Direction.TopToBottom if safe.width()<440 else QBoxLayout.Direction.LeftToRight)
        callback=getattr(self,'_responsive_callback',None)
        if callback:callback(safe.width())
    def resizeEvent(self,e):
        self._apply_panel_layout();super().resizeEvent(e)
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
        from ..journal_paint import panel,panel_asset
        p=QPainter(self);r=QRectF(self.rect()).adjusted(12,12,-12,-12)
        if not panel_asset(p,r,self.panel_kind,modal=True):panel(p,r)
