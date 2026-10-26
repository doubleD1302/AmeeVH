"""Reference-aligned guide sidebar, connected steps and expandable FAQ."""
from PySide6.QtCore import Qt,QRectF,QTimer
from PySide6.QtGui import QPainter,QPen,QColor
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QStackedWidget,QFrame
from ..assets import AssetManager
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import AssetImage,ArtDivider,SectionRule,RichRow,AlertStrip,text_label,scroll_area
class StepChain(QWidget):
    def __init__(self,current=1,parent=None):super().__init__(parent);self.current=current;self.setMinimumHeight(102)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);a=AssetManager.get();xs=[self.width()*.17,self.width()*.5,self.width()*.83];p.setPen(QPen(QColor('#4fa3d4'),1));p.drawLine(round(xs[0]),32,round(xs[2]),32)
        for index,(x,label) in enumerate(zip(xs,['Chọn thư mục','Cài bản dịch','Kiểm tra']),1):
            status='current' if index==self.current else ('done' if index<self.current else 'pending');a.paint(p,f'controls/step_{index}_{status}',QRectF(x-28,3,56,56),'contain');p.setPen(QColor('#eff8ff' if index==self.current else '#96cef2'));p.drawText(QRectF(x-80,66,160,29),Qt.AlignmentFlag.AlignCenter,label)
class InstructionCard(QWidget):
    def __init__(self,number,title,detail,parent=None):
        super().__init__(parent);l=QHBoxLayout(self);l.setContentsMargins(15,10,16,10);l.setSpacing(12);l.addWidget(AssetImage(f'controls/step_{number}_pending',38));text=QVBoxLayout();text.setSpacing(2);text.addWidget(text_label(title,16,bold=True,wrap=True));text.addWidget(text_label(detail,13,'#a5cae9',wrap=True));l.addLayout(text,1);self.setMinimumHeight(66)
    def paintEvent(self,e):p=QPainter(self);AssetManager.get().paint(p,'controls/list_row_normal',QRectF(self.rect()))
