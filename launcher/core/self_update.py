"""Unicode-safe standalone update helper; no shell or command interpolation."""
from __future__ import annotations
import json,os,shutil,subprocess,sys,time,uuid
from pathlib import Path
from .safety import InstallerError,sha256_file,atomic_json

def apply_job(job_path):
    job_path=Path(job_path);j=json.loads(job_path.read_text(encoding='utf8'))
    target=Path(j['target']).resolve();source=Path(j['source']).resolve();backup=target.with_name(target.name+'.preupdate.'+uuid.uuid4().hex)
    if target==Path(sys.executable).resolve():raise InstallerError('Helper không được thay chính nó.','UPDATE_INVALID')
    if sha256_file(source)!=j['sha256'] or sha256_file(target)!=j['preimage_sha256']:raise InstallerError('Nguồn hoặc launcher cũ đổi trước cập nhật.','PREIMAGE_CONFLICT')
    deadline=time.monotonic()+min(30,max(1,float(j.get('timeout',25))))
    shutil.copy2(target,backup)
    if sha256_file(backup)!=j['preimage_sha256']:raise InstallerError('Backup launcher sai SHA256.','BACKUP_CORRUPT')
    tmp=target.with_name('.launcher_update_'+uuid.uuid4().hex+'.exe');shutil.copy2(source,tmp)
    if sha256_file(tmp)!=j['sha256']:raise InstallerError('Bản launcher tạm sai SHA256.','HASH_MISMATCH')
    try:
        while True:
            if sha256_file(target)!=j['preimage_sha256']:raise InstallerError('Launcher cũ đã thay đổi.','PREIMAGE_CONFLICT')
            try:os.replace(tmp,target);break
            except PermissionError:
                if time.monotonic()>=deadline:raise InstallerError('Launcher chưa đóng sau thời hạn; giữ bản cũ.','UPDATE_TIMEOUT')
                time.sleep(.2)
        if sha256_file(target)!=j['sha256']:raise InstallerError('Đọc lại launcher mới sai hash.','READBACK_MISMATCH')
        try:proc=subprocess.Popen([str(target)],cwd=str(target.parent));time.sleep(.7)
        except Exception:shutil.copy2(backup,target);raise
        if proc.poll() not in (None,0):shutil.copy2(backup,target);raise InstallerError('Launcher mới không khởi chạy được; đã phục hồi bản cũ.','RELAUNCH_FAILED')
        atomic_json(job_path.with_suffix('.result.json'),{'status':'started','target':str(target),'sha256':j['sha256'],'backup':str(backup),'pid':proc.pid})
    except Exception as e:
        # Preserve the backup; restore only our replacement, never an unrelated changed EXE.
        try:
            if target.is_file() and sha256_file(target)==j['sha256'] and sha256_file(backup)==j['preimage_sha256']:
                shutil.copy2(backup,target)
        except OSError:pass
        atomic_json(job_path.with_suffix('.result.json'),{'status':'error','message':str(e),'backup':str(backup)});raise
    finally:tmp.unlink(missing_ok=True)

def schedule_update(source,expected_sha,app_data):
    if not getattr(sys,'frozen',False):raise InstallerError('Tự cập nhật chỉ dành cho EXE đóng gói.','UPDATE_UNAVAILABLE')
    source=Path(source).resolve();target=Path(sys.executable).resolve()
    if sha256_file(source)!=expected_sha:raise InstallerError('Tệp update sai SHA256.','HASH_MISMATCH')
    cache=Path(app_data)/'update_helper';cache.mkdir(parents=True,exist_ok=True);helper=cache/('helper_'+uuid.uuid4().hex+'.exe');shutil.copy2(target,helper)
    job=cache/(uuid.uuid4().hex+'.json');atomic_json(job,{'source':str(source),'target':str(target),'sha256':expected_sha,'preimage_sha256':sha256_file(target),'timeout':25})
    subprocess.Popen([str(helper),'--apply-update',str(job)],cwd=str(cache),creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    return job
