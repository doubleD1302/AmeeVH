# -*- coding: utf-8 -*-
"""Restore the game to FRESH OFFICIAL publisher data, downloaded from the official server.

Why this exists: the old "Khôi phục" copied *.orig_en / launcher backups. Those can be stale
(an old game version) or may themselves be Vietnamese. This engine never reads them. Instead it:

 1. asks the official resource server which files/versions exist (OfficialClient),
 2. decides the target official version (see `prefer`),
 3. reuses a local file only when its MD5 equals the official MD5 (e.g. StreamingAssets/InstallResource),
    otherwise downloads (full file or base + BSDIFF delta chain) into a cache and verifies every MD5,
 4. stages verified copies next to the targets, backs up what it replaces, swaps atomically and
    reads everything back; any failure rolls the already-swapped files back,
 5. removes the Vietnamese receipt and records the state in Persistent_Store/viethoa_installed.json.

Nothing in the game folder is modified before every replacement has been downloaded and verified.

`prefer`:
  "game"   (default) target the official version the game itself recorded in Persistent_Store/ss_win.mani.
           This is what the game's own updater expects, so it can patch/update normally afterwards.
           Equal to the newest server version whenever the game is up to date.
  "latest" target the newest version published by the server (used when ss_win.mani is missing/unreadable).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from .game_detection import canonicalize_path, is_game_process_running, read_game_versions, read_official_state  # noqa: F401
from .installer import TERMINAL_JOURNAL_STATES, PatchInstaller
from .official_resources import (
    TEXT_ARCHIVES,
    CancelledError,
    OfficialCatalog,
    OfficialClient,
    OfficialDownloader,
    OfficialResourceError,
    md5_file,
    official_relative_path,
    parse_manifest,
)
from .safety import InstallerError, atomic_json, safe_official_path, safe_path
from .types import OperationEvent, OperationPhase

RECEIPT = ".vietnamese_patch_receipt.json"
STATE_FILE = "viethoa_installed.json"
SAFETY_MARGIN = 256 * 1024 * 1024
_BUNDLE_RE = re.compile(r"Persistent_Store/AssetBundles/[A-Za-z0-9_.-]+[.]en[.]unity3d")
_SRT_RE = re.compile(r'Persistent_Store/Videos/[^/<>:"|?*]+[.]srt')


def _is_reparse_or_symlink(path: Path) -> bool:
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        return True
    try:
        return bool(path.lstat().st_file_attributes & 0x400)
    except (OSError, AttributeError):
        return False


def _fallback_version_parts(v) -> Optional[tuple[int, int, int, int]]:
    m = re.fullmatch(r"v?(\d+(?:\.\d+){0,3})", str(v or "").strip(), re.I)
    if not m:
        return None
    parts = tuple(int(p) for p in m.group(1).split("."))
    return parts + (0,) * (4 - len(parts))


def _fallback_newer(a, b) -> bool:
    pa, pb = _fallback_version_parts(a), _fallback_version_parts(b)
    return bool(pa and pb and pa > pb)


def _newer(a, b) -> bool:
    try:
        from .update_notice import newer as _update_notice_newer
    except ModuleNotFoundError as exc:
        expected = f"{__package__}.update_notice" if __package__ else "update_notice"
        if exc.name in (expected, "update_notice"):
            return _fallback_newer(a, b)
        raise
    return _update_notice_newer(a, b)


@dataclass
class Target:
    rel: str                 # Persistent_Store/...
    name: str
    path: Path
    action: str              # keep | replace | delete
    checksum: Optional[str] = None
    size: int = 0
    source: str = ""         # install_resource | download | ""
    local_source: Optional[Path] = None
    item: Optional[dict] = None
    current_md5: Optional[str] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_local_manifest(root: Path) -> Optional[tuple[dict, dict]]:
    """(headers, files) of the game's Persistent_Store manifest (merging ss_win_add & p_N_m if present)."""
    ps = Path(root) / "Persistent_Store"
    mf = ps / "ss_win.mani"
    try:
        if not mf.is_file() or _is_reparse_or_symlink(mf) or mf.stat().st_size > 32 * 1024 * 1024:
            return None
        headers, files, _patches = parse_manifest(mf.read_bytes())
    except (OSError, OfficialResourceError):
        return None
    if not headers.get("RES_VER") or not files:
        return None
    merged_headers = dict(headers)
    merged_files = dict(files)
    add_mf = ps / "ss_win_add.mani"
    try:
        if add_mf.is_file() and not _is_reparse_or_symlink(add_mf) and add_mf.stat().st_size <= 32 * 1024 * 1024:
            _ah, afiles, _ap = parse_manifest(add_mf.read_bytes())
            merged_files.update(afiles)
    except (OSError, OfficialResourceError):
        pass
    patch_ver_raw = str(headers.get("BIN_DIFF_PATCH_VER") or "").strip()
    if patch_ver_raw.isdigit() and int(patch_ver_raw) > 0:
        pmf = ps / f"p_{int(patch_ver_raw)}_m.ss_win.mani"
        try:
            if pmf.is_file() and not _is_reparse_or_symlink(pmf) and pmf.stat().st_size <= 32 * 1024 * 1024:
                pheaders, pfiles, _pp = parse_manifest(pmf.read_bytes())
                merged_files.update(pfiles)
                for key in ("RES_VER", "GAME_VER", "CLIENT_VER"):
                    if pheaders.get(key):
                        merged_headers[key] = pheaders[key]
        except (OSError, OfficialResourceError):
            pass
    return merged_headers, merged_files


