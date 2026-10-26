"""Six-state supplied button artwork with native text, icon and keyboard behavior."""
from PySide6.QtCore import Qt,QRectF,QSize
from PySide6.QtGui import QPainter,QFont,QColor,QIcon,QPen
from PySide6.QtWidgets import QPushButton
from ..assets import AssetManager
class StarlitButton(QPushButton):
    def __init__(self,text='',variant='primary',icon=None,parent=None):
        super().__init__(text,parent);self.variant=variant;self.art_icon_name=icon if isinstance(icon,str) else None;self.setCursor(Qt.CursorShape.PointingHandCursor);self.setFocusPolicy(Qt.FocusPolicy.StrongFocus);self.setMinimumHeight(38 if variant in ('ghost','square') else 42);self.setMouseTracking(True)
        f=QFont('Segoe UI',10);f.setWeight(QFont.Weight.DemiBold);self.setFont(f)
        if icon:self.setIcon(AssetManager.get().get_icon(icon) if isinstance(icon,str) else icon)
        self.setIconSize(QSize(22,22));self.setAccessibleName(text or 'Thao tác')
        self.setStyleSheet('QPushButton{background:transparent;border:0;padding:0;}')
    def sizeHint(self):return QSize(max(42,self.fontMetrics().horizontalAdvance(self.text())+(32 if not self.icon().isNull() else 0)+44),44)
    def set_variant(self,v):self.variant=v;self.update()
    def enterEvent(self,e):self.update();super().enterEvent(e)
    def leaveEvent(self,e):self.update();super().leaveEvent(e)
    def focusInEvent(self,e):self.update();super().focusInEvent(e)
    def focusOutEvent(self,e):self.update();super().focusOutEvent(e)
    def paintEvent(self,event):
        a=AssetManager.get();p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);rect=QRectF(self.rect())
        state='disabled' if not self.isEnabled() else ('pressed' if self.isDown() else ('selected' if self.isChecked() else ('focus' if self.hasFocus() else ('hover' if self.underMouse() else 'normal'))))
        if self.variant!='ghost':
            aid='buttons/'+self.variant+'_'+state;a.paint(p,aid,rect);content=a.content_rect(aid,rect)
        else:
            content=rect.adjusted(8,2,-8,-2)
            if self.isDown() or self.underMouse() or self.hasFocus():p.fillRect(content,QColor(70,170,235,25))
        light=self.variant in ('primary','tab') and (self.variant=='primary' or self.isChecked()) and self.isEnabled();color=QColor('#073253' if light else ('#f0f7ff' if self.isEnabled() else '#7196b5'))
        p.setPen(color);p.setFont(self.font());fm=p.fontMetrics();iconwidth=self.iconSize().width() if not self.icon().isNull() else 0;gap=8 if iconwidth and self.text() else 0
        text=fm.elidedText(self.text(),Qt.TextElideMode.ElideRight,max(0,int(content.width())-iconwidth-gap));tw=fm.horizontalAdvance(text);whole=tw+iconwidth+gap;left=content.center().x()-whole/2
        if iconwidth:
            mode=QIcon.Mode.Disabled if not self.isEnabled() else (QIcon.Mode.Active if self.underMouse() else QIcon.Mode.Normal)
            pix=a.get_icon_pixmap(self.art_icon_name,'ink' if light or not self.isEnabled() else ('cyan' if self.underMouse() else 'white')) if self.art_icon_name else self.icon().pixmap(self.iconSize(),mode);p.drawPixmap(QRectF(left,content.center().y()-iconwidth/2,iconwidth,iconwidth),pix,QRectF(pix.rect()));left+=iconwidth+gap
        p.drawText(QRectF(left,content.top(),tw+1,content.height()),Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft,text)
        if self.hasFocus():p.setPen(QPen(QColor('#8deaff'),1,Qt.PenStyle.DashLine));p.drawRoundedRect(rect.adjusted(5,5,-5,-5),7,7)
