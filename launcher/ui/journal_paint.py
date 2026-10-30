"""Resizable, text-free travel-journal surfaces for the launcher."""
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPen, QPainter, QFont

INK = QColor('#334b83')
PAPER = QColor('#fbf8ef')
TEAL = QColor('#10bdc6')

def panel(p, rect):
    r = QRectF(rect).adjusted(1,1,-1,-1)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor('#b4a98f'), 1)); p.setBrush(QColor('#e7dfce')); p.drawRoundedRect(r, 13, 13)
    inner=r.adjusted(5,5,-5,-5)
    p.setPen(QPen(QColor('#d2c5aa'),1));p.setBrush(PAPER);p.drawRoundedRect(inner,9,9)
    # Small corner trim remains outside the content region at every size.
    p.setPen(QPen(QColor('#d7c9ad'),1,Qt.PenStyle.DashLine));p.setBrush(Qt.BrushStyle.NoBrush);p.drawRoundedRect(inner.adjusted(4,4,-4,-4),7,7)
    p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#e9e5d7'));p.drawEllipse(QRectF(inner.left()+3,inner.bottom()-17,16,12));p.drawEllipse(QRectF(inner.left()+13,inner.bottom()-15,18,10))
    p.setBrush(QColor('#20bfc9'));p.drawRoundedRect(QRectF(inner.right()-20,inner.top()+3,16,4),2,2)

# Source rectangles and decorative caps describe the unchanged RGBA images.
# Caps cover the artwork at each corner; their destination scale is uniform.
_PANEL_ART = {
    'notice': ('panel_notice_r02.png', (1920, 819), (36, 35, 1890, 760), (500, 340, 500, 300)),
    'action': ('panel_action_r02.png', (1774, 887), (26, 52, 1748, 800), (500, 355, 500, 330)),
    'dialog': ('panel_dialog.png', (1774, 887), (34, 71, 1764, 771), (450, 430, 350, 240)),
    'large': ('panel_large_r02.png', (1774, 887), (20, 23, 1760, 843), (600, 400, 550, 350)),
}

def whole_target(rect,kind):
    from .panel_geometry import panel_target
    return panel_target(rect,kind)

def panel_asset(p,rect,kind,modal=False,compact=False):
    """Paint the full PNG uniformly; the same target drives content layout."""
    from .assets import AssetManager
    from .panel_geometry import panel_meta,panel_target,KINDS
    if kind not in KINDS:return False
    a=AssetManager.get();m=panel_meta(kind);path=a.ui_dir/'journey_panels_r01'/(m['id']+'.png')
    pix=a.get_pixmap(str(path))
    if pix.isNull():return False
    target=panel_target(rect,kind)
    if target.width()<=0 or target.height()<=0:return False
    p.save();p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,True)
    p.drawPixmap(target,pix,QRectF(pix.rect()));p.restore();return True


def button(p, rect, variant, state):
    r=QRectF(rect).adjusted(1,1,-1,-1)
    active = variant == 'primary' or state == 'selected'
    colors={'normal':('#f9f7ed','#b7aa91'),'hover':('#fbf2df','#aa9875'),'pressed':('#e8deca','#a6977e'),'selected':('#51d2d4','#8abfba'),'disabled':('#e1ded7','#b5afa5')}
    fill,border=colors.get(state,colors['normal'])
    if variant=='primary' and state not in ('disabled','pressed'):fill='#58d4d7' if state!='hover' else '#9be8e4'
    if variant=='primary' and state=='pressed':fill='#27b2bf'
    if variant=='danger' and state!='disabled':fill,border=('#f5d5cc','#a66265')
    p.setRenderHint(QPainter.RenderHint.Antialiasing,True);p.setPen(QPen(QColor(border),2));p.setBrush(QColor(fill));p.drawRoundedRect(r,8,8)
    p.setPen(QPen(QColor('#d8cbb3'),1,Qt.PenStyle.DashLine));p.setBrush(Qt.BrushStyle.NoBrush);p.drawRoundedRect(r.adjusted(4,4,-4,-4),5,5)
    return active

def field(p, rect, state='normal'):
    p.setRenderHint(QPainter.RenderHint.Antialiasing,True);p.setPen(QPen(QColor('#09afbc' if state=='selected' else ('#b6a379' if state=='hover' else '#c5bba7')),1));p.setBrush(QColor('#f1f4f6'));p.drawRoundedRect(QRectF(rect).adjusted(1,1,-1,-1),8,8)

def row(p,rect,state='normal'):
    p.setRenderHint(QPainter.RenderHint.Antialiasing,True);p.setPen(QPen(QColor('#d4cab6'),1));p.setBrush(QColor('#dceef0' if state in ('selected','hover') else '#f5f2eb'));p.drawRoundedRect(QRectF(rect).adjusted(1,1,-1,-1),8,8)


def badge(p, rect, kind):
    palette={'project':'#cdecef','guide':'#d5e6f5','notice':'#f6e4c9','feedback':'#efdbe0'}
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor('#c4b79e'),1));p.setBrush(QColor(palette.get(kind,'#cdecef')))
    p.drawRoundedRect(QRectF(rect).adjusted(1,1,-1,-1),6,6)

