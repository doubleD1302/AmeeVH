# -*- coding: utf-8 -*-
"""
Rollback engine strictly bound to canonical game root.
Guards against cross-root restoration and verifies backup integrity before applying.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Callable, Optional

from .game_detection import canonicalize_path, is_game_process_running
from .installer import InstallerError, sha256_file
from .types import OperationEvent, OperationPhase


class RollbackEngine:
    """Handles restoring the game to pristine original state from backed-up preimages."""

    def __init__(self, backup_root: Path):
        self.backup_root = backup_root

    def get_backups_for_game(self, game_root: Path) -> list[dict]:
        """Returns list of verified backups strictly belonging to this canonical game root."""
        cpath = canonicalize_path(game_root)
        import hashlib
        root_hash = hashlib.sha256(cpath.encode("utf-8")).hexdigest()[:12]
        game_backup_dir = self.backup_root / f"game_{root_hash}"
        if not game_backup_dir.exists():
            return []

        backups = []
        for bdir in sorted(game_backup_dir.iterdir(), reverse=True):
            if bdir.is_dir() and (bdir / "backup_manifest.json").exists():
                try:
                    with open(bdir / "backup_manifest.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Verify canonical root binding
                        if canonicalize_path(data.get("game_root", "")) == cpath:
                            backups.append({
                                "id": bdir.name,
                                "path": bdir,
                                "created_at": data.get("created_at", bdir.name),
                                "files_count": len(data.get("files", {})),
                                "manifest": data
                            })
                except Exception:
                    pass
        return backups

    def rollback(
        self,
        game_root: Path,
        backup_id: Optional[str] = None,
        operation_id: str = "op_rollback",
        event_cb: Optional[Callable[[OperationEvent], None]] = None
    ) -> dict:
        """Executes full verified rollback."""
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

        emit(OperationPhase.PREFLIGHT, "Đang kiểm tra môi trường để khôi phục...")
        if not game_root.exists() or not (game_root / "StellaSora.exe").exists():
            raise InstallerError("Thư mục game không hợp lệ hoặc thiếu StellaSora.exe", "INVALID_ROOT")

        if is_game_process_running():
            raise InstallerError("Game Stella Sora đang chạy! Vui lòng đóng game trước khi khôi phục.", "GAME_RUNNING")

        # Find target backup
        backups = self.get_backups_for_game(game_root)
        if not backups:
            raise InstallerError("Không tìm thấy bản sao lưu gốc nào tương ứng với thư mục game này!", "NO_BACKUP_FOUND")

        target_backup = None
        if backup_id:
            for b in backups:
                if b["id"] == backup_id:
                    target_backup = b
                    break
            if not target_backup:
                raise InstallerError(f"Không tìm thấy bản sao lưu có mã {backup_id}", "BACKUP_NOT_FOUND")
        else:
            # Latest verified backup for this game
            target_backup = backups[0]

        b_dir = target_backup["path"]
        b_manifest = target_backup["manifest"].get("files", {})
        total_files = len(b_manifest)

        # 1. Verify backup files exist and are uncorrupted before touching game
        emit(OperationPhase.VERIFY, "Đang kiểm tra tính toàn vẹn của bản sao lưu...", 0, total_files)
        restore_list: list[tuple[Path, Path, str]] = []  # (src_backup, dest_path, expected_sha)
        for i, (rel_dest, meta) in enumerate(b_manifest.items()):
            src_file = b_dir / Path(rel_dest)
            dest_file = (game_root / Path(rel_dest)).resolve()
            if not src_file.exists():
                raise InstallerError(f"Tệp sao lưu bị thiếu: {rel_dest}", "BACKUP_CORRUPT")
            
            exp_sha = meta.get("sha256", "").lower()
            act_sha = sha256_file(src_file).lower()
            if exp_sha and act_sha != exp_sha:
                raise InstallerError(f"Tệp sao lưu bị hỏng checksum: {src_file.name}", "BACKUP_CORRUPT")

            restore_list.append((src_file, dest_file, exp_sha or act_sha))
            emit(OperationPhase.VERIFY, f"Hợp lệ: {src_file.name}", i + 1, total_files)

        # 2. Perform safe restore
        emit(OperationPhase.APPLY, "Đang khôi phục tệp dữ liệu gốc...", 0, total_files)
        for i, (src_file, dest_file, exp_sha) in enumerate(restore_list):
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_dest = dest_file.parent / f".tmp_restore_{dest_file.name}"
            shutil.copy2(src_file, tmp_dest)
            os.replace(tmp_dest, dest_file)
            emit(OperationPhase.APPLY, f"Khôi phục: {dest_file.name}", i + 1, total_files)

        # 3. Readback Verification
        emit(OperationPhase.READBACK, "Đang xác minh sau khi khôi phục...", 0, total_files)
        for i, (_, dest_file, exp_sha) in enumerate(restore_list):
            read_sha = sha256_file(dest_file).lower()
            if exp_sha and read_sha != exp_sha:
                raise InstallerError(f"Lỗi kiểm tra tệp sau khôi phục: {dest_file.name}", "RESTORE_VERIFY_FAILED")
            emit(OperationPhase.READBACK, f"Đã khôi phục chuẩn: {dest_file.name}", i + 1, total_files)

        # 4. Remove patch receipt if present
        receipt_file = game_root / ".vietnamese_patch_receipt.json"
        if receipt_file.exists():
            receipt_file.unlink(missing_ok=True)

        emit(OperationPhase.DONE, "Đã khôi phục hoàn toàn dữ liệu game gốc ban đầu!", total_files, total_files)
        return {"status": "success", "restored_files_count": total_files, "backup_id": target_backup["id"]}
