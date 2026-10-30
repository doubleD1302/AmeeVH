"""Reference-aligned guide sidebar, connected steps and expandable FAQ."""
import json
from PySide6.QtCore import Qt,QRectF,QTimer,QUrl
from PySide6.QtGui import QPainter,QPen,QColor,QFont,QDesktopServices
from ..typography import font as ui_font
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QStackedWidget,QFrame,QGridLayout,QBoxLayout
from ..assets import AssetManager
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import AssetImage,ArtDivider,SectionRule,RichRow,AlertStrip,text_label,scroll_area
class StepChain(QWidget):
    def __init__(self,current=1,parent=None):super().__init__(parent);self.current=current;self.setMinimumHeight(102)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);a=AssetManager.get();xs=[self.width()*.17,self.width()*.5,self.width()*.83];p.setPen(QPen(QColor('#c9bba2'),1));p.drawLine(round(xs[0]),32,round(xs[2]),32)
        for index,(x,label) in enumerate(zip(xs,['Chọn thư mục','Cài bản dịch','Kiểm tra']),1):
            status='current' if index==self.current else ('done' if index<self.current else 'pending');a.paint(p,f'controls/step_{index}_{status}',QRectF(x-28,3,56,56),'contain');p.setPen(QColor('#304679' if index==self.current else '#637596'));p.setFont(ui_font(13));p.drawText(QRectF(x-self.width()/6+3,66,max(1,self.width()/3-6),34),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,label)
class InstructionCard(QWidget):
    def __init__(self,number,title,detail,parent=None):
        super().__init__(parent);l=QHBoxLayout(self);l.setContentsMargins(15,10,16,10);l.setSpacing(12);l.addWidget(AssetImage(f'controls/step_{number}_pending',38));text=QVBoxLayout();text.setSpacing(2);text.addWidget(text_label(title,16,bold=True,wrap=True));text.addWidget(text_label(detail,15,'#b6d7ef',wrap=True));l.addLayout(text,1);self.setMinimumHeight(125)
    def paintEvent(self,e):p=QPainter(self);AssetManager.get().paint(p,'controls/list_row_normal',QRectF(self.rect()))
