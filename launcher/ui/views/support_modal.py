"""Full reference support scaffold with honest unavailable payment/list states."""
from PySide6.QtCore import Qt,QRectF,QSize
from PySide6.QtGui import QPainter,QColor,QPen,QFont,QPixmap,QGuiApplication
from pathlib import Path
import json,hashlib
from ..typography import font as ui_font
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFrame,QButtonGroup,QBoxLayout
from ..assets import AssetManager
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import AssetImage,ArtInput,ArtTableRow,AlertStrip,ArtDivider,text_label,scroll_area
class PaymentQR(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.setMinimumHeight(220);self.setMaximumHeight(260);self.master=QPixmap();self.error='Chọn phương thức để xem mã QR.'
    def set_method(self,method,asset_dir):
        self.master=QPixmap();self.error=''
        try:
            name=method['qr_file']
            if Path(name).name!=name:raise ValueError('Tên ảnh QR không hợp lệ.')
            path=asset_dir/name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=method['qr_sha256']:raise ValueError('Ảnh QR thiếu hoặc không khớp nguồn đã cung cấp.')
            self.master=QPixmap(str(path))
            if self.master.isNull():raise ValueError('Không đọc được ảnh QR. Hãy dùng thông tin tài khoản bên dưới.')
        except (OSError,ValueError,KeyError) as exc:self.error=str(exc)
        self.setAccessibleName('Mã QR '+method.get('provider',''));self.update()
    def paintEvent(self,event):
        painter=QPainter(self)
        if self.master.isNull():
            painter.setPen(QColor('#405682'));painter.drawText(QRectF(16,16,self.width()-32,self.height()-32),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,self.error);return
        # Keep the exact supplied raster, preserve aspect, and never upscale
        # beyond its physical master pixels. White padding is the quiet zone.
        dpr=max(1.,self.devicePixelRatioF());scale=min((self.width()-48)/self.master.width(),(self.height()-48)/self.master.height(),1./dpr)
        width=self.master.width()*scale;height=self.master.height()*scale;target=QRectF(0,0,width,height);target.moveCenter(QRectF(self.rect()).center())
        painter.fillRect(target.adjusted(-20,-20,20,20),QColor('white'));painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,False);painter.drawPixmap(target,self.master,QRectF(self.master.rect()))
class EmptySupport(QWidget):
    def __init__(self,parent=None):super().__init__(parent);self.setMinimumHeight(245)
    def paintEvent(self,e):
        p=QPainter(self);a=AssetManager.get();p.setPen(QColor('#405682'));p.drawText(QRectF(10,156,self.width()-20,30),Qt.AlignmentFlag.AlignCenter,'Danh sách chưa có dữ liệu');p.setPen(QColor('#637596'));p.drawText(QRectF(20,190,self.width()-40,50),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,'Chỉ hiển thị thông tin sau khi có nguồn được xác minh.')
class PaymentTile(StarlitButton):
    # The authored selected skin already shows selection. Painting a second
    # radio glyph over the caption would reintroduce the overlap defect.
    pass