def cleanup_game_patch_caches(root: Path) -> int:
    """Remove stale partial patch files in Temporary_Store/ and Patch_Store/ (preserving folder layout).

    Stella Sora's DownloadStore stages BinDiff deltas under Temporary_Store/PatchTemp/ and
    Temporary_Store/. After an aborted update ("Patch file verification failed"), stale partial
    files there can keep breaking verification even after Persistent_Store/ is restored cleanly.
    Never follows symlinks/junctions/reparse points.
    """
    resolved_root = Path(root).resolve()
    removed = 0
    for folder_name in ("Temporary_Store", "Patch_Store"):
        try:
            store_dir = safe_path(resolved_root, folder_name, False)
        except InstallerError:
            continue
        if not store_dir.is_dir() or _is_reparse_or_symlink(store_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(store_dir, topdown=True, followlinks=False):
            cur = Path(dirpath)
            if _is_reparse_or_symlink(cur):
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not _is_reparse_or_symlink(cur / d)]
            for fname in filenames:
                candidate = cur / fname
                if _is_reparse_or_symlink(candidate):
                    continue
                try:
                    rel = candidate.relative_to(resolved_root).as_posix()
                    safe_cand = safe_path(resolved_root, rel, False)
                    safe_cand.unlink(missing_ok=True)
                    removed += 1
                except (ValueError, InstallerError, OSError):
                    continue
    return removed