class GuideModal(ArtDialog):
    def __init__(self,parent=None):
        super().__init__('Hướng dẫn','Cài đặt dễ dàng, bắt đầu nhanh chóng','book',parent,width=1160,height=790);self.body_widget.setMinimumWidth(850);helpbtn=StarlitButton('Hỗ trợ',variant='ghost',icon='help');helpbtn.clicked.connect(self._support);self.header_extra.addWidget(helpbtn)
        row=QHBoxLayout();row.setSpacing(24);sidebar=QWidget();sl=QVBoxLayout(sidebar);sl.setContentsMargins(0,4,0,0);sl.setSpacing(12);sidebar.setMaximumWidth(270);self.sidebuttons=[]
        names=[('Bắt đầu','star_small'),('Cài Việt hoá','settings'),('Cập nhật bản dịch','refresh'),('Khôi phục bản gốc','file_check'),('Câu hỏi thường gặp','help')]
        for index,(label,icon) in enumerate(names):
            b=StarlitButton(label,variant='tab',icon=AssetManager.get().get_icon(icon) if icon!='star_small' else None);b.setMinimumWidth(210);b.setFixedHeight(50);b.setCheckable(True);b.clicked.connect(lambda checked=False,n=index:self._change(n));sl.addWidget(b);self.sidebuttons.append(b)
        sl.addStretch();row.addWidget(sidebar,3);divider=QFrame();divider.setFixedWidth(1);divider.setStyleSheet('background:#39769d');row.addWidget(divider);self.pages=QStackedWidget();row.addWidget(self.pages,7);self.body.addLayout(row,1)
        content=[('Cài bản Việt hoá','Đóng game trước khi thực hiện.',1,[('Chọn thư mục game','Trỏ đến thư mục đang cài Stella Sora.'),('Cài Việt hoá','Nhấn nút cài đặt và chờ công cụ hoàn tất.'),('Mở game và kiểm tra','Kiểm tra nội dung hiển thị sau khi cài.')]),('Cài Việt hoá','Chỉ cài các tệp được manifest xác minh.',2,[('Chọn gói phù hợp','Dùng kênh đã cấu hình hoặc gói ngoại tuyến có SHA256.'),('Xác nhận thư mục','Phiên bản game và tài nguyên phải khớp manifest.'),('Chờ cài và đối chiếu','Biên bản chỉ được ghi khi hoàn tất đọc lại toàn bộ tệp.')]),('Cập nhật bản dịch','Kiểm tra phiên bản tương thích sau khi game cập nhật.',2,[('Kiểm tra bản game','Launcher đọc GAME_VER và RES_VER từ manifest game.'),('Tải manifest mới','Gói chỉ gồm texture sẽ chỉ cài texture được kê khai.'),('Đối chiếu sau cài','Dùng Kiểm tra tệp; quan sát chữ trong game do bạn thực hiện.')]),('Khôi phục bản gốc','Phục hồi trạng thái trước lần cài đã ghi nhận.',3,[('Chọn đúng thư mục','Khôi phục dùng biên bản và backup gắn với game này.'),('Đối chiếu tệp hiện tại','Game đã đổi tệp sẽ báo xung đột, không tự ghi đè.'),('Phục hồi thao tác bị ngắt','Công cụ nâng cao có mục phục hồi nhật ký nếu cần.')])]
        for title,subtitle,current,steps in content:
            w=QWidget();vl=QVBoxLayout(w);vl.setContentsMargins(0,0,8,0);vl.setSpacing(10);headline=QHBoxLayout();headline.addWidget(text_label(title,24,'#d9f6ff',True));headline.addWidget(SectionRule(),1);vl.addLayout(headline);vl.addWidget(text_label(subtitle,14,'#a6c9e9',wrap=True));vl.addWidget(StepChain(current))
            for i,(head,detail) in enumerate(steps,1):vl.addWidget(InstructionCard(i,head,detail))
            vl.addWidget(AlertStrip('Giữ bản sao lưu và đóng game trước khi thay đổi.','info'));self._faq(vl,compact=True);vl.addStretch();self.pages.addWidget(scroll_area(w))
        faq=QWidget();fl=QVBoxLayout(faq);fl.setSpacing(14);fl.addWidget(text_label('Câu hỏi thường gặp',24,bold=True));self._faq(fl);fl.addStretch();self.pages.addWidget(scroll_area(faq))
        back=StarlitButton('Về Tổng quan',variant='ghost',icon='arrow_left');back.clicked.connect(self.accept);self.footer.addWidget(back);self.footer.addStretch();ret=StarlitButton('Về màn hình cài đặt',variant='primary',icon='chevron_right');ret.setMinimumWidth(235);ret.clicked.connect(self._return_install);self.footer.addWidget(ret);self._change(0)
    def _faq(self,layout,compact=False):
        heading=QHBoxLayout();heading.addWidget(text_label('Câu hỏi thường gặp',19,bold=True));heading.addWidget(SectionRule(),1);layout.addLayout(heading)
        entries=[('Không tìm thấy thư mục game?','Chọn thư mục có StellaSora.exe. Có thể dùng nút Chọn… trên Tổng quan hoặc bật tự dò Steam/Yostar trong Cài đặt.'),('Làm sao để khôi phục bản gốc?','Dùng Khôi phục trên Tổng quan. Chỉ khôi phục khi biên bản và hash tệp còn khớp backup của thư mục này.'),('Vì sao gói bản dịch bị từ chối?','Có thể do phiên bản, kích thước hoặc SHA256 không khớp. Không bỏ các kiểm tra này để cài bằng gói cũ.'),('Cách gửi thông tin lỗi?','Mở biểu tượng bánh răng → Công cụ nâng cao → Chẩn đoán; sao chép báo cáo và nội dung lỗi.')]
        for question,answer in entries[:2 if compact else len(entries)]:
            button=StarlitButton(question,variant='secondary',icon='chevron_right');button.setCheckable(True);button.setMinimumHeight(40);detail=text_label(answer,13,'#acd0ec',wrap=True);detail.hide();button.toggled.connect(lambda checked,b=button,d=detail:self._toggle_question(b,d,checked));layout.addWidget(button);layout.addWidget(detail)
    def _toggle_question(self,button,detail,checked):
        detail.setVisible(checked);button.art_icon_name='chevron_down' if checked else 'chevron_right';button.setIcon(AssetManager.get().get_icon(button.art_icon_name));button.update()
    def _change(self,index):self.pages.setCurrentIndex(index);[(b.setChecked(i==index)) for i,b in enumerate(self.sidebuttons)]
    def _return_install(self):
        parent=self.parentWidget();self.accept()
        if parent and hasattr(parent,'overview_view'):QTimer.singleShot(0,parent.overview_view.btn_install.setFocus)
    def _support(self):
        parent=self.parentWidget();self.accept()
        if parent:QTimer.singleShot(0,lambda:parent._handle_navigation('tools'))
