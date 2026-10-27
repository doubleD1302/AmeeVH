"""Slim authored titlebar: brand, a tools/settings menu, minimize and close."""
from PySide6.QtCore import Qt,Signal,QRectF
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget,QHBoxLayout,QMenu
from .starlit_button import StarlitButton
from .art_controls import AssetImage,text_label
from ..assets import AssetManager
class TitleBar(QWidget):
    navigate_requested=Signal(str);minimize_requested=Signal();close_requested=Signal()
    def __init__(self,parent):
        super().__init__(parent);self.parent_window=parent;self._drag=None;self.setFixedHeight(42);l=QHBoxLayout(self);l.setContentsMargins(18,0,10,0);l.setSpacing(12);l.addWidget(AssetImage('decor/star_small',21));l.addWidget(text_label('Stella Sora  •  Việt hoá',15));l.addStretch()
        self.gear=StarlitButton('',variant='ghost',icon='settings');self.gear.setFixedSize(36,34);self.gear.setToolTip('Cài đặt và công cụ');self.gear.setAccessibleName('Cài đặt và công cụ');self.gear.clicked.connect(self._menu);l.addWidget(self.gear)
        for icon,tip,handler in [('minimize','Thu nhỏ',self.minimize_requested.emit),('close','Đóng launcher',self.close_requested.emit)]:
            b=StarlitButton('',variant='ghost',icon=icon);b.setFixedSize(36,34);b.setAccessibleName(tip);b.setToolTip(tip);b.clicked.connect(handler);l.addWidget(b)
    def _menu(self):
        m=QMenu(self);m.setToolTipsVisible(True);m.setStyleSheet('QMenu{background:#0b2d50;color:#eef7ff;border:1px solid #55bde9;padding:6px;}QMenu::item{padding:10px 22px;}QMenu::item:selected{background:#135884;}')
        for label,dest,icon in [('Cài đặt launcher','settings','settings'),('Kiểm tra cập nhật','check_update','download'),('Công cụ nâng cao / ADB','tools','shield'),('Thông báo','notifications','bell'),('Mở game','launch','play')]:
            a=m.addAction(AssetManager.get().get_icon(icon),label);a.triggered.connect(lambda checked=False,d=dest:self.navigate_requested.emit(d))
            if dest=='launch':
                info=self.parent_window.current_game_info;ready=bool(info.installed and not info.is_running and not self.parent_window.active_worker);a.setEnabled(ready);a.setToolTip('Mở game Stella Sora' if ready else 'Chọn đúng thư mục và đóng thao tác/game đang chạy trước.')
        m.exec(self.gear.mapToGlobal(self.gear.rect().bottomLeft()))
    def set_active_tab(self,key):pass
    def paintEvent(self,e):p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing,True);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,True);AssetManager.get().paint(p,'controls/titlebar',QRectF(self.rect()),'stretch')
    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton:self._drag=e.globalPosition().toPoint()-self.parent_window.pos()
    def mouseMoveEvent(self,e):
        if self._drag is not None and e.buttons()&Qt.MouseButton.LeftButton:self.parent_window.move(e.globalPosition().toPoint()-self._drag)
    def mouseReleaseEvent(self,e):self._drag=None
    def mouseDoubleClickEvent(self,e):self.parent_window.showNormal() if self.parent_window.isMaximized() else self.parent_window.showMaximized()
