"""Tests for configuration persistence, migration, and filesystem layout."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from launcher.core.config import ConfigManager, PathManager


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_cfg_"))
        self.app_data = self.temp_dir / "app_data"
        self.res_dir = self.temp_dir / "resources"
        self.res_dir.mkdir(parents=True)
        self.pm = PathManager(resource_dir=self.res_dir, app_data_dir=self.app_data)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_config_creation(self):
        cfg = ConfigManager(self.pm)
        from launcher.core.config import LAUNCHER_VERSION
        self.assertEqual(cfg.get("version"), LAUNCHER_VERSION)
        self.assertTrue(cfg.get("auto_detect_game"))
        self.assertFalse(cfg.get("reduced_motion"))

    def test_atomic_save(self):
        cfg = ConfigManager(self.pm)
        cfg.set("game_path", "D:\\Games\\StellaSora")
        cfg.set("reduced_motion", True)
        self.assertTrue(cfg.save())

        # Reload from fresh instance
        cfg2 = ConfigManager(self.pm)
        self.assertEqual(cfg2.get("game_path"), "D:\\Games\\StellaSora")
        self.assertTrue(cfg2.get("reduced_motion"))

    def test_migration_from_old_config(self):
        # Create an old config file in exe_dir / launcher
        old_cfg_dir = self.pm.exe_dir / "launcher"
        old_cfg_dir.mkdir(parents=True, exist_ok=True)
        old_cfg_file = old_cfg_dir / "launcher_config.json"

        # Only create if it doesn't already exist to avoid mutating workspace
        existed_before = old_cfg_file.exists()
        if not existed_before:
            old_cfg_file.write_text(json.dumps({"game_path": "C:\\Legacy\\StellaSora", "custom_key": 123}), encoding="utf-8")

        try:
            cfg = ConfigManager(self.pm)
            self.assertIn("game_path", cfg.data)
        finally:
            if not existed_before and old_cfg_file.exists():
                old_cfg_file.unlink()


if __name__ == "__main__":
    unittest.main()
