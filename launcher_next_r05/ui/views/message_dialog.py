"""Common art shell for honest information/error state and copyable diagnostics."""
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QPlainTextEdit
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import AlertStrip,ArtScrollBar,text_label
class MessageDialog(ArtDialog):
    def __init__(self,title,message,details='',parent=None,is_error=False):
        super().__init__(title,'Thông tin từ thao tác vừa thực hiện.','warning' if is_error else 'info',parent,width=790,height=540,panel='panels/dialog');self.message=message;self.details=details;self.body.addWidget(AlertStrip(message,'error' if is_error else 'info'))
        if details:
            text=QPlainTextEdit(details);text.setReadOnly(True);text.setVerticalScrollBar(ArtScrollBar());text.setStyleSheet('QPlainTextEdit{background:rgba(5,22,42,110);border:1px solid #326c94;color:#cce8ff;border-radius:8px;font-size:14px;padding:10px;}');self.body.addWidget(text,1)
        self.footer.addStretch();copy=StarlitButton('Sao chép',variant='secondary',icon='copy');copy.clicked.connect(lambda:QGuiApplication.clipboard().setText(self.message+'\n'+self.details));self.footer.addWidget(copy);close=StarlitButton('Đóng',variant='primary');close.clicked.connect(self.accept);self.footer.addWidget(close)
