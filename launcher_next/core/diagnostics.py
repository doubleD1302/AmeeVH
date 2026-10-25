"""System diagnostics and safe ADB discovery bridge."""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from launcher_next.core.types import GameInfo

logger = logging.getLogger("launcher.diagnostics")


@dataclass
class SystemReport:
    timestamp: str
    os_name: str
    os_release: str
    os_arch: str
    python_version: str
    is_frozen: bool
    screen_dpi_info: str
    launcher_dir: str
    app_data_dir: str
    backup_dir: str
    game_detected: bool
    game_source: str
    game_path: str
    game_executable_found: bool
    game_running: bool
    disk_free_gb: float
    receipt_summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_text(self) -> str:
        lines = [
            "=== BÁO CÁO CHẨN ĐOÁN HỆ THỐNG STELLA SORA LAUNCHER ===",
            f"Thời gian tạo: {self.timestamp}",
            f"Hệ điều hành: {self.os_name} {self.os_release} ({self.os_arch})",
            f"Môi trường Python: {self.python_version} (Đóng gói EXE: {self.is_frozen})",
            f"Độ phân giải / DPI: {self.screen_dpi_info}",
            f"Thư mục ứng dụng: {self.launcher_dir}",
            f"Thư mục cấu hình (AppData): {self.app_data_dir}",
            f"Thư mục sao lưu: {self.backup_dir}",
            f"Dung lượng ổ đĩa trống: {self.disk_free_gb:.2f} GB",
            "",
            "--- Trạng thái Game ---",
            f"Phát hiện game: {'Có' if self.game_detected else 'Không'}",
            f"Nguồn phát hiện: {self.game_source}",
            f"Đường dẫn cài đặt: {self.game_path or 'Chưa xác định'}",
            f"Tệp thực thi game: {'Tồn tại' if self.game_executable_found else 'Không tìm thấy'}",
            f"Tiến trình đang chạy: {'CẢNH BÁO: ĐANG CHẠY' if self.game_running else 'Không chạy'}",
            "",
        ]
        if self.receipt_summary:
            lines.extend([
                "--- Biên bản cài đặt hiện tại ---",
                f"Phiên bản patch: {self.receipt_summary.get('patch_version', self.receipt_summary.get('version', 'N/A'))}",
                f"Thời gian cài: {self.receipt_summary.get('installed_at', 'N/A')}",
                f"Số tệp đã vá: {len(self.receipt_summary.get('applied_files', []))}",
            ])
        else:
            lines.append("--- Biên bản cài đặt hiện tại: Chưa cài đặt bản vá ---")

        return "\n".join(lines)


class DiagnosticsCollector:
    """Collects system, environment, and game diagnostic information."""

    @staticmethod
    def collect(path_manager, game_info: GameInfo, screen_info: str = "1280x900 DIP") -> SystemReport:
        import datetime

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        free_bytes = 0
        try:
            free_bytes = shutil.disk_usage(path_manager.app_data_dir).free
        except Exception:
            try:
                free_bytes = shutil.disk_usage("C:\\").free
            except Exception:
                pass
        free_gb = free_bytes / (1024**3)

        receipt_summary = None
        receipt_file = path_manager.receipt_file
        if receipt_file.is_file():
            try:
                with open(receipt_file, "r", encoding="utf-8") as f:
                    receipt_summary = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read patch receipt: {e}")

        exe_found = False
        if game_info.game_path:
            exe_path = game_info.game_path / "StellaSora.exe"
            exe_found = exe_path.is_file()

        return SystemReport(
            timestamp=now,
            os_name=platform.system(),
            os_release=platform.release(),
            os_arch=platform.machine(),
            python_version=platform.python_version(),
            is_frozen=getattr(sys, "frozen", False),
            screen_dpi_info=screen_info,
            launcher_dir=str(path_manager.resource_dir),
            app_data_dir=str(path_manager.app_data_dir),
            backup_dir=str(path_manager.backup_root),
            game_detected=game_info.installed,
            game_source=game_info.platform,
            game_path=str(game_info.game_path) if game_info.game_path else "",
            game_executable_found=exe_found,
            game_running=game_info.is_running,
            disk_free_gb=free_gb,
            receipt_summary=receipt_summary,
        )


class AdbBridge:
    """Safe ADB bridge for emulator discovery and status check.
    
    Adheres strictly to read-only discovery. Never modifies or pushes files
    automatically without user instruction.
    """

    KNOWN_SEARCH_LOCATIONS = [
        r"C:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe",
        r"C:\Program Files (x86)\Netease\MuMuPlayer-12.0\shell\adb.exe",
        r"D:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe",
        r"C:\LDPlayer\LDPlayer9\adb.exe",
        r"D:\LDPlayer\LDPlayer9\adb.exe",
        r"C:\Program Files\nox\bin\nox_adb.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
    ]

    def __init__(self, custom_adb_path: Optional[str] = None):
        self.adb_path = custom_adb_path or self.locate_adb()

    @classmethod
    def locate_adb(cls) -> Optional[str]:
        """Find adb.exe in PATH or well-known emulator paths."""
        which_path = shutil.which("adb")
        if which_path and os.path.isfile(which_path):
            return which_path

        for loc in cls.KNOWN_SEARCH_LOCATIONS:
            if os.path.isfile(loc):
                return loc

        return None

    def is_available(self) -> bool:
        return bool(self.adb_path and os.path.isfile(self.adb_path))

    def list_devices(self) -> List[Dict[str, str]]:
        """Run 'adb devices -l' safely with a short timeout."""
        if not self.is_available():
            return []

        devices = []
        try:
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            cmd = [self.adb_path, "devices", "-l"]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3,
                creationflags=creationflags,
            )
            if proc.returncode == 0:
                lines = proc.stdout.splitlines()
                for line in lines[1:]:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        serial = parts[0]
                        state = parts[1]
                        details = " ".join(parts[2:]) if len(parts) > 2 else ""
                        devices.append({
                            "serial": serial,
                            "state": state,
                            "details": details,
                        })
        except Exception as e:
            logger.warning(f"Error querying adb devices: {e}")

        return devices
