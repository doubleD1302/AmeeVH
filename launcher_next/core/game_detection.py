# -*- coding: utf-8 -*-
"""
Game detection, status resolution, process monitoring, and execution.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import winreg
from pathlib import Path
from typing import Optional

from .types import GameInfo

STELLA_SORA_STEAM_APP_ID = "3041920"
GAME_EXE_NAME = "StellaSora.exe"


def canonicalize_path(p: str | Path) -> str:
    """Returns canonical normalized absolute path string."""
    try:
        resolved = Path(p).resolve()
        # On Windows normalize drive letter casing
        s = str(resolved).replace("/", "\\").rstrip("\\")
        if len(s) >= 2 and s[1] == ":":
            s = s[0].upper() + s[1:]
        return s
    except Exception:
        return str(p).replace("/", "\\").rstrip("\\")


def is_game_process_running() -> bool:
    """Checks whether StellaSora.exe is running on Windows."""
    try:
        # Use tasklist on Windows
        output = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {GAME_EXE_NAME}", "/NH"],
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            timeout=3
        )
        return GAME_EXE_NAME.lower() in output.lower()
    except Exception:
        return False


def get_steam_libraries() -> list[Path]:
    """Finds all configured Steam library folders on the system."""
    libraries: list[Path] = []

    # 1. Check Windows Registry for Steam install path
    steam_path: Optional[Path] = None
    reg_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
    ]
    for hkey, subkey in reg_keys:
        try:
            with winreg.OpenKey(hkey, subkey) as k:
                val, _ = winreg.QueryValueEx(k, "InstallPath")
                if val and Path(val).exists():
                    steam_path = Path(val)
                    break
        except Exception:
            pass

    # Default common paths
    common_steam = [
        Path(r"C:\Program Files (x86)\Steam"),
        Path(r"C:\Program Files\Steam"),
        Path(r"D:\Steam"),
        Path(r"E:\Steam"),
        Path(r"D:\SteamLibrary"),
        Path(r"E:\SteamLibrary")
    ]
    for cs in common_steam:
        if cs.exists() and steam_path is None:
            steam_path = cs

    if steam_path and steam_path.exists():
        libraries.append(steam_path)
        # Parse libraryfolders.vdf
        vdf = steam_path / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            try:
                content = vdf.read_text(encoding="utf-8", errors="ignore")
                matches = re.findall(r'"path"\s+"([^"]+)"', content)
                for m in matches:
                    lp = Path(m.replace(r"\\", "\\"))
                    if lp.exists() and lp not in libraries:
                        libraries.append(lp)
            except Exception:
                pass

    return libraries


def find_all_potential_game_installations() -> list[dict]:
    """Discovers all Stella Sora installations on the machine."""
    discovered: list[dict] = []
    seen_canonical = set()

    # 1. Search Steam libraries
    for lib in get_steam_libraries():
        candidate = lib / "steamapps" / "common" / "Stella Sora"
        if candidate.exists() and (candidate / GAME_EXE_NAME).exists():
            cpath = canonicalize_path(candidate)
            if cpath not in seen_canonical:
                seen_canonical.add(cpath)
                discovered.append({
                    "path": candidate,
                    "canonical": cpath,
                    "platform": "steam",
                    "label": f"Steam ({candidate})"
                })

    # 2. Search Yostar / Standalone paths
    standalone_candidates = [
        Path(r"c:\YostarGames\StellaSora_EN"),
        Path(r"D:\YostarGames\StellaSora_EN"),
        Path(r"E:\YostarGames\StellaSora_EN"),
        Path(r"C:\Program Files\YostarGames\StellaSora_EN"),
        Path(r"C:\Program Files (x86)\YostarGames\StellaSora_EN")
    ]
    for sc in standalone_candidates:
        if sc.exists() and (sc / GAME_EXE_NAME).exists():
            cpath = canonicalize_path(sc)
            if cpath not in seen_canonical:
                seen_canonical.add(cpath)
                discovered.append({
                    "path": sc,
                    "canonical": cpath,
                    "platform": "standalone",
                    "label": f"Yostar Standalone ({sc})"
                })

    return discovered


class GameDetector:
    """Resolves and inspects the active game target."""

    def __init__(self, backup_root: Path):
        self.backup_root = backup_root

    def detect_info(self, raw_path: str | Path | None) -> GameInfo:
        """Inspects game directory and returns structured GameInfo."""
        if not raw_path:
            # Auto-detect
            found = find_all_potential_game_installations()
            if found:
                raw_path = found[0]["path"]
            else:
                return GameInfo(installed=False)

        path = Path(raw_path)
        if not path.exists():
            return GameInfo(installed=False, game_path=path)

        exe_path = path / GAME_EXE_NAME
        if not exe_path.exists():
            return GameInfo(installed=False, game_path=path)

        cpath = canonicalize_path(path)
        is_running = is_game_process_running()

        # Platform resolution
        platform = "standalone"
        if "steamapps" in str(path).lower() or (path / "steam_appid.txt").exists():
            platform = "steam"

        # Check for receipt
        receipt_file = path / ".vietnamese_patch_receipt.json"
        installed_receipt = None
        has_vietnamese = False
        vi_version = None

        if receipt_file.exists():
            try:
                import json
                with open(receipt_file, "r", encoding="utf-8") as f:
                    installed_receipt = json.load(f)
                    has_vietnamese = True
                    vi_version = installed_receipt.get("version", "v0.9.7")
            except Exception:
                pass

        # Also verify if patched files exist in Persistent_Store
        ps_lua = path / "Persistent_Store" / "Scripts" / "lua.arcx"
        if ps_lua.exists() and ps_lua.stat().st_size > 60_000_000:
            has_vietnamese = True
            if not vi_version:
                vi_version = "v0.9.7"

        # Count backups for this canonical game root
        backup_count = 0
        import hashlib
        root_hash = hashlib.sha256(cpath.encode("utf-8")).hexdigest()[:12]
        root_backup_dir = self.backup_root / f"game_{root_hash}"
        if root_backup_dir.exists():
            backup_count = len([d for d in root_backup_dir.iterdir() if d.is_dir()])

        return GameInfo(
            installed=True,
            game_path=path,
            canonical_path=cpath,
            platform=platform,
            version="2.0.0",
            is_running=is_running,
            has_vietnamese=has_vietnamese,
            vietnamese_version=vi_version,
            installed_receipt=installed_receipt,
            backup_count=backup_count,
            detection_source="filesystem_scan"
        )

    def launch(self, game_info: GameInfo) -> tuple[bool, str]:
        """Launches the game cleanly without console window."""
        if not game_info.installed or not game_info.game_path:
            return False, "Thư mục game không hợp lệ hoặc chưa được chọn."

        if is_game_process_running():
            return False, "Game Stella Sora hiện đang chạy rồi!"

        try:
            exe = game_info.game_path / GAME_EXE_NAME
            if not exe.exists():
                return False, f"Không tìm thấy file {GAME_EXE_NAME} trong thư mục game."

            # Launch process detached
            if game_info.platform == "steam":
                # Launch via Steam URL protocol if available, or direct exe
                try:
                    os.startfile(f"steam://rungameid/{STELLA_SORA_STEAM_APP_ID}")
                    return True, "Đã gửi lệnh khởi động qua Steam client."
                except Exception:
                    pass

            # Direct execution fallback
            subprocess.Popen(
                [str(exe)],
                cwd=str(game_info.game_path),
                creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0
            )
            return True, "Khởi động game thành công!"
        except Exception as e:
            return False, f"Lỗi khởi động game: {e}"