class GuideModal(ArtDialog):
    def __init__(self,parent=None):
        super().__init__('Hướng dẫn','Cài đặt dễ dàng, bắt đầu nhanh chóng','book',parent,width=1160,height=790,panel='panels/guide');self.help_content=json.loads((AssetManager.get().ui_dir/'support_r09'/'help_content.json').read_text(encoding='utf8'));self.body_widget.setMinimumWidth(0);helpbtn=StarlitButton('Hỗ trợ',variant='ghost',icon='help');helpbtn.clicked.connect(self._open_issues);self.header_extra.addWidget(helpbtn)
        row=QHBoxLayout();self.guide_columns=row;row.setSpacing(18);sidebar=QWidget();self.guide_sidebar=sidebar;sl=QGridLayout(sidebar);self.guide_nav=sl;sl.setContentsMargins(0,4,0,0);sl.setSpacing(8);sl.setAlignment(Qt.AlignmentFlag.AlignTop);sidebar.setFixedWidth(230);self.sidebuttons=[]
        names=[('Bắt đầu','star_small'),('Cài Việt hoá','settings'),('Cập nhật bản dịch','refresh'),('Khôi phục bản gốc','file_check'),('Câu hỏi thường gặp','help')]
        for index,(label,icon) in enumerate(names):
            b=StarlitButton(label,variant='tab',icon=icon if icon!='star_small' else None);b.setMinimumWidth(0);b.setFixedHeight(54);b.stretch_background=True;b.caption_wrap=True;b.setFont(ui_font(15,QFont.Weight.DemiBold));b.setToolTip(label);b.setCheckable(True);b.clicked.connect(lambda checked=False,n=index:self._change(n));sl.addWidget(b,index,0);self.sidebuttons.append(b)
        row.addWidget(sidebar,0);divider=QFrame();self.guide_divider=divider;divider.setFixedWidth(1);divider.setStyleSheet('background:#c9bda7');row.addWidget(divider);self.pages=QStackedWidget();self.pages.setMinimumWidth(0);self.pages.setMinimumHeight(320);row.addWidget(self.pages,1);self.body.addLayout(row,1)
        for section in self.help_content['sections']:
            w=QWidget();vl=QVBoxLayout(w);vl.setContentsMargins(0,0,8,0);vl.setSpacing(12);headline=QHBoxLayout();headline.addWidget(text_label(section['title'],24,'#d9f6ff',True,True));headline.addWidget(SectionRule(),1);vl.addLayout(headline);vl.addWidget(text_label(section['subtitle'],15,'#b6d7ef',wrap=True));vl.addWidget(StepChain(section['current']))
            for index,step in enumerate(section['steps'],1):vl.addWidget(InstructionCard(index,step['title'],step['detail']))
            vl.addWidget(AlertStrip('Giữ bản sao lưu và đóng game trước khi thay đổi.','info'))
            if section['title']=='Cập nhật bản dịch':
                sync=StarlitButton('Đến Đồng bộ GitHub',variant='secondary',icon='refresh');sync.caption_wrap=True;sync.stretch_background=True;sync.setMinimumHeight(56);sync.clicked.connect(self._open_sync_settings);vl.addWidget(sync)
            self._faq(vl,compact=True);vl.addStretch();self.pages.addWidget(scroll_area(w))
        faq=QWidget();fl=QVBoxLayout(faq);fl.setSpacing(14);fl.addWidget(text_label('Câu hỏi thường gặp',24,bold=True));self._faq(fl);fl.addStretch();self.pages.addWidget(scroll_area(faq))
        back=StarlitButton('Về Tổng quan',variant='ghost',icon='arrow_left');back.clicked.connect(self.accept);self.footer.addWidget(back);self.footer.addStretch();ret=StarlitButton('Về màn hình cài đặt',variant='primary',icon='chevron_right');ret.setMinimumWidth(235);ret.clicked.connect(self._return_install);self.footer.addWidget(ret);self._change(0);self._responsive_callback=self._layout_guide_columns;self._apply_panel_layout()
    def _layout_guide_columns(self,width):
        compact=width<760
        self.guide_columns.setDirection(QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight)
        self.guide_divider.setVisible(not compact)
        self.guide_sidebar.setMinimumWidth(0);self.guide_sidebar.setMaximumWidth(16777215 if compact else 230)
        if not compact:self.guide_sidebar.setMinimumWidth(230)
        self.guide_sidebar.setMaximumHeight(190 if compact else 16777215)
        if getattr(self,'_guide_compact',None)!=compact:
            self._guide_compact=compact
            while self.guide_nav.count():self.guide_nav.takeAt(0)
            for i,b in enumerate(self.sidebuttons):self.guide_nav.addWidget(b,i//2 if compact else i,i%2 if compact else 0)
        self.body_widget.setMinimumHeight(540 if compact else 340)
    def _faq(self,layout,compact=False):
        heading=QHBoxLayout();heading.addWidget(text_label('Câu hỏi thường gặp',19,bold=True));heading.addWidget(SectionRule(),1);layout.addLayout(heading)
        entries=self.help_content['faq']
        for entry in entries[:2 if compact else len(entries)]:
            button=StarlitButton(entry['question'],variant='secondary',icon='chevron_right');button.setCheckable(True);button.caption_wrap=True;button.stretch_background=True;button.setFont(ui_font(15,QFont.Weight.DemiBold));button.setMinimumHeight(82);button.setToolTip(entry['question']);detail=QWidget();answer_layout=QVBoxLayout(detail);answer_layout.setContentsMargins(10,3,10,10);answer_layout.addWidget(text_label(entry['answer'],15,'#b6d7ef',wrap=True));detail.hide();button.toggled.connect(lambda checked,b=button,d=detail:self._toggle_question(b,d,checked));layout.addWidget(button);layout.addWidget(detail)
            if entry['question']=='Gửi thông tin lỗi ở đâu?':
                issues=StarlitButton('Mở trang báo lỗi GitHub',variant='secondary',icon='external_link');issues.caption_wrap=True;issues.stretch_background=True;issues.setMinimumHeight(56);issues.clicked.connect(self._open_issues);answer_layout.addWidget(issues)
    def _open_issues(self):
        parent=self.parentWidget()
        try:repo=parent.config_manager.channel()['repo']
        except (AttributeError,ValueError):self.subtitle.setText('Hãy kiểm tra kho GitHub trong Cài đặt launcher.');return
        url='https://github.com/'+repo+'/issues'
        if not QDesktopServices.openUrl(QUrl(url)):self.subtitle.setText('Không mở được trình duyệt. Liên kết báo lỗi: '+url)
    def _open_sync_settings(self):
        parent=self.parentWidget();self.accept()
        if parent:QTimer.singleShot(0,lambda:parent._handle_navigation('settings'))
    def _toggle_question(self,button,detail,checked):
        detail.setVisible(checked);button.art_icon_name='chevron_down' if checked else 'chevron_right';button.setIcon(AssetManager.get().get_icon(button.art_icon_name));button.update()
    def _change(self,index):self.pages.setCurrentIndex(index);[(b.setChecked(i==index)) for i,b in enumerate(self.sidebuttons)]
    def _return_install(self):
        parent=self.parentWidget();self.accept()
        if parent and hasattr(parent,'overview_view'):QTimer.singleShot(0,parent.overview_view.btn_install.setFocus)
    def _support(self):
        parent=self.parentWidget();self.accept()
        if parent:QTimer.singleShot(0,lambda:parent._handle_navigation('tools'))
