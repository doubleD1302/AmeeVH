"""Affecting-action confirmation in the supplied dialog art shell."""
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import AlertStrip,text_label
class ConfirmationDialog(ArtDialog):
    def __init__(self,title,message,confirm_label='Xác nhận',cancel_label='Hủy bỏ',is_danger=False,parent=None):
        super().__init__(title,'Hãy kiểm tra thư mục và phạm vi trước khi tiếp tục.','warning' if is_danger else 'info',parent,width=700,height=440,panel='panels/dialog');self.heading.setStyleSheet('color:#ffccdf;' if is_danger else 'color:#eef7ff;');self.body.addWidget(text_label(message,14,wrap=True));self.body.addStretch();self.body.addWidget(AlertStrip('Dữ liệu chỉ được thay đổi sau khi bạn xác nhận.','warning' if is_danger else 'info'));self.footer.addStretch();cancel=StarlitButton(cancel_label,variant='secondary',icon='close');cancel.clicked.connect(self.reject);self.footer.addWidget(cancel);confirm=StarlitButton(confirm_label,variant='danger' if is_danger else 'primary',icon='check');confirm.clicked.connect(self.accept);self.footer.addWidget(confirm)
