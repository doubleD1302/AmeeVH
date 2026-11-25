"""Non-destructive one-time migration from v1.3.4 AppData (StellaSora_Launcher_Candidate_r02)."""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import PathManager
from .safety import InstallerError, atomic_json

MIGRATION_MARKER_NAME = ".migrated_from_r02.json"


def _is_reparse_or_symlink(path: Path) -> bool:
    try:
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            return True
        if os.name == "nt":
            attrs = getattr(path.lstat(), "st_file_attributes", 0)
            if attrs & 0x400:
                return True
    except OSError:
        return True
    return False


def _norm_parts(path: Path) -> tuple[str, ...]:
    norm = os.path.normpath(str(path))
    parts = Path(norm).parts
    if os.name == "nt":
        return tuple(p.casefold() for p in parts)
    return parts


def _rewrite_backup_prefix(raw_path: str, src_backups: Path, dst_backups: Path) -> Optional[str]:
    raw_str = raw_path.strip()
    if not raw_str:
        return None
    raw_obj = Path(raw_str)
    src_candidates: list[Path] = [src_backups]
    try:
        src_resolved = src_backups.resolve()
        if src_resolved != src_backups:
            src_candidates.append(src_resolved)
    except OSError:
        pass

    raw_candidates: list[Path] = [raw_obj]
    try:
        raw_resolved = raw_obj.resolve()
        if raw_resolved != raw_obj:
            raw_candidates.append(raw_resolved)
    except OSError:
        pass

    dst_resolved = dst_backups
    try:
        dst_resolved = dst_backups.resolve()
    except OSError:
        pass

    for rc in raw_candidates:
        rc_raw_parts = Path(os.path.normpath(str(rc))).parts
        rc_cmp = _norm_parts(rc)
        for sc in src_candidates:
            sc_cmp = _norm_parts(sc)
            if len(rc_cmp) >= len(sc_cmp) and rc_cmp[: len(sc_cmp)] == sc_cmp:
                rel_parts = rc_raw_parts[len(sc_cmp) :]
                return str(dst_resolved.joinpath(*rel_parts))
    return None


def _rewrite_field(mapping: dict[str, Any], key: str, record_key: str, src_backups: Path, dst_backups: Path) -> bool:
    val = mapping.get(key)
    if not isinstance(val, str):
        return False
    rewritten = _rewrite_backup_prefix(val, src_backups, dst_backups)
    if rewritten is None or rewritten == val:
        return False
    mapping.setdefault(record_key, val)
    mapping[key] = rewritten
    return True


def _rewrite_journal_data(j: dict[str, Any], src_backups: Path, dst_backups: Path) -> bool:
    changed = False
    if _rewrite_field(j, "backup_dir", "_migrated_from_backup_dir", src_backups, dst_backups):
        changed = True
    prev = j.get("previous_receipt")
    if isinstance(prev, dict):
        if _rewrite_field(prev, "backup_dir", "_migrated_from_backup_dir", src_backups, dst_backups):
            changed = True
    for container_key in ("entries", "files"):
        container = j.get(container_key)
        if isinstance(container, dict):
            items = container.values()
        elif isinstance(container, list):
            items = container
        else:
            items = ()
        for item in items:
            if isinstance(item, dict):
                if _rewrite_field(item, "backup_path", "_migrated_from_backup_path", src_backups, dst_backups):
                    changed = True
                if _rewrite_field(item, "backup_dir", "_migrated_from_backup_dir", src_backups, dst_backups):
                    changed = True
    return changed


def migration_warning_error(result: Optional[dict[str, Any]]) -> Optional[InstallerError]:
    if (
        not isinstance(result, dict)
        or result.get("status") == "already_migrated"
        or result.get("warning_code") != "MIGRATION"
    ):
        return None
    warnings = result.get("warnings") or []
    detail = "; ".join(str(w) for w in warnings if w)
    msg = detail or "Di trú dữ liệu từ phiên bản cũ gặp cảnh báo."
    return InstallerError(msg, "MIGRATION")


