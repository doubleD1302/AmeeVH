"""Art-styled diagnostics/ADB/recovery with worker-backed read-only collection."""
from PySide6.QtCore import Qt,QThread,Signal,QTimer,QRectF
from PySide6.QtGui import QGuiApplication,QPainter,QFont
from ..typography import font as ui_font
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QStackedWidget,QPlainTextEdit,QTableWidget,QTableWidgetItem,QHeaderView,QStyledItemDelegate,QStyle
from ...core.diagnostics import DiagnosticsCollector,AdbBridge
from ..assets import AssetManager
from ..components.modal_shell import ArtDialog
from ..components.glass_card import GlassCard
from ..components.starlit_button import StarlitButton
from ..components.art_controls import ArtScrollBar,AlertStrip,Spinner,ArtDivider,text_label
class ToolWorker(QThread):
    result_ready=Signal(bool,object)
    def __init__(self,target,parent):super().__init__(parent);self.target=target
    def run(self):
        try:self.result_ready.emit(True,self.target())
        except Exception as e:self.result_ready.emit(False,str(e))
class TableDelegate(QStyledItemDelegate):
    def paint(self,painter,option,index):
        kind='hover' if option.state & QStyle.StateFlag.State_MouseOver else ('odd' if index.row()%2 else 'even');AssetManager.get().paint(painter,'controls/table_row_'+kind,QRectF(option.rect),'stretch');super().paint(painter,option,index)
