"""A user-dismissable release notice; release notes are untrusted plain text."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPlainTextEdit
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import text_label

class UpdateNoticeDialog(ArtDialog):
    def __init__(self, version, notes, parent=None):
        super().__init__('Có phiên bản mới', 'Thông tin mới nhất từ GitHub', 'info', parent, width=740, height=560, panel='panels/dialog')
        title = text_label('Phiên bản ' + str(version), 20, '#eaf7ff', bold=True, wrap=True)
        self.body.addWidget(title)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText(notes.strip() or 'Bản phát hành chưa cung cấp mô tả thay đổi.')
        text.setStyleSheet('QPlainTextEdit{background:rgba(5,22,42,130);border:1px solid #326c94;color:#edf8ff;border-radius:8px;font-size:15px;padding:12px;}')
        self.body.addWidget(text, 1)
        self.footer.addStretch()
        snooze = StarlitButton('Tắt trong 24 giờ', variant='secondary')
        snooze.setMinimumWidth(0)
        snooze.clicked.connect(lambda: self.done(2))
        self.footer.addWidget(snooze, 1)
        close = StarlitButton('Đóng', variant='primary')
        close.setMinimumWidth(0)
        close.clicked.connect(self.accept)
        self.footer.addWidget(close, 1)
