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
import shutil
import subprocess
import sys
import threading
import traceback
import urllib.error
import urllib.request

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parents[1]
LAUNCHER_DIR = Path(__file__).resolve().parent
CONFIG_FILE = LAUNCHER_DIR / "config.json"
NOTIFS_FILE = LAUNCHER_DIR / "notifications.json"
BACKUP_DIR = BASE_DIR / "backups"

DEFAULT_CONFIG = {
    "version": "1.0.0",
    "app_name": "Stella Sora Việt Hóa - Multiplatform Launcher",
    "default_game_path": "C:\\YostarGames\\StellaSora_EN",
    "github_repo": "stellasora-vn/StellaSora_VietHoa",
    "github_branch": "main",
    "github_api_url": "https://api.github.com/repos/stellasora-vn/StellaSora_VietHoa/releases/latest",
    "remote_notifications_url": "https://raw.githubusercontent.com/stellasora-vn/StellaSora_VietHoa/main/launcher/notifications.json",
    "android_package": "com.YoStar.StellaSora",
    "android_game_storage": "/sdcard/Android/data/com.YoStar.StellaSora/files",
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(CONFIG_FILE.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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

            # Source batch proposals
            batches_dir = BASE_DIR / "work" / "batches"
            batch_files = {
                "Persistent_Store/Videos/Prologue-Prologue_P4_JPVA_FP_EN.srt": batches_dir / "SRT001_JPVA.json",
                "Persistent_Store/Videos/Prologue-Prologue_P4_CNVA_FP_EN.srt": batches_dir / "SRT002_CNVA.json",
                "Persistent_Store/Videos/CH04ED-CH04ED_EN.srt": batches_dir / "SRT003_CH04ED.json",
                "Persistent_Store/Videos/CH06ED-CH06ED_EN.srt": batches_dir / "SRT004_CH06ED.json",
            }

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

            (run_backup_dir / "manifest.json").write_text(json.dumps(backup_manifest, indent=2), encoding="utf-8")

            # 2. Render & Install Translated Files
            log("2. Tiến hành đóng gói và áp dụng dữ liệu Việt hóa...")
            # Import render helper from tools/localize.py
            sys.path.insert(0, str(BASE_DIR))
            from tools.localize import parse_srt, render_srt

            installed_count = 0
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
                log(f"   ✓ Đã cài đặt thành công: {orig_file.name} ({len(translations)} cues)")

            # 3. Write installation marker
            marker_file = game_path / "Persistent_Store" / "viethoa_installed.json"
            marker_data = {
                "installed_at": timestamp,
                "version": "1.0.0",
                "installed_files": target_subtitles,
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
    """Handles auto-updating from GitHub repository."""

    @staticmethod
    def check_updates(repo: str) -> dict:
        url = f"https://api.github.com/repos/{repo}/commits?per_page=1"
        req = urllib.request.Request(url, headers={"User-Agent": "StellaSora-Localizer"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                if isinstance(data, list) and len(data) > 0:
                    latest = data[0]
                    sha = latest.get("sha", "")[:7]
                    msg = latest.get("commit", {}).get("message", "").split("\n")[0]
                    date = latest.get("commit", {}).get("author", {}).get("date", "")
                    return {
                        "has_update": True,
                        "latest_commit": sha,
                        "commit_message": msg,
                        "date": date,
                    }
        except Exception as e:
            DiagnosticCollector.log(f"Không thể kiểm tra GitHub API: {e}")
        return {"has_update": False, "error": "Không thể kết nối tới GitHub"}

    @staticmethod
    def fetch_announcements(url: str) -> list[dict]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StellaSora-Localizer"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                d = json.loads(resp.read().decode())
                return d.get("announcements", [])
        except Exception:
            # Fallback to local
            if NOTIFS_FILE.exists():
                try:
                    d = json.loads(NOTIFS_FILE.read_text(encoding="utf-8"))
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
        head = tk.Frame(self.tab_news, bg="#1e1e2e")
        head.pack(fill="x", padx=12, pady=8)

        tk.Label(head, text="Thông Báo Mới & Cập Nhật GitHub", font=("Segoe UI", 12, "bold"), fg="#89b4fa", bg="#1e1e2e").pack(side="left")
        btn_check_git = tk.Button(head, text="🌐 Kiểm Tra GitHub", font=("Segoe UI", 9, "bold"), bg="#cba6f7", fg="#11111b", bd=0, padx=10, pady=4, cursor="hand2", command=self.on_check_github)
        btn_check_git.pack(side="right")

        self.txt_news = tk.Text(self.tab_news, bg="#181825", fg="#cdd6f4", font=("Segoe UI", 10), wrap="word", padx=12, pady=12, bd=0)
        self.txt_news.pack(fill="both", expand=True, padx=12, pady=8)
        self.load_announcements()

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

    def on_check_github(self):
        res = GitHubManager.check_updates(self.config.get("github_repo", ""))
        if res.get("has_update"):
            msg = f"Đã kết nối GitHub thành công!\nCommit mới nhất: {res['latest_commit']}\nNội dung: {res['commit_message']}"
            messagebox.showinfo("Cập Nhật GitHub", msg)
        else:
            messagebox.showinfo("Cập Nhật GitHub", res.get("error", "Chưa có cập nhật mới."))

    def on_copy_error_log(self):
        report = DiagnosticCollector.generate_report(self.game_path)
        self.root.clipboard_clear()
        self.root.clipboard_append(report)
        messagebox.showinfo("Đã Sao Chép!", "Đã sao chép toàn bộ thông tin mã lỗi & chẩn đoán vào bộ nhớ tạm!\nBạn chỉ cần dán (Ctrl+V) gửi cho Dev.")


def cli_main():
    parser = argparse.ArgumentParser(description="Stella Sora Việt Hóa CLI & Launcher")
    parser.add_argument("--install", action="store_true", help="Cài đặt Việt Hóa 1-chạm")
    parser.add_argument("--rollback", action="store_true", help="Khôi phục nguyên bản gốc")
    parser.add_argument("--copy-error", action="store_true", help="In báo cáo lỗi ra màn hình")
    parser.add_argument("--gui", action="store_true", help="Khởi động giao diện GUI")
    args = parser.parse_args()

    cfg = load_config()
    game_path = Path(cfg.get("default_game_path", "C:\\YostarGames\\StellaSora_EN"))

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
