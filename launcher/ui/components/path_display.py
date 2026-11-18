"""Readonly path with middle elision, explicit auto-discovery and context Explorer/copy menu."""
import os
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QSize, Signal
from PySide6.QtGui import QPainter, QColor, QGuiApplication
from PySide6.QtWidgets import QWidget, QMenu
from ..assets import AssetManager
from ..typography import font
from .starlit_button import StarlitButton


class PathDisplay(QWidget):
    auto_detect_requested = Signal()

    def __init__(self, placeholder='Chọn thư mục game', parent=None):
        super().__init__(parent)
        self.full_path = ''
        self.placeholder = placeholder
        self.setMinimumHeight(54)
        self.setMinimumWidth(100)
        self.locate_button = StarlitButton('', variant='ghost', icon='search', parent=self)
        self.locate_button.setFixedSize(48, 48)
        self.locate_button.setIconSize(QSize(24, 24))
        self.locate_button.setAccessibleName('Tự tìm thư mục game')
        self.locate_button.setToolTip('Tự tìm thư mục game Steam / Yostar')
        self.locate_button.clicked.connect(self.auto_detect_requested.emit)

    def text(self):
        return self.full_path

    def setText(self, value):
        self.full_path = str(value)
        self.setToolTip(self.full_path)
        self.update()

    def set_busy(self, busy):
        self.locate_button.setEnabled(not busy)

    def _copy(self):
        if self.full_path:
            QGuiApplication.clipboard().setText(self.full_path)

    def _open_explorer(self):
        if not self.full_path:
            return
        p = Path(self.full_path)
        target = p if p.is_dir() else p.parent
        if target.is_dir() and hasattr(os, 'startfile'):
            try:
                os.startfile(str(target))
            except OSError:
                pass

    def sizeHint(self):
        return QSize(260, 40)

    def resizeEvent(self, event):
        self.locate_button.move(max(0, self.width() - 52), (self.height() - 48) // 2)
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        assets = AssetManager.get()
        __import__('launcher.ui.journal_paint', fromlist=['field']).field(painter, QRectF(self.rect()))
        assets.paint(painter, 'icons/folder_ink', QRectF(9, (self.height() - 42) / 2, 42, 42), 'contain')
        painter.setFont(font(14))
        painter.setPen(QColor('#304679' if self.full_path else '#637596'))
        available = max(0, self.width() - 120)
        value = painter.fontMetrics().elidedText(self.full_path or self.placeholder, Qt.TextElideMode.ElideMiddle, available)
        painter.drawText(QRectF(58, 0, available, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, value)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(
            'QMenu{background:#fbf8ef;color:#273d6b;border:1px solid #c3b59a;padding:6px;}'
            'QMenu::item{padding:8px 18px;}'
            'QMenu::item:selected{background:#cbe9ed;}'
            'QMenu::item:disabled{color:#8c9ab3;}'
        )
        open_act = menu.addAction('Mở thư mục trong Explorer')
        open_act.setEnabled(bool(self.full_path) and Path(self.full_path).exists())
        open_act.triggered.connect(self._open_explorer)
        copy_act = menu.addAction('Sao chép đầy đủ đường dẫn')
        copy_act.setEnabled(bool(self.full_path))
        copy_act.triggered.connect(self._copy)
        menu.exec(event.globalPos())
