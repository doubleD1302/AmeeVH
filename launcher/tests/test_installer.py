"""End-to-end tests for transactional patch installer."""

import hashlib
import json
import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from launcher.core.installer import InstallerError, PatchInstaller, sha256_file
from launcher.core.types import OperationPhase


class TestPatchInstaller(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_inst_"))
        self.game_root = self.temp_dir / "game"
        self.game_root.mkdir()
        (self.game_root / "StellaSora.exe").write_text("game_binary", encoding="utf-8")

        # Create original files in game root
        scripts_dir = self.game_root / "Persistent_Store" / "Scripts"
        scripts_dir.mkdir(parents=True)
        self.orig_lua = scripts_dir / "lua.arcx"
        self.orig_lua.write_text("ORIGINAL_LUA_CONTENT_12345", encoding="utf-8")

        # Create patch store / payload
        self.payload_root = self.temp_dir / "payload"
        self.payload_root.mkdir()
        patch_scripts = self.payload_root / "Persistent_Store" / "Scripts"
        patch_scripts.mkdir(parents=True)
        self.patch_lua = patch_scripts / "lua.arcx"
        self.patch_lua.write_text("VIETNAMESE_TRANSLATED_LUA_CONTENT_99999", encoding="utf-8")

        # Manifest
        self.manifest = {
            "version": "v1.0.5",
            "client_game_version": "2.0.0",
            "resource_version": "2610201624",
            "files": {
                "Persistent_Store/Scripts/lua.arcx": {
                    "sha256": sha256_file(self.patch_lua),
                    "size": self.patch_lua.stat().st_size
                }
            }
        }
        with open(self.payload_root / "patch_manifest.json", "w", encoding="utf-8") as f:
            json.dump(self.manifest, f)

        self.backup_root = self.temp_dir / "backups"
        self.journals_dir = self.temp_dir / "journals"
        self.installer = PatchInstaller(self.backup_root, self.journals_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_successful_installation_and_backup(self):
        events = []
        receipt = self.installer.install(
            self.game_root,
            self.payload_root,
            manifest_data=self.manifest,
            event_cb=lambda e: events.append(e)
        )

        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.get("version"), "v1.0.5")

        # Verify lua file was replaced with patch content
        content = self.orig_lua.read_text(encoding="utf-8")
        self.assertEqual(content, "VIETNAMESE_TRANSLATED_LUA_CONTENT_99999")

        # Verify backup exists
        backups = [p for p in self.backup_root.glob("game_*/*") if p.is_dir()]
        self.assertTrue(len(backups) > 0)
        backup_manifest = json.loads((backups[0] / "backup_manifest.json").read_text(encoding="utf-8"))
        self.assertIn("Persistent_Store/Scripts/lua.arcx", backup_manifest["files"])

        # Verify receipt file exists in game root
        receipt_file = self.game_root / ".vietnamese_patch_receipt.json"
        self.assertTrue(receipt_file.exists())

        # Verify event sequence reached DONE
        phases = [e.phase for e in events]
        self.assertIn(OperationPhase.PREFLIGHT, phases)
        self.assertIn(OperationPhase.BACKUP, phases)
        self.assertIn(OperationPhase.APPLY, phases)
        self.assertIn(OperationPhase.READBACK, phases)
        self.assertIn(OperationPhase.DONE, phases)

    def test_auto_bundle_and_arcx_manifest_mapping(self):
        # Setup real-world style dist layout: lua_patched_vi.arcx, data_patched_vi.arcx, AssetBundles/
        real_payload = self.temp_dir / "real_payload"
        real_payload.mkdir()
        (real_payload / "lua_patched_vi.arcx").write_text("REAL_LUA_ARCX", encoding="utf-8")
        (real_payload / "data_patched_vi.arcx").write_text("REAL_DATA_ARCX", encoding="utf-8")
        bundles_dir = real_payload / "AssetBundles"
        bundles_dir.mkdir()
        (bundles_dir / "ui_sample.en.unity3d").write_text("BUNDLE_SAMPLE", encoding="utf-8")

        manifest_file = real_payload / "patch_manifest.json"
        manifest_data = {
            "release_tag": "v1.0.5",
            "client_game_version": "2.0.0",
            "resource_version": "2610201624",
            "lua_arcx": {
                "filename": "lua_patched_vi.arcx",
                "sha256": sha256_file(real_payload / "lua_patched_vi.arcx"),
                "size_bytes": (real_payload / "lua_patched_vi.arcx").stat().st_size
            },
            "data_arcx": {
                "filename": "data_patched_vi.arcx",
                "sha256": sha256_file(real_payload / "data_patched_vi.arcx"),
                "size_bytes": (real_payload / "data_patched_vi.arcx").stat().st_size
            },
            "total_bundles": 1,
            "bundles": {
                "ui_sample.en.unity3d": {
                    "patched_sha256": sha256_file(bundles_dir / "ui_sample.en.unity3d"),
                    "size_bytes": 13
                }
            }
        }
        manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")

        receipt = self.installer.install(self.game_root, real_payload)
        self.assertIn("Persistent_Store/Scripts/lua.arcx", receipt["files"])
        self.assertIn("Persistent_Store/Tables/data.arcx", receipt["files"])
        self.assertIn("Persistent_Store/AssetBundles/ui_sample.en.unity3d", receipt["files"])

    def test_preimage_hash_mismatch_fails_cleanly(self):
        bad_manifest = {
            "version": "v1.0.5",
            "client_game_version": "2.0.0",
            "resource_version": "2610201624",
            "client_game_version": "2.0.0",
            "resource_version": "2610201624",
            "files": {
                "Persistent_Store/Scripts/lua.arcx": {
                    "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                    "size": 100
                }
            }
        }
        with self.assertRaises(InstallerError) as ctx:
            self.installer.install(self.game_root, self.payload_root, manifest_data=bad_manifest)
        self.assertIn(ctx.exception.code, ("CORRUPT_PAYLOAD", "HASH_MISMATCH"))

        # Verify game file remained untouched
        content = self.orig_lua.read_text(encoding="utf-8")
        self.assertEqual(content, "ORIGINAL_LUA_CONTENT_12345")

    @unittest.skipUnless(os.name == 'nt', 'Windows file attributes')
    def test_readonly_destination_reports_access_denied_and_preserves_original(self):
        self.orig_lua.chmod(stat.S_IREAD)
        try:
            with self.assertRaises(InstallerError) as ctx:
                self.installer.install(self.game_root, self.payload_root, self.manifest)
            self.assertEqual(ctx.exception.code, 'FILE_ACCESS_DENIED')
            self.assertIn('chỉ đọc', str(ctx.exception))
            self.assertEqual(self.orig_lua.read_text(), 'ORIGINAL_LUA_CONTENT_12345')
            self.assertFalse((self.game_root / '.vietnamese_patch_receipt.json').exists())
            self.assertEqual(self.installer.pending(self.game_root), [])
            self.assertEqual(list(self.orig_lua.parent.glob('.patch_*')), [])
        finally:
            self.orig_lua.chmod(stat.S_IREAD | stat.S_IWRITE)

    @unittest.skipUnless(os.name == 'nt', 'Windows error codes')
    def test_sharing_violation_retries_then_installs(self):
        original_replace = os.replace
        attempts = []
        def replace(src, dst):
            if Path(src).name.startswith('.patch_'):
                attempts.append(1)
                if len(attempts) < 3:
                    raise OSError(None, 'sharing violation', str(src), 32, str(dst))
            return original_replace(src, dst)
        with patch('launcher.core.installer.os.replace', side_effect=replace), patch('launcher.core.installer.time.sleep'):
            self.installer.install(self.game_root, self.payload_root, self.manifest)
        self.assertEqual(len(attempts), 3)
        self.assertEqual(self.orig_lua.read_text(), 'VIETNAMESE_TRANSLATED_LUA_CONTENT_99999')

    @unittest.skipUnless(os.name == 'nt', 'Windows error codes')
    def test_sharing_violation_exhaustion_rolls_back(self):
        original_replace = os.replace
        def replace(src, dst):
            if Path(src).name.startswith('.patch_'):
                raise OSError(None, 'sharing violation', str(src), 32, str(dst))
            return original_replace(src, dst)
        with patch('launcher.core.installer.os.replace', side_effect=replace), patch('launcher.core.installer.time.sleep'):
            with self.assertRaises(InstallerError) as ctx:
                self.installer.install(self.game_root, self.payload_root, self.manifest)
        self.assertEqual(ctx.exception.code, 'FILE_IN_USE')
        self.assertEqual(self.orig_lua.read_text(), 'ORIGINAL_LUA_CONTENT_12345')
        self.assertEqual(self.installer.pending(self.game_root), [])
        self.assertFalse((self.game_root / '.vietnamese_patch_receipt.json').exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows file sharing')
    def test_real_windows_sharing_handle_is_retried(self):
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.CreateFileW(str(self.orig_lua), 0x80000000, 3, None, 3, 0x80, None)
        self.assertNotEqual(handle, ctypes.c_void_p(-1).value)
        closed = []
        def release(_):
            if not closed:
                self.assertTrue(kernel.CloseHandle(handle))
                closed.append(True)
        try:
            with patch('launcher.core.installer.time.sleep', side_effect=release):
                self.installer.install(self.game_root, self.payload_root, self.manifest)
        finally:
            if not closed: kernel.CloseHandle(handle)
        self.assertEqual(closed, [True])
        self.assertEqual(self.orig_lua.read_text(), 'VIETNAMESE_TRANSLATED_LUA_CONTENT_99999')

    @unittest.skipUnless(os.name == 'nt', 'Windows file attributes')
    def test_denied_second_file_restores_first_file(self):
        table = self.game_root / 'Persistent_Store' / 'Tables' / 'data.arcx'
        table.parent.mkdir(parents=True)
        table.write_text('original data')
        payload = self.payload_root / 'Persistent_Store' / 'Tables' / 'data.arcx'
        payload.parent.mkdir(parents=True)
        payload.write_text('patched data')
        self.manifest['files']['Persistent_Store/Tables/data.arcx'] = {'sha256': sha256_file(payload), 'size': payload.stat().st_size}
        table.chmod(stat.S_IREAD)
        try:
            with self.assertRaises(InstallerError) as ctx:
                self.installer.install(self.game_root, self.payload_root, self.manifest)
            self.assertEqual(ctx.exception.code, 'FILE_ACCESS_DENIED')
            self.assertEqual(self.orig_lua.read_text(), 'ORIGINAL_LUA_CONTENT_12345')
            self.assertEqual(table.read_text(), 'original data')
            self.assertEqual(self.installer.pending(self.game_root), [])
            self.assertFalse((self.game_root / '.vietnamese_patch_receipt.json').exists())
        finally:
            table.chmod(stat.S_IREAD | stat.S_IWRITE)

    @unittest.skipUnless(os.name == 'nt', 'Windows error codes')
    def test_changed_destination_during_retry_requires_recovery(self):
        original_replace = os.replace
        def replace(src, dst):
            if Path(src).name.startswith('.patch_'):
                raise OSError(None, 'sharing violation', str(src), 32, str(dst))
            return original_replace(src, dst)
        def change_external(_):
            self.orig_lua.write_text('EXTERNAL_CHANGE')
        with patch('launcher.core.installer.os.replace', side_effect=replace), patch('launcher.core.installer.time.sleep', side_effect=change_external):
            with self.assertRaises(InstallerError) as ctx:
                self.installer.install(self.game_root, self.payload_root, self.manifest)
        self.assertEqual(ctx.exception.code, 'RECOVERY_REQUIRED')
        self.assertEqual(self.orig_lua.read_text(), 'EXTERNAL_CHANGE')
        self.assertEqual(len(self.installer.pending(self.game_root)), 1)
        self.assertFalse((self.game_root / '.vietnamese_patch_receipt.json').exists())


if __name__ == "__main__":
    unittest.main()
