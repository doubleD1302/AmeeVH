"""Bounded JSON/network adapters for the existing Stella Sora release provider."""
from __future__ import annotations
import json,os,re,shutil,time,urllib.request,urllib.parse,uuid,zipfile,hashlib
from datetime import datetime,timezone
from pathlib import Path
from .types import NotificationItem,SupporterData,OperationPhase,OperationEvent
from .safety import InstallerError,sha256_file,safe_path,relative_name,normalize_manifest,atomic_json

def valid_url(url):
    try:
        u=urllib.parse.urlparse(url)
        return u.scheme in ('https','http') and bool(u.hostname) and not u.username and not u.password
    except ValueError:return False

def version_tuple(v):return tuple(int(n) for n in re.findall(r'\d+',str(v).split('-')[0]))

class NetworkService:
    def __init__(self,update_url=None,notifications_url=None,cache_dir=None,timeout=8):
        self.update_url=update_url;self.notifications_url=notifications_url;self.cache_dir=Path(cache_dir) if cache_dir else None;self.timeout=timeout;self.notification_status='unavailable';self.notification_message='Chưa tải thông báo.';self.connection_status='Chưa kiểm tra kết nối';self.notification_version=None
    def _json(self,url,expected_sha=None,expected_size=None):
        if not valid_url(url):raise InstallerError('Endpoint không phải HTTP/HTTPS hợp lệ.','ENDPOINT_INVALID')
        req=urllib.request.Request(url,headers={'User-Agent':'StellaSora-Launcher/0.9.8','Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=self.timeout) as r:
            data=r.read(4*1024*1024+1)
            if len(data)>4*1024*1024:raise InstallerError('JSON máy chủ quá lớn.','SCHEMA_INVALID')
            if expected_size is not None and len(data)!=expected_size:raise InstallerError('Metadata tải về không đúng kích thước đã công bố.','SIZE_MISMATCH')
            if expected_sha and hashlib.sha256(data).hexdigest()!=expected_sha.lower():raise InstallerError('Metadata tải về không khớp SHA256 của bản phát hành.','HASH_MISMATCH')
            result=json.loads(data.decode('utf8'))
            if not isinstance(result,dict):raise InstallerError('Máy chủ trả JSON sai định dạng.','SCHEMA_INVALID')
            return result
    def _notifications(self,d):
        raw=d.get('announcements',d.get('notifications'))
        if not isinstance(raw,list):raise InstallerError('Thông báo thiếu danh sách announcements.','SCHEMA_INVALID')
        out=[];ids=set()
        for e in raw:
            if not isinstance(e,dict) or not all(isinstance(e.get(k),str) for k in ('id','title','content')) or e['id'] in ids:raise InstallerError('Thông báo chứa mục không hợp lệ/trùng ID.','SCHEMA_INVALID')
            ids.add(e['id']);link=e.get('link_url') or e.get('url')
            if link and not valid_url(link):link=None
            out.append(NotificationItem(e['id'],e['title'],str(e.get('summary',e['content'][:160])),e['content'],str(e.get('category',e.get('type','notice'))),str(e.get('badge',e.get('type','Thông báo'))),str(e.get('date','')),link,bool(e.get('is_unread',False))))
        return out
    def fetch_notifications(self,fallback_path=None):
        cache=self.cache_dir/'notifications.json' if self.cache_dir else None
        failure=''
        if self.notifications_url:
            try:
                d=self._json(self.notifications_url);items=self._notifications(d);self.notification_version=str(d.get('version','Chưa công bố'))
                if cache:atomic_json(cache,d)
                self.notification_status='online' if items else 'empty';self.notification_message='Thông báo trực tuyến' if items else 'Máy chủ hiện chưa có thông báo.';self.connection_status='Kết nối thành công';return items
            except Exception as e:failure=str(e);self.connection_status='Lỗi kết nối thông báo'
        for path,label in ((cache,'cached'),(Path(fallback_path) if fallback_path else None,'bundled')):
            if path and path.is_file():
                try:
                    d=json.loads(path.read_text(encoding='utf8'));items=self._notifications(d);self.notification_version=str(d.get('version','Chưa công bố'));self.notification_status=label;self.notification_message=('Bản lưu ngoại tuyến' if label=='cached' else 'Thông báo đi kèm launcher')+('. Không tải được dữ liệu mới: '+failure if failure else '');return items
                except Exception as e:failure=str(e)
        self.notification_status='error' if failure else 'empty';self.notification_message='Không đọc được thông báo: '+failure if failure else 'Chưa có thông báo.';return []
    def _validate_release(self,d):
        if not isinstance(d,dict) or not isinstance(d.get('tag_name'),str) or not isinstance(d.get('assets'),list):raise InstallerError('Bản phát hành thiếu thông tin hợp lệ.','SCHEMA_INVALID')
        if d.get('draft') or d.get('prerelease'):raise InstallerError('Kênh đang trỏ đến bản nháp/thử nghiệm.','RELEASE_UNAVAILABLE')
        for a in d['assets']:
            if not isinstance(a,dict) or not isinstance(a.get('name'),str) or not isinstance(a.get('size'),int) or not valid_url(a.get('browser_download_url','')):raise InstallerError('Thông tin tệp phát hành không hợp lệ.','SCHEMA_INVALID')
        return d
    def release(self):
        if not self.update_url:raise InstallerError('Chưa cấu hình kênh cập nhật.','ENDPOINT_UNAVAILABLE')
        d=self._validate_release(self._json(self.update_url));self.connection_status='Kết nối thành công';return d
    def _asset_digest(self,asset,required=False):
        value=asset.get('digest','')
        if re.fullmatch('sha256:[0-9a-fA-F]{64}',str(value)):return value[7:].lower()
        if required:raise InstallerError('Tệp phát hành chưa có SHA256 để xác minh: '+asset.get('name','metadata'),'METADATA_UNVERIFIED')
        return None
    def _manifest_for_release(self,release,manifest_url=None):
        if release is None:
            if manifest_url:return self._json(manifest_url),{'source':'explicit_custom_manifest'}
            raise InstallerError('Chưa đọc được bản phát hành trực tuyến.','RELEASE_UNAVAILABLE')
        matches=[a for a in release['assets'] if a['name'] in ('patch_manifest.json','stella_patch_manifest.json')]
        asset=next((a for a in release['assets'] if manifest_url and a['browser_download_url']==manifest_url),None) if manifest_url else (matches[0] if matches else None)
        if asset:
            digest=self._asset_digest(asset,True);raw=self._json(asset['browser_download_url'],digest,asset['size'])
            return raw,{'source':'release_asset','asset':asset['name'],'sha256':digest,'size':asset['size'],'release_tag':release['tag_name']}
        if manifest_url:
            # This URL is explicitly configured by the user. No compatibility or
            # files are synthesized from unrelated GitHub asset names.
            return self._json(manifest_url),{'source':'explicit_custom_manifest','release_tag':release['tag_name']}
        raise InstallerError('Bản phát hành chưa có bảng kê tệp tương thích.','MANIFEST_MISSING')
    def _windows_manifest(self,raw):
        manifest=normalize_manifest(raw)
        platform=str(manifest.get('platform','windows')).lower()
        if platform not in ('windows','win','pc'):
            raise InstallerError('Bảng kê không dành cho Windows.','PLATFORM_MISMATCH')
        return manifest
    def check_for_updates(self,current_version='0.9.8',release_data=None):
        base={'status':'unavailable','has_update':False,'latest_version':None,'download_url':None,'message':'Chưa có kênh cập nhật launcher đã xác minh.'}
        if not self.update_url:return base
        try:
            d=release_data if release_data is not None else self.release();latest=d['tag_name'];new=version_tuple(latest)>version_tuple(current_version)
            assets=d.get('assets',[]);asset=None
            for a in assets:
                n=a.get('name','').lower()
                if a.get('name','').endswith('.exe') and not n.startswith('helper'):
                    if any(k in n for k in ('launcher','windows','stellasora')):
                        asset=a;break
            if not asset:
                for a in assets:
                    if a.get('name','').endswith('.exe') and not a.get('name','').lower().startswith('helper'):
                        asset=a;break
            digest=self._asset_digest(asset) if asset else None
            if asset and not digest:
                sums_asset=next((a for a in assets if a.get('name')=='SHA256SUMS.txt'),None)
                if sums_asset and valid_url(sums_asset.get('browser_download_url','')):
                    try:
                        sreq=urllib.request.Request(sums_asset['browser_download_url'],headers={'User-Agent':'StellaSora-Launcher'})
                        with urllib.request.urlopen(sreq,timeout=self.timeout) as sresp:
                            stext=sresp.read(64*1024).decode('utf-8',errors='ignore')
                            for sline in stext.splitlines():
                                sparts=sline.strip().split()
                                if len(sparts)>=2 and re.fullmatch(r'[0-9a-fA-F]{64}',sparts[0]):
                                    sname=sparts[1].lstrip('*')
                                    if sname==asset['name'] or (sname=='StellaSora_Launcher.exe' and 'launcher' in asset['name'].lower()):
                                        digest=sparts[0].lower();break
                    except Exception:pass
            actionable=bool(new and asset and digest)
            return {**base,'status':'online','has_update':new,'latest_version':latest,'download_url':asset['browser_download_url'] if actionable else None,'asset':asset,'sha256':digest if actionable else None,'message':('Có bản cập nhật launcher '+latest+('. Có thể tự động tải và cập nhật.' if actionable else '; chưa có tệp được xác minh để tự cập nhật.')) if new else f'Launcher hiện tại ({current_version}) là phiên bản mới nhất.','changelog':d.get('body','')}
        except Exception as exc:return {**base,'status':'error','message':'Không kiểm tra được cập nhật: '+str(exc)}
    def sync_channel(self,fallback_path,current_version='0.9.8',manifest_url=None,check_launcher=True):
        items=self.fetch_notifications(fallback_path);release=None;release_status='error';release_error='';manifest_status='unavailable';manifest_error='';translation_version=None;file_count=None;translation_scope=None;cache_warning='';translation_game=None;translation_resource=None
        try:
            release=self.release();release_status='online'
            if self.cache_dir:
                try:atomic_json(self.cache_dir/'release.json',release)
                except OSError as exc:cache_warning='Đã đọc trực tuyến nhưng chưa lưu được bản dự phòng: '+str(exc)
        except Exception as exc:
            release_error=str(exc);cached=self.cache_dir/'release.json' if self.cache_dir else None
            if cached and cached.is_file():
                try:release=self._validate_release(json.loads(cached.read_text(encoding='utf8')));release_status='cached'
                except (OSError,ValueError,InstallerError):pass
        update={'status':release_status,'has_update':False,'download_url':None,'message':'Chưa lấy được thông tin launcher trực tuyến.'}
        if release_status=='online':
            update=self.check_for_updates(current_version,release) if check_launcher else {'status':'not_checked','has_update':False,'download_url':None,'message':'Đã tắt kiểm tra launcher lúc mở. Bạn vẫn có thể kiểm tra thủ công.'}
            try:
                raw,binding=self._manifest_for_release(release,manifest_url);manifest=self._windows_manifest(raw);translation_version=manifest['version'];file_count=len(manifest['files']);translation_game=manifest['client_game_version'];translation_resource=manifest['resource_version'];translation_scope='images_only' if all(path.startswith('Persistent_Store/AssetBundles/') for path in manifest['files']) else 'declared_files';manifest_status='online'
            except Exception as exc:manifest_status='error';manifest_error=str(exc)
        if manifest_url and release_status!='online':
            try:
                raw,binding=self._manifest_for_release(None,manifest_url);manifest=self._windows_manifest(raw);translation_version=manifest['version'];file_count=len(manifest['files']);translation_game=manifest['client_game_version'];translation_resource=manifest['resource_version'];translation_scope='images_only' if all(path.startswith('Persistent_Store/AssetBundles/') for path in manifest['files']) else 'declared_files';manifest_status='online'
            except Exception as exc:manifest_status='error';manifest_error=str(exc)
        fresh=self.notification_status in ('online','empty') and release_status=='online' and manifest_status=='online'
        return {'notifications':items,'notification_status':self.notification_status,'notification_message':self.notification_message,'notification_version':self.notification_version,'release_status':release_status,'release_version':release.get('tag_name') if release else None,'release_notes':str(release.get('body') or '')[:8000] if release_status=='online' else '', 'release_error':release_error,'translation_version':translation_version,'translation_game':translation_game,'translation_resource':translation_resource,'manifest_status':manifest_status,'manifest_error':manifest_error,'translation_file_count':file_count,'translation_scope':translation_scope,'cache_warning':cache_warning,'update':update,'fresh':fresh,'message':'Đã đọc thông tin mới từ GitHub.' if fresh else 'Đồng bộ chưa đầy đủ. Xem trạng thái từng nguồn bên dưới.','fetched_at':datetime.now(timezone.utc).isoformat()}
    def download(self,url,dest,size,sha=None,event_cb=None,operation_id='download'):
        if not valid_url(url) or not isinstance(size,int) or size<=0:raise InstallerError('Thiếu URL/kích thước tải hợp lệ.','DOWNLOAD_INVALID')
        dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True);part=dest.with_name(dest.name+'.'+uuid.uuid4().hex+'.part');deadline=time.monotonic()+120
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'StellaSora-Launcher/0.9.8'}),timeout=self.timeout) as r,part.open('xb') as out:
                n=0
                while True:
                    if time.monotonic()>deadline:raise InstallerError('Tải quá thời hạn. Hãy thử lại.','DOWNLOAD_TIMEOUT')
                    chunk=r.read(256*1024)
                    if not chunk:break
                    n+=len(chunk)
                    if n>size:raise InstallerError('Máy chủ trả quá kích thước đã kê khai.','SIZE_MISMATCH')
                    out.write(chunk)
                    if event_cb:event_cb(OperationEvent(operation_id,OperationPhase.DOWNLOAD,dest.name,n,size,'bytes'))
                out.flush();os.fsync(out.fileno())
            if part.stat().st_size!=size or (sha and sha256_file(part)!=sha.lower()):raise InstallerError('Tải thiếu hoặc sai SHA256.','HASH_MISMATCH')
            os.replace(part,dest);return dest
        finally:part.unlink(missing_ok=True)
    def prepare_payload(self,cache_root,manifest_url=None,event_cb=None,operation_id='download'):
        # Always re-resolve the online release at install time; cached display
        # metadata never authorizes installation or a downgrade.
        try:release=self.release()
        except Exception:
            if not manifest_url:raise
            # Explicit custom manifest sources can operate independently; unlike
            # the default GitHub path, they do not acquire missing file metadata
            # from a cached release or from asset names.
            release=None
        raw,binding=self._manifest_for_release(release,manifest_url)
        manifest=self._windows_manifest(raw);stage=Path(cache_root)/('payload_'+uuid.uuid4().hex);stage.mkdir(parents=True)
        release_assets={a['name']:a for a in release['assets']} if release else {}
        assets=release_assets if binding['source']=='release_asset' else {}
        package=raw.get('package_zip',{}) if isinstance(raw.get('package_zip'),dict) else {}
        if binding['source']=='explicit_custom_manifest' and package.get('filename'):
            # An independent custom manifest cannot inherit an arbitrary ZIP.
            # Reuse only its explicit exact filename/hash/size package binding.
            candidate=release_assets.get(package['filename']);digest=package.get('sha256');size=package.get('size_bytes')
            if candidate and isinstance(digest,str) and re.fullmatch('[0-9a-fA-F]{64}',digest) and isinstance(size,int) and not isinstance(size,bool) and size>0 and candidate['size']==size and self._asset_digest(candidate)==digest.lower():
                assets={package['filename']:candidate};binding={**binding,'explicit_package_asset':package['filename'],'explicit_package_sha256':digest.lower()}
        zasset=assets.get(package.get('filename')) if package.get('filename') else next((a for a in assets.values() if 'AssetBundles' in a['name'] and a['name'].endswith('.zip')),None)
        bundle_entries={r:v for r,v in manifest['files'].items() if r.startswith('Persistent_Store/AssetBundles/')}
        if bundle_entries and zasset:
            # Container size is checked; promotion of payload requires each manifest hash.
            zip_digest=self._asset_digest(zasset);declared_digest=package.get('sha256') or raw.get('asset_bundles_package_sha256');declared_size=package.get('size_bytes') or raw.get('asset_bundles_package_size')
            if declared_digest is not None and (not isinstance(declared_digest,str) or not re.fullmatch('[0-9a-fA-F]{64}',declared_digest)):raise InstallerError('Mã xác minh gói ảnh không hợp lệ.','MANIFEST_INVALID')
            if declared_size is not None and (not isinstance(declared_size,int) or isinstance(declared_size,bool) or declared_size<=0):raise InstallerError('Kích thước gói ảnh không hợp lệ.','MANIFEST_INVALID')
            if declared_digest and zip_digest and declared_digest.lower()!=zip_digest:raise InstallerError('Gói ảnh không khớp bảng kê của bản phát hành.','HASH_MISMATCH')
            if declared_size is not None and declared_size!=zasset['size']:raise InstallerError('Kích thước gói ảnh không khớp bản phát hành.','SIZE_MISMATCH')
            archive=self.download(zasset['browser_download_url'],stage/'bundles.download',zasset['size'],declared_digest or zip_digest,event_cb,operation_id)
            with zipfile.ZipFile(archive) as z:
                members={};seen=set()
                for info in z.infolist():
                    if info.is_dir():continue
                    name=relative_name(info.filename)
                    if name.casefold() in seen:raise InstallerError('Archive trùng tên tệp.','ARCHIVE_INVALID')
                    seen.add(name.casefold())
                    if (info.external_attr>>16)&0o170000==0o120000:raise InstallerError('Archive có symlink.','PATH_ESCAPE')
                    members[name]=info
                for rel,meta in bundle_entries.items():
                    options=[meta['source'],Path(meta['source']).name,'AssetBundles/'+Path(meta['source']).name]
                    info=next((members[x] for x in options if x in members),None)
                    if info is None or info.file_size!=meta['size']:raise InstallerError('Bundle thiếu/sai kích thước trong archive.','CORRUPT_PAYLOAD')
                    target=safe_path(stage,meta['source']);target.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(info) as src,target.open('xb') as out:shutil.copyfileobj(src,out,256*1024)
                    if sha256_file(target)!=meta['sha256']:raise InstallerError('Bundle sai SHA256: '+rel,'HASH_MISMATCH')
            archive.unlink()
        for rel,meta in manifest['files'].items():
            target=safe_path(stage,meta['source'])
            if target.is_file():continue
            original=raw.get('files',{}).get(rel,{})
            url=original.get('url') or original.get('download_url')
            asset=assets.get(Path(meta['source']).name)
            if not url and asset:url=asset['browser_download_url']
            if not url:raise InstallerError('Gói chưa cung cấp đường dẫn tải cho '+rel+'. Nguồn tùy chỉnh cần đường dẫn tệp trực tiếp hoặc một gói ZIP được khai báo đúng tên, kích thước và mã xác minh.','PAYLOAD_UNAVAILABLE')
            self.download(url,target,meta['size'],meta['sha256'],event_cb,operation_id)
        manifest['source_metadata']=binding;atomic_json(stage/'patch_manifest.json',manifest);return stage
    def get_supporter_data(self):return SupporterData(status='unavailable',supporters=[],qr_placeholder_text='Thông tin thanh toán do người dùng cung cấp. Danh sách người đồng hành hiện chưa có nguồn dữ liệu.')
