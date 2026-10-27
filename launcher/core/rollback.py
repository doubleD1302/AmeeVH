"""Receipt-selected restore; never chooses another installation's latest backup."""
from pathlib import Path
import json
from .installer import PatchInstaller,RECEIPT,same
from .safety import InstallerError,safe_path,atomic_json
from .game_detection import canonicalize_path
from .types import OperationPhase
class RollbackEngine:
    def __init__(self,backup_root,journals_dir=None):
        self.backup_root=Path(backup_root);self.engine=PatchInstaller(self.backup_root,Path(journals_dir) if journals_dir else self.backup_root.parent/'journals')
    def get_backups_for_game(self,root):
        out=[]
        for b in self.engine.get_backup_dir_for_root(root).glob('backup_*'):
            try:
                m=json.loads((b/'backup_manifest.json').read_text(encoding='utf8'))
                if m.get('game_root')==canonicalize_path(root):out.append({'id':b.name,'path':b,'manifest':m,'files_count':len(m['files']),'created_at':m['created_at']})
            except (OSError,ValueError,KeyError):pass
        return sorted(out,key=lambda v:v['created_at'],reverse=True)
    def rollback(self,game_root,backup_id=None,operation_id='rollback',event_cb=None):
        root=Path(game_root).resolve();self.engine._preflight(root)
        with self.engine._lock(root):
            if self.engine.pending(root):raise InstallerError('Hãy phục hồi nhật ký bị ngắt trước.','RECOVERY_REQUIRED')
            try:r=json.loads((root/RECEIPT).read_text(encoding='utf8'))
            except (OSError,ValueError):raise InstallerError('Thiếu biên bản cài; không tự chọn backup gần nhất.','NO_BACKUP_FOUND')
            if r.get('schema')!=2 or r.get('game_root')!=canonicalize_path(root):raise InstallerError('Biên bản không thuộc game hoặc định dạng cũ chưa được xác minh.','ROOT_MISMATCH')
            jid=r.get('journal_id','')
            if not isinstance(jid,str) or len(jid)!=32 or any(c not in '0123456789abcdef' for c in jid):raise InstallerError('Mã nhật ký không hợp lệ.','JOURNAL_CORRUPT')
            jf=self.engine.journals_dir/(jid+'.json')
            try:j=json.loads(jf.read_text(encoding='utf8'))
            except (OSError,ValueError):raise InstallerError('Nhật ký/backup đã mất; không ghi đè game.','BACKUP_CORRUPT')
            if backup_id and Path(j['backup_dir']).name!=backup_id:raise InstallerError('Backup được chọn không khớp biên bản hiện tại.','BACKUP_MISMATCH')
            if j['game_root']!=canonicalize_path(root) or j['backup_dir']!=r.get('backup_dir'):raise InstallerError('Backup không khớp biên bản.','BACKUP_MISMATCH')
            for rel,item in j['files'].items():
                if rel not in r['files'] or not same(safe_path(root,rel,True),r['files'][rel]):raise InstallerError('Game đã đổi sau cài; không khôi phục đè tệp: '+rel,'PREIMAGE_CONFLICT')
            self.engine._emit(event_cb,operation_id,OperationPhase.ROLLBACK,'Đang khôi phục bản sao lưu gắn với game...')
            self.engine._restore_journal(root,jf,j)
            self.engine._emit(event_cb,operation_id,OperationPhase.DONE,'Đã khôi phục trạng thái trước lần cài này.',len(j['files']),len(j['files']))
            return {'status':'success','restored_files_count':len(j['files']),'backup_id':Path(j['backup_dir']).name}
