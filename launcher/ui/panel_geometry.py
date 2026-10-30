"""Whole-image panel geometry from the reviewed immutable asset manifest."""
from functools import lru_cache
import json
from PySide6.QtCore import QRectF
from .assets import AssetManager
KINDS={'notice':'01_notice','action':'02_install','update':'03_update','guide':'04_guide','support':'05_support','confirm':'06_confirm','dialog':'06_confirm','large':'04_guide'}
@lru_cache(maxsize=1)
def panel_manifest():
    folder=AssetManager.get().ui_dir/'journey_panels_r01'
    data=json.loads((folder/'ASSET_MANIFEST.json').read_text(encoding='utf8'))
    return {a['id']:a for a in data['assets']}
def panel_meta(kind):return panel_manifest()[KINDS[kind]]
def panel_target(rect,kind):
    r=QRectF(rect);w,h=panel_meta(kind)['size_px'];scale=max(0.,min(r.width()/w,r.height()/h))
    target=QRectF(0,0,w*scale,h*scale);target.moveCenter(r.center());return target
def panel_content_rect(rect,kind):
    t=panel_target(rect,kind);m=panel_meta(kind);scale=t.width()/m['size_px'][0];x1,y1,x2,y2=m['content_rect_xyxy']
    return QRectF(t.left()+x1*scale,t.top()+y1*scale,(x2-x1)*scale,(y2-y1)*scale)
def panel_height(width,kind):
    w,h=panel_meta(kind)['size_px'];return round(width*h/w)
