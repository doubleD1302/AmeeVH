"""Explicit root choice when discovery finds more than one installation."""
from PySide6.QtWidgets import QWidget,QVBoxLayout
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import text_label,scroll_area
class GameSelectionDialog(ArtDialog):
    def __init__(self,installations,parent=None):
        super().__init__('Chọn bản game đang dùng','Máy có nhiều bản cài. Chọn đúng Steam hoặc Yostar bạn mở để chơi.','folder',parent,width=900,height=620);self.selected_path=None
        content=QWidget();layout=QVBoxLayout(content);layout.setSpacing(12)
        for entry in installations:
            platform='Steam' if entry.get('platform')=='steam' else 'Yostar';path=str(entry['path']);canonical=str(entry.get('canonical') or path)
            button=StarlitButton(platform+'\n'+canonical,variant='secondary',icon='folder');button.caption_wrap=True;button.stretch_background=True;button.setMinimumHeight(94);button.setToolTip(canonical);button.clicked.connect(lambda checked=False,p=path:self._select(p));layout.addWidget(button)
        layout.addStretch();self.body.addWidget(scroll_area(content),1);self.footer.addWidget(text_label('Mỗi bản cài có thư mục và bản sao lưu riêng.',13,wrap=True),1);close=StarlitButton('Để sau',variant='secondary');close.clicked.connect(self.reject);self.footer.addWidget(close)
    def _select(self,path):self.selected_path=path;self.accept()
