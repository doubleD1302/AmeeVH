"""Unicode-safe Windows .lnk shortcut creation, persistent icon sync & Desktop status checks."""
from __future__ import annotations

import base64
import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore[assignment]

PRIMARY_GUARD_SHORTCUT_NAME = "Chơi Stella VH"
LEGACY_SHORTCUT_NAMES: tuple[str, ...] = ("Stella Sora Việt Hóa",)


def get_desktop_path() -> Path:
    """Returns the true Windows Desktop directory, resolving OneDrive/localized folders."""
    if os.name == "nt":
        if winreg is not None:
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
                ) as key:
                    val, _ = winreg.QueryValueEx(key, "Desktop")
                    p = Path(os.path.expandvars(val))
                    if p.is_dir():
                        return p
            except Exception:
                pass
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            p = Path(user_profile) / "Desktop"
            if p.is_dir():
                return p
    return Path.home() / "Desktop"


def _default_icon_cache_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or Path.home())
    return base / "StellaSora_VietHoa_Launcher"


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _notify_shell_icon_refresh() -> None:
    """Tell Windows Explorer to refresh cached desktop shortcut icons cleanly."""
    if os.name != "nt":
        return
    try:
        import ctypes

        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
    except Exception:
        pass


def ensure_persistent_shortcut_icon(
    *,
    resource_dir: Optional[Path] = None,
    icon_cache_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Copy bundled `shortcut_vh_icon.ico` into a persistent non-temp path for Windows `.lnk` shortcuts.

    PyInstaller `--onefile` extracts `sys._MEIPASS` to a temporary directory deleted on exit,
    so `.lnk` IconLocation MUST point to a persistent location under app_data_dir/icons/.
    """
    candidates: list[Path] = []
    if resource_dir is not None:
        candidates.append(Path(resource_dir) / "branding" / "shortcut_vh_icon.ico")
    default_res = Path(__file__).resolve().parents[1] / "resources" / "branding" / "shortcut_vh_icon.ico"
    if default_res not in candidates:
        candidates.append(default_res)

    src_ico: Optional[Path] = next((p for p in candidates if p.is_file()), None)
    if src_ico is None:
        return None

    base_dir = Path(icon_cache_dir) if icon_cache_dir is not None else _default_icon_cache_dir()
    dst_dir = base_dir / "icons"
    dst_ico = dst_dir / "shortcut_vh_icon.ico"
    try:
        dst_dir.mkdir(parents=True, exist_ok=True)
        need_copy = not dst_ico.is_file()
        if not need_copy:
            need_copy = _file_sha256(src_ico) != _file_sha256(dst_ico)
        if need_copy:
            tmp_dst = dst_dir / f".shortcut_vh_icon.{os.getpid()}.tmp"
            shutil.copy2(src_ico, tmp_dst)
            os.replace(tmp_dst, dst_ico)
            _notify_shell_icon_refresh()
        return dst_ico.resolve()
    except OSError:
        return src_ico.resolve()


def _vbs_escape(value: str | Path) -> str:
    return str(value).replace('"', '""')


def _ps_quote(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _create_via_powershell(
    lnk_path: Path,
    target_path: Path,
    work_dir: Path,
    icon: str,
    description: str,
    arguments: str = "",
) -> tuple[bool, str]:
    arg_stmt = f"$s.Arguments = {_ps_quote(arguments)}; " if arguments else ""
    ps_script = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut({_ps_quote(lnk_path)}); "
        f"$s.TargetPath = {_ps_quote(target_path)}; "
        f"{arg_stmt}"
        f"$s.WorkingDirectory = {_ps_quote(work_dir)}; "
        f"$s.IconLocation = {_ps_quote(icon)}; "
        f"$s.Description = {_ps_quote(description)}; "
        "$s.Save()"
    )
    encoded = base64.b64encode(ps_script.encode("utf-16-le")).decode("ascii")
    res = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        timeout=15,
    )
    if res.returncode == 0 and lnk_path.is_file():
        return True, f"Đã tạo lối tắt thành công tại {lnk_path}"
    err = res.stderr.strip() or res.stdout.strip() or f"Mã thoát {res.returncode}"
    return False, f"Lỗi tạo lối tắt: {err}"


def create_desktop_shortcut(
    target_path: Path,
    shortcut_name: str,
    working_dir: Optional[Path] = None,
    icon_location: Optional[str] = None,
    description: str = "Chơi Stella Sora (Việt Hoá · Bảo vệ cập nhật)",
    desktop_dir: Optional[Path] = None,
    arguments: str = "",
) -> tuple[bool, str]:
    """Creates a Windows .lnk desktop shortcut with full Vietnamese Unicode support (UTF-16LE VBScript + PowerShell fallback)."""
    target_path = Path(target_path).resolve()
    if not target_path.exists():
        return False, f"Không tìm thấy tệp đích: {target_path}"

    clean_name = str(shortcut_name or "").strip()
    if not clean_name:
        return False, "Tên lối tắt không hợp lệ."
    if not clean_name.lower().endswith(".lnk"):
        clean_name += ".lnk"

    desktop = Path(desktop_dir) if desktop_dir is not None else get_desktop_path()
    if not desktop.is_dir():
        try:
            desktop.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"Không thể tạo thư mục màn hình chính: {e}"

    lnk_path = desktop / clean_name

    work_dir = Path(working_dir).resolve() if working_dir else target_path.parent
    icon = str(icon_location) if icon_location else f"{target_path},0"
    clean_args = str(arguments or "").strip()
    vbs_arg_line = f's.Arguments = "{_vbs_escape(clean_args)}"\r\n' if clean_args else ""

    vbs_content = (
        'Set ws = CreateObject("WScript.Shell")\r\n'
        f'Set s = ws.CreateShortcut("{_vbs_escape(lnk_path)}")\r\n'
        f's.TargetPath = "{_vbs_escape(target_path)}"\r\n'
        f"{vbs_arg_line}"
        f's.WorkingDirectory = "{_vbs_escape(work_dir)}"\r\n'
        f's.IconLocation = "{_vbs_escape(icon)}"\r\n'
        f's.Description = "{_vbs_escape(description)}"\r\n'
        "s.Save\r\n"
    )

    vbs_path = None
    cscript_err = ""
    try:
        # cscript.exe requires UTF-16LE with BOM ('utf-16') to preserve Vietnamese Unicode paths!
        with tempfile.NamedTemporaryFile(mode="w", suffix=".vbs", delete=False, encoding="utf-16") as f:
            f.write(vbs_content)
            vbs_path = f.name

        res = subprocess.run(
            ["cscript.exe", "//nologo", vbs_path],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            timeout=10,
        )
        if res.returncode == 0 and lnk_path.is_file():
            return True, f"Đã tạo lối tắt thành công tại {lnk_path}"
        cscript_err = res.stderr.strip() or res.stdout.strip() or f"Mã thoát {res.returncode}"
    except Exception as e:
        cscript_err = str(e)
    finally:
        if vbs_path and os.path.exists(vbs_path):
            try:
                os.unlink(vbs_path)
            except OSError:
                pass

    # Fallback for Windows 11 24H2+ systems where VBScript optional feature is disabled/removed
    try:
        ok, ps_msg = _create_via_powershell(
            lnk_path,
            target_path,
            work_dir,
            icon,
            description,
            arguments=clean_args,
        )
        if ok:
            return True, ps_msg
        return False, ps_msg
    except Exception:
        return False, f"Lỗi tạo lối tắt: {cscript_err}"


def _lnk_contains_token(raw: bytes, token: str) -> bool:
    if not raw or not token:
        return False
    low_ascii = token.lower().encode("ascii", errors="ignore")
    if low_ascii and low_ascii in raw.lower():
        return True
    try:
        u16_lo = token.lower().encode("utf-16-le")
        u16_raw = raw.decode("utf-16-le", errors="ignore").lower().encode("utf-16-le")
        if u16_lo in u16_raw:
            return True
    except Exception:
        pass
    return False


def check_guarded_shortcut_status(
    desktop_dir: Optional[Path] = None,
    *,
    expected_launcher: Optional[Path] = None,
) -> dict[str, Any]:
    """Inspect Desktop for the guarded `Chơi Stella VH.lnk` shortcut (zero subprocess overhead)."""
    desktop = Path(desktop_dir) if desktop_dir is not None else get_desktop_path()
    primary_lnk = desktop / f"{PRIMARY_GUARD_SHORTCUT_NAME}.lnk"
    legacy_paths = [desktop / f"{name}.lnk" for name in LEGACY_SHORTCUT_NAMES]
    legacy_found = next((p for p in legacy_paths if p.is_file()), None)

    exists = primary_lnk.is_file()
    guarded = False
    has_synced_icon = False
    target_matches = True

    if exists:
        try:
            raw = primary_lnk.read_bytes()
            guarded = _lnk_contains_token(raw, "--launch-game")
            has_synced_icon = _lnk_contains_token(raw, "shortcut_vh_icon.ico")
            if expected_launcher is not None:
                exp_name = Path(expected_launcher).name
                if exp_name:
                    target_matches = _lnk_contains_token(raw, exp_name)
        except OSError:
            exists = False

    return {
        "exists": exists,
        "guarded": guarded,
        "has_synced_icon": has_synced_icon,
        "target_matches": target_matches,
        "ready": bool(exists and (guarded or expected_launcher is None)),
        "path": str(primary_lnk),
        "desktop_dir": str(desktop),
        "legacy_exists": legacy_found is not None,
        "legacy_path": str(legacy_found) if legacy_found is not None else "",
    }


def create_game_shortcut(
    game_root: Path,
    shortcut_name: str = PRIMARY_GUARD_SHORTCUT_NAME,
    desktop_dir: Optional[Path] = None,
    *,
    launcher_exe: Optional[Path] = None,
    app_data_dir: Optional[Path] = None,
    resource_dir: Optional[Path] = None,
    icon_cache_dir: Optional[Path] = None,
    icon_location: Optional[str] = None,
) -> tuple[bool, str]:
    raw_str = str(game_root or "").strip()
    if not raw_str:
        return False, "Chưa xác định được thư mục cài đặt game."
    game_root = Path(raw_str).resolve()
    target_exe = game_root / "StellaSora.exe"
    if not target_exe.is_file():
        candidates = list(game_root.glob("**/StellaSora.exe"))
        if candidates:
            target_exe = candidates[0]
        else:
            return False, f"Không tìm thấy StellaSora.exe trong thư mục: {game_root}"

    resolved_icon = icon_location
    if not resolved_icon:
        persisted_ico = ensure_persistent_shortcut_icon(
            resource_dir=resource_dir,
            icon_cache_dir=icon_cache_dir or app_data_dir,
        )
        resolved_icon = f"{persisted_ico},0" if persisted_ico is not None else f"{target_exe},0"

    if launcher_exe is not None:
        lpath = Path(launcher_exe).resolve()
        if lpath.is_file():
            arg_str = "--launch-game"
            if app_data_dir is not None:
                arg_str += f' --app-data-dir "{Path(app_data_dir).resolve()}"'
            return create_desktop_shortcut(
                target_path=lpath,
                shortcut_name=shortcut_name,
                working_dir=lpath.parent,
                icon_location=resolved_icon,
                description="Chơi Stella Sora (Việt Hoá · Tự kiểm tra cập nhật an toàn)",
                desktop_dir=desktop_dir,
                arguments=arg_str,
            )

    return create_desktop_shortcut(
        target_path=target_exe,
        shortcut_name=shortcut_name,
        working_dir=target_exe.parent,
        icon_location=resolved_icon,
        description="Khởi động game Stella Sora Việt Hóa",
        desktop_dir=desktop_dir,
    )


def upgrade_existing_desktop_shortcuts(
    game_root: Path,
    *,
    desktop_dir: Optional[Path] = None,
    launcher_exe: Optional[Path] = None,
    app_data_dir: Optional[Path] = None,
    resource_dir: Optional[Path] = None,
    icon_cache_dir: Optional[Path] = None,
) -> bool:
    """Refresh persistent shortcut icon & upgrade existing Desktop shortcuts in-place on launcher startup."""
    ensure_persistent_shortcut_icon(
        resource_dir=resource_dir,
        icon_cache_dir=icon_cache_dir or app_data_dir,
    )
    status = check_guarded_shortcut_status(desktop_dir=desktop_dir, expected_launcher=launcher_exe)
    upgraded = False

    # Refresh primary "Chơi Stella VH.lnk" if missing synced icon, missing --launch-game, or pointing to an older exe
    if status["exists"] and (
        not status["has_synced_icon"]
        or (launcher_exe is not None and (not status["guarded"] or not status["target_matches"]))
    ):
        ok, _ = create_game_shortcut(
            game_root,
            shortcut_name=PRIMARY_GUARD_SHORTCUT_NAME,
            desktop_dir=desktop_dir,
            launcher_exe=launcher_exe,
            app_data_dir=app_data_dir,
            resource_dir=resource_dir,
            icon_cache_dir=icon_cache_dir,
        )
        upgraded = upgraded or ok

    # Also refresh legacy "Stella Sora Việt Hóa.lnk" icon & guard target if the user still keeps it on Desktop
    if status["legacy_exists"]:
        legacy_path = Path(status["legacy_path"])
        try:
            raw = legacy_path.read_bytes()
            need_legacy_upgrade = (
                not _lnk_contains_token(raw, "shortcut_vh_icon.ico")
                or (launcher_exe is not None and not _lnk_contains_token(raw, "--launch-game"))
                or (
                    launcher_exe is not None
                    and Path(launcher_exe).name
                    and not _lnk_contains_token(raw, Path(launcher_exe).name)
                )
            )
        except OSError:
            need_legacy_upgrade = False
        if need_legacy_upgrade:
            ok, _ = create_game_shortcut(
                game_root,
                shortcut_name=legacy_path.stem,
                desktop_dir=desktop_dir,
                launcher_exe=launcher_exe,
                app_data_dir=app_data_dir,
                resource_dir=resource_dir,
                icon_cache_dir=icon_cache_dir,
            )
            upgraded = upgraded or ok

    return upgraded
