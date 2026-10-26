"""Sidebar guide with actionable pages and expandable FAQ."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QHBoxLayout,QVBoxLayout,QListWidget,QStackedWidget,QScrollArea,QWidget,QLabel,QPushButton
from ..components.glass_card import GlassCard
from ..components.starlit_button import StarlitButton
class GuideModal(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent);self.resize(920,650);self.setWindowTitle('Hướng dẫn');self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.Dialog)
        root=QVBoxLayout(self);root.setContentsMargins(0,0,0,0);card=GlassCard();l=QVBoxLayout(card);l.setContentsMargins(32,30,32,30);root.addWidget(card)
        top=QHBoxLayout();top.addWidget(QLabel('HƯỚNG DẪN SỬ DỤNG'));top.addStretch();close=StarlitButton('✕','ghost');close.clicked.connect(self.accept);top.addWidget(close);l.addLayout(top)
        row=QHBoxLayout();side=QListWidget();side.addItems(['Bắt đầu','Cài Việt hóa','Cập nhật','Khôi phục','FAQ']);side.setMaximumWidth(180);row.addWidget(side);stack=QStackedWidget();row.addWidget(stack,1);l.addLayout(row,1)
        pages=[('Bắt đầu',['01 · Chọn đúng bản cài Steam hoặc Yostar trong Tổng quan → Chọn…','02 · Đóng game. Phiên bản game và tài nguyên được đọc từ manifest bản cài. Không xác định được phiên bản sẽ chặn cài.','03 · Chọn gói ngoại tuyến trong Cài đặt hoặc dùng kênh cập nhật đã cấu hình.']),('Cài Việt hóa',['01 · Bấm CÀI / CẬP NHẬT VIỆT HÓA và xác nhận thư mục.','02 · Launcher chỉ cài các tệp được kê khai với SHA256 và kích thước. Manifest chỉ gồm texture sẽ chỉ cài texture; không tự thêm tệp dịch truyện.','03 · Tệp hiện có được sao lưu theo thư mục game. Tệp tạm được đọc lại trước khi thay thế. Khi xảy ra xung đột, giữ nhật ký để phục hồi.','04 · Sau khi cài, chọn Kiểm tra tệp để đối chiếu với biên bản. Chữ hiển thị trong game cần được bạn tự quan sát.']),('Cập nhật',['Bản dịch: dùng CÀI / CẬP NHẬT với manifest phù hợp phiên bản game.','Launcher: Công cụ nâng cao → Kiểm tra cập nhật. Thiếu SHA256 từ máy chủ thì tự cập nhật chưa khả dụng. Không tự áp dụng khi chỉ kiểm tra.','Trước cập nhật game chính thức, có thể khôi phục lần cài đã ghi nhận. Nếu game đã tự cập nhật tệp, launcher sẽ báo xung đột để tránh ghi đè.']),('Khôi phục',['Khôi phục dùng đúng backup trong biên bản cài của thư mục đang chọn. Không lấy backup mới nhất từ game khác.','Các tệp được kiểm tra với hash bản đã cài trước khi phục hồi. Tệp được tạo mới bởi lần cài sẽ được xóa khi phục hồi đúng lần đó.','Nếu thao tác bị ngắt: Công cụ nâng cao → Phục hồi thao tác bị ngắt. Hãy giữ thư mục dữ liệu launcher và backup.','Nếu thiếu hoặc hỏng backup, launcher dừng và báo lỗi. Không tự dựng lại tệp gốc.'])]
        for title,steps in pages:
            scroll=QScrollArea();scroll.setWidgetResizable(True);w=QWidget();vl=QVBoxLayout(w);vl.setSpacing(16);h=QLabel(title);h.setStyleSheet('font-size:22px;color:#62d4ff');vl.addWidget(h)
            for text in steps:lab=QLabel(text);lab.setWordWrap(True);lab.setStyleSheet('font-size:14px;color:#f0f7ff;padding:10px;');vl.addWidget(lab)
            vl.addStretch();scroll.setWidget(w);stack.addWidget(scroll)
        faq=QWidget();fl=QVBoxLayout(faq)
        for question,answer in [('Vì sao gói bị từ chối?','Phiên bản, kích thước hoặc SHA256 không khớp. Hãy tải manifest đúng kênh và đúng phiên bản game.'),('Có cần cài Python để chạy EXE?','Bản EXE đã đóng gói thư viện cần thiết. Bản candidate này chưa được chạy kiểm thử theo yêu cầu của bạn.'),('Ủng hộ ở đâu?','Chưa có thông tin nhận ủng hộ hoặc API người đồng hành được xác minh.'),('Báo lỗi bằng cách nào?','Mở Công cụ nâng cao, làm mới chẩn đoán và sao chép báo cáo. Nhật ký được giữ trong thư mục dữ liệu launcher.')]:
            b=QPushButton('▸ '+question);b.setCheckable(True);lab=QLabel(answer);lab.setWordWrap(True);lab.hide();b.toggled.connect(lab.setVisible);fl.addWidget(b);fl.addWidget(lab)
        fl.addStretch();stack.addWidget(faq);side.currentRowChanged.connect(stack.setCurrentIndex);side.setCurrentRow(0)
        back=StarlitButton('Quay về Tổng quan','secondary');back.clicked.connect(self.accept);l.addWidget(back,0,Qt.AlignmentFlag.AlignRight)
