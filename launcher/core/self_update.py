"""Unicode-safe standalone update helper with Windows atomic rename fallback."""
from __future__ import annotations
import json, os, shutil, subprocess, sys, time, uuid
from pathlib import Path
from .safety import InstallerError, sha256_file, atomic_json

SYNCHRONIZE = 0x00100000
PROCESS_QUERY_LIMITED_INFORMATION = 0x00001000
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
ERROR_INVALID_PARAMETER = 87


def cleanup_update_artifacts(directory: Path):
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
    except OSError:
        pass


def _wait_parent(pid, deadline: float):
    """Waits for a single verified parent PID using a Win32 SYNCHRONIZE handle."""
    if not (isinstance(pid, int) and not isinstance(pid, bool) and pid > 0 and pid != os.getpid()):
        raise InstallerError('PID tiến trình cha không hợp lệ.', 'UPDATE_INVALID')

    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
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
            raise InstallerError(f'Không thể mở handle chờ tiến trình cha (WinError {err}).', 'UPDATE_TIMEOUT')

        try:
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            res = kernel32.WaitForSingleObject(handle, remaining_ms)
            if res == WAIT_OBJECT_0:
                return
            if res == WAIT_TIMEOUT:
                raise InstallerError('Launcher cũ chưa đóng sau thời hạn; giữ nguyên bản cũ.', 'UPDATE_TIMEOUT')
            raise InstallerError(f'Lỗi chờ tiến trình cha kết thúc (mã {res}).', 'UPDATE_TIMEOUT')
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
        raise InstallerError('Launcher cũ chưa đóng sau thời hạn; giữ nguyên bản cũ.', 'UPDATE_TIMEOUT')


def _force_close_verified_launcher(pid: int, target: Path) -> bool:
    """Terminates pid ONLY after verifying its executable image path matches target.resolve()."""
    if not (isinstance(pid, int) and not isinstance(pid, bool) and pid > 0 and pid != os.getpid()):
        return False
    if os.name != 'nt':
        return False
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
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
            ['taskkill', '/F', '/PID', str(pid)],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,
        )
        return True
    except Exception:
        return False


