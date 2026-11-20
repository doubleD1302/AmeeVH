"""Resolve full regional PC resources and BSDIFF dependencies from official metadata.

AES format independently checked against live regional serverlists, 2026-11-05.
Dependency: pycryptodome. Keys/format reference: Nebula-nb AeadHelper.java.
"""
import urllib.request
import urllib.parse
import hashlib
import re
import time
from concurrent.futures import ThreadPoolExecutor

REGIONS = {
    'EN': ('https://nova-static.stellasora.global', b'ma5Dn2FhC*Xhxy%c'),
    'JP': ('https://nova-static.stellasora.jp', b'ZnUFA@S9%4KyoryM'),
    'CN': ('https://nova-static.yostar.cn', b'Xf&FRcsYm48cJ2A@'),
}


def decrypt_metadata(data, region):
    from Crypto.Cipher import AES
    if len(data) < 32 or len(data) % 16:
        raise ValueError('Invalid encrypted metadata length')
    plain = AES.new(REGIONS[region][1], AES.MODE_CBC, data[:16]).decrypt(data[16:])
    n = plain[-1]
    if not 1 <= n <= 16 or plain[-n:] != bytes([n]) * n:
        raise ValueError('Invalid metadata padding / wrong region')
    return plain[:-n]


def varint(data, offset):
    number = 0
    for shift in range(0, 70, 7):
        if offset >= len(data):
            raise ValueError('Truncated protobuf varint')
        value = data[offset]
        offset += 1
        number |= (value & 127) << shift
        if value < 128:
            return number, offset
    raise ValueError('Oversized protobuf varint')


def protobuf_fields(data):
    """Return repeated field numbers without guessing nested message structure."""
    result = {}
    pos = 0
    while pos < len(data):
        tag, pos = varint(data, pos)
        field, wire = tag >> 3, tag & 7
        if not field:
            raise ValueError('Zero protobuf field')
        if wire == 0:
            value, pos = varint(data, pos)
        elif wire in (1, 2, 5):
            if wire == 2:
                size, pos = varint(data, pos)
            else:
                size = {1: 8, 5: 4}[wire]
            if pos + size > len(data):
                raise ValueError('Truncated protobuf field')
            value = data[pos:pos + size]
            pos += size
        else:
            raise ValueError('Unsupported protobuf wire type')
        result.setdefault(field, []).append((wire, value))
    return result


def fetch_metadata(url, region):
    if not url.startswith(REGIONS[region][0] + '/'):
        raise ValueError('Metadata URL belongs to another region')
    req = urllib.request.Request(url, headers={'User-Agent': 'StellaResourceFetch/2.0'})
    with urllib.request.urlopen(req, timeout=20) as response:
        encrypted = response.read(16 * 1024 * 1024 + 1)
    if len(encrypted) > 16 * 1024 * 1024:
        raise ValueError('Metadata exceeds size limit')
    return decrypt_metadata(encrypted, region)


def fetch_serverlist(region):
    url = REGIONS[region][0] + '/meta/serverlist.html'
    plain = fetch_metadata(url, region)
    fields = protobuf_fields(plain)
    version = fields.get(1)
    if not version or len(version) != 1 or version[0][0] != 0:
        raise ValueError('Missing or ambiguous server data version')
    return {'metadata_url': url, 'server_data_version': version[0][1],
            'resource_game_version': None, 'resource_version': None,
            'status': 'serverlist_verified_update_manifest_unresolved'}


def read_url(url, cap=16*1024*1024):
    error = None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 StellaResourceFetch/2.0','Cache-Control':'no-cache'})
            with urllib.request.urlopen(req,timeout=30) as resp:
                data=resp.read(cap+1)
                evidence={k:resp.headers.get(k) for k in ('Date','Age','Last-Modified','ETag')}
            if len(data)>cap:raise ValueError('Response exceeds limit')
            return data,evidence
        except OSError as exc:error=exc
    raise OSError(f'Cannot fetch {url}: {error}') from error


