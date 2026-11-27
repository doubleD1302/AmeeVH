# -*- coding: utf-8 -*-
"""
Vanilla Restore Engine for Stella Sora.
Restores the game installation to 100% clean, original publisher data (vanilla, unmodded):
1. Restores Tables/data.arcx from clean publisher original (orig_en, unmodded backup, or explicit vanilla_dir).
2. Restores Scripts/lua.arcx from clean publisher original (orig_en, unmodded backup, or explicit vanilla_dir).
3. Restores / cleans modded AssetBundles in Persistent_Store/AssetBundles/ (scoped to receipt files when available so official publisher hotfix bundles remain untouched).
4. Removes Vietnamese subtitle files (*.srt) installed by patch.
5. Removes .vietnamese_patch_receipt.json and marks pending journals restored.
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

from .game_detection import canonicalize_path, is_game_process_running, read_game_versions
from .official_restore import cleanup_game_patch_caches
from .safety import InstallerError, atomic_json, safe_path, sha256_file
from .types import OperationEvent, OperationPhase

RECEIPT = ".vietnamese_patch_receipt.json"


def _atomic_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(f".restore_{uuid.uuid4().hex}")
    try:
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)
    finally:
        tmp.unlink(missing_ok=True)


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
            except OSError as e:
                raise InstallerError("Một thao tác khác đang dùng thư mục game này.", "OPERATION_BUSY") from e
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

    def _known_patched_shas(self, root: Path, rel_key: str) -> set[str]:
        """Collects known modded/Vietnamese SHA256s for rel_key from receipts and journals."""
        shas: set[str] = set()
        croot = canonicalize_path(root)
        rp = root / RECEIPT
        if rp.is_file():
            try:
                r = json.loads(rp.read_text(encoding="utf8"))
                if isinstance(r, dict):
                    entry = (r.get("files") or {}).get(rel_key)
                    if isinstance(entry, dict) and isinstance(entry.get("sha256"), str):
                        shas.add(entry["sha256"].lower())
            except (OSError, ValueError):
                pass
        if self.journals_dir.is_dir():
            for jf in self.journals_dir.glob("*.json"):
                try:
                    jd = json.loads(jf.read_text(encoding="utf8"))
                    if not isinstance(jd, dict) or jd.get("game_root") != croot:
                        continue
                    fentry = (jd.get("files") or {}).get(rel_key)
                    if isinstance(fentry, dict):
                        after = fentry.get("after")
                        if isinstance(after, dict) and isinstance(after.get("sha256"), str):
                            shas.add(after["sha256"].lower())
                    prev_rec = jd.get("previous_receipt")
                    if isinstance(prev_rec, dict):
                        pentry = (prev_rec.get("files") or {}).get(rel_key)
                        if isinstance(pentry, dict) and isinstance(pentry.get("sha256"), str):
                            shas.add(pentry["sha256"].lower())
                except (OSError, ValueError):
                    pass
        return shas

    def _find_unmodded_backup_file(self, root: Path, rel_key: str) -> Optional[Path]:
        """Finds the oldest unmodded backup copy of rel_key, preferring current game_version when available."""
        patched_shas = self._known_patched_shas(root, rel_key)
        current_game_ver = read_game_versions(root).get("game", "unknown")
        root_hash = hashlib.sha256(canonicalize_path(root).encode("utf8")).hexdigest()[:12]
        game_backup_dir = self.backup_root / f"game_{root_hash}"
        if not game_backup_dir.is_dir():
            return None

        def _backup_sort_key(d: Path):
            bm_f = d / "backup_manifest.json"
            if bm_f.is_file():
                try:
                    bm_d = json.loads(bm_f.read_text(encoding="utf8"))
                    if isinstance(bm_d, dict):
                        return (str(bm_d.get("created_at") or ""), d.name)
                except (OSError, ValueError):
                    pass
            return ("", d.name)

        backups = sorted([d for d in game_backup_dir.glob("backup_*") if d.is_dir() and not d.is_symlink()], key=_backup_sort_key)
        matched_ver_cand: Optional[Path] = None
        fallback_cand: Optional[Path] = None

        for b in backups:
            cand = b / rel_key
            if cand.is_symlink() or not cand.is_file() or cand.stat().st_size <= 0:
                continue
            try:
                c_sha = sha256_file(cand).lower()
            except OSError:
                continue
            if c_sha in patched_shas:
                continue

            if fallback_cand is None:
                fallback_cand = cand

            if current_game_ver != "unknown":
                bm_file = b / "backup_manifest.json"
                if bm_file.is_file():
                    try:
                        bm = json.loads(bm_file.read_text(encoding="utf8"))
                        if isinstance(bm, dict) and bm.get("game_version") == current_game_ver:
                            matched_ver_cand = cand
                            break
                    except (OSError, ValueError):
                        pass

        return matched_ver_cand or fallback_cand

    def _find_vanilla_archive(self, root: Path, subpath: str, orig_name: str) -> Optional[Path]:
        """Searches for clean vanilla archive in local game directory, unmodded backups, or explicit vanilla_dir."""
        rel_key = f"Persistent_Store/{subpath}/{orig_name}"
        patched_shas = self._known_patched_shas(root, rel_key)

        # 1. Check local game orig_en (e.g. Tables/data.arcx.orig_en)
        local_orig = root / "Persistent_Store" / subpath / f"{orig_name}.orig_en"
        if not local_orig.is_symlink() and local_orig.is_file() and local_orig.stat().st_size > 0:
            try:
                if sha256_file(local_orig).lower() not in patched_shas:
                    return local_orig
            except OSError:
                pass

        # 2. Check unmodded backups in backup_root for this game
        backup_cand = self._find_unmodded_backup_file(root, rel_key)
        if backup_cand is not None:
            return backup_cand

        # 3. Check explicit vanilla_dir only (never repo dist/vanilla which holds 2.0.0 modded dev snapshots)
        if self.vanilla_dir and self.vanilla_dir.is_dir():
            cand = self.vanilla_dir / f"{orig_name.replace('.arcx', '')}_original_en.arcx"
            if not cand.is_symlink() and cand.is_file():
                return cand
            cand2 = self.vanilla_dir / orig_name
            if not cand2.is_symlink() and cand2.is_file():
                return cand2

        return None

    def restore_vanilla(
        self,
        game_root: str | Path,
        event_cb: Optional[Callable[[OperationEvent], None]] = None,
        operation_id: str = "vanilla_restore",
    ) -> dict:
        """Executes full vanilla recovery to original publisher data."""
        root = Path(game_root).resolve()
        self._preflight(root)

        with self._lock(root):
            self._emit(event_cb, operation_id, OperationPhase.ROLLBACK, "Đang chuẩn bị khôi phục dữ liệu gốc từ nhà phát hành...", 0, 5)

            streaming_ir = root / "StellaSora_Data" / "StreamingAssets" / "InstallResource"

            receipt_data = None
            rp = root / RECEIPT
            if rp.is_file():
                try:
                    receipt_data = json.loads(rp.read_text(encoding="utf8"))
                except (OSError, ValueError):
                    receipt_data = None
            receipt_files = (
                receipt_data.get("files")
                if isinstance(receipt_data, dict) and isinstance(receipt_data.get("files"), dict) and receipt_data.get("files")
                else None
            )

            # 1. Restore Tables/data.arcx
            self._emit(event_cb, operation_id, OperationPhase.VERIFY, "Đang kiểm tra bảng dữ liệu gốc (data.arcx)...", 1, 5)
            data_target = safe_path(root, "Persistent_Store/Tables/data.arcx", True)
            vanilla_data = self._find_vanilla_archive(root, "Tables", "data.arcx")

            if vanilla_data and vanilla_data.is_file():
                _atomic_copy(vanilla_data, data_target)
                local_orig_data = safe_path(root, "Persistent_Store/Tables/data.arcx.orig_en", False)
                if not local_orig_data.exists():
                    try:
                        shutil.copy2(vanilla_data, local_orig_data)
                    except Exception:
                        pass
            elif data_target.is_file():
                data_patched_shas = self._known_patched_shas(root, "Persistent_Store/Tables/data.arcx")
                if data_patched_shas and sha256_file(data_target).lower() in data_patched_shas:
                    raise InstallerError(
                        "Không tìm thấy bản sao lưu dữ liệu gốc (data.arcx) để khôi phục. Hãy dùng tính năng Sửa tệp / Kiểm tra tệp trong Yostar Launcher hoặc Steam.",
                        "BACKUP_MISSING",
                    )

            # 2. Restore Scripts/lua.arcx
            self._emit(event_cb, operation_id, OperationPhase.VERIFY, "Đang kiểm tra kịch bản gốc (lua.arcx)...", 2, 5)
            lua_target = safe_path(root, "Persistent_Store/Scripts/lua.arcx", True)
            vanilla_lua = self._find_vanilla_archive(root, "Scripts", "lua.arcx")

            if vanilla_lua and vanilla_lua.is_file():
                _atomic_copy(vanilla_lua, lua_target)
                local_orig_lua = safe_path(root, "Persistent_Store/Scripts/lua.arcx.orig_en", False)
                if not local_orig_lua.exists():
                    try:
                        shutil.copy2(vanilla_lua, local_orig_lua)
                    except Exception:
                        pass
            elif lua_target.is_file():
                lua_patched_shas = self._known_patched_shas(root, "Persistent_Store/Scripts/lua.arcx")
                if lua_patched_shas and sha256_file(lua_target).lower() in lua_patched_shas:
                    raise InstallerError(
                        "Không tìm thấy bản sao lưu kịch bản gốc (lua.arcx) để khôi phục. Hãy dùng tính năng Sửa tệp / Kiểm tra tệp trong Yostar Launcher hoặc Steam.",
                        "BACKUP_MISSING",
                    )

            # 3. Restore / Revert AssetBundles in Persistent_Store/AssetBundles/
            self._emit(event_cb, operation_id, OperationPhase.APPLY, "Đang phục hồi AssetBundles về bản gốc nhà phát hành...", 3, 5)
            ps_bundles = safe_path(root, "Persistent_Store/AssetBundles", False)
            cleaned_bundles = 0
            if receipt_files is not None:
                for rel in receipt_files:
                    if not rel.startswith("Persistent_Store/AssetBundles/"):
                        continue
                    try:
                        bpath = safe_path(root, rel, True)
                    except InstallerError as exc:
                        if exc.code == "PATH_ESCAPE":
                            raise
                        continue
                    bname = bpath.name
                    backup_bundle = self._find_unmodded_backup_file(root, rel)
                    ir_source = streaming_ir / bname
                    if backup_bundle and backup_bundle.is_file():
                        _atomic_copy(backup_bundle, bpath)
                        cleaned_bundles += 1
                    elif not ir_source.is_symlink() and ir_source.is_file():
                        _atomic_copy(ir_source, bpath)
                        cleaned_bundles += 1
                    elif bpath.exists():
                        bpath.unlink(missing_ok=True)
                        cleaned_bundles += 1
            elif ps_bundles.is_dir():
                for bpath in list(ps_bundles.glob("*.en.unity3d")):
                    bname = bpath.name
                    safe_bpath = safe_path(root, f"Persistent_Store/AssetBundles/{bname}", True)
                    ir_source = streaming_ir / bname
                    if not ir_source.is_symlink() and ir_source.is_file():
                        _atomic_copy(ir_source, safe_bpath)
                        cleaned_bundles += 1
                    else:
                        safe_bpath.unlink(missing_ok=True)
                        cleaned_bundles += 1

            # 4. Clean Vietnamese Subtitles in Persistent_Store/Videos/
            self._emit(event_cb, operation_id, OperationPhase.APPLY, "Đang dọn dẹp phụ đề tiếng Việt...", 4, 5)
            ps_videos = safe_path(root, "Persistent_Store/Videos", False)
            cleaned_srts = 0
            if receipt_files is not None:
                for rel in receipt_files:
                    if not (rel.startswith("Persistent_Store/Videos/") and rel.endswith(".srt")):
                        continue
                    try:
                        srt_path = safe_path(root, rel, True)
                    except InstallerError as exc:
                        if exc.code == "PATH_ESCAPE":
                            raise
                        continue
                    backup_srt = self._find_unmodded_backup_file(root, rel)
                    if backup_srt and backup_srt.is_file():
                        _atomic_copy(backup_srt, srt_path)
                        cleaned_srts += 1
                    elif srt_path.exists():
                        srt_path.unlink(missing_ok=True)
                        cleaned_srts += 1
            elif ps_videos.is_dir():
                for srt in list(ps_videos.glob("*.srt")):
                    safe_srt = safe_path(root, f"Persistent_Store/Videos/{srt.name}", True)
                    safe_srt.unlink(missing_ok=True)
                    cleaned_srts += 1

            # 5. Remove receipt, clear stale Temporary_Store/Patch_Store caches, and cleanup journals
            self._emit(event_cb, operation_id, OperationPhase.READBACK, "Đang dọn dẹp biên bản cài đặt và bộ nhớ tạm cập nhật...", 5, 5)
            cleaned_temp_files = cleanup_game_patch_caches(root)
            rp.unlink(missing_ok=True)
            (root / "viethoa_installed.json").unlink(missing_ok=True)

            croot = canonicalize_path(root)
            for jf in self.journals_dir.glob("*.json"):
                try:
                    d = json.loads(jf.read_text(encoding="utf8"))
                    if isinstance(d, dict) and d.get("game_root") == croot:
                        d["state"] = "restored"
                        atomic_json(jf, d)
                except Exception:
                    pass

            self._emit(
                event_cb,
                operation_id,
                OperationPhase.DONE,
                "✓ Đã khôi phục hoàn toàn dữ liệu gốc nguyên bản của nhà phát hành.",
                5,
                5,
            )

            return {
                "status": "success",
                "restored_tables": bool(vanilla_data and vanilla_data.is_file()),
                "restored_scripts": bool(vanilla_lua and vanilla_lua.is_file()),
                "cleaned_bundles_count": cleaned_bundles,
                "cleaned_subtitles_count": cleaned_srts,
                "cleaned_temp_files": cleaned_temp_files,
                "message": "✓ Hoàn tất khôi phục! Đã đưa toàn bộ dữ liệu game về trạng thái gốc nguyên bản từ nhà phát hành (bản hoàn chỉnh, chưa Việt hoá).",
            }
