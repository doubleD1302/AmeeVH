# -*- coding: utf-8 -*-
"""
Pure-Python real-time game update guard for Stella Sora (PC Windows).

Zero PySide6 imports (enforces launcher_v2/core purity contract):
- Tails Unity Player.log (Yostar standalone + Steam) for live update prompts,
  BinDiffPatch download sizes, and patch verification errors.
- Gracefully minimizes or closes verified StellaSora.exe windows/processes.
- Manages optional Windows HKCU Run (--tray) autostart.
- Evaluates pre-Qt `--launch-game` fast-path guard decisions.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .game_detection import GAME_EXE_NAME, GameDetector, is_game_process_running
from .official_resources import OfficialClient
from .official_restore import check_official_update
from .update_notice import has_game_patch_conflict_in_log, newer

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore[assignment]

AUTOSTART_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_VALUE_NAME = "StellaSoraVietHoaGuard"

# Verified against live Stella Sora Unity Player.log sessions (Yostar & Steam)
_RE_NEED_FULL = re.compile(r"Need\s+full\s+update\s*:\s*True", re.I)
_RE_NEED_PATCH = re.compile(
    r"need\s+patch\s+update\s*:\s*True(?:\s*\(([^)\r\n]+)\))?",
    re.I,
)
_RE_BINDIFF_PLAN = re.compile(
    r"BinDiffPatch\s+Ver\s*:\s*([0-9A-Za-z_.-]+)\s+Need\s+update\s+bundles\s*:\s*(\d+)\s*\+\s*(\d+)"
    r"(?:.*?Need\s+download\s+size\s*:\s*([^\r\n]+))?",
    re.I,
)
_RE_UPDATE_HINT = re.compile(r"ShowHintMessageBeforeDownloadResources", re.I)
_RE_PATCH_ERROR = re.compile(
    r"BinDiffPatchError|Patch file verification failed|Data check fail|no found patch target bundle",
    re.I,
)


@dataclass(frozen=True)
class GameUpdateSignal:
    """Structured signal emitted when an official game update or patch conflict is detected."""

    source: str  # "player_log" | "official_server"
    kind: str  # "update_prompt" | "patch_update" | "full_update" | "patch_error" | "server_update"
    detail: str
    download_size: str = ""
    patch_transition: str = ""
    local_game_version: str = ""
    local_resource_version: str = ""
    latest_game_version: str = ""
    latest_resource_version: str = ""
    log_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def fingerprint(self) -> str:
        return "|".join(
            [
                self.source,
                self.kind,
                self.patch_transition,
                self.latest_resource_version,
                self.latest_game_version,
                self.download_size,
            ]
        )


def default_player_log_paths(game_root: Optional[Path] = None) -> list[Path]:
    """Return Unity Player.log candidates for Yostar standalone and Steam builds."""
    user_profile = os.environ.get("USERPROFILE")
    base = (Path(user_profile) if user_profile else Path.home()) / "AppData" / "LocalLow" / "YOSTAR (HONG KONG) LIMITED"
    yostar = base / "StellaSora" / "Player.log"
    steam = base / "StellaSora_steam" / "Player.log"
    is_steam = False
    if game_root is not None:
        try:
            gp = Path(game_root)
            is_steam = "steamapps" in str(gp).lower() or (gp / "steam_appid.txt").is_file()
        except OSError:
            is_steam = False
    return [steam, yostar] if is_steam else [yostar, steam]


def _compute_stale_cutoff(game_root: Optional[Path] = None, game_info: Any = None) -> float:
    """Return latest timestamp of manifest/receipt/restore state so older logs are ignored."""
    cutoff = 0.0
    gpath = game_root or (getattr(game_info, "game_path", None) if game_info is not None else None)
    if gpath:
        gp = Path(gpath)
        for rel in (
            Path("Persistent_Store") / "ss_win.mani",
            Path("Persistent_Store") / "viethoa_installed.json",
            Path(".vietnamese_patch_receipt.json"),
        ):
            p = gp / rel
            try:
                if p.is_file():
                    cutoff = max(cutoff, float(p.stat().st_mtime))
            except OSError:
                pass
    receipt = getattr(game_info, "installed_receipt", None) if game_info is not None else None
    if isinstance(receipt, dict) and isinstance(receipt.get("installed_at"), str):
        try:
            inst_ts = datetime.fromisoformat(receipt["installed_at"].replace("Z", "+00:00")).timestamp()
            cutoff = max(cutoff, inst_ts)
        except ValueError:
            pass
    return cutoff


def parse_log_chunk_for_update(
    text: str,
    *,
    log_path: str = "",
    local_game_version: str = "",
    local_resource_version: str = "",
) -> Optional[GameUpdateSignal]:
    """Parse newly written Unity Player.log lines for update prompts, sizes, or errors."""
    if not text:
        return None

    has_error = False
    error_line = ""
    has_prompt = False
    has_full = False
    has_patch = False
    patch_transition = ""
    download_size = ""
    patch_detail = ""

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if _RE_PATCH_ERROR.search(line):
            has_error = True
            error_line = line[:220]
            continue

        if _RE_UPDATE_HINT.search(line):
            has_prompt = True
            continue

        if _RE_NEED_FULL.search(line):
            has_full = True
            patch_detail = line[:220]
            continue

        m_patch = _RE_NEED_PATCH.search(line)
        if m_patch:
            has_patch = True
            if m_patch.group(1):
                patch_transition = m_patch.group(1).strip()
            patch_detail = line[:220]
            continue

        m_plan = _RE_BINDIFF_PLAN.search(line)
        if m_plan:
            ver, b_main, b_add, dl_size = (
                m_plan.group(1),
                int(m_plan.group(2)),
                int(m_plan.group(3)),
                (m_plan.group(4) or "").strip(),
            )
            if (b_main + b_add) > 0:
                has_patch = True
                if not patch_transition:
                    patch_transition = f"BinDiff Ver:{ver} ({b_main + b_add} gói)"
                if dl_size:
                    download_size = dl_size
                patch_detail = line[:220]

    if has_error:
        return GameUpdateSignal(
            source="player_log",
            kind="patch_error",
            detail=f"Game báo lỗi xác minh bản vá do tệp đã Việt hóa: {error_line}",
            download_size=download_size,
            patch_transition=patch_transition,
            local_game_version=local_game_version,
            local_resource_version=local_resource_version,
            log_path=log_path,
        )

    if has_prompt:
        extra = []
        if patch_transition:
            extra.append(f"gói vá {patch_transition}")
        if download_size:
            extra.append(f"dung lượng {download_size}")
        suffix = f" ({', '.join(extra)})" if extra else ""
        return GameUpdateSignal(
            source="player_log",
            kind="update_prompt",
            detail=f"Game vừa mở hộp thoại yêu cầu tải bản cập nhật mới{suffix}.",
            download_size=download_size,
            patch_transition=patch_transition,
            local_game_version=local_game_version,
            local_resource_version=local_resource_version,
            log_path=log_path,
        )

    if has_full:
        return GameUpdateSignal(
            source="player_log",
            kind="full_update",
            detail=f"Game phát hiện bản cập nhật toàn phần từ máy chủ ({patch_detail}).",
            download_size=download_size,
            patch_transition=patch_transition,
            local_game_version=local_game_version,
            local_resource_version=local_resource_version,
            log_path=log_path,
        )

    if has_patch:
        extra = []
        if patch_transition:
            extra.append(patch_transition)
        if download_size:
            extra.append(download_size)
        suffix = f" ({' · '.join(extra)})" if extra else ""
        return GameUpdateSignal(
            source="player_log",
            kind="patch_update",
            detail=f"Game phát hiện bản vá tài nguyên mới từ Yostar{suffix}.",
            download_size=download_size,
            patch_transition=patch_transition,
            local_game_version=local_game_version,
            local_resource_version=local_resource_version,
            log_path=log_path,
        )

    return None


class GameLogWatcher:
    """Non-locking incremental tail watcher over Stella Sora Unity Player.log files."""

    MAX_CHUNK_BYTES = 512 * 1024
    RECENT_REWIND_BYTES = 16 * 1024
    RECENT_WINDOW_SECONDS = 45.0

    def __init__(
        self,
        log_paths: Optional[list[Path]] = None,
        game_root: Optional[Path] = None,
    ) -> None:
        self._explicit_paths = [Path(p) for p in log_paths] if log_paths is not None else None
        self._game_root: Optional[Path] = Path(game_root) if game_root else None
        self._offsets: dict[Path, int] = {}
        self._stale_cutoff: float = 0.0
        self._local_game_ver: str = ""
        self._local_res_ver: str = ""
        self._armed: bool = False

    def watched_paths(self) -> list[Path]:
        if self._explicit_paths is not None:
            return list(self._explicit_paths)
        return default_player_log_paths(self._game_root)

    def arm(
        self,
        *,
        game_root: Optional[Path] = None,
        game_info: Any = None,
        from_end: bool = True,
    ) -> None:
        if game_root is not None:
            self._game_root = Path(game_root)
        elif game_info is not None and getattr(game_info, "game_path", None):
            self._game_root = Path(game_info.game_path)

        self._local_game_ver = str(getattr(game_info, "version", "") or "")
        self._local_res_ver = str(getattr(game_info, "resource_version", "") or "")
        self._stale_cutoff = _compute_stale_cutoff(self._game_root, game_info)
        self._offsets.clear()

        now = time.time()
        for path in self.watched_paths():
            try:
                if path.is_file():
                    st = path.stat()
                    if not from_end:
                        self._offsets[path] = 0
                    elif st.st_mtime >= self._stale_cutoff and (now - st.st_mtime) <= self.RECENT_WINDOW_SECONDS:
                        # Game likely started writing just before we armed; rewind tail window
                        self._offsets[path] = max(0, st.st_size - self.RECENT_REWIND_BYTES)
                    else:
                        self._offsets[path] = st.st_size
                else:
                    self._offsets[path] = 0
            except OSError:
                self._offsets[path] = 0
        self._armed = True

    def disarm(self) -> None:
        self._armed = False
        self._offsets.clear()

    @property
    def is_armed(self) -> bool:
        return self._armed

    def poll(self) -> Optional[GameUpdateSignal]:
        if not self._armed:
            return None

        best_signal: Optional[GameUpdateSignal] = None
        severity = {
            "patch_error": 4,
            "update_prompt": 3,
            "full_update": 2,
            "patch_update": 1,
        }

        for path in self.watched_paths():
            try:
                if not path.is_file():
                    self._offsets[path] = 0
                    continue
                st = path.stat()
                if self._stale_cutoff > 0 and st.st_mtime < self._stale_cutoff:
                    self._offsets[path] = st.st_size
                    continue

                prev_offset = self._offsets.get(path, 0)
                if st.st_size < prev_offset:
                    # Unity truncated Player.log for a fresh game session
                    prev_offset = 0
                if st.st_size == prev_offset:
                    continue

                read_start = max(prev_offset, st.st_size - self.MAX_CHUNK_BYTES)
                with path.open("rb") as f:
                    f.seek(read_start)
                    raw = f.read(self.MAX_CHUNK_BYTES)
                    self._offsets[path] = f.tell()

                chunk = raw.decode("utf-8", errors="ignore")
                sig = parse_log_chunk_for_update(
                    chunk,
                    log_path=str(path),
                    local_game_version=self._local_game_ver,
                    local_resource_version=self._local_res_ver,
                )
                if sig is not None:
                    if best_signal is None or severity.get(sig.kind, 0) > severity.get(best_signal.kind, 0):
                        best_signal = sig
            except OSError:
                continue

        return best_signal


# ---------------- Win32 Process & Window Control Helpers ----------------

def _find_verified_game_pids(expected_game_root: Optional[Path] = None) -> list[int]:
    """Return PIDs of StellaSora.exe verified by executable path when expected_game_root is given."""
    if sys.platform != "win32":
        return []
    try:
        import ctypes
        from ctypes import wintypes

        TH32CS_SNAPPROCESS = 0x00000002
        INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
        PROCESS_QUERY_LIMITED_INFORMATION = 0x00001000

        class PROCESSENTRY32W(ctypes.Structure):
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
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        kernel32.Process32FirstW.restype = wintypes.BOOL
        kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        kernel32.Process32NextW.restype = wintypes.BOOL
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        expected_exe = (
            (Path(expected_game_root) / GAME_EXE_NAME).resolve()
            if expected_game_root is not None
            else None
        )

        raw_pids: list[int] = []
        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap and snap != INVALID_HANDLE_VALUE:
            try:
                pe = PROCESSENTRY32W()
                pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
                if kernel32.Process32FirstW(snap, ctypes.byref(pe)):
                    while True:
                        if str(pe.szExeFile).lower() == GAME_EXE_NAME.lower():
                            pid = int(pe.th32ProcessID)
                            if pid > 0 and pid != os.getpid():
                                raw_pids.append(pid)
                        if not kernel32.Process32NextW(snap, ctypes.byref(pe)):
                            break
            finally:
                kernel32.CloseHandle(snap)

        if expected_exe is None:
            return raw_pids

        verified: list[int] = []
        for pid in raw_pids:
            h_query = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not h_query:
                verified.append(pid)
                continue
            try:
                buf_len = wintypes.DWORD(32768)
                buf = ctypes.create_unicode_buffer(buf_len.value)
                if kernel32.QueryFullProcessImageNameW(h_query, 0, buf, ctypes.byref(buf_len)):
                    if Path(buf.value).resolve() != expected_exe:
                        continue
                verified.append(pid)
            finally:
                kernel32.CloseHandle(h_query)
        return verified
    except Exception:
        return []


def _enum_windows_for_pids(pids: set[int]) -> list[int]:
    if sys.platform != "win32" or not pids:
        return []
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
        user32.EnumWindows.restype = wintypes.BOOL
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD

        hwnds: list[int] = []

        @WNDENUMPROC
        def _cb(hwnd, _lparam):
            if user32.IsWindowVisible(hwnd):
                proc_id = wintypes.DWORD(0)
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
                if int(proc_id.value) in pids:
                    hwnds.append(int(hwnd))
            return True

        user32.EnumWindows(_cb, 0)
        return hwnds
    except Exception:
        return []


def minimize_game_windows(expected_game_root: Optional[Path] = None) -> int:
    """Minimize visible StellaSora.exe windows so the launcher alert is immediately visible."""
    if sys.platform != "win32":
        return 0
    pids = set(_find_verified_game_pids(expected_game_root))
    hwnds = _enum_windows_for_pids(pids)
    if not hwnds:
        return 0
    try:
        import ctypes
        from ctypes import wintypes

        SW_MINIMIZE = 6
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL
        count = 0
        for hwnd in hwnds:
            user32.ShowWindow(wintypes.HWND(hwnd), SW_MINIMIZE)
            count += 1
        return count
    except Exception:
        return 0


def close_game_gracefully_or_force(
    expected_game_root: Optional[Path] = None,
    *,
    wait_seconds: float = 2.5,
) -> tuple[bool, str]:
    """Send WM_CLOSE to StellaSora.exe first, then fall back to verified TerminateProcess/taskkill."""
    if sys.platform != "win32":
        return False, "Chỉ hỗ trợ đóng tiến trình trên Windows."

    pids = _find_verified_game_pids(expected_game_root)
    if not pids:
        return True, "Không phát hiện tiến trình StellaSora.exe đang chạy."

    # 1. Try graceful WM_CLOSE on top-level windows
    try:
        import ctypes
        from ctypes import wintypes

        WM_CLOSE = 0x0010
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.PostMessageW.restype = wintypes.BOOL

        hwnds = _enum_windows_for_pids(set(pids))
        for hwnd in hwnds:
            user32.PostMessageW(wintypes.HWND(hwnd), WM_CLOSE, 0, 0)

        if hwnds and wait_seconds > 0:
            deadline = time.monotonic() + float(wait_seconds)
            while time.monotonic() < deadline:
                if not is_game_process_running():
                    return True, "Đã đóng game Stella Sora an toàn."
                time.sleep(0.15)
    except Exception:
        pass

    # 2. Fallback to verified TerminateProcess + taskkill /F /PID
    try:
        import ctypes
        from ctypes import wintypes

        PROCESS_TERMINATE = 0x0001
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.TerminateProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        remaining_pids = _find_verified_game_pids(expected_game_root)
        if not remaining_pids:
            return True, "Đã đóng tiến trình StellaSora.exe."

        terminated_any = False
        access_denied = False
        for pid in remaining_pids:
            h_term = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
            if h_term:
                try:
                    if kernel32.TerminateProcess(h_term, 1):
                        terminated_any = True
                        continue
                finally:
                    kernel32.CloseHandle(h_term)
            elif ctypes.get_last_error() == 5:
                access_denied = True

            res = subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
            if res.returncode == 0:
                terminated_any = True
            elif res.returncode == 5:
                access_denied = True

        if terminated_any:
            time.sleep(0.35)
            return not is_game_process_running(), "Đã đóng tiến trình StellaSora.exe."
        if access_denied:
            return (
                False,
                "Không đủ quyền đóng StellaSora.exe (game có thể đang chạy quyền Quản trị). Hãy đóng bằng Task Manager.",
            )
        return False, "Không thể đóng StellaSora.exe. Hãy đóng thủ công hoặc dùng Task Manager."
    except Exception as exc:  # noqa: BLE001
        return False, f"Lỗi khi đóng game: {exc}"


# ---------------- Windows HKCU Autostart (--tray) ----------------

def build_autostart_command(
    exe_path: Optional[Path] = None,
    *,
    app_data_dir: Optional[Path] = None,
) -> str:
    """Build HKCU Run command line to start the launcher silently in system tray."""
    parts: list[str] = []
    if exe_path is not None:
        parts.append(f'"{Path(exe_path).resolve()}"')
    elif getattr(sys, "frozen", False):
        parts.append(f'"{Path(sys.executable).resolve()}"')
    else:
        app_py = Path(__file__).resolve().parents[1] / "app.py"
        parts.append(f'"{Path(sys.executable).resolve()}"')
        parts.append(f'"{app_py}"')
    parts.append("--tray")
    if app_data_dir is not None:
        parts.append("--app-data-dir")
        parts.append(f'"{Path(app_data_dir).resolve()}"')
    return " ".join(parts)


def is_windows_autostart_enabled() -> bool:
    if sys.platform != "win32" or winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_RUN_KEY, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, AUTOSTART_VALUE_NAME)
            return bool(str(val or "").strip())
    except OSError:
        return False


def set_windows_autostart(
    enabled: bool,
    exe_path: Optional[Path] = None,
    *,
    app_data_dir: Optional[Path] = None,
) -> tuple[bool, str]:
    """Enable or disable silent tray autostart in HKCU\\...\\Run (no admin required)."""
    if sys.platform != "win32" or winreg is None:
        return False, "Chỉ hỗ trợ khởi động cùng Windows."
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, AUTOSTART_RUN_KEY) as key:
            if enabled:
                cmd = build_autostart_command(exe_path, app_data_dir=app_data_dir)
                winreg.SetValueEx(key, AUTOSTART_VALUE_NAME, 0, winreg.REG_SZ, cmd)
                return True, "Đã bật khởi chạy ngầm bảo vệ cập nhật cùng Windows."
            try:
                winreg.DeleteValue(key, AUTOSTART_VALUE_NAME)
            except FileNotFoundError:
                pass
            return True, "Đã tắt khởi chạy cùng Windows."
    except OSError as exc:
        return False, f"Không thể cập nhật Registry khởi động cùng Windows: {exc}"


# ---------------- Pre-Qt `--launch-game` Fast-Path Evaluator ----------------

def _digits(value: Any) -> Optional[int]:
    s = str(value or "").strip()
    return int(s) if s.isdigit() else None


def _evaluate_cached_official_check(cache_file: Path, game_info: Any) -> Optional[dict[str, Any]]:
    if not cache_file.is_file():
        return None
    try:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        if not isinstance(cached, dict):
            return None
    except (OSError, ValueError):
        return None

    latest_res = str(cached.get("resource_version") or "")
    latest_game = str(cached.get("game_version") or "")
    local_res = str(getattr(game_info, "resource_version", "") or "")
    local_game = str(getattr(game_info, "version", "") or "")
    new_r, old_r = _digits(latest_res), _digits(local_res)
    update_available = bool(new_r and old_r and new_r > old_r)
    if not update_available and latest_game and local_game not in ("", "unknown"):
        update_available = newer(latest_game, local_game)
    vh_modified = bool(getattr(game_info, "installed_receipt", None)) or bool(getattr(game_info, "has_vietnamese", False))
    return {
        "latest_resource_version": latest_res,
        "latest_game_version": latest_game,
        "local_resource_version": local_res,
        "local_game_version": local_game,
        "update_available": update_available,
        "vh_modified": vh_modified,
        "needs_restore": bool(update_available and vh_modified),
        "server_data_version": cached.get("server_data_version"),
        "checked_at": cached.get("checked_at", ""),
        "from_cache": True,
    }


def evaluate_fast_launch_guard(
    pm: Any,
    cm: Any,
    *,
    client: Optional[OfficialClient] = None,
    timeout: int = 8,
) -> dict[str, Any]:
    """Pre-Qt fast-path guard decision for `--launch-game`.

    Returns a dict with key ``action`` in:
      - ``"launch"``: safe to launch Stella Sora immediately without loading Qt.
      - ``"already_running"``: StellaSora.exe is already running.
      - ``"block"``: official update or patch conflict detected while Việt hóa is active;
        must open GUI directly into mandatory restore dialog.
      - ``"open_gui"``: game folder not found/configured; open normal launcher UI.
    """
    raw_path = str(cm.get("game_path", "") or "").strip()
    auto_detect = bool(cm.get("auto_detect_game", True))
    detector = GameDetector(pm.backup_root)
    info = detector.detect_info(raw_path if raw_path else (None if auto_detect else ""))

    if not info.installed or not info.game_path:
        return {"action": "open_gui", "reason": "not_installed", "game": info}

    if is_game_process_running():
        return {"action": "already_running", "reason": "running", "game": info}

    vh_modified = bool(info.installed_receipt or info.has_vietnamese)
    if not vh_modified:
        return {"action": "launch", "reason": "vanilla", "game": info}

    notice: Optional[dict[str, Any]] = None
    try:
        oc = client or OfficialClient("EN", timeout=timeout, retries=1)
        notice = check_official_update(oc, info, pm.official_check_file)
    except Exception:  # noqa: BLE001
        notice = _evaluate_cached_official_check(pm.official_check_file, info)

    if notice and notice.get("needs_restore"):
        return {
            "action": "block",
            "reason": "official_update",
            "game": info,
            "notice": notice,
        }

    if has_game_patch_conflict_in_log(info):
        fallback_notice = dict(notice or {})
        fallback_notice.setdefault("local_resource_version", str(info.resource_version or "unknown"))
        fallback_notice.setdefault("local_game_version", str(info.version or "unknown"))
        fallback_notice.setdefault("latest_resource_version", "Bản mới (phát hiện từ Player.log)")
        fallback_notice.setdefault("latest_game_version", str(info.version or "unknown"))
        fallback_notice["update_available"] = True
        fallback_notice["vh_modified"] = True
        fallback_notice["needs_restore"] = True
        fallback_notice["source"] = "player_log"
        fallback_notice["detail"] = "Nhật ký Stella Sora ghi nhận lỗi xác minh tệp bản vá gần đây."
        return {
            "action": "block",
            "reason": "log_conflict",
            "game": info,
            "notice": fallback_notice,
        }

    return {
        "action": "launch",
        "reason": "up_to_date",
        "game": info,
        "notice": notice,
    }