def decode_diff(plain, region):
    records={}
    for wire,raw in protobuf_fields(plain).get(1,[]):
        if wire!=2:raise ValueError('Invalid FileDiff wire')
        f=protobuf_fields(raw)
        def one(field,wire):
            a=f.get(field,[])
            if len(a)!=1 or a[0][0]!=wire:raise ValueError('Invalid FileDiff field')
            return a[0][1]
        name=one(1,2).decode('utf8'); checksum=one(2,2).decode('ascii'); version=one(3,0); folder=one(4,2).decode('ascii')
        if '/' in name or '\\' in name or name in ('.','..') or not re.fullmatch('[a-zA-Z0-9_. -]+',name):raise ValueError('Unsafe file name')
        if not re.fullmatch('[a-f0-9]{1,32}',checksum) or not re.fullmatch('[a-f0-9]{1,32}',folder):raise ValueError('Invalid FileDiff checksum/path')
        if name in records:raise ValueError('Duplicate FileDiff')
        url=REGIONS[region][0]+f'/res/win/{version}/{folder}/'+urllib.parse.quote(name)
        records[name]={'name':name,'checksum':checksum.zfill(32),'version':version,'url':url}
    return records


def parse_manifest(data):
    headers={}; files={}; patches={}
    for line in data.decode('utf-8-sig').splitlines():
        if not line:continue
        if line.startswith('$'):
            key,sep,value=line[1:].partition(':')
            if not sep:raise ValueError('Malformed header')
            if key=='BIN_DIFF_PATCH_FILE':
                p=value.split('|')
                if len(p)<5:raise ValueError('Malformed patch directive')
                patches[p[0]]={'name':p[0],'checksum':p[1].zfill(32),'size':int(p[2]),'old_checksum':p[3].removeprefix('@').zfill(32),'kind':p[4]}
            elif key=='BIN_DIFF_PATCH_INFO':
                headers.setdefault(key,[]).append(value)
            else:headers[key]=value
        else:
            p=line.split('|')
            if len(p)<4:raise ValueError('Malformed resource line')
            if p[0] in files:raise ValueError('Duplicate resource line')
            files[p[0]]={'name':p[0],'checksum':p[1].zfill(32),'size':int(p[2])}
    return headers,files,patches


