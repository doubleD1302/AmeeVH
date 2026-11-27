"""Explicit resource/user-data/payload paths and lossless config migration."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import uuid
from pathlib import Path
from typing import Any

from .safety import atomic_json

LAUNCHER_VERSION = "2.1.3"
SUPPORT_DONATION_ENABLED: bool = False
DEFAULT_GITHUB_REPO = "doubleD1302/AmeeVH"
DEFAULT_GITHUB_BRANCH = "main"
APP_DATA_DIR_NAME = "StellaSora_VietHoa_Launcher"
LEGACY_APP_DATA_DIR_NAME = "StellaSora_Launcher_Candidate_r02"
VALID_GRAPHICS_MODES = ("auto", "software", "noblur")

DEFAULT_CONFIG: dict[str, Any] = {
    "version": LAUNCHER_VERSION,
    "game_path": "",
    "auto_detect_game": True,
    "check_updates_on_start": True,
    "check_official_on_start": True,
    "auto_restore_before_game_update": False,
    "guard_watch_game_updates": True,
    "guard_background_tray": True,
    "guard_auto_close_game_on_update": False,
    "guard_start_with_windows": False,
    "reduced_motion": False,
    "graphics_mode": "auto",
    "auto_sync_official_bg": True,
    "create_desktop_shortcut": True,
    "github_repo": DEFAULT_GITHUB_REPO,
    "github_branch": DEFAULT_GITHUB_BRANCH,
    "github_api_url": "https://api.github.com/repos/doubleD1302/AmeeVH/releases/latest",
    "remote_notifications_url": "https://raw.githubusercontent.com/doubleD1302/AmeeVH/main/launcher/notifications.json",
    "custom_manifest_url": "",
    "custom_announcements_url": "",
    "payload_path": "",
    "language": "vi",
}


def derived_github_endpoints(repo: str, branch: str = "main") -> dict[str, str]:
    if not isinstance(repo, str):
        raise ValueError("Kho GitHub cần có dạng tên-tài-khoản/tên-kho.")
    repo = repo.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("Kho GitHub cần có dạng tên-tài-khoản/tên-kho.")
    owner, name = repo.split("/", 1)
    if any(seg in (".", "..") or set(seg) == {"."} for seg in (owner, name)):
        raise ValueError("Kho GitHub không được chứa thành phần điều hướng dấu chấm.")
    if not isinstance(branch, str):
        raise ValueError("Tên nhánh GitHub không hợp lệ.")
    branch = branch.strip()
    if not branch or len(branch) > 200 or any(ord(c) < 32 for c in branch):
        raise ValueError("Tên nhánh GitHub không hợp lệ.")
    return {
        "github_api_url": f"https://api.github.com/repos/{repo}/releases/latest",
        "remote_notifications_url": (
            f"https://raw.githubusercontent.com/{repo}/{urllib.parse.quote(branch, safe='')}/launcher/notifications.json"
        ),
    }


def migrate_github_channel(cfg: dict[str, Any]) -> dict[str, Any]:
    # Only empty values, recorded derived values and the shipped old defaults are
    # replaced. Any other explicit endpoint, custom field or unknown key survives.
    raw_repo = cfg.get("github_repo", DEFAULT_GITHUB_REPO)
    if raw_repo is None or (isinstance(raw_repo, str) and not raw_repo.strip()):
        raw_repo = DEFAULT_GITHUB_REPO
        cfg["github_repo"] = raw_repo
    raw_branch = cfg.get("github_branch", DEFAULT_GITHUB_BRANCH)
    if not isinstance(raw_branch, str) or not raw_branch.strip():
        raw_branch = DEFAULT_GITHUB_BRANCH
        cfg["github_branch"] = raw_branch
    target = derived_github_endpoints(raw_repo, raw_branch)
    previous = cfg.get("_github_derived_endpoints", {})
    if not isinstance(previous, dict):
        previous = {}
    legacy = derived_github_endpoints(DEFAULT_GITHUB_REPO, DEFAULT_GITHUB_BRANCH)
    for key, url in target.items():
        value = cfg.get(key)
        if not value or value == previous.get(key) or value == legacy[key]:
            cfg[key] = url
    cfg["_github_derived_endpoints"] = target
    return cfg


def _default_local_app_data_base() -> Path:
    return Path(os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or Path.home())


class PathManager:
    def __init__(self, resource_dir=None, app_data_dir=None, override_app_data=None):
        self._resource = Path(resource_dir) if resource_dir else None
        chosen_app = app_data_dir if app_data_dir else override_app_data
        self._app = Path(chosen_app) if chosen_app else None

    @property
    def is_frozen(self) -> bool:
        return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))

    @property
    def is_custom_app_data(self) -> bool:
        return self._app is not None

    @property
    def exe_dir(self) -> Path:
        return Path(sys.executable).resolve().parent if self.is_frozen else Path(__file__).resolve().parents[1]

    @property
    def resource_dir(self) -> Path:
        if self._resource is not None:
            if not self._resource.is_dir():
                raise OSError("Không tìm thấy thư mục tài nguyên: " + str(self._resource))
            return self._resource
        return Path(sys._MEIPASS) / "resources" if self.is_frozen else Path(__file__).resolve().parents[1] / "resources"

    @property
    def app_data_dir(self) -> Path:
        p = self._app or (_default_local_app_data_base() / APP_DATA_DIR_NAME)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def legacy_app_data_dir(self) -> Path:
        return _default_local_app_data_base() / LEGACY_APP_DATA_DIR_NAME

    def _dir(self, name: str) -> Path:
        p = self.app_data_dir / name
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def backup_root(self) -> Path:
        return self._dir("backups")

    @property
    def journals_dir(self) -> Path:
        return self._dir("journals")

    @property
    def logs_dir(self) -> Path:
        return self._dir("logs")

    @property
    def log_dir(self) -> Path:
        return self.logs_dir

    @property
    def config_file(self) -> Path:
        return self.app_data_dir / "config.json"

    @property
    def receipt_file(self) -> Path:
        return self.app_data_dir / ".vietnamese_patch_receipt.json"  # legacy diagnostics only

    @property
    def payload_root(self) -> Path:
        return self._dir("payload_cache")

    @property
    def patch_store_dir(self) -> Path:
        return self.payload_root

    @property
    def bg_cache_dir(self) -> Path:
        return self._dir("bg_cache")

    @property
    def update_helper_dir(self) -> Path:
        return self._dir("update_helper")

    @property
    def migration_marker_file(self) -> Path:
        return self.app_data_dir / ".migrated_from_r02.json"

    @property
    def graphics_sentinel_file(self) -> Path:
        return self.app_data_dir / ".graphics_boot_pending"

    @property
    def official_check_file(self) -> Path:
        return self.app_data_dir / "official_check.json"


class ConfigManager:
    def __init__(self, path_manager: PathManager):
        self.pm = path_manager
        self.warnings: list[str] = []
        self._config: dict[str, Any] = {}
        self._corrupt: bool = False
        self.load()

    def load(self) -> dict[str, Any]:
        self._corrupt = False
        cfg = dict(DEFAULT_CONFIG)
        old = [
            self.pm.exe_dir / "config.json",
            self.pm.exe_dir / "launcher" / "config.json",
            self.pm.exe_dir.parent / "launcher" / "config.json",
            self.pm.app_data_dir / "launcher_config.json",
        ]
        for f in old:
            if f == self.pm.config_file or not f.is_file():
                continue
            try:
                d = json.loads(f.read_text(encoding="utf8"))
                if isinstance(d, dict):
                    cfg.update(d)
            except (ValueError, OSError) as e:
                self.warnings.append("Không đọc được cấu hình cũ " + str(f) + ": " + str(e))
        if not cfg.get("game_path") and cfg.get("default_game_path"):
            cfg["game_path"] = cfg["default_game_path"]
        f = self.pm.config_file
        if f.is_file():
            try:
                d = json.loads(f.read_text(encoding="utf8"))
                if not isinstance(d, dict):
                    raise ValueError("JSON phải là object")
                cfg.update(d)
            except (OSError, ValueError) as e:
                # Keep the malformed preimage; save() is inhibited until user chooses recovery.
                self.warnings.append("Cấu hình bị hỏng; bản gốc được giữ tại " + str(f) + ". " + str(e))
                self._corrupt = True
        gm = cfg.get("graphics_mode")
        if not isinstance(gm, str) or gm not in VALID_GRAPHICS_MODES:
            if gm is not None:
                self.warnings.append(f"Chế độ đồ họa không hợp lệ ({gm!r}); đặt lại về 'auto'.")
            cfg["graphics_mode"] = "auto"
        try:
            migrate_github_channel(cfg)
        except ValueError as exc:
            self.warnings.append(str(exc))
        self._config = cfg
        return dict(cfg)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def update(self, mapping: dict[str, Any]) -> None:
        self._config.update(mapping)

    def set_channel(self, repo: str, branch: str) -> None:
        derived_github_endpoints(repo, branch)
        updated = dict(self._config)
        updated.update({"github_repo": repo.strip(), "github_branch": branch.strip()})
        migrate_github_channel(updated)
        self._config = updated

    def channel(self) -> dict[str, Any]:
        cfg = dict(self._config)
        try:
            migrate_github_channel(cfg)
        except ValueError:
            cfg["github_repo"] = DEFAULT_GITHUB_REPO
            cfg["github_branch"] = DEFAULT_GITHUB_BRANCH
            migrate_github_channel(cfg)
        branch = cfg.get("github_branch")
        if not isinstance(branch, str) or not branch.strip():
            branch = DEFAULT_GITHUB_BRANCH
        return {
            "repo": cfg.get("github_repo") or DEFAULT_GITHUB_REPO,
            "branch": branch.strip(),
            "release_url": cfg.get("github_api_url"),
            "notifications_url": cfg.get("custom_announcements_url") or cfg.get("remote_notifications_url"),
            "manifest_url": cfg.get("custom_manifest_url") or None,
        }

    def save(self) -> bool:
        if getattr(self, "_corrupt", False):
            self.warnings.append("Chưa lưu: cần bảo toàn cấu hình lỗi trước khi phục hồi.")
            return False
        self._config["version"] = LAUNCHER_VERSION
        try:
            atomic_json(self.pm.config_file, self._config)
            return True
        except OSError as e:
            self.warnings.append("Không lưu được cấu hình: " + str(e))
            return False

    def preserve_corrupt_and_reset(self) -> bool:
        f = self.pm.config_file
        if f.is_file():
            f.rename(f.with_name("config.corrupt." + uuid.uuid4().hex + ".json"))
        fresh = dict(DEFAULT_CONFIG)
        migrate_github_channel(fresh)
        self._config = fresh
        self._corrupt = False
        return self.save()

    @property
    def data(self) -> dict[str, Any]:
        return dict(self._config)
