"""Readonly full path with middle elision, full tooltip and explicit copy action."""
from PySide6.QtCore import Qt,QRectF,QSize
from PySide6.QtGui import QPainter,QColor,QGuiApplication
from PySide6.QtWidgets import QWidget,QMenu
from ..assets import AssetManager
from ..typography import font
from .starlit_button import StarlitButton
class PathDisplay(QWidget):
    def __init__(self,placeholder='Chọn thư mục game',parent=None):
        super().__init__(parent);self.full_path='';self.placeholder=placeholder;self.setMinimumHeight(40);self.setMinimumWidth(100);self.copy_button=StarlitButton('',variant='ghost',icon='copy',parent=self);self.copy_button.setFixedSize(30,30);self.copy_button.setIconSize(QSize(20,20));self.copy_button.setAccessibleName('Sao chép đầy đủ đường dẫn game');self.copy_button.setToolTip('Sao chép đầy đủ đường dẫn game');self.copy_button.clicked.connect(self._copy);self.copy_button.setEnabled(False)
    def text(self):return self.full_path
    def setText(self,value):self.full_path=str(value);self.setToolTip(self.full_path);self.copy_button.setEnabled(bool(self.full_path));self.update()
    def _copy(self):
        if self.full_path:QGuiApplication.clipboard().setText(self.full_path)
    def sizeHint(self):return QSize(260,40)
    def resizeEvent(self,event):self.copy_button.move(self.width()-35,(self.height()-30)//2);super().resizeEvent(event)
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);assets=AssetManager.get();assets.paint(painter,'controls/input_normal',QRectF(self.rect()));assets.paint(painter,'icons/folder_white',QRectF(11,(self.height()-24)/2,24,24),'contain');painter.setFont(font(14));painter.setPen(QColor('#edf7ff' if self.full_path else '#b2cde3'));available=max(0,self.width()-82);value=painter.fontMetrics().elidedText(self.full_path or self.placeholder,Qt.TextElideMode.ElideMiddle,available);painter.drawText(QRectF(44,0,available,self.height()),Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft,value)
    def contextMenuEvent(self,event):
        menu=QMenu(self);action=menu.addAction('Sao chép đầy đủ đường dẫn');action.setEnabled(bool(self.full_path));action.triggered.connect(self._copy);menu.exec(event.globalPos())
