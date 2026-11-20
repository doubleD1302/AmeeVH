# -*- coding: utf-8 -*-
"""
Rollback / "Khôi phục gốc" engine.

Default (source="official"): downloads the fresh official text resources from the publisher's
server and installs them (core/official_restore.py). Local backups / *.orig_en are NOT used,
because they may be stale or may themselves be Vietnamese.
source="local_backup" keeps the legacy offline behaviour (core/vanilla_restore.py) for tests
and emergency use without network; it can restore an OLD game version.
"""
from __future__ import annotations
from pathlib import Path
import json
from .installer import PatchInstaller, RECEIPT, same
from .safety import InstallerError, safe_path, atomic_json
from .game_detection import canonicalize_path
from .types import OperationPhase
from .vanilla_restore import VanillaRestoreEngine
from .official_restore import OfficialRestoreEngine


class RollbackEngine:
    def __init__(self, backup_root: Path | str, journals_dir: Path | str | None = None, vanilla_dir: Path | str | None = None, cache_dir: Path | str | None = None, client=None):
        self.backup_root = Path(backup_root)
        self.journals_dir = Path(journals_dir) if journals_dir else self.backup_root.parent / "journals"
        self.vanilla_dir = Path(vanilla_dir) if vanilla_dir else None
        self.engine = PatchInstaller(self.backup_root, self.journals_dir)
        self.vanilla_engine = VanillaRestoreEngine(self.backup_root, self.journals_dir, self.vanilla_dir)
        self.official_engine = OfficialRestoreEngine(
            self.backup_root, self.journals_dir, Path(cache_dir) if cache_dir else self.backup_root.parent / "official_cache", client
        )

    def get_backups_for_game(self, root: str | Path) -> list[dict]:
        out = []
        for b in self.engine.get_backup_dir_for_root(root).glob("backup_*"):
            try:
                m = json.loads((b / "backup_manifest.json").read_text(encoding="utf8"))
                if m.get("game_root") == canonicalize_path(root):
                    out.append({
                        "id": b.name,
                        "path": b,
                        "manifest": m,
                        "files_count": len(m["files"]),
                        "created_at": m["created_at"]
                    })
            except (OSError, ValueError, KeyError):
                pass
        return sorted(out, key=lambda v: v["created_at"], reverse=True)

    def rollback(self, game_root: str | Path, backup_id: str | None = None, operation_id: str = "rollback", event_cb=None, source: str = "official", should_cancel=None) -> dict:
        """
        Restores the game to true original publisher data (vanilla, unmodded).
        source="official": download + verify the official files (default).
        source="local_backup": legacy offline restore from launcher backups.
        """
        root = Path(game_root).resolve()
        if source == "official":
            res = self.official_engine.restore(root, event_cb=event_cb, operation_id=operation_id, should_cancel=should_cancel)
            res["restored_files_count"] = len(res.get("replaced", [])) + len(res.get("already_official", []))
            return res
        self.engine._preflight(root)

        # Execute full vanilla restore
        res = self.vanilla_engine.restore_vanilla(root, event_cb=event_cb, operation_id=operation_id)
        return {
            "status": "success",
            "restored_files_count": res.get("cleaned_bundles_count", 0) + 2,
            "message": "✓ Hoàn tất khôi phục! Đã đưa game về dữ liệu gốc nguyên bản của nhà phát hành (bản hoàn chỉnh, chưa Việt hoá)."
        }
