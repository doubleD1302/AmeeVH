#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deploy the complete 2.1.0-compatible Vietnamese localization package
(data.arcx, lua.arcx, 105 Android AssetBundles, 10 SRT subtitles) to Android device 9f762c76 via ADB,
backing up existing device files and verifying 117/117 SHA256 hashes on-device."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

DEVICE_ID = "9f762c76"
PKG = "com.YoStarEN.StellaSora"
REMOTE_FILES = f"/sdcard/Android/data/{PKG}/files"
REMOTE_STORE = f"{REMOTE_FILES}/Persistent_Store"

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BACKUP_DIR = ROOT / "backups" / "android_9f762c76_20261125"

DATA_SRC = DIST / "data_patched_vi.arcx"
LUA_SRC = DIST / "lua_patched_vi.arcx"
ANDROID_ZIP = DIST / "StellaSora_Android_AssetBundles_VI.zip"
ANDROID_MANIFEST = DIST / "android_patch_manifest.json"
VIDEOS_DIR = DIST / "Videos"

EXPECTED_OFFICIAL_UI_ACT_ENT_SHA = (
    "35e97f384aab7cb29e44a96b0f759a53d8586a3fb411ac713fb0265a1f94a7ab"
)


def find_adb() -> str:
    sdk_adb = Path(r"C:\Users\chann\AppData\Local\Android\sdk\platform-tools\adb.exe")
    if sdk_adb.exists():
        return str(sdk_adb)
    found = shutil.which("adb")
    if found:
        return found
    return "adb"


ADB = find_adb()


