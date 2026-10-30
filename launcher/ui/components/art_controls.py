"""Real Qt controls styled with authored assets; values come from real providers."""
from __future__ import annotations
from PySide6.QtCore import Qt,QRectF,QSize,QTimer
from PySide6.QtGui import QPainter,QColor,QFont,QPen
from PySide6.QtWidgets import QWidget,QLabel,QLineEdit,QCheckBox,QScrollBar,QProgressBar,QStyleOptionSlider,QStyle,QPushButton,QVBoxLayout,QHBoxLayout,QScrollArea,QFrame,QLayout,QSizePolicy
from ..assets import AssetManager
from ..typography import font as ui_font

def text_label(text='',size=15,color='#eef7ff',bold=False,wrap=False):
    if color.startswith('#') and len(color)==7:
        c=QColor(color)
        if c.lightness()>130:color='#405682'
    w=QLabel(text);w.setTextFormat(Qt.TextFormat.PlainText);w.setWordWrap(wrap);w.setMinimumWidth(0);w.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred);size=13 if size<13 else (15 if size==14 else (20 if size==17 else size));f=ui_font(size,(QFont.Weight.Bold if size>=20 else QFont.Weight.DemiBold) if bold else QFont.Weight.Normal);w.setFont(f);w.setStyleSheet('color:'+color+';background:transparent;');return w
class AssetImage(QWidget):
    def __init__(self,asset_id,size=24,parent=None):super().__init__(parent);self.asset_id=asset_id;self.setFixedSize(size,size)
    def paintEvent(self,e):p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);AssetManager.get().paint(p,self.asset_id,QRectF(self.rect()),'contain')
class ArtDivider(QWidget):
    def __init__(self,parent=None):super().__init__(parent);self.setFixedHeight(14)
    def paintEvent(self,e):p=QPainter(self);p.setPen(QPen(QColor(190,174,146,120),1));p.drawLine(0,self.height()//2,self.width(),self.height()//2)
class Badge(QLabel):
    def __init__(self,text='Dự án',kind='project',parent=None):super().__init__(text,parent);self.kind=kind if kind in ('project','guide','notice','feedback') else 'project';self.setFixedSize(90,29);self.setFont(ui_font(13,QFont.Weight.DemiBold))
    def paintEvent(self,e):p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);AssetManager.get().paint(p,'badges/'+self.kind,QRectF(self.rect()),'stretch');p.setPen(QColor('#073454'));p.setFont(self.font());p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,self.text())
class ArtInput(QLineEdit):
    def __init__(self,text='',placeholder='',icon='search',parent=None):
        super().__init__(text,parent);self.art_icon=icon;self.setPlaceholderText(placeholder);self.setMinimumHeight(42);self.setTextMargins(40,0,14,0);self.setStyleSheet('QLineEdit{background:transparent;border:0;color:#304679;font-size:17px;padding:0;selection-background-color:#45caff;selection-color:#06223c;}');self.setMouseTracking(True)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);a=AssetManager.get();state='disabled' if not self.isEnabled() else ('selected' if self.hasFocus() else ('hover' if self.underMouse() else 'normal'));__import__('launcher.ui.journal_paint',fromlist=['field']).field(p,QRectF(self.rect()),state);a.paint(p,'icons/'+self.art_icon+'_ink',QRectF(12,(self.height()-24)/2,24,24),'contain');p.end();super().paintEvent(e)
class ArtScrollBar(QScrollBar):
    def __init__(self,orientation=Qt.Orientation.Vertical,parent=None):super().__init__(orientation,parent);self.setFixedWidth(14);self.setStyleSheet('QScrollBar{background:transparent;border:0;margin:0;}')
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);a=AssetManager.get();o=QStyleOptionSlider();self.initStyleOption(o);groove=self.style().subControlRect(QStyle.ComplexControl.CC_ScrollBar,o,QStyle.SubControl.SC_ScrollBarGroove,self);thumb=self.style().subControlRect(QStyle.ComplexControl.CC_ScrollBar,o,QStyle.SubControl.SC_ScrollBarSlider,self);a.paint(p,'controls/scrollbar_track',QRectF(groove),'stretch')
        if self.maximum()>self.minimum():a.paint(p,'controls/scrollbar_thumb',QRectF(thumb),'stretch')
