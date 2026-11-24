#!/usr/bin/env python3
"""Step 7: Package rebuilt PC & Android texture AssetBundles into dist/ and deploy PC independently.

- NEVER touches data.arcx or lua.arcx content (only preserves their entries in dist manifests).
- NEVER cross-copies between Yostar and Steam clients (copies each independently from rebuilt_pc/).
- Backs up all overwritten dist/ files and client AssetBundles into backups/pre_texture_full_20261122/.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "work" / "textures" / "texture_full_20261122_r01"
DIST_DIR = ROOT / "dist"
BACKUP_DIR = ROOT / "backups" / "pre_texture_keepen_getitem_20261124"

RESTORE_OFFICIAL_BUNDLES = ["ui_activity_entrance.en.unity3d"]

CLIENT_DIRS = {
    "yostar": Path(r"C:\YostarGames\StellaSora_EN\Persistent_Store\AssetBundles"),
    "steam": Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\AssetBundles"),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def backup_file(src: Path, backup_root: Path, rel_name: str) -> None:
    if not src.exists():
        return
    dst = backup_root / rel_name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_zip(src_dir: Path, bundles: list[str], arc_prefix: str, out_zip: Path) -> tuple[int, str]:
    tmp_zip = out_zip.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for bname in bundles:
            zf.write(src_dir / bname, f"{arc_prefix}/{bname}")
    os.replace(tmp_zip, out_zip)
    return out_zip.stat().st_size, sha256_file(out_zip)


def sync_dir_exact(src_dir: Path, dst_dir: Path, bundles: list[str], backup_root: Path, backup_tag: str) -> None:
    if dst_dir.exists():
        for existing in sorted(dst_dir.glob("*.unity3d")):
            backup_file(existing, backup_root / backup_tag, existing.name)
            existing.unlink()
    dst_dir.mkdir(parents=True, exist_ok=True)
    for bname in bundles:
        shutil.copy2(src_dir / bname, dst_dir / bname)


def deploy_pc_client(src_dir: Path, dst_dir: Path, bundles: list[str], backup_root: Path, client_tag: str) -> int:
    assert dst_dir.parent.exists(), f"Client Store missing for {client_tag}: {dst_dir.parent}"
    dst_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for bname in bundles:
        target = dst_dir / bname
        if target.exists():
            backup_file(target, backup_root / client_tag, bname)
        shutil.copy2(src_dir / bname, target)
        copied += 1
    return copied


def update_manifests_and_checksums(
    bundles: list[str],
    pc_dir: Path,
    and_dir: Path,
    pc_counts: dict[str, int],
    pc_zip_info: tuple[int, str],
    and_zip_info: tuple[int, str],
) -> None:
    # 1. Update dist/patch_manifest.json
    pm_path = DIST_DIR / "patch_manifest.json"
    pm = json.loads(pm_path.read_text(encoding="utf-8"))

    preserved_pm_files = {
        k: v
        for k, v in pm.get("files", {}).items()
        if not k.startswith("Persistent_Store/AssetBundles/")
    }
    new_pm_bundles = {}
    new_pm_files = dict(preserved_pm_files)
    total_patched = 0
    for bname in bundles:
        bp = pc_dir / bname
        size = bp.stat().st_size
        digest = sha256_file(bp)
        tex_cnt = pc_counts.get(bname, 0)
        total_patched += tex_cnt
        new_pm_bundles[bname] = {
            "patched_sha256": digest,
            "size_bytes": size,
            "textures_patched": tex_cnt,
        }
        new_pm_files[f"Persistent_Store/AssetBundles/{bname}"] = {
            "source": f"AssetBundles/{bname}",
            "sha256": digest,
            "size": size,
        }

    pm["total_bundles"] = len(bundles)
    pm["total_textures_patched"] = total_patched
    pm["bundles"] = new_pm_bundles
    pm["files"] = new_pm_files
    pm["package_zip"]["size"] = pc_zip_info[0]
    pm["package_zip"]["sha256"] = pc_zip_info[1]
    pm_path.write_text(json.dumps(pm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 2. Update dist/android_patch_manifest.json
    apm_path = DIST_DIR / "android_patch_manifest.json"
    apm = json.loads(apm_path.read_text(encoding="utf-8"))
    preserved_apm_files = [
        entry
        for entry in apm.get("files", [])
        if not str(entry.get("path", "")).startswith("Persistent_Store/AssetBundles/")
    ]
    new_apm_files = list(preserved_apm_files)
    for bname in bundles:
        bp = and_dir / bname
        new_apm_files.append(
            {
                "path": f"Persistent_Store/AssetBundles/{bname}",
                "size": bp.stat().st_size,
                "sha256": sha256_file(bp),
                "asset_platform": "android",
            }
        )

    apm["files"] = new_apm_files
    apm["total_size"] = sum(int(x["size"]) for x in new_apm_files)
    apm["package_zip"]["size"] = and_zip_info[0]
    apm["package_zip"]["sha256"] = and_zip_info[1]
    apm_path.write_text(json.dumps(apm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # 3. Update ONLY the 4 texture/manifest lines in dist/SHA256SUMS.txt
    sums_path = DIST_DIR / "SHA256SUMS.txt"
    refresh_targets = {
        "patch_manifest.json": sha256_file(pm_path),
        "android_patch_manifest.json": sha256_file(apm_path),
        "StellaSora_AssetBundles_VI.zip": pc_zip_info[1],
        "StellaSora_Android_AssetBundles_VI.zip": and_zip_info[1],
    }
    updated_lines = []
    seen = set()
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        fname = parts[-1] if parts else ""
        if fname in refresh_targets:
            updated_lines.append(f"{refresh_targets[fname]}  {fname}")
            seen.add(fname)
        else:
            updated_lines.append(line)
    assert seen == set(refresh_targets), f"Missing SHA256SUMS entries: {set(refresh_targets) - seen}"
    sums_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def main() -> int:
    report_path = RUN_DIR / "build_readback_report.json"
    assert report_path.exists(), f"Missing Step 6 build report: {report_path}"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    parity = report.get("parity", {})
    assert parity.get("parity_failures_count", -1) == 0, f"Parity check not green: {parity}"

    pc_dir = RUN_DIR / "rebuilt_pc"
    and_dir = RUN_DIR / "rebuilt_android"
    pc_bundles = sorted(p.name for p in pc_dir.glob("*.unity3d"))
    and_bundles = sorted(p.name for p in and_dir.glob("*.unity3d"))
    assert pc_bundles and pc_bundles == and_bundles, "PC and Android rebuilt bundle sets differ or are empty!"

    pc_counts = {
        r["bundle"]: int(r["standalone_patched"]) + int(r["atlas_patched"])
        for r in report.get("bundles", [])
        if r.get("platform") == "pc"
    }

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for sub in ("dist", "yostar", "steam"):
        sub_dir = BACKUP_DIR / sub
        if sub_dir.exists():
            shutil.rmtree(sub_dir)

    for rel in [
        "patch_manifest.json",
        "android_patch_manifest.json",
        "SHA256SUMS.txt",
        "StellaSora_AssetBundles_VI.zip",
        "StellaSora_Android_AssetBundles_VI.zip",
    ]:
        backup_file(DIST_DIR / rel, BACKUP_DIR / "dist", rel)

    sync_dir_exact(pc_dir, DIST_DIR / "AssetBundles", pc_bundles, BACKUP_DIR / "dist", "AssetBundles")

    pc_zip_info = build_zip(pc_dir, pc_bundles, "AssetBundles", DIST_DIR / "StellaSora_AssetBundles_VI.zip")
    and_zip_info = build_zip(
        and_dir,
        and_bundles,
        "Persistent_Store/AssetBundles",
        DIST_DIR / "StellaSora_Android_AssetBundles_VI.zip",
    )

    update_manifests_and_checksums(pc_bundles, pc_dir, and_dir, pc_counts, pc_zip_info, and_zip_info)

    deployed = {}
    restored_official = {}
    for client_tag, client_dir in CLIENT_DIRS.items():
        deployed[client_tag] = deploy_pc_client(pc_dir, client_dir, pc_bundles, BACKUP_DIR, client_tag)
        restored_list = []
        for bname in RESTORE_OFFICIAL_BUNDLES:
            off_src = RUN_DIR / "official_pc" / bname
            assert off_src.exists(), f"Missing official bundle to restore: {off_src}"
            target = client_dir / bname
            if target.exists():
                backup_file(target, BACKUP_DIR / client_tag, bname)
            shutil.copy2(off_src, target)
            restored_list.append(bname)
        restored_official[client_tag] = restored_list

    yostar_root = CLIENT_DIRS["yostar"].parents[1]
    routing_warning = None
    try:
        from sync_persistent_texture_routing import inspect_status

        if (yostar_root / "Persistent_Store" / "ss_win.mani").is_file():
            r_status = inspect_status(
                yostar_root,
                DIST_DIR / "AssetBundles",
                ROOT / "backups" / "pre_routing_sync_20261124",
            )
            shadowed = [x["bundle"] for x in r_status.get("shadowed_bundles", [])]
            fv_mismatches = [x["bundle"] for x in r_status.get("file_versions_mismatches", [])]
            if shadowed or fv_mismatches:
                routing_warning = {
                    "shadowed_bundles": shadowed,
                    "file_versions_mismatches": fv_mismatches,
                    "hint": "Run tools/sync_persistent_texture_routing.py --status (and --mode file-versions-only or --mode persistent-override) without touching InstallResource.",
                }
    except Exception as exc:
        routing_warning = {"check_error": str(exc)}

    print(
        json.dumps(
            {
                "ok": True,
                "bundles": len(pc_bundles),
                "pc_zip_size": pc_zip_info[0],
                "pc_zip_sha256": pc_zip_info[1],
                "android_zip_size": and_zip_info[0],
                "android_zip_sha256": and_zip_info[1],
                "deployed": deployed,
                "restored_official_en": restored_official,
                "backup_dir": str(BACKUP_DIR),
                "routing_warning": routing_warning,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    if routing_warning and (routing_warning.get("shadowed_bundles") or routing_warning.get("file_versions_mismatches")):
        print(
            f"[WARNING] Yostar routing notice: shadowed={routing_warning.get('shadowed_bundles')}, "
            f"file_versions_mismatches={routing_warning.get('file_versions_mismatches')}. "
            f"{routing_warning.get('hint')}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
