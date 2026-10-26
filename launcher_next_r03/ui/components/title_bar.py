"""Compact draggable chrome; navigation is placed below the supplied logo."""
from PySide6.QtCore import Qt,Signal,QPoint
from PySide6.QtWidgets import QWidget,QHBoxLayout,QLabel,QPushButton
class TitleBar(QWidget):
    navigate_requested=Signal(str);minimize_requested=Signal();close_requested=Signal()
    def __init__(self,parent):
        super().__init__(parent);self.parent_window=parent;self._drag=None;self.setFixedHeight(42)
        l=QHBoxLayout(self);l.setContentsMargins(18,2,12,2)
        title=QLabel('STELLA SORA  ·  VIỆT HÓA');title.setStyleSheet('color:#a4c9e7;font-size:11px;letter-spacing:2px;');l.addWidget(title);l.addStretch()
        for text,tip,handler in [('⚙','Cài đặt',lambda:self.navigate_requested.emit('settings')),('—','Thu nhỏ',self.minimize_requested.emit),('✕','Đóng',self.close_requested.emit)]:
            b=QPushButton(text);b.setToolTip(tip);b.setAccessibleName(tip);b.setFixedSize(34,30);b.setStyleSheet('QPushButton{background:transparent;color:#f0f7ff;border:0;border-radius:5px;}QPushButton:hover{background:#174567;}QPushButton:focus{border:1px solid #62d4ff;}');b.clicked.connect(handler);l.addWidget(b)
    def set_active_tab(self,key):pass
    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton:self._drag=e.globalPosition().toPoint()-self.parent_window.pos()
    def mouseMoveEvent(self,e):
        if self._drag is not None and e.buttons()&Qt.MouseButton.LeftButton:self.parent_window.move(e.globalPosition().toPoint()-self._drag)
    def mouseReleaseEvent(self,e):self._drag=None