class WidthScrollArea(QScrollArea):
    """Reflow to viewport width and use vertical scrolling only."""
    def __init__(self):
        super().__init__();self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumWidth(0);self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.viewport().installEventFilter(self)
    def _fit_width(self):
        w=self.widget()
        if w is not None:
            if w.layout():w.layout().setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
            width=max(1,self.viewport().width())
            if w.width()!=width or w.minimumWidth()!=width:w.setFixedWidth(width)
    def eventFilter(self,obj,event):
        from PySide6.QtCore import QEvent
        if obj is self.viewport() and event.type()==QEvent.Type.Resize:self._fit_width()
        return super().eventFilter(obj,event)
    def resizeEvent(self,event):
        super().resizeEvent(event);self._fit_width()

def scroll_area(widget=None):
    s=WidthScrollArea();s.setWidgetResizable(True);s.setFrameShape(QFrame.Shape.NoFrame);s.setStyleSheet('QScrollArea{background:transparent;border:0;}QScrollArea>QWidget>QWidget{background:transparent;}');s.setVerticalScrollBar(ArtScrollBar())
    if widget is not None:s.setWidget(widget)
    return s
class ArtProgress(QProgressBar):
    def __init__(self,parent=None):super().__init__(parent);self.setFixedHeight(14);self.setRange(0,100);self.setTextVisible(False)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing,True)
        r=QRectF(self.rect()).adjusted(1,1,-1,-1);p.setPen(QPen(QColor('#c8bba3'),1));p.setBrush(QColor('#eee7da'));p.drawRoundedRect(r,6,6)
        ratio=max(0,min(1,(self.value()-self.minimum())/(self.maximum()-self.minimum()))) if self.maximum()>self.minimum() else 0
        if ratio>0:
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#13c2c8'));fill=QRectF(r.left()+2,r.top()+2,max(0,(r.width()-4)*ratio),max(0,r.height()-4));p.drawRoundedRect(fill,4,4)
class Spinner(QWidget):
    def __init__(self,parent=None):super().__init__(parent);self.setFixedSize(26,26);self.frame=0;self.timer=QTimer(self);self.timer.setInterval(80);self.timer.timeout.connect(self._advance);self.hide()
    def _advance(self):self.frame=(self.frame+1)%12;self.update()
    def start(self,reduced_motion=False):self.show();self.frame=0;self.timer.stop();self.timer.start() if not reduced_motion else None
    def stop(self):self.timer.stop();self.hide()
    def paintEvent(self,e):p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing,True);p.setPen(QPen(QColor('#12b6bf'),3));p.drawArc(self.rect().adjusted(4,4,-4,-4),self.frame*30*16,220*16)
class ArtCheckBox(QCheckBox):
    def __init__(self,text='',parent=None,toggle=False):super().__init__(text,parent);self.toggle=toggle;self.setMinimumHeight(40);self.setMinimumWidth(0);self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred);self.setCursor(Qt.CursorShape.PointingHandCursor);self.setFont(ui_font(15));self._keyboard_focus=False;self.setStyleSheet('background:transparent;color:#e8f6ff;')
    def sizeHint(self):return QSize(self.fontMetrics().horizontalAdvance(self.text())+(74 if self.toggle else 46),48)
    def minimumSizeHint(self):return QSize(0,48)
    def paintEvent(self,e):
        p=QPainter(self);a=AssetManager.get();indicator=52 if self.toggle else 28
        aid=('controls/toggle_'+('disabled_' if not self.isEnabled() else '')+('on' if self.isChecked() else 'off')) if self.toggle else ('controls/checkbox_'+('disabled_' if not self.isEnabled() else '')+('checked' if self.isChecked() else 'empty'))
        a.paint(p,aid,QRectF(0,(self.height()-28)/2,indicator,28),'contain');p.setPen(QColor('#304679' if self.isEnabled() else '#8490a5'));p.setFont(self.font());p.drawText(QRectF(indicator+10,0,self.width()-indicator-10,self.height()),Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft|Qt.TextFlag.TextWordWrap,self.text())
        if self.hasFocus() and self._keyboard_focus:p.setPen(QPen(QColor('#8deaff'),1));p.drawRoundedRect(self.rect().adjusted(1,1,-2,-2),5,5)
    def focusInEvent(self,e):self._keyboard_focus=e.reason() in (Qt.FocusReason.TabFocusReason,Qt.FocusReason.BacktabFocusReason,Qt.FocusReason.ShortcutFocusReason);self.update();super().focusInEvent(e)
