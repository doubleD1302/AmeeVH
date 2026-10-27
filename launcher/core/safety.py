"""Strict destination/manifest contracts shared by install, restore and download."""
from __future__ import annotations
import hashlib,json,os,re,uuid
from pathlib import Path,PureWindowsPath
class InstallerError(Exception):
    def __init__(self,message,code="INSTALL_ERR"):
        super().__init__(message);self.code=code

def sha256_file(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def atomic_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with t.open('x',encoding='utf8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(t,path)
    finally:
        t.unlink(missing_ok=True)

def relative_name(name):
    if not isinstance(name,str) or not name or name!=name.strip() or chr(0) in name:raise InstallerError('Đường dẫn trống hoặc không hợp lệ.','PATH_TRAVERSAL')
    s=name.replace(chr(92),'/')
    if PureWindowsPath(s).is_absolute() or ':' in s or s.startswith('/') or any(x in ('','..','.') or x.rstrip(' .')!=x for x in s.split('/')):
        raise InstallerError('Đường dẫn vượt phạm vi: '+name,'PATH_TRAVERSAL')
    if any(re.match(r'(?i)^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)',x) for x in s.split('/')):raise InstallerError('Tên tệp Windows không hợp lệ.','PATH_TRAVERSAL')
    return s

def safe_path(root,name,destination=False):
    rel=relative_name(name);root=Path(root).resolve();dest=root/rel
    cursor=dest
    while cursor!=root:
        if cursor.is_symlink() or (hasattr(cursor,'is_junction') and cursor.is_junction()):raise InstallerError('Không cho phép liên kết/junction trong đường dẫn.','PATH_ESCAPE')
        # Python 3.10 Windows: FILE_ATTRIBUTE_REPARSE_POINT also identifies junctions.
        try:
            if cursor.lstat().st_file_attributes & 0x400:raise InstallerError('Đường dẫn chứa reparse point.','PATH_ESCAPE')
        except (FileNotFoundError,AttributeError):pass
        cursor=cursor.parent
    try:dest.resolve().relative_to(root)
    except ValueError:raise InstallerError('Đường dẫn vượt thư mục đã chọn.','PATH_ESCAPE')
    if destination:
        allowed=rel in ('Persistent_Store/Scripts/lua.arcx','Persistent_Store/Tables/data.arcx') or bool(re.fullmatch(r'Persistent_Store/AssetBundles/[A-Za-z0-9_.-]+[.]en[.]unity3d',rel)) or bool(re.fullmatch(r'Persistent_Store/Videos/[^/<>:"|?*]+[.]srt',rel))
        if not allowed:raise InstallerError('Tệp nằm ngoài danh sách tài nguyên được phép: '+rel,'PATH_NOT_ALLOWED')
    return dest

def normalize_manifest(raw):
    if not isinstance(raw,dict):raise InstallerError('Manifest phải là JSON object.','MANIFEST_INVALID')
    m=dict(raw);version=m.get('version') or m.get('release_tag')
    if not isinstance(version,str) or not version:raise InstallerError('Manifest thiếu phiên bản bản dịch.','MANIFEST_INVALID')
    game=m.get('client_game_version');res=m.get('resource_version')
    if not isinstance(game,str) or not game or not isinstance(res,(str,int)) or not str(res):raise InstallerError('Manifest thiếu phiên bản game/tài nguyên tương thích.','VERSION_MISSING')
    mapping=m.get('files')
    if mapping is None:
        bundles=m.get('bundles',{})
        mapping={f'Persistent_Store/AssetBundles/{n}':{'source':f'AssetBundles/{n}','sha256':v.get('patched_sha256') or v.get('sha256'),'size':v.get('size_bytes') or v.get('size')} for n,v in bundles.items() if isinstance(v,dict)}
        if isinstance(m.get('lua_arcx'),dict):
            l=m['lua_arcx']
            mapping['Persistent_Store/Scripts/lua.arcx']={'source':l.get('filename','lua_patched_vi.arcx'),'sha256':l.get('sha256'),'size':l.get('size_bytes') or l.get('size')}
        if isinstance(m.get('data_arcx'),dict):
            d=m['data_arcx']
            mapping['Persistent_Store/Tables/data.arcx']={'source':d.get('filename','data_patched_vi.arcx'),'sha256':d.get('sha256'),'size':d.get('size_bytes') or d.get('size')}
        if not mapping:raise InstallerError('Manifest không khai báo tệp được xác minh.','EMPTY_MANIFEST')
    if not isinstance(mapping,dict) or not mapping:raise InstallerError('Danh sách tệp rỗng/không hợp lệ.','EMPTY_MANIFEST')
    result={};seen=set()
    for dest,meta in mapping.items():
        rel=relative_name(dest)
        if rel.casefold() in seen:raise InstallerError('Manifest trùng đường dẫn khác hoa/thường.','MANIFEST_INVALID')
        seen.add(rel.casefold());safe_path(Path.cwd(),rel,True)
        if not isinstance(meta,dict):raise InstallerError('Metadata tệp không hợp lệ.','MANIFEST_INVALID')
        digest=meta.get('sha256');size=meta.get('size')
        if not isinstance(digest,str) or not re.fullmatch('[0-9a-fA-F]{64}',digest) or not isinstance(size,int) or isinstance(size,bool) or size<0:raise InstallerError('Mỗi tệp phải có SHA256 và kích thước hợp lệ: '+rel,'MANIFEST_INVALID')
        src=relative_name(meta.get('source',rel))
        result[rel]={'source':src,'sha256':digest.lower(),'size':size}
    return {**m,'version':version,'client_game_version':game,'resource_version':str(res),'files':result}
