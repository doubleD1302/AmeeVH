#!/usr/bin/env python3
"""Safe Persistent_Store texture routing helper for Stella Sora PC (Yostar).

Never modifies StellaSora_Data/, InstallResource/, executables, DLLs, data.arcx,
or lua.arcx. Only inspects InstallResource read-only and routes via
file_versions.dat (Level 1) or Persistent_Store/ss_win.mani + file_versions.dat
(Level 2) with immutable original backups and atomic writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

DEFAULT_GAME_DIR = Path(r"C:\YostarGames\StellaSora_EN")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST_BUNDLES = PROJECT_ROOT / "dist" / "AssetBundles"
DEFAULT_BACKUP_DIR = PROJECT_ROOT / "backups" / "pre_routing_sync_20261124"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _assert_safe_target(path: Path, game_dir: Path) -> None:
    """Hard guard forbidding any write inside StellaSora_Data or InstallResource."""
    resolved = path.resolve()
    forbidden = (game_dir / "StellaSora_Data").resolve()
    if resolved == forbidden or forbidden in resolved.parents:
        raise RuntimeError(f"Refusing to write inside forbidden directory: {resolved}")


def _atomic_write_bytes(path: Path, data: bytes, game_dir: Path | None = None) -> None:
    if game_dir is not None:
        _assert_safe_target(path, game_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp.open("wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def _detect_newline(raw: bytes) -> str:
    return "\r\n" if b"\r\n" in raw else "\n"


def _parse_manifest_entries(text: str) -> dict[str, dict]:
    entries: dict[str, dict] = {}
    for line in text.splitlines():
        if not line or line.startswith("$"):
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            entries[parts[0]] = {
                "md5": parts[1],
                "size": parts[2],
                "rest": parts[3:],
            }
    return entries


def _parse_file_versions(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) >= 2:
            name = Path(parts[0].replace("\\", "/")).name
            entries[name] = parts[1]
    return entries


def _collect_dist_bundles(dist_bundles_dir: Path) -> list[str]:
    if not dist_bundles_dir.is_dir():
        raise FileNotFoundError(f"Missing dist AssetBundles directory: {dist_bundles_dir}")
    bundles = sorted(p.name for p in dist_bundles_dir.glob("*.en.unity3d") if p.is_file())
    if not bundles:
        raise FileNotFoundError(f"No *.en.unity3d files found in: {dist_bundles_dir}")
    return bundles


def _ensure_backup(game_dir: Path, backup_dir: Path) -> dict:
    """Create immutable initial backup of file_versions.dat and ss_win.mani if absent."""
    meta_path = backup_dir / "backup_meta.json"
    fv_path = game_dir / "file_versions.dat"
    mani_path = game_dir / "Persistent_Store" / "ss_win.mani"
    if not fv_path.is_file():
        raise FileNotFoundError(f"Missing file_versions.dat: {fv_path}")
    if not mani_path.is_file():
        raise FileNotFoundError(f"Missing ss_win.mani: {mani_path}")

    if meta_path.is_file():
        return json.loads(meta_path.read_text(encoding="utf-8"))

    backup_dir.mkdir(parents=True, exist_ok=True)
    fv_bak = backup_dir / "file_versions.dat"
    mani_bak = backup_dir / "ss_win.mani"
    shutil.copy2(fv_path, fv_bak)
    shutil.copy2(mani_path, mani_bak)
    meta = {
        "game_dir": str(game_dir),
        "file_versions": {
            "path": str(fv_bak),
            "sha256": _sha256_file(fv_bak),
            "size": fv_bak.stat().st_size,
        },
        "ss_win_mani": {
            "path": str(mani_bak),
            "sha256": _sha256_file(mani_bak),
            "size": mani_bak.stat().st_size,
        },
    }
    _atomic_write_bytes(meta_path, (json.dumps(meta, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return meta


def inspect_status(game_dir: Path, dist_bundles_dir: Path, backup_dir: Path) -> dict:
    """Inspect current routing state without modifying any file."""
    bundles = _collect_dist_bundles(dist_bundles_dir)
    ps_ab_dir = game_dir / "Persistent_Store" / "AssetBundles"
    mani_path = game_dir / "Persistent_Store" / "ss_win.mani"
    ir_dir = game_dir / "StellaSora_Data" / "StreamingAssets" / "InstallResource"
    ir_mani_path = ir_dir / "install_resource_manifest.mani"
    fv_path = game_dir / "file_versions.dat"

    ps_mani = _parse_manifest_entries(mani_path.read_text(encoding="utf-8", errors="ignore")) if mani_path.is_file() else {}
    ir_mani = _parse_manifest_entries(ir_mani_path.read_text(encoding="utf-8", errors="ignore")) if ir_mani_path.is_file() else {}
    fv_map = _parse_file_versions(fv_path.read_text(encoding="utf-8", errors="ignore")) if fv_path.is_file() else {}

    shadowed_bundles: list[dict] = []
    file_versions_mismatches: list[dict] = []
    persistent_store_mismatches: list[str] = []
    persistent_store_matched = 0
    install_resource_sha256: dict[str, str] = {}

    for bname in bundles:
        dist_p = dist_bundles_dir / bname
        ps_p = ps_ab_dir / bname
        if ps_p.is_file() and _sha256_file(ps_p) == _sha256_file(dist_p):
            persistent_store_matched += 1
        else:
            persistent_store_mismatches.append(bname)

        ps_ent = ps_mani.get(bname)
        ir_ent = ir_mani.get(bname)
        fv_md5 = fv_map.get(bname)
        ir_file = ir_dir / bname
        if ir_file.is_file():
            install_resource_sha256[bname] = _sha256_file(ir_file)

        if ps_ent and ir_ent and ps_ent["md5"] == ir_ent["md5"]:
            shadowed_bundles.append(
                {
                    "bundle": bname,
                    "ss_win_md5": ps_ent["md5"],
                    "install_resource_md5": ir_ent["md5"],
                    "file_versions_md5": fv_md5,
                }
            )

        if ps_ent and fv_md5 != ps_ent["md5"]:
            file_versions_mismatches.append(
                {
                    "bundle": bname,
                    "file_versions_md5": fv_md5,
                    "ss_win_md5": ps_ent["md5"],
                }
            )

    meta_path = backup_dir / "backup_meta.json"
    return {
        "game_dir": str(game_dir),
        "dist_bundles_count": len(bundles),
        "persistent_store_matched": persistent_store_matched,
        "persistent_store_mismatches": persistent_store_mismatches,
        "shadowed_bundles": shadowed_bundles,
        "file_versions_mismatches": file_versions_mismatches,
        "install_resource_sha256": install_resource_sha256,
        "ss_win_mani_sha256": _sha256_file(mani_path) if mani_path.is_file() else None,
        "file_versions_dat_sha256": _sha256_file(fv_path) if fv_path.is_file() else None,
        "backup_present": meta_path.is_file(),
        "backup_dir": str(backup_dir),
    }


def _update_file_versions_lines(raw_bytes: bytes, desired_md5_by_bundle: dict[str, str]) -> tuple[bytes, list[str]]:
    nl = _detect_newline(raw_bytes)
    had_trailing_nl = raw_bytes.endswith((b"\n", b"\r"))
    text = raw_bytes.decode("utf-8")
    lines = text.splitlines()
    seen: set[str] = set()
    updated: list[str] = []
    changed_bundles: list[str] = []

    for line in lines:
        parts = line.split("|")
        if len(parts) >= 2:
            bname = Path(parts[0].replace("\\", "/")).name
            if bname in desired_md5_by_bundle:
                seen.add(bname)
                new_md5 = desired_md5_by_bundle[bname]
                if parts[1] != new_md5:
                    parts[1] = new_md5
                    changed_bundles.append(bname)
                updated.append("|".join(parts))
                continue
        updated.append(line)

    for bname in sorted(desired_md5_by_bundle):
        if bname not in seen:
            updated.append(f"\\Persistent_Store\\AssetBundles\\{bname}|{desired_md5_by_bundle[bname]}")
            changed_bundles.append(bname)

    out_text = nl.join(updated) + (nl if had_trailing_nl else "")
    return out_text.encode("utf-8"), sorted(set(changed_bundles))


def _update_ss_win_mani_lines(raw_bytes: bytes, overrides: dict[str, tuple[str, str]]) -> tuple[bytes, list[str]]:
    nl = _detect_newline(raw_bytes)
    had_trailing_nl = raw_bytes.endswith((b"\n", b"\r"))
    text = raw_bytes.decode("utf-8")
    lines = text.splitlines()
    updated: list[str] = []
    changed_bundles: list[str] = []

    for line in lines:
        if not line or line.startswith("$"):
            updated.append(line)
            continue
        parts = line.split("|")
        if len(parts) >= 3 and parts[0] in overrides:
            new_md5, new_size = overrides[parts[0]]
            if parts[1] != new_md5 or parts[2] != new_size:
                parts[1] = new_md5
                parts[2] = new_size
                changed_bundles.append(parts[0])
            updated.append("|".join(parts))
            continue
        updated.append(line)

    out_text = nl.join(updated) + (nl if had_trailing_nl else "")
    return out_text.encode("utf-8"), sorted(set(changed_bundles))


def apply_file_versions_only(game_dir: Path, dist_bundles_dir: Path, backup_dir: Path) -> dict:
    """Level 1: align file_versions.dat MD5s to official ss_win.mani without modifying ss_win.mani."""
    bundles = _collect_dist_bundles(dist_bundles_dir)
    before = inspect_status(game_dir, dist_bundles_dir, backup_dir)
    _ensure_backup(game_dir, backup_dir)

    mani_path = game_dir / "Persistent_Store" / "ss_win.mani"
    fv_path = game_dir / "file_versions.dat"
    ps_mani = _parse_manifest_entries(mani_path.read_text(encoding="utf-8", errors="ignore"))

    desired = {b: ps_mani[b]["md5"] for b in bundles if b in ps_mani}
    new_fv_bytes, changed = _update_file_versions_lines(fv_path.read_bytes(), desired)
    if changed:
        _atomic_write_bytes(fv_path, new_fv_bytes, game_dir=game_dir)

    after = inspect_status(game_dir, dist_bundles_dir, backup_dir)
    if after["file_versions_mismatches"]:
        raise RuntimeError(f"Readback failed: remaining mismatches {after['file_versions_mismatches']}")
    if before["install_resource_sha256"] != after["install_resource_sha256"]:
        raise RuntimeError("InstallResource SHA256 changed unexpectedly!")
    if before["ss_win_mani_sha256"] != after["ss_win_mani_sha256"]:
        raise RuntimeError("ss_win.mani changed unexpectedly in file-versions-only mode!")

    return {
        "ok": True,
        "mode": "file-versions-only",
        "changed_file_versions": changed,
        "status": after,
    }


def apply_persistent_override(game_dir: Path, dist_bundles_dir: Path, backup_dir: Path) -> dict:
    """Level 2: override shadowed bundles' MD5/size in ss_win.mani & file_versions.dat using VI file hashes."""
    bundles = _collect_dist_bundles(dist_bundles_dir)
    before = inspect_status(game_dir, dist_bundles_dir, backup_dir)
    meta = _ensure_backup(game_dir, backup_dir)

    orig_mani_path = Path(meta["ss_win_mani"]["path"])
    ir_mani_path = game_dir / "StellaSora_Data" / "StreamingAssets" / "InstallResource" / "install_resource_manifest.mani"
    ps_ab_dir = game_dir / "Persistent_Store" / "AssetBundles"
    mani_path = game_dir / "Persistent_Store" / "ss_win.mani"
    fv_path = game_dir / "file_versions.dat"

    orig_ps_mani = _parse_manifest_entries(orig_mani_path.read_text(encoding="utf-8", errors="ignore"))
    ir_mani = _parse_manifest_entries(ir_mani_path.read_text(encoding="utf-8", errors="ignore")) if ir_mani_path.is_file() else {}

    shadowed = [
        b
        for b in bundles
        if b in orig_ps_mani and b in ir_mani and orig_ps_mani[b]["md5"] == ir_mani[b]["md5"]
    ]

    overrides: dict[str, tuple[str, str]] = {}
    for b in shadowed:
        ps_file = ps_ab_dir / b
        dist_file = dist_bundles_dir / b
        if not ps_file.is_file():
            raise FileNotFoundError(f"Missing Persistent_Store bundle: {ps_file}")
        if _sha256_file(ps_file) != _sha256_file(dist_file):
            raise RuntimeError(f"Persistent_Store bundle {b} does not match dist/AssetBundles/{b}")
        overrides[b] = (_md5_file(ps_file), str(ps_file.stat().st_size))

    new_mani_bytes, changed_mani = _update_ss_win_mani_lines(mani_path.read_bytes(), overrides)
    if changed_mani:
        _atomic_write_bytes(mani_path, new_mani_bytes, game_dir=game_dir)

    updated_ps_mani = _parse_manifest_entries(mani_path.read_text(encoding="utf-8", errors="ignore"))
    desired_fv = {b: updated_ps_mani[b]["md5"] for b in bundles if b in updated_ps_mani}
    new_fv_bytes, changed_fv = _update_file_versions_lines(fv_path.read_bytes(), desired_fv)
    if changed_fv:
        _atomic_write_bytes(fv_path, new_fv_bytes, game_dir=game_dir)

    after = inspect_status(game_dir, dist_bundles_dir, backup_dir)
    if after["shadowed_bundles"]:
        raise RuntimeError(f"Readback failed: bundles still shadowed {after['shadowed_bundles']}")
    if after["file_versions_mismatches"]:
        raise RuntimeError(f"Readback failed: file_versions mismatches {after['file_versions_mismatches']}")
    if before["install_resource_sha256"] != after["install_resource_sha256"]:
        raise RuntimeError("InstallResource SHA256 changed unexpectedly!")

    for b, (vi_md5, _) in overrides.items():
        if updated_ps_mani.get(b, {}).get("md5") != vi_md5:
            raise RuntimeError(f"Readback failed: ss_win.mani MD5 mismatch for {b}")

    return {
        "ok": True,
        "mode": "persistent-override",
        "overridden_bundles": sorted(overrides.keys()),
        "changed_ss_win_mani": changed_mani,
        "changed_file_versions": changed_fv,
        "status": after,
    }