def run_adb(args: list[str], timeout: int = 120) -> str:
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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def remote_sha256_batch(remote_paths: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    batch_size = 35
    for i in range(0, len(remote_paths), batch_size):
        chunk = remote_paths[i : i + batch_size]
        quoted = " ".join(f'"{p}"' for p in chunk)
        stdout = run_adb(["shell", f"sha256sum {quoted}"], timeout=120)
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                out[parts[1].strip()] = parts[0].strip().lower()
    return out


def preflight_check() -> None:
    state = run_adb(["get-state"]).strip()
    if state != "device":
        raise RuntimeError(f"Expected device state 'device', got {state!r}")

    # pidof exits 1 when process is not running; call subprocess directly
    pid_res = subprocess.run(
        [ADB, "-s", DEVICE_ID, "shell", f"pidof {PKG}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if pid_res.stdout.strip():
        raise RuntimeError(f"{PKG} is currently running (pid={pid_res.stdout.strip()}); close it first.")

    prefs = run_adb(["shell", f"cat {REMOTE_FILES}/prefs.dat"])
    if "LOCAL_GAME_VERSION:2.1.0" not in prefs:
        raise RuntimeError(f"Unexpected prefs.dat game version:\n{prefs}")

    mani_head = run_adb(["shell", f"head -n 10 {REMOTE_STORE}/ss_and.mani"])
    if "$RES_VER:2611141939" not in mani_head or "$GAME_VER:2.1.0" not in mani_head:
        raise RuntimeError(f"Unexpected ss_and.mani header:\n{mani_head}")

    for req in (DATA_SRC, LUA_SRC, ANDROID_ZIP, ANDROID_MANIFEST):
        if not req.is_file():
            raise FileNotFoundError(f"Missing required local file: {req}")
    print(f"[PREFLIGHT] Device {DEVICE_ID} online, {PKG} not running, GAME_VER=2.1.0 RES_VER=2611141939 OK.")


def prepare_local_sources(tmp_bundle_dir: Path) -> list[tuple[Path, str, str]]:
    """Return list of (local_path, remote_path, expected_sha256) for all 117 files."""
    manifest = json.loads(ANDROID_MANIFEST.read_text(encoding="utf-8"))
    manifest_by_path = {entry["path"]: entry for entry in manifest["files"]}

    plan: list[tuple[Path, str, str]] = []

    data_sha = sha256_file(DATA_SRC)
    if data_sha != manifest["data_arcx"]["sha256"]:
        raise RuntimeError("data_patched_vi.arcx SHA256 differs from android_patch_manifest.json")
    plan.append((DATA_SRC, f"{REMOTE_STORE}/Tables/data.arcx", data_sha))

    lua_sha = sha256_file(LUA_SRC)
    if lua_sha != manifest["lua_arcx"]["sha256"]:
        raise RuntimeError("lua_patched_vi.arcx SHA256 differs from android_patch_manifest.json")
    plan.append((LUA_SRC, f"{REMOTE_STORE}/Scripts/lua.arcx", lua_sha))

    with zipfile.ZipFile(ANDROID_ZIP) as zf:
        znames = sorted(zf.namelist())
        if len(znames) != 105:
            raise RuntimeError(f"Expected 105 bundles in Android zip, got {len(znames)}")
        for zname in znames:
            bname = Path(zname).name
            out_path = tmp_bundle_dir / bname
            data = zf.read(zname)
            out_path.write_bytes(data)
            bsha = hashlib.sha256(data).hexdigest()
            exp = manifest_by_path.get(zname)
            if not exp or exp["sha256"] != bsha or exp["size"] != len(data):
                raise RuntimeError(f"Zip vs manifest mismatch for {zname}")
            plan.append((out_path, f"{REMOTE_STORE}/AssetBundles/{bname}", bsha))

    srt_files = sorted(VIDEOS_DIR.glob("*.srt"))
    if len(srt_files) != 10:
        raise RuntimeError(f"Expected 10 SRT files in {VIDEOS_DIR}, got {len(srt_files)}")
    for sp in srt_files:
        plan.append((sp, f"{REMOTE_STORE}/Videos/{sp.name}", sha256_file(sp)))

    if len(plan) != 117:
        raise RuntimeError(f"Expected 117 total files, got {len(plan)}")
    print(f"[SOURCES] Verified all {len(plan)} local golden files (2 arcx + 105 bundles + 10 SRTs).")
    return plan


def backup_device_files(srt_names: list[str]) -> dict[str, str]:
    (BACKUP_DIR / "Tables").mkdir(parents=True, exist_ok=True)
    (BACKUP_DIR / "Scripts").mkdir(parents=True, exist_ok=True)
    (BACKUP_DIR / "Videos").mkdir(parents=True, exist_ok=True)

    pulls = [
        (f"{REMOTE_STORE}/Tables/data.arcx", BACKUP_DIR / "Tables" / "data.arcx"),
        (f"{REMOTE_STORE}/Scripts/lua.arcx", BACKUP_DIR / "Scripts" / "lua.arcx"),
    ]
    for sname in srt_names:
        pulls.append((f"{REMOTE_STORE}/Videos/{sname}", BACKUP_DIR / "Videos" / sname))

    pulled = 0
    for remote, local in pulls:
        if not local.exists():
            run_adb(["pull", remote, str(local)], timeout=180)
            pulled += 1
    print(f"[BACKUP] Device backup ready at {BACKUP_DIR} (pulled {pulled} files).")

    # Capture untouched system file hashes
    guard_paths = [
        f"{REMOTE_STORE}/ss_and.mani",
        f"{REMOTE_FILES}/file_versions.dat",
        f"{REMOTE_STORE}/AssetBundles/ui_activity_entrance.en.unity3d",
    ]
    guard_hashes = remote_sha256_batch(guard_paths)
    if guard_hashes.get(f"{REMOTE_STORE}/AssetBundles/ui_activity_entrance.en.unity3d") != EXPECTED_OFFICIAL_UI_ACT_ENT_SHA:
        raise RuntimeError(f"Unexpected pre-deploy ui_activity_entrance hash: {guard_hashes}")
    return guard_hashes


def push_all(plan: list[tuple[Path, str, str]]) -> None:
    # 1. Tables/data.arcx and Scripts/lua.arcx
    for local_path, remote_path, _ in plan[:2]:
        run_adb(["push", str(local_path), remote_path], timeout=300)
        print(f"[PUSH] {local_path.name} -> {remote_path}")

    # 2. 105 AssetBundles in batches of 25 explicit file paths into AssetBundles/
    bundle_items = plan[2:107]
    for i in range(0, len(bundle_items), 25):
        batch = bundle_items[i : i + 25]
        run_adb(
            ["push", *[str(p) for p, _, _ in batch], f"{REMOTE_STORE}/AssetBundles/"],
            timeout=300,
        )
        print(f"[PUSH] AssetBundles batch {i + 1}..{i + len(batch)}/105")

    # 3. 10 Videos/*.srt in one batch into Videos/
    srt_items = plan[107:]
    run_adb(
        ["push", *[str(p) for p, _, _ in srt_items], f"{REMOTE_STORE}/Videos/"],
        timeout=120,
    )
    print(f"[PUSH] Videos/*.srt ({len(srt_items)}/10)")


def verify_device(plan: list[tuple[Path, str, str]], pre_guards: dict[str, str]) -> None:
    remote_paths = [r for _, r, _ in plan]
    all_targets = remote_paths + list(pre_guards.keys())
    got = remote_sha256_batch(all_targets)

    mismatches = []
    for _, rpath, exp_sha in plan:
        actual = got.get(rpath)
        if actual != exp_sha:
            mismatches.append((rpath, exp_sha, actual))

    if mismatches:
        raise RuntimeError(f"Post-push SHA256 mismatch on {len(mismatches)} files: {mismatches[:5]}")

    for gpath, exp_sha in pre_guards.items():
        actual = got.get(gpath)
        if actual != exp_sha:
            raise RuntimeError(f"Guarded file changed unexpectedly: {gpath} ({exp_sha} -> {actual})")

    print(
        f"[VERIFY] 117/117 deployed files SHA256 MATCH on device {DEVICE_ID}! "
        "ss_and.mani, file_versions.dat, ui_activity_entrance.en.unity3d untouched."
    )


def main() -> int:
    preflight_check()
    tmp_dir = Path(tempfile.mkdtemp(prefix="stella_android_bundles_"))
    try:
        plan = prepare_local_sources(tmp_dir)
        srt_names = [p.name for p, _, _ in plan[107:]]
        pre_guards = backup_device_files(srt_names)
        push_all(plan)
        verify_device(plan, pre_guards)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
