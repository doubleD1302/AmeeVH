"""Manifest-bound transaction with preimages, atomic journal and restart recovery."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .game_detection import canonicalize_path, is_game_process_running, read_game_versions
from .safety import InstallerError, atomic_json, manifest_sha256, normalize_manifest, safe_path, sha256_file
from .types import OperationEvent, OperationPhase

RECEIPT = ".vietnamese_patch_receipt.json"
TERMINAL_JOURNAL_STATES = ("done", "rolled_back", "restored", "superseded")


def _fallback_version_parts(value):
    match = re.fullmatch(r"v?(\d+(?:\.\d+){0,3})", str(value or "").strip(), re.I)
    if not match:
        return None
    parts = tuple(int(p) for p in match.group(1).split("."))
    return parts + (0,) * (4 - len(parts))


def version_parts(value):
    try:
        from .update_notice import version_parts as _update_notice_version_parts
    except ModuleNotFoundError as exc:
        expected = f"{__package__}.update_notice" if __package__ else "update_notice"
        if exc.name in (expected, "update_notice"):
            return _fallback_version_parts(value)
        raise
    return _update_notice_version_parts(value)


def state(path):
    return {"exists": True, "sha256": sha256_file(path), "size": path.stat().st_size} if path.is_file() else {"exists": False}


def same(path, expected):
    if expected.get("exists", True):
        return path.is_file() and path.stat().st_size == expected["size"] and sha256_file(path) == expected["sha256"]
    return not path.exists()


class PatchInstaller:
    def __init__(self, backup_root, journals_dir):
        self.backup_root = Path(backup_root)
        self.journals_dir = Path(journals_dir)
        self._last_proc_check = 0.0
        for p in (self.backup_root, self.journals_dir):
            p.mkdir(parents=True, exist_ok=True)

    def _validate_path_security(self, game_root, rel_path):
        return safe_path(game_root, rel_path, True)

    def get_backup_dir_for_root(self, root):
        p = self.backup_root / ("game_" + hashlib.sha256(canonicalize_path(root).encode("utf8")).hexdigest()[:12])
        p.mkdir(parents=True, exist_ok=True)
        return p

    @contextlib.contextmanager
    def _lock(self, root):
        import msvcrt

        p = self.get_backup_dir_for_root(root) / ".operation.lock"
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

    def _preflight(self, root):
        if not root.is_dir() or not (root / "StellaSora.exe").is_file():
            raise InstallerError("Hãy chọn đúng thư mục có StellaSora.exe.", "INVALID_ROOT")
        if is_game_process_running():
            raise InstallerError("Hãy đóng game trước khi thay đổi tài nguyên.", "GAME_RUNNING")
        self._last_proc_check = time.monotonic()

    def _preflight_throttled(self, root, interval: float = 1.0):
        if not root.is_dir() or not (root / "StellaSora.exe").is_file():
            raise InstallerError("Hãy chọn đúng thư mục có StellaSora.exe.", "INVALID_ROOT")
        now = time.monotonic()
        if now - self._last_proc_check >= interval:
            if is_game_process_running():
                raise InstallerError("Hãy đóng game trước khi thay đổi tài nguyên.", "GAME_RUNNING")
            self._last_proc_check = now

    def _emit(self, cb, op, phase, msg, n=0, total=0, receipt=None):
        if cb:
            cb(OperationEvent(op, phase, msg, n, total, receipt=receipt))

    def _replace_patch(self, root, tmp, target, before, after, rel):
        # Windows may report access denied (5) as well as sharing/lock errors
        # for an open destination. Retry briefly without changing ACLs/attributes.
        for attempt in range(3):
            self._preflight_throttled(root)
            if not same(target, before):
                raise InstallerError("Tệp đã đổi trước ghi: " + rel, "PREIMAGE_CONFLICT")
            if not same(tmp, after):
                raise InstallerError("Tệp tạm đã đổi trước ghi: " + rel, "SOURCE_CHANGED")
            try:
                os.replace(tmp, target)
                return
            except OSError as e:
                winerror = getattr(e, "winerror", None)
                if winerror in (5, 32, 33) and attempt < 2:
                    time.sleep((0.2, 0.5)[attempt])
                    continue
                if winerror in (32, 33):
                    raise InstallerError(
                        "Không thể thay " + rel + " vì tệp đang bị chương trình khác sử dụng. Hãy đóng game và trình cập nhật, rồi thử lại.",
                        "FILE_IN_USE",
                    ) from e
                if winerror == 5:
                    raise InstallerError(
                        "Windows từ chối thay " + rel + ". Hãy đóng game và trình cập nhật, kiểm tra thuộc tính chỉ đọc và quyền thay hoặc xóa tệp trong thư mục game; nếu cần, mở launcher bằng quyền quản trị rồi thử lại.",
                        "FILE_ACCESS_DENIED",
                    ) from e
                raise

    def pending(self, root):
        out = []
        croot = canonicalize_path(root)
        for p in self.journals_dir.glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf8"))
                if not isinstance(d, dict):
                    raise InstallerError("Nhật ký bị hỏng; giữ nguyên và kiểm tra thư mục chẩn đoán.", "JOURNAL_CORRUPT")
                if d.get("game_root") == croot and d.get("state") not in TERMINAL_JOURNAL_STATES:
                    out.append((p, d))
            except InstallerError:
                raise
            except (OSError, ValueError) as e:
                raise InstallerError("Nhật ký bị hỏng; giữ nguyên và kiểm tra thư mục chẩn đoán.", "JOURNAL_CORRUPT") from e
        return out

    def _validated_journal_backup(self, root: Path, j: dict) -> Path:
        raw_backup = j.get("backup_dir")
        if not isinstance(raw_backup, str) or not raw_backup.strip():
            raise InstallerError("Backup ngoài vùng gắn với game.", "BACKUP_INVALID")
        backup = Path(raw_backup).resolve()
        game_backup_dir = self.get_backup_dir_for_root(root).resolve()
        if backup == game_backup_dir:
            raise InstallerError("Backup ngoài vùng gắn với game.", "BACKUP_INVALID")
        try:
            backup.relative_to(game_backup_dir)
        except ValueError as e:
            raise InstallerError("Backup ngoài vùng gắn với game.", "BACKUP_INVALID") from e
        return backup

    def _restore_journal(self, root, jfile, j):
        """Strict rollback used inside install() so external destination changes trigger RECOVERY_REQUIRED."""
        if j.get("game_root") != canonicalize_path(root):
            raise InstallerError("Nhật ký không thuộc thư mục game này.", "ROOT_MISMATCH")
        backup = self._validated_journal_backup(root, j)
        for rel, item in j["files"].items():
            target = safe_path(root, rel, True)
            old = item["before"]
            new = item["after"]
            if not same(target, old) and not same(target, new):
                raise InstallerError("Tệp đã đổi sau thao tác; không ghi đè: " + rel, "PREIMAGE_CONFLICT")
            if old["exists"] and not same(safe_path(backup, rel), old):
                raise InstallerError("Backup thiếu/hỏng: " + rel, "BACKUP_CORRUPT")
        j["state"] = "recovering"
        atomic_json(jfile, j)
        for rel, item in j["files"].items():
            target = safe_path(root, rel, True)
            old = item["before"]
            if same(target, old):
                continue
            if not same(target, item["after"]):
                raise InstallerError("Tệp đổi trong lúc khôi phục: " + rel, "PREIMAGE_CONFLICT")
            if old["exists"]:
                target.parent.mkdir(parents=True, exist_ok=True)
                tmp = target.with_name(".restore_" + uuid.uuid4().hex)
                try:
                    shutil.copy2(safe_path(backup, rel), tmp)
                    if not same(tmp, old):
                        raise InstallerError("Bản tạm khôi phục sai hash.", "RESTORE_VERIFY_FAILED")
                    os.replace(tmp, target)
                finally:
                    tmp.unlink(missing_ok=True)
            else:
                target.unlink(missing_ok=True)
            if not same(target, old):
                raise InstallerError("Đọc lại khôi phục thất bại.", "RESTORE_VERIFY_FAILED")
        rp = root / RECEIPT
        previous = j.get("previous_receipt")
        if previous is None:
            rp.unlink(missing_ok=True)
        else:
            atomic_json(rp, previous)
        j["state"] = "rolled_back"
        atomic_json(jfile, j)

    def _recover_journal_superseded_aware(self, root, jfile, j) -> bool:
        """Recovers an interrupted journal cleanly even if Steam/Yostar externally updated some files."""
        if j.get("game_root") != canonicalize_path(root):
            raise InstallerError("Nhật ký không thuộc thư mục game này.", "ROOT_MISMATCH")
        backup = self._validated_journal_backup(root, j)

        has_external_change = False
        for rel, item in j["files"].items():
            target = safe_path(root, rel, True)
            old = item["before"]
            new = item["after"]
            if not same(target, old) and not same(target, new):
                has_external_change = True
            elif same(target, new) and not same(target, old):
                if old["exists"] and not same(safe_path(backup, rel), old):
                    raise InstallerError("Backup thiếu/hỏng: " + rel, "BACKUP_CORRUPT")

        if not has_external_change:
            self._restore_journal(root, jfile, j)
            return False

        # Superseded recovery: restore ONLY files that still match our interrupted `after` state,
        # while preserving all externally updated publisher files untouched.
        j["state"] = "recovering"
        atomic_json(jfile, j)
        for rel, item in j["files"].items():
            target = safe_path(root, rel, True)
            old = item["before"]
            new = item["after"]
            if same(target, old) or not same(target, new):
                continue
            if old["exists"]:
                target.parent.mkdir(parents=True, exist_ok=True)
                tmp = target.with_name(".restore_" + uuid.uuid4().hex)
                try:
                    shutil.copy2(safe_path(backup, rel), tmp)
                    if not same(tmp, old):
                        raise InstallerError("Bản tạm khôi phục sai hash.", "RESTORE_VERIFY_FAILED")
                    os.replace(tmp, target)
                finally:
                    tmp.unlink(missing_ok=True)
            else:
                target.unlink(missing_ok=True)
            if not same(target, old):
                raise InstallerError("Đọc lại khôi phục thất bại.", "RESTORE_VERIFY_FAILED")

        rp = root / RECEIPT
        if j.get("previous_receipt") is None:
            rp.unlink(missing_ok=True)
        j["state"] = "superseded"
        atomic_json(jfile, j)
        return True

    def recover(self, root, event_cb=None, operation_id="recover"):
        root = Path(root).resolve()
        self._preflight(root)
        any_superseded = False
        with self._lock(root):
            entries = self.pending(root)
            for p, j in entries:
                if self._recover_journal_superseded_aware(root, p, j):
                    any_superseded = True
        res = {"status": "recovered", "journals": len(entries)}
        if any_superseded:
            res["superseded"] = True
        return res

    def _prune_backups(self, root: Path, active_backup: Path, current_game_version: str):
        """Keeps active backup, 2 most recent backups, earliest vanilla backup (overall & current game_version), and any pending-journal backups."""
        try:
            bdir = self.get_backup_dir_for_root(root)
            raw_dirs = [d for d in bdir.glob("backup_*") if d.is_dir()]
            if len(raw_dirs) <= 3:
                return

            def _sort_key(d: Path):
                bm_f = d / "backup_manifest.json"
                if bm_f.is_file():
                    try:
                        bm_d = json.loads(bm_f.read_text(encoding="utf8"))
                        if isinstance(bm_d, dict):
                            return (str(bm_d.get("created_at") or ""), d.name)
                    except (OSError, ValueError):
                        pass
                return ("", d.name)

            all_backups = sorted(raw_dirs, key=_sort_key)
            keep = {active_backup.resolve(), all_backups[0].resolve()}
            for recent in all_backups[-2:]:
                keep.add(recent.resolve())

            # Keep earliest backup matching current game_version
            if current_game_version and current_game_version != "unknown":
                for b in all_backups:
                    bm_file = b / "backup_manifest.json"
                    if bm_file.is_file():
                        try:
                            bm = json.loads(bm_file.read_text(encoding="utf8"))
                            if isinstance(bm, dict) and bm.get("game_version") == current_game_version:
                                keep.add(b.resolve())
                                break
                        except (OSError, ValueError):
                            pass

            # Keep any backup referenced by non-terminal journals
            croot = canonicalize_path(root)
            for jf in self.journals_dir.glob("*.json"):
                try:
                    jd = json.loads(jf.read_text(encoding="utf8"))
                    if (
                        isinstance(jd, dict)
                        and jd.get("game_root") == croot
                        and jd.get("state") not in TERMINAL_JOURNAL_STATES
                        and isinstance(jd.get("backup_dir"), str)
                        and jd["backup_dir"].strip()
                    ):
                        keep.add(Path(jd["backup_dir"]).resolve())
                except (OSError, ValueError):
                    pass

            for b in all_backups:
                if b.resolve() not in keep:
                    shutil.rmtree(b, ignore_errors=True)
        except OSError:
            pass

    def _archive_legacy_receipt(self, rp: Path):
        bak = rp.with_name(f".vietnamese_patch_receipt.legacy_{uuid.uuid4().hex[:8]}.bak")
        try:
            os.replace(rp, bak)
        except OSError:
            try:
                shutil.copy2(rp, bak)
                rp.unlink(missing_ok=True)
            except OSError:
                pass

    def install(self, game_root, payload_root, manifest_data=None, operation_id="install", event_cb=None):
        root = Path(game_root).resolve()
        payload = Path(payload_root).resolve()
        emit = lambda ph, msg, n=0, t=0, receipt=None: self._emit(event_cb, operation_id, ph, msg, n, t, receipt)
        emit(OperationPhase.PREFLIGHT, "Đang kiểm tra phiên bản và gói Việt hóa...")
        self._preflight(root)
        with self._lock(root):
            if self.pending(root):
                raise InstallerError("Có thao tác bị ngắt. Chọn Phục hồi thao tác trong Công cụ trước khi cài.", "RECOVERY_REQUIRED")
            if manifest_data is None:
                try:
                    manifest_data = json.loads((payload / "patch_manifest.json").read_text(encoding="utf8"))
                except (OSError, ValueError) as e:
                    raise InstallerError("Không đọc được patch_manifest.json: " + str(e), "MANIFEST_MISSING") from e
            m = normalize_manifest(manifest_data)
            if str(m.get("platform", "windows")).lower() not in ("windows", "win", "pc"):
                raise InstallerError("Gói không dành cho Windows.", "PLATFORM_MISMATCH")
            target_version = version_parts(m["version"])
            if target_version is None:
                raise InstallerError("Phiên bản bản Việt hoá không thể so sánh an toàn.", "VERSION_INVALID")

            croot = canonicalize_path(root)
            rp = root / RECEIPT
            previous = None
            if rp.exists():
                parsed_prev = None
                try:
                    parsed_prev = json.loads(rp.read_text(encoding="utf8"))
                except (ValueError, OSError):
                    parsed_prev = None
                valid_prev = (
                    isinstance(parsed_prev, dict)
                    and parsed_prev.get("schema") == 2
                    and parsed_prev.get("game_root") == croot
                    and isinstance(parsed_prev.get("files"), dict)
                    and bool(parsed_prev["files"])
                    and version_parts(parsed_prev.get("version")) is not None
                )
                if not valid_prev:
                    self._archive_legacy_receipt(rp)
                    previous = None
                else:
                    previous = parsed_prev
                    old_version = version_parts(previous.get("version"))
                    if target_version < old_version:
                        still_installed = all(
                            isinstance(fmeta, dict) and same(safe_path(root, frel, True), {**fmeta, "exists": True})
                            for frel, fmeta in previous["files"].items()
                        )
                        if still_installed:
                            raise InstallerError("Gói cũ hơn phiên bản đã cài; thao tác hạ cấp bị từ chối.", "DOWNGRADE_BLOCKED")

            plan = {}
            total = len(m["files"])
            for i, (rel, meta) in enumerate(m["files"].items()):
                src = safe_path(payload, meta["source"])
                target = safe_path(root, rel, True)
                if not same(src, {**meta, "exists": True}):
                    raise InstallerError("Thiếu hoặc sai hash/kích thước gói: " + meta["source"], "CORRUPT_PAYLOAD")
                plan[rel] = {
                    "before": state(target),
                    "after": {"exists": True, "sha256": meta["sha256"], "size": meta["size"]},
                    "source": meta["source"],
                }
                emit(OperationPhase.VERIFY, src.name, i + 1, total)

            needed = sum(v["before"].get("size", 0) + v["after"]["size"] for v in plan.values()) + 1024 * 1024
            if shutil.disk_usage(root).free < needed or shutil.disk_usage(self.backup_root).free < needed:
                raise InstallerError("Không đủ dung lượng cho bản sao lưu và tệp tạm.", "DISK_FULL")

            gvers = read_game_versions(root)
            bid = "backup_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f") + "_" + uuid.uuid4().hex[:8]
            backup = self.get_backup_dir_for_root(root) / bid
            backup.mkdir()
            for i, (rel, item) in enumerate(plan.items()):
                target = safe_path(root, rel, True)
                if not same(target, item["before"]):
                    raise InstallerError("Game thay đổi trước sao lưu: " + rel, "PREIMAGE_CONFLICT")
                if item["before"]["exists"]:
                    b = safe_path(backup, rel)
                    b.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, b)
                    if not same(b, item["before"]):
                        raise InstallerError("Sao lưu sai hash: " + rel, "BACKUP_CORRUPT")
                emit(OperationPhase.BACKUP, target.name, i + 1, total)

            bm = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "game_root": croot,
                "game_version": gvers["game"],
                "resource_version": gvers["resource"],
                "files": {r: v["before"] for r, v in plan.items()},
            }
            atomic_json(backup / "backup_manifest.json", bm)

            jid = uuid.uuid4().hex
            jfile = self.journals_dir / (jid + ".json")
            j = {
                "schema": 2,
                "id": jid,
                "game_root": croot,
                "backup_dir": str(backup),
                "files": plan,
                "previous_receipt": previous,
                "state": "prepared",
            }
            atomic_json(jfile, j)
            try:
                for i, (rel, item) in enumerate(plan.items()):
                    self._preflight_throttled(root)
                    target = safe_path(root, rel, True)
                    if not same(target, item["before"]):
                        raise InstallerError("Tệp đã đổi trước ghi: " + rel, "PREIMAGE_CONFLICT")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    tmp = target.with_name(".patch_" + uuid.uuid4().hex)
                    try:
                        shutil.copyfile(safe_path(payload, item["source"]), tmp)
                        if not same(tmp, item["after"]):
                            raise InstallerError("Nguồn đổi hoặc tệp tạm sai hash.", "SOURCE_CHANGED")
                        if not same(target, item["before"]):
                            raise InstallerError("Tệp đã đổi trong lúc staging.", "PREIMAGE_CONFLICT")
                        j["state"] = "applying"
                        j["pending"] = rel
                        atomic_json(jfile, j)
                        self._replace_patch(root, tmp, target, item["before"], item["after"], rel)
                    finally:
                        tmp.unlink(missing_ok=True)
                    emit(OperationPhase.APPLY, target.name, i + 1, total)

                for i, (rel, item) in enumerate(plan.items()):
                    if not same(safe_path(root, rel, True), item["after"]):
                        raise InstallerError("Đọc lại sai hash: " + rel, "READBACK_MISMATCH")
                    emit(OperationPhase.READBACK, rel, i + 1, total)

                receipt = {
                    "schema": 2,
                    "version": m["version"],
                    "client_game_version": m["client_game_version"],
                    "resource_version": m["resource_version"],
                    "game_root": croot,
                    "backup_dir": str(backup),
                    "journal_id": jid,
                    "installed_at": datetime.now(timezone.utc).isoformat(),
                    "files": {r: v["after"] for r, v in plan.items()},
                    "files_count": total,
                    "manifest_sha256": manifest_sha256(m),
                }
                atomic_json(rp, receipt)
                j["state"] = "done"
                atomic_json(jfile, j)
            except Exception as e:
                try:
                    self._restore_journal(root, jfile, j)
                except Exception as recovery:
                    j["state"] = "recovery_required"
                    j["error"] = str(e)
                    j["recovery_error"] = str(recovery)
                    atomic_json(jfile, j)
                    raise InstallerError("Thao tác bị ngắt; cần phục hồi từ nhật ký. Chi tiết: " + str(recovery), "RECOVERY_REQUIRED") from e
                if isinstance(e, InstallerError) and e.code in ("FILE_IN_USE", "FILE_ACCESS_DENIED"):
                    raise InstallerError("Cài đặt thất bại; đã phục hồi trạng thái trước thao tác. " + str(e), e.code) from e
                raise InstallerError("Cài đặt thất bại; đã phục hồi trạng thái trước thao tác: " + str(e), "TRANSACTION_FAILED") from e

            self._prune_backups(root, backup, gvers["game"])
            emit(OperationPhase.DONE, f"Đã cài {total} tệp trong manifest {m['version']}.", total, total, receipt)
            return receipt

    def verify_installed(self, root, event_cb=None, operation_id="verify"):
        root = Path(root).resolve()
        rp = root / RECEIPT
        try:
            r = json.loads(rp.read_text(encoding="utf8"))
        except (OSError, ValueError) as e:
            raise InstallerError("Chưa có biên bản cài đặt hợp lệ để kiểm tệp.", "NOT_VERIFIED") from e
        if not isinstance(r, dict) or r.get("schema") != 2 or r.get("game_root") != canonicalize_path(root) or not r.get("files"):
            raise InstallerError("Biên bản không khớp thư mục hoặc định dạng.", "NOT_VERIFIED")
        for i, (rel, meta) in enumerate(r["files"].items()):
            if not same(safe_path(root, rel, True), meta):
                raise InstallerError("Tệp không khớp bản đã cài: " + rel, "FILE_MISMATCH")
            self._emit(event_cb, operation_id, OperationPhase.VERIFY, rel, i + 1, len(r["files"]))
        return {"status": "verified", "version": r["version"], "files": len(r["files"])}
