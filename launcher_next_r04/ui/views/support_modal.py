"""Full reference support scaffold with honest unavailable payment/list states."""
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QPainter,QColor
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFrame
from ..assets import AssetManager
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import AssetImage,ArtInput,ArtTableRow,AlertStrip,ArtDivider,text_label,scroll_area
class QRUnavailable(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.setMinimumHeight(175);l=QVBoxLayout(self);l.setContentsMargins(22,85,22,16);l.addStretch();text=text_label('Chưa có thông tin nhận ủng hộ',13,wrap=True);text.setAlignment(Qt.AlignmentFlag.AlignCenter);l.addWidget(text);small=text_label('Mã QR chỉ hiện khi có người nhận được xác minh.',11,'#95c3e4',wrap=True);small.setAlignment(Qt.AlignmentFlag.AlignCenter);l.addWidget(small)
    def paintEvent(self,e):p=QPainter(self);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);AssetManager.get().paint(p,'controls/qr_placeholder',QRectF(self.rect()),'contain')
class EmptySupport(QWidget):
    def __init__(self,parent=None):super().__init__(parent);self.setMinimumHeight(245)
    def paintEvent(self,e):
        p=QPainter(self);a=AssetManager.get();a.paint(p,'supplemental/decor/empty_constellation',QRectF((self.width()-245)/2,12,245,140),'contain');p.setPen(QColor('#c5e7ff'));p.drawText(QRectF(10,156,self.width()-20,30),Qt.AlignmentFlag.AlignCenter,'Danh sách chưa có dữ liệu');p.setPen(QColor('#9bc4e3'));p.drawText(QRectF(20,190,self.width()-40,50),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,'Chỉ hiển thị thông tin sau khi có nguồn được xác minh.')
class PaymentTile(StarlitButton):
    def paintEvent(self,e):
        super().paintEvent(e);p=QPainter(self);AssetManager.get().paint(p,'controls/radio_on' if self.isChecked() else 'controls/radio_off',QRectF(self.width()-19,5,13,13),'contain')
class FactIcon(QWidget):
    def __init__(self,name):super().__init__();self.name=name;self.setFixedSize(42,42)
    def paintEvent(self,e):
        p=QPainter(self);a=AssetManager.get();a.paint(p,'controls/avatar',QRectF(self.rect()),'contain');a.paint(p,'icons/'+self.name+'_white',QRectF(8,8,26,26),'contain')
class SupportModal(ArtDialog):
    def __init__(self,supporter_data,parent=None):
        super().__init__('Ủng hộ dự án','Cảm ơn bạn đã tiếp sức cho Stella Sora Việt hoá.','star_small',parent,width=1160,height=790);self.body_widget.setMinimumWidth(820);self.supporter_data=supporter_data
        columns=QHBoxLayout();columns.setSpacing(25);left=QWidget();ll=QVBoxLayout(left);ll.setContentsMargins(0,0,5,0);ll.setSpacing(11);ll.addWidget(text_label('Gửi một chút động viên',23,bold=True,wrap=True));ll.addWidget(text_label('Sự ủng hộ của bạn giúp nhóm duy trì công cụ và tiếp tục hoàn thiện bản dịch.',15,'#bddaf1',wrap=True));ll.addSpacing(5);ll.addWidget(text_label('Chọn phương thức',14,bold=True));methods=QHBoxLayout();methods.setSpacing(10)
        for text,icon in [('Chuyển khoản','bank'),('Ví điện tử','wallet')]:
            b=PaymentTile(text,variant='secondary',icon=icon);b.setMinimumHeight(58);b.setEnabled(False);b.setToolTip('Chưa có người nhận được xác minh');methods.addWidget(b)
        ll.addLayout(methods);ll.addWidget(QRUnavailable(),1)
        for text,icon in [('Ủng hộ hoàn toàn tự nguyện.','heart'),('Bản Việt hoá luôn miễn phí.','gift')]:
            row=QHBoxLayout();row.setSpacing(12);row.addWidget(FactIcon(icon));row.addWidget(text_label(text,13,wrap=True),1);ll.addLayout(row)
        columns.addWidget(scroll_area(left),46);line=QFrame();line.setFixedWidth(1);line.setStyleSheet('background:#39769d');columns.addWidget(line)
        right=QWidget();rl=QVBoxLayout(right);rl.setContentsMargins(0,0,0,0);rl.setSpacing(10);rl.addWidget(text_label('Những người bạn đồng hành',23,bold=True,wrap=True));rl.addWidget(text_label('Mỗi sự ủng hộ là một lời động viên.',14,'#bddaf1'));self.search=ArtInput(placeholder='Tìm tên người đồng hành',icon='search');self.search.textChanged.connect(self._populate);rl.addWidget(self.search)
        header=QWidget();header.setFixedHeight(38);hl=QHBoxLayout(header);hl.setContentsMargins(12,0,12,0);hl.addWidget(text_label('Người đồng hành',13,'#bde9ff',True),3);hl.addWidget(text_label('Ủng hộ',13,'#bde9ff',True),2);hl.addWidget(text_label('Ngày',12,'#bde9ff',True),2)
        class Header(QWidget):
            def paintEvent(self,e):p=QPainter(self);AssetManager.get().paint(p,'controls/table_header',QRectF(self.rect()),'stretch')
        arthead=Header();arthead.setFixedHeight(38);artlayout=QHBoxLayout(arthead);artlayout.setContentsMargins(0,0,0,0);artlayout.addWidget(header);rl.addWidget(arthead)
        self.rows=QWidget();self.rows_layout=QVBoxLayout(self.rows);self.rows_layout.setContentsMargins(0,0,0,0);self.rows_layout.setSpacing(0);rl.addWidget(scroll_area(self.rows),1);rl.addWidget(text_label('Trân trọng sự đồng hành của bạn.',12,'#bed9f0'));columns.addWidget(right,54);self.body.addLayout(columns,1)
        self.footer.addWidget(text_label('Dự án Việt hoá • Phi thương mại',12,'#a9cfea'));self.footer.addStretch();b=StarlitButton('Đóng',variant='primary');b.setMinimumWidth(150);b.clicked.connect(self.reject);self.footer.addWidget(b);self._populate()
    def _populate(self,*args):
        while self.rows_layout.count():
            item=self.rows_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        query=self.search.text().strip().casefold();items=[s for s in self.supporter_data.supporters if not query or query in (s.name+' '+s.tier+' '+s.date).casefold()]
        if not items:self.rows_layout.addWidget(EmptySupport())
        else:
            for i,s in enumerate(items):self.rows_layout.addWidget(ArtTableRow(s.name,s.tier,s.date,s.message,i))
        self.rows_layout.addStretch()