def migrate_from_r02_if_needed(pm: PathManager, legacy_dir: Optional[str | Path] = None) -> dict[str, Any]:
    """Non-destructively migrate v1.3.4 AppData into v2.0 AppData once."""
    if getattr(pm, "is_custom_app_data", False) or getattr(pm, "_app", None) is not None:
        return {
            "status": "skipped_custom_app_data",
            "source_dir": None,
            "target_dir": str(pm.app_data_dir),
            "copied_files": 0,
            "corrupt_configs_copied": 0,
            "backups_copied": 0,
            "journals_copied": 0,
            "journals_rewritten": 0,
            "shared_downloads_copied": 0,
            "official_check_copied": False,
            "corrupt_config": False,
            "warnings": [],
            "warning_code": None,
            "error_code": None,
        }

    marker = getattr(pm, "migration_marker_file", None) or (pm.app_data_dir / MIGRATION_MARKER_NAME)
    if marker.is_file():
        try:
            existing = json.loads(marker.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                return {
                    **existing,
                    "status": "already_migrated",
                    "previous_status": existing.get("status"),
                    "previous_warning_code": existing.get("warning_code"),
                    "previous_warnings": list(existing.get("warnings") or []),
                    "warnings": [],
                    "warning_code": None,
                    "error_code": None,
                }
        except (OSError, ValueError) as exc:
            return {
                "status": "already_migrated",
                "source_dir": None,
                "target_dir": str(pm.app_data_dir),
                "copied_files": 0,
                "corrupt_configs_copied": 0,
                "backups_copied": 0,
                "journals_copied": 0,
                "journals_rewritten": 0,
                "shared_downloads_copied": 0,
                "official_check_copied": False,
                "corrupt_config": False,
                "previous_warning_code": "MIGRATION",
                "previous_warnings": [f"Không đọc được dấu vết di trú {marker}: {exc}"],
                "warnings": [],
                "warning_code": None,
                "error_code": None,
            }
        return {
            "status": "already_migrated",
            "source_dir": None,
            "target_dir": str(pm.app_data_dir),
            "copied_files": 0,
            "corrupt_configs_copied": 0,
            "backups_copied": 0,
            "journals_copied": 0,
            "journals_rewritten": 0,
            "shared_downloads_copied": 0,
            "official_check_copied": False,
            "corrupt_config": False,
            "warnings": [],
            "warning_code": None,
            "error_code": None,
        }

    src = Path(legacy_dir) if legacy_dir is not None else pm.legacy_app_data_dir
    now_iso = datetime.now(timezone.utc).isoformat()
    if not src.is_dir():
        payload: dict[str, Any] = {
            "status": "fresh_install",
            "migrated_at": now_iso,
            "source_dir": str(src),
            "target_dir": str(pm.app_data_dir),
            "copied_files": 0,
            "corrupt_configs_copied": 0,
            "backups_copied": 0,
            "journals_copied": 0,
            "journals_rewritten": 0,
            "shared_downloads_copied": 0,
            "official_check_copied": False,
            "corrupt_config": False,
            "warnings": [],
            "warning_code": None,
            "error_code": None,
        }
        try:
            atomic_json(marker, payload)
        except OSError as exc:
            payload["status"] = "partial"
            payload["warnings"].append(f"Không ghi được dấu vết di trú {marker}: {exc}")
            payload["warning_code"] = "MIGRATION"
            payload["error_code"] = "E-MIGRATION"
        return payload

    warnings: list[str] = []
    copied_files = 0
    corrupt_configs_copied = 0
    backups_copied = 0
    journals_copied = 0
    journals_rewritten = 0
    shared_downloads_copied = 0
    official_check_copied = False
    corrupt_config = False

    # 1. Copy config.corrupt.*.json files
    try:
        corrupt_files = sorted(src.glob("config.corrupt.*.json"))
    except OSError as exc:
        corrupt_files = []
        warnings.append(f"Không liệt kê được cấu hình lỗi cũ: {exc}")

    for cf in corrupt_files:
        if not cf.is_file() or _is_reparse_or_symlink(cf):
            continue
        dst_cf = pm.app_data_dir / cf.name
        if not dst_cf.exists():
            try:
                shutil.copy2(cf, dst_cf)
                copied_files += 1
                corrupt_configs_copied += 1
            except OSError as exc:
                warnings.append(f"Không sao chép được {cf.name}: {exc}")

    # 2. Copy config.json byte-for-byte (even if corrupt) and detect corruption read-only
    src_cfg = src / "config.json"
    if src_cfg.is_file() and not _is_reparse_or_symlink(src_cfg):
        if not pm.config_file.exists():
            try:
                shutil.copy2(src_cfg, pm.config_file)
                copied_files += 1
            except OSError as exc:
                warnings.append(f"Không sao chép được config.json: {exc}")
        if pm.config_file.is_file():
            try:
                parsed = json.loads(pm.config_file.read_text(encoding="utf-8"))
                if not isinstance(parsed, dict):
                    raise ValueError("JSON phải là object")
            except (OSError, ValueError) as exc:
                corrupt_config = True
                warnings.append(f"config.json cũ bị hỏng (đã giữ nguyên bản gốc): {exc}")

    # 3. Copy backups/ tree non-destructively (skipping symlinks/junctions and .operation.lock)
    src_backups = src / "backups"
    dst_backups = pm.backup_root
    if src_backups.is_dir() and not _is_reparse_or_symlink(src_backups):
        for dirpath, dirnames, filenames in os.walk(src_backups, followlinks=False):
            dp = Path(dirpath)
            dirnames[:] = [d for d in dirnames if not _is_reparse_or_symlink(dp / d)]
            for fname in filenames:
                if fname == ".operation.lock":
                    continue
                sf = dp / fname
                if _is_reparse_or_symlink(sf):
                    continue
                rel = dp.relative_to(src_backups) / fname
                df = dst_backups / rel
                if df.exists():
                    continue
                try:
                    df.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(sf, df)
                    copied_files += 1
                    backups_copied += 1
                except OSError as exc:
                    warnings.append(f"Không sao chép được sao lưu {rel}: {exc}")

    # 4. Copy and rewrite journals/*.json
    src_journals = src / "journals"
    dst_journals = pm.journals_dir
    if src_journals.is_dir() and not _is_reparse_or_symlink(src_journals):
        try:
            journal_files = sorted(src_journals.glob("*.json"))
        except OSError as exc:
            journal_files = []
            warnings.append(f"Không liệt kê được nhật ký cũ: {exc}")

        for jf in journal_files:
            if not jf.is_file() or _is_reparse_or_symlink(jf):
                continue
            dst_j = dst_journals / jf.name
            if dst_j.exists():
                continue
            try:
                j_data = json.loads(jf.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                warnings.append(f"Nhật ký {jf.name} bị hỏng (sao chép nguyên trạng): {exc}")
                try:
                    shutil.copy2(jf, dst_j)
                    copied_files += 1
                    journals_copied += 1
                except OSError as copy_exc:
                    warnings.append(f"Không sao chép được nhật ký hỏng {jf.name}: {copy_exc}")
                continue

            if isinstance(j_data, dict):
                rewritten = _rewrite_journal_data(j_data, src_backups, dst_backups)
                try:
                    atomic_json(dst_j, j_data)
                    copied_files += 1
                    journals_copied += 1
                    if rewritten:
                        journals_rewritten += 1
                except OSError as exc:
                    warnings.append(f"Không ghi được nhật ký {jf.name}: {exc}")
            else:
                warnings.append(f"Nhật ký {jf.name} không phải JSON object (sao chép nguyên trạng).")
                try:
                    shutil.copy2(jf, dst_j)
                    copied_files += 1
                    journals_copied += 1
                except OSError as exc:
                    warnings.append(f"Không sao chép được nhật ký {jf.name}: {exc}")

    # 5. Copy official_check.json & payload_cache/shared_downloads/ (skip update_helper/ & logs/)
    src_official = src / "official_check.json"
    dst_official = getattr(pm, "official_check_file", pm.app_data_dir / "official_check.json")
    if src_official.is_file() and not _is_reparse_or_symlink(src_official) and not dst_official.exists():
        try:
            shutil.copy2(src_official, dst_official)
            copied_files += 1
            official_check_copied = True
        except OSError as exc:
            warnings.append(f"Không sao chép được official_check.json: {exc}")

    src_shared = src / "payload_cache" / "shared_downloads"
    if src_shared.is_dir() and not _is_reparse_or_symlink(src_shared):
        dst_shared = pm.payload_root / "shared_downloads"
        for dirpath, dirnames, filenames in os.walk(src_shared, followlinks=False):
            dp = Path(dirpath)
            dirnames[:] = [d for d in dirnames if not _is_reparse_or_symlink(dp / d)]
            for fname in filenames:
                sf = dp / fname
                if _is_reparse_or_symlink(sf):
                    continue
                rel = dp.relative_to(src_shared) / fname
                df = dst_shared / rel
                if df.exists():
                    continue
                try:
                    df.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(sf, df)
                    copied_files += 1
                    shared_downloads_copied += 1
                except OSError as exc:
                    warnings.append(f"Không sao chép được tệp tải chia sẻ {rel}: {exc}")

    has_warning = bool(warnings or corrupt_config)
    result: dict[str, Any] = {
        "status": "partial" if has_warning else "migrated",
        "migrated_at": now_iso,
        "source_dir": str(src),
        "target_dir": str(pm.app_data_dir),
        "copied_files": copied_files,
        "corrupt_configs_copied": corrupt_configs_copied,
        "backups_copied": backups_copied,
        "journals_copied": journals_copied,
        "journals_rewritten": journals_rewritten,
        "shared_downloads_copied": shared_downloads_copied,
        "official_check_copied": official_check_copied,
        "corrupt_config": corrupt_config,
        "warnings": warnings,
        "warning_code": "MIGRATION" if has_warning else None,
        "error_code": "E-MIGRATION" if has_warning else None,
    }
    try:
        atomic_json(marker, result)
    except OSError as exc:
        warnings.append(f"Không ghi được dấu vết di trú {marker}: {exc}")
        result["status"] = "partial"
        result["warning_code"] = "MIGRATION"
        result["error_code"] = "E-MIGRATION"
    return result
