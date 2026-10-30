"""Readonly path with middle elision, explicit auto-discovery and secondary context copy."""
from PySide6.QtCore import Qt,QRectF,QSize,Signal
from PySide6.QtGui import QPainter,QColor,QGuiApplication
from PySide6.QtWidgets import QWidget,QMenu
from ..assets import AssetManager
from ..typography import font
from .starlit_button import StarlitButton
class PathDisplay(QWidget):
    auto_detect_requested=Signal()
    def __init__(self,placeholder='Chọn thư mục game',parent=None):
        super().__init__(parent);self.full_path='';self.placeholder=placeholder;self.setMinimumHeight(40);self.setMinimumWidth(100);self.locate_button=StarlitButton('',variant='ghost',icon='search',parent=self);self.locate_button.setFixedSize(36,36);self.locate_button.setIconSize(QSize(24,24));self.locate_button.setAccessibleName('Tự tìm thư mục game');self.locate_button.setToolTip('Tự tìm thư mục game Steam / Yostar');self.locate_button.clicked.connect(self.auto_detect_requested.emit)
    def text(self):return self.full_path
    def setText(self,value):self.full_path=str(value);self.setToolTip(self.full_path);self.update()
    def set_busy(self,busy):self.locate_button.setEnabled(not busy)
    def _copy(self):
        if self.full_path:QGuiApplication.clipboard().setText(self.full_path)
    def sizeHint(self):return QSize(260,40)
    def resizeEvent(self,event):self.locate_button.move(max(0,self.width()-40),(self.height()-36)//2);super().resizeEvent(event)
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);assets=AssetManager.get();__import__('launcher.ui.journal_paint',fromlist=['field']).field(painter,QRectF(self.rect()));assets.paint(painter,'icons/folder_ink',QRectF(9,(self.height()-28)/2,28,28),'contain');painter.setFont(font(14));painter.setPen(QColor('#304679' if self.full_path else '#637596'));available=max(0,self.width()-88);value=painter.fontMetrics().elidedText(self.full_path or self.placeholder,Qt.TextElideMode.ElideMiddle,available);painter.drawText(QRectF(44,0,available,self.height()),Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft,value)
    def contextMenuEvent(self,event):
        menu=QMenu(self);action=menu.addAction('Sao chép đầy đủ đường dẫn');action.setEnabled(bool(self.full_path));action.triggered.connect(self._copy);menu.exec(event.globalPos())
