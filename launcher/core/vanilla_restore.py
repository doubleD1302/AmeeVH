# -*- coding: utf-8 -*-
"""
Vanilla Restore Engine for Stella Sora.
Restores the game installation to 100% clean, original publisher data (vanilla, unmodded):
1. Restores Tables/data.arcx from clean publisher original (orig_en, earliest backup, golden store, or payload).
2. Restores Scripts/lua.arcx from clean publisher original (orig_en, earliest backup, golden store, or payload).
3. Restores / cleans modded AssetBundles in Persistent_Store/AssetBundles/:
   - For bundles present in StreamingAssets/InstallResource/, restores clean original.
   - For other modded bundles, removes modded files so game client verifies/updates cleanly.
4. Removes all Vietnamese subtitle files (*.srt) from Persistent_Store/Videos/.
5. Removes .vietnamese_patch_receipt.json and clears any pending journal.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Callable, Optional

from .game_detection import canonicalize_path, is_game_process_running
from .safety import InstallerError
from .types import OperationEvent, OperationPhase

RECEIPT = ".vietnamese_patch_receipt.json"


class VanillaRestoreEngine:
    def __init__(self, backup_root: Path | str, journals_dir: Path | str | None = None, vanilla_dir: Path | str | None = None):
        self.backup_root = Path(backup_root)
        self.journals_dir = Path(journals_dir) if journals_dir else self.backup_root.parent / "journals"
        self.vanilla_dir = Path(vanilla_dir) if vanilla_dir else None
        for p in (self.backup_root, self.journals_dir):
            p.mkdir(parents=True, exist_ok=True)

    @contextlib.contextmanager
    def _lock(self, root: Path):
        import msvcrt
        root_hash = hashlib.sha256(canonicalize_path(root).encode("utf8")).hexdigest()[:12]
        p_dir = self.backup_root / f"game_{root_hash}"
        p_dir.mkdir(parents=True, exist_ok=True)
        p = p_dir / ".operation.lock"
        with p.open("a+b") as f:
            if not f.tell():
                f.write(b"0")
                f.flush()
            f.seek(0)
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                raise InstallerError("Một thao tác khác đang dùng thư mục game này.", "OPERATION_BUSY")
            try:
                yield
            finally:
                f.seek(0)
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass

    def _preflight(self, root: Path):
        if not root.is_dir() or not (root / "StellaSora.exe").is_file():
            raise InstallerError("Hãy chọn đúng thư mục có StellaSora.exe.", "INVALID_ROOT")
        if is_game_process_running():
            raise InstallerError("Hãy đóng game trước khi khôi phục dữ liệu.", "GAME_RUNNING")

    def _emit(self, cb: Optional[Callable[[OperationEvent], None]], op: str, phase: OperationPhase, msg: str, n: int = 0, total: int = 0):
        if cb:
            cb(OperationEvent(op, phase, msg, n, total))

    def _find_vanilla_archive(self, root: Path, subpath: str, orig_name: str) -> Optional[Path]:
        """Searches for clean vanilla archive in local game directory, earliest backup, dist/vanilla, or bundled resources."""
        # 1. Check local game orig_en (e.g. Tables/data.arcx.orig_en)
        local_orig = root / "Persistent_Store" / subpath / f"{orig_name}.orig_en"
        if local_orig.is_file() and local_orig.stat().st_size > 0:
            return local_orig

        # 2. Check earliest backup in backup_root for this game
        root_hash = hashlib.sha256(canonicalize_path(root).encode("utf8")).hexdigest()[:12]
        game_backup_dir = self.backup_root / f"game_{root_hash}"
        if game_backup_dir.is_dir():
            backups = sorted(game_backup_dir.glob("backup_*"))
            # Oldest backup first
            for b in backups:
                cand = b / "Persistent_Store" / subpath / orig_name
                if cand.is_file() and cand.stat().st_size > 0:
                    return cand

        # 3. Check explicit vanilla_dir
        if self.vanilla_dir and self.vanilla_dir.is_dir():
            cand = self.vanilla_dir / f"{orig_name.replace('.arcx', '')}_original_en.arcx"
            if cand.is_file():
                return cand
            cand2 = self.vanilla_dir / orig_name
            if cand2.is_file():
                return cand2

        # 4. Check project dist/vanilla relative to root
        proj_vanilla = root / "StellaSora_VietHoa" / "dist" / "vanilla"
        if proj_vanilla.is_dir():
            cand = proj_vanilla / f"{orig_name.replace('.arcx', '')}_original_en.arcx"
            if cand.is_file():
                return cand

        # 5. Check repo dist/vanilla from file location
        repo_vanilla = Path(__file__).resolve().parents[2] / "dist" / "vanilla"
        if repo_vanilla.is_dir():
            cand = repo_vanilla / f"{orig_name.replace('.arcx', '')}_original_en.arcx"
            if cand.is_file():
                return cand

        return None

    def restore_vanilla(
        self,
        game_root: str | Path,
        event_cb: Optional[Callable[[OperationEvent], None]] = None,
        operation_id: str = "vanilla_restore"
    ) -> dict:
        """Executes full vanilla recovery to original publisher data."""
        root = Path(game_root).resolve()
        self._preflight(root)

        with self._lock(root):
            self._emit(event_cb, operation_id, OperationPhase.ROLLBACK, "Đang chuẩn bị khôi phục dữ liệu gốc từ nhà phát hành...", 0, 5)

            persistent = root / "Persistent_Store"
            streaming_ir = root / "StellaSora_Data" / "StreamingAssets" / "InstallResource"

            # 1. Restore Tables/data.arcx
            self._emit(event_cb, operation_id, OperationPhase.VERIFY, "Đang kiểm tra bảng dữ liệu gốc (data.arcx)...", 1, 5)
            data_target = persistent / "Tables" / "data.arcx"
            vanilla_data = self._find_vanilla_archive(root, "Tables", "data.arcx")

            if vanilla_data and vanilla_data.is_file():
                data_target.parent.mkdir(parents=True, exist_ok=True)
                tmp = data_target.with_name(f".restore_{uuid.uuid4().hex}")
                try:
                    shutil.copy2(vanilla_data, tmp)
                    os.replace(tmp, data_target)
                finally:
                    tmp.unlink(missing_ok=True)
                # Keep local orig_en preserved as golden backup
                local_orig_data = data_target.with_name("data.arcx.orig_en")
                if not local_orig_data.exists():
                    try:
                        shutil.copy2(vanilla_data, local_orig_data)
                    except Exception:
                        pass

            # 2. Restore Scripts/lua.arcx
            self._emit(event_cb, operation_id, OperationPhase.VERIFY, "Đang kiểm tra kịch bản gốc (lua.arcx)...", 2, 5)
            lua_target = persistent / "Scripts" / "lua.arcx"
            vanilla_lua = self._find_vanilla_archive(root, "Scripts", "lua.arcx")

            if vanilla_lua and vanilla_lua.is_file():
                lua_target.parent.mkdir(parents=True, exist_ok=True)
                tmp = lua_target.with_name(f".restore_{uuid.uuid4().hex}")
                try:
                    shutil.copy2(vanilla_lua, tmp)
                    os.replace(tmp, lua_target)
                finally:
                    tmp.unlink(missing_ok=True)
                # Keep local orig_en preserved as golden backup
                local_orig_lua = lua_target.with_name("lua.arcx.orig_en")
                if not local_orig_lua.exists():
                    try:
                        shutil.copy2(vanilla_lua, local_orig_lua)
                    except Exception:
                        pass

            # 3. Restore / Revert AssetBundles in Persistent_Store/AssetBundles/
            self._emit(event_cb, operation_id, OperationPhase.APPLY, "Đang phục hồi AssetBundles về bản gốc nhà phát hành...", 3, 5)
            ps_bundles = persistent / "AssetBundles"
            cleaned_bundles = 0
            if ps_bundles.is_dir():
                for bpath in list(ps_bundles.glob("*.en.unity3d")):
                    bname = bpath.name
                    ir_source = streaming_ir / bname
                    if ir_source.is_file():
                        # Restore clean pristine version from InstallResource
                        shutil.copy2(ir_source, bpath)
                        cleaned_bundles += 1
                    else:
                        # Remove modded bundle so game client fetches or falls back cleanly
                        bpath.unlink(missing_ok=True)
                        cleaned_bundles += 1

            # 4. Clean Vietnamese Subtitles in Persistent_Store/Videos/
            self._emit(event_cb, operation_id, OperationPhase.APPLY, "Đang dọn dẹp phụ đề tiếng Việt...", 4, 5)
            ps_videos = persistent / "Videos"
            cleaned_srts = 0
            if ps_videos.is_dir():
                for srt in list(ps_videos.glob("*.srt")):
                    srt.unlink(missing_ok=True)
                    cleaned_srts += 1

            # 5. Remove receipt and cleanup temporary journals/files
            self._emit(event_cb, operation_id, OperationPhase.READBACK, "Đang dọn dẹp biên bản cài đặt...", 5, 5)
            (root / RECEIPT).unlink(missing_ok=True)
            (root / "viethoa_installed.json").unlink(missing_ok=True)

            # Clean any pending journals for this root
            for jf in self.journals_dir.glob("*.json"):
                try:
                    d = json.loads(jf.read_text(encoding="utf8"))
                    if d.get("game_root") == canonicalize_path(root):
                        d["state"] = "restored"
                        jf.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf8")
                except Exception:
                    pass

            self._emit(
                event_cb,
                operation_id,
                OperationPhase.DONE,
                "✓ Đã khôi phục hoàn toàn dữ liệu gốc nguyên bản của nhà phát hành.",
                5,
                5
            )

            return {
                "status": "success",
                "restored_tables": bool(vanilla_data and vanilla_data.is_file()),
                "restored_scripts": bool(vanilla_lua and vanilla_lua.is_file()),
                "cleaned_bundles_count": cleaned_bundles,
                "cleaned_subtitles_count": cleaned_srts,
                "message": "✓ Hoàn tất khôi phục! Đã đưa toàn bộ dữ liệu game về trạng thái gốc nguyên bản từ nhà phát hành (bản hoàn chỉnh, chưa Việt hoá)."
            }
