"""Slim authored titlebar: brand + version, direct launch button, tools/settings menu, minimize and close."""
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QWidget, QHBoxLayout, QMenu, QSizePolicy
from .starlit_button import StarlitButton
from .art_controls import text_label
from ..assets import AssetManager
from ..typography import font as ui_font
from ...core.config import LAUNCHER_VERSION


class TitleBar(QWidget):
    navigate_requested = Signal(str)
    minimize_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self._drag = None
        self.setFixedHeight(54)
        l = QHBoxLayout(self)
        l.setContentsMargins(18, 0, 10, 0)
        l.setSpacing(10)
        l.addWidget(text_label(f'Stella Sora  •  Việt hoá  v{LAUNCHER_VERSION}', 15))
        l.addStretch()

        self.btn_play = StarlitButton('Vào game', variant='secondary', icon='play')
        self.btn_play.setFixedHeight(38)
        self.btn_play.setMinimumWidth(132)
        self.btn_play.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.btn_play.setIconSize(QSize(18, 18))
        self.btn_play.setFont(ui_font(14, QFont.Weight.DemiBold))
        self.btn_play.setToolTip('Hãy chọn thư mục có StellaSora.exe trước khi mở game.')
        self.btn_play.setAccessibleName('Vào game Stella Sora')
        self.btn_play.setEnabled(False)
        self.btn_play.clicked.connect(lambda: self.navigate_requested.emit('launch'))
        l.addWidget(self.btn_play)

        self.gear = StarlitButton('', variant='ghost', icon='settings')
        self.gear.setFixedSize(48, 46)
        self.gear.setIconSize(QSize(24, 24))
        self.gear.setToolTip('Cài đặt và công cụ')
        self.gear.setAccessibleName('Cài đặt và công cụ')
        self.gear.clicked.connect(self._menu)
        l.addWidget(self.gear)

        for icon, tip, handler in [
            ('minimize', 'Thu nhỏ', self.minimize_requested.emit),
            ('close', 'Đóng launcher', self.close_requested.emit),
        ]:
            b = StarlitButton('', variant='ghost', icon=icon)
            b.setFixedSize(48, 46)
            b.setIconSize(QSize(24, 24))
            b.setAccessibleName(tip)
            b.setToolTip(tip)
            b.clicked.connect(handler)
            l.addWidget(b)

    def update_game_state(self, info, busy: bool = False):
        ready = bool(info and info.installed and not info.is_running and not busy)
        self.btn_play.setEnabled(ready)
        if busy:
            self.btn_play.setText('Vào game')
            self.btn_play.setToolTip('Đang có thao tác chạy, vui lòng chờ hoàn tất.')
        elif info and info.is_running:
            self.btn_play.setText('Đang chạy')
            self.btn_play.setToolTip('Game Stella Sora hiện đang chạy.')
        elif info and info.installed:
            self.btn_play.setText('Vào game')
            self.btn_play.setToolTip('Mở game Stella Sora')
        else:
            self.btn_play.setText('Vào game')
            self.btn_play.setToolTip('Hãy chọn thư mục có StellaSora.exe trước khi mở game.')

    def _menu(self):
        m = QMenu(self)
        m.setToolTipsVisible(True)
        m.setStyleSheet(
            'QMenu{background:#fbf8ef;color:#273d6b;border:1px solid #c3b59a;padding:6px;}'
            'QMenu::item{padding:10px 22px;}'
            'QMenu::item:selected{background:#cbe9ed;}'
            'QMenu::item:disabled{color:#8c9ab3;}'
        )
        for label, dest, icon in [
            ('Cài đặt launcher', 'settings', 'settings'),
            ('Kiểm tra cập nhật', 'check_update', 'download'),
            ('Công cụ nâng cao / ADB', 'tools', 'shield'),
            ('Thông báo', 'notifications', 'bell'),
            ('Mở game', 'launch', 'play'),
        ]:
            a = m.addAction(AssetManager.get().get_icon(icon), label)
            a.triggered.connect(lambda checked=False, d=dest: self.navigate_requested.emit(d))
            if dest == 'launch':
                info = self.parent_window.current_game_info
                ready = bool(info.installed and not info.is_running and not self.parent_window.active_worker)
                a.setEnabled(ready)
                a.setToolTip('Mở game Stella Sora' if ready else 'Chọn đúng thư mục và đóng thao tác/game đang chạy trước.')
        m.exec(self.gear.mapToGlobal(self.gear.rect().bottomLeft()))

    def set_active_tab(self, key):
        pass

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#f7f5ec'))

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and not self.parent_window.isMaximized():
            self._drag = e.globalPosition().toPoint() - self.parent_window.pos()
        else:
            self._drag = None

    def mouseMoveEvent(self, e):
        if self.parent_window.isMaximized():
            self._drag = None
            return
        if self._drag is not None and e.buttons() & Qt.MouseButton.LeftButton:
            self.parent_window.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None

    def mouseDoubleClickEvent(self, e):
        self.parent_window.showNormal() if self.parent_window.isMaximized() else self.parent_window.showMaximized()
