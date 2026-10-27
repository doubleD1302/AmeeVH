"""Manifest-bound transaction with preimages, atomic journal and restart recovery."""
from __future__ import annotations
import contextlib,json,os,shutil,uuid
from datetime import datetime,timezone
from pathlib import Path
from .game_detection import canonicalize_path,is_game_process_running,read_game_versions
from .types import OperationEvent,OperationPhase
from .safety import InstallerError,sha256_file,safe_path,normalize_manifest,atomic_json
RECEIPT='.vietnamese_patch_receipt.json'

def state(path):
    return {'exists':True,'sha256':sha256_file(path),'size':path.stat().st_size} if path.is_file() else {'exists':False}

def same(path,expected):
    if expected.get('exists',True):return path.is_file() and path.stat().st_size==expected['size'] and sha256_file(path)==expected['sha256']
    return not path.exists()

class PatchInstaller:
    def __init__(self,backup_root,journals_dir):
        self.backup_root=Path(backup_root);self.journals_dir=Path(journals_dir)
        for p in (self.backup_root,self.journals_dir):p.mkdir(parents=True,exist_ok=True)
    def _validate_path_security(self,game_root,rel_path):return safe_path(game_root,rel_path,True)
    def get_backup_dir_for_root(self,root):
        import hashlib
        p=self.backup_root/('game_'+hashlib.sha256(canonicalize_path(root).encode('utf8')).hexdigest()[:12]);p.mkdir(parents=True,exist_ok=True);return p
    @contextlib.contextmanager
    def _lock(self,root):
        import msvcrt
        p=self.get_backup_dir_for_root(root)/'.operation.lock'
        with p.open('a+b') as f:
            if not f.tell():f.write(b'0');f.flush()
            f.seek(0)
            try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
            except OSError:raise InstallerError('Một thao tác khác đang dùng thư mục game này.','OPERATION_BUSY')
            try:yield
            finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
    def _preflight(self,root):
        if not root.is_dir() or not (root/'StellaSora.exe').is_file():raise InstallerError('Hãy chọn đúng thư mục có StellaSora.exe.','INVALID_ROOT')
        if is_game_process_running():raise InstallerError('Hãy đóng game trước khi thay đổi tài nguyên.','GAME_RUNNING')
    def _emit(self,cb,op,phase,msg,n=0,total=0,receipt=None):
        if cb:cb(OperationEvent(op,phase,msg,n,total,receipt=receipt))
    def pending(self,root):
        out=[]
        for p in self.journals_dir.glob('*.json'):
            try:
                d=json.loads(p.read_text(encoding='utf8'))
                if d.get('game_root')==canonicalize_path(root) and d.get('state') not in ('done','rolled_back','restored'):out.append((p,d))
            except (OSError,ValueError):raise InstallerError('Nhật ký bị hỏng; giữ nguyên và kiểm tra thư mục chẩn đoán.','JOURNAL_CORRUPT')
        return out
    def _restore_journal(self,root,jfile,j):
        if j['game_root']!=canonicalize_path(root):raise InstallerError('Nhật ký không thuộc thư mục game này.','ROOT_MISMATCH')
        backup=Path(j['backup_dir']).resolve()
        try:backup.relative_to(self.get_backup_dir_for_root(root).resolve())
        except ValueError:raise InstallerError('Backup ngoài vùng gắn với game.','BACKUP_INVALID')
        # Check every backup and current preimage before the first restoring write.
        for rel,item in j['files'].items():
            target=safe_path(root,rel,True);old=item['before'];new=item['after']
            if not same(target,old) and not same(target,new):raise InstallerError('Tệp đã đổi sau thao tác; không ghi đè: '+rel,'PREIMAGE_CONFLICT')
            if old['exists'] and not same(safe_path(backup,rel),old):raise InstallerError('Backup thiếu/hỏng: '+rel,'BACKUP_CORRUPT')
        j['state']='recovering';atomic_json(jfile,j)
        for rel,item in j['files'].items():
            target=safe_path(root,rel,True);old=item['before']
            if same(target,old):continue
            if not same(target,item['after']):raise InstallerError('Tệp đổi trong lúc khôi phục: '+rel,'PREIMAGE_CONFLICT')
            if old['exists']:
                target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_name('.restore_'+uuid.uuid4().hex)
                try:
                    shutil.copy2(safe_path(backup,rel),tmp)
                    if not same(tmp,old):raise InstallerError('Bản tạm khôi phục sai hash.','RESTORE_VERIFY_FAILED')
                    os.replace(tmp,target)
                finally:tmp.unlink(missing_ok=True)
            else:target.unlink(missing_ok=True)
            if not same(target,old):raise InstallerError('Đọc lại khôi phục thất bại.','RESTORE_VERIFY_FAILED')
        rp=root/RECEIPT
        previous=j.get('previous_receipt')
        if previous is None:rp.unlink(missing_ok=True)
        else:atomic_json(rp,previous)
        j['state']='rolled_back';atomic_json(jfile,j)
    def recover(self,root,event_cb=None,operation_id='recover'):
        root=Path(root).resolve();self._preflight(root)
        with self._lock(root):
            entries=self.pending(root)
            for p,j in entries:self._restore_journal(root,p,j)
        return {'status':'recovered','journals':len(entries)}
    def install(self,game_root,payload_root,manifest_data=None,operation_id='install',event_cb=None):
        root=Path(game_root).resolve();payload=Path(payload_root).resolve();emit=lambda ph,msg,n=0,t=0,receipt=None:self._emit(event_cb,operation_id,ph,msg,n,t,receipt)
        emit(OperationPhase.PREFLIGHT,'Đang kiểm tra phiên bản và gói Việt hóa...');self._preflight(root)
        with self._lock(root):
            if self.pending(root):raise InstallerError('Có thao tác bị ngắt. Chọn Phục hồi thao tác trong Công cụ trước khi cài.','RECOVERY_REQUIRED')
            if manifest_data is None:
                try:manifest_data=json.loads((payload/'patch_manifest.json').read_text(encoding='utf8'))
                except (OSError,ValueError) as e:raise InstallerError('Không đọc được patch_manifest.json: '+str(e),'MANIFEST_MISSING')
            m=normalize_manifest(manifest_data);observed=read_game_versions(root)
            def _match_ver(exp, obs):
                if not exp or exp in ('*', 'all') or obs in ('*', 'all', 'unknown'): return True
                if obs == exp: return True
                for p in str(exp).replace(';', ',').replace('|', ',').split(','):
                    p = p.strip()
                    if p in ('*', obs): return True
                    if p.endswith('*') and obs.startswith(p[:-1]): return True
                return False
            if not _match_ver(m.get('client_game_version'), observed['game']) or not _match_ver(m.get('resource_version'), observed['resource']):raise InstallerError(f"Gói dành cho game {m['client_game_version']} / tài nguyên {m['resource_version']}; bản đã chọn là {observed['game']} / {observed['resource']}.",'VERSION_MISMATCH')
            plan={};total=len(m['files'])
            for i,(rel,meta) in enumerate(m['files'].items()):
                src=safe_path(payload,meta['source']);target=safe_path(root,rel,True)
                if not same(src,{**meta,'exists':True}):raise InstallerError('Thiếu hoặc sai hash/kích thước gói: '+meta['source'],'CORRUPT_PAYLOAD')
                plan[rel]={'before':state(target),'after':{'exists':True,'sha256':meta['sha256'],'size':meta['size']},'source':meta['source']};emit(OperationPhase.VERIFY,src.name,i+1,total)
            needed=sum(v['before'].get('size',0)+v['after']['size'] for v in plan.values())+1024*1024
            if shutil.disk_usage(root).free<needed or shutil.disk_usage(self.backup_root).free<needed:raise InstallerError('Không đủ dung lượng cho bản sao lưu và tệp tạm.','DISK_FULL')
            bid='backup_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:10];backup=self.get_backup_dir_for_root(root)/bid;backup.mkdir()
            rp=root/RECEIPT;previous=None
            if rp.exists():
                try:previous=json.loads(rp.read_text(encoding='utf8'))
                except ValueError:raise InstallerError('Biên bản cũ bị hỏng; không tự ghi đè.','RECEIPT_CORRUPT')
            for i,(rel,item) in enumerate(plan.items()):
                target=safe_path(root,rel,True)
                if not same(target,item['before']):raise InstallerError('Game thay đổi trước sao lưu: '+rel,'PREIMAGE_CONFLICT')
                if item['before']['exists']:
                    b=safe_path(backup,rel);b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,b)
                    if not same(b,item['before']):raise InstallerError('Sao lưu sai hash: '+rel,'BACKUP_CORRUPT')
                emit(OperationPhase.BACKUP,target.name,i+1,total)
            bm={'created_at':datetime.now(timezone.utc).isoformat(),'game_root':canonicalize_path(root),'files':{r:v['before'] for r,v in plan.items()}}
            atomic_json(backup/'backup_manifest.json',bm)
            jid=uuid.uuid4().hex;jfile=self.journals_dir/(jid+'.json');j={'schema':2,'id':jid,'game_root':canonicalize_path(root),'backup_dir':str(backup),'files':plan,'previous_receipt':previous,'state':'prepared'};atomic_json(jfile,j)
            try:
                for i,(rel,item) in enumerate(plan.items()):
                    self._preflight(root);target=safe_path(root,rel,True)
                    if not same(target,item['before']):raise InstallerError('Tệp đã đổi trước ghi: '+rel,'PREIMAGE_CONFLICT')
                    target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_name('.patch_'+uuid.uuid4().hex)
                    try:
                        shutil.copy2(safe_path(payload,item['source']),tmp)
                        if not same(tmp,item['after']):raise InstallerError('Nguồn đổi hoặc tệp tạm sai hash.','SOURCE_CHANGED')
                        if not same(target,item['before']):raise InstallerError('Tệp đã đổi trong lúc staging.','PREIMAGE_CONFLICT')
                        j['state']='applying';j['pending']=rel;atomic_json(jfile,j);os.replace(tmp,target)
                    finally:tmp.unlink(missing_ok=True)
                    emit(OperationPhase.APPLY,target.name,i+1,total)
                for i,(rel,item) in enumerate(plan.items()):
                    if not same(safe_path(root,rel,True),item['after']):raise InstallerError('Đọc lại sai hash: '+rel,'READBACK_MISMATCH')
                    emit(OperationPhase.READBACK,rel,i+1,total)
                receipt={'schema':2,'version':m['version'],'client_game_version':m['client_game_version'],'resource_version':m['resource_version'],'game_root':canonicalize_path(root),'backup_dir':str(backup),'journal_id':jid,'installed_at':datetime.now(timezone.utc).isoformat(),'files':{r:v['after'] for r,v in plan.items()},'files_count':total,'manifest_sha256':__import__('hashlib').sha256(json.dumps(m,sort_keys=True).encode()).hexdigest()}
                atomic_json(rp,receipt);j['state']='done';atomic_json(jfile,j)
            except Exception as e:
                try:self._restore_journal(root,jfile,j)
                except Exception as recovery:
                    j['state']='recovery_required';j['error']=str(e);j['recovery_error']=str(recovery);atomic_json(jfile,j)
                    raise InstallerError('Thao tác bị ngắt; cần phục hồi từ nhật ký. Chi tiết: '+str(recovery),'RECOVERY_REQUIRED') from e
                raise InstallerError('Cài đặt thất bại; đã phục hồi trạng thái trước thao tác: '+str(e),'TRANSACTION_FAILED') from e
            emit(OperationPhase.DONE,f"Đã cài {total} tệp trong manifest {m['version']}.",total,total,receipt);return receipt
    def verify_installed(self,root,event_cb=None,operation_id='verify'):
        root=Path(root).resolve();rp=root/RECEIPT
        try:r=json.loads(rp.read_text(encoding='utf8'))
        except (OSError,ValueError):raise InstallerError('Chưa có biên bản cài đặt hợp lệ để kiểm tệp.','NOT_VERIFIED')
        if r.get('schema')!=2 or r.get('game_root')!=canonicalize_path(root) or not r.get('files'):raise InstallerError('Biên bản không khớp thư mục hoặc định dạng.','NOT_VERIFIED')
        for i,(rel,meta) in enumerate(r['files'].items()):
            if not same(safe_path(root,rel,True),meta):raise InstallerError('Tệp không khớp bản đã cài: '+rel,'FILE_MISMATCH')
            self._emit(event_cb,operation_id,OperationPhase.VERIFY,rel,i+1,len(r['files']))
        return {'status':'verified','version':r['version'],'files':len(r['files'])}