def apply_job(job_path):
    job_path = Path(job_path)
    j = json.loads(job_path.read_text(encoding='utf8'))
    target = Path(j['target']).resolve()
    source = Path(j['source']).resolve()
    backup = target.with_name(target.name + '.preupdate.' + uuid.uuid4().hex)
    tmp = target.with_name('.launcher_update_' + uuid.uuid4().hex + '.exe')
    old_target = target.with_name(target.name + '.old_' + uuid.uuid4().hex)
    replaced = False

    try:
        if target == Path(sys.executable).resolve() or target == source:
            raise InstallerError('Helper không được thay chính nó hoặc trùng tệp nguồn.', 'UPDATE_INVALID')
        if (
            not source.is_file()
            or not target.is_file()
            or sha256_file(source) != j['sha256']
            or sha256_file(target) != j['preimage_sha256']
        ):
            raise InstallerError('Nguồn hoặc launcher cũ đổi trước cập nhật.', 'PREIMAGE_CONFLICT')

        start_ts = time.monotonic()
        deadline = start_ts + min(90.0, max(5.0, float(j.get('timeout', 60))))

        # Ignore legacy parent_pids list (must NEVER wait on or kill explorer.exe)
        parent_pid = j.get('parent_pid')
        allow_force_close = bool(j.get('allow_force_close', False))
        if parent_pid is not None:
            wait_limit = min(deadline, start_ts + 3.0) if allow_force_close else deadline
            try:
                _wait_parent(parent_pid, wait_limit)
            except InstallerError as wait_err:
                if wait_err.code == 'UPDATE_TIMEOUT' and allow_force_close:
                    if _force_close_verified_launcher(parent_pid, target):
                        _wait_parent(parent_pid, deadline)
                    else:
                        raise
                else:
                    raise

        if (
            not source.is_file()
            or not target.is_file()
            or sha256_file(source) != j['sha256']
            or sha256_file(target) != j['preimage_sha256']
        ):
            raise InstallerError('Launcher cũ đã thay đổi trong lúc chờ đóng.', 'PREIMAGE_CONFLICT')

        shutil.copy2(target, backup)
        if sha256_file(backup) != j['preimage_sha256']:
            raise InstallerError('Backup launcher sai SHA256.', 'BACKUP_CORRUPT')

        shutil.copyfile(source, tmp)
        if sha256_file(tmp) != j['sha256']:
            raise InstallerError('Bản launcher tạm sai SHA256.', 'HASH_MISMATCH')

        while True:
            if not target.is_file() or sha256_file(target) != j['preimage_sha256']:
                raise InstallerError('Launcher cũ đã thay đổi.', 'PREIMAGE_CONFLICT')
            if not tmp.is_file() or sha256_file(tmp) != j['sha256']:
                raise InstallerError('Bản launcher tạm sai SHA256.', 'HASH_MISMATCH')
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
                    raise InstallerError('Launcher chưa đóng sau thời hạn; giữ bản cũ.', 'UPDATE_TIMEOUT')
                time.sleep(min(0.3, max(0.0, deadline - now)))

        if old_target.exists():
            try:
                old_target.unlink(missing_ok=True)
            except OSError:
                pass

        if not target.is_file() or sha256_file(target) != j['sha256']:
            raise InstallerError('Đọc lại launcher mới sai hash.', 'READBACK_MISMATCH')

        try:
            proc = subprocess.Popen([str(target)], cwd=str(target.parent))
        except OSError as exc:
            raise InstallerError('Launcher mới không khởi chạy được; đã phục hồi bản cũ.', 'RELAUNCH_FAILED') from exc

        time.sleep(0.7)
        if proc.poll() not in (None, 0):
            raise InstallerError('Launcher mới thoát sớm; đã phục hồi bản cũ.', 'RELAUNCH_FAILED')

        atomic_json(job_path.with_suffix('.result.json'), {
            'status': 'started',
            'target': str(target),
            'sha256': j['sha256'],
            'backup': str(backup),
            'pid': proc.pid,
        })
    except Exception as e:
        if replaced:
            can_restore = (
                target.is_file()
                and sha256_file(target) == j['sha256']
                and backup.is_file()
                and sha256_file(backup) == j['preimage_sha256']
            )
            if not can_restore:
                rec_err = InstallerError(
                    'Tệp launcher đã thay đổi ngoài dự kiến sau khi cập nhật; giữ nguyên cả hai bản để phục hồi thủ công.',
                    'UPDATE_RECOVERY_REQUIRED',
                )
                atomic_json(job_path.with_suffix('.result.json'), {
                    'status': 'recovery_required',
                    'code': 'UPDATE_RECOVERY_REQUIRED',
                    'message': str(rec_err),
                    'backup': str(backup),
                    'target': str(target),
                })
                raise rec_err from e

            restore_tmp = target.with_name('.launcher_restore_' + uuid.uuid4().hex + '.exe')
            try:
                shutil.copy2(backup, restore_tmp)
                if sha256_file(restore_tmp) != j['preimage_sha256']:
                    raise OSError('Restore copy hash mismatch')
                os.replace(restore_tmp, target)
            except OSError as restore_exc:
                rec_err = InstallerError(
                    'Không thể tự động phục hồi bản cũ; bản sao lưu được giữ nguyên.',
                    'UPDATE_RECOVERY_REQUIRED',
                )
                atomic_json(job_path.with_suffix('.result.json'), {
                    'status': 'recovery_required',
                    'code': 'UPDATE_RECOVERY_REQUIRED',
                    'message': str(rec_err),
                    'backup': str(backup),
                    'target': str(target),
                })
                raise rec_err from restore_exc
            finally:
                restore_tmp.unlink(missing_ok=True)

        code = getattr(e, 'code', 'UPDATE_ERROR')
        atomic_json(job_path.with_suffix('.result.json'), {
            'status': 'error',
            'code': code,
            'message': str(e),
            'backup': str(backup) if backup.exists() else '',
        })
        raise
    finally:
        tmp.unlink(missing_ok=True)
        if replaced and old_target.exists():
            try:
                old_target.unlink(missing_ok=True)
            except OSError:
                pass


def schedule_update(source, expected_sha, app_data):
    source = Path(source).resolve()
    expected = str(expected_sha).lower()
    if not source.is_file() or sha256_file(source) != expected:
        raise InstallerError('Tệp update sai SHA256.', 'HASH_MISMATCH')
    if not getattr(sys, 'frozen', False):
        raise InstallerError('Tự cập nhật chỉ hỗ trợ bản launcher đóng gói.', 'UPDATE_UNSUPPORTED')

    target = Path(sys.executable).resolve()
    cache = Path(app_data) / 'update_helper'
    cache.mkdir(parents=True, exist_ok=True)
    helper = cache / ('helper_' + uuid.uuid4().hex + '.exe')
    shutil.copy2(source, helper)
    if sha256_file(helper) != expected:
        helper.unlink(missing_ok=True)
        raise InstallerError('Bản helper tự cập nhật sai SHA256.', 'HASH_MISMATCH')

    job = cache / (uuid.uuid4().hex + '.json')
    atomic_json(job, {
        'source': str(source),
        'target': str(target),
        'sha256': expected,
        'preimage_sha256': sha256_file(target),
        'timeout': 60,
        'parent_pid': os.getpid(),
        'allow_force_close': True,
    })
    subprocess.Popen(
        [str(helper), '--apply-update', str(job)],
        cwd=str(cache),
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
    )
    return job
