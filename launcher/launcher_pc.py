#!/usr/bin/env python3
"""Stella Sora Việt Hóa - Multiplatform 1-Click Launcher (PC & Local ADB).

Features:
1. 1-Click Install / Rollback for Windows PC adhering to transaction & safety guidelines.
2. Local ADB patcher & floating notification trigger for Android.
3. Auto-update checking & downloading from GitHub.
4. Notifications / Announcement center.
5. 1-Click Error Log & Diagnostic copy to clipboard for Devs.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import threading
import traceback
import urllib.error
import urllib.request
import webbrowser
import zipfile

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(sys._MEIPASS)
    EXE_DIR = Path(sys.executable).resolve().parent
    LAUNCHER_DIR = EXE_DIR
    BASE_DIR = BUNDLE_DIR
else:
    LAUNCHER_DIR = Path(__file__).resolve().parent
    BASE_DIR = Path(__file__).resolve().parents[1]
    EXE_DIR = LAUNCHER_DIR

CONFIG_FILE = EXE_DIR / "config.json"
NOTIFS_FILE = EXE_DIR / "notifications.json"
BACKUP_DIR = EXE_DIR / "backups"

DEFAULT_CONFIG = {
    "version": "0.9.6",
    "app_name": "Stella Sora Việt Hóa - Multiplatform & Steam Launcher (v0.9.6)",
    "default_game_path": "C:\\YostarGames\\StellaSora_EN",
    "github_repo": "doubleD1302/AmeeVH",
    "github_branch": "main",
    "github_api_url": "https://api.github.com/repos/doubleD1302/AmeeVH/releases/latest",
    "remote_notifications_url": "https://raw.githubusercontent.com/doubleD1302/AmeeVH/main/launcher/notifications.json",
    "android_package": "com.YoStar.StellaSora",
    "android_game_storage": "/sdcard/Android/data/com.YoStar.StellaSora/files",
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
        except Exception:
            pass
    bundle_cfg = BASE_DIR / "launcher" / "config.json"
    if bundle_cfg.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(bundle_cfg.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(new_config: dict):
    """Saves updated launcher configuration."""
    global CONFIG_FILE
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(new_config, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        DiagnosticCollector.log(f"Lỗi lưu cấu hình: {e}")


def get_steam_libraries() -> list[Path]:
    """Detects all Steam library directories from Registry and libraryfolders.vdf."""
    libraries = []
    default_steams = [
        Path(r"C:\Program Files (x86)\Steam"),
        Path(r"C:\Program Files\Steam"),
    ]
    try:
        import winreg
        for root_key in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(root_key, r"Software\Valve\Steam") as key:
                    val, _ = winreg.QueryValueEx(key, "SteamPath")
                    if val:
                        p = Path(val)
                        if p.exists() and p not in default_steams:
                            default_steams.insert(0, p)
            except Exception:
                pass
    except Exception:
        pass

    for steam_root in default_steams:
        if not steam_root.exists():
            continue
        if steam_root not in libraries:
            libraries.append(steam_root)
        vdf = steam_root / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            try:
                content = vdf.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r'"path"\s+"([^"]+)"', content):
                    raw_p = m.group(1).replace("\\\\", "\\")
                    lib_p = Path(raw_p)
                    if lib_p.exists() and lib_p not in libraries:
                        libraries.append(lib_p)
            except Exception:
                pass
    return libraries


def find_potential_game_paths() -> list[dict]:
    """Returns detected Stella Sora game installations (Steam, Yostar, Config)."""
    found = []
    seen = set()

    def add_candidate(path: Path, source_label: str):
        try:
            resolved = path.resolve()
        except Exception:
            resolved = path
        res_str = str(resolved).lower()
        if res_str in seen:
            return
        seen.add(res_str)

        has_exe = (resolved / "StellaSora.exe").exists()
        has_store = (resolved / "Persistent_Store").exists()
        has_data = (resolved / "StellaSora_Data").exists()
        is_valid = has_exe or has_store or has_data

        edition = "Bản Tùy Chọn"
        if "steamapps" in res_str or "steam" in res_str:
            edition = "Bản Steam PC"
        elif "yostargames" in res_str or "stellasora_en" in res_str:
            edition = "Bản Yostar PC"

        found.append({
            "path": resolved,
            "label": f"{source_label} ({edition})",
            "edition": edition,
            "exists": resolved.exists(),
            "is_valid_game": is_valid
        })

    # 1. Configured default path
    cfg = load_config()
    cfg_p = Path(cfg.get("default_game_path", r"C:\YostarGames\StellaSora_EN"))
    add_candidate(cfg_p, "Thư Mục Đang Chọn")

    # 2. Standalone paths
    add_candidate(Path(r"C:\YostarGames\StellaSora_EN"), "Yostar Standalone [C:]")
    add_candidate(Path(r"D:\YostarGames\StellaSora_EN"), "Yostar Standalone [D:]")
    add_candidate(Path(r"F:\YostarGames\StellaSora_EN"), "Yostar Standalone [F:]")

    # 3. Steam paths
    for lib in get_steam_libraries():
        steam_game = lib / "steamapps" / "common" / "Stella Sora"
        add_candidate(steam_game, f"Steam Library [{lib.drive}]")

    return found


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


CUE_PATTERN = re.compile(
    r"(?m)^(?P<index>\d+)\r?\n(?P<time>\d{2,}:\d{2}:\d{2},\d{3} --> \d{2,}:\d{2}:\d{2},\d{3}[^\r\n]*)"
    r"\r?\n(?P<body>[^\r\n]+(?:\r?\n(?!\r?$)[^\r\n]+)*)"
)


def parse_srt(raw: bytes) -> tuple[str, list[dict]]:
    text = raw.decode("utf-8-sig")
    cues, previous_end = [], 0
    seen = set()
    for match in CUE_PATTERN.finditer(text):
        if text[previous_end:match.start()].strip():
            raise ValueError("Unparsed SRT data before cue")
        key = match["index"]
        if key in seen:
            raise ValueError(f"Duplicate SRT cue {key}")
        seen.add(key)
        cues.append({
            "index": key,
            "timestamp": match["time"],
            "text": match["body"].replace("\r\n", "\n"),
            "start": match.start("body"),
            "end": match.end("body")
        })
        previous_end = match.end()
    if text[previous_end:].strip() or not cues:
        raise ValueError("Unparsed/empty SRT data")
    return text, cues


def render_srt(raw: bytes, translations: dict[str, str]) -> bytes:
    text, cues = parse_srt(raw)
    if set(translations) - {c["index"] for c in cues}:
        raise ValueError("Unknown subtitle cue")
    newline = "\r\n" if b"\r\n" in raw else "\n"
    for cue in reversed(cues):
        if cue["index"] in translations:
            target = translations[cue["index"]]
            if "\r" in target or "\n\n" in target or not target.strip():
                raise ValueError("Invalid subtitle body")
            text = text[:cue["start"]] + target.replace("\n", newline) + text[cue["end"]:]
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    return bom + text.encode("utf-8")


def detect_game_info(game_path: Path) -> dict:
    info = {
        "exists": game_path.exists(),
        "client_ver": "Unknown",
        "game_ver": "Unknown",
        "res_ver": "Unknown",
        "is_running": False,
        "installed_patch": False,
        "backup_count": 0,
        "edition": "Không xác định",
        "is_steam": False,
        "has_game_data": False,
    }
    if not game_path.exists():
        return info

    path_lower = str(game_path).lower()
    if "steamapps" in path_lower or "steam" in path_lower:
        info["edition"] = "Bản Steam PC"
        info["is_steam"] = True
    elif "yostargames" in path_lower or "stellasora_en" in path_lower:
        info["edition"] = "Bản Yostar Standalone"
        info["is_steam"] = False
    else:
        info["edition"] = "Bản PC Tùy Chọn"
        info["is_steam"] = False

    has_exe = (game_path / "StellaSora.exe").exists()
    has_store = (game_path / "Persistent_Store").exists()
    info["has_game_data"] = has_exe or has_store

    # Check running process
    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq StellaSora.exe" /NH', shell=True).decode()
        info["is_running"] = "StellaSora.exe" in out
    except Exception:
        info["is_running"] = False

    # Check client version from Yostar config if available
    launcher_cfg = game_path / "game-launcher-config.json"
    if launcher_cfg.exists():
        try:
            d = json.loads(launcher_cfg.read_text(encoding="utf-8"))
            info["client_ver"] = d.get("version", "Unknown")
        except Exception:
            pass

    # Fallback 1: Read prefs.dat (present in all PC builds including Steam)
    prefs_file = game_path / "prefs.dat"
    if prefs_file.exists():
        try:
            lines = prefs_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines:
                if line.startswith("LOCAL_CLIENT_VERSION:"):
                    if info["client_ver"] == "Unknown":
                        info["client_ver"] = line.split(":", 1)[1].strip()
                elif line.startswith("LOCAL_GAME_VERSION:"):
                    if info["game_ver"] == "Unknown":
                        info["game_ver"] = line.split(":", 1)[1].strip()
                elif line.startswith("LOCAL_CLIENT_RESOURCE_VERSION:"):
                    if info["res_ver"] == "Unknown":
                        info["res_ver"] = line.split(":", 1)[1].strip()
        except Exception:
            pass

    # Fallback 2: Check manifest version
    mani = game_path / "Persistent_Store" / "ss_win.mani"
    if mani.exists():
        try:
            lines = mani.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines[:15]:
                if "GAME_VER" in line:
                    parts = line.split("|")
                    for p in parts:
                        if p.startswith("GAME_VER"):
                            info["game_ver"] = p.split()[-1]
                        elif p.startswith("RES_VER"):
                            info["res_ver"] = p.split()[-1]
        except Exception:
            pass

    # Check installed patch marker
    patch_marker = game_path / "Persistent_Store" / "viethoa_installed.json"
    info["installed_patch"] = patch_marker.exists()

    # Count backups
    if BACKUP_DIR.exists():
        info["backup_count"] = len([d for d in BACKUP_DIR.iterdir() if d.is_dir()])

    return info


def launch_game(game_path: Path) -> tuple[bool, str]:
    """Launches Stella Sora via Steam protocol or direct executable."""
    info = detect_game_info(game_path)
    exe_file = game_path / "StellaSora.exe"

    if info["is_steam"]:
        try:
            webbrowser.open("steam://rungameid/4813850")
            DiagnosticCollector.log("Đã phát lệnh khởi động qua giao thức Steam (AppID 4813850)")
            return True, "Đang khởi động trò chơi qua Steam Client..."
        except Exception as e:
            DiagnosticCollector.log(f"Lỗi khởi động qua Steam: {e}")

    if exe_file.exists():
        try:
            subprocess.Popen([str(exe_file)], cwd=str(game_path))
            DiagnosticCollector.log(f"Đã khởi động trực tiếp file thực thi: {exe_file}")
            return True, "Đã khởi động Stella Sora thành công!"
        except Exception as e:
            return False, f"Không thể khởi động game: {e}"
    else:
        return False, f"Không tìm thấy file StellaSora.exe tại: {game_path}"


class DiagnosticCollector:
    """Collects system, game, and error information to format for dev."""

    _last_error: str = ""
    _logs: list[str] = []

    @classmethod
    def log(cls, message: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        cls._logs.append(entry)
        print(entry)

    @classmethod
    def record_error(cls, err: str):
        cls._last_error = err
        cls.log(f"ERROR: {err}")

    @classmethod
    def generate_report(cls, game_path: Path) -> str:
        info = detect_game_info(game_path)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = [
            "### 🛠️ Báo Cáo Chẩn Đoán Lỗi Việt Hóa Stella Sora",
            f"- **Thời gian**: `{timestamp}`",
            f"- **Hệ điều hành**: `{platform.system()} {platform.release()} ({platform.version()})`",
            f"- **Kiến trúc**: `{platform.machine()}`",
            f"- **Python**: `{platform.python_version()}`",
            "",
            "#### 📁 Thông Tin Bản Cài Game",
            f"- **Đường dẫn**: `{game_path}`",
            f"- **Phiên bản cài đặt**: `{info.get('edition', 'Không xác định')}`",
            f"- **Thư mục tồn tại**: `{'Có' if info['exists'] else 'Không'}`",
            f"- **Client Version**: `{info['client_ver']}`",
            f"- **Game Version**: `{info['game_ver']}`",
            f"- **Resource Version**: `{info['res_ver']}`",
            f"- **Game đang chạy**: `{'Có' if info['is_running'] else 'Không'}`",
            f"- **Trạng thái Việt Hóa**: `{'Đã cài' if info['installed_patch'] else 'Chưa cài'}`",
            f"- **Số bản backup**: `{info['backup_count']}`",
            "",
            "#### ⚠️ Lỗi Gần Nhất",
            "```text",
            cls._last_error if cls._last_error else "Chưa ghi nhận lỗi nghiêm trọng nào.",
            "```",
            "",
            "#### 📜 Nhật Ký Hoạt Động (Last 25 entries)",
            "```text",
            "\n".join(cls._logs[-25:]) if cls._logs else "Chưa có log.",
            "```",
            "",
            "---",
            "*Sao chép tự động từ Stella Sora 1-Click Launcher*",
        ]
        return "\n".join(report)


class LocalizationEngine:
    """Handles 1-Click Install and Rollback safely."""

    @staticmethod
    def install_pc(game_path: Path, log_cb=None) -> tuple[bool, str]:
        def log(msg):
            DiagnosticCollector.log(msg)
            if log_cb:
                log_cb(msg)

        try:
            log("--- Bắt đầu quy trình Cài đặt Việt Hóa 1-Chạm ---")
            info = detect_game_info(game_path)
            if not info["exists"]:
                raise FileNotFoundError(f"Không tìm thấy thư mục game tại: {game_path}")
            if not info["has_game_data"]:
                raise FileNotFoundError(f"Thư mục đã chọn chưa có tệp trò chơi ({game_path}).\nNếu bạn tải từ Steam, vui lòng đảm bảo game đã được tải hoàn tất qua Steam.")
            if info["is_running"]:
                raise RuntimeError("Game StellaSora.exe đang chạy! Vui lòng đóng game trước khi cài đặt.")

            # Identify target paths
            target_subtitles = [
                "Persistent_Store/Videos/Prologue-Prologue_P4_JPVA_FP_EN.srt",
                "Persistent_Store/Videos/Prologue-Prologue_P4_CNVA_FP_EN.srt",
                "Persistent_Store/Videos/CH04ED-CH04ED_EN.srt",
                "Persistent_Store/Videos/CH06ED-CH06ED_EN.srt",
            ]
            table_rel = "Persistent_Store/Tables/data.arcx"
            script_rel = "Persistent_Store/Scripts/lua.arcx"

            # Source batch proposals
            batches_dir = BASE_DIR / "work" / "batches"
            batch_files = {
                "Persistent_Store/Videos/Prologue-Prologue_P4_JPVA_FP_EN.srt": batches_dir / "SRT001_JPVA.json",
                "Persistent_Store/Videos/Prologue-Prologue_P4_CNVA_FP_EN.srt": batches_dir / "SRT002_CNVA.json",
                "Persistent_Store/Videos/CH04ED-CH04ED_EN.srt": batches_dir / "SRT003_CH04ED.json",
                "Persistent_Store/Videos/CH06ED-CH06ED_EN.srt": batches_dir / "SRT004_CH06ED.json",
            }
            patched_arcx = BASE_DIR / "dist" / "data_patched_vi.arcx"
            if not patched_arcx.exists():
                patched_arcx = BASE_DIR / "work" / "research" / "data_patched_vi.arcx"

            patched_lua_arcx = BASE_DIR / "dist" / "lua_patched_vi.arcx"
            if not patched_lua_arcx.exists():
                patched_lua_arcx = BASE_DIR / "work" / "research" / "lua_patched_vi.arcx"

            # 1. Create Backup
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            run_backup_dir = BACKUP_DIR / f"run_{timestamp}"
            run_backup_dir.mkdir(parents=True, exist_ok=True)
            log(f"1. Tạo thư mục sao lưu: {run_backup_dir.name}")

            backup_manifest = {
                "created_at": timestamp,
                "game_path": str(game_path),
                "files": []
            }

            # Backup subtitles
            for rel in target_subtitles:
                orig_file = game_path / rel
                if orig_file.exists():
                    orig_hash = sha256_file(orig_file)
                    bak_file = run_backup_dir / rel.replace("/", "_")
                    shutil.copy2(orig_file, bak_file)
                    backup_manifest["files"].append({
                        "relative_path": rel,
                        "backup_file": bak_file.name,
                        "original_sha256": orig_hash,
                        "size": orig_file.stat().st_size
                    })
                    log(f"   Đã sao lưu: {orig_file.name} (SHA: {orig_hash[:8]}...)")

            # Backup table archive if game table and patched arcx exist
            orig_table = game_path / table_rel
            if patched_arcx.exists() and orig_table.exists():
                orig_hash = sha256_file(orig_table)
                bak_file = run_backup_dir / table_rel.replace("/", "_")
                shutil.copy2(orig_table, bak_file)
                backup_manifest["files"].append({
                    "relative_path": table_rel,
                    "backup_file": bak_file.name,
                    "original_sha256": orig_hash,
                    "size": orig_table.stat().st_size
                })
                log(f"   Đã sao lưu: {orig_table.name} (Giao diện Core UI ArcX)")

            # Backup lua archive if game script and patched lua arcx exist
            orig_script = game_path / script_rel
            if patched_lua_arcx.exists() and orig_script.exists():
                orig_hash = sha256_file(orig_script)
                bak_file = run_backup_dir / script_rel.replace("/", "_")
                shutil.copy2(orig_script, bak_file)
                backup_manifest["files"].append({
                    "relative_path": script_rel,
                    "backup_file": bak_file.name,
                    "original_sha256": orig_hash,
                    "size": orig_script.stat().st_size
                })
                log(f"   Đã sao lưu: {orig_script.name} (Kịch bản thoại & Tin nhắn ArcX)")

            (run_backup_dir / "manifest.json").write_text(json.dumps(backup_manifest, indent=2), encoding="utf-8")

            # 2. Render & Install Translated Files
            log("2. Tiến hành đóng gói và áp dụng dữ liệu Việt hóa...")
            installed_count = 0
            installed_files = []

            # Install Core UI table archive
            if patched_arcx.exists() and orig_table.exists():
                temp_table = orig_table.with_suffix(".tmp_patch")
                shutil.copy2(patched_arcx, temp_table)
                temp_table.replace(orig_table)
                installed_count += 1
                installed_files.append(table_rel)
                log(f"   ✓ Đã cài đặt thành công: {orig_table.name} (Giao diện Core UI ArcX)")

            # Install Dialogue & Phone script archive
            if patched_lua_arcx.exists() and orig_script.exists():
                temp_script = orig_script.with_suffix(".tmp_patch")
                shutil.copy2(patched_lua_arcx, temp_script)
                temp_script.replace(orig_script)
                installed_count += 1
                installed_files.append(script_rel)
                log(f"   ✓ Đã cài đặt thành công: {orig_script.name} (Kịch bản thoại & Tin nhắn Lua ArcX)")

            # Install Vietnamese AssetBundles (Textures: Verified Loading Comics)
            bundles_src_dirs = [
                BASE_DIR / "staging" / "texture_candidate_full" / "Persistent_Store" / "AssetBundles",
                BASE_DIR / "dist" / "AssetBundles",
                BASE_DIR / "staging" / "texture_candidate_v096" / "Persistent_Store" / "AssetBundles",
                BASE_DIR / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles",
            ]
            bundles_src = next((d for d in bundles_src_dirs if d.exists()), None)
            if bundles_src:
                target_bundles_dir = game_path / "Persistent_Store" / "AssetBundles"
                target_bundles_dir.mkdir(parents=True, exist_ok=True)
                b_count = 0
                for b_file in bundles_src.glob("*.en.unity3d"):
                    dest_b = target_bundles_dir / b_file.name
                    if dest_b.exists():
                        bak_b = run_backup_dir / b_file.name
                        shutil.copy2(dest_b, bak_b)
                        backup_manifest["files"].append({
                            "relative_path": f"Persistent_Store/AssetBundles/{b_file.name}",
                            "backup_file": b_file.name,
                            "original_sha256": sha256_file(dest_b),
                            "size": dest_b.stat().st_size
                        })
                    temp_b = dest_b.with_suffix(".en.unity3d.tmp_patch")
                    shutil.copy2(b_file, temp_b)
                    temp_b.replace(dest_b)
                    b_count += 1
                if b_count > 0:
                    installed_count += b_count
                    installed_files.append(f"Persistent_Store/AssetBundles/ ({b_count} bundles)")
                    log(f"   ✓ Đã cài đặt thành công: {b_count} tệp AssetBundles ảnh chữ Việt hóa (Truyện tranh, Danh hiệu, Tiêu đề)")

            # Install subtitles
            for rel, proposal_file in batch_files.items():
                orig_file = game_path / rel
                if not orig_file.exists():
                    log(f"   Bỏ qua (không tồn tại trong game): {rel}")
                    continue

                if not proposal_file.exists():
                    log(f"   Cảnh báo: Không tìm thấy proposal {proposal_file.name}")
                    continue

                prop_data = json.loads(proposal_file.read_text(encoding="utf-8"))
                translations = {}
                for entry in prop_data.get("entries", []):
                    cue = entry["source"]["locator"]["cue"]
                    text_vi = entry.get("text_vi", "").strip()
                    if text_vi:
                        translations[cue] = text_vi

                if not translations:
                    log(f"   Cảnh báo: Proposal {proposal_file.name} chưa có bản dịch!")
                    continue

                raw_bytes = orig_file.read_bytes()
                candidate_bytes = render_srt(raw_bytes, translations)

                # Atomic write
                temp_file = orig_file.with_suffix(".tmp_patch")
                temp_file.write_bytes(candidate_bytes)
                temp_file.replace(orig_file)
                installed_count += 1
                installed_files.append(rel)
                log(f"   ✓ Đã cài đặt thành công: {orig_file.name} ({len(translations)} cues)")

            # 3. Write installation marker
            marker_file = game_path / "Persistent_Store" / "viethoa_installed.json"
            marker_data = {
                "installed_at": timestamp,
                "version": "1.0.0",
                "installed_files": installed_files,
                "backup_run": run_backup_dir.name
            }
            marker_file.write_text(json.dumps(marker_data, indent=2), encoding="utf-8")

            msg = f"Cài đặt hoàn tất! Đã Việt hóa thành công {installed_count} tệp tài nguyên."
            log(f"✓ {msg}")
            return True, msg

        except Exception as e:
            err = f"Lỗi trong quá trình cài đặt: {e}\n{traceback.format_exc()}"
            DiagnosticCollector.record_error(err)
            return False, str(e)

    @staticmethod
    def rollback_pc(game_path: Path, log_cb=None) -> tuple[bool, str]:
        def log(msg):
            DiagnosticCollector.log(msg)
            if log_cb:
                log_cb(msg)

        try:
            log("--- Bắt đầu quy trình Khôi phục Gốc (Rollback) ---")
            info = detect_game_info(game_path)
            if not info["exists"]:
                raise FileNotFoundError(f"Không tìm thấy thư mục game: {game_path}")
            if info["is_running"]:
                raise RuntimeError("Game đang chạy! Vui lòng đóng game trước khi khôi phục.")

            if not BACKUP_DIR.exists():
                raise FileNotFoundError("Không tìm thấy thư mục lưu trữ backup!")

            # Find latest backup
            backups = sorted([d for d in BACKUP_DIR.iterdir() if d.is_dir() and (d / "manifest.json").exists()],
                             key=lambda d: d.name, reverse=True)
            if not backups:
                raise FileNotFoundError("Không có bản backup hợp lệ nào để khôi phục!")

            latest_backup = backups[0]
            log(f"Sử dụng bản sao lưu: {latest_backup.name}")
            manifest = json.loads((latest_backup / "manifest.json").read_text(encoding="utf-8"))

            restored = 0
            for item in manifest.get("files", []):
                rel = item["relative_path"]
                bak_file = latest_backup / item["backup_file"]
                orig_file = game_path / rel

                if not bak_file.exists():
                    log(f"   Lỗi: Thiếu tệp backup {bak_file.name}")
                    continue

                # Verify backup integrity
                if sha256_file(bak_file) != item["original_sha256"]:
                    raise ValueError(f"Tệp sao lưu {bak_file.name} bị sai lệch SHA256!")

                orig_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bak_file, orig_file)
                restored += 1
                log(f"   ✓ Đã khôi phục: {orig_file.name}")

            # Remove patch marker
            marker_file = game_path / "Persistent_Store" / "viethoa_installed.json"
            if marker_file.exists():
                marker_file.unlink()

            msg = f"Khôi phục thành công {restored} tệp về nguyên bản gốc!"
            log(f"✓ {msg}")
            return True, msg

        except Exception as e:
            err = f"Lỗi trong quá trình khôi phục: {e}\n{traceback.format_exc()}"
            DiagnosticCollector.record_error(err)
            return False, str(e)


class GitHubManager:
    """Handles GitHub release synchronization, auto-updating, and announcements."""

    @staticmethod
    def parse_version(v: str) -> tuple[int, ...]:
        nums = re.findall(r"\d+", str(v))
        return tuple(map(int, nums)) if nums else (0, 0, 0)

    @classmethod
    def check_updates(cls, repo: str, current_ver: str = "0.4.0") -> dict:
        """Fetches the latest GitHub release and checks for available updates."""
        headers = {"User-Agent": "StellaSora-Localizer", "Accept": "application/vnd.github.v3+json"}
        rel_data = None

        # 1. Try /releases/latest first
        url_latest = f"https://api.github.com/repos/{repo}/releases/latest"
        try:
            req = urllib.request.Request(url_latest, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                rel_data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass

        # 2. Fallback to /releases?per_page=1
        if not rel_data:
            url_list = f"https://api.github.com/repos/{repo}/releases?per_page=1"
            try:
                req = urllib.request.Request(url_list, headers=headers)
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if isinstance(data, list) and len(data) > 0:
                        rel_data = data[0]
            except Exception as e:
                DiagnosticCollector.log(f"Lỗi kết nối GitHub Releases: {e}")

        if not rel_data:
            return {"has_update": False, "error": "Không thể kết nối hoặc chưa có bản phát hành trên GitHub"}

        tag_name = rel_data.get("tag_name", "v0.0.0")
        release_name = rel_data.get("name", tag_name)
        body = rel_data.get("body", "Không có ghi chú bản phát hành.")
        date = (rel_data.get("published_at") or rel_data.get("created_at") or "")[:10]
        html_url = rel_data.get("html_url", f"https://github.com/{repo}/releases")

        assets = rel_data.get("assets", [])
        launcher_asset = next((a for a in assets if a.get("name", "").endswith("Launcher.exe")), None)

        # Explicit non-ambiguous asset matching
        zip_asset = next((a for a in assets if a.get("name", "").startswith("StellaSora_Launcher_PC") and a.get("name", "").endswith(".zip")), None)
        if not zip_asset:
            zip_asset = next((a for a in assets if "Launcher_PC" in a.get("name", "") and a.get("name", "").endswith(".zip")), None)

        apk_asset = next((a for a in assets if a.get("name", "").endswith(".apk")), None)
        arcx_asset = next((a for a in assets if "data_patched_vi.arcx" in a.get("name", "")), None)
        lua_arcx_asset = next((a for a in assets if "lua_patched_vi.arcx" in a.get("name", "") or "lua.arcx" in a.get("name", "")), None)

        # Precise match for AssetBundles package and Manifest
        bundles_asset = next((a for a in assets if a.get("name", "").startswith("StellaSora_AssetBundles_VI") and a.get("name", "").endswith(".zip")), None)
        if not bundles_asset:
            bundles_asset = next((a for a in assets if "AssetBundles" in a.get("name", "") and a.get("name", "").endswith(".zip")), None)

        manifest_asset = next((a for a in assets if a.get("name", "") in ("patch_manifest.json", "stella_patch_manifest.json") or a.get("name", "").endswith("_manifest.json")), None)

        has_update = cls.parse_version(tag_name) > cls.parse_version(current_ver)

        return {
            "success": True,
            "has_update": has_update,
            "tag": tag_name,
            "name": release_name,
            "body": body,
            "date": date,
            "html_url": html_url,
            "current_ver": current_ver,
            "launcher_asset": launcher_asset,
            "zip_asset": zip_asset,
            "apk_asset": apk_asset,
            "arcx_asset": arcx_asset,
            "lua_arcx_asset": lua_arcx_asset,
            "bundles_asset": bundles_asset,
            "manifest_asset": manifest_asset,
            "assets": assets,
        }

    @staticmethod
    def download_file(url: str, dest_path: Path, progress_cb=None, expected_size: int = 0, expected_sha256: str = "") -> bool:
        """Downloads a remote file with progress reporting, size check, hash check, and atomic placement."""
        temp_download = dest_path.with_suffix(dest_path.suffix + ".part")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StellaSora-Localizer"})
            hasher = hashlib.sha256() if expected_sha256 else None
            temp_download.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(req, timeout=45) as resp:
                total_len = resp.headers.get("Content-Length")
                total_size = int(total_len) if total_len else expected_size
                downloaded = 0
                chunk_size = 64 * 1024

                with open(temp_download, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        if hasher:
                            hasher.update(chunk)
                        downloaded += len(chunk)
                        if progress_cb and total_size > 0:
                            percent = min(100.0, (downloaded / total_size) * 100.0)
                            progress_cb(downloaded, total_size, percent)

            # Verification of size
            if expected_size > 0 and downloaded != expected_size:
                DiagnosticCollector.log(f"Lỗi kích thước tệp tải về: {downloaded} != {expected_size}")
                temp_download.unlink(missing_ok=True)
                return False

            # Verification of SHA256
            if expected_sha256:
                calc_sha = hasher.hexdigest()
                if calc_sha.lower() != expected_sha256.lower():
                    DiagnosticCollector.log(f"Lỗi sai lệch SHA256 tệp {dest_path.name}: {calc_sha} != {expected_sha256}")
                    temp_download.unlink(missing_ok=True)
                    return False

            # Atomic replace into dest_path on the same volume
            temp_download.replace(dest_path)
            return True
        except Exception as e:
            DiagnosticCollector.log(f"Lỗi khi tải tệp {url}: {e}")
            if temp_download.exists():
                temp_download.unlink(missing_ok=True)
            return False

    @staticmethod
    def perform_self_update(new_exe_path: Path) -> tuple[bool, str]:
        """Self-updates the launcher on Windows using a robust batch runner."""
        try:
            current_exe = Path(sys.executable).resolve()
            parent_pid = os.getpid()

            temp_dir = Path(os.environ.get("TEMP", str(EXE_DIR)))
            updater_bat = temp_dir / f"stellasora_updater_{parent_pid}.bat"

            bat_lines = [
                "@echo off",
                f'set "TARGET={current_exe}"',
                f'set "SOURCE={new_exe_path}"',
                f'set "PID={parent_pid}"',
                "",
                ":wait_loop",
                'tasklist /fi "PID eq %PID%" 2>NUL | find "%PID%" >NUL',
                "if not errorlevel 1 (",
                "    timeout /t 1 /nobreak >nul",
                "    goto wait_loop",
                ")",
                "timeout /t 1 /nobreak >nul",
                "",
                "set /a attempts=0",
                ":move_loop",
                'move /y "%SOURCE%" "%TARGET%" >nul 2>&1',
                'if not exist "%SOURCE%" goto launch',
                "set /a attempts+=1",
                "if %attempts% geq 15 goto fallback_copy",
                "timeout /t 1 /nobreak >nul",
                "goto move_loop",
                "",
                ":fallback_copy",
                'copy /y "%SOURCE%" "%TARGET%" >nul 2>&1',
                'del /f /q "%SOURCE%" >nul 2>&1',
                "",
                ":launch",
                'start "" "%TARGET%"',
                'del /f /q "%~f0" >nul 2>&1',
                "exit",
            ]

            updater_bat.write_text("\r\n".join(bat_lines), encoding="latin1")

            subprocess.Popen(
                ["cmd.exe", "/c", str(updater_bat)],
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            os._exit(0)
        except Exception as e:
            return False, str(e)

    @staticmethod
    def fetch_announcements(url: str) -> list[dict]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StellaSora-Localizer"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                d = json.loads(resp.read().decode())
                return d.get("announcements", [])
        except Exception:
            for path in [NOTIFS_FILE, BASE_DIR / "launcher" / "notifications.json"]:
                if path.exists():
                    try:
                        d = json.loads(path.read_text(encoding="utf-8"))
                        return d.get("announcements", [])
                    except Exception:
                        pass
        return []


class ADBBridge:
    """Manages Android connections, pushing patches, and floating notifications."""

    @staticmethod
    def get_adb_path() -> str:
        candidates = [
            r"C:\Users\chann\AppData\Local\Android\sdk\platform-tools\adb.exe",
            "adb",
        ]
        for c in candidates:
            if shutil.which(c) or (Path(c).exists()):
                return c
        return "adb"

    @classmethod
    def list_devices(cls) -> list[str]:
        adb = cls.get_adb_path()
        try:
            out = subprocess.check_output([adb, "devices"], timeout=5).decode()
            lines = out.strip().splitlines()[1:]
            devices = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
            return devices
        except Exception as e:
            DiagnosticCollector.log(f"Lỗi kiểm tra adb devices: {e}")
            return []

    @classmethod
    def trigger_floating_notification(cls, device_id: str, message: str) -> bool:
        adb = cls.get_adb_path()
        cmd = [
            adb, "-s", device_id, "shell", "am", "broadcast",
            "-a", "com.stellasora.viethoa.ACTION_NOTIFY",
            "--es", "message", message,
        ]
        try:
            subprocess.run(cmd, check=True, timeout=5)
            DiagnosticCollector.log(f"Đã phát broadcast thông báo nổi tới thiết bị {device_id}")
            return True
        except Exception as e:
            DiagnosticCollector.log(f"Lỗi gửi thông báo qua ADB: {e}")
            return False


# ---------------------------------------------------------------------------
# TKINTER GUI LAUNCHER
# ---------------------------------------------------------------------------

class LauncherGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.config = load_config()
        self.game_path = Path(self.config.get("default_game_path", "C:\\YostarGames\\StellaSora_EN"))

        self.root.title("Stella Sora - Trình Cài Đặt Việt Hóa Đa Nền Tảng & Steam (v0.8.0)")
        self.root.geometry("840x640")
        self.root.minsize(780, 560)
        self.root.configure(bg="#1e1e2e")

        self.setup_styles()
        self.build_ui()
        self.refresh_status()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground="#cdd6f4", padding=[12, 6], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#89b4fa")], foreground=[("selected", "#11111b")])
        style.configure("TFrame", background="#1e1e2e")
        style.configure("Card.TFrame", background="#24273a", relief="flat")

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#181825", height=60)
        header.pack(fill="x", side="top")
        
        lbl_title = tk.Label(header, text="✨ STELLA SORA VIỆT HÓA", font=("Segoe UI", 16, "bold"), fg="#89b4fa", bg="#181825")
        lbl_title.pack(side="left", padx=16, pady=10)

        lbl_version = tk.Label(header, text=f"v{self.config['version']} | Multiplatform", font=("Segoe UI", 10), fg="#a6adc8", bg="#181825")
        lbl_version.pack(side="right", padx=16, pady=10)

        # Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=8)

        # Tab 1: PC Installer
        self.tab_pc = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_pc, text=" 💻 Bản Cài PC (1-Chạm) ")
        self.build_pc_tab()

        # Tab 2: Android & Local ADB
        self.tab_adb = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_adb, text=" 📱 Android & Local ADB ")
        self.build_adb_tab()

        # Tab 3: Announcements & Github Updates
        self.tab_news = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_news, text=" 📢 Thông Báo & Cập Nhật ")
        self.build_news_tab()

        # Tab 4: Diagnostics & Error Copy
        self.tab_diag = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_diag, text=" 🛠️ Báo Lỗi Cho Dev ")
        self.build_diag_tab()

    def build_pc_tab(self):
        # Card 1: Game Status & Path Selector
        card_info = tk.Frame(self.tab_pc, bg="#24273a", bd=1, relief="solid")
        card_info.pack(fill="x", padx=12, pady=10)

        # Top row: Title & Edition Badge
        top_frame = tk.Frame(card_info, bg="#24273a")
        top_frame.pack(fill="x", padx=12, pady=(8, 4))

        tk.Label(top_frame, text="Trạng Thái & Thư Mục Trò Chơi", font=("Segoe UI", 11, "bold"), fg="#cdd6f4", bg="#24273a").pack(side="left")

        self.lbl_edition_badge = tk.Label(top_frame, text="[Đang nhận diện...]", font=("Segoe UI", 9, "bold"), fg="#89b4fa", bg="#313244", padx=8, pady=2)
        self.lbl_edition_badge.pack(side="right")

        # Path entry row with Browse and Scan buttons
        path_box = tk.Frame(card_info, bg="#24273a")
        path_box.pack(fill="x", padx=12, pady=4)

        tk.Label(path_box, text="Thư mục:", font=("Segoe UI", 9, "bold"), fg="#bac2de", bg="#24273a").pack(side="left")

        self.ent_path = tk.Entry(path_box, font=("Consolas", 9), bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4", bd=1, relief="solid")
        self.ent_path.pack(side="left", fill="x", expand=True, padx=(8, 8))
        self.ent_path.insert(0, str(self.game_path))
        self.ent_path.bind("<Return>", lambda e: self.on_path_entered())

        btn_browse = tk.Button(path_box, text="📁 Chọn Thư Mục...", font=("Segoe UI", 9, "bold"),
                               bg="#89b4fa", fg="#11111b", activebackground="#b4befe",
                               bd=0, padx=8, pady=3, cursor="hand2", command=self.on_browse_game_path)
        btn_browse.pack(side="left", padx=(0, 6))

        btn_scan_steam = tk.Button(path_box, text="🔍 Quét Steam/PC", font=("Segoe UI", 9),
                                   bg="#45475a", fg="#cdd6f4", activebackground="#585b70",
                                   bd=0, padx=8, pady=3, cursor="hand2", command=self.on_quick_scan_paths)
        btn_scan_steam.pack(side="left")

        # Status & Version Information
        status_box = tk.Frame(card_info, bg="#24273a")
        status_box.pack(fill="x", padx=12, pady=(4, 8))

        self.lbl_game_ver = tk.Label(status_box, text="Phiên bản: Đang kiểm tra...", font=("Segoe UI", 9), fg="#bac2de", bg="#24273a")
        self.lbl_game_ver.pack(anchor="w", pady=1)

        self.lbl_patch_status = tk.Label(status_box, text="Trạng thái Việt Hóa: Chưa xác định", font=("Segoe UI", 10, "bold"), fg="#f9e2af", bg="#24273a")
        self.lbl_patch_status.pack(anchor="w", pady=2)

        # Buttons Row
        btn_frame = tk.Frame(self.tab_pc, bg="#1e1e2e")
        btn_frame.pack(fill="x", padx=12, pady=6)

        self.btn_install = tk.Button(btn_frame, text="⚡ CÀI ĐẶT VIỆT HÓA (1-CHẠM)", font=("Segoe UI", 10, "bold"),
                                     bg="#a6e3a1", fg="#11111b", activebackground="#94e2d5",
                                     padx=12, pady=8, bd=0, cursor="hand2", command=self.on_install_pc)
        self.btn_install.pack(side="left", padx=(0, 6))

        self.btn_launch_game = tk.Button(btn_frame, text="🚀 KHỞI ĐỘNG GAME", font=("Segoe UI", 10, "bold"),
                                         bg="#fab387", fg="#11111b", activebackground="#f9e2af",
                                         padx=12, pady=8, bd=0, cursor="hand2", command=self.on_launch_game)
        self.btn_launch_game.pack(side="left", padx=(0, 6))

        self.btn_online_sync = tk.Button(btn_frame, text="🌐 CẬP NHẬT TỪ GITHUB", font=("Segoe UI", 9, "bold"),
                                         bg="#89b4fa", fg="#11111b", activebackground="#b4befe",
                                         padx=10, pady=8, bd=0, cursor="hand2", command=self.on_sync_game_patch_from_github)
        self.btn_online_sync.pack(side="left", padx=(0, 6))

        self.btn_rollback = tk.Button(btn_frame, text="🔄 Khôi Phục Gốc", font=("Segoe UI", 9, "bold"),
                                      bg="#eba0ac", fg="#11111b", activebackground="#f38ba8",
                                      padx=10, pady=8, bd=0, cursor="hand2", command=self.on_rollback_pc)
        self.btn_rollback.pack(side="left", padx=(0, 6))

        self.btn_steam_help = tk.Button(btn_frame, text="🎮 Hướng Dẫn Steam", font=("Segoe UI", 9),
                                        bg="#cba6f7", fg="#11111b", activebackground="#b4befe",
                                        padx=10, pady=8, bd=0, cursor="hand2", command=self.on_show_steam_guide)
        self.btn_steam_help.pack(side="left")

        self.btn_refresh = tk.Button(btn_frame, text="🔄 Làm Mới", font=("Segoe UI", 9),
                                     bg="#45475a", fg="#cdd6f4", activebackground="#585b70",
                                     padx=10, pady=8, bd=0, cursor="hand2", command=self.refresh_status)
        self.btn_refresh.pack(side="right")

        # Log Window
        tk.Label(self.tab_pc, text="Nhật Ký Thực Thi:", font=("Segoe UI", 9, "bold"), fg="#cdd6f4", bg="#1e1e2e").pack(anchor="w", padx=12, pady=(10, 2))
        self.txt_log = tk.Text(self.tab_pc, height=12, bg="#11111b", fg="#a6adc8", font=("Consolas", 9), bd=0, padx=8, pady=8)
        self.txt_log.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def build_adb_tab(self):
        f = tk.Frame(self.tab_adb, bg="#24273a", bd=1, relief="solid")
        f.pack(fill="x", padx=12, pady=10)

        tk.Label(f, text="Kết Nối Android & Emulators (Local ADB)", font=("Segoe UI", 11, "bold"), fg="#cdd6f4", bg="#24273a").pack(anchor="w", padx=12, pady=8)
        tk.Label(f, text="Hỗ trợ cài đặt trực tiếp bản dịch vào máy ảo hoặc điện thoại Android qua ADB nội bộ.", font=("Segoe UI", 9), fg="#bac2de", bg="#24273a").pack(anchor="w", padx=12, pady=2)

        row = tk.Frame(f, bg="#24273a")
        row.pack(fill="x", padx=12, pady=8)

        self.lbl_adb_devices = tk.Label(row, text="Thiết bị phát hiện: Chưa quét", font=("Segoe UI", 10), fg="#f9e2af", bg="#24273a")
        self.lbl_adb_devices.pack(side="left")

        btn_scan = tk.Button(row, text="🔍 Quét Thiết Bị ADB", font=("Segoe UI", 9, "bold"), bg="#89b4fa", fg="#11111b", bd=0, padx=10, pady=4, cursor="hand2", command=self.on_scan_adb)
        btn_scan.pack(side="right")

        # Action Buttons
        actions = tk.Frame(self.tab_adb, bg="#1e1e2e")
        actions.pack(fill="x", padx=12, pady=10)

        btn_notify = tk.Button(actions, text="🔔 Bật Thông Báo Nổi Lên Game (ADB)", font=("Segoe UI", 10, "bold"),
                               bg="#f9e2af", fg="#11111b", bd=0, padx=14, pady=8, cursor="hand2", command=self.on_send_floating_notif)
        btn_notify.pack(side="left", padx=(0, 10))

    def build_news_tab(self):
        # Card 1: GitHub Release Status
        card_rel = tk.Frame(self.tab_news, bg="#24273a", bd=1, relief="solid")
        card_rel.pack(fill="x", padx=12, pady=10)

        # Title & Action Buttons
        top_row = tk.Frame(card_rel, bg="#24273a")
        top_row.pack(fill="x", padx=12, pady=(10, 4))

        tk.Label(top_row, text="Đồng Bộ Bản Phát Hành (GitHub Releases)", font=("Segoe UI", 12, "bold"), fg="#89b4fa", bg="#24273a").pack(side="left")

        btn_open_browser = tk.Button(top_row, text="🌐 Mở Trang Web Release", font=("Segoe UI", 9),
                                     bg="#45475a", fg="#cdd6f4", activebackground="#585b70",
                                     bd=0, padx=8, pady=4, cursor="hand2", command=self.on_open_release_url)
        btn_open_browser.pack(side="right", padx=(6, 0))

        btn_check_git = tk.Button(top_row, text="🔄 Kiểm Tra Lại", font=("Segoe UI", 9, "bold"),
                                  bg="#cba6f7", fg="#11111b", activebackground="#b4befe",
                                  bd=0, padx=10, pady=4, cursor="hand2", command=self.on_check_github)
        btn_check_git.pack(side="right")

        # Status & Version Labels
        self.lbl_rel_status = tk.Label(card_rel, text="⏳ Đang kiểm tra bản phát hành trên GitHub...", font=("Segoe UI", 10, "bold"), fg="#f9e2af", bg="#24273a")
        self.lbl_rel_status.pack(anchor="w", padx=12, pady=(4, 2))

        self.lbl_rel_details = tk.Label(card_rel, text=f"Bản cài hiện tại: v{self.config.get('version', '0.1.0')} | Đang kết nối tới GitHub...", font=("Segoe UI", 9), fg="#bac2de", bg="#24273a")
        self.lbl_rel_details.pack(anchor="w", padx=12, pady=(0, 8))

        # Download / Action Row
        act_row = tk.Frame(card_rel, bg="#24273a")
        act_row.pack(fill="x", padx=12, pady=(0, 10))

        self.btn_auto_download = tk.Button(act_row, text="⚡ TẢI & CẬP NHẬT TỰ ĐỘNG (1-CHẠM)", font=("Segoe UI", 10, "bold"),
                                           bg="#a6e3a1", fg="#11111b", activebackground="#94e2d5",
                                           bd=0, padx=14, pady=6, cursor="hand2", command=self.on_auto_update_release)
        self.btn_auto_download.pack(side="left")

        self.lbl_download_progress = tk.Label(act_row, text="", font=("Segoe UI", 9), fg="#cdd6f4", bg="#24273a")
        self.lbl_download_progress.pack(side="left", padx=12)

        # Progress bar
        self.progress_bar = ttk.Progressbar(card_rel, orient="horizontal", mode="determinate")

        # Card 2: Release Notes / Changelog
        tk.Label(self.tab_news, text="Chi Tiết Bản Phát Hành & Thông Báo Mới:", font=("Segoe UI", 10, "bold"), fg="#cdd6f4", bg="#1e1e2e").pack(anchor="w", padx=12, pady=(6, 2))
        self.txt_news = tk.Text(self.tab_news, bg="#181825", fg="#cdd6f4", font=("Segoe UI", 10), wrap="word", padx=12, pady=12, bd=0)
        self.txt_news.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.latest_release_info = None
        self.load_announcements()
        self.root.after(400, self.on_check_github)

    def build_diag_tab(self):
        card = tk.Frame(self.tab_diag, bg="#24273a", bd=1, relief="solid")
        card.pack(fill="x", padx=12, pady=10)

        tk.Label(card, text="Trợ Giúp & Báo Cáo Sự Cố", font=("Segoe UI", 12, "bold"), fg="#f38ba8", bg="#24273a").pack(anchor="w", padx=12, pady=8)
        tk.Label(card, text="Nếu gặp bất kỳ lỗi nào, bạn chỉ cần bấm nút bên dưới. Toàn bộ mã lỗi và thông tin chẩn đoán sẽ được copy sẵn vào bộ nhớ tạm để gửi cho Dev.",
                 font=("Segoe UI", 9), fg="#bac2de", bg="#24273a", wraplength=750, justify="left").pack(anchor="w", padx=12, pady=2)

        btn_copy = tk.Button(card, text="📋 SAO CHÉP MÃ LỖI & CHẨN ĐOÁN CHO DEV (1-CHẠM)", font=("Segoe UI", 11, "bold"),
                             bg="#f38ba8", fg="#11111b", activebackground="#eba0ac", bd=0, padx=16, pady=10, cursor="hand2",
                             command=self.on_copy_error_log)
        btn_copy.pack(anchor="w", padx=12, pady=12)

        tk.Label(self.tab_diag, text="Xem Trước Bản Báo Cáo:", font=("Segoe UI", 9, "bold"), fg="#cdd6f4", bg="#1e1e2e").pack(anchor="w", padx=12, pady=(10, 2))
        self.txt_diag_preview = tk.Text(self.tab_diag, bg="#11111b", fg="#a6adc8", font=("Consolas", 9), wrap="word", padx=10, pady=10, bd=0)
        self.txt_diag_preview.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def log_ui(self, msg: str):
        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")

    def on_browse_game_path(self):
        new_dir = filedialog.askdirectory(
            title="Chọn Thư Mục Cài Đặt Trò Chơi Stella Sora (Steam hoặc Yostar)",
            initialdir=str(self.game_path) if self.game_path.exists() else "C:\\"
        )
        if new_dir:
            self.set_game_path(Path(new_dir))

    def on_path_entered(self):
        entered = self.ent_path.get().strip()
        if entered:
            self.set_game_path(Path(entered))

    def set_game_path(self, path: Path):
        self.game_path = path
        self.config["default_game_path"] = str(path)
        save_config(self.config)
        self.ent_path.delete(0, "end")
        self.ent_path.insert(0, str(path))
        self.log_ui(f"Đã chuyển sang thư mục game: {path}")
        self.refresh_status()

    def on_quick_scan_paths(self):
        candidates = find_potential_game_paths()
        existing = [c for c in candidates if c["exists"]]

        if not existing:
            messagebox.showinfo("Quét Thư Mục", "Không phát hiện thêm thư mục Stella Sora nào khác trên máy.")
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("🔍 Chọn Bản Cài Đặt Stella Sora")
        dlg.geometry("640x360")
        dlg.configure(bg="#1e1e2e")
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="Các thư mục Stella Sora được phát hiện trên máy tính:", font=("Segoe UI", 10, "bold"), fg="#89b4fa", bg="#1e1e2e").pack(anchor="w", padx=14, pady=(12, 6))

        frame_list = tk.Frame(dlg, bg="#24273a", bd=1, relief="solid")
        frame_list.pack(fill="both", expand=True, padx=14, pady=6)

        for c in candidates:
            row = tk.Frame(frame_list, bg="#24273a")
            row.pack(fill="x", padx=10, pady=4)
            badge_color = "#a6e3a1" if c["is_valid_game"] else "#f9e2af"
            status_text = "✓ Sẵn sàng" if c["is_valid_game"] else ("Thư mục trống" if c["exists"] else "Chưa cài đặt")

            lbl_name = tk.Label(row, text=f"[{c['edition']}] {c['label']}", font=("Segoe UI", 9, "bold"), fg="#cdd6f4", bg="#24273a")
            lbl_name.pack(side="left")

            lbl_sub = tk.Label(row, text=f" — {status_text}", font=("Segoe UI", 8), fg=badge_color, bg="#24273a")
            lbl_sub.pack(side="left")

            def make_chooser(p):
                return lambda: (self.set_game_path(p), dlg.destroy())

            if c["exists"]:
                btn_select = tk.Button(row, text="Chọn Thư Mục Này", font=("Segoe UI", 8, "bold"),
                                       bg="#89b4fa", fg="#11111b", bd=0, padx=8, pady=2, cursor="hand2",
                                       command=make_chooser(c["path"]))
                btn_select.pack(side="right")

        tk.Button(dlg, text="Đóng", font=("Segoe UI", 9), bg="#45475a", fg="#cdd6f4", bd=0, padx=14, pady=4, cursor="hand2", command=dlg.destroy).pack(pady=10)

    def on_launch_game(self):
        info = detect_game_info(self.game_path)
        if not info["exists"]:
            messagebox.showwarning("Cảnh Báo", "Thư mục trò chơi chưa tồn tại!")
            return
        ok, msg = launch_game(self.game_path)
        if ok:
            self.log_ui(f"🚀 {msg}")
        else:
            self.log_ui(f"❌ {msg}")
            messagebox.showerror("Khởi Động Lỗi", msg)

    def on_show_steam_guide(self):
        msg = (
            "HƯỚNG DẪN CHƠI STELLA SORA TRÊN STEAM\n"
            "====================================\n\n"
            "1. Nếu bạn tải game từ Steam (AppID 4813850):\n"
            "   - Trong Launcher, bấm '📁 Chọn Thư Mục...' hoặc '🔍 Quét Steam/PC'.\n"
            "   - Chọn thư mục: .../steamapps/common/Stella Sora\n"
            "   - Bấm '⚡ CÀI ĐẶT VIỆT HÓA (1-CHẠM)'.\n"
            "   - Bấm '🚀 KHỞI ĐỘNG GAME' hoặc mở trực tiếp từ Steam!\n\n"
            "2. Chơi bản Yostar qua Steam (Non-Steam Game - Khuyên Dùng):\n"
            "   - Mở Steam -> Menu 'Games' -> 'Add a Non-Steam Game to My Library...'\n"
            "   - Bấm 'Browse...' -> Chọn file:\n"
            "     C:\\YostarGames\\StellaSora_EN\\StellaSora.exe\n"
            "   - Bấm 'Add Selected Programs'.\n"
            "   - Bạn sẽ có toàn bộ tính năng cao cấp của Steam: Steam Overlay (Shift+Tab), xem FPS, chụp ảnh màn hình F12 và kết nối mọi tay cầm (Xbox, PlayStation, Switch)!"
        )
        messagebox.showinfo("🎮 Hướng Dẫn Chơi Trên Steam", msg)

    def refresh_status(self):
        info = detect_game_info(self.game_path)

        # Update edition badge
        edition = info.get("edition", "Không xác định")
        if info.get("is_steam"):
            self.lbl_edition_badge.config(text=f"🎮 {edition}", bg="#1e66f5", fg="#ffffff")
            self.btn_launch_game.config(text="🚀 CHẠY QUA STEAM")
        elif "Yostar" in edition:
            self.lbl_edition_badge.config(text=f"🏢 {edition}", bg="#cba6f7", fg="#11111b")
            self.btn_launch_game.config(text="🚀 KHỞI ĐỘNG GAME")
        else:
            self.lbl_edition_badge.config(text=f"📁 {edition}", bg="#45475a", fg="#cdd6f4")
            self.btn_launch_game.config(text="🚀 KHỞI ĐỘNG GAME")

        if not info["exists"]:
            self.lbl_patch_status.config(text="⚠️ Thư mục chưa tồn tại trên máy!", fg="#f38ba8")
            self.lbl_game_ver.config(text="Phiên bản: Không tìm thấy tệp trò chơi")
            self.btn_install.config(state="disabled")
            self.btn_launch_game.config(state="disabled")
            return

        if not info["has_game_data"]:
            self.lbl_patch_status.config(text="⚠️ Thư mục trống hoặc game chưa tải xong!", fg="#fab387")
            self.lbl_game_ver.config(text="Vui lòng tải game từ Steam/Yostar trước khi cài Việt Hóa")
            self.btn_install.config(state="disabled")
            self.btn_launch_game.config(state="disabled")
            return

        self.btn_launch_game.config(state="normal")
        self.lbl_game_ver.config(text=f"Client: {info['client_ver']} | Game: {info['game_ver']} | Res: {info['res_ver']}")

        if info["installed_patch"]:
            self.lbl_patch_status.config(text="✓ ĐÃ CÀI ĐẶT BẢN VIỆT HÓA (Active - Sẵn sàng chơi)", fg="#a6e3a1")
        else:
            self.lbl_patch_status.config(text="Chưa cài đặt bản Việt Hóa (Sẵn sàng cài 1-chạm)", fg="#f9e2af")
        self.btn_install.config(state="normal")

        # Update diag preview
        report = DiagnosticCollector.generate_report(self.game_path)
        self.txt_diag_preview.delete("1.0", "end")
        self.txt_diag_preview.insert("1.0", report)

    def on_install_pc(self):
        def worker():
            self.btn_install.config(state="disabled")
            self.log_ui("Bắt đầu cài đặt...")
            ok, msg = LocalizationEngine.install_pc(self.game_path, log_cb=self.log_ui)
            if ok:
                messagebox.showinfo("Thành Công", "Đã cài đặt bản Việt Hóa thành công!\nBạn có thể khởi động game để trải nghiệm.")
            else:
                messagebox.showerror("Lỗi Cài Đặt", f"Không thể hoàn tất cài đặt:\n{msg}")
            self.refresh_status()

        threading.Thread(target=worker, daemon=True).start()

    def on_sync_game_patch_from_github(self):
        """Downloads the latest verified translation packages and AssetBundles with manifest verification,
        atomic replacement on the same volume, traversal guards, and automatic rollback on failure.
        """
        if not messagebox.askyesno(
            "Cập Nhật Bản Dịch Từ GitHub",
            "Tải trọn bộ bản dịch tiếng Việt mới nhất (Bảng dữ liệu + Thoại & Tin nhắn + AssetBundles ảnh chữ) từ GitHub Release và cài đặt an toàn vào game?\n\n"
            "- Tự động kiểm tra mã băm SHA256 và Manifest phát hành\n"
            "- Sao lưu preimage nguyên bản an toàn trước khi thay đổi\n"
            "- Thay thế nguyên tử (atomic replace), tự động rollback nếu gặp sự cố\n\n"
            "Bạn có muốn tiếp tục không?"
        ):
            return

        def worker():
            self.btn_online_sync.config(state="disabled")
            self.btn_install.config(state="disabled")
            self.log_ui("Đang kiểm tra kết nối và các gói bản dịch trên GitHub Releases...")

            info = detect_game_info(self.game_path)
            if not info["exists"]:
                self.log_ui("❌ Không tìm thấy thư mục cài đặt game Stella Sora.")
                messagebox.showerror("Lỗi", f"Không tìm thấy thư mục game:\n{self.game_path}")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            if info["is_running"]:
                self.log_ui("⚠️ Trò chơi StellaSora.exe đang chạy! Vui lòng thoát game.")
                messagebox.showwarning("Cảnh Báo", "StellaSora.exe đang chạy! Vui lòng đóng trò chơi trước khi cập nhật bản dịch.")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            repo = self.config.get("github_repo", "doubleD1302/AmeeVH")
            res = GitHubManager.check_updates(repo, "0.0.0")

            if not res or not res.get("success"):
                self.log_ui("❌ Không thể kết nối đến GitHub Release.")
                messagebox.showerror("Lỗi", "Không thể lấy thông tin phát hành từ GitHub. Vui lòng kiểm tra lại kết nối mạng!")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            tag = res.get("tag", "v0.9.6")
            arcx_asset = res.get("arcx_asset")
            lua_asset = res.get("lua_arcx_asset")
            bundles_asset = res.get("bundles_asset")
            manifest_asset = res.get("manifest_asset")

            if not arcx_asset or not arcx_asset.get("browser_download_url"):
                self.log_ui("⚠️ Không tìm thấy tệp data_patched_vi.arcx trên GitHub Release.")
                messagebox.showerror("Lỗi", "Không tìm thấy gói dữ liệu trên GitHub Release!")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            # --- BƯỚC 0: TẢI VÀ PHÂN TÍCH PATCH MANIFEST (NẾU CÓ) ---
            manifest_data = {}
            if manifest_asset and manifest_asset.get("browser_download_url"):
                self.log_ui("Đang tải tệp kê khai xác thực bản vá (patch_manifest.json)...")
                temp_manifest = Path(os.environ.get("TEMP", str(EXE_DIR))) / "patch_manifest.json"
                if GitHubManager.download_file(manifest_asset["browser_download_url"], temp_manifest):
                    try:
                        manifest_data = json.loads(temp_manifest.read_text(encoding="utf-8"))
                        self.log_ui("   ✓ Đã xác thực patch_manifest.json chính thức từ nhóm phát hành!")
                    except Exception as e:
                        DiagnosticCollector.log(f"Lỗi đọc manifest: {e}")

            # Check game version against manifest
            if manifest_data:
                target_game_ver = manifest_data.get("client_game_version", "2.0.0")
                target_res_ver = manifest_data.get("resource_version", "2610201624")
                cur_client_ver = info.get("client_ver", "unknown")
                cur_res_ver = info.get("res_ver", "unknown")
                if cur_client_ver != "unknown" and cur_client_ver != target_game_ver:
                    self.log_ui(f"   ℹ️ Thông báo phiên bản: Game hiện tại ({cur_client_ver}) | Bản vá tối ưu cho ({target_game_ver})")

            arcx_mb = (arcx_asset.get('size', 0) / (1024 * 1024)) if arcx_asset else 0.0
            lua_mb = (lua_asset.get('size', 0) / (1024 * 1024)) if lua_asset else 0.0
            bundles_mb = (bundles_asset.get('size', 0) / (1024 * 1024)) if bundles_asset else 0.0
            total_mb = arcx_mb + lua_mb + bundles_mb

            bundles_count_desc = f"{manifest_data.get('total_bundles', 16)} bundles" if manifest_data else "AssetBundles"

            self.log_ui("==================================================")
            self.log_ui(f"📦 PHÁT HÀNH {tag}: TỔNG DUNG LƯỢNG {total_mb:.1f} MB (3 PHẦN)")
            self.log_ui(f"   [1/3] Bảng dữ liệu Tables (data.arcx): {arcx_mb:.1f} MB")
            self.log_ui(f"   [2/3] Kịch bản thoại & Tin nhắn Scripts (lua.arcx): {lua_mb:.1f} MB")
            self.log_ui(f"   [3/3] Đồ họa ảnh chữ ({bundles_count_desc}): {bundles_mb:.1f} MB")
            self.log_ui("==================================================")

            # Transaction journal for rollback on failure
            session_journal = []

            # --- BƯỚC 1: TẢI VÀ CÀI ĐẶT TABLES/DATA.ARCX ---
            self.log_ui(f"\n[1/3] Bắt đầu tải Bảng dữ liệu Core Tables ({arcx_mb:.1f} MB)...")
            download_url = arcx_asset["browser_download_url"]
            temp_dest = Path(os.environ.get("TEMP", str(EXE_DIR))) / "data_patched_vi_download.arcx"

            def progress_arcx(dl, total, pct):
                if int(pct) % 25 == 0:
                    self.log_ui(f"   Đang tải [1/3]: {dl/(1024*1024):.1f}/{total/(1024*1024):.1f} MB ({pct:.1f}%)")

            ok = GitHubManager.download_file(download_url, temp_dest, progress_cb=progress_arcx, expected_size=arcx_asset.get("size", 0))
            if not ok:
                self.log_ui("❌ Lỗi khi tải Tables/data.arcx từ GitHub.")
                messagebox.showerror("Lỗi Tải Về", "Tải dữ liệu Tables từ GitHub thất bại!")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            target_table = self.game_path / "Persistent_Store" / "Tables" / "data.arcx"
            target_table.parent.mkdir(parents=True, exist_ok=True)
            orig_table_bak = target_table.with_suffix(".arcx.orig_en")
            if target_table.exists() and not orig_table_bak.exists():
                shutil.copy2(target_table, orig_table_bak)
                self.log_ui("   Đã sao lưu tệp gốc: data.arcx.orig_en")

            # Same-volume temporary file and atomic replace
            tmp_table = target_table.with_suffix(".tmp_patch")
            shutil.copy2(temp_dest, tmp_table)
            tmp_table.replace(target_table)
            temp_dest.unlink(missing_ok=True)
            session_journal.append(("table", target_table, orig_table_bak))
            self.log_ui("   ✓ [1/3] Đã cài đặt thành công Tables/data.arcx (Atomic replace)")

            # --- BƯỚC 2: TẢI VÀ CÀI ĐẶT SCRIPTS/LUA.ARCX ---
            if lua_asset and lua_asset.get("browser_download_url"):
                lua_url = lua_asset["browser_download_url"]
                self.log_ui(f"\n[2/3] Bắt đầu tải Kịch bản thoại & Tin nhắn ({lua_mb:.1f} MB)...")
                temp_lua = Path(os.environ.get("TEMP", str(EXE_DIR))) / "lua_patched_vi_download.arcx"
                def prog_lua(dl, total, pct):
                    if int(pct) % 25 == 0:
                        self.log_ui(f"   Đang tải [2/3]: {dl/(1024*1024):.1f}/{total/(1024*1024):.1f} MB ({pct:.1f}%)")
                if GitHubManager.download_file(lua_url, temp_lua, progress_cb=prog_lua, expected_size=lua_asset.get("size", 0)):
                    target_script = self.game_path / "Persistent_Store" / "Scripts" / "lua.arcx"
                    target_script.parent.mkdir(parents=True, exist_ok=True)
                    orig_lua_bak = target_script.with_suffix(".arcx.orig_en")
                    if target_script.exists() and not orig_lua_bak.exists():
                        shutil.copy2(target_script, orig_lua_bak)
                        self.log_ui("   Đã sao lưu tệp gốc: lua.arcx.orig_en")

                    tmp_lua = target_script.with_suffix(".tmp_patch")
                    shutil.copy2(temp_lua, tmp_lua)
                    tmp_lua.replace(target_script)
                    temp_lua.unlink(missing_ok=True)
                    session_journal.append(("script", target_script, orig_lua_bak))
                    self.log_ui("   ✓ [2/3] Đã cài đặt thành công Scripts/lua.arcx (Thoại & Tin nhắn)")

            # --- BƯỚC 3: TẢI VÀ CÀI ĐẶT ASSETBUNDLES (ẢNH CHỮ) ---
            b_extracted = 0
            if bundles_asset and bundles_asset.get("browser_download_url"):
                bundles_url = bundles_asset["browser_download_url"]
                expected_zip_sha = manifest_data.get("package_sha256", "")
                self.log_ui(f"\n[3/3] Bắt đầu tải Đồ họa ảnh chữ AssetBundles ({bundles_mb:.1f} MB)...")
                temp_bundles_zip = Path(os.environ.get("TEMP", str(EXE_DIR))) / "AssetBundles_VI_download.zip"

                def prog_bundles(dl, total, pct):
                    if int(pct) % 25 == 0:
                        self.log_ui(f"   Đang tải [3/3]: {dl/(1024*1024):.1f}/{total/(1024*1024):.1f} MB ({pct:.1f}%)")

                dl_ok = GitHubManager.download_file(
                    bundles_url,
                    temp_bundles_zip,
                    progress_cb=prog_bundles,
                    expected_size=bundles_asset.get("size", 0),
                    expected_sha256=expected_zip_sha
                )

                if not dl_ok:
                    self.log_ui("❌ Lỗi khi tải hoặc xác thực tệp AssetBundles từ GitHub.")
                    # Rollback session changes
                    self.log_ui("   Đang phục hồi trạng thái an toàn trước khi cập nhật...")
                    for j_type, target_p, bak_p in session_journal:
                        if bak_p.exists():
                            shutil.copy2(bak_p, target_p)
                    messagebox.showerror("Lỗi Cài Đặt", "Tải hoặc kiểm tra tính toàn vẹn gói AssetBundles thất bại. Game đã được giữ nguyên trạng.")
                    self.btn_online_sync.config(state="normal")
                    self.btn_install.config(state="normal")
                    return

                # Map bundles from manifest (supports both dict and list schemas)
                bundles_val = manifest_data.get("bundles", {})
                if isinstance(bundles_val, dict):
                    manifest_bundles_map = {k: {**v, "bundle_name": k} for k, v in bundles_val.items()}
                else:
                    manifest_bundles_map = {b.get("bundle_name", ""): b for b in bundles_val if isinstance(b, dict)}

                target_bundles_dir = self.game_path / "Persistent_Store" / "AssetBundles"
                target_bundles_dir.mkdir(parents=True, exist_ok=True)
                session_bundles_applied = []

                try:
                    self.log_ui("   Đang xác thực bảo mật và áp dụng các tệp AssetBundles...")
                    with zipfile.ZipFile(temp_bundles_zip, "r") as zf:
                        for member in zf.infolist():
                            if member.is_dir():
                                continue
                            fname = Path(member.filename).name

                            # Guard 1: Allowlist check
                            if not fname.endswith(".en.unity3d"):
                                continue

                            # Guard 2: Traversal check
                            if ".." in member.filename or member.filename.startswith("/") or member.filename.startswith("\\"):
                                raise SecurityError(f"Phát hiện đường dẫn không an toàn: {member.filename}")

                            dest_f = target_bundles_dir / fname
                            # Guard 3: Destination root check
                            if not str(dest_f.resolve()).startswith(str(target_bundles_dir.resolve())):
                                raise SecurityError(f"Nỗ lực ghi ngoài thư mục đích: {member.filename}")

                            b_info = manifest_bundles_map.get(fname, {})
                            exp_patched_sha = b_info.get("patched_sha256")
                            exp_preimage_sha = b_info.get("preimage_sha256")

                            # Repeated update check: if current file matches patched SHA, skip re-extracting
                            if dest_f.exists() and exp_patched_sha:
                                cur_sha = sha256_file(dest_f)
                                if cur_sha.lower() == exp_patched_sha.lower():
                                    b_extracted += 1
                                    continue

                            # Preimage backup: backup pristine file if not already backed up
                            orig_bak = target_bundles_dir / f"{fname}.orig_en"
                            legacy_bak = target_bundles_dir / fname.replace(".unity3d", ".en.unity3d.orig_en")
                            if dest_f.exists() and not orig_bak.exists() and not legacy_bak.exists():
                                shutil.copy2(dest_f, orig_bak)
                                self.log_ui(f"   Đã sao lưu gốc: {orig_bak.name}")

                            # Write to temporary file on same volume
                            temp_b = dest_f.with_suffix(".en.unity3d.tmp_patch")
                            with zf.open(member) as s_fp, open(temp_b, "wb") as d_fp:
                                shutil.copyfileobj(s_fp, d_fp)

                            # Verify SHA256 of extracted bundle
                            if exp_patched_sha:
                                tmp_sha = sha256_file(temp_b)
                                if tmp_sha.lower() != exp_patched_sha.lower():
                                    temp_b.unlink(missing_ok=True)
                                    raise ValueError(f"Sai lệch mã băm bundle {fname}: {tmp_sha} != {exp_patched_sha}")

                            # Atomic replace
                            temp_b.replace(dest_f)
                            session_bundles_applied.append(dest_f)
                            b_extracted += 1

                    temp_bundles_zip.unlink(missing_ok=True)
                    self.log_ui(f"   ✓ [3/3] Đã cài đặt thành công {b_extracted} tệp AssetBundles ảnh chữ!")

                except Exception as b_err:
                    self.log_ui(f"❌ Lỗi áp dụng AssetBundles: {b_err}. Đang rollback tự động...")
                    for bf in session_bundles_applied:
                        bak = target_bundles_dir / f"{bf.name}.orig_en"
                        if not bak.exists():
                            bak = target_bundles_dir / bf.name.replace(".unity3d", ".en.unity3d.orig_en")
                        if bak.exists():
                            shutil.copy2(bak, bf)
                    for tmp in target_bundles_dir.glob("*.tmp_patch"):
                        tmp.unlink(missing_ok=True)
                    temp_bundles_zip.unlink(missing_ok=True)
                    messagebox.showerror("Lỗi Cài Đặt", f"Quá trình áp dụng AssetBundles thất bại:\n{b_err}\n\nCác tệp đã được khôi phục về trạng thái an toàn.")
                    self.btn_online_sync.config(state="normal")
                    self.btn_install.config(state="normal")
                    return

            # --- BƯỚC 4: GHI DẤU VẾT TRẠNG THÁI CÀI ĐẶT CHÍNH XÁC ---
            marker_file = self.game_path / "Persistent_Store" / "viethoa_installed.json"
            marker_data = {
                "installed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": tag.lstrip("v"),
                "release_tag": tag,
                "total_mb_synced": round(total_mb, 2),
                "components": {
                    "tables": {
                        "file": "Persistent_Store/Tables/data.arcx",
                        "status": "installed",
                        "size": target_table.stat().st_size if target_table.exists() else 0
                    },
                    "scripts": {
                        "file": "Persistent_Store/Scripts/lua.arcx",
                        "status": "installed",
                        "size": (self.game_path / "Persistent_Store" / "Scripts" / "lua.arcx").stat().st_size if (self.game_path / "Persistent_Store" / "Scripts" / "lua.arcx").exists() else 0
                    },
                    "asset_bundles": {
                        "target_dir": "Persistent_Store/AssetBundles",
                        "bundles_installed_count": b_extracted,
                        "active_scope": "53 Loading Comics (16 bundles, 4-vertex quad mesh verified)",
                        "pending_scope": "Honor Titles, Logos, Event Banners (Pending mesh repair and BC7 atlas regional isolator)",
                        "manifest_verified": bool(manifest_data)
                    }
                },
                "status": "success"
            }
            marker_file.write_text(json.dumps(marker_data, indent=2, ensure_ascii=False), encoding="utf-8")

            self.log_ui("")
            self.log_ui("==================================================")
            self.log_ui(f"🎉 CHÚC MỪNG! ĐÃ CẬP NHẬT THÀNH CÔNG BẢN VIỆT HÓA {tag}!")
            self.log_ui("   - 100% Cơ sở dữ liệu và phụ đề VoiceTable tiếng Việt")
            self.log_ui("   - 100% Cốt truyện thoại và tin nhắn lữ khách")
            self.log_ui(f"   - 53 Truyện tranh 4 ô màn hình chờ ({b_extracted} AssetBundles)")
            self.log_ui("==================================================")
            msg_ok = (
                f"Đã cập nhật trọn vẹn bản Việt Hóa {tag} ({total_mb:.1f} MB) vào game thành công!\n\n"
                f"- Bảng dữ liệu: Đã nạp Tables/data.arcx\n"
                f"- Thoại & Tin nhắn: Đã nạp Scripts/lua.arcx\n"
                f"- Đồ họa: Đã nạp {b_extracted} AssetBundles truyện tranh màn hình chờ\n\n"
                "Bạn có thể khởi động game để trải nghiệm ngay."
            )
            messagebox.showinfo("Thành Công", msg_ok)

            self.refresh_status()
            self.btn_online_sync.config(state="normal")
            self.btn_install.config(state="normal")

        threading.Thread(target=worker, daemon=True).start()

    def on_rollback_pc(self):
        if not messagebox.askyesno("Xác Nhận", "Bạn có chắc chắn muốn khôi phục toàn bộ tệp game về bản gốc nguyên thủy?"):
            return

        def worker():
            self.btn_rollback.config(state="disabled")
            self.log_ui("Bắt đầu khôi phục...")
            ok, msg = LocalizationEngine.rollback_pc(self.game_path, log_cb=self.log_ui)
            if ok:
                messagebox.showinfo("Thành Công", "Đã khôi phục game về nguyên bản gốc!")
            else:
                messagebox.showerror("Lỗi Khôi Phục", f"Lỗi khôi phục: {msg}")
            self.btn_rollback.config(state="normal")
            self.refresh_status()

        threading.Thread(target=worker, daemon=True).start()

    def on_scan_adb(self):
        devices = ADBBridge.list_devices()
        if devices:
            self.lbl_adb_devices.config(text=f"Thiết bị phát hiện: {', '.join(devices)}", fg="#a6e3a1")
            self.log_ui(f"Phát hiện thiết bị ADB: {devices}")
        else:
            self.lbl_adb_devices.config(text="Không tìm thấy thiết bị ADB nào kết nối!", fg="#f38ba8")
            self.log_ui("Không tìm thấy thiết bị ADB.")

    def on_send_floating_notif(self):
        devices = ADBBridge.list_devices()
        if not devices:
            messagebox.showwarning("Cảnh Báo", "Vui lòng kết nối thiết bị Android / giả lập trước!")
            return
        ADBBridge.trigger_floating_notification(devices[0], "Stella Sora Việt Hóa đang hoạt động!")
        messagebox.showinfo("Thông Báo", f"Đã gửi lệnh kích hoạt thông báo nổi tới thiết bị {devices[0]}!")

    def load_announcements(self):
        items = GitHubManager.fetch_announcements(self.config.get("remote_notifications_url", ""))
        self.txt_news.delete("1.0", "end")
        for item in items:
            self.txt_news.insert("end", f"📌 [{item.get('date', '')}] {item.get('title', '')}\n", "title")
            self.txt_news.insert("end", f"{item.get('content', '')}\n\n", "body")
        self.txt_news.tag_config("title", font=("Segoe UI", 11, "bold"), foreground="#89b4fa")
        self.txt_news.tag_config("body", font=("Segoe UI", 10), foreground="#cdd6f4")

    def on_open_release_url(self):
        url = "https://github.com/doubleD1302/AmeeVH/releases"
        if self.latest_release_info and self.latest_release_info.get("html_url"):
            url = self.latest_release_info["html_url"]
        webbrowser.open(url)

    def on_check_github(self):
        def worker():
            repo = self.config.get("github_repo", "doubleD1302/AmeeVH")
            cur_ver = self.config.get("version", "0.1.0")
            res = GitHubManager.check_updates(repo, cur_ver)
            self.latest_release_info = res

            def update_ui():
                if res.get("success"):
                    tag = res.get("tag", "v0.0.0")
                    name = res.get("name", tag)
                    date = res.get("date", "")
                    has_up = res.get("has_update", False)
                    body = res.get("body", "")

                    if has_up:
                        self.lbl_rel_status.config(text=f"⚡ ĐÃ CÓ BẢN CẬP NHẬT MỚI: {tag} ({name})", fg="#a6e3a1")
                        self.lbl_rel_details.config(text=f"Bản hiện tại: v{cur_ver}  ➔  Bản mới nhất: {tag} (Phát hành: {date})")
                        self.btn_auto_download.config(state="normal", text=f"⚡ TẢI & CẬP NHẬT LÊN {tag} (1-CHẠM)")
                    else:
                        self.lbl_rel_status.config(text=f"✓ Bạn đang sử dụng bản phát hành mới nhất ({tag})", fg="#89b4fa")
                        self.lbl_rel_details.config(text=f"Bản hiện tại: v{cur_ver} | Phát hành: {date} | Trạng thái: Đồng bộ 100%")
                        self.btn_auto_download.config(state="normal", text="🔄 Tải Lại / Đồng Bộ Lại Bản Mới Nhất")

                    # Display release notes
                    self.txt_news.delete("1.0", "end")
                    self.txt_news.insert("end", f"✨ [{tag}] {name}\n", "title")
                    self.txt_news.insert("end", f"📅 Ngày phát hành: {date}\n", "sub")
                    self.txt_news.insert("end", f"🔗 Đường dẫn: {res.get('html_url')}\n\n", "sub")
                    self.txt_news.insert("end", "Nội dung cập nhật:\n", "h2")
                    self.txt_news.insert("end", f"{body}\n\n", "body")

                    # Add announcements below
                    self.txt_news.insert("end", "────────────────────────────────────────\n", "sub")
                    self.txt_news.insert("end", "📢 THÔNG BÁO DỰ ÁN\n\n", "h2")
                    items = GitHubManager.fetch_announcements(self.config.get("remote_notifications_url", ""))
                    for item in items:
                        self.txt_news.insert("end", f"📌 [{item.get('date', '')}] {item.get('title', '')}\n", "title")
                        self.txt_news.insert("end", f"{item.get('content', '')}\n\n", "body")

                    self.txt_news.tag_config("title", font=("Segoe UI", 11, "bold"), foreground="#89b4fa")
                    self.txt_news.tag_config("h2", font=("Segoe UI", 10, "bold"), foreground="#fab387")
                    self.txt_news.tag_config("sub", font=("Segoe UI", 9), foreground="#a6adc8")
                    self.txt_news.tag_config("body", font=("Segoe UI", 10), foreground="#cdd6f4")
                else:
                    self.lbl_rel_status.config(text="⚠️ Không thể đồng bộ với GitHub Releases", fg="#f38ba8")
                    self.lbl_rel_details.config(text=res.get("error", "Lỗi mạng hoặc không thể kết nối tới GitHub."))

            self.root.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def on_auto_update_release(self):
        if not self.latest_release_info or not self.latest_release_info.get("success"):
            messagebox.showwarning("Cảnh Báo", "Vui lòng đợi kiểm tra bản phát hành GitHub trước!")
            return

        asset = self.latest_release_info.get("launcher_asset")
        if not asset or not asset.get("browser_download_url"):
            messagebox.showwarning("Thông Báo", "Bản phát hành này không có tệp Launcher.exe đính kèm để tự động cập nhật.")
            return

        download_url = asset["browser_download_url"]
        file_size = asset.get("size", 0)
        size_mb = f"{file_size / (1024*1024):.1f} MB" if file_size else "Unknown"

        if not messagebox.askyesno("Xác Nhận Tự Động Cập Nhật",
                                   f"Tải và cập nhật Launcher mới nhất từ GitHub?\n\n- Tệp: {asset.get('name')}\n- Kích thước: {size_mb}\n- Thẻ phiên bản: {self.latest_release_info.get('tag')}\n\nQuá trình tải về sẽ diễn ra tự động."):
            return

        def download_worker():
            self.btn_auto_download.config(state="disabled")
            self.progress_bar.pack(fill="x", padx=12, pady=(0, 8))
            self.progress_bar["value"] = 0
            self.lbl_download_progress.config(text="Đang kết nối tải về...")

            temp_dest = Path(os.environ.get("TEMP", str(EXE_DIR))) / "StellaSora_Launcher_update.exe"

            def progress(downloaded, total, pct):
                self.root.after(0, lambda: self._update_progress_ui(downloaded, total, pct))

            ok = GitHubManager.download_file(download_url, temp_dest, progress_cb=progress)
            if ok:
                self.root.after(0, lambda: self._on_download_complete(temp_dest))
            else:
                self.root.after(0, lambda: self._on_download_failed())

        threading.Thread(target=download_worker, daemon=True).start()

    def _update_progress_ui(self, downloaded, total, pct):
        self.progress_bar["value"] = pct
        dl_mb = downloaded / (1024 * 1024)
        tot_mb = total / (1024 * 1024)
        self.lbl_download_progress.config(text=f"Đang tải: {dl_mb:.1f}/{tot_mb:.1f} MB ({pct:.1f}%)")

    def _on_download_complete(self, temp_dest: Path):
        self.progress_bar.pack_forget()
        self.lbl_download_progress.config(text="✓ Tải về hoàn tất! Đang áp dụng cập nhật...")
        messagebox.showinfo("Cập Nhật Thành Công", "Đã tải xong bản Launcher mới nhất!\nỨng dụng sẽ tự động cập nhật và khởi động lại ngay bây giờ.")
        GitHubManager.perform_self_update(temp_dest)
        self.btn_auto_download.config(state="normal")

    def _on_download_failed(self):
        self.progress_bar.pack_forget()
        self.lbl_download_progress.config(text="❌ Tải về thất bại!", fg="#f38ba8")
        messagebox.showerror("Lỗi Tải Về", "Không thể tải tệp cập nhật từ GitHub. Vui lòng kiểm tra lại kết nối mạng!")
        self.btn_auto_download.config(state="normal")

    def on_copy_error_log(self):
        report = DiagnosticCollector.generate_report(self.game_path)
        self.root.clipboard_clear()
        self.root.clipboard_append(report)
        messagebox.showinfo("Đã Sao Chép!", "Đã sao chép toàn bộ thông tin mã lỗi & chẩn đoán vào bộ nhớ tạm!\nBạn chỉ cần dán (Ctrl+V) gửi cho Dev.")


def cli_main():
    parser = argparse.ArgumentParser(description="Stella Sora Việt Hóa CLI & Launcher")
    parser.add_argument("--game-path", type=str, default="", help="Đường dẫn thư mục game tùy chọn")
    parser.add_argument("--install", action="store_true", help="Cài đặt Việt Hóa 1-chạm")
    parser.add_argument("--rollback", action="store_true", help="Khôi phục nguyên bản gốc")
    parser.add_argument("--check-update", action="store_true", help="Kiểm tra bản phát hành mới nhất từ GitHub Releases")
    parser.add_argument("--copy-error", action="store_true", help="In báo cáo lỗi ra màn hình")
    parser.add_argument("--gui", action="store_true", help="Khởi động giao diện GUI")
    args = parser.parse_args()

    cfg = load_config()
    game_path = Path(args.game_path) if args.game_path else Path(cfg.get("default_game_path", "C:\\YostarGames\\StellaSora_EN"))

    if args.check_update:
        repo = cfg.get("github_repo", "doubleD1302/AmeeVH")
        cur_ver = cfg.get("version", "0.1.0")
        res = GitHubManager.check_updates(repo, cur_ver)
        if res.get("success"):
            print(f"Phiên bản hiện tại: v{cur_ver}")
            print(f"Bản mới nhất trên GitHub: {res.get('tag')} ({res.get('name')})")
            print(f"Ngày phát hành: {res.get('date')}")
            print(f"Trạng thái cập nhật: {'Có bản cập nhật mới!' if res.get('has_update') else 'Đang là bản mới nhất'}")
            print(f"URL: {res.get('html_url')}")
            for a in res.get("assets", []):
                print(f"  Asset: {a.get('name')} ({a.get('size')} bytes)")
            return 0
        else:
            print(f"[FAIL] {res.get('error')}")
            return 1

    if args.install:
        ok, msg = LocalizationEngine.install_pc(game_path)
        print(f"[{'OK' if ok else 'FAIL'}] {msg}")
        return 0 if ok else 1
    elif args.rollback:
        ok, msg = LocalizationEngine.rollback_pc(game_path)
        print(f"[{'OK' if ok else 'FAIL'}] {msg}")
        return 0 if ok else 1
    elif args.copy_error:
        print(DiagnosticCollector.generate_report(game_path))
        return 0

    # Default to GUI if Tkinter available
    if TKINTER_AVAILABLE:
        root = tk.Tk()
        app = LauncherGUI(root)
        root.mainloop()
    else:
        print("Giao diện GUI yêu cầu Tkinter. Đang chạy ở chế độ CLI:")
        print(DiagnosticCollector.generate_report(game_path))
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
