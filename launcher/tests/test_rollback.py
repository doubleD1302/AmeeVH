"""Tests for canonical root-bound rollback engine."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from launcher.core.installer import PatchInstaller, sha256_file
from launcher.core.rollback import RollbackEngine
from launcher.core.types import OperationPhase


class TestRollbackEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_roll_"))
        self.game_root = self.temp_dir / "game_primary"
        self.game_root.mkdir()
        (self.game_root / "StellaSora.exe").write_text("game_binary", encoding="utf-8")

        scripts_dir = self.game_root / "Persistent_Store" / "Scripts"
        scripts_dir.mkdir(parents=True)
        self.lua_file = scripts_dir / "lua.arcx"
        self.lua_file.write_text("ORIGINAL_PRISTINE_STATE", encoding="utf-8")

        # Payload
        self.payload_root = self.temp_dir / "payload"
        self.payload_root.mkdir()
        patch_scripts = self.payload_root / "Persistent_Store" / "Scripts"
        patch_scripts.mkdir(parents=True)
        patch_lua = patch_scripts / "lua.arcx"
        patch_lua.write_text("PATCHED_VIETNAMESE_STATE", encoding="utf-8")

        self.manifest = {
            "version": "v1.0.5",
            "client_game_version": "2.0.0",
            "resource_version": "2610201624",
            "files": {
                "Persistent_Store/Scripts/lua.arcx": {
                    "sha256": sha256_file(patch_lua),
                    "size": patch_lua.stat().st_size
                }
            }
        }

        self.backup_root = self.temp_dir / "backups"
        self.journals_dir = self.temp_dir / "journals"

        # Install patch first to produce backup
        installer = PatchInstaller(self.backup_root, self.journals_dir)
        installer.install(self.game_root, self.payload_root, manifest_data=self.manifest)

        self.rollback_engine = RollbackEngine(self.backup_root)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_successful_rollback(self):
        # Game is currently patched
        self.assertEqual(self.lua_file.read_text(encoding="utf-8"), "PATCHED_VIETNAMESE_STATE")
        receipt_file = self.game_root / ".vietnamese_patch_receipt.json"
        self.assertTrue(receipt_file.exists())

        # Execute rollback
        events = []
        result = self.rollback_engine.rollback(
            self.game_root,
            event_cb=lambda e: events.append(e)
        )

        self.assertIsNotNone(result)
        # Content restored to original
        self.assertEqual(self.lua_file.read_text(encoding="utf-8"), "ORIGINAL_PRISTINE_STATE")
        # Receipt file cleaned up
        self.assertFalse(receipt_file.exists())

        phases = [e.phase for e in events]
        self.assertIn(OperationPhase.ROLLBACK, phases)
        self.assertIn(OperationPhase.DONE, phases)

    def test_cross_root_backup_isolation(self):
        # Another game root should NOT see or restore backups from primary root
        another_root = self.temp_dir / "game_secondary"
        another_root.mkdir()
        (another_root / "StellaSora.exe").write_text("game_binary_2", encoding="utf-8")

        backups = self.rollback_engine.get_backups_for_game(another_root)
        self.assertEqual(len(backups), 0)


if __name__ == "__main__":
    unittest.main()
