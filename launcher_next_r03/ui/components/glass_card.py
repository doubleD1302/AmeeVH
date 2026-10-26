"""Supplied nine-slice glass panel with separate proportional leaf/star decorations."""
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QPainter,QColor
from PySide6.QtWidgets import QFrame
from ..assets import AssetManager

def nine_patch(painter,rect,pix,insets=(36,36,36,36),scale=2):
    if pix.isNull():return
    l,t,r,b=insets;w=rect.width();h=rect.height();l=min(l,w/3);r=min(r,w/3);t=min(t,h/3);b=min(b,h/3)
    sx=[0,insets[0]*scale,pix.width()-insets[2]*scale,pix.width()];sy=[0,insets[1]*scale,pix.height()-insets[3]*scale,pix.height()]
    dx=[rect.x(),rect.x()+l,rect.right()-r,rect.right()];dy=[rect.y(),rect.y()+t,rect.bottom()-b,rect.bottom()]
    for y in range(3):
        for x in range(3):painter.drawPixmap(QRectF(dx[x],dy[y],dx[x+1]-dx[x],dy[y+1]-dy[y]),pix,QRectF(sx[x],sy[y],sx[x+1]-sx[x],sy[y+1]-sy[y]))
class GlassCard(QFrame):
    def __init__(self,parent=None,border_color='#1f568a',bg_color='rgba(8,26,48,0.95)',decorated=True):
        super().__init__(parent);self.decorated=decorated;self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        a=AssetManager.get();nine_patch(p,QRectF(self.rect()),a.get_component_pixmap('panels','plain',2))
        if self.decorated:
            leaves=a.get_component_pixmap('decor','leaves',2);star=a.get_component_pixmap('decor','star_large',2)
            p.drawPixmap(QRectF(self.width()-118,self.height()-65,114,63),leaves,QRectF(leaves.rect()))
            p.drawPixmap(QRectF(2,2,34,34),star,QRectF(star.rect()))
