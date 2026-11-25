"""Unicode-safe standalone update helper with Windows atomic rename fallback."""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from .safety import InstallerError, atomic_json, sha256_file

if TYPE_CHECKING:
    from .config import PathManager

SYNCHRONIZE = 0x00100000
PROCESS_QUERY_LIMITED_INFORMATION = 0x00001000
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
ERROR_INVALID_PARAMETER = 87
FORCE_CLOSE_WAIT_SECONDS = 3.0
RELAUNCH_SURVIVAL_SECONDS = 0.7


def cleanup_update_artifacts(directory: Path | str) -> None:
    """Safely cleans up stale unlocked temporary update binaries without touching *.preupdate.* backups."""
    try:
        p = Path(directory)
        if not p.is_dir():
            return
        for pattern in (".launcher_update_*.exe", ".launcher_restore_*.exe", "*.old_*"):
            for item in p.glob(pattern):
                try:
                    item.unlink(missing_ok=True)
                except OSError:
                    pass
        is_helper_dir = p.name.lower() == "update_helper"
        for item in p.glob("helper_*.exe"):
            if ".preupdate." in item.name.lower():
                continue
            if is_helper_dir or re.fullmatch(r"helper_[0-9a-f]{32}\.exe", item.name, re.I):
                try:
                    item.unlink(missing_ok=True)
                except OSError:
                    pass
    except OSError:
        pass


def cleanup_all_update_artifacts(pm: PathManager) -> None:
    """Best-effort cleanup of stale update artifacts across exe, v2 app_data, and legacy r02 helper dirs."""
    candidates: list[Path] = []
    try:
        candidates.append(Path(pm.exe_dir))
    except Exception:
        pass
    try:
        candidates.append(Path(pm.app_data_dir) / "update_helper")
    except Exception:
        pass
    try:
        if not getattr(pm, "is_custom_app_data", False):
            candidates.append(Path(pm.legacy_app_data_dir) / "update_helper")
    except Exception:
        pass
    for directory in candidates:
        try:
            cleanup_update_artifacts(directory)
        except Exception:
            pass


def _wait_parent(pid, deadline: float) -> None:
    """Waits for a single verified parent PID using a Win32 SYNCHRONIZE handle."""
    if not (isinstance(pid, int) and not isinstance(pid, bool) and 0 < pid <= 0xFFFFFFFF and pid != os.getpid()):
        raise InstallerError("PID tiến trình cha không hợp lệ.", "UPDATE_INVALID")

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        ctypes.set_last_error(0)
        handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if not handle:
            err = ctypes.get_last_error()
            if err == ERROR_INVALID_PARAMETER:
                return  # Process already exited
            raise InstallerError(f"Không thể mở handle chờ tiến trình cha (WinError {err}).", "UPDATE_TIMEOUT")

        try:
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            res = kernel32.WaitForSingleObject(handle, remaining_ms)
            if res == WAIT_OBJECT_0:
                return
            if res == WAIT_TIMEOUT:
                raise InstallerError("Launcher cũ chưa đóng sau thời hạn; giữ nguyên bản cũ.", "UPDATE_TIMEOUT")
            raise InstallerError(f"Lỗi chờ tiến trình cha kết thúc (mã {res}).", "UPDATE_TIMEOUT")
        finally:
            kernel32.CloseHandle(handle)
    else:
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            except PermissionError:
                pass
            time.sleep(0.1)
        raise InstallerError("Launcher cũ chưa đóng sau thời hạn; giữ nguyên bản cũ.", "UPDATE_TIMEOUT")


def _force_close_verified_launcher(pid: int, target: Path) -> bool:
    """Terminates pid ONLY after verifying its executable image path matches target.resolve()."""
    if not (isinstance(pid, int) and not isinstance(pid, bool) and 0 < pid <= 0xFFFFFFFF and pid != os.getpid()):
        return False
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
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

        ctypes.set_last_error(0)
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return ctypes.get_last_error() == ERROR_INVALID_PARAMETER

        image_path = None
        try:
            size = wintypes.DWORD(32768)
            buf = ctypes.create_unicode_buffer(size.value)
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                image_path = Path(buf.value).resolve()
        finally:
            kernel32.CloseHandle(handle)

        if image_path is None or image_path != Path(target).resolve():
            return False

        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )
        return True
    except Exception:
        return False


