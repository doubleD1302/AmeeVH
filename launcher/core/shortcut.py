import os
import sys
import tempfile
import subprocess
import winreg
from pathlib import Path

def get_desktop_path() -> Path:
    """Returns the true Windows Desktop directory, resolving OneDrive/localized folders."""
    if os.name == 'nt':
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
                val, _ = winreg.QueryValueEx(key, "Desktop")
                p = Path(os.path.expandvars(val))
                if p.is_dir():
                    return p
        except Exception:
            pass
        user_profile = os.environ.get('USERPROFILE')
        if user_profile:
            p = Path(user_profile) / 'Desktop'
            if p.is_dir():
                return p
    return Path.home() / 'Desktop'

def create_desktop_shortcut(
    target_path: Path,
    shortcut_name: str,
    working_dir: Path = None,
    icon_location: str = None,
    description: str = "Stella Sora Việt Hóa"
) -> tuple[bool, str]:
    """Creates a Windows .lnk desktop shortcut using native WScript.Shell without external dependencies."""
    target_path = Path(target_path).resolve()
    if not target_path.exists():
        return False, f"Không tìm thấy tệp đích: {target_path}"

    desktop = get_desktop_path()
    if not desktop.is_dir():
        try:
            desktop.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"Không thể tạo thư mục màn hình chính: {e}"

    clean_name = shortcut_name.strip()
    if not clean_name.lower().endswith(".lnk"):
        clean_name += ".lnk"
    lnk_path = desktop / clean_name

    work_dir = Path(working_dir).resolve() if working_dir else target_path.parent
    icon = str(icon_location) if icon_location else f"{target_path},0"

    vbs_content = (
        'Set ws = CreateObject("WScript.Shell")\n'
        f'Set s = ws.CreateShortcut("{str(lnk_path)}")\n'
        f's.TargetPath = "{str(target_path)}"\n'
        f's.WorkingDirectory = "{str(work_dir)}"\n'
        f's.IconLocation = "{icon}"\n'
        f's.Description = "{description}"\n'
        's.Save\n'
    )

    vbs_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vbs', delete=False, encoding='utf-8') as f:
            f.write(vbs_content)
            vbs_path = f.name

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        res = subprocess.run(
            ["cscript.exe", "//nologo", vbs_path],
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            timeout=10
        )
        if res.returncode == 0 and lnk_path.is_file():
            return True, f"Đã tạo lối tắt thành công tại {lnk_path}"
        else:
            err = res.stderr.strip() or res.stdout.strip() or f"Mã thoát {res.returncode}"
            return False, f"Lỗi tạo lối tắt: {err}"
    except Exception as e:
        return False, f"Lỗi tạo lối tắt: {e}"
    finally:
        if vbs_path and os.path.exists(vbs_path):
            try:
                os.unlink(vbs_path)
            except Exception:
                pass

def create_game_shortcut(game_root: Path, shortcut_name: str = "Stella Sora Việt Hóa") -> tuple[bool, str]:
    game_root = Path(game_root).resolve()
    target_exe = game_root / "StellaSora.exe"
    if not target_exe.is_file():
        # Check subdirectories if any
        candidates = list(game_root.glob("**/StellaSora.exe"))
        if candidates:
            target_exe = candidates[0]
        else:
            return False, f"Không tìm thấy StellaSora.exe trong thư mục: {game_root}"

    return create_desktop_shortcut(
        target_path=target_exe,
        shortcut_name=shortcut_name,
        working_dir=target_exe.parent,
        icon_location=f"{target_exe},0",
        description="Khởi động game Stella Sora Việt Hóa"
    )

if __name__ == "__main__":
    steam_root = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora")
    ok, msg = create_game_shortcut(steam_root, "Stella Sora Test LNK")
    print("Result:", ok, msg)
    desktop = get_desktop_path()
    test_file = desktop / "Stella Sora Test LNK.lnk"
    print("File exists:", test_file.exists())
    if test_file.exists():
        test_file.unlink()
        print("Test file deleted successfully.")
