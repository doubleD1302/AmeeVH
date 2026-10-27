"""Precision-skin buttons: uniform slanted tabs, readable disabled state and real icons."""
from PySide6.QtCore import Qt,QRectF,QSize
from PySide6.QtGui import QPainter,QColor,QFont,QIcon,QPen
from PySide6.QtWidgets import QPushButton
from ..assets import AssetManager
from ..typography import font
class StarlitButton(QPushButton):
    def __init__(self,text='',variant='primary',icon=None,parent=None):
        super().__init__(text,parent);self.variant=variant;self.art_icon_name=icon if isinstance(icon,str) else None;self.icon_side='left';self.text_alignment='center';self.caption_wrap=False;self.stretch_background=False;self._keyboard_focus=False;self.setCursor(Qt.CursorShape.PointingHandCursor);self.setFocusPolicy(Qt.FocusPolicy.StrongFocus);self.setMinimumHeight(40 if variant in ('ghost','square') else 44);self.setMouseTracking(True);self.setFont(font(16,QFont.Weight.DemiBold));self.setIconSize(QSize(24,24));self.setAccessibleName(text or 'Thao tác')
        if icon:self.setIcon(AssetManager.get().get_icon(icon) if isinstance(icon,str) else icon)
        self.setStyleSheet('QPushButton{background:transparent;border:0;padding:0;}')
    def sizeHint(self):return QSize(max(44,self.fontMetrics().horizontalAdvance(self.text())+(32 if not self.icon().isNull() else 0)+36),46)
    def set_variant(self,value):self.variant=value;self.update()
    def enterEvent(self,e):self.update();super().enterEvent(e)
    def leaveEvent(self,e):self.update();super().leaveEvent(e)
    def focusInEvent(self,e):self._keyboard_focus=e.reason() in (Qt.FocusReason.TabFocusReason,Qt.FocusReason.BacktabFocusReason,Qt.FocusReason.ShortcutFocusReason);self.update();super().focusInEvent(e)
    def focusOutEvent(self,e):self._keyboard_focus=False;self.update();super().focusOutEvent(e)
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing,True);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,True);painter.setRenderHint(QPainter.RenderHint.TextAntialiasing,True);assets=AssetManager.get();rect=QRectF(self.rect());focus=self.hasFocus() and self._keyboard_focus
        state='disabled' if not self.isEnabled() else ('pressed' if self.isDown() else ('selected' if self.isChecked() else ('focus' if focus else ('hover' if self.underMouse() else 'normal'))))
        if self.variant=='tab' and state=='focus' and not self.isChecked():state='hover'
        if self.variant!='ghost':
            aid='buttons/'+self.variant+'_'+state
            assets.paint(painter,aid,rect,'stretch' if self.stretch_background else 'nine')
            if self.stretch_background:
                meta=assets.meta(aid);box=meta['content_rect'];sx=rect.width()/meta['width'];sy=rect.height()/meta['height']
                content=QRectF(rect.left()+box[0]*sx,rect.top()+box[1]*sy,box[2]*sx,box[3]*sy)
            else:content=assets.content_rect(aid,rect)
        else:
            content=rect.adjusted(5,3,-5,-3)
            if self.isEnabled() and (self.isDown() or self.underMouse()):painter.fillRect(content,QColor(70,170,235,24))
        light=self.isEnabled() and (self.variant=='primary' or (self.variant=='tab' and self.isChecked()));painter.setPen(QColor('#073253' if light else ('#f0f7ff' if self.isEnabled() else '#b2cde3')));iconw=self.iconSize().width() if not self.icon().isNull() else 0;gap=8 if iconw and self.text() else 0;available=max(0,int(content.width())-iconw-gap)
        display_font=QFont(self.font());painter.setFont(display_font);fm=painter.fontMetrics()
        # Resize action captions rather than clipping them at higher DPI or in
        # narrower windows. Notification titles may still elide with a tooltip.
        if self.icon_side!='far_right' and not self.caption_wrap:
            while fm.horizontalAdvance(self.text())>available and display_font.pixelSize()>11:
                display_font.setPixelSize(display_font.pixelSize()-1);painter.setFont(display_font);fm=painter.fontMetrics()
        label=self.text() if self.caption_wrap else fm.elidedText(self.text(),Qt.TextElideMode.ElideRight,available);textw=available if self.caption_wrap else min(available,fm.horizontalAdvance(label))
        if self.icon_side=='far_right':
            textrect=QRectF(content.left(),content.top(),max(0,content.width()-iconw-gap),content.height());iconrect=QRectF(content.right()-iconw,content.center().y()-iconw/2,iconw,iconw)
        else:
            whole=textw+iconw+gap;left=content.left() if self.text_alignment=='left' else content.center().x()-whole/2
            if self.icon_side=='right':textrect=QRectF(left,content.top(),textw+1,content.height());iconrect=QRectF(left+textw+gap,content.center().y()-iconw/2,iconw,iconw)
            else:iconrect=QRectF(left,content.center().y()-iconw/2,iconw,iconw);textrect=QRectF(left+iconw+gap,content.top(),textw+1,content.height())
        if iconw:
            if self.art_icon_name:pix=assets.get_icon_pixmap(self.art_icon_name,'muted' if not self.isEnabled() else ('ink' if light else ('cyan' if self.underMouse() else 'white')))
            else:pix=self.icon().pixmap(self.iconSize(),QIcon.Mode.Disabled if not self.isEnabled() else QIcon.Mode.Normal)
            painter.drawPixmap(iconrect,pix,QRectF(pix.rect()))
        painter.drawText(textrect,Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft|(Qt.TextFlag.TextWordWrap if self.caption_wrap else Qt.TextFlag.TextSingleLine),label)
        if focus:painter.setPen(QPen(QColor('#a4efff'),1));painter.drawRoundedRect(rect.adjusted(3,3,-3,-3),6,6)