class AdvancedToolsModal(ArtDialog):
    def __init__(self,path_manager,game_info,parent=None):
        super().__init__('Công cụ nâng cao','Chẩn đoán, cầu nối ADB và phục hồi thao tác.','shield',parent,width=1080,height=760);self.path_manager=path_manager;self.game_info=game_info;self.adb_bridge=AdbBridge();self.worker=None;self.kind='';self.buttons=[]
        tabs=QHBoxLayout();tabs.setSpacing(10);self.tabbuttons=[]
        for i,(label,icon) in enumerate([('Chẩn đoán','log'),('ADB / Giả lập','globe'),('Phục hồi & cập nhật','restore')]):
            b=StarlitButton(label,variant='tab',icon=icon);self._caption_button(b,(235,280,340)[i],66);b.setCheckable(True);b.clicked.connect(lambda checked=False,n=i:self._page(n));tabs.addWidget(b);self.tabbuttons.append(b)
        tabs.addStretch();self.spinner=Spinner();tabs.addWidget(self.spinner);self.body.addLayout(tabs);self.stack=QStackedWidget();self.body.addWidget(self.stack,1)
        diag=QWidget();dl=QVBoxLayout(diag);dl.setContentsMargins(0,0,0,0);dl.setSpacing(12);self.diag_text=QPlainTextEdit();self.diag_text.setReadOnly(True);self.diag_text.setPlainText('Chọn Làm mới chẩn đoán để thu thập dữ liệu trên máy hiện tại.');self.diag_text.setVerticalScrollBar(ArtScrollBar());self.diag_text.setStyleSheet('QPlainTextEdit{background:rgba(5,25,48,130);border:1px solid #2c668f;border-radius:8px;color:#d9eeff;padding:14px;font-size:14px;}');dl.addWidget(self.diag_text,1);row=QHBoxLayout();b=StarlitButton('Làm mới chẩn đoán',variant='secondary',icon='refresh');self._caption_button(b,275,54);b.clicked.connect(self._run_diagnostics);self.buttons.append(b);row.addWidget(b);b=StarlitButton('Sao chép báo cáo',variant='secondary',icon='copy');self._caption_button(b,255,54);b.clicked.connect(self._copy_diagnostics);row.addWidget(b);row.addStretch();self.diag_status_label=text_label('',12,'#85dfff');row.addWidget(self.diag_status_label);dl.addLayout(row);self.stack.addWidget(diag)
        adb=QWidget();al=QVBoxLayout(adb);al.setContentsMargins(0,0,0,0);al.setSpacing(12);self.adb_info_label=text_label('Chọn Quét thiết bị để đọc trạng thái ADB.',13,'#b2d7f2',wrap=True);al.addWidget(self.adb_info_label);self.device_table=QTableWidget(0,3);self.device_table.setHorizontalHeaderLabels(['Mã thiết bị','Trạng thái','Chi tiết nhận diện']);self.device_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);self.device_table.setMouseTracking(True);self.device_table.setItemDelegate(TableDelegate(self.device_table));self.device_table.setVerticalScrollBar(ArtScrollBar());headerpath=(AssetManager.get().ui_dir/AssetManager.get().meta('controls/table_header')['png_2x']).as_posix();self.device_table.setStyleSheet('QTableWidget{background:transparent;color:#eef7ff;border:1px solid #2e668e;}QHeaderView::section{border-image:url("'+headerpath+'");color:#c9edff;padding:9px;border:0;}');al.addWidget(self.device_table,1);b=StarlitButton('Quét thiết bị / Giả lập',variant='secondary',icon='refresh');self._caption_button(b,320,58);b.clicked.connect(self._scan_adb_devices);self.buttons.append(b);al.addWidget(b,0,Qt.AlignmentFlag.AlignLeft);al.addWidget(AlertStrip('Chỉ đọc trạng thái. Không tự đẩy tệp hoặc cài APK.','info'));self.stack.addWidget(adb)
        recovery=GlassCard(asset_id='panels/plain');rl=QVBoxLayout(recovery);rl.setContentsMargins(30,26,30,30);rl.setSpacing(16);rl.addWidget(text_label('Phục hồi thao tác bị ngắt',21,bold=True));rl.addWidget(text_label('Nhật ký và backup được gắn với thư mục game đã chọn. Tệp có thay đổi ngoài thao tác sẽ được giữ lại và báo xung đột.',14,'#b6d7ef',wrap=True));b=StarlitButton('Phục hồi từ nhật ký',variant='secondary',icon='restore');self._caption_button(b,300,58);b.clicked.connect(self._recover_operation);rl.addWidget(b,0,Qt.AlignmentFlag.AlignLeft);rl.addWidget(ArtDivider());rl.addWidget(text_label('Cập nhật launcher',21,bold=True));rl.addWidget(text_label('Chỉ có thể tự cập nhật khi kênh phát hành cung cấp SHA256 xác minh. Kiểm tra không tự áp dụng bản cập nhật.',14,'#b6d7ef',wrap=True));b=StarlitButton('Kiểm tra cập nhật launcher',variant='secondary',icon='download');self._caption_button(b,370,58);b.clicked.connect(self._update_launcher);rl.addWidget(b,0,Qt.AlignmentFlag.AlignLeft);rl.addStretch();self.stack.addWidget(recovery)
        self.success_strip=AlertStrip('','success');self.success_strip.hide();self.body.addWidget(self.success_strip);self.error_strip=AlertStrip('','error');self.error_strip.hide();self.body.addWidget(self.error_strip);self.footer.addWidget(text_label('Dữ liệu chẩn đoán được giữ trên máy của bạn.',12,'#9bc5e5'));self.footer.addStretch();close=StarlitButton('Đóng',variant='secondary',icon='close');self._caption_button(close,150,50);close.clicked.connect(self.reject);self.footer.addWidget(close);self._page(0)
    def _caption_button(self,button,width,height):
        button.stretch_background=True;button.caption_wrap=True;button.setFont(ui_font(15,QFont.Weight.DemiBold));button.setMinimumWidth(width);button.setFixedHeight(height);button.setToolTip(button.text())
    def _page(self,i):self.stack.setCurrentIndex(i);[(b.setChecked(n==i)) for n,b in enumerate(self.tabbuttons)]
    def _can_close(self):return self.worker is None and super()._can_close()
    def _work(self,kind,target):
        if self.worker is not None:return
        self.kind=kind;self.error_strip.hide();self.success_strip.hide();self.spinner.start(getattr(self.parentWidget(),'config_manager',None).get('reduced_motion',False) if self.parentWidget() else False)
        for b in self.buttons:b.setEnabled(False)
        w=ToolWorker(target,self);self.worker=w;w.result_ready.connect(self._result);w.finished.connect(lambda:self._done(w));w.start()
    def _done(self,w):
        if self.worker is w:self.worker=None
        self.spinner.stop();[(b.setEnabled(True)) for b in self.buttons];w.deleteLater()
    def _result(self,ok,data):
        if not ok:self.error_strip.setText(str(data));self.error_strip.show();return
        if self.kind=='diagnostics':self.diag_text.setPlainText(data);self.diag_status_label.setText('Đã thu thập trên máy hiện tại.');self.success_strip.setText('Đã thu thập báo cáo chẩn đoán trên máy hiện tại.');self.success_strip.show()
        else:
            self.adb_info_label.setText(data['message']);devices=data['devices'];self.device_table.setRowCount(len(devices))
            for i,d in enumerate(devices):
                for j,key in enumerate(('serial','state','details')):self.device_table.setItem(i,j,QTableWidgetItem(d.get(key,'')))
    def _run_diagnostics(self):
        screen=self.screen();area=screen.availableGeometry();info=f'{area.width()}×{area.height()} DIP · {screen.logicalDotsPerInch():.0f} DPI';self._work('diagnostics',lambda:DiagnosticsCollector.collect(self.path_manager,self.game_info,info).to_text())
    def _copy_diagnostics(self):QGuiApplication.clipboard().setText(self.diag_text.toPlainText());self.diag_status_label.setText('Đã sao chép.')
    def _scan_adb_devices(self):
        def collect():
            if not self.adb_bridge.is_available():return {'message':'Không tìm thấy adb.exe. Cầu nối ADB hiện chưa khả dụng.','devices':[]}
            devices=self.adb_bridge.list_devices();return {'message':'ADB: '+str(self.adb_bridge.adb_path)+(' · Không có thiết bị kết nối.' if not devices else f' · {len(devices)} thiết bị.'),'devices':devices}
        self._work('adb',collect)
    def _recover_operation(self):
        if not self._can_close():return
        p=self.parentWidget();self.accept()
        if p:QTimer.singleShot(0,p._recover)
    def _update_launcher(self):
        if not self._can_close():return
        p=self.parentWidget();self.accept()
        if p:QTimer.singleShot(0,p._check_update)
