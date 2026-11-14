"""Security tests: Path traversal guards, root boundary enforcement."""

import shutil
import tempfile
import unittest
from pathlib import Path

from launcher.core.installer import InstallerError, PatchInstaller


class TestSecurityGuards(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_sec_"))
        self.game_root = self.temp_dir / "game"
        self.game_root.mkdir()
        (self.game_root / "StellaSora.exe").write_text("dummy", encoding="utf-8")

        self.backup_root = self.temp_dir / "backups"
        self.journals_dir = self.temp_dir / "journals"
        self.installer = PatchInstaller(self.backup_root, self.journals_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_absolute_path_traversal_blocked(self):
        with self.assertRaises(InstallerError) as ctx:
            self.installer._validate_path_security(self.game_root, "C:/Windows/System32/calc.exe")
        self.assertIn("PATH_TRAVERSAL", ctx.exception.code)

    def test_relative_dot_dot_traversal_blocked(self):
        with self.assertRaises(InstallerError) as ctx:
            self.installer._validate_path_security(self.game_root, "../evil.txt")
        self.assertIn("PATH_TRAVERSAL", ctx.exception.code)

    def test_nested_dot_dot_traversal_blocked(self):
        with self.assertRaises(InstallerError) as ctx:
            self.installer._validate_path_security(self.game_root, "sub/../../evil.txt")
        self.assertIn("PATH_TRAVERSAL", ctx.exception.code)

    def test_valid_path_allowed(self):
        dest = self.installer._validate_path_security(self.game_root, "Persistent_Store/Scripts/lua.arcx")
        self.assertTrue(str(dest).startswith(str(self.game_root)))


if __name__ == "__main__":
    unittest.main()