def restore_from_backup(game_dir: Path, dist_bundles_dir: Path, backup_dir: Path) -> dict:
    """Restore original file_versions.dat and Persistent_Store/ss_win.mani from backup_dir."""
    meta_path = backup_dir / "backup_meta.json"
    if not meta_path.is_file():
        raise FileNotFoundError(f"Missing backup metadata: {meta_path}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    fv_bak = Path(meta["file_versions"]["path"])
    mani_bak = Path(meta["ss_win_mani"]["path"])
    fv_dst = game_dir / "file_versions.dat"
    mani_dst = game_dir / "Persistent_Store" / "ss_win.mani"

    _atomic_write_bytes(fv_dst, fv_bak.read_bytes(), game_dir=game_dir)
    _atomic_write_bytes(mani_dst, mani_bak.read_bytes(), game_dir=game_dir)

    if _sha256_file(fv_dst) != meta["file_versions"]["sha256"]:
        raise RuntimeError("Restored file_versions.dat SHA256 mismatch!")
    if _sha256_file(mani_dst) != meta["ss_win_mani"]["sha256"]:
        raise RuntimeError("Restored ss_win.mani SHA256 mismatch!")

    return {
        "ok": True,
        "mode": "restore",
        "restored_file_versions_sha256": _sha256_file(fv_dst),
        "restored_ss_win_mani_sha256": _sha256_file(mani_dst),
        "status": inspect_status(game_dir, dist_bundles_dir, backup_dir),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Safe Persistent_Store texture routing helper")
    ap.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    ap.add_argument("--dist-bundles-dir", type=Path, default=DEFAULT_DIST_BUNDLES)
    ap.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)

    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--status", action="store_true", help="Read-only routing & shadow check")
    grp.add_argument("--mode", choices=["file-versions-only", "persistent-override"], help="Apply routing fix")
    grp.add_argument("--restore", action="store_true", help="Restore file_versions.dat and ss_win.mani from backup")

    args = ap.parse_args(argv)
    if args.status:
        res = inspect_status(args.game_dir, args.dist_bundles_dir, args.backup_dir)
    elif args.mode == "file-versions-only":
        res = apply_file_versions_only(args.game_dir, args.dist_bundles_dir, args.backup_dir)
    elif args.mode == "persistent-override":
        res = apply_persistent_override(args.game_dir, args.dist_bundles_dir, args.backup_dir)
    elif args.restore:
        res = restore_from_backup(args.game_dir, args.dist_bundles_dir, args.backup_dir)
    else:
        raise RuntimeError("No action selected")

    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