def apply_job(job_path: Path | str) -> None:
    job_path = Path(job_path)
    result_path: Path | None = (
        job_path.with_suffix(".result.json") if job_path.name and "\x00" not in str(job_path) else None
    )
    target: Path | None = None
    backup: Path | None = None
    tmp: Path | None = None
    old_target: Path | None = None
    expected_sha = ""
    preimage_sha = ""
    replaced = False

    try:
        try:
            j = json.loads(job_path.read_text(encoding="utf8"))
        except (OSError, ValueError) as exc:
            raise InstallerError("Tệp cấu hình tự cập nhật không hợp lệ.", "UPDATE_INVALID") from exc

        if not isinstance(j, dict):
            raise InstallerError("Cấu hình tự cập nhật phải là JSON object.", "UPDATE_INVALID")

        for req_key in ("source", "target", "sha256", "preimage_sha256"):
            val = j.get(req_key)
            if not isinstance(val, str) or not val.strip():
                raise InstallerError(f"Thiếu trường tự cập nhật hợp lệ: {req_key}.", "UPDATE_INVALID")

        raw_timeout = j.get("timeout", 60)
        if isinstance(raw_timeout, bool) or not isinstance(raw_timeout, (int, float)):
            raise InstallerError("Giá trị timeout tự cập nhật không hợp lệ.", "UPDATE_INVALID")
        timeout_val = float(raw_timeout)
        if not math.isfinite(timeout_val) or timeout_val <= 0:
            raise InstallerError("Giá trị timeout tự cập nhật không hợp lệ.", "UPDATE_INVALID")

        if "allow_force_close" in j:
            raw_afc = j["allow_force_close"]
            if not isinstance(raw_afc, bool):
                raise InstallerError("Giá trị allow_force_close tự cập nhật không hợp lệ.", "UPDATE_INVALID")
            allow_force_close = raw_afc
        else:
            allow_force_close = False

        raw_target = j["target"].strip()
        raw_source = j["source"].strip()
        if "\x00" in raw_target or "\x00" in raw_source:
            raise InstallerError("Đường dẫn tự cập nhật không hợp lệ.", "UPDATE_INVALID")

        try:
            target = Path(raw_target).resolve()
            source = Path(raw_source).resolve()
            if not target.name or not source.name:
                raise InstallerError("Đường dẫn tự cập nhật phải trỏ tới tệp.", "UPDATE_INVALID")
            backup = target.with_name(target.name + ".preupdate." + uuid.uuid4().hex)
            tmp = target.with_name(".launcher_update_" + uuid.uuid4().hex + ".exe")
            old_target = target.with_name(target.name + ".old_" + uuid.uuid4().hex)
        except InstallerError:
            raise
        except (OSError, ValueError, RuntimeError) as exc:
            raise InstallerError("Đường dẫn tự cập nhật không hợp lệ.", "UPDATE_INVALID") from exc

        expected_sha = j["sha256"].strip().lower()
        preimage_sha = j["preimage_sha256"].strip().lower()

        if target == Path(sys.executable).resolve() or target == source:
            raise InstallerError("Helper không được thay chính nó hoặc trùng tệp nguồn.", "UPDATE_INVALID")
        if (
            not source.is_file()
            or not target.is_file()
            or sha256_file(source) != expected_sha
            or sha256_file(target) != preimage_sha
        ):
            raise InstallerError("Nguồn hoặc launcher cũ đổi trước cập nhật.", "PREIMAGE_CONFLICT")

        start_ts = time.monotonic()
        deadline = start_ts + min(90.0, max(5.0, timeout_val))

        # Ignore legacy parent_pids list (must NEVER wait on or kill explorer.exe)
        parent_pid = j.get("parent_pid")
        if parent_pid is not None:
            wait_limit = min(deadline, start_ts + FORCE_CLOSE_WAIT_SECONDS) if allow_force_close else deadline
            try:
                _wait_parent(parent_pid, wait_limit)
            except InstallerError as wait_err:
                if wait_err.code == "UPDATE_TIMEOUT" and allow_force_close:
                    if _force_close_verified_launcher(parent_pid, target):
                        _wait_parent(parent_pid, deadline)
                    else:
                        raise
                else:
                    raise

        if (
            not source.is_file()
            or not target.is_file()
            or sha256_file(source) != expected_sha
            or sha256_file(target) != preimage_sha
        ):
            raise InstallerError("Launcher cũ đã thay đổi trong lúc chờ đóng.", "PREIMAGE_CONFLICT")

        shutil.copy2(target, backup)
        if sha256_file(backup) != preimage_sha:
            raise InstallerError("Backup launcher sai SHA256.", "BACKUP_CORRUPT")

        shutil.copyfile(source, tmp)
        if sha256_file(tmp) != expected_sha:
            raise InstallerError("Bản launcher tạm sai SHA256.", "HASH_MISMATCH")

        while True:
            if not target.is_file() or sha256_file(target) != preimage_sha:
                raise InstallerError("Launcher cũ đã thay đổi.", "PREIMAGE_CONFLICT")
            if not tmp.is_file() or sha256_file(tmp) != expected_sha:
                raise InstallerError("Bản launcher tạm sai SHA256.", "HASH_MISMATCH")
            try:
                os.replace(tmp, target)
                replaced = True
                break
            except PermissionError:
                now = time.monotonic()
                if now < deadline:
                    renamed = False
                    try:
                        target.rename(old_target)
                        renamed = True
                        os.replace(tmp, target)
                        replaced = True
                        break
                    except OSError:
                        if renamed and old_target.exists() and not target.exists():
                            try:
                                old_target.rename(target)
                            except OSError:
                                pass
                if now >= deadline:
                    raise InstallerError("Launcher chưa đóng sau thời hạn; giữ bản cũ.", "UPDATE_TIMEOUT")
                time.sleep(min(0.3, max(0.0, deadline - now)))

        if old_target.exists():
            try:
                old_target.unlink(missing_ok=True)
            except OSError:
                pass

        if not target.is_file() or sha256_file(target) != expected_sha:
            raise InstallerError("Đọc lại launcher mới sai hash.", "READBACK_MISMATCH")

        try:
            proc = subprocess.Popen([str(target)], cwd=str(target.parent))
        except OSError as exc:
            raise InstallerError("Launcher mới không khởi chạy được; đã phục hồi bản cũ.", "RELAUNCH_FAILED") from exc

        time.sleep(RELAUNCH_SURVIVAL_SECONDS)
        if proc.poll() not in (None, 0):
            raise InstallerError("Launcher mới thoát sớm; đã phục hồi bản cũ.", "RELAUNCH_FAILED")

        if result_path is not None:
            atomic_json(
                result_path,
                {
                    "status": "started",
                    "target": str(target),
                    "sha256": expected_sha,
                    "backup": str(backup),
                    "pid": proc.pid,
                },
            )
    except Exception as e:
        if replaced and target is not None and backup is not None:
            can_restore = (
                target.is_file()
                and sha256_file(target) == expected_sha
                and backup.is_file()
                and sha256_file(backup) == preimage_sha
            )
            if not can_restore:
                rec_err = InstallerError(
                    "Tệp launcher đã thay đổi ngoài dự kiến sau khi cập nhật; giữ nguyên cả hai bản để phục hồi thủ công.",
                    "UPDATE_RECOVERY_REQUIRED",
                )
                if result_path is not None:
                    atomic_json(
                        result_path,
                        {
                            "status": "recovery_required",
                            "code": "UPDATE_RECOVERY_REQUIRED",
                            "message": str(rec_err),
                            "backup": str(backup),
                            "target": str(target),
                        },
                    )
                raise rec_err from e

            restore_tmp = target.with_name(".launcher_restore_" + uuid.uuid4().hex + ".exe")
            restore_old: Path | None = None
            try:
                shutil.copy2(backup, restore_tmp)
                if sha256_file(restore_tmp) != preimage_sha:
                    raise OSError("Restore copy hash mismatch")
                for attempt in range(5):
                    try:
                        os.replace(restore_tmp, target)
                        break
                    except OSError as replace_err:
                        is_transient = isinstance(replace_err, PermissionError) or getattr(
                            replace_err, "winerror", None
                        ) in (5, 32, 33)
                        if not is_transient:
                            raise
                        if attempt < 4:
                            time.sleep(0.2)
                            continue
                        restore_old = target.with_name(target.name + ".old_" + uuid.uuid4().hex)
                        renamed_restore = False
                        try:
                            target.rename(restore_old)
                            renamed_restore = True
                            os.replace(restore_tmp, target)
                            break
                        except OSError:
                            if renamed_restore and restore_old.exists() and not target.exists():
                                try:
                                    restore_old.rename(target)
                                except OSError:
                                    pass
                            raise
            except OSError as restore_exc:
                rec_err = InstallerError(
                    "Không thể tự động phục hồi bản cũ; bản sao lưu được giữ nguyên.",
                    "UPDATE_RECOVERY_REQUIRED",
                )
                if result_path is not None:
                    atomic_json(
                        result_path,
                        {
                            "status": "recovery_required",
                            "code": "UPDATE_RECOVERY_REQUIRED",
                            "message": str(rec_err),
                            "backup": str(backup),
                            "target": str(target),
                        },
                    )
                raise rec_err from restore_exc
            finally:
                restore_tmp.unlink(missing_ok=True)
                if restore_old is not None and restore_old.exists():
                    try:
                        restore_old.unlink(missing_ok=True)
                    except OSError:
                        pass

        code = getattr(e, "code", "UPDATE_ERROR")
        if result_path is not None:
            atomic_json(
                result_path,
                {
                    "status": "error",
                    "code": code,
                    "message": str(e),
                    "backup": str(backup) if backup is not None and backup.exists() else "",
                },
            )
        raise
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
        if replaced and old_target is not None and old_target.exists():
            try:
                old_target.unlink(missing_ok=True)
            except OSError:
                pass