class FactIcon(QWidget):
    def __init__(self,name):super().__init__();self.name=name;self.setFixedSize(42,42)
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setPen(QPen(QColor('#c7b79a'),1));p.setBrush(QColor('#d8f0ef'));p.drawEllipse(QRectF(2,2,38,38));AssetManager.get().paint(p,'icons/'+self.name+'_white',QRectF(9,9,24,24),'contain')
class SupportModal(ArtDialog):
    def __init__(self,supporter_data,parent=None):
        super().__init__('Ủng hộ dự án','Cảm ơn bạn đã tiếp sức cho Stella Sora Việt hoá.','star_small',parent,width=1160,height=790,panel='panels/support');self.body_widget.setMinimumWidth(0);self.supporter_data=supporter_data
        columns=QHBoxLayout();self.support_columns=columns;columns.setSpacing(20);left=QWidget();ll=QVBoxLayout(left);ll.setContentsMargins(0,0,5,0);ll.setSpacing(11);ll.addWidget(text_label('Gửi một chút động viên',23,bold=True,wrap=True));ll.addWidget(text_label('Sự ủng hộ của bạn giúp nhóm duy trì công cụ và tiếp tục hoàn thiện bản dịch.',15,'#bddaf1',wrap=True));ll.addSpacing(5);ll.addWidget(text_label('Chọn phương thức',14,bold=True));methods=QHBoxLayout();methods.setSpacing(8)
        self.payment_dir=AssetManager.get().ui_dir/'support_r09';self.payment_methods=[];self.payment_group=QButtonGroup(self);self.payment_group.setExclusive(True)
        try:
            data=json.loads((self.payment_dir/'payment_methods.json').read_text(encoding='utf8'));candidates=data['methods']
            if not isinstance(candidates,list) or not candidates:raise ValueError('Chưa có phương thức ủng hộ.')
            for method in candidates:
                if not isinstance(method,dict) or not all(isinstance(method.get(key),str) and method[key] for key in ('id','label','provider','recipient_name','qr_file','qr_sha256')):raise ValueError('Thông tin phương thức ủng hộ không đầy đủ.')
                if method.get('account_number') is not None and not isinstance(method['account_number'],str):raise ValueError('Số tài khoản không đúng định dạng.')
                if method.get('account_masked') is not None and not isinstance(method['account_masked'],str):raise ValueError('Số ví được che không đúng định dạng.')
            self.payment_methods=candidates
        except (OSError,ValueError,KeyError,TypeError) as exc:self.payment_methods=[];ll.addWidget(AlertStrip('Không đọc được thông tin ủng hộ: '+str(exc),'error'))
        for index,method in enumerate(self.payment_methods):
            button=PaymentTile(method['label'],variant='secondary',icon='bank' if method['id']=='bank' else 'wallet');button.setCheckable(True);button.setFixedHeight(58);button.setMinimumWidth(0);button.setIconSize(QSize(20,20));button.stretch_background=True;button.caption_wrap=True;button.setFont(ui_font(15,QFont.Weight.DemiBold));button.setToolTip(method['provider']);self.payment_group.addButton(button,index);methods.addWidget(button,1);button.clicked.connect(lambda checked=False,m=method:self._select_payment(m))
        ll.addLayout(methods);self.payment_qr=PaymentQR();ll.addWidget(self.payment_qr)
        self.payment_details=text_label('',15,'#d7efff',wrap=True);self.payment_details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);ll.addWidget(self.payment_details)
        self.copy_account=StarlitButton('Sao chép số tài khoản',variant='secondary',icon='copy');self.copy_account.caption_wrap=True;self.copy_account.stretch_background=True;self.copy_account.setMinimumHeight(52);self.copy_account.clicked.connect(self._copy_account);ll.addWidget(self.copy_account)
        ll.addWidget(text_label('Thông tin từ mã được cung cấp. Hãy kiểm tra tên người nhận trong ứng dụng thanh toán trước khi xác nhận.',13,'#a6cce9',wrap=True))
        if self.payment_methods:
            self.payment_group.button(0).setChecked(True);self._select_payment(self.payment_methods[0])
        else:self.copy_account.setEnabled(False)
        for text,icon in [('Ủng hộ hoàn toàn tự nguyện.','heart'),('Bản Việt hoá luôn miễn phí.','gift')]:
            row=QHBoxLayout();row.setSpacing(12);row.addWidget(FactIcon(icon));row.addWidget(text_label(text,13,wrap=True),1);ll.addLayout(row)
        self.payment_scroll=scroll_area(left);columns.addWidget(self.payment_scroll,46);line=QFrame();self.support_divider=line;line.setFixedWidth(1);line.setStyleSheet('background:#c9bda7');columns.addWidget(line)
        right=QWidget();self.support_right=right;rl=QVBoxLayout(right);rl.setContentsMargins(0,0,0,0);rl.setSpacing(10);rl.addWidget(text_label('Những người bạn đồng hành',23,bold=True,wrap=True));rl.addWidget(text_label('Mỗi sự ủng hộ là một lời động viên.',14,'#bddaf1'));self.search=ArtInput(placeholder='Tìm tên người đồng hành',icon='search');self.search.textChanged.connect(self._populate);rl.addWidget(self.search)
        header=QWidget();header.setFixedHeight(38);hl=QHBoxLayout(header);hl.setContentsMargins(12,0,12,0);hl.addWidget(text_label('Người đồng hành',13,'#bde9ff',True),3);hl.addWidget(text_label('Ủng hộ',13,'#bde9ff',True),2);hl.addWidget(text_label('Ngày',12,'#bde9ff',True),2)
        class Header(QWidget):
            def paintEvent(self,e):p=QPainter(self);AssetManager.get().paint(p,'controls/table_header',QRectF(self.rect()),'stretch')
        arthead=Header();arthead.setFixedHeight(38);artlayout=QHBoxLayout(arthead);artlayout.setContentsMargins(0,0,0,0);artlayout.addWidget(header);rl.addWidget(arthead)
        self.rows=QWidget();self.rows_layout=QVBoxLayout(self.rows);self.rows_layout.setContentsMargins(0,0,0,0);self.rows_layout.setSpacing(0);rl.addWidget(scroll_area(self.rows),1);rl.addWidget(text_label('Trân trọng sự đồng hành của bạn.',12,'#bed9f0'));columns.addWidget(right,54);self.body.addLayout(columns,1)
        reminder=text_label('Bản Việt hoá luôn luôn miễn phí.',23,'#a4efff',True,True);reminder.setFont(ui_font(23,QFont.Weight.Bold));reminder.setMinimumHeight(40);reminder.setAccessibleName('Bản Việt hoá luôn luôn miễn phí.');self.footer.addWidget(reminder,1);self.footer.addSpacing(16);b=StarlitButton('Đóng',variant='primary');b.setMinimumWidth(150);b.clicked.connect(self.reject);self.footer.addWidget(b);self._populate();self._responsive_callback=self._layout_support_columns;self._apply_panel_layout()
    def _layout_support_columns(self,width):
        compact=width<760
        self.support_columns.setDirection(QBoxLayout.Direction.TopToBottom if compact else QBoxLayout.Direction.LeftToRight)
        self.support_divider.setVisible(not compact)
        self.payment_scroll.setMinimumHeight(430 if compact else 0)
        self.support_right.setMinimumHeight(340 if compact else 0)
        self.body_widget.setMinimumHeight(800 if compact else 320)
    def _select_payment(self,method):
        self.selected_payment=method;self.payment_qr.set_method(method,self.payment_dir)
        account=method.get('account_number');display=account or method.get('account_masked') or 'Quét mã để xem người nhận'
        self.payment_details.setText(method['provider']+'\n'+method['recipient_name']+'\n'+display)
        self.copy_account.setEnabled(bool(account));self.copy_account.setText('Sao chép số tài khoản' if account else 'Số ví đang được ẩn');self.copy_account.setToolTip('Sao chép '+account if account else 'Nguồn chỉ hiển thị số ví được che; hãy quét mã bằng MoMo.')
    def _copy_account(self):
        value=getattr(self,'selected_payment',{}).get('account_number')
        if value:QGuiApplication.clipboard().setText(value);self.copy_account.setToolTip('Đã sao chép số tài khoản.')
    def _populate(self,*args):
        while self.rows_layout.count():
            item=self.rows_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        query=self.search.text().strip().casefold();items=[s for s in self.supporter_data.supporters if not query or query in (s.name+' '+s.tier+' '+s.date).casefold()]
        if not items:self.rows_layout.addWidget(EmptySupport())
        else:
            for i,s in enumerate(items):self.rows_layout.addWidget(ArtTableRow(s.name,s.tier,s.date,s.message,i))
        self.rows_layout.addStretch()