def indicator(p,rect,checked=False,disabled=False,toggle=False):
    r=QRectF(rect).adjusted(2,3,-2,-3)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    border=QColor('#b8b2a8' if disabled else '#b1a48e')
    p.setPen(QPen(border,1.4));p.setBrush(QColor('#ddd8cf' if disabled else ('#4ac8ce' if checked else '#f6f5ef')))
    if toggle:
        p.drawRoundedRect(r,r.height()/2,r.height()/2)
        diameter=max(0,r.height()-4);x=r.right()-diameter-2 if checked else r.left()+2
        p.setPen(QPen(border,1));p.setBrush(QColor('#f8f7ef'));p.drawEllipse(QRectF(x,r.top()+2,diameter,diameter))
    else:
        side=min(r.width(),r.height());box=QRectF(r.left()+(r.width()-side)/2,r.top()+(r.height()-side)/2,side,side)
        p.drawRoundedRect(box,4,4)
        if checked:
            p.setPen(QPen(QColor('#6e798d' if disabled else '#263e72'),2.3))
            p.drawLine(QPointF(box.left()+side*.22,box.top()+side*.52),QPointF(box.left()+side*.43,box.top()+side*.72))
            p.drawLine(QPointF(box.left()+side*.43,box.top()+side*.72),QPointF(box.left()+side*.80,box.top()+side*.30))

def scroll_part(p,rect,thumb):
    r=QRectF(rect).adjusted(3,2,-3,-2)
    if r.width()<=0 or r.height()<=0:return
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True);p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor('#baa98d' if thumb else '#e9e3d7'));p.drawRoundedRect(r,r.width()/2,r.width()/2)

def status(p,rect,name):
    colors={'online':'#19b4a7','offline':'#9eaac1','warning':'#d99e38','error':'#cd6b6b','busy':'#4f8abb'}
    r=QRectF(rect);side=min(r.width(),r.height())*.65
    d=QRectF(r.center().x()-side/2,r.center().y()-side/2,side,side)
    p.setRenderHint(QPainter.RenderHint.Antialiasing,True);p.setPen(QPen(QColor('#f9f7ef'),1));p.setBrush(QColor(colors.get(name,'#9eaac1')));p.drawEllipse(d)

def step(p,rect,number,state):
    r=QRectF(rect);side=max(0,min(r.width(),r.height())-3);r=QRectF(r.center().x()-side/2,r.center().y()-side/2,side,side)
    p.setRenderHint(QPainter.RenderHint.Antialiasing,True)
    border='#2caab5' if state=='current' else '#bdae94';fill='#b8e9e5' if state=='current' else ('#d4e9e8' if state=='done' else '#f9f7ef')
    p.setPen(QPen(QColor(border),1.5));p.setBrush(QColor(fill));p.drawEllipse(r)
    p.save()
    font=QFont('Baloo 2');font.setPixelSize(max(10,round(side*.43)));font.setWeight(QFont.Weight.DemiBold);p.setFont(font);p.setPen(QColor('#304679'));p.drawText(r,Qt.AlignmentFlag.AlignCenter,str(number))
    p.restore()

def avatar(p,rect):
    r=QRectF(rect).adjusted(2,2,-2,-2);p.setRenderHint(QPainter.RenderHint.Antialiasing,True);p.setPen(QPen(QColor('#c2b69e'),1));p.setBrush(QColor('#dbe9ed'));p.drawEllipse(r)
    p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#738db4'));p.drawEllipse(QRectF(r.left()+r.width()*.35,r.top()+r.height()*.21,r.width()*.3,r.height()*.3));p.drawRoundedRect(QRectF(r.left()+r.width()*.21,r.top()+r.height()*.56,r.width()*.58,r.height()*.23),3,3)


def ornaments(p, rect, modal=False, compact=False):
    """Scale separate transparent corner illustrations isotropically."""
    from .assets import AssetManager
    r=QRectF(rect)
    # These sizes fit the reserved widget content margins; small dialogs use
    # smaller ornaments. Clip to each box to avoid covering text and controls.
    w,h=((40.,32.) if compact else (96.,72.)) if modal else (55.,40.)
    w=min(w,r.width()/4);h=min(h,r.height()/4)
    specs=[('corner_topleft',QRectF(r.left()+2,r.top()+2,w,h),(1374,1145),(50,65,907,1008)),
           ('corner_bottomright',QRectF(r.right()-w-2,r.bottom()-h-2,w,h),(1536,1024),(480,344,1504,925))]
    manager=AssetManager.get()
    for name,box,original,bbox in specs:
        path=manager.ui_dir/'journey_r01'/'decor'/(name+'.png')
        if not path.is_file() or box.width()<=0 or box.height()<=0:continue
        pix=manager.journey_pixmap(path)
        if pix is None or pix.isNull():continue
        ow,oh=original;left,top,right,bottom=bbox
        src=QRectF(left*pix.width()/ow,top*pix.height()/oh,(right-left)*pix.width()/ow,(bottom-top)*pix.height()/oh)
        if src.width()<=0 or src.height()<=0:continue
        factor=min(box.width()/src.width(),box.height()/src.height())
        target=QRectF(0,0,src.width()*factor,src.height()*factor);target.moveCenter(box.center())
        p.save();p.setClipRect(box,Qt.ClipOperation.IntersectClip);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,True)
        p.drawPixmap(target,pix,src);p.restore()
