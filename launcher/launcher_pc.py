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

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
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
    "version": "0.3.0",
    "app_name": "Stella Sora Việt Hóa - Multiplatform Launcher",
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
    }
    if not game_path.exists():
        return info

    # Check running process
    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq StellaSora.exe" /NH', shell=True).decode()
        info["is_running"] = "StellaSora.exe" in out
    except Exception:
        info["is_running"] = False

    # Check client version
    launcher_cfg = game_path / "game-launcher-config.json"
    if launcher_cfg.exists():
        try:
            d = json.loads(launcher_cfg.read_text(encoding="utf-8"))
            info["client_ver"] = d.get("version", "Unknown")
        except Exception:
            pass

    # Check manifest version
    mani = game_path / "Persistent_Store" / "ss_win.mani"
    if mani.exists():
        try:
            lines = mani.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in lines[:10]:
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

            # Source batch proposals
            batches_dir = BASE_DIR / "work" / "batches"
            batch_files = {
                "Persistent_Store/Videos/Prologue-Prologue_P4_JPVA_FP_EN.srt": batches_dir / "SRT001_JPVA.json",
                "Persistent_Store/Videos/Prologue-Prologue_P4_CNVA_FP_EN.srt": batches_dir / "SRT002_CNVA.json",
                "Persistent_Store/Videos/CH04ED-CH04ED_EN.srt": batches_dir / "SRT003_CH04ED.json",
                "Persistent_Store/Videos/CH06ED-CH06ED_EN.srt": batches_dir / "SRT004_CH06ED.json",
            }
            patched_arcx = BASE_DIR / "work" / "research" / "data_patched_vi.arcx"

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
                log(f"   Đã sao lưu: {orig_table.name} (SHA: {orig_hash[:8]}...)")

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
    def check_updates(cls, repo: str, current_ver: str = "0.3.0") -> dict:
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
        launcher_asset = next((a for a in assets if "Launcher.exe" in a.get("name", "")), None)
        zip_asset = next((a for a in assets if a.get("name", "").endswith(".zip")), None)
        apk_asset = next((a for a in assets if a.get("name", "").endswith(".apk")), None)

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
            "assets": assets,
        }

    @staticmethod
    def download_file(url: str, dest_path: Path, progress_cb=None) -> bool:
        """Downloads a remote file with progress reporting."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StellaSora-Localizer"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                total_len = resp.headers.get("Content-Length")
                total_size = int(total_len) if total_len else 0
                downloaded = 0
                chunk_size = 64 * 1024

                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_path, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_cb and total_size > 0:
                            percent = min(100.0, (downloaded / total_size) * 100.0)
                            progress_cb(downloaded, total_size, percent)
            return True
        except Exception as e:
            DiagnosticCollector.log(f"Lỗi khi tải tệp {url}: {e}")
            return False

    @staticmethod
    def perform_self_update(new_exe_path: Path) -> tuple[bool, str]:
        """Self-updates the launcher on Windows."""
        try:
            if getattr(sys, "frozen", False):
                current_exe = Path(sys.executable).resolve()
                ps_script = f"Start-Sleep -Milliseconds 800; Move-Item -Force '{new_exe_path}' '{current_exe}'; Start-Process '{current_exe}'"
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
                os._exit(0)
            else:
                target_exe = EXE_DIR / "StellaSora_Launcher.exe"
                shutil.copy2(new_exe_path, target_exe)
                return True, f"Đã lưu bản Launcher mới tại: {target_exe}"
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

        self.root.title("Stella Sora - Trình Cài Đặt Việt Hóa Đa Nền Tảng (1-Chạm)")
        self.root.geometry("820x620")
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
        # Card 1: Game Status
        card_info = tk.Frame(self.tab_pc, bg="#24273a", bd=1, relief="solid")
        card_info.pack(fill="x", padx=12, pady=10)

        tk.Label(card_info, text="Trạng Thái Trò Chơi", font=("Segoe UI", 11, "bold"), fg="#cdd6f4", bg="#24273a").grid(row=0, column=0, sticky="w", padx=12, pady=8)

        self.lbl_path = tk.Label(card_info, text=f"Thư mục: {self.game_path}", font=("Segoe UI", 9), fg="#bac2de", bg="#24273a")
        self.lbl_path.grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=2)

        self.lbl_game_ver = tk.Label(card_info, text="Phiên bản: Đang kiểm tra...", font=("Segoe UI", 9), fg="#bac2de", bg="#24273a")
        self.lbl_game_ver.grid(row=2, column=0, sticky="w", padx=12, pady=2)

        self.lbl_patch_status = tk.Label(card_info, text="Trạng thái Việt Hóa: Chưa xác định", font=("Segoe UI", 10, "bold"), fg="#f9e2af", bg="#24273a")
        self.lbl_patch_status.grid(row=3, column=0, sticky="w", padx=12, pady=6)

        # Buttons Row
        btn_frame = tk.Frame(self.tab_pc, bg="#1e1e2e")
        btn_frame.pack(fill="x", padx=12, pady=6)

        self.btn_install = tk.Button(btn_frame, text="⚡ CÀI ĐẶT VIỆT HÓA (1-CHẠM)", font=("Segoe UI", 11, "bold"),
                                     bg="#a6e3a1", fg="#11111b", activebackground="#94e2d5",
                                     padx=16, pady=8, bd=0, cursor="hand2", command=self.on_install_pc)
        self.btn_install.pack(side="left", padx=(0, 10))

        self.btn_rollback = tk.Button(btn_frame, text="🔄 Khôi Phục Gốc (Rollback)", font=("Segoe UI", 10, "bold"),
                                      bg="#eba0ac", fg="#11111b", activebackground="#f38ba8",
                                      padx=12, pady=8, bd=0, cursor="hand2", command=self.on_rollback_pc)
        self.btn_rollback.pack(side="left", padx=10)

        self.btn_refresh = tk.Button(btn_frame, text="🔄 Làm Mới", font=("Segoe UI", 10),
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

    def refresh_status(self):
        info = detect_game_info(self.game_path)
        if not info["exists"]:
            self.lbl_patch_status.config(text="⚠️ Không tìm thấy game!", fg="#f38ba8")
            self.btn_install.config(state="disabled")
            return

        self.lbl_game_ver.config(text=f"Client: {info['client_ver']} | Game: {info['game_ver']} | Res: {info['res_ver']}")
        if info["installed_patch"]:
            self.lbl_patch_status.config(text="✓ ĐÃ CÀI ĐẶT BẢN VIỆT HÓA (Active)", fg="#a6e3a1")
        else:
            self.lbl_patch_status.config(text="Chưa cài đặt bản Việt Hóa", fg="#f9e2af")
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
                messagebox.showerror("Lỗi Khôi Phục", f"Lỗi khôi phục:\n{msg}")
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

            temp_dest = EXE_DIR / "StellaSora_Launcher_update.exe"

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
    parser.add_argument("--install", action="store_true", help="Cài đặt Việt Hóa 1-chạm")
    parser.add_argument("--rollback", action="store_true", help="Khôi phục nguyên bản gốc")
    parser.add_argument("--check-update", action="store_true", help="Kiểm tra bản phát hành mới nhất từ GitHub Releases")
    parser.add_argument("--copy-error", action="store_true", help="In báo cáo lỗi ra màn hình")
    parser.add_argument("--gui", action="store_true", help="Khởi động giao diện GUI")
    args = parser.parse_args()

    cfg = load_config()
    game_path = Path(cfg.get("default_game_path", "C:\\YostarGames\\StellaSora_EN"))

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