class OfficialRestoreEngine:
    def __init__(
        self,
        backup_root: Path | str,
        journals_dir: Path | str,
        cache_dir: Path | str,
        client: Optional[OfficialClient] = None,
    ):
        self.backup_root = Path(backup_root)
        self.journals_dir = Path(journals_dir)
        self.cache_dir = Path(cache_dir)
        self.client = client or OfficialClient("EN")
        self.installer = PatchInstaller(self.backup_root, self.journals_dir)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _emit(cb, op, phase, msg, n=0, total=0, unit="items"):
        if cb:
            cb(OperationEvent(op, phase, msg, n, total, unit))

    def _preflight(self, root: Path):
        if not root.is_dir() or not (root / "StellaSora.exe").is_file():
            raise InstallerError("Hãy chọn đúng thư mục có StellaSora.exe.", "INVALID_ROOT")
        if is_game_process_running():
            raise InstallerError("Hãy đóng game trước khi khôi phục dữ liệu.", "GAME_RUNNING")

    def _candidates(self, root: Path) -> tuple[list[tuple[str, bool]], Optional[dict]]:
        """[(rel, from_receipt)] files the Vietnamese package may have changed + the receipt (if valid)."""
        rels: dict[str, bool] = {
            "Persistent_Store/Tables/data.arcx": True,
            "Persistent_Store/Scripts/lua.arcx": True,
        }
        receipt = None
        rp = root / RECEIPT
        if rp.is_file():
            try:
                r = json.loads(rp.read_text(encoding="utf8"))
                if isinstance(r, dict) and isinstance(r.get("files"), dict):
                    receipt = r
            except (OSError, ValueError):
                receipt = None
        if receipt:
            for rel in receipt["files"]:
                try:
                    safe_path(root, rel, True)
                except InstallerError:
                    continue  # never touch anything outside the allow-list
                rels[rel] = True
        # Always scan allow-listed AssetBundles (*.en.unity3d) and Videos (*.srt), even when a
        # receipt exists: an outdated or partial receipt (e.g. from an older translation version or
        # a script/manual deployment) can omit patched bundles or subtitles, leaving modified files
        # behind that break the game's delta updater ("Patch file verification failed").
        scan_specs = (
            (root / "Persistent_Store" / "AssetBundles", "Persistent_Store/AssetBundles/", "*.en.unity3d", _BUNDLE_RE),
            (root / "Persistent_Store" / "Videos", "Persistent_Store/Videos/", "*.srt", _SRT_RE),
        )
        for directory, prefix, pattern, regex in scan_specs:
            if not directory.is_dir() or _is_reparse_or_symlink(directory):
                continue
            for p in sorted(directory.glob(pattern), key=lambda x: x.name):
                if not p.is_file() or _is_reparse_or_symlink(p):
                    continue
                rel = prefix + p.name
                if not regex.fullmatch(rel):
                    continue
                try:
                    safe_path(root, rel, True)
                except InstallerError:
                    continue
                rels.setdefault(rel, False)
        return list(rels.items()), receipt

    def _find_verified_local_backup(self, root: Path, rel: str, expected_size: int, expected_md5: str) -> Optional[Path]:
        """Search launcher backups and *.orig_en for an EXACT size+MD5 match to Yostar's local manifest.

        Because we require an exact 128-bit MD5 match against ss_win.mani, contaminated or stale
        backups can never be chosen; this safely rescues older game versions rotated off Yostar CDN.
        """
        candidates: list[Path] = []
        try:
            broot = self.installer.get_backup_dir_for_root(root)
            if broot.is_dir() and not _is_reparse_or_symlink(broot):
                bdirs = sorted(
                    (d for d in broot.glob("backup_*") if d.is_dir() and not _is_reparse_or_symlink(d)),
                    key=lambda d: d.name,
                    reverse=True,
                )
                for bd in bdirs:
                    candidates.append(bd / rel)
        except OSError:
            pass
        try:
            orig = safe_path(root, rel + ".orig_en", False)
            candidates.append(orig)
        except InstallerError:
            pass
        for cand in candidates:
            try:
                if _is_reparse_or_symlink(cand) or not cand.is_file():
                    continue
                if cand.stat().st_size == expected_size and md5_file(cand) == expected_md5:
                    return cand
            except OSError:
                continue
        return None

    def _plan(self, root: Path, catalog: OfficialCatalog, prefer: str, cb, op) -> tuple[list[Target], dict]:
        local = read_local_manifest(root) if prefer == "game" else None
        mode = "game" if local else "latest"
        local_files = local[1] if local else {}
        local_res = local[0].get("RES_VER") if local else None
        cands, receipt = self._candidates(root)
        streaming = root / "StellaSora_Data" / "StreamingAssets" / "InstallResource"
        pending_patch_repairs: set[str] = set()
        if mode == "game":
            seen = {rel for rel, _ in cands}
            # 1) Check missing *.en.unity3d / *.srt files declared in local ss_win.mani
            for name, rec in sorted(local_files.items()):
                rel = "Persistent_Store/" + official_relative_path(name)
                if rel in seen:
                    continue
                if not (_BUNDLE_RE.fullmatch(rel) or _SRT_RE.fullmatch(rel)):
                    continue
                try:
                    path = safe_official_path(root, rel)
                except InstallerError:
                    continue
                if path.exists():
                    continue
                rec_checksum = rec["checksum"]
                rec_size = int(rec["size"])
                # Missing from Persistent_Store: if StreamingAssets/InstallResource already provides
                # the exact official file, the game loads it from there without needing a copy.
                cand = streaming / name
                try:
                    if not _is_reparse_or_symlink(cand) and cand.is_file() and cand.stat().st_size == rec_size and md5_file(cand) == rec_checksum:
                        continue
                except OSError:
                    pass
                if not catalog.knows(name, rec_checksum) and self._find_verified_local_backup(root, rel, rec_size, rec_checksum) is None:
                    continue
                seen.add(rel)
                cands.append((rel, False))

            # 2) Audit EVERY file targeted by pending CDN BinDiff patches (p_k newer than local_res),
            # including non-.en bundles & hotfix.arch! A prior aborted BinDiffPatch can leave 40+
            # non-.en bundles half-patched, corrupted, stale-overridden, or deleted while ss_win.mani
            # remains on the older RES_VER, causing repeat "Patch file verification failed" errors.
            pending_names = catalog.pending_patch_names(local_res)
            for name in sorted(pending_names):
                rec = local_files.get(name)
                if rec is None:
                    continue  # brand-new file added in a newer patch step (not expected on local_res)
                rel = "Persistent_Store/" + official_relative_path(name)
                if rel in seen:
                    continue
                try:
                    path = safe_official_path(root, rel)
                except InstallerError:
                    continue
                rec_checksum = rec["checksum"]
                rec_size = int(rec["size"])
                needs_repair = False
                if path.is_file():
                    try:
                        if path.stat().st_size != rec_size or md5_file(path) != rec_checksum:
                            needs_repair = True
                    except OSError:
                        needs_repair = True
                else:
                    cand = streaming / name
                    try:
                        ir_ok = not _is_reparse_or_symlink(cand) and cand.is_file() and cand.stat().st_size == rec_size and md5_file(cand) == rec_checksum
                    except OSError:
                        ir_ok = False
                    if not ir_ok:
                        needs_repair = True
                if needs_repair:
                    seen.add(rel)
                    cands.append((rel, False))
                    pending_patch_repairs.add(name)
        targets: list[Target] = []
        total = len(cands)
        for index, (rel, from_receipt) in enumerate(cands, 1):
            self._emit(cb, op, OperationPhase.VERIFY, f"Đang đối chiếu với bản gốc: {Path(rel).name}", index, total)
            path = safe_official_path(root, rel)
            name = path.name
            record = (local_files if mode == "game" else catalog.final_files).get(name)
            if record is None:
                # Not an official file for this version: a Vietnamese-only addition.
                if from_receipt and name not in TEXT_ARCHIVES and path.is_file():
                    targets.append(Target(rel, name, path, "delete"))
                elif name in TEXT_ARCHIVES:
                    raise OfficialResourceError(f"Manifest chính thức không có {name}.", "NOT_FOUND")
                continue
            checksum = record["checksum"]
            size = int(record["size"])
            current = None
            if path.is_file():
                try:
                    if path.stat().st_size == size:
                        current = md5_file(path)
                except OSError:
                    current = None
            t = Target(rel, name, path, "keep" if current == checksum else "replace", checksum, size, current_md5=current)
            if t.action == "replace":
                cand = streaming / name
                try:
                    if not _is_reparse_or_symlink(cand) and cand.is_file() and cand.stat().st_size == size and md5_file(cand) == checksum:
                        t.source, t.local_source = "install_resource", cand
                except OSError:
                    pass
                if not t.source:
                    if catalog.knows(name, checksum):
                        t.source, t.item = "download", catalog.resolve(name, checksum)
                    else:
                        local_bak = self._find_verified_local_backup(root, rel, size, checksum)
                        if local_bak is not None:
                            t.source, t.local_source = "local_verified_backup", local_bak
                        else:
                            raise OfficialResourceError(
                                f"Máy chủ chính thức không có phiên bản {name} mà game đang ghi nhận ({checksum[:8]}…). "
                                "Hãy dùng chức năng Kiểm tra/Sửa tệp của Yostar Launcher hoặc Steam cho bản cài này.",
                                "NOT_FOUND",
                            )
            targets.append(t)
        info = {
            "mode": mode,
            "target_resource_version": local_res if mode == "game" else catalog.resource_version,
            "target_game_version": (local[0].get("GAME_VER") if local else None) or catalog.game_version,
            "latest_resource_version": catalog.resource_version,
            "latest_game_version": catalog.game_version,
            "had_receipt": receipt is not None,
            "repaired_pending_patch_files": sorted(pending_patch_repairs),
        }
        return targets, info

    # ------------------------------------------------------------------ public API
    def restore(
        self,
        game_root: str | Path,
        event_cb: Optional[Callable[[OperationEvent], None]] = None,
        operation_id: str = "official_restore",
        prefer: str = "game",
        dry_run: bool = False,
        should_cancel: Optional[Callable[[], bool]] = None,
    ) -> dict:
        root = Path(game_root).resolve()
        self._preflight(root)
        emit = lambda phase, msg, n=0, t=0, unit="items": self._emit(event_cb, operation_id, phase, msg, n, t, unit)
        with self.installer._lock(root):
            self._recover_interrupted(root)
            if should_cancel and should_cancel():
                raise CancelledError("Đã huỷ khôi phục tài nguyên.", "CANCELLED")
            emit(OperationPhase.PREFLIGHT, "Đang hỏi máy chủ chính thức phiên bản tài nguyên mới nhất…", 0, 1)
            catalog = self.client.fetch_catalog()
            targets, info = self._plan(root, catalog, prefer, event_cb, operation_id)
            todo = [t for t in targets if t.action in ("replace", "delete")]
            downloader = OfficialDownloader(
                self.client,
                self.cache_dir,
                should_cancel=should_cancel,
                max_workers=4,
                event_cb=event_cb,
                operation_id=operation_id,
            )
            items = [t.item for t in todo if t.item]
            need_bytes = downloader.estimate_download(items)
            write_bytes = sum(t.size for t in todo if t.action == "replace")
            summary = {
                "status": "dry_run" if dry_run else "success",
                **info,
                "server_data_version": catalog.server_data_version,
                "manifest_sha256": catalog.manifest_sha256,
                "already_official": [t.name for t in targets if t.action == "keep"],
                "to_replace": [t.name for t in targets if t.action == "replace"],
                "to_delete": [t.name for t in targets if t.action == "delete"],
                "from_install_resource": [t.name for t in targets if t.source == "install_resource"],
                "download_bytes": need_bytes,
                "write_bytes": write_bytes,
            }
            if dry_run:
                summary["message"] = f"Chạy thử: cần thay {len(summary['to_replace'])} tệp, xoá {len(summary['to_delete'])}, tải ~{need_bytes / 1048576:.0f} MB."
                return summary

            # --- space checks (game untouched so far) ---
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            biggest = max([t.size for t in todo if t.size] or [0])
            if shutil.disk_usage(self.cache_dir).free < need_bytes + 3 * biggest + SAFETY_MARGIN:
                raise InstallerError("Ổ đĩa chứa bộ nhớ đệm launcher không đủ dung lượng để tải bản gốc.", "DISK_FULL")
            if shutil.disk_usage(root).free < write_bytes + SAFETY_MARGIN:
                raise InstallerError("Ổ đĩa chứa game không đủ dung lượng để thay tệp.", "DISK_FULL")

            # --- download + verify everything first ---
            sources: dict[str, Path] = {}
            if items:
                emit(OperationPhase.DOWNLOAD, "Đang tải tài nguyên gốc từ máy chủ chính thức…", 0, max(need_bytes, 1), "bytes")
                try:
                    cached = downloader.prepare(items)
                except CancelledError:
                    raise
                for t in todo:
                    if t.item:
                        sources[t.rel] = cached[t.item["checksum"]]
            for t in todo:
                if t.local_source:
                    sources[t.rel] = t.local_source

            if should_cancel and should_cancel():
                raise CancelledError("Đã huỷ khôi phục tài nguyên.", "CANCELLED")

            replaced = self._apply(root, todo, sources, event_cb, operation_id)
            cleaned_temp_files = cleanup_game_patch_caches(root)
            self._cleanup_stale_official_temps(root)
            self._finish_state(root, catalog, info, targets, replaced)
            downloader.cleanup()  # verified bytes are installed; free the cache disk space

            names = [t.name for t in todo if t.action == "replace"]
            extra_notes = []
            if cleaned_temp_files:
                extra_notes.append(f"dọn {cleaned_temp_files} tệp tạm cập nhật")
            if info.get("repaired_pending_patch_files"):
                extra_notes.append(f"vá {len(info['repaired_pending_patch_files'])} tệp hệ thống lệch bản vá")
            extra_suffix = (" (" + ", ".join(extra_notes) + ")") if extra_notes else ""
            msg = (
                f"✓ Đã tải và cài tài nguyên gốc của nhà phát hành (tài nguyên {info['target_resource_version']}): "
                f"{len(names)} tệp được thay, {len(summary['already_official'])} tệp đã đúng bản gốc, "
                f"{len(summary['to_delete'])} tệp Việt hoá riêng được gỡ{extra_suffix}."
            )
            if info["mode"] == "game" and info["target_resource_version"] != info["latest_resource_version"]:
                msg += (
                    f"\nMáy chủ đã có bản {info['latest_resource_version']}: hãy mở game (hoặc Yostar Launcher) để game tự cập nhật."
                )
            summary.update(
                message=msg,
                replaced=names,
                downloaded_bytes=downloader.downloaded_bytes,
                cleaned_temp_files=cleaned_temp_files,
            )
            emit(OperationPhase.DONE, msg, 1, 1)
            return summary

    # ------------------------------------------------------------------ transaction
    def _apply(self, root: Path, todo: list[Target], sources: dict[str, Path], cb, op) -> list[str]:
        if not todo:
            return []
        bdir = self.installer.get_backup_dir_for_root(root) / f"official_restore_{time.strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"
        bdir.mkdir(parents=True)
        journal = bdir / "journal.json"
        entries = {t.rel: {"action": t.action, "swapped": False, "had_original": t.path.is_file()} for t in todo}
        atomic_json(journal, {"game_root": canonicalize_path(root), "state": "staging", "files": entries})
        staged: dict[str, Path] = {}
        swapped: list[Target] = []
        try:
            # Phase A: stage + verify next to the targets. Failure here leaves the game untouched.
            total = len(todo)
            for i, t in enumerate(todo, 1):
                if t.action != "replace":
                    continue
                self._emit(cb, op, OperationPhase.APPLY, f"Đang chuẩn bị tệp: {t.name}", i, total)
                t.path.parent.mkdir(parents=True, exist_ok=True)
                tmp = t.path.with_name(f".official_{uuid.uuid4().hex}")
                staged[t.rel] = tmp
                shutil.copyfile(sources[t.rel], tmp)
                if tmp.stat().st_size != t.size or md5_file(tmp) != t.checksum:
                    raise InstallerError(f"Bản sao tạm của {t.name} sai MD5.", "STAGE_VERIFY_FAILED")
            # Phase B: backup the current file and swap.
            atomic_json(journal, {"game_root": canonicalize_path(root), "state": "applying", "files": entries})
            for i, t in enumerate(todo, 1):
                self._emit(cb, op, OperationPhase.BACKUP if i == 1 else OperationPhase.APPLY, f"Đang thay bằng bản gốc: {t.name}", i, total)
                backup = bdir / t.rel
                if t.path.exists():
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(t.path), str(backup))
                entries[t.rel]["swapped"] = True
                atomic_json(journal, {"game_root": canonicalize_path(root), "state": "applying", "files": entries})
                swapped.append(t)
                if t.action == "replace":
                    os.replace(staged[t.rel], t.path)
                    staged.pop(t.rel)
            # Phase C: read back.
            for i, t in enumerate(todo, 1):
                if t.action == "replace":
                    self._emit(cb, op, OperationPhase.READBACK, f"Đang đọc lại để kiểm tra: {t.name}", i, total)
                    if not t.path.is_file() or t.path.stat().st_size != t.size or md5_file(t.path) != t.checksum:
                        raise InstallerError(f"Đọc lại {t.name} thất bại sau khi thay.", "READBACK_FAILED")
                elif t.path.exists():
                    raise InstallerError(f"Không gỡ được {t.name}.", "READBACK_FAILED")
        except BaseException:
            for tmp in staged.values():
                tmp.unlink(missing_ok=True)
            self._rollback_swapped(swapped, bdir)
            atomic_json(journal, {"game_root": canonicalize_path(root), "state": "rolled_back", "files": entries})
            raise
        atomic_json(journal, {"game_root": canonicalize_path(root), "state": "done", "files": entries})
        shutil.rmtree(bdir, ignore_errors=True)  # Vietnamese copies are reinstallable; no need to keep them
        return [t.name for t in todo]

    @staticmethod
    def _rollback_swapped(swapped: list[Target], bdir: Path):
        for t in reversed(swapped):
            backup = bdir / t.rel
            try:
                if backup.exists():
                    if t.path.exists():
                        t.path.unlink()
                    shutil.move(str(backup), str(t.path))
                elif t.action == "replace" and t.path.exists():
                    t.path.unlink()  # file did not exist before
            except OSError:
                pass

    def _recover_interrupted(self, root: Path):
        """If a previous run died mid-swap, put the moved-away originals back."""
        base = self.installer.get_backup_dir_for_root(root)
        croot = canonicalize_path(root)
        for jf in base.glob("official_restore_*/journal.json"):
            try:
                j = json.loads(jf.read_text(encoding="utf8"))
            except (OSError, ValueError):
                continue
            if not isinstance(j, dict) or j.get("game_root") != croot or j.get("state") not in ("staging", "applying"):
                continue
            bdir = jf.parent
            for rel, e in (j.get("files") or {}).items():
                if not isinstance(e, dict):
                    continue
                try:
                    target = safe_official_path(root, rel)
                    backup = safe_path(bdir, rel)
                except InstallerError:
                    continue
                if e.get("swapped") and backup.is_file():
                    if target.exists():
                        target.unlink()
                    shutil.move(str(backup), str(target))
            j["state"] = "rolled_back"
            atomic_json(jf, j)
            self._cleanup_stale_official_temps(root)

    @staticmethod
    def _cleanup_stale_official_temps(root: Path) -> None:
        resolved_root = root.resolve()
        try:
            ps_dir = safe_path(resolved_root, "Persistent_Store", False)
        except InstallerError:
            return
        if not ps_dir.is_dir() or _is_reparse_or_symlink(ps_dir):
            return
        for dirpath, dirnames, filenames in os.walk(ps_dir, topdown=True, followlinks=False):
            cur = Path(dirpath)
            if _is_reparse_or_symlink(cur):
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not _is_reparse_or_symlink(cur / d)]
            for fname in filenames:
                if not fname.startswith(".official_"):
                    continue
                candidate = cur / fname
                if _is_reparse_or_symlink(candidate):
                    continue
                try:
                    rel = candidate.relative_to(resolved_root).as_posix()
                    safe_candidate = safe_path(resolved_root, rel, False)
                except (ValueError, InstallerError):
                    continue
                try:
                    safe_candidate.unlink(missing_ok=True)
                except OSError:
                    pass

    # ------------------------------------------------------------------ state
    def _finish_state(self, root: Path, catalog: OfficialCatalog, info: dict, targets: list[Target], replaced: list[str]):
        (root / RECEIPT).unlink(missing_ok=True)
        (root / STATE_FILE).unlink(missing_ok=True)  # legacy location
        ps = root / "Persistent_Store"
        ps.mkdir(parents=True, exist_ok=True)
        versions = read_game_versions(root)
        atomic_json(
            ps / STATE_FILE,
            {
                "status": "official_restored",
                "vietnamese_installed": False,
                "restored_at": _now(),
                "source": "launcher_official_restore",
                "official_resource_version": info["target_resource_version"],
                "official_game_version": info["target_game_version"],
                "latest_server_resource_version": info["latest_resource_version"],
                "manifest_sha256": catalog.manifest_sha256,
                "mode": info["mode"],
                "game_manifest_version": versions.get("resource"),
                "files": {t.rel: {"md5": t.checksum} for t in targets if t.checksum},
                "removed": [t.rel for t in targets if t.action == "delete"],
            },
        )
        croot = canonicalize_path(root)
        for jf in self.journals_dir.glob("*.json"):
            try:
                d = json.loads(jf.read_text(encoding="utf8"))
                if isinstance(d, dict) and d.get("game_root") == croot and d.get("state") not in TERMINAL_JOURNAL_STATES:
                    d["state"] = "restored"
                    atomic_json(jf, d)
            except (OSError, ValueError):
                pass


