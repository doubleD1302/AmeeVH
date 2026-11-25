#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix the 42 Trekker Item.<cid>.1 entries in dist/data_patched_vi.arcx that erroneously carry
the 'Mảnh ' prefix, update dist manifests & SHA256SUMS, and deploy directly to Yostar PC,
Steam PC, and connected Android device 9f762c76."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from tools.arcx_adapter import (  # noqa: E402
    XXTEA_KEY,
    ArcxArchive,
    repack_archive,
    xxtea_decrypt,
    xxtea_encrypt,
)

OFFICIAL_DATA = Path(
    r"C:/YostarGames/StellaResourceDownloads/EN/2.1.0_2611141949_text_a9a03c7c2b63/files/Tables/data.arcx"
)
DIST_DIR = ROOT / "dist"
DIST_DATA = DIST_DIR / "data_patched_vi.arcx"
YOSTAR_DATA = Path(r"C:/YostarGames/StellaSora_EN/Persistent_Store/Tables/data.arcx")
STEAM_DATA = Path(r"C:/Program Files (x86)/Steam/steamapps/common/Stella Sora/Persistent_Store/Tables/data.arcx")

BACKUP_DIR = ROOT / "backups" / "pre_item_trekker_manh_20261125"
STAGING_DIR = ROOT / "staging" / "item_trekker_manh_20261125"
STAGING_DATA = STAGING_DIR / "data_patched_vi.arcx"

CHAR_HASH = 0x40C643F18BF8D5FF
ITEM_HASH = 0xE60634348B826F41

DEVICE_ID = "9f762c76"
PKG = "com.YoStarEN.StellaSora"
REMOTE_FILES = f"/sdcard/Android/data/{PKG}/files"
REMOTE_STORE = f"{REMOTE_FILES}/Persistent_Store"
REMOTE_DATA = f"{REMOTE_STORE}/Tables/data.arcx"


def find_adb() -> str:
    sdk_adb = Path(r"C:\Users\chann\AppData\Local\Android\sdk\platform-tools\adb.exe")
    if sdk_adb.exists():
        return str(sdk_adb)
    return shutil.which("adb") or "adb"


ADB = find_adb()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def run_adb(args: list[str], timeout: int = 180) -> str:
    cmd = [ADB, "-s", DEVICE_ID, *args]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"ADB command failed ({res.returncode}): {' '.join(cmd)}\n"
            f"STDOUT: {res.stdout}\nSTDERR: {res.stderr}"
        )
    return res.stdout


def load_arc(path: Path):
    arc = ArcxArchive(path)
    raw = path.read_bytes()
    return arc, {e["hash"]: (e, arc.extract_entry(e, raw)) for e in arc.entries}


def backup_before_modify() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    targets = [
        (DIST_DATA, "dist__data_patched_vi.arcx"),
        (DIST_DIR / "patch_manifest.json", "patch_manifest.json"),
        (DIST_DIR / "android_patch_manifest.json", "android_patch_manifest.json"),
        (DIST_DIR / "SHA256SUMS.txt", "SHA256SUMS.txt"),
        (YOSTAR_DATA, "yostar__data.arcx"),
        (STEAM_DATA, "steam__data.arcx"),
    ]
    for src, name in targets:
        if not src.exists():
            raise FileNotFoundError(f"Missing required source for backup: {src}")
        dst = BACKUP_DIR / name
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"[BACKUP] {src} -> {dst} (sha256={sha256_file(dst)})")
        else:
            print(f"[BACKUP] Preserved existing backup: {dst}")


