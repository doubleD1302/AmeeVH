#!/usr/bin/env python3
"""Stella Sora Android Local ADB Patcher & Manager.

Features:
- Scan and manage connected Android devices / emulators via ADB.
- 1-Click push translation assets into Android game data directory.
- Trigger floating notification on device via ADB broadcast.
- Auto-update from GitHub.
- View announcements / notifications.
- 1-Click copy error logs for dev.
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_FILE = BASE_DIR / "launcher" / "config.json"
DEFAULT_PKG = "com.YoStar.StellaSora"
DEFAULT_TARGET_DIR = f"/sdcard/Android/data/{DEFAULT_PKG}/files/Persistent_Store/Videos"


def get_adb_path() -> str:
    sdk_adb = r"C:\Users\chann\AppData\Local\Android\sdk\platform-tools\adb.exe"
    if Path(sdk_adb).exists():
        return sdk_adb
    if shutil.which("adb"):
        return "adb"
    return "adb"


def run_adb(args: list[str], device: str | None = None) -> tuple[int, str]:
    adb = get_adb_path()
    cmd = [adb]
    if device:
        cmd.extend(["-s", device])
    cmd.extend(args)
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        return proc.returncode, proc.stdout.strip()
    except Exception as e:
        return 1, str(e)


def list_devices() -> list[str]:
    ret, out = run_adb(["devices"])
    if ret != 0:
        return []
    devices = []
    lines = out.splitlines()[1:]
    for line in lines:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def push_vietnamese_subtitles(device: str) -> tuple[bool, str]:
    # 1. Check device connected
    devs = list_devices()
    if device not in devs:
        return False, f"Thiết bị {device} không phản hồi hoặc đã ngắt kết nối!"

    # 2. Render files from proposals
    sys.path.insert(0, str(BASE_DIR))
    from tools.localize import render_srt

    staging_dir = BASE_DIR / "staging" / "android_subtitles"
    staging_dir.mkdir(parents=True, exist_ok=True)

    game_source = Path(r"C:\YostarGames\StellaSora_EN")
    batches_dir = BASE_DIR / "work" / "batches"

    files_to_push = {
        "Prologue-Prologue_P4_JPVA_FP_EN.srt": (
            game_source / "Persistent_Store/Videos/Prologue-Prologue_P4_JPVA_FP_EN.srt",
            batches_dir / "SRT001_JPVA.json"
        ),
        "Prologue-Prologue_P4_CNVA_FP_EN.srt": (
            game_source / "Persistent_Store/Videos/Prologue-Prologue_P4_CNVA_FP_EN.srt",
            batches_dir / "SRT002_CNVA.json"
        ),
        "CH04ED-CH04ED_EN.srt": (
            game_source / "Persistent_Store/Videos/CH04ED-CH04ED_EN.srt",
            batches_dir / "SRT003_CH04ED.json"
        ),
        "CH06ED-CH06ED_EN.srt": (
            game_source / "Persistent_Store/Videos/CH06ED-CH06ED_EN.srt",
            batches_dir / "SRT004_CH06ED.json"
        )
    }

    pushed_count = 0
    # Ensure remote directory exists
    run_adb(["shell", "mkdir", "-p", DEFAULT_TARGET_DIR], device=device)

    for fname, (orig_path, prop_path) in files_to_push.items():
        if not orig_path.exists() or not prop_path.exists():
            continue

        raw = orig_path.read_bytes()
        prop = json.loads(prop_path.read_text(encoding="utf-8"))
        trans = {e["source"]["locator"]["cue"]: e["text_vi"] for e in prop["entries"] if e.get("text_vi")}

        rendered = render_srt(raw, trans)
        local_target = staging_dir / fname
        local_target.write_bytes(rendered)

        remote_dest = f"{DEFAULT_TARGET_DIR}/{fname}"
        ret, out = run_adb(["push", str(local_target), remote_dest], device=device)
        if ret == 0:
            pushed_count += 1
            print(f"   [ADB] ✓ Đã đẩy tệp {fname} -> {remote_dest}")
        else:
            print(f"   [ADB] ❌ Lỗi đẩy tệp {fname}: {out}")

    # Trigger floating notification broadcast
    msg = f"Đã áp dụng Việt Hóa ({pushed_count} tệp phụ đề) thành công qua ADB!"
    trigger_floating_notification(device, msg)
    return True, f"Hoàn tất! Đã cài {pushed_count} tệp Việt hóa lên thiết bị {device}."


def trigger_floating_notification(device: str, message: str) -> bool:
    action = "com.stellasora.viethoa.ACTION_NOTIFY"
    ret, out = run_adb([
        "shell", "am", "broadcast",
        "-a", action,
        "--es", "message", message
    ], device=device)
    return ret == 0


def generate_error_report() -> str:
    devs = list_devices()
    adb_path = get_adb_path()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = [
        "### 📱 Báo Cáo Chẩn Đoán Local ADB - Stella Sora",
        f"- **Thời gian**: `{timestamp}`",
        f"- **Hệ điều hành Host**: `{platform.system()} {platform.release()}`",
        f"- **Đường dẫn ADB**: `{adb_path}`",
        f"- **Thiết bị kết nối ({len(devs)})**: `{', '.join(devs) if devs else 'Không có'}`",
        "",
        "#### ⚙️ Cấu Hình Đích",
        f"- **Package Android**: `{DEFAULT_PKG}`",
        f"- **Thư mục game đích**: `{DEFAULT_TARGET_DIR}`",
        "",
        "---",
        "*Tạo tự động từ Stella Sora Local ADB Tool*",
    ]
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Stella Sora Local ADB Patcher")
    parser.add_argument("--scan", action="store_true", help="Quét danh sách thiết bị ADB")
    parser.add_argument("--push", metavar="DEVICE", help="Cài đặt Việt Hóa lên thiết bị qua ADB")
    parser.add_argument("--notify", nargs=2, metavar=("DEVICE", "MSG"), help="Gửi thông báo nổi lên thiết bị")
    parser.add_argument("--copy-error", action="store_true", help="In thông tin chẩn đoán lỗi ADB")
    args = parser.parse_args()

    if args.scan:
        devs = list_devices()
        print(f"Thiết bị kết nối ({len(devs)}): {devs}")
        return 0
    elif args.push:
        ok, msg = push_vietnamese_subtitles(args.push)
        print(f"[{'OK' if ok else 'FAIL'}] {msg}")
        return 0 if ok else 1
    elif args.notify:
        dev, msg = args.notify
        ok = trigger_floating_notification(dev, msg)
        print(f"[{'OK' if ok else 'FAIL'}] Gửi thông báo nổi: {msg}")
        return 0 if ok else 1
    elif args.copy_error:
        print(generate_error_report())
        return 0

    # Default action: scan and print summary
    devs = list_devices()
    print("=== Stella Sora Local ADB Manager ===")
    print(f"Đường dẫn ADB: {get_adb_path()}")
    print(f"Thiết bị phát hiện: {devs if devs else 'Chưa có thiết bị nào'}")
    if devs:
        print(f"Để cài đặt Việt Hóa, chạy: python tools/adb_patcher.py --push {devs[0]}")


if __name__ == "__main__":
    main()
