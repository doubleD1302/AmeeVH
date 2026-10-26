"""Decorated settings sharing the same real paths/config contracts."""
from pathlib import Path
from PySide6.QtCore import Qt,Signal,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFileDialog,QMessageBox
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import ArtInput,ArtCheckBox,AlertStrip,ArtDivider,text_label,scroll_area
class SettingsModal(ArtDialog):
    game_path_changed=Signal(str)
    def __init__(self,config_manager,network_service,parent=None):
        super().__init__('Cài đặt launcher','Đường dẫn, gói bản dịch và tuỳ chọn của bạn.','settings',parent,width=980,height=750);self.config_manager=config_manager;self.network_service=network_service
        content=QWidget();body=QVBoxLayout(content);body.setContentsMargins(0,0,10,0);body.setSpacing(12)
        body.addWidget(text_label('Thư mục cài đặt game',17,bold=True));row=QHBoxLayout();self.path_input=ArtInput(config_manager.get('game_path',''),placeholder='Chọn thư mục có StellaSora.exe',icon='folder');self.path_input.textChanged.connect(self._validate);row.addWidget(self.path_input,1);b=StarlitButton('Chọn thư mục',variant='secondary',icon='folder');b.clicked.connect(self._browse_path);row.addWidget(b);body.addLayout(row);self.path_status_label=text_label('',12,'#a5cce9',wrap=True);body.addWidget(self.path_status_label)
        body.addWidget(text_label('Gói Việt hoá ngoại tuyến',17,bold=True));row=QHBoxLayout();self.payload_input=ArtInput(config_manager.get('payload_path',''),placeholder='Để trống để tải từ kênh đã cấu hình',icon='folder');row.addWidget(self.payload_input,1);b=StarlitButton('Chọn gói',variant='secondary',icon='folder');b.clicked.connect(self._browse_payload);row.addWidget(b);body.addLayout(row);body.addWidget(text_label('Gói ngoại tuyến cần patch_manifest.json và các tệp đúng SHA256/kích thước.',12,'#a6c9e8',wrap=True));body.addWidget(ArtDivider())
        self.chk_auto_detect=ArtCheckBox('Tự dò tìm game khi chưa chọn thư mục');self.chk_auto_detect.setChecked(config_manager.get('auto_detect_game',True));body.addWidget(self.chk_auto_detect)
        self.chk_update=ArtCheckBox('Kiểm tra cập nhật lúc mở — chỉ kiểm tra');self.chk_update.setChecked(config_manager.get('check_updates_on_start',True));body.addWidget(self.chk_update)
        self.chk_reduced_motion=ArtCheckBox('Giảm hiệu ứng chuyển động và làm mờ',toggle=True);self.chk_reduced_motion.setChecked(config_manager.get('reduced_motion',False));body.addWidget(self.chk_reduced_motion)
        b=StarlitButton('Kiểm tra cập nhật launcher',variant='secondary',icon='refresh');b.clicked.connect(self._check_update);body.addWidget(b,0,Qt.AlignmentFlag.AlignLeft);endpoint=text_label('Kênh: '+str(network_service.update_url),11,'#91bfdf',wrap=True);body.addWidget(endpoint)
        if getattr(config_manager,'_corrupt',False):
            for field in (self.path_input,self.payload_input,self.chk_auto_detect,self.chk_update,self.chk_reduced_motion):field.setEnabled(False)
        if config_manager.warnings:
            body.addWidget(AlertStrip('\n'.join(config_manager.warnings),'warning'))
            if getattr(config_manager,'_corrupt',False):
                b=StarlitButton('Giữ bản lỗi và phục hồi cấu hình',variant='danger',icon='restore');b.clicked.connect(self._recover_config);body.addWidget(b)
        body.addStretch();self.body.addWidget(scroll_area(content));self.footer.addWidget(text_label('Launcher 0.9.8 · giao diện r04',11,'#a6c9e8'));self.footer.addStretch();b=StarlitButton('Đóng',variant='secondary',icon='close');b.clicked.connect(self.reject);self.footer.addWidget(b);b=StarlitButton('Lưu cài đặt',variant='primary',icon='check');b.clicked.connect(self._save_settings);self.footer.addWidget(b);self._validate()
    def _validate(self,*args):
        p=Path(self.path_input.text());self.path_status_label.setText('Đã tìm thấy StellaSora.exe. Phiên bản được đối chiếu khi cài.' if (p/'StellaSora.exe').is_file() else 'Chọn đúng thư mục đang cài game có StellaSora.exe.')
    def _browse_path(self):
        s=QFileDialog.getExistingDirectory(self,'Chọn thư mục game',self.path_input.text() or 'C:/')
        if s:self.path_input.setText(s)
    def _browse_payload(self):
        s=QFileDialog.getExistingDirectory(self,'Chọn thư mục có patch_manifest.json',self.payload_input.text())
        if s:self.payload_input.setText(s)
    def _check_update(self):
        parent=self.parentWidget();self.accept()
        if parent and hasattr(parent,'_check_update'):QTimer.singleShot(0,parent._check_update)
    def _recover_config(self):
        ok=self.config_manager.preserve_corrupt_and_reset()
        if ok:
            for field in (self.path_input,self.payload_input,self.chk_auto_detect,self.chk_update,self.chk_reduced_motion):field.setEnabled(True)
        self.path_status_label.setText('Đã giữ bản lỗi và lưu cấu hình phục hồi.' if ok else '\n'.join(self.config_manager.warnings))
    def _save_settings(self):
        c=self.config_manager;c.update({'game_path':self.path_input.text().strip(),'payload_path':self.payload_input.text().strip(),'auto_detect_game':self.chk_auto_detect.isChecked(),'check_updates_on_start':self.chk_update.isChecked(),'reduced_motion':self.chk_reduced_motion.isChecked()})
        if not c.save():self.path_status_label.setText('\n'.join(c.warnings));return
        self.game_path_changed.emit(c.get('game_path'));self.accept()
