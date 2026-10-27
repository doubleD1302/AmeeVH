"""Unicode-safe standalone update helper with Windows atomic rename fallback."""
from __future__ import annotations
import json, os, shutil, subprocess, sys, time, uuid
from pathlib import Path
from .safety import InstallerError, sha256_file, atomic_json

def cleanup_update_artifacts(directory: Path):
    """Safely cleans up stale update artifacts and temporary binaries."""
    try:
        p = Path(directory)
        if not p.is_dir():
            return
        for item in p.glob(".launcher_update_*.exe"):
            try: item.unlink(missing_ok=True)
            except OSError: pass
        for item in p.glob("*.old_*"):
            try: item.unlink(missing_ok=True)
            except OSError: pass
        for item in p.glob("*.preupdate.*"):
            try: item.unlink(missing_ok=True)
            except OSError: pass
    except OSError:
        pass

def apply_job(job_path):
    job_path = Path(job_path)
    j = json.loads(job_path.read_text(encoding='utf8'))
    target = Path(j['target']).resolve()
    source = Path(j['source']).resolve()
    backup = target.with_name(target.name + '.preupdate.' + uuid.uuid4().hex)
    parent_pid = j.get('parent_pid')

    if target == Path(sys.executable).resolve():
        raise InstallerError('Helper không được thay chính nó.', 'UPDATE_INVALID')
    if sha256_file(source) != j['sha256'] or sha256_file(target) != j['preimage_sha256']:
        raise InstallerError('Nguồn hoặc launcher cũ đổi trước cập nhật.', 'PREIMAGE_CONFLICT')

    deadline = time.monotonic() + min(35, max(5, float(j.get('timeout', 30))))
    shutil.copy2(target, backup)
    if sha256_file(backup) != j['preimage_sha256']:
        raise InstallerError('Backup launcher sai SHA256.', 'BACKUP_CORRUPT')

    tmp = target.with_name('.launcher_update_' + uuid.uuid4().hex + '.exe')
    shutil.copy2(source, tmp)
    if sha256_file(tmp) != j['sha256']:
        raise InstallerError('Bản launcher tạm sai SHA256.', 'HASH_MISMATCH')

    # Gracefully wait for the launcher parent process to exit
    if parent_pid:
        start_wait = time.monotonic()
        while time.monotonic() - start_wait < 4.0:
            try:
                out = subprocess.check_output(f'tasklist /FI "PID eq {parent_pid}" /NH', shell=True, text=True)
                if str(parent_pid) not in out:
                    break
            except Exception:
                break
            time.sleep(0.3)
        # Terminate parent if still running after wait
        try:
            subprocess.run(f'taskkill /F /PID {parent_pid}', shell=True, capture_output=True)
        except Exception:
            pass

    old_target = target.with_name(target.name + '.old_' + uuid.uuid4().hex)
    try:
        while True:
            if target.exists() and sha256_file(target) != j['preimage_sha256']:
                raise InstallerError('Launcher cũ đã thay đổi.', 'PREIMAGE_CONFLICT')
            try:
                # Direct replacement attempt
                os.replace(tmp, target)
                break
            except PermissionError:
                # Fallback for Windows file lock: rename running target, then move new exe in
                try:
                    if target.exists():
                        target.rename(old_target)
                    os.replace(tmp, target)
                    break
                except Exception:
                    pass
                if time.monotonic() >= deadline:
                    raise InstallerError('Launcher chưa đóng sau thời hạn; giữ bản cũ.', 'UPDATE_TIMEOUT')
                time.sleep(0.3)

        # Cleanup old target file if possible
        if old_target.exists():
            try: old_target.unlink(missing_ok=True)
            except OSError: pass

        if sha256_file(target) != j['sha256']:
            raise InstallerError('Đọc lại launcher mới sai hash.', 'READBACK_MISMATCH')

        try:
            proc = subprocess.Popen([str(target)], cwd=str(target.parent))
            time.sleep(0.7)
        except Exception:
            shutil.copy2(backup, target)
            raise

        if proc.poll() not in (None, 0):
            shutil.copy2(backup, target)
            raise InstallerError('Launcher mới không khởi chạy được; đã phục hồi bản cũ.', 'RELAUNCH_FAILED')

        atomic_json(job_path.with_suffix('.result.json'), {
            'status': 'started',
            'target': str(target),
            'sha256': j['sha256'],
            'backup': str(backup),
            'pid': proc.pid
        })
    except Exception as e:
        try:
            if target.is_file() and sha256_file(target) == j['sha256'] and sha256_file(backup) == j['preimage_sha256']:
                shutil.copy2(backup, target)
            elif not target.exists() and old_target.exists():
                old_target.rename(target)
        except OSError:
            pass
        atomic_json(job_path.with_suffix('.result.json'), {'status': 'error', 'message': str(e), 'backup': str(backup)})
        raise
    finally:
        tmp.unlink(missing_ok=True)
        if old_target.exists():
            try: old_target.unlink(missing_ok=True)
            except OSError: pass

def schedule_update(source, expected_sha, app_data):
    source = Path(source).resolve()
    if sha256_file(source) != expected_sha:
        raise InstallerError('Tệp update sai SHA256.', 'HASH_MISMATCH')
    if not getattr(sys, 'frozen', False):
        game_root = Path(__file__).resolve().parent.parent.parent.parent
        for p in (game_root / 'StellaSora_Launcher.exe', game_root / 'StellaSora_VietHoa' / 'dist' / 'StellaSora_Launcher.exe'):
            if p.is_file():
                try: shutil.copy2(source, p)
                except OSError: pass
        return None
    target = Path(sys.executable).resolve()
    cache = Path(app_data) / 'update_helper'
    cache.mkdir(parents=True, exist_ok=True)
    helper = cache / ('helper_' + uuid.uuid4().hex + '.exe')
    try: shutil.copy2(source, helper)
    except Exception: shutil.copy2(target, helper)
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