def schedule_update(source: Path | str, expected_sha: str, app_data: Path | str) -> Path:
    source = Path(source).resolve()
    expected = str(expected_sha).strip().lower()
    if not source.is_file() or sha256_file(source) != expected:
        raise InstallerError("Tệp update sai SHA256.", "HASH_MISMATCH")
    if not getattr(sys, "frozen", False):
        raise InstallerError("Tự cập nhật chỉ hỗ trợ bản launcher đóng gói.", "UPDATE_UNSUPPORTED")

    target = Path(sys.executable).resolve()
    cache = Path(app_data) / "update_helper"
    cache.mkdir(parents=True, exist_ok=True)
    helper = cache / ("helper_" + uuid.uuid4().hex + ".exe")
    shutil.copy2(source, helper)
    if sha256_file(helper) != expected:
        helper.unlink(missing_ok=True)
        raise InstallerError("Bản helper tự cập nhật sai SHA256.", "HASH_MISMATCH")

    job = cache / (uuid.uuid4().hex + ".json")
    atomic_json(
        job,
        {
            "source": str(source),
            "target": str(target),
            "sha256": expected,
            "preimage_sha256": sha256_file(target),
            "timeout": 60,
            "parent_pid": os.getpid(),
            "allow_force_close": True,
        },
    )
    subprocess.Popen(
        [str(helper), "--apply-update", str(job)],
        cwd=str(cache),
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    return job