def patch_data_archive() -> dict[str, str]:
    off_arc, off_map = load_arc(OFFICIAL_DATA)
    base_arc, base_map = load_arc(BACKUP_DIR / "dist__data_patched_vi.arcx")

    off_char = json.loads(xxtea_decrypt(off_map[CHAR_HASH][1], XXTEA_KEY).decode("utf-8"))
    off_item = json.loads(xxtea_decrypt(off_map[ITEM_HASH][1], XXTEA_KEY).decode("utf-8"))

    vi_char = json.loads(xxtea_decrypt(base_map[CHAR_HASH][1], XXTEA_KEY).decode("utf-8"))
    vi_item = json.loads(xxtea_decrypt(base_map[ITEM_HASH][1], XXTEA_KEY).decode("utf-8"))

    char_ids = sorted(
        {k.split(".")[1] for k in off_char if k.endswith(".1")},
        key=lambda x: int(x) if x.isdigit() else 999999,
    )

    fixed_map: dict[str, str] = {}
    for cid in char_ids:
        ikey = f"Item.{cid}.1"
        ckey = f"Character.{cid}.1"
        if ikey not in vi_item:
            continue
        if off_item.get(ikey) != off_char.get(ckey):
            raise RuntimeError(
                f"Official EN mismatch for {cid}: Item={off_item.get(ikey)!r}, Char={off_char.get(ckey)!r}"
            )
        expected_old = f"Mảnh {vi_char[ckey]}"
        if vi_item[ikey] != expected_old:
            raise RuntimeError(
                f"Unexpected current VI for {ikey}: got {vi_item[ikey]!r}, expected {expected_old!r}"
            )
        clean_name = unicodedata.normalize("NFC", vi_char[ckey])
        vi_item[ikey] = clean_name
        fixed_map[ikey] = clean_name

    if len(fixed_map) != 42:
        raise RuntimeError(f"Expected exactly 42 fixed Trekker Item entries, got {len(fixed_map)}")
    if vi_item.get("Item.11103.1") != "Mảnh Ghép 1/365 Của Cậu":
        raise RuntimeError("Item.11103.1 unexpected value")
    if not str(vi_item.get("Item.2.3", "")).startswith("Mảnh vỡ tỏa ra sức mạnh"):
        raise RuntimeError("Item.2.3 unexpected value")

    serialized_item = json.dumps(vi_item, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encrypted_item = xxtea_encrypt(serialized_item, XXTEA_KEY)

    work = Path(tempfile.mkdtemp(prefix="data_fix_manh_"))
    entries_dir = work / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "archive_name": "data.arcx",
        "version": base_arc.version,
        "flag": base_arc.flag,
        "entry_count": base_arc.entry_count,
        "payload_decrypted": False,
        "entries": [],
    }

    try:
        for h in sorted(base_map, key=lambda x: base_map[x][0]["index"]):
            e, base_enc = base_map[h]
            payload = encrypted_item if h == ITEM_HASH else base_enc
            fname = f"{e['index']:05d}_{e['hash_hex']}.bin"
            (entries_dir / fname).write_bytes(payload)
            manifest["entries"].append(
                {
                    "index": e["index"],
                    "hash": h,
                    "hash_hex": e["hash_hex"],
                    "filename": fname,
                    "origin_size": len(payload),
                    "payload_size": len(payload),
                }
            )
        (work / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        repack_archive(work, STAGING_DATA, encrypt_payload=False)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print(f"[PATCH] Fixed {len(fixed_map)}/42 Trekker Item.<cid>.1 entries -> {STAGING_DATA}")
    return fixed_map


def update_dist_and_manifests() -> tuple[int, str]:
    shutil.copy2(STAGING_DATA, DIST_DATA)
    new_size = DIST_DATA.stat().st_size
    new_sha = sha256_file(DIST_DATA)
    print(f"[DIST] Installed {DIST_DATA} (size={new_size:,}, sha256={new_sha})")

    # 1. patch_manifest.json
    pm_path = DIST_DIR / "patch_manifest.json"
    pm = json.loads(pm_path.read_text(encoding="utf-8"))
    pm["files"]["Persistent_Store/Tables/data.arcx"]["sha256"] = new_sha
    pm["files"]["Persistent_Store/Tables/data.arcx"]["size"] = new_size
    pm["data_arcx"]["sha256"] = new_sha
    pm["data_arcx"]["size_bytes"] = new_size
    pm_path.write_text(json.dumps(pm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 2. android_patch_manifest.json
    apm_path = DIST_DIR / "android_patch_manifest.json"
    apm = json.loads(apm_path.read_text(encoding="utf-8"))
    old_size = None
    for item in apm["files"]:
        if item.get("path") == "Persistent_Store/Tables/data.arcx":
            old_size = item["size"]
            item["sha256"] = new_sha
            item["size"] = new_size
            break
    if old_size is None:
        raise RuntimeError("Missing Persistent_Store/Tables/data.arcx in android_patch_manifest.json")
    apm["total_size"] = apm["total_size"] + (new_size - old_size)
    apm["data_arcx"]["sha256"] = new_sha
    apm["data_arcx"]["size_bytes"] = new_size
    apm_path.write_text(json.dumps(apm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 3. SHA256SUMS.txt
    pm_sha = sha256_file(pm_path)
    apm_sha = sha256_file(apm_path)
    sums_path = DIST_DIR / "SHA256SUMS.txt"
    out_lines = []
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if line.rstrip().endswith("  data_patched_vi.arcx"):
            out_lines.append(f"{new_sha}  data_patched_vi.arcx")
        elif line.rstrip().endswith("  patch_manifest.json"):
            out_lines.append(f"{pm_sha}  patch_manifest.json")
        elif line.rstrip().endswith("  android_patch_manifest.json"):
            out_lines.append(f"{apm_sha}  android_patch_manifest.json")
        else:
            out_lines.append(line)
    sums_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"[MANIFEST] Updated patch_manifest.json ({pm_sha}), android_patch_manifest.json ({apm_sha}), SHA256SUMS.txt")
    return new_size, new_sha


def readback_verify_dist(fixed_map: dict[str, str]) -> None:
    bk_arc, bk_map = load_arc(BACKUP_DIR / "dist__data_patched_vi.arcx")
    new_arc, new_map = load_arc(DIST_DATA)

    if new_arc.entry_count != bk_arc.entry_count or list(new_map.keys()) != list(bk_map.keys()):
        raise RuntimeError("Archive entry structure changed after repack!")

    untouched = 0
    for h in new_map:
        if h != ITEM_HASH:
            if new_map[h][1] != bk_map[h][1]:
                raise RuntimeError(f"Untouched table modified: {hex(h)}")
            untouched += 1

    vi_char = json.loads(xxtea_decrypt(new_map[CHAR_HASH][1], XXTEA_KEY).decode("utf-8"))
    vi_item = json.loads(xxtea_decrypt(new_map[ITEM_HASH][1], XXTEA_KEY).decode("utf-8"))

    for ikey, expected in fixed_map.items():
        cid = ikey.split(".")[1]
        if vi_item.get(ikey) != expected or vi_item.get(ikey) != vi_char.get(f"Character.{cid}.1"):
            raise RuntimeError(f"Readback mismatch at {ikey}: {vi_item.get(ikey)!r} vs {expected!r}")
        if "mảnh" in vi_item[ikey].lower():
            raise RuntimeError(f"Unexpected 'Mảnh' still present at {ikey}: {vi_item[ikey]!r}")

    if vi_item.get("Item.11103.1") != "Mảnh Ghép 1/365 Của Cậu":
        raise RuntimeError("Legitimate Item.11103.1 was modified!")

    print(
        f"[READBACK] PASSED: 42/42 Trekker Item.<cid>.1 match Character.<cid>.1, "
        f"{untouched} untouched tables byte-identical."
    )


def deploy_pc_and_android(expected_sha: str) -> None:
    # 1. PC (Yostar & Steam) directly from dist/data_patched_vi.arcx
    for label, dst in (("Yostar PC", YOSTAR_DATA), ("Steam PC", STEAM_DATA)):
        shutil.copy2(DIST_DATA, dst)
        got = sha256_file(dst)
        if got != expected_sha:
            raise RuntimeError(f"{label} deploy hash mismatch: {got} != {expected_sha}")
        print(f"[DEPLOY] {label}: {dst} (sha256={got})")

    # 2. Android device 9f762c76
    state = run_adb(["get-state"]).strip()
    if state != "device":
        raise RuntimeError(f"Android device {DEVICE_ID} not ready: {state!r}")

    run_adb(["shell", f"am force-stop {PKG}"])
    print(f"[ANDROID] Stopped {PKG} cleanly on {DEVICE_ID}.")

    guard_paths = [f"{REMOTE_STORE}/ss_and.mani", f"{REMOTE_FILES}/file_versions.dat"]
    pre_guards = {}
    for line in run_adb(["shell", "sha256sum " + " ".join(f'"{p}"' for p in guard_paths)]).splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            pre_guards[parts[1].strip()] = parts[0].strip().lower()

    run_adb(["push", str(DIST_DATA), REMOTE_DATA], timeout=300)

    post_out = run_adb(
        ["shell", "sha256sum " + " ".join(f'"{p}"' for p in [REMOTE_DATA, *guard_paths])]
    )
    post_hashes = {}
    for line in post_out.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            post_hashes[parts[1].strip()] = parts[0].strip().lower()

    if post_hashes.get(REMOTE_DATA) != expected_sha:
        raise RuntimeError(
            f"Android data.arcx SHA256 mismatch: {post_hashes.get(REMOTE_DATA)} != {expected_sha}"
        )
    for gp, exp in pre_guards.items():
        if post_hashes.get(gp) != exp:
            raise RuntimeError(f"Android guarded file mutated: {gp}")

    print(f"[DEPLOY] Android {DEVICE_ID}: {REMOTE_DATA} (sha256={post_hashes[REMOTE_DATA]}) — ss_and.mani & file_versions.dat untouched.")


def main() -> int:
    backup_before_modify()
    fixed_map = patch_data_archive()
    _, new_sha = update_dist_and_manifests()
    readback_verify_dist(fixed_map)
    deploy_pc_and_android(new_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
