# -*- coding: utf-8 -*-
"""
Configuration and filesystem layout manager for Stella Sora Launcher.
Maintains clear separation of:
- resource_dir: Readonly bundled UI and branding assets (MEIPASS or source tree)
- app_data_dir: Writable storage for user config, backups, journals, logs
- payload_root: Sidecar or verified cached Vietnamese localization payloads
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

LAUNCHER_VERSION = "0.9.8"
DEFAULT_GITHUB_REPO = "channhat/StellaSora_VietHoa"

DEFAULT_CONFIG: dict[str, Any] = {
    "version": LAUNCHER_VERSION,
    "game_path": "",
    "selected_platform": "auto",  # "auto", "steam", "standalone"
    "language": "vi",  # "vi", "en"
    "check_updates_on_start": True,
    "reduced_motion": False,
    "github_repo": DEFAULT_GITHUB_REPO,
    "custom_manifest_url": "",
    "custom_announcements_url": "",
    "auto_detect_game": True,
}


class PathManager:
    """Manages filesystem paths for both development and frozen PyInstaller environments."""

    def __init__(self, resource_dir: Path | None = None, app_data_dir: Path | None = None, override_app_data: Path | None = None):
        self._override_resource_dir = resource_dir
        self._override_app_data = app_data_dir or override_app_data

    @property
    def is_frozen(self) -> bool:
        return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

    @property
    def exe_dir(self) -> Path:
        if self.is_frozen:
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[2]

    @property
    def resource_dir(self) -> Path:
        """Read-only bundled assets directory."""
        if self._override_resource_dir is not None and self._override_resource_dir.exists():
            return self._override_resource_dir
        if self.is_frozen:
            meipass = Path(sys._MEIPASS)  # type: ignore
            res = meipass / "resources"
            if res.exists():
                return res
            return meipass
        # Source tree: launcher_next/resources
        src_res = Path(__file__).resolve().parent.parent / "resources"
        if src_res.exists():
            return src_res
        return Path(__file__).resolve().parents[2] / "launcher_next" / "resources"

    @property
    def app_data_dir(self) -> Path:
        """Writable user data directory (config, logs, backups, journals)."""
        if self._override_app_data is not None:
            self._override_app_data.mkdir(parents=True, exist_ok=True)
            return self._override_app_data

        # Standard Windows AppData
        appdata_env = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if appdata_env:
            base = Path(appdata_env) / "StellaSora_Launcher"
        else:
            base = Path.home() / ".stellasora_launcher"

        try:
            base.mkdir(parents=True, exist_ok=True)
            # Test writeability
            test_file = base / ".write_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
            return base
        except Exception:
            # Fallback to tempdir
            fallback = Path(tempfile.gettempdir()) / "StellaSora_Launcher"
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback

    @property
    def backup_root(self) -> Path:
        p = self.app_data_dir / "backups"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def logs_dir(self) -> Path:
        p = self.app_data_dir / "logs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def journals_dir(self) -> Path:
        p = self.app_data_dir / "journals"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def log_dir(self) -> Path:
        return self.logs_dir

    @property
    def patch_store_dir(self) -> Path:
        return self.payload_root

    @property
    def receipt_file(self) -> Path:
        return self.app_data_dir / ".vietnamese_patch_receipt.json"

    @property
    def config_file(self) -> Path:
        return self.app_data_dir / "config.json"

    @property
    def payload_root(self) -> Path:
        """Location of patch files / AssetBundles / arcx to install."""
        candidates = [
            self.exe_dir.parent,  # when candidate exe is in dist/launcher_ui_candidate_r01
            self.exe_dir / "StellaSora_VietHoa" / "dist",  # when running from game root
            self.exe_dir / "dist",
            self.exe_dir,
            Path("C:/YostarGames/StellaSora_EN/StellaSora_VietHoa/dist"),
            Path(__file__).resolve().parents[2] / "dist",
            Path(__file__).resolve().parents[3] / "dist",
        ]
        for c in candidates:
            if c.exists() and ((c / "patch_manifest.json").exists() or (c / "lua_patched_vi.arcx").exists() or (c / "AssetBundles").exists()):
                return c

        # Fallback to app_data downloaded cache
        p = self.app_data_dir / "payload_cache"
        p.mkdir(parents=True, exist_ok=True)
        return p


class ConfigManager:
    """Loads, saves, and migrates launcher settings without losing unknown custom fields."""

    def __init__(self, path_manager: PathManager):
        self.pm = path_manager
        self._config: dict[str, Any] = {}
        self.load()

    def load(self) -> dict[str, Any]:
        cfg = dict(DEFAULT_CONFIG)

        # Migration from old launcher config if present
        old_configs = [
            self.pm.exe_dir / "launcher" / "launcher_config.json",
            self.pm.exe_dir / "launcher_config.json",
            self.pm.app_data_dir / "launcher_config.json"
        ]
        migrated: dict[str, Any] = {}
        for old_p in old_configs:
            if old_p.exists():
                try:
                    with open(old_p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            migrated.update(data)
                except Exception:
                    pass

        # Load current config if exists
        cfg_p = self.pm.config_file
        if cfg_p.exists():
            try:
                with open(cfg_p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        cfg.update(data)
            except Exception as e:
                # Log error and preserve default with migration
                pass
        elif migrated:
            cfg.update(migrated)

        self._config = cfg
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        self._config[key] = value

    def update(self, mapping: dict[str, Any]):
        self._config.update(mapping)

    def save(self) -> bool:
        """Atomically saves configuration to disk."""
        cfg_p = self.pm.config_file
        cfg_p.parent.mkdir(parents=True, exist_ok=True)
        tmp_p = cfg_p.with_suffix(".tmp")
        try:
            with open(tmp_p, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            if cfg_p.exists():
                cfg_p.unlink()
            tmp_p.rename(cfg_p)
            return True
        except Exception as e:
            if tmp_p.exists():
                tmp_p.unlink(missing_ok=True)
            return False

    @property
    def data(self) -> dict[str, Any]:
        return dict(self._config)
