"""Common art shell for honest information/error state and copyable diagnostics."""
import sys
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QPlainTextEdit
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import AlertStrip, ArtScrollBar, text_label


class MessageDialog(ArtDialog):
    def __init__(self, title, message, details='', parent=None, is_error=False, error_code=''):
        super().__init__(
            title,
            'Thông tin từ thao tác vừa thực hiện.',
            'warning' if is_error else 'info',
            parent,
            width=840,
            height=580 if details else 460,
            panel='panels/update',
        )
        self.message = message
        self.details = details
        self.error_code = str(error_code or '')
        self.root.setSpacing(8)
        self.body.addWidget(AlertStrip(message, 'error' if is_error else 'info'))
        if details:
            text = QPlainTextEdit(details)
            text.setReadOnly(True)
            text.setVerticalScrollBar(ArtScrollBar())
            text.setStyleSheet(
                'QPlainTextEdit{background:rgba(236,242,247,220);border:1px solid #c7bca8;color:#304679;border-radius:8px;font-size:15px;padding:10px;}'
            )
            self.body.addWidget(text, 1)
        else:
            self.body.addStretch(1)

        self.copied_label = text_label('', 13, '#1f6e58', bold=True)
        self.footer.addWidget(self.copied_label)
        self.footer.addStretch()

        if self.error_code == 'FILE_ACCESS_DENIED' and sys.platform == 'win32' and getattr(sys, 'frozen', False):
            admin_btn = StarlitButton('Chạy quyền Quản trị', variant='secondary', icon='shield')
            admin_btn.setMinimumWidth(210)
            admin_btn.clicked.connect(self._relaunch_as_admin)
            self.footer.addWidget(admin_btn)

        self.copy_btn = StarlitButton('Sao chép', variant='secondary', icon='copy')
        self.copy_btn.setMinimumWidth(140)
        self.copy_btn.clicked.connect(self._copy_to_clipboard)
        self.footer.addWidget(self.copy_btn)

        close = StarlitButton('Đóng', variant='primary')
        close.setMinimumWidth(120)
        close.clicked.connect(self.accept)
        self.footer.addWidget(close)

    def _copy_to_clipboard(self):
        payload = self.message if not self.details else (self.message + '\n' + self.details)
        QGuiApplication.clipboard().setText(payload)
        self.copied_label.setText('Đã sao chép ✓')
        QTimer.singleShot(2000, self._clear_copied_feedback)

    def _clear_copied_feedback(self):
        try:
            self.copied_label.setText('')
        except RuntimeError:
            pass

    def _relaunch_as_admin(self):
        try:
            import ctypes
            rc = ctypes.windll.shell32.ShellExecuteW(
                None, 'runas', sys.executable, None, str(Path(sys.executable).parent), 1
            )
            if rc > 32:
                self.accept()
                app = QApplication.instance()
                if app is not None:
                    app.quit()
        except Exception:
            pass
