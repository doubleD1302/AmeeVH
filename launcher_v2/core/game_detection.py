# -*- coding: utf-8 -*-
"""
Game detection, status resolution, process monitoring, and execution.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore[assignment]

from .types import GameInfo

STELLA_SORA_STEAM_APP_ID = "4813850"
GAME_EXE_NAME = "StellaSora.exe"


def canonicalize_path(p: str | Path) -> str:
    """Returns canonical normalized absolute path string."""
    try:
        resolved = Path(p).resolve()
        # On Windows normalize drive letter casing
        s = os.path.normcase(str(resolved)).replace("/", "\\").rstrip("\\")
        if len(s) >= 2 and s[1] == ":":
            s = s[0].upper() + s[1:]
        return s
    except Exception:
        return str(p).replace("/", "\\").rstrip("\\")


def find_game_exe_hint(chosen) -> Optional[Path]:
    """A folder next to/inside ``chosen`` that really contains StellaSora.exe (parent or a direct child), else None.

    Used to say "the game is actually in X" when the user picked the parent or a sub-folder of the game folder.
    Bounded: looks at the parent and at most 80 direct children, never recurses.
    """
    if not chosen:
        return None
    try:
        base = Path(chosen)
        candidates = [base.parent] if base.parent != base else []
        if base.is_dir():
            candidates += [c for _, c in zip(range(80), (e for e in base.iterdir() if e.is_dir()))]
        for c in candidates:
            if (c / GAME_EXE_NAME).is_file():
                return c
    except (OSError, TypeError):
        pass
    return None


def is_game_process_running() -> bool:
    """Checks whether StellaSora.exe is running on Windows with 64-bit safe HANDLE types."""
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            TH32CS_SNAPPROCESS = 0x00000002
            INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ("dwSize", wintypes.DWORD),
                    ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD),
                    ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD),
                    ("szExeFile", ctypes.c_char * 260),
                ]

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
            kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
            kernel32.Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
            kernel32.Process32First.restype = wintypes.BOOL
            kernel32.Process32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
            kernel32.Process32Next.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL

            h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if h_snap and h_snap != INVALID_HANDLE_VALUE:
                pe = PROCESSENTRY32()
                pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
                found = False
                target_lower = GAME_EXE_NAME.lower()
                try:
                    if kernel32.Process32First(h_snap, ctypes.byref(pe)):
                        while True:
                            if pe.szExeFile.decode(errors="ignore").lower() == target_lower:
                                found = True
                                break
                            if not kernel32.Process32Next(h_snap, ctypes.byref(pe)):
                                break
                finally:
                    kernel32.CloseHandle(h_snap)
                return found
        except Exception:
            pass
    try:
        output = subprocess.check_output(
            ["tasklist", "/FI", f"IMAGENAME eq {GAME_EXE_NAME}", "/NH"],
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            timeout=10,
        )
        return GAME_EXE_NAME.lower() in output.lower()
    except Exception:
        return False


def _available_drive_letters() -> list[str]:
    """Returns mounted local fixed/removable drive letters (C..Z) without probing slow network shares."""
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.GetLogicalDrives.argtypes = []
            kernel32.GetLogicalDrives.restype = wintypes.DWORD
            kernel32.GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
            kernel32.GetDriveTypeW.restype = wintypes.UINT

            bitmask = kernel32.GetLogicalDrives()
            drives = []
            # DRIVE_FIXED = 3, DRIVE_REMOVABLE = 2
            for idx in range(2, 26):
                if bitmask & (1 << idx):
                    letter = chr(ord("A") + idx)
                    dtype = kernel32.GetDriveTypeW(f"{letter}:\\")
                    if dtype in (2, 3):
                        drives.append(letter)
            if drives:
                return drives
        except Exception:
            pass
    return ["C", "D", "E", "F", "G"]


def get_steam_libraries() -> list[Path]:
    """Finds all configured Steam library folders on the system."""
    libraries: list[Path] = []
    seen = set()

    def _add_lib(p: Path):
        try:
            if p.exists():
                cp = canonicalize_path(p)
                if cp not in seen:
                    seen.add(cp)
                    libraries.append(p)
        except OSError:
            pass

    # 1. Check Windows Registry for Steam install path
    steam_path: Optional[Path] = None
    if os.name == "nt" and winreg is not None:
        reg_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
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

    drives = _available_drive_letters()
    common_steam = [
        Path(r"C:\Program Files (x86)\Steam"),
        Path(r"C:\Program Files\Steam"),
    ]
    for d in drives:
        common_steam.append(Path(f"{d}:\\Steam"))
        common_steam.append(Path(f"{d}:\\SteamLibrary"))

    for cs in common_steam:
        if cs.exists() and steam_path is None:
            steam_path = cs

    if steam_path and steam_path.exists():
        _add_lib(steam_path)
        vdf = steam_path / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            try:
                content = vdf.read_text(encoding="utf-8", errors="ignore")
                matches = re.findall(r'"path"\s+"([^"]+)"', content)
                for m in matches:
                    _add_lib(Path(m.replace(r"\\", "\\")))
            except Exception:
                pass

    for cs in common_steam:
        _add_lib(cs)

    return libraries


def _discover_from_uninstall_registry() -> list[Path]:
    """Checks Windows Uninstall registry keys for Stella Sora InstallLocation."""
    results: list[Path] = []
    if os.name != "nt" or winreg is None:
        return results
    uninstall_roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hkey, root_subkey in uninstall_roots:
        try:
            with winreg.OpenKey(hkey, root_subkey) as root_key:
                subkey_count, _, _ = winreg.QueryInfoKey(root_key)
                for i in range(subkey_count):
                    try:
                        sub_name = winreg.EnumKey(root_key, i)
                        with winreg.OpenKey(root_key, sub_name) as sk:
                            try:
                                loc, _ = winreg.QueryValueEx(sk, "InstallLocation")
                            except OSError:
                                loc = ""
                            if loc and isinstance(loc, str):
                                p = Path(loc.strip().strip('"'))
                                if (p / GAME_EXE_NAME).is_file():
                                    results.append(p)
                                    continue
                                # Yostar launcher sometimes registers parent folder containing StellaSora_EN
                                sub_p = p / "StellaSora_EN"
                                if (sub_p / GAME_EXE_NAME).is_file():
                                    results.append(sub_p)
                    except OSError:
                        continue
        except OSError:
            continue
    return results


def find_all_potential_game_installations() -> list[dict]:
    """Discovers all Stella Sora installations on the machine."""
    discovered: list[dict] = []
    seen_canonical = set()

    def _register(candidate: Path, default_platform: str = "standalone"):
        try:
            if not candidate.exists() or not (candidate / GAME_EXE_NAME).is_file():
                return
            cpath = canonicalize_path(candidate)
            if cpath in seen_canonical:
                return
            seen_canonical.add(cpath)
            is_steam = (
                default_platform == "steam"
                or "steamapps" in str(candidate).lower()
                or (candidate / "steam_appid.txt").exists()
            )
            plat = "steam" if is_steam else "standalone"
            label = f"Steam ({candidate})" if plat == "steam" else f"Yostar Standalone ({candidate})"
            discovered.append(
                {
                    "path": candidate,
                    "canonical": cpath,
                    "platform": plat,
                    "label": label,
                }
            )
        except OSError:
            pass

    # 0. Launcher's own directory and parent directories (when placed inside game folder)
    local_dirs = []
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        local_dirs.extend([exe_dir, exe_dir.parent])
    else:
        src_root = Path(__file__).resolve().parents[2]
        local_dirs.extend([src_root, src_root.parent])
    for ld in local_dirs:
        _register(ld)

    # 1. Search Steam libraries
    for lib in get_steam_libraries():
        _register(lib / "steamapps" / "common" / "Stella Sora", "steam")

    # 2. Search Yostar / Standalone paths across all mounted drives C..Z
    drives = _available_drive_letters()
    for d in drives:
        for rel in (
            f"{d}:\\YostarGames\\StellaSora_EN",
            f"{d}:\\Games\\StellaSora_EN",
            f"{d}:\\StellaSora_EN",
            f"{d}:\\Program Files\\YostarGames\\StellaSora_EN",
            f"{d}:\\Program Files (x86)\\YostarGames\\StellaSora_EN",
        ):
            _register(Path(rel), "standalone")

    # 3. Search Windows Uninstall Registry
    for reg_cand in _discover_from_uninstall_registry():
        _register(reg_cand)

    return discovered


class GameDetector:
    """Resolves and inspects the active game target."""

    def __init__(self, backup_root: Path | str):
        self.backup_root = Path(backup_root)

    def detect_info(self, raw_path: str | Path | None) -> GameInfo:
        """Inspects game directory and returns structured GameInfo."""
        if not raw_path:
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

        receipt_file = path / ".vietnamese_patch_receipt.json"
        installed_receipt = None
        has_vietnamese = False
        vi_version = None
        receipt_stale = False
        if receipt_file.is_file():
            try:
                candidate = json.loads(receipt_file.read_text(encoding="utf8"))
                if (
                    isinstance(candidate, dict)
                    and candidate.get("schema") == 2
                    and candidate.get("game_root") == cpath
                    and isinstance(candidate.get("files"), dict)
                    and candidate.get("files")
                ):
                    installed_receipt = candidate
                    vi_version = candidate.get("version")
                    files_map = candidate["files"]
                    for key_rel in ("Persistent_Store/Tables/data.arcx", "Persistent_Store/Scripts/lua.arcx"):
                        if key_rel in files_map and isinstance(files_map[key_rel], dict):
                            expected_size = files_map[key_rel].get("size")
                            disk_file = path / key_rel
                            try:
                                if not disk_file.is_file() or (
                                    isinstance(expected_size, int) and disk_file.stat().st_size != expected_size
                                ):
                                    receipt_stale = True
                                    break
                            except OSError:
                                receipt_stale = True
                                break
                    has_vietnamese = not receipt_stale
            except (ValueError, OSError):
                pass
        versions = read_game_versions(path)
        official_restore = None if installed_receipt else read_official_state(path)

        # Count backups for this canonical game root
        backup_count = 0
        root_hash = hashlib.sha256(cpath.encode("utf-8")).hexdigest()[:12]
        root_backup_dir = self.backup_root / f"game_{root_hash}"
        if root_backup_dir.exists():
            try:
                backup_count = len([d for d in root_backup_dir.iterdir() if d.is_dir()])
            except OSError:
                backup_count = 0

        return GameInfo(
            installed=True,
            game_path=path,
            canonical_path=cpath,
            platform=platform,
            version=versions["game"],
            resource_version=versions["resource"],
            is_running=is_running,
            has_vietnamese=has_vietnamese,
            vietnamese_version=vi_version,
            installed_receipt=installed_receipt,
            receipt_stale=receipt_stale,
            backup_count=backup_count,
            detection_source="filesystem_scan",
            official_restore=official_restore,
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

            if game_info.platform == "steam":
                try:
                    os.startfile(f"steam://rungameid/{STELLA_SORA_STEAM_APP_ID}")
                    return True, "Đã gửi lệnh khởi động qua Steam client."
                except Exception:
                    pass

            subprocess.Popen(
                [str(exe)],
                cwd=str(game_info.game_path),
                creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0,
            )
            return True, "Khởi động game thành công!"
        except Exception as e:
            return False, f"Lỗi khởi động game: {e}"


def read_official_state(root) -> Optional[dict]:
    """Record written by a successful official-data restore (Persistent_Store/viethoa_installed.json)."""
    f = Path(root) / "Persistent_Store" / "viethoa_installed.json"
    try:
        d = json.loads(f.read_text(encoding="utf8"))
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) and d.get("status") == "official_restored" else None


def read_game_versions(root) -> dict[str, str]:
    """Read actual version headers; never infer from a directory or bundle size."""
    out = {"game": "unknown", "resource": "unknown"}
    game_version = None
    client_version = None
    root = Path(root)
    mf = root / "Persistent_Store" / "ss_win.mani"
    if mf.is_file():
        try:
            with mf.open(encoding="utf8", errors="replace") as f:
                header = "".join(next(f, "") for _ in range(32))
            for line in header.splitlines():
                line = line.strip().lstrip("$")
                m = re.match(r"^(GAME_VER|CLIENT_VER|RES_VER|RESOURCE_VER)[:=\s]+([0-9A-Za-z_.-]+)", line)
                if m:
                    k, v = m.group(1), m.group(2)
                    if k == "GAME_VER" and game_version is None:
                        game_version = v
                    elif k == "CLIENT_VER" and client_version is None:
                        client_version = v
                    elif k in ("RES_VER", "RESOURCE_VER") and out["resource"] == "unknown":
                        out["resource"] = v
            out["game"] = game_version or client_version or "unknown"
        except OSError:
            pass
    return out
