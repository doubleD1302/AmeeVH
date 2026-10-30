"""Dialog displayed upon successful installation with option to create desktop shortcut."""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton
from ..components.art_controls import ArtCheckBox, AssetImage, text_label
from .confirmation_dialog import InfoGlassCard
from ...core.shortcut import create_game_shortcut, get_desktop_path

class InstallCompletedDialog(ArtDialog):
    def __init__(self, game_info, install_result, shortcut_created_initially=False, parent=None):
        super().__init__(
            title='CÀI ĐẶT HOÀN TẤT',
            subtitle='Dữ liệu Việt hóa Stella Sora đã được cài đặt thành công!',
            icon='check',
            parent=parent,
            width=760,
            height=490,
            panel='panels/dialog'
        )
        self.game_info = game_info
        self.install_result = install_result or {}
        self.launch_game_clicked = False

        self.body.setContentsMargins(12, 6, 12, 6)
        self.body.setSpacing(10)

        # 1. Thẻ thông tin cài đặt
        card_info = InfoGlassCard(self)
        cl = QVBoxLayout(card_info)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(8)

        r1 = QHBoxLayout()
        r1.setSpacing(8)
        r1.addWidget(AssetImage('icons/file_check_cyan', 20))
        r1.addWidget(text_label('KẾT QUẢ CÀI ĐẶT VIỆT HÓA', 12, '#7cd4fd', bold=True))
        r1.addStretch()
        badge = text_label('Thành công', 11, '#63f5aa')
        badge.setStyleSheet('background: rgba(217, 239, 225, 0.95); border: 1px solid #83b79a; color:#305f4f; border-radius: 4px; padding: 2px 8px;')
        r1.addWidget(badge)
        cl.addLayout(r1)

        msg = self.install_result.get('message', 'Đã nạp toàn bộ tệp bản dịch thành công.')
        lbl_msg = text_label(msg, 13, '#eef8ff')
        lbl_msg.setWordWrap(True)
        cl.addWidget(lbl_msg)

        if game_info and getattr(game_info, 'game_path', None):
            lbl_path = text_label(f"Thư mục game: {game_info.game_path}", 12, '#91bfdf')
            lbl_path.setWordWrap(True)
            cl.addWidget(lbl_path)

        self.body.addWidget(card_info)

        # 2. Tuỳ chọn lối tắt màn hình chính (Desktop Shortcut)
        card_sc = InfoGlassCard(self)
        scl = QVBoxLayout(card_sc)
        scl.setContentsMargins(16, 12, 16, 12)
        scl.setSpacing(8)

        s_top = QHBoxLayout()
        s_top.setSpacing(8)
        s_top.addWidget(AssetImage('icons/link_cyan', 20))
        s_top.addWidget(text_label('LỐI TẮT MÀN HÌNH CHÍNH (DESKTOP)', 12, '#7cd4fd', bold=True))
        s_top.addStretch()
        scl.addLayout(s_top)

        sc_row = QHBoxLayout()
        sc_row.setSpacing(10)
        self.cb_shortcut = ArtCheckBox('Thêm lối tắt vào màn hình chính', self)
        self.cb_shortcut.setChecked(True)
        sc_row.addWidget(self.cb_shortcut)
        sc_row.addStretch()

        self.btn_create_now = StarlitButton('Tạo lối tắt ngay', variant='ghost', icon='link')
        self.btn_create_now.setFixedHeight(34)
        self.btn_create_now.clicked.connect(self._create_shortcut_now)
        sc_row.addWidget(self.btn_create_now)
        scl.addLayout(sc_row)

        self.lbl_sc_status = text_label(
            '✓ Đã tạo lối tắt "Stella Sora Việt Hóa" trên màn hình chính.' if shortcut_created_initially
            else 'Tích chọn để tự động tạo lối tắt khởi động game ngoài màn hình chính.',
            12, '#a6d9fa', wrap=True
        )
        scl.addWidget(self.lbl_sc_status)
        self.body.addWidget(card_sc)
        self.body.addStretch()

        # 3. Footer buttons
        self.footer.addStretch()
        btn_close = StarlitButton('Đóng', variant='secondary', icon='check')
        btn_close.setMinimumWidth(130)
        btn_close.setMinimumHeight(44)
        btn_close.clicked.connect(self._on_close)
        self.footer.addWidget(btn_close)

        btn_launch = StarlitButton('Mở game ngay', variant='primary', icon='play')
        btn_launch.setMinimumWidth(160)
        btn_launch.setMinimumHeight(44)
        btn_launch.clicked.connect(self._on_launch)
        self.footer.addWidget(btn_launch)

    def _create_shortcut_now(self):
        if not self.game_info or not getattr(self.game_info, 'game_path', None):
            self.lbl_sc_status.setText('⚠ Không xác định được thư mục game để tạo lối tắt.')
            return
        ok, msg = create_game_shortcut(self.game_info.game_path)
        if ok:
            self.lbl_sc_status.setText('✓ Đã tạo lối tắt "Stella Sora Việt Hóa" trên màn hình chính thành công!')
            self.cb_shortcut.setChecked(True)
        else:
            self.lbl_sc_status.setText(f'⚠ {msg}')

    def _ensure_shortcut(self):
        if self.cb_shortcut.isChecked() and self.game_info and getattr(self.game_info, 'game_path', None):
            desktop = get_desktop_path()
            lnk = desktop / 'Stella Sora Việt Hóa.lnk'
            if not lnk.exists():
                create_game_shortcut(self.game_info.game_path)

    def _on_close(self):
        self._ensure_shortcut()
        self.accept()

    def _on_launch(self):
        self._ensure_shortcut()
        self.launch_game_clicked = True
        self.accept()
