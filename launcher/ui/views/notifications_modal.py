"""Two-column announcement center with rich rows and genuine pagination/filtering."""
import math
from urllib.parse import urlparse
from PySide6.QtCore import Qt,QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QTextBrowser,QFrame,QSizePolicy
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import ArtInput,RichRow,Badge,ArtDivider,AlertStrip,text_label,scroll_area
class NotificationsModal(ArtDialog):
    def __init__(self,notifications,parent=None):
        super().__init__('Thông báo','Cập nhật và thông tin từ nhóm dịch','bell',parent,width=1160,height=780);self.body_widget.setMinimumWidth(760);self.notifications=list(notifications);self.category=None;self.page=0;self.page_size=4;self._selected=None
        self.search_input=ArtInput(placeholder='Tìm thông báo',icon='search');self.search_input.setMaximumWidth(330);self.header_extra.addWidget(self.search_input);self.search_input.textChanged.connect(self._filter)
        tabs=QHBoxLayout();tabs.setSpacing(7);self.filters={}
        for label,cat in [('Tất cả',None),('Cập nhật','project'),('Hướng dẫn','guide'),('Lưu ý','notice')]:
            b=StarlitButton(label,variant='tab');b.setCheckable(True);b.setMinimumWidth(130);b.clicked.connect(lambda checked=False,c=cat:self._set_category(c));tabs.addWidget(b);self.filters[cat]=b
        tabs.addStretch();self.body.addLayout(tabs)
        columns=QHBoxLayout();columns.setSpacing(20);left=QWidget();self.rows_layout=QVBoxLayout(left);self.rows_layout.setContentsMargins(0,0,0,0);self.rows_layout.setSpacing(8);self.rows_layout.addStretch();self.rows_scroll=scroll_area(left);columns.addWidget(self.rows_scroll,4)
        divider=QFrame();divider.setFixedWidth(1);divider.setStyleSheet('background:#387499');columns.addWidget(divider)
        right=QWidget();dl=QVBoxLayout(right);dl.setContentsMargins(2,0,0,0);dl.setSpacing(12);self.detail_badge=Badge();dl.addWidget(self.detail_badge);self.detail_title=text_label('',25,bold=True,wrap=True);dl.addWidget(self.detail_title);self.detail_date=text_label('',11,'#98bddb');dl.addWidget(self.detail_date)
        self.detail_body=QTextBrowser();self.detail_body.setOpenExternalLinks(False);self.detail_body.setOpenLinks(False);self.detail_body.setStyleSheet('QTextBrowser{background:transparent;border:0;color:#eff7ff;font-size:15px;padding:0;}');self.detail_body.anchorClicked.connect(self._open_url);self.detail_body.setVerticalScrollBar(__import__('launcher.ui.components.art_controls',fromlist=['ArtScrollBar']).ArtScrollBar());dl.addWidget(self.detail_body,1);dl.addWidget(ArtDivider());self.info=AlertStrip('Đóng game và chọn đúng thư mục trước khi cài bản dịch.','info');dl.addWidget(self.info)
        self.link_button=StarlitButton('Xem hướng dẫn',variant='ghost',icon='external_link');self.link_button.clicked.connect(self._follow_link);dl.addWidget(self.link_button,0,Qt.AlignmentFlag.AlignLeft);columns.addWidget(right,6);self.body.addLayout(columns,1)
        self.count_label=text_label('',12);self.footer.addWidget(self.count_label);self.footer.addStretch();self.prev=StarlitButton('',variant='square',icon='chevron_left');self.prev.setFixedSize(36,36);self.prev.setAccessibleName('Trang thông báo trước');self.prev.clicked.connect(lambda:self._page(-1));self.footer.addWidget(self.prev);self.page_label=text_label('1',13,bold=True);self.footer.addWidget(self.page_label);self.next=StarlitButton('',variant='square',icon='chevron_right');self.next.setFixedSize(36,36);self.next.setAccessibleName('Trang thông báo sau');self.next.clicked.connect(lambda:self._page(1));self.footer.addWidget(self.next);self.footer.addStretch();close=StarlitButton('Đóng',variant='secondary',icon='close');close.setMinimumWidth(118);close.clicked.connect(self.reject);self.footer.addWidget(close);self._populate()
    def _kind(self,n):
        c=n.category.lower();return 'project' if c in ('release','project','update') else ('guide' if c=='guide' else ('feedback' if c=='feedback' else 'notice'))
    def _set_category(self,c):self.category=c;self.page=0;self._populate()
    def _filter(self,*args):self.page=0;self._populate()
    def _page(self,delta):self.page+=delta;self._populate()
    def _populate(self):
        for c,b in self.filters.items():b.setChecked(c==self.category)
        q=self.search_input.text().strip().casefold();items=[n for n in self.notifications if (not q or q in (n.title+' '+n.summary+' '+n.content).casefold()) and (self.category is None or self._kind(n)==self.category or (self.category=='notice' and self._kind(n)=='feedback'))]
        pages=max(1,math.ceil(len(items)/self.page_size));self.page=max(0,min(self.page,pages-1));start=self.page*self.page_size;visible=items[start:start+self.page_size]
        while self.rows_layout.count():
            child=self.rows_layout.takeAt(0)
            if child.widget():child.widget().deleteLater()
        self.rows=[]
        for n in visible:
            kind=self._kind(n);row=RichRow(n.title,n.summary,{'project':'Dự án','guide':'Hướng dẫn','notice':'Lưu ý','feedback':'Phản hồi'}[kind],kind);row.clicked.connect(lambda checked=False,item=n:self._select(item));self.rows_layout.addWidget(row);self.rows.append((row,n))
        if not visible:self.rows_layout.addWidget(AlertStrip('Không tìm thấy thông báo phù hợp.','info'))
        self.rows_layout.addStretch();self.count_label.setText(f'{len(items)} thông báo');self.page_label.setText(f'{self.page+1} / {pages}');self.prev.setEnabled(self.page>0);self.next.setEnabled(self.page+1<pages)
        chosen=next((n for n in visible if n.id==self._selected),visible[0] if visible else None);self._select(chosen)
    def _select(self,n):
        self._selected=n.id if n else None
        for row,item in self.rows:row.setChecked(bool(n and item.id==n.id))
        if n is None:self.detail_title.setText('Chưa có thông báo');self.detail_badge.hide();self.detail_date.clear();self.detail_body.setPlainText('Dữ liệu từ kênh thông báo hiện đang trống.');self.link_button.hide();return
        self.detail_badge.show();self.detail_badge.kind=self._kind(n);self.detail_badge.setText({'project':'Dự án','guide':'Hướng dẫn','notice':'Lưu ý','feedback':'Phản hồi'}[self._kind(n)]);self.detail_badge.update();self.detail_title.setText(n.title);self.detail_date.setText(n.date);self.detail_body.setPlainText(n.content);self.link_button.show();self.link_button.setText('Mở liên kết' if n.link_url else 'Xem hướng dẫn')
    def select_id(self,identity):
        self.category=None;self.search_input.clear();self._selected=identity
        index=next((i for i,n in enumerate(self.notifications) if n.id==identity),0);self.page=index//self.page_size;self._populate()
    def _open_url(self,url):
        if url.scheme() in ('http','https') and url.host():QDesktopServices.openUrl(url)
    def _follow_link(self):
        n=next((n for n in self.notifications if n.id==self._selected),None)
        if n and n.link_url:
            u=QUrl(n.link_url)
            if u.scheme() in ('http','https') and u.host():self._open_url(u)
        else:
            p=self.parentWidget();self.accept()
            if p:p._handle_navigation('guide')