# ---------------------------------------------------------------------- update detection
def _digits(value) -> Optional[int]:
    s = str(value or "").strip()
    return int(s) if s.isdigit() else None


def check_official_update(
    client: OfficialClient,
    game_info,
    cache_file: Optional[Path] = None,
) -> dict:
    """Compare the game's recorded official version with what the official server publishes now.

    Cheap in the common case: only the 432-byte serverlist is fetched; the full catalog is read
    again only when the server's data version changed (result cached in `cache_file`).
    Returns a dict with update_available / vh_modified / needs_restore (see keys below).
    """
    cache: dict = {}
    if cache_file and Path(cache_file).is_file():
        try:
            loaded = json.loads(Path(cache_file).read_text(encoding="utf8"))
            if isinstance(loaded, dict):
                cache = loaded
        except (OSError, ValueError):
            cache = {}
    server_version = client.server_data_version()
    if cache.get("server_data_version") == server_version and cache.get("resource_version") and cache.get("region") == client.region:
        latest = {k: cache.get(k) for k in ("resource_version", "game_version", "client_version")}
    else:
        catalog = client.fetch_catalog()
        latest = {"resource_version": catalog.resource_version, "game_version": catalog.game_version, "client_version": catalog.client_version}
        if cache_file:
            try:
                atomic_json(cache_file, {"region": client.region, "server_data_version": catalog.server_data_version, "checked_at": _now(), **latest})
            except OSError:
                pass
    local_res = getattr(game_info, "resource_version", "") or ""
    local_game = getattr(game_info, "version", "") or ""
    new_res, old_res = _digits(latest["resource_version"]), _digits(local_res)
    update_available = bool(new_res and old_res and new_res > old_res)
    if not update_available and latest.get("game_version") and local_game not in ("", "unknown"):
        update_available = _newer(latest["game_version"], local_game)
    vh_modified = bool(getattr(game_info, "installed_receipt", None)) or bool(getattr(game_info, "has_vietnamese", False))
    return {
        "latest_resource_version": latest["resource_version"],
        "latest_game_version": latest["game_version"],
        "local_resource_version": local_res,
        "local_game_version": local_game,
        "update_available": update_available,
        "vh_modified": vh_modified,
        "needs_restore": bool(update_available and vh_modified),
        "server_data_version": server_version,
        "checked_at": _now(),
    }
