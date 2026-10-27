"""Typed panels from the original manifest, preserving their authored decoration."""
from PySide6.QtCore import QRectF,Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QFrame
from ..assets import AssetManager
class GlassCard(QFrame):
    def __init__(self,parent=None,border_color=None,bg_color=None,decorated=True,asset_id='panels/plain'):
        super().__init__(parent);self.asset_id=asset_id;self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);AssetManager.get().paint(p,self.asset_id,QRectF(self.rect()))
        if self.asset_id=='panels/plain' and not AssetManager.get().meta(self.asset_id).get('avoid_r04_ornament_overlays'):AssetManager.get().paint(p,'decor/corner_bottom_right',QRectF(self.width()-170,self.height()-94,166,91),'contain')
