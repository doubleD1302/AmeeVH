"""Persist game/payload paths and preferences; no automatic update application."""
from pathlib import Path
from PySide6.QtCore import Qt,Signal,QTimer
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QFileDialog,QCheckBox,QMessageBox,QScrollArea,QWidget
from ..components.glass_card import GlassCard
from ..components.starlit_button import StarlitButton
class SettingsModal(QDialog):
    game_path_changed=Signal(str)
    def __init__(self,config_manager,network_service,parent=None):
        super().__init__(parent);self.config_manager=config_manager;self.network_service=network_service;self.resize(780,640);self.setWindowTitle('Cài đặt launcher');self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.Dialog)
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0);card=GlassCard();l=QVBoxLayout(card);l.setContentsMargins(32,30,32,32);l.setSpacing(14);root.addWidget(card)
        top=QHBoxLayout();top.addWidget(QLabel('CÀI ĐẶT LAUNCHER'));top.addStretch();close=StarlitButton('✕','ghost');close.clicked.connect(self.reject);top.addWidget(close);l.addLayout(top)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.Shape.NoFrame);content=QWidget();body=QVBoxLayout(content);body.setContentsMargins(0,0,8,0);body.setSpacing(12)
        body.addWidget(QLabel('Thư mục cài đặt game'))
        row=QHBoxLayout();self.path_input=QLineEdit(config_manager.get('game_path',''));self.path_input.textChanged.connect(self._validate);row.addWidget(self.path_input);b=StarlitButton('Chọn…','secondary');b.clicked.connect(self._browse_path);row.addWidget(b);body.addLayout(row);self.path_status_label=QLabel();self.path_status_label.setWordWrap(True);body.addWidget(self.path_status_label)
        body.addWidget(QLabel('Gói Việt hóa ngoại tuyến (để trống để tải từ kênh đã cấu hình)'))
        row=QHBoxLayout();self.payload_input=QLineEdit(config_manager.get('payload_path',''));self.payload_input.setPlaceholderText('Thư mục chứa patch_manifest.json và payload có SHA256');row.addWidget(self.payload_input);b=StarlitButton('Chọn gói…','secondary');b.clicked.connect(self._browse_payload);row.addWidget(b);body.addLayout(row)
        self.chk_auto_detect=QCheckBox('Tự dò tìm thư mục game khi chưa chọn đường dẫn');self.chk_auto_detect.setChecked(config_manager.get('auto_detect_game',True));body.addWidget(self.chk_auto_detect)
        self.chk_update=QCheckBox('Kiểm tra cập nhật lúc mở (chỉ kiểm tra)');self.chk_update.setChecked(config_manager.get('check_updates_on_start',True));body.addWidget(self.chk_update)
        self.chk_reduced_motion=QCheckBox('Giảm hiệu ứng chuyển động và làm mờ');self.chk_reduced_motion.setChecked(config_manager.get('reduced_motion',False));body.addWidget(self.chk_reduced_motion)
        b=StarlitButton('Kiểm tra cập nhật launcher','secondary');b.clicked.connect(self._check_update);body.addWidget(b)
        endpoint=QLabel('Kênh: '+str(network_service.update_url));endpoint.setWordWrap(True);endpoint.setStyleSheet('font-size:11px;color:#a4c9e7');body.addWidget(endpoint)
        if config_manager.warnings:
            w=QLabel('\n'.join(config_manager.warnings));w.setWordWrap(True);w.setStyleSheet('color:#ffce79');body.addWidget(w)
            if getattr(config_manager,'_corrupt',False):
                r=StarlitButton('Giữ bản lỗi và phục hồi cấu hình','secondary');r.clicked.connect(self._recover_config);body.addWidget(r)
        body.addStretch();scroll.setWidget(content);l.addWidget(scroll,1)
        row=QHBoxLayout();row.addStretch();b=StarlitButton('Đóng','secondary');b.clicked.connect(self.reject);row.addWidget(b);b=StarlitButton('Lưu cài đặt','primary');b.clicked.connect(self._save_settings);row.addWidget(b);l.addLayout(row);self._validate()
    def _validate(self,*args):
        p=Path(self.path_input.text())
        self.path_status_label.setText('Đã tìm thấy StellaSora.exe. Phiên bản sẽ được đối chiếu khi cài.' if (p/'StellaSora.exe').is_file() else 'Hãy chọn đúng thư mục có StellaSora.exe.')
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
        if self.config_manager.preserve_corrupt_and_reset():QMessageBox.information(self,'Cấu hình','Đã giữ bản gốc bị lỗi và lưu cấu hình phục hồi.')
        else:QMessageBox.warning(self,'Chưa lưu','\n'.join(self.config_manager.warnings))
    def _save_settings(self):
        c=self.config_manager;c.update({'game_path':self.path_input.text().strip(),'payload_path':self.payload_input.text().strip(),'auto_detect_game':self.chk_auto_detect.isChecked(),'check_updates_on_start':self.chk_update.isChecked(),'reduced_motion':self.chk_reduced_motion.isChecked()})
        if not c.save():QMessageBox.warning(self,'Không lưu được','\n'.join(c.warnings));return
        self.game_path_changed.emit(c.get('game_path'));self.accept()
