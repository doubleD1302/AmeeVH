"""Unicode-safe standalone update helper with Windows atomic rename fallback."""
from __future__ import annotations
import json, os, shutil, subprocess, sys, time, uuid
from pathlib import Path
from .safety import InstallerError, sha256_file, atomic_json

def cleanup_update_artifacts(directory: Path):
    """Keep recovery artifacts: only the job that created a temp may remove it."""
    return None


def _wait_parent(pid, deadline):
    """Wait for the one launcher PID in the job; never terminate a process."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0 or pid == os.getpid():
        raise InstallerError('Không xác định được tiến trình launcher cần chờ.', 'UPDATE_INVALID')
    if os.name != 'nt':
        raise InstallerError('Chỉ hỗ trợ cập nhật launcher trên Windows.', 'UPDATE_UNSUPPORTED')
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE only
    if not handle:
        if ctypes.get_last_error() == 87:  # PID already exited
            return
        raise InstallerError('Không thể xác nhận launcher cũ đã đóng.', 'UPDATE_PARENT_UNKNOWN')
    try:
        remaining = max(0, int((deadline - time.monotonic()) * 1000))
        status = kernel.WaitForSingleObject(handle, remaining)
        if status == 0:
            return
        if status == 258:
            raise InstallerError('Launcher cũ chưa đóng sau thời hạn; giữ nguyên bản cũ.', 'UPDATE_TIMEOUT')
        raise InstallerError('Không thể xác nhận launcher cũ đã đóng.', 'UPDATE_PARENT_UNKNOWN')
    finally:
        kernel.CloseHandle(handle)


def apply_job(job_path):
    """Apply old and new jobs with guarded atomic replacement and recovery."""
    job_path = Path(job_path)
    j = json.loads(job_path.read_text(encoding='utf8'))
    target = Path(j['target']).resolve()
    source = Path(j['source']).resolve()
    result_path = job_path.with_suffix('.result.json')
    backup = target.with_name(target.name + '.preupdate.' + uuid.uuid4().hex)
    tmp = target.with_name('.launcher_update_' + uuid.uuid4().hex + '.exe')
    restore_tmp = target.with_name('.launcher_restore_' + uuid.uuid4().hex + '.exe')
    replaced = False
    try:
        if target == Path(sys.executable).resolve() or target == source:
            raise InstallerError('Helper không được thay chính nó hoặc nguồn cập nhật.', 'UPDATE_INVALID')
        if sha256_file(source) != j['sha256'] or sha256_file(target) != j['preimage_sha256']:
            raise InstallerError('Nguồn hoặc launcher cũ đổi trước cập nhật.', 'PREIMAGE_CONFLICT')
        deadline = time.monotonic() + min(35, max(5, float(j.get('timeout', 30))))
        # Legacy jobs may contain parent_pids with unrelated processes. Ignore it.
        _wait_parent(j.get('parent_pid'), deadline)
        if sha256_file(source) != j['sha256'] or sha256_file(target) != j['preimage_sha256']:
            raise InstallerError('Nguồn hoặc launcher cũ đổi trong lúc chờ.', 'PREIMAGE_CONFLICT')
        shutil.copy2(target, backup)
        if sha256_file(backup) != j['preimage_sha256']:
            raise InstallerError('Backup launcher sai SHA256.', 'BACKUP_CORRUPT')
        shutil.copyfile(source, tmp)
        if sha256_file(tmp) != j['sha256']:
            raise InstallerError('Bản launcher tạm sai SHA256.', 'HASH_MISMATCH')
        while True:
            if not target.is_file() or sha256_file(target) != j['preimage_sha256']:
                raise InstallerError('Launcher cũ đã thay đổi.', 'PREIMAGE_CONFLICT')
            if sha256_file(tmp) != j['sha256']:
                raise InstallerError('Bản launcher tạm đã thay đổi.', 'HASH_MISMATCH')
            try:
                os.replace(tmp, target)
                replaced = True
                break
            except PermissionError:
                if time.monotonic() >= deadline:
                    raise InstallerError('Không thể thay launcher sau thời hạn; giữ bản cũ.', 'UPDATE_TIMEOUT')
                time.sleep(min(0.3, max(0, deadline-time.monotonic())))
        if sha256_file(target) != j['sha256']:
            raise InstallerError('Đọc lại launcher mới sai hash.', 'READBACK_MISMATCH')
        try:
            proc = subprocess.Popen([str(target)], cwd=str(target.parent))
            time.sleep(0.7)
            if proc.poll() not in (None, 0):
                raise InstallerError('Launcher mới thoát khi khởi động.', 'RELAUNCH_FAILED')
        except Exception as e:
            if isinstance(e, InstallerError): raise
            raise InstallerError('Không mở được launcher mới: '+str(e), 'RELAUNCH_FAILED') from e
        atomic_json(result_path, {'status':'started', 'target':str(target), 'sha256':j['sha256'], 'backup':str(backup), 'pid':proc.pid})
    except Exception as e:
        recovery_error = None
        if replaced:
            try:
                if not target.is_file() or sha256_file(target) != j['sha256']:
                    raise InstallerError('Launcher đích đã đổi; không ghi đè.', 'PREIMAGE_CONFLICT')
                if not backup.is_file() or sha256_file(backup) != j['preimage_sha256']:
                    raise InstallerError('Backup thiếu hoặc sai hash.', 'BACKUP_CORRUPT')
                shutil.copyfile(backup, restore_tmp)
                if sha256_file(restore_tmp) != j['preimage_sha256']:
                    raise InstallerError('Bản tạm phục hồi sai hash.', 'BACKUP_CORRUPT')
                if sha256_file(target) != j['sha256']:
                    raise InstallerError('Launcher đích đã đổi trong lúc phục hồi.', 'PREIMAGE_CONFLICT')
                os.replace(restore_tmp, target)
                if sha256_file(target) != j['preimage_sha256']:
                    raise InstallerError('Đọc lại bản phục hồi sai hash.', 'READBACK_MISMATCH')
            except Exception as recovery:
                recovery_error = str(recovery)
        code = 'UPDATE_RECOVERY_REQUIRED' if recovery_error else getattr(e, 'code', 'UPDATE_FAILED')
        message = str(e) + ((' Không thể tự phục hồi; giữ backup. '+recovery_error) if recovery_error else '')
        atomic_json(result_path, {'status':'recovery_required' if recovery_error else 'error', 'code':code, 'message':message, 'backup':str(backup) if backup.exists() else None})
        if recovery_error:
            raise InstallerError(message, code) from e
        raise
    finally:
        for path in (tmp, restore_tmp):
            try: path.unlink(missing_ok=True)
            except OSError: pass

def schedule_update(source, expected_sha, app_data):
    source = Path(source).resolve()
    if sha256_file(source) != expected_sha:
        raise InstallerError('Tệp update sai SHA256.', 'HASH_MISMATCH')
    if not getattr(sys, 'frozen', False):
        raise InstallerError('Tự cập nhật chỉ hỗ trợ bản launcher đóng gói.', 'UPDATE_UNSUPPORTED')
    target = Path(sys.executable).resolve()
    cache = Path(app_data) / 'update_helper'
    cache.mkdir(parents=True, exist_ok=True)
    helper = cache / ('helper_' + uuid.uuid4().hex + '.exe')
    # Only the verified new binary has this safe helper. Never fall back to
    # an older executable whose helper may forcibly terminate processes.
    shutil.copy2(source, helper)
    if sha256_file(helper) != expected_sha:
        helper.unlink(missing_ok=True)
        raise InstallerError('Helper cập nhật sai SHA256.', 'HASH_MISMATCH')
    job = cache / (uuid.uuid4().hex + '.json')
    atomic_json(job, {
        'source': str(source),
        'target': str(target),
        'sha256': expected_sha,
        'preimage_sha256': sha256_file(target),
        'timeout': 30,
        'parent_pid': os.getpid()
    })
    subprocess.Popen([str(helper), '--apply-update', str(job)], cwd=str(cache), creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    return job