class AlertStrip(QWidget):
    def __init__(self,message='',kind='info',parent=None):
        super().__init__(parent);self.kind=kind;l=QHBoxLayout(self);l.setContentsMargins(14,9,14,9);l.setSpacing(9);self.icon=AssetImage('icons/'+('info' if kind in ('info','success') else 'warning')+'_cyan',22);l.addWidget(self.icon);self.label=text_label(message,13,wrap=True);l.addWidget(self.label,1)
    def setText(self,t):self.label.setText(t)
    def paintEvent(self,e):p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing,True);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,True);AssetManager.get().paint(p,'controls/alert_'+self.kind,QRectF(self.rect()))
class StatusPill(QWidget):
    def __init__(self,text='Chưa kiểm tra kết nối',state='offline',parent=None):super().__init__(parent);self.text=text;self.state=state;self.setMinimumHeight(32)
    def setText(self,text):self.text=text;self.update()
    def set_status(self,text,state):self.text=text;self.state=state if state in ('online','offline','warning','error','busy') else 'offline';self.setToolTip(text);self.update()
    def paintEvent(self,e):
        p=QPainter(self);a=AssetManager.get();a.paint(p,'status/'+self.state,QRectF(3,(self.height()-18)/2,18,18),'contain');p.setPen(QColor('#304679'));f=ui_font(15);p.setFont(f);text=p.fontMetrics().elidedText(self.text,Qt.TextElideMode.ElideRight,max(0,self.width()-30));p.drawText(QRectF(28,0,self.width()-30,self.height()),Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft,text)
class RichRow(QPushButton):
    def __init__(self,title,summary='',badge_text='',badge_kind='project',icon='chevron_right',parent=None):
        super().__init__('',parent);self.title=title;self.summary=summary;self.badge_text=badge_text;self.badge_kind=badge_kind;self.art_icon=icon;self.setCheckable(True);self.setMinimumHeight(88);self.setCursor(Qt.CursorShape.PointingHandCursor);self.setFocusPolicy(Qt.FocusPolicy.StrongFocus);self.setToolTip(title+'\n'+summary);self.setAccessibleName(title);self.setStyleSheet('background:transparent;border:0;');self.setMouseTracking(True)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);a=AssetManager.get();state='disabled' if not self.isEnabled() else ('selected' if self.isChecked() or self.hasFocus() else ('hover' if self.underMouse() else 'normal'));a.paint(p,'controls/list_row_'+state,QRectF(self.rect()));x=18
        if self.badge_text:
            a.paint(p,'badges/'+self.badge_kind,QRectF(15,17,78,25),'stretch');f=ui_font(13,QFont.Weight.DemiBold);p.setFont(f);p.setPen(QColor('#073454'));p.drawText(QRectF(15,17,78,25),Qt.AlignmentFlag.AlignCenter,self.badge_text);x=106
        f=ui_font(15,QFont.Weight.DemiBold);p.setFont(f);p.setPen(QColor('#304679'));width=max(30,self.width()-x-35);p.drawText(QRectF(x,14,width,29),Qt.AlignmentFlag.AlignVCenter,p.fontMetrics().elidedText(self.title,Qt.TextElideMode.ElideRight,width));f=ui_font(13);p.setFont(f);p.setPen(QColor('#637596'));p.drawText(QRectF(x,43,width,28),Qt.AlignmentFlag.AlignVCenter,p.fontMetrics().elidedText(self.summary,Qt.TextElideMode.ElideRight,width));a.paint(p,'icons/'+self.art_icon+'_white',QRectF(self.width()-29,(self.height()-20)/2,20,20),'contain')
class ArtTableRow(QWidget):
    def __init__(self,name,tier,date,message='',index=0,parent=None):
        super().__init__(parent);self.index=index;self.setMinimumHeight(46);self.setMouseTracking(True);l=QHBoxLayout(self);l.setContentsMargins(10,3,12,3);avatar=AssetImage('controls/avatar',30);l.addWidget(avatar);l.addWidget(text_label(name,13),3);l.addWidget(text_label(tier,13,'#7ae4ff'),2);l.addWidget(text_label(date,11,'#a4c9e7'),2);self.setToolTip(message)
    def paintEvent(self,e):
        p=QPainter(self);state='hover' if self.underMouse() else ('odd' if self.index%2 else 'even');AssetManager.get().paint(p,'controls/table_row_'+state,QRectF(self.rect()),'stretch')

    def enterEvent(self,e):self.update();super().enterEvent(e)
    def leaveEvent(self,e):self.update();super().leaveEvent(e)
class SectionRule(ArtDivider):
    def paintEvent(self,e):super().paintEvent(e)
