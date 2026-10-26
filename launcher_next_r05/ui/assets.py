"""Manifest-driven asset lookup, content geometry and nine-slice painting."""
from __future__ import annotations
import json,logging
from pathlib import Path
from PySide6.QtCore import Qt,QRectF,QMargins
from PySide6.QtGui import QPixmap,QIcon
logger=logging.getLogger('launcher.assets')
class AssetManager:
    _instance=None
    def __init__(self,resource_dir):
        self.resource_dir=Path(resource_dir);self.ui_dir=self.resource_dir/'ui';self.branding_dir=self.resource_dir/'branding';self._cache={};self._icons={}
        self.manifest=json.loads((self.ui_dir/'asset_manifest.json').read_text(encoding='utf8'));self.entries={a['id']:a for a in self.manifest['assets']};self.supplement_dir=self.ui_dir/'supplemental'
        extra=json.loads((self.supplement_dir/'asset_manifest.json').read_text(encoding='utf8'))
        self.entries.update({a['id']:{**a,'_supplement':True} for a in extra['assets']})
        self.skin_dir=self.ui_dir/'skin_r05';self.skin=json.loads((self.skin_dir/'asset_manifest.json').read_text(encoding='utf8'));self.entries.update({a['id']:{**a,'_skin':True} for a in self.skin['assets']})
    @classmethod
    def initialize(cls,p):cls._instance=cls(p);return cls._instance
    @classmethod
    def get(cls):
        if cls._instance is None:raise RuntimeError('Asset manager was not initialized')
        return cls._instance
    def meta(self,asset_id):return self.entries.get(asset_id,{})
    def get_pixmap(self,relative_path):
        if relative_path not in self._cache:
            f=self.ui_dir/relative_path
            if not f.is_file():f=self.branding_dir/relative_path
            pix=QPixmap(str(f))
            if pix.isNull():logger.error('Missing or invalid asset: %s',f)
            self._cache[relative_path]=pix
        return self._cache[relative_path]
    def pixmap(self,asset_id):
        m=self.entries[asset_id];rel=m.get('png_4x') or m.get('png_2x') or m['png'];return self.get_pixmap(str(self.skin_dir/rel) if m.get('_skin') else (str(self.supplement_dir/rel) if m.get('_supplement') else rel))
    def supplement(self,name):
        key='supplement:'+name
        if key not in self._cache:self._cache[key]=QPixmap(str(self.supplement_dir/name))
        return self._cache[key]
    def get_component_pixmap(self,category,name,scale=2):return self.pixmap(category+'/'+name)
    def get_icon_pixmap(self,name,color_variant='white'):return self.pixmap('icons/'+name+'_'+color_variant)
    def get_icon(self,name):
        if name not in self._icons:
            icon=QIcon()
            for suffix,mode in [('white',QIcon.Mode.Normal),('cyan',QIcon.Mode.Active),('muted',QIcon.Mode.Disabled)]:icon.addPixmap(self.get_icon_pixmap(name,suffix),mode)
            self._icons[name]=icon
        return self._icons[name]
    def get_background(self):return self.get_pixmap(str(self.skin_dir/self.skin['branding']['background']))
    def get_logo(self):return self.get_pixmap(str(self.skin_dir/self.skin['branding']['logo']))
    def get_app_icon(self):return QIcon(str(self.branding_dir/'app_icon.ico'))
    def has_skin(self,asset_id):return bool(self.meta(asset_id).get('_skin'))
    def fit_rect(self,asset_id,rect):
        rect=QRectF(rect);m=self.meta(asset_id);factor=min(rect.width()/m.get('width',1),rect.height()/m.get('height',1));fitted=QRectF(0,0,m.get('width',1)*factor,m.get('height',1)*factor);fitted.moveCenter(rect.center());return fitted
    def content_rect(self,asset_id,rect):
        m=self.meta(asset_id);box=m.get('content_rect',[0,0,m.get('width',1),m.get('height',1)]);w=m.get('width',1);h=m.get('height',1)
        if m.get('render_mode') in ('uniform','contain'):
            r=self.fit_rect(asset_id,rect);factor=r.width()/w;return QRectF(r.left()+box[0]*factor,r.top()+box[1]*factor,box[2]*factor,box[3]*factor)
        scale=min(1.,rect.width()/w,rect.height()/h)
        return rect.adjusted(box[0]*scale,box[1]*scale,-(w-box[0]-box[2])*scale,-(h-box[1]-box[3])*scale)
    def content_margins(self,asset_id,width,height):
        m=self.meta(asset_id);box=m.get('content_rect',[20,20,m.get('width',40)-40,m.get('height',40)-40]);w=m.get('width',1);h=m.get('height',1);s=min(1.,width/w,height/h)
        return QMargins(round(box[0]*s),round(box[1]*s),round((w-box[0]-box[2])*s),round((h-box[1]-box[3])*s))
    def paint(self,painter,asset_id,rect,mode='nine'):
        rect=QRectF(rect);pix=self.pixmap(asset_id);m=self.meta(asset_id)
        if mode=='nine' and m.get('render_mode') in ('uniform','contain'):mode='contain'
        if pix.isNull() or rect.width()<=0 or rect.height()<=0:return
        if mode=='contain':
            d=self.fit_rect(asset_id,rect);painter.drawPixmap(d,pix,QRectF(pix.rect()));return
        insets=m.get('slice_insets')
        if mode!='nine' or not insets:painter.drawPixmap(rect,pix,QRectF(pix.rect()));return
        source_scale=pix.width()/m['width'];corner_scale=min(1.,rect.width()/m['width'],rect.height()/m['height']);l,t,r,b=[v*corner_scale for v in insets]
        sx=[0,insets[0]*source_scale,pix.width()-insets[2]*source_scale,pix.width()];sy=[0,insets[1]*source_scale,pix.height()-insets[3]*source_scale,pix.height()]
        dx=[rect.left(),rect.left()+l,rect.right()-r,rect.right()];dy=[rect.top(),rect.top()+t,rect.bottom()-b,rect.bottom()]
        for y in range(3):
            for x in range(3):painter.drawPixmap(QRectF(dx[x],dy[y],dx[x+1]-dx[x],dy[y+1]-dy[y]),pix,QRectF(sx[x],sy[y],sx[x+1]-sx[x],sy[y+1]-sy[y]))
