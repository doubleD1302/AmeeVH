"""Local preferences and explicit read-only GitHub channel synchronization."""
from pathlib import Path
from PySide6.QtCore import Qt,Signal,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFileDialog
from ...core.config import LAUNCHER_VERSION
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import ArtInput,ArtCheckBox,AlertStrip,ArtDivider,text_label,scroll_area
class SettingsModal(ArtDialog):
    game_path_changed=Signal(str);github_sync_requested=Signal();channel_changed=Signal()
    def __init__(self,config_manager,network_service,parent=None):
        super().__init__('Cài đặt launcher','Đường dẫn, kênh GitHub và tuỳ chọn của bạn.','settings',parent,width=980,height=800);self.config_manager=config_manager;self.network_service=network_service
        content=QWidget();body=QVBoxLayout(content);body.setContentsMargins(0,0,10,0);body.setSpacing(12)
        body.addWidget(text_label('Thư mục cài đặt game',20,bold=True));row=QHBoxLayout();self.path_input=ArtInput(config_manager.get('game_path',''),placeholder='Chọn thư mục có StellaSora.exe',icon='folder');self.path_input.textChanged.connect(self._validate);row.addWidget(self.path_input,1);button=self._button('Chọn thư mục','folder',190);button.clicked.connect(self._browse_path);row.addWidget(button);body.addLayout(row);self.path_status_label=text_label('',13,'#a5cce9',wrap=True);body.addWidget(self.path_status_label)
        body.addWidget(text_label('Gói Việt hoá ngoại tuyến',20,bold=True));row=QHBoxLayout();self.payload_input=ArtInput(config_manager.get('payload_path',''),placeholder='Để trống để tải bản dịch từ GitHub',icon='folder');row.addWidget(self.payload_input,1);button=self._button('Chọn gói','folder',160);button.clicked.connect(self._browse_payload);row.addWidget(button);body.addLayout(row);body.addWidget(text_label('Chọn thư mục gói đầy đủ có patch_manifest.json. Launcher vẫn kiểm tra các tệp trước khi cài.',13,'#a6c9e8',wrap=True));body.addWidget(ArtDivider())
        body.addWidget(text_label('Kênh GitHub',20,bold=True));row=QHBoxLayout();self.repo_input=ArtInput(str(config_manager.get('github_repo') or ''),placeholder='tài-khoản/tên-kho',icon='globe');row.addWidget(self.repo_input,3);self.branch_input=ArtInput(str(config_manager.get('github_branch') or ''),placeholder='Nhánh',icon='folder');row.addWidget(self.branch_input,1);body.addLayout(row)
        row=QHBoxLayout();self.sync_button=self._button('Đồng bộ GitHub','refresh',230);self.sync_button.clicked.connect(self._request_sync);row.addWidget(self.sync_button);update=self._button('Kiểm tra cập nhật launcher','download',310);update.clicked.connect(self._check_update);row.addWidget(update);row.addStretch();body.addLayout(row)
        self.sync_status_label=text_label('',14,'#bce4fc',wrap=True);body.addWidget(self.sync_status_label);self.endpoint_label=text_label('',13,'#91bfdf',wrap=True);body.addWidget(self.endpoint_label);body.addWidget(text_label('Đồng bộ chỉ đọc thông báo và bản phát hành từ GitHub. Cài đặt được lưu trên máy của bạn, không tải cấu hình cá nhân lên mạng.',13,'#a6c9e8',wrap=True));body.addWidget(ArtDivider())
        self.chk_auto_detect=ArtCheckBox('Tự tìm game khi chưa chọn thư mục');self.chk_auto_detect.setChecked(config_manager.get('auto_detect_game',True));body.addWidget(self.chk_auto_detect)
        self.chk_update=ArtCheckBox('Kiểm tra cập nhật launcher lúc mở');self.chk_update.setChecked(config_manager.get('check_updates_on_start',True));body.addWidget(self.chk_update)
        self.chk_reduced_motion=ArtCheckBox('Giảm hiệu ứng chuyển động và làm mờ',toggle=True);self.chk_reduced_motion.setChecked(config_manager.get('reduced_motion',False));body.addWidget(self.chk_reduced_motion)
        self.fields=(self.path_input,self.payload_input,self.repo_input,self.branch_input,self.chk_auto_detect,self.chk_update,self.chk_reduced_motion)
        if getattr(config_manager,'_corrupt',False):
            for field in self.fields:field.setEnabled(False)
            self.sync_button.setEnabled(False)
        if config_manager.warnings:
            body.addWidget(AlertStrip('\n'.join(config_manager.warnings),'warning'))
            if getattr(config_manager,'_corrupt',False):
                button=self._button('Giữ bản lỗi và phục hồi cấu hình','restore',370);button.clicked.connect(self._recover_config);body.addWidget(button)
        body.addStretch();self.body.addWidget(scroll_area(content));self.footer.addWidget(text_label('Launcher '+LAUNCHER_VERSION+' · giao diện r09',13,'#a6c9e8'));self.footer.addStretch();button=self._button('Đóng','close',130);button.clicked.connect(self.reject);self.footer.addWidget(button);button=self._button('Lưu cài đặt','check',180,'primary');button.clicked.connect(self._save_settings);self.footer.addWidget(button);self._validate()
        if parent and hasattr(parent,'github_sync_changed'):
            parent.github_sync_changed.connect(self._sync_status);self._sync_status(getattr(parent,'_github_sync_state',{}))
        else:self._sync_status({})
    def _button(self,label,icon,width,variant='secondary'):
        button=StarlitButton(label,variant=variant,icon=icon);button.stretch_background=True;button.caption_wrap=True;button.setMinimumWidth(width);button.setMinimumHeight(54);return button
    def _validate(self,*args):
        path=Path(self.path_input.text());self.path_status_label.setText('Đã tìm thấy StellaSora.exe. Phiên bản được đối chiếu khi cài.' if (path/'StellaSora.exe').is_file() else 'Chọn đúng thư mục đang cài game có StellaSora.exe.')
    def _browse_path(self):
        selected=QFileDialog.getExistingDirectory(self,'Chọn thư mục game',self.path_input.text() or 'C:/')
        if selected:self.path_input.setText(selected)
    def _browse_payload(self):
        selected=QFileDialog.getExistingDirectory(self,'Chọn thư mục có patch_manifest.json',self.payload_input.text())
        if selected:self.payload_input.setText(selected)
    def _persist_channel(self):
        config=self.config_manager;before=config.data
        try:config.set_channel(self.repo_input.text(),self.branch_input.text())
        except ValueError as exc:self.sync_status_label.setText(str(exc));return False
        if not config.save():config.update(before);self.sync_status_label.setText('\n'.join(config.warnings));return False
        return True
    def _request_sync(self):
        if self._persist_channel():self.github_sync_requested.emit()
    def _sync_status(self,state):
        labels={'online':'trực tuyến','empty':'trực tuyến, chưa có mục mới','cached':'bản lưu, chưa lấy được dữ liệu mới','bundled':'đi kèm ứng dụng, chưa lấy được dữ liệu mới','error':'lỗi kết nối hoặc dữ liệu','unavailable':'chưa có dữ liệu'}
        lines=[state.get('message','Chưa đồng bộ GitHub.')]
        if 'notification_status' in state:lines.append('Thông báo: '+str(state.get('notification_version') or 'chưa công bố')+' — '+labels.get(state['notification_status'],state['notification_status']))
        if 'release_status' in state:lines.append('Bản phát hành: '+str(state.get('release_version') or 'chưa đọc được')+' — '+labels.get(state['release_status'],state['release_status']))
        if 'manifest_status' in state:lines.append('Gói bản dịch: '+str(state.get('translation_version') or 'chưa xác minh')+' — '+labels.get(state['manifest_status'],state['manifest_status'])+((' · '+str(state['translation_file_count'])+' tệp được kê khai') if state.get('translation_file_count') is not None else ''))
        if state.get('translation_scope')=='images_only':lines.append('Gói hiện tại chỉ kê khai tệp hình ảnh; không tự thêm thoại hoặc bảng chữ ngoài gói.')
        if state.get('notification_message') and state.get('notification_status') not in ('online','empty'):lines.append(state['notification_message'])
        if state.get('cache_warning'):lines.append(state['cache_warning'])
        lines.append('Launcher trên máy: '+LAUNCHER_VERSION)
        if isinstance(state.get('update'),dict) and state['update'].get('message'):lines.append(state['update']['message'])
        for key in ('release_error','manifest_error'):
            if state.get(key):lines.append(state[key])
        self.sync_status_label.setText('\n'.join(lines))
        try:channel=self.config_manager.channel();self.endpoint_label.setText('Kho: '+channel['repo']+' · nhánh '+channel['branch']+'\nThông báo: '+str(channel['notifications_url'])+'\nPhát hành: '+str(channel['release_url']))
        except ValueError as exc:self.endpoint_label.setText(str(exc))
    def _check_update(self):
        if not self._persist_channel():return
        parent=self.parentWidget();self.accept()
        if parent and hasattr(parent,'_check_update'):QTimer.singleShot(0,parent._check_update)
    def _recover_config(self):
        ok=self.config_manager.preserve_corrupt_and_reset()
        if ok:
            for field in self.fields:field.setEnabled(True)
            self.sync_button.setEnabled(True)
        self.path_status_label.setText('Đã giữ bản lỗi và lưu cấu hình phục hồi.' if ok else '\n'.join(self.config_manager.warnings))
    def _save_settings(self):
        config=self.config_manager;before=config.data
        try:old_channel=config.channel()
        except (ValueError,TypeError):old_channel=None
        try:config.set_channel(self.repo_input.text(),self.branch_input.text())
        except ValueError as exc:self.sync_status_label.setText(str(exc));return
        config.update({'game_path':self.path_input.text().strip(),'payload_path':self.payload_input.text().strip(),'auto_detect_game':self.chk_auto_detect.isChecked(),'check_updates_on_start':self.chk_update.isChecked(),'reduced_motion':self.chk_reduced_motion.isChecked()})
        if not config.save():config.update(before);self.path_status_label.setText('\n'.join(config.warnings));return
        if config.channel()!=old_channel:self.channel_changed.emit()
        self.game_path_changed.emit(config.get('game_path'));self.accept()