def latest_plan(region,profile='localization'):
    root=REGIONS[region][0]
    token=str(time.time_ns())
    encrypted,meta_evidence=read_url(root+'/meta/win.html?nocache='+token)
    plain=decrypt_metadata(encrypted,region)
    diff=decode_diff(plain,region)
    server_encrypted,server_ev=read_url(root+'/meta/serverlist.html?nocache='+token)
    server_plain=decrypt_metadata(server_encrypted,region)
    server_version=protobuf_fields(server_plain)[1][0][1]
    if max(x['version'] for x in diff.values())!=server_version:raise ValueError('Serverlist and resource metadata versions disagree')
    evidence=[{'url':root+'/meta/win.html','sha256':hashlib.sha256(plain).hexdigest(),'headers':meta_evidence}]
    evidence[0]['encrypted_sha256']=hashlib.sha256(encrypted).hexdigest()
    evidence.append({'url':root+'/meta/serverlist.html','sha256':hashlib.sha256(server_plain).hexdigest(),'encrypted_sha256':hashlib.sha256(server_encrypted).hexdigest(),'headers':server_ev})
    def manifest(name):
        item=diff[name];data,ev=read_url(item['url'])
        if hashlib.md5(data).hexdigest()!=item['checksum']:raise ValueError('Manifest MD5 mismatch '+name)
        return name,data,parse_manifest(data),{'url':item['url'],'sha256':hashlib.sha256(data).hexdigest(),'md5':item['checksum'],'headers':ev}
    base=manifest('ss_win.mani');evidence.append(base[3])
    count=int(base[2][0].get('BIN_DIFF_PATCH_VER','0'))
    names=(['ss_win_add.mani'] if 'ss_win_add.mani' in diff else [])+[f'p_{i}_m.ss_win.mani' for i in range(1,count+1)]
    with ThreadPoolExecutor(max_workers=4) as pool: manifests=list(pool.map(manifest,names))
    all_manifests=[base]+manifests
    evidence.extend(m[3] for m in manifests)
    final=next((m for m in manifests if m[0]==f'p_{count}_m.ss_win.mani'),base)
    final_files=dict(base[2][1])
    if 'ss_win_add.mani' in names:
        final_files.update(next(m for m in manifests if m[0]=='ss_win_add.mani')[2][1])
    final_files.update(final[2][1])
    versions={}
    patch_index={}
    for name,data,(head,files,patches),ev in all_manifests:
        for key,record in files.items():versions[(key,record['checksum'])]=record
        for patch_name,patch in patches.items():
            match=re.fullmatch(r'p_\d+_[un]\.(.+)',patch_name)
            if not match:raise ValueError('Unsupported patch name '+patch_name)
            actual=match[1]
            if actual not in files:raise ValueError('Patch target missing')
            patch_index[(actual,files[actual]['checksum'])]=patch
    def path(name):
        if name=='data.arcx':return 'Tables/'+name
        if name=='lua.arcx':return 'Scripts/'+name
        if name.endswith('.srt'):return 'Videos/'+name
        return 'AssetBundles/'+name
    def resolve(name,checksum,trail=()):
        key=(name,checksum)
        if key in trail:raise ValueError('Cyclic patch chain')
        record=versions[key]
        out={'path':path(name),'size':record['size'],'algorithm':'md5','checksum':checksum}
        if name in diff and diff[name]['checksum']==checksum:
            out['url']=diff[name]['url'];return out
        patch=patch_index.get(key)
        if patch is None:raise ValueError('Unresolved resource '+name+' '+checksum)
        remote=diff[patch['name']]
        if remote['checksum']!=patch['checksum']:raise ValueError('Patch metadata mismatch')
        if patch['kind']=='N':
            if remote['checksum']!=checksum:raise ValueError('New file checksum does not match final manifest')
            out['url']=remote['url'];return out
        if patch['kind']!='U':raise ValueError('Unsupported patch action '+patch['kind'])
        out['base']=resolve(name,patch['old_checksum'],trail+(key,))
        out['patch']={'path':patch['name'],'size':patch['size'],'algorithm':'md5','checksum':patch['checksum'],'url':remote['url']}
        out['url']=remote['url']
        return out
    files=[]
    for name,item in sorted(final_files.items()):
        if name in ('data.arcx','lua.arcx') or name.endswith('.srt') or (profile!='text' and name.endswith('.unity3d')):
            files.append(resolve(name,item['checksum']))
    if not {'data.arcx','lua.arcx'}.issubset({item['path'].split('/')[-1] for item in files}):raise ValueError('Required text archives absent')
    # Recheck the live update identity after planning; refuse a mixed snapshot.
    encrypted2,ev2=read_url(root+'/meta/win.html?nocache='+str(time.time_ns()))
    if decrypt_metadata(encrypted2,region)!=plain:raise ValueError('Update metadata changed during planning; retry')
    head=final[2][0]
    if count:
        latest_info=next((s.split('|') for s in base[2][0].get('BIN_DIFF_PATCH_INFO',[]) if s.split('|')[0]==str(count)),None)
        if not latest_info or head.get('RES_VER')!=latest_info[1]:raise ValueError('Latest patch version mismatch')
    if not all(head.get(x) for x in ('CLIENT_VER','GAME_VER','RES_VER')):raise ValueError('Required version header absent')
    if final[0] in diff and diff[final[0]]['version']!=server_version:raise ValueError('Final manifest metadata is not current server version')
    return {'region':region,'client_version':head.get('CLIENT_VER'),'game_version':head.get('GAME_VER'),'resource_version':head.get('RES_VER'),'manifest_sha256':hashlib.sha256(final[1]).hexdigest(),'profile':profile,'latest_verified':True,'server_data_version':server_version,'files':files,'evidence':evidence,'manifest_snapshots':{name:data.decode('utf-8-sig') for name,data,_,_ in all_manifests}}
