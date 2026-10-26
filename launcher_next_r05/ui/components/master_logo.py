"""Paint directly from the full master image. No logical-sized intermediate pixmap."""
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget
from ..assets import AssetManager
class MasterLogo(QWidget):
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);master=AssetManager.get().get_logo()
        if master.isNull():return
        scale=min(self.width()/master.width(),self.height()/master.height());target=QRectF(0,0,master.width()*scale,master.height()*scale)
        painter.drawPixmap(target,master,QRectF(master.rect()))
