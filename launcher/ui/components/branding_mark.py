"""Paint the supplied Việt Hoá flag directly from its full master pixels."""
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget
from ..assets import AssetManager
class BrandingMark(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.setAccessibleName('Việt Hoá');self.setToolTip('Việt Hoá')
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);assets=AssetManager.get();master=assets.get_pixmap(str(assets.branding_dir/'app_icon.png'))
        if master.isNull():return
        scale=min(self.width()/master.width(),self.height()/master.height());target=QRectF(0,0,master.width()*scale,master.height()*scale);target.moveCenter(QRectF(self.rect()).center());painter.drawPixmap(target,master,QRectF(master.rect()))
