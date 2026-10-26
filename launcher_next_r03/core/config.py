"""Explicit resource/user-data/payload paths and lossless config migration."""
from __future__ import annotations
import json,os,sys,uuid
from pathlib import Path
from .safety import atomic_json
LAUNCHER_VERSION="0.9.8"
DEFAULT_GITHUB_REPO="doubleD1302/AmeeVH"
DEFAULT_CONFIG={"version":LAUNCHER_VERSION,"game_path":"","auto_detect_game":True,"check_updates_on_start":True,"reduced_motion":False,"github_repo":DEFAULT_GITHUB_REPO,"github_api_url":"https://api.github.com/repos/doubleD1302/AmeeVH/releases/latest","remote_notifications_url":"https://raw.githubusercontent.com/doubleD1302/AmeeVH/main/launcher/notifications.json","custom_manifest_url":"","custom_announcements_url":"","payload_path":"","language":"vi"}
class PathManager:
    def __init__(self,resource_dir=None,app_data_dir=None,override_app_data=None):
        self._resource=Path(resource_dir) if resource_dir else None
        self._app=Path(app_data_dir or override_app_data) if app_data_dir or override_app_data else None
    @property
    def is_frozen(self):return bool(getattr(sys,'frozen',False) and hasattr(sys,'_MEIPASS'))
    @property
    def exe_dir(self):return Path(sys.executable).resolve().parent if self.is_frozen else Path(__file__).resolve().parents[1]
    @property
    def resource_dir(self):
        if self._resource is not None:
            if not self._resource.is_dir():raise OSError('Không tìm thấy thư mục tài nguyên: '+str(self._resource))
            return self._resource
        return Path(sys._MEIPASS)/'resources' if self.is_frozen else Path(__file__).resolve().parents[1]/'resources'
    @property
    def app_data_dir(self):
        p=self._app or Path(os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or Path.home())/'StellaSora_Launcher_Candidate_r02'
        p.mkdir(parents=True,exist_ok=True);return p
    def _dir(self,n):
        p=self.app_data_dir/n;p.mkdir(parents=True,exist_ok=True);return p
    @property
    def backup_root(self):return self._dir('backups')
    @property
    def journals_dir(self):return self._dir('journals')
    @property
    def logs_dir(self):return self._dir('logs')
    @property
    def log_dir(self):return self.logs_dir
    @property
    def config_file(self):return self.app_data_dir/'config.json'
    @property
    def receipt_file(self):return self.app_data_dir/'.vietnamese_patch_receipt.json' # legacy diagnostics only
    @property
    def payload_root(self):return self._dir('payload_cache')
    @property
    def patch_store_dir(self):return self.payload_root
class ConfigManager:
    def __init__(self,path_manager):self.pm=path_manager;self.warnings=[];self._config={};self.load()
    def load(self):
        cfg=dict(DEFAULT_CONFIG)
        old=[self.pm.exe_dir/'config.json',self.pm.exe_dir/'launcher'/'config.json',self.pm.exe_dir.parent/'launcher'/'config.json',self.pm.app_data_dir/'launcher_config.json']
        for f in old:
            if f==self.pm.config_file or not f.is_file():continue
            try:
                d=json.loads(f.read_text(encoding='utf8'))
                if isinstance(d,dict):cfg.update(d)
            except (ValueError,OSError) as e:self.warnings.append('Không đọc được cấu hình cũ '+str(f)+': '+str(e))
        if not cfg.get('game_path') and cfg.get('default_game_path'):cfg['game_path']=cfg['default_game_path']
        f=self.pm.config_file
        if f.is_file():
            try:
                d=json.loads(f.read_text(encoding='utf8'))
                if not isinstance(d,dict):raise ValueError('JSON phải là object')
                cfg.update(d)
            except (OSError,ValueError) as e:
                # Keep the malformed preimage; save() is inhibited until user chooses recovery.
                self.warnings.append('Cấu hình bị hỏng; bản gốc được giữ tại '+str(f)+'. '+str(e));self._corrupt=True
        self._config=cfg;return dict(cfg)
    def get(self,key,default=None):return self._config.get(key,default)
    def set(self,key,value):self._config[key]=value
    def update(self,mapping):self._config.update(mapping)
    def save(self):
        if getattr(self,'_corrupt',False):self.warnings.append('Chưa lưu: cần bảo toàn cấu hình lỗi trước khi phục hồi.');return False
        try:atomic_json(self.pm.config_file,self._config);return True
        except OSError as e:self.warnings.append('Không lưu được cấu hình: '+str(e));return False
    def preserve_corrupt_and_reset(self):
        f=self.pm.config_file
        if f.is_file():f.rename(f.with_name('config.corrupt.'+uuid.uuid4().hex+'.json'))
        self._corrupt=False;return self.save()
    @property
    def data(self):return dict(self._config)
