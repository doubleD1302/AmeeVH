# -*- coding: utf-8 -*-
"""
Transactional, atomic, journaling installer for Stella Sora Vietnamese patch.
Enforces path traversal guards, preimage snapshots, volume-local staging,
and complete readback verification before writing receipt.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .game_detection import canonicalize_path, is_game_process_running
from .types import OperationEvent, OperationPhase


def sha256_file(p: Path) -> str:
    """Calculates SHA256 hex digest of a file in 64KB chunks."""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class InstallerError(Exception):
    def __init__(self, message: str, code: str = "INSTALL_ERR"):
        super().__init__(message)
        self.code = code


class PatchInstaller:
    """Transactional patch installer bound to a specific game root."""

    def __init__(self, backup_root: Path, journals_dir: Path):
        self.backup_root = backup_root
        self.journals_dir = journals_dir
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.journals_dir.mkdir(parents=True, exist_ok=True)

    def _validate_path_security(self, game_root: Path, rel_path: str) -> Path:
        """Guards against directory traversal and symlink escapes."""
        # Normalize and forbid leading slashes or Windows drive specifiers
        clean_rel = rel_path.replace("\\", "/").strip()
        if clean_rel.startswith("/") or ":" in clean_rel:
            raise InstallerError(f"Đường dẫn không hợp lệ (tuyệt đối): {rel_path}", "PATH_TRAVERSAL")

        parts = clean_rel.split("/")
        if any(part in ("..", ".", "") for part in parts):
            raise InstallerError(f"Đường dẫn không hợp lệ (chứa ..): {rel_path}", "PATH_TRAVERSAL")

        dest = (game_root / clean_rel).resolve()
        canonical_game = Path(canonicalize_path(game_root))
        canonical_dest = Path(canonicalize_path(dest))

        # Check destination is inside game_root
        try:
            canonical_dest.relative_to(canonical_game)
        except ValueError:
            raise InstallerError(f"Đường dẫn vượt khỏi thư mục game: {rel_path}", "PATH_ESCAPE")

        return dest

    def get_backup_dir_for_root(self, game_root: Path) -> Path:
        """Returns the canonical backup directory bound to this game installation."""
        cpath = canonicalize_path(game_root)
        root_hash = hashlib.sha256(cpath.encode("utf-8")).hexdigest()[:12]
        p = self.backup_root / f"game_{root_hash}"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def install(
        self,
        game_root: Path,
        payload_root: Path,
        manifest_data: Optional[dict] = None,
        operation_id: str = "op_install",
        event_cb: Optional[Callable[[OperationEvent], None]] = None
    ) -> dict:
        """Executes full atomic patch transaction."""
        def emit(phase: OperationPhase, msg: str, completed: int = 0, total: int = 0, err: str = None, receipt: dict = None):
            if event_cb:
                event_cb(OperationEvent(
                    operation_id=operation_id,
                    phase=phase,
                    message=msg,
                    completed=completed,
                    total=total,
                    error_code=err,
                    receipt=receipt
                ))

        # 1. Preflight
        emit(OperationPhase.PREFLIGHT, "Đang kiểm tra môi trường và tệp trò chơi...")
        if not game_root.exists() or not (game_root / "StellaSora.exe").exists():
            raise InstallerError("Thư mục game không hợp lệ hoặc thiếu StellaSora.exe", "INVALID_ROOT")

        if is_game_process_running():
            raise InstallerError("Game Stella Sora đang chạy! Vui lòng đóng game trước khi cài đặt.", "GAME_RUNNING")

        # Test write permission in game root
        test_file = game_root / f".write_test_{int(time.time())}"
        try:
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink()
        except Exception as e:
            raise InstallerError(f"Không có quyền ghi vào thư mục game: {e}", "PERMISSION_DENIED")

        # Load and resolve manifest
        if manifest_data is None:
            manifest_file = payload_root / "patch_manifest.json"
            if not manifest_file.exists():
                raise InstallerError(f"Không tìm thấy file patch_manifest.json trong {payload_root}", "MANIFEST_MISSING")
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)

        patch_version = manifest_data.get("version", manifest_data.get("release_tag", "v0.9.8"))
        files_map = manifest_data.get("files", {})

        # If files_map not explicitly provided, build from payload_root automatically
        if not files_map:
            files_map = {}
            # 1. Patched ArcX archives
            lua_arcx = payload_root / "lua_patched_vi.arcx"
            if lua_arcx.exists():
                files_map["Persistent_Store/Scripts/lua.arcx"] = {
                    "source": "lua_patched_vi.arcx",
                    "desc": "Kịch bản thoại & Tin nhắn Lua ArcX"
                }
            data_arcx = payload_root / "data_patched_vi.arcx"
            if data_arcx.exists():
                files_map["Persistent_Store/Tables/data.arcx"] = {
                    "source": "data_patched_vi.arcx",
                    "desc": "Dữ liệu giao diện Core UI ArcX"
                }

            # 2. Bundles declared in patch manifest
            for b_name, b_meta in manifest_data.get("bundles", {}).items():
                files_map[f"Persistent_Store/AssetBundles/{b_name}"] = {
                    "source": f"AssetBundles/{b_name}",
                    "sha256": b_meta.get("patched_sha256", ""),
                    "size": b_meta.get("size_bytes", 0),
                    "desc": f"AssetBundle {b_name}"
                }

            # 3. Any additional AssetBundles present in AssetBundles/ folder
            bundles_dir = payload_root / "AssetBundles"
            if bundles_dir.exists():
                for bf in bundles_dir.glob("*.en.unity3d"):
                    rel = f"Persistent_Store/AssetBundles/{bf.name}"
                    if rel not in files_map:
                        files_map[rel] = {
                            "source": f"AssetBundles/{bf.name}",
                            "size": bf.stat().st_size,
                            "desc": f"AssetBundle {bf.name}"
                        }

        if not files_map:
            raise InstallerError("Không tìm thấy tệp bản dịch hợp lệ nào trong kho asset!", "EMPTY_MANIFEST")

        total_files = len(files_map)
        emit(OperationPhase.PREFLIGHT, f"Chuẩn bị cài đặt {total_files} tệp bản dịch...")

        # 2. Verification of payload files before modifying anything
        emit(OperationPhase.VERIFY, "Đang xác minh tính toàn vẹn của tệp nguồn...", 0, total_files)
        validated_payloads: list[tuple[str, Path, Path, str]] = []  # (rel_dest, payload_src, dest_path, expected_hash)

        for i, (rel_dest, meta) in enumerate(files_map.items()):
            dest_path = self._validate_path_security(game_root, rel_dest)
            
            # Find payload file
            src_rel = meta.get("source", rel_dest)
            src_path = payload_root / src_rel
            if not src_path.exists():
                # Check inside AssetBundles subfolder or flat
                if (payload_root / "AssetBundles" / Path(src_rel).name).exists():
                    src_path = payload_root / "AssetBundles" / Path(src_rel).name
                elif (payload_root / Path(src_rel).name).exists():
                    src_path = payload_root / Path(src_rel).name
                else:
                    raise InstallerError(f"Thiếu tệp dữ liệu nguồn: {src_rel}", "PAYLOAD_MISSING")

            expected_sha = meta.get("sha256", "").lower()
            actual_sha = sha256_file(src_path).lower()
            if expected_sha and actual_sha != expected_sha:
                raise InstallerError(f"Sai mã kiểm tra SHA256 cho tệp nguồn {src_path.name}", "HASH_MISMATCH")

            validated_payloads.append((rel_dest, src_path, dest_path, expected_sha or actual_sha))
            emit(OperationPhase.VERIFY, f"Đã kiểm tra: {src_path.name}", i + 1, total_files)

        # 3. Create Backup & Preimage Snapshot
        emit(OperationPhase.BACKUP, "Đang tạo bản sao lưu dữ liệu gốc...", 0, total_files)
        backup_root_dir = self.get_backup_dir_for_root(game_root)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = backup_root_dir / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_manifest = {
            "created_at": datetime.now().isoformat(),
            "game_root": canonicalize_path(game_root),
            "files": {}
        }

        backed_up_count = 0
        for i, (rel_dest, _, dest_path, _) in enumerate(validated_payloads):
            if dest_path.exists():
                rel_p = Path(rel_dest)
                b_target = backup_dir / rel_p
                b_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dest_path, b_target)
                b_sha = sha256_file(b_target)
                orig_sha = sha256_file(dest_path)
                if b_sha != orig_sha:
                    # Cleanup corrupt backup and fail
                    shutil.rmtree(backup_dir, ignore_errors=True)
                    raise InstallerError(f"Lỗi sao lưu tệp {dest_path.name} (sai checksum)", "BACKUP_FAILED")
                backup_manifest["files"][rel_dest] = {
                    "sha256": b_sha,
                    "size": dest_path.stat().st_size
                }
                backed_up_count += 1
            emit(OperationPhase.BACKUP, f"Sao lưu: {dest_path.name}", i + 1, total_files)

        with open(backup_dir / "backup_manifest.json", "w", encoding="utf-8") as f:
            json.dump(backup_manifest, f, indent=2, ensure_ascii=False)

        # 4. Initialize Transaction Journal
        journal_id = f"journal_{int(time.time())}_{operation_id}"
        journal_file = self.journals_dir / f"{journal_id}.json"
        journal_data = {
            "journal_id": journal_id,
            "operation_id": operation_id,
            "game_root": canonicalize_path(game_root),
            "backup_dir": str(backup_dir),
            "timestamp": datetime.now().isoformat(),
            "state": "backed_up",
            "applied_files": []
        }
        with open(journal_file, "w", encoding="utf-8") as f:
            json.dump(journal_data, f, indent=2, ensure_ascii=False)

        # 5. Apply Files (Local volume staging & Atomic replace)
        emit(OperationPhase.APPLY, "Đang ghi dữ liệu Việt hóa...", 0, total_files)
        applied_list = []
        try:
            for i, (rel_dest, src_path, dest_path, expected_sha) in enumerate(validated_payloads):
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write to temp on same volume/directory
                tmp_dest = dest_path.parent / f".tmp_{dest_path.name}_{int(time.time())}"
                shutil.copy2(src_path, tmp_dest)
                tmp_sha = sha256_file(tmp_dest).lower()
                if tmp_sha != expected_sha:
                    tmp_dest.unlink(missing_ok=True)
                    raise InstallerError(f"Lỗi ghi tệp tạm {dest_path.name} (sai checksum)", "WRITE_CORRUPT")

                # Atomic replace
                os.replace(tmp_dest, dest_path)
                applied_list.append((rel_dest, dest_path, expected_sha))
                
                # Update journal
                journal_data["applied_files"].append(rel_dest)
                with open(journal_file, "w", encoding="utf-8") as f:
                    json.dump(journal_data, f, indent=2, ensure_ascii=False)

                emit(OperationPhase.APPLY, f"Cài đặt: {dest_path.name}", i + 1, total_files)

        except Exception as e:
            # Automatic Rollback on failure!
            emit(OperationPhase.ROLLBACK, f"Xảy ra sự cố ({e}), đang tự động hoàn nguyên...", 0, len(applied_list))
            self._emergency_rollback(game_root, backup_dir, journal_data["applied_files"])
            journal_data["state"] = "rolled_back"
            with open(journal_file, "w", encoding="utf-8") as f:
                json.dump(journal_data, f, indent=2, ensure_ascii=False)
            raise InstallerError(f"Cài đặt thất bại và đã hoàn nguyên an toàn: {e}", "TRANSACTION_FAILED")

        # 6. Readback Verification
        emit(OperationPhase.READBACK, "Đang kiểm tra độ chính xác sau khi cài đặt...", 0, total_files)
        readback_receipt_files = {}
        for i, (rel_dest, dest_path, expected_sha) in enumerate(applied_list):
            if not dest_path.exists():
                raise InstallerError(f"Tệp không tồn tại sau khi cài: {dest_path.name}", "READBACK_MISSING")
            read_sha = sha256_file(dest_path).lower()
            if read_sha != expected_sha:
                raise InstallerError(f"Sai checksum sau khi ghi tệp: {dest_path.name}", "READBACK_MISMATCH")
            readback_receipt_files[rel_dest] = {
                "sha256": read_sha,
                "size": dest_path.stat().st_size
            }
            emit(OperationPhase.READBACK, f"Khớp 100%: {dest_path.name}", i + 1, total_files)

        # 7. Write Installed Receipt
        receipt_data = {
            "version": patch_version,
            "installed_at": datetime.now().isoformat(),
            "game_root": canonicalize_path(game_root),
            "backup_dir": str(backup_dir),
            "files_count": len(readback_receipt_files),
            "files": readback_receipt_files
        }
        receipt_file = game_root / ".vietnamese_patch_receipt.json"
        tmp_receipt = game_root / ".tmp_receipt.json"
        with open(tmp_receipt, "w", encoding="utf-8") as f:
            json.dump(receipt_data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_receipt, receipt_file)

        # Update and clean journal
        journal_data["state"] = "done"
        with open(journal_file, "w", encoding="utf-8") as f:
            json.dump(journal_data, f, indent=2, ensure_ascii=False)

        emit(
            OperationPhase.DONE,
            f"Cài đặt bản Việt hóa {patch_version} thành công trọn vẹn!",
            total_files,
            total_files,
            receipt=receipt_data
        )
        return receipt_data

    def _emergency_rollback(self, game_root: Path, backup_dir: Path, applied_files: list[str]):
        """Rolls back applied files during a failed transaction."""
        backup_manifest_file = backup_dir / "backup_manifest.json"
        backup_manifest = {}
        if backup_manifest_file.exists():
            try:
                with open(backup_manifest_file, "r", encoding="utf-8") as f:
                    backup_manifest = json.load(f).get("files", {})
            except Exception:
                pass

        for rel in applied_files:
            try:
                dest = self._validate_path_security(game_root, rel)
                if rel in backup_manifest:
                    # Restore backed up original
                    b_src = backup_dir / Path(rel)
                    if b_src.exists():
                        shutil.copy2(b_src, dest)
                else:
                    # File was newly added by patch, remove it
                    if dest.exists():
                        dest.unlink(missing_ok=True)
            except Exception:
                pass
