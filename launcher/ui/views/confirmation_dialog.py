"""Affecting-action confirmation in the supplied dialog art shell."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import AssetImage, AlertStrip, text_label, ArtCheckBox

class InfoGlassCard(QFrame):
    """High-contrast translucent card for structured information."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: rgba(8, 32, 58, 0.78);
                border: 1px solid rgba(82, 166, 219, 0.38);
                border-radius: 8px;
            }
        """)

class ConfirmationDialog(ArtDialog):
    def __init__(self, title, message, confirm_label='Xác nhận', cancel_label='Hủy bỏ', is_danger=False, show_shortcut_option=False, shortcut_default=True, parent=None):
        subtitle = 'Vui lòng kiểm tra lại thông tin và vị trí trước khi thực hiện.'
        has_shortcut = show_shortcut_option or ('CÀI' in title)
        super().__init__(
            title,
            subtitle,
            'warning' if is_danger else ('download' if 'CÀI' in title else ('restore' if 'KHÔI PHỤC' in title else 'info')),
            parent,
            width=780,
            height=550 if has_shortcut else 510,
            panel='panels/dialog'
        )
        self.heading.setStyleSheet('color:#ffccd5;' if is_danger else 'color:#f0f8ff;')
        self.body.setContentsMargins(10, 4, 10, 4)
        self.body.setSpacing(10)

        # Parse message content
        lines = [l.strip() for l in message.splitlines() if l.strip()]
        folder_path = None
        backup_path = None
        desc_lines = []
        for line in lines:
            if line.startswith('Thư mục:'):
                folder_path = line.split('Thư mục:', 1)[1].strip()
            elif line.startswith('Backup:'):
                backup_path = line.split('Backup:', 1)[1].strip()
            else:
                desc_lines.append(line)

        # 1. Thư mục cài game
        if folder_path:
            folder_box = InfoGlassCard(self)
            fl = QVBoxLayout(folder_box)
            fl.setContentsMargins(16, 12, 16, 12)
            fl.setSpacing(6)

            top_row = QHBoxLayout()
            top_row.setSpacing(8)
            top_row.addWidget(AssetImage('icons/folder_cyan', 18))
            top_row.addWidget(text_label('VỊ TRÍ CÀI ĐẶT GAME', 11, '#7cd4fd', bold=True))
            top_row.addStretch()

            badge = text_label('Đã nhận diện', 11, '#a6d9fa')
            badge.setStyleSheet('background: rgba(24, 76, 118, 0.7); border: 1px solid #4da0d4; border-radius: 4px; padding: 2px 8px;')
            top_row.addWidget(badge)
            fl.addLayout(top_row)

            path_lbl = text_label(folder_path, 13, '#eef8ff', bold=True)
            path_lbl.setWordWrap(True)
            path_lbl.setStyleSheet('color:#eef8ff; font-family: "Consolas", "Courier New", monospace;')
            fl.addWidget(path_lbl)
            self.body.addWidget(folder_box)

        # 2. Thư mục backup (nếu có)
        if backup_path:
            b_box = InfoGlassCard(self)
            bl = QVBoxLayout(b_box)
            bl.setContentsMargins(16, 10, 16, 10)
            bl.setSpacing(4)
            b_top = QHBoxLayout()
            b_top.setSpacing(8)
            b_top.addWidget(AssetImage('icons/restore_cyan', 18))
            b_top.addWidget(text_label('BẢN SAO LƯU DỰ PHÒNG', 11, '#92d5f7', bold=True))
            b_top.addStretch()
            bl.addLayout(b_top)
            bl.addWidget(text_label(backup_path, 13, '#e0f2fe'))
            self.body.addWidget(b_box)

        # 3. Khối mô tả / tính năng
        scope_box = InfoGlassCard(self)
        sl = QVBoxLayout(scope_box)
        sl.setContentsMargins(16, 12, 16, 12)
        sl.setSpacing(8)

        if 'CÀI' in title:
            features = [
                ('icons/shield_cyan', 'Sao lưu an toàn', 'Tự động tạo bản lưu toàn vẹn trước khi nạp dữ liệu mới.'),
                ('icons/file_check_cyan', 'Nạp dữ liệu chuẩn', 'Cài đặt thoại, bảng text, kỹ năng và texture banner Việt hóa.'),
                ('icons/restore_cyan', 'Hỗ trợ khôi phục', 'Dễ dàng quay lại bản gốc bất kỳ lúc nào với 1 cú click.')
            ]
            for icon_name, heading, detail in features:
                row = QHBoxLayout()
                row.setSpacing(10)
                row.addWidget(AssetImage(icon_name, 18))
                t_lbl = text_label(f'{heading}: ', 13, '#bce4fc', bold=True)
                d_lbl = text_label(detail, 13, '#d3ecfc')
                d_lbl.setWordWrap(True)
                row.addWidget(t_lbl)
                row.addWidget(d_lbl, 1)
                sl.addLayout(row)
        else:
            for d in desc_lines:
                row = QHBoxLayout()
                row.setSpacing(10)
                row.addWidget(AssetImage('icons/info_cyan', 18))
                lbl = text_label(d, 13, '#d3ecfc', wrap=True)
                row.addWidget(lbl, 1)
                sl.addLayout(row)

        self.body.addWidget(scope_box)

        # Tuỳ chọn lối tắt màn hình chính khi cài đặt
        self.cb_shortcut = None
        if has_shortcut:
            sc_box = InfoGlassCard(self)
            scl = QHBoxLayout(sc_box)
            scl.setContentsMargins(16, 8, 16, 8)
            scl.setSpacing(10)
            self.cb_shortcut = ArtCheckBox('Thêm lối tắt vào màn hình chính', self)
            self.cb_shortcut.setChecked(shortcut_default)
            scl.addWidget(self.cb_shortcut)
            scl.addStretch()
            self.body.addWidget(sc_box)

        # Alert Strip
        alert = AlertStrip('Dữ liệu game chỉ được thay đổi sau khi bạn bấm xác nhận.', 'warning' if is_danger else 'info')
        self.body.addWidget(alert)
        self.body.addStretch()

        # Footer buttons
        self.footer.addStretch()
        cancel = StarlitButton(cancel_label, variant='secondary', icon='close')
        cancel.setMinimumWidth(130)
        cancel.setMinimumHeight(44)
        cancel.clicked.connect(self.reject)
        self.footer.addWidget(cancel)

        confirm = StarlitButton(confirm_label, variant='danger' if is_danger else 'primary', icon='check')
        confirm.setMinimumWidth(160)
        confirm.setMinimumHeight(44)
        confirm.clicked.connect(self.accept)
        self.footer.addWidget(confirm)

    def create_shortcut_requested(self) -> bool:
        return bool(self.cb_shortcut and self.cb_shortcut.isChecked())
