"""Release notice with plain-text notes and explicit update actions."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QBoxLayout, QFrame, QHBoxLayout, QPlainTextEdit, QSizePolicy

from ..components.art_controls import ArtDivider, text_label
from ..components.modal_shell import ArtDialog
from ..components.starlit_button import StarlitButton


class UpdateNoticeDialog(ArtDialog):
    def __init__(self, version, notes, parent=None, has_launcher_update=False):
        super().__init__(
            'Thông báo cập nhật', 'Thông tin bản phát hành mới', 'info',
            parent, width=860, height=620, panel='panels/update',
        )
        self.root.setSpacing(7)
        self.body.setSpacing(9)
        self._version_text = str(version)
        self._notice_icon = self.header.itemAt(0).widget()
        self._dividers = [self.root.itemAt(i).widget() for i in range(self.root.count())
                          if isinstance(self.root.itemAt(i).widget(), ArtDivider)]

        # Keep the version separate from the notes so it remains easy to find
        # even when the release description is long or empty.
        version_row = QFrame()
        version_row.setObjectName('releaseVersion')
        self.version_row = version_row
        version_row.setStyleSheet(
            'QFrame#releaseVersion {background:#e5f4f3;'
            'border:1px solid #b9dcd8;border-radius:8px;}'
        )
        row = QHBoxLayout(version_row)
        row.setContentsMargins(14, 7, 14, 7)
        row.setSpacing(10)
        caption = text_label('PHIÊN BẢN', 13, '#567286', bold=True)
        caption.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        row.addWidget(caption)
        title = text_label(str(version), 18, '#304679', bold=True, wrap=True)
        title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(title, 1)
        self.body.addWidget(version_row)

        notes_title = text_label('Nội dung cập nhật', 15, '#304679', bold=True)
        self.notes_title = notes_title
        self.body.addWidget(notes_title)
        self.notes_view = QPlainTextEdit()
        self.notes_view.setAccessibleName('Nội dung bản phát hành')
        self.notes_view.setReadOnly(True)
        self.notes_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.notes_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.notes_view.setMinimumHeight(90)
        self.notes_view.setMaximumHeight(155)
        # GitHub release notes are untrusted; render as text, never HTML.
        self.notes_view.setPlainText(notes.strip() or 'Bản phát hành chưa cung cấp mô tả thay đổi.')
        self._compact_notes = False
        self.notes_view.setStyleSheet(self._notes_style(10))
        self.body.addWidget(self.notes_view, 1)

        if has_launcher_update:
            update_btn = StarlitButton('Cập nhật ngay', variant='primary')
            update_btn.clicked.connect(lambda: self.done(3))
            self.footer.addWidget(update_btn, 1)
            later = StarlitButton('Để sau', variant='secondary')
            later.clicked.connect(self.accept)
            self.footer.addWidget(later, 1)
        else:
            close = StarlitButton('Đóng', variant='primary')
            close.clicked.connect(self.accept)
            self.footer.addWidget(close, 1)
        snooze = StarlitButton('Tắt trong 24 giờ', variant='secondary')
        snooze.clicked.connect(lambda: self.done(2))
        self.footer.addWidget(snooze, 1)

        for index in range(self.footer.count()):
            button = self.footer.itemAt(index).widget()
            if isinstance(button, StarlitButton):
                button.setMinimumWidth(0)
                button.setMinimumHeight(52)
        self._responsive_callback = self._adapt_notice

    @staticmethod
    def _notes_style(padding):
        return (
            'QPlainTextEdit {background:#f4f8f8;border:1px solid #c7dcde;'
            f'color:#304679;border-radius:8px;font-size:15px;padding:{padding}px;'
            'selection-background-color:#a8d9d9;}'
            'QScrollBar:vertical {background:transparent;width:9px;margin:5px 2px;}'
            'QScrollBar::handle:vertical {background:#abc9c9;min-height:24px;border-radius:3px;}'
            'QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {height:0;}'
        )

    def _adapt_notice(self, width):
        # On smaller screens move the version into the existing subtitle so
        # that the scrollable notes retain usable space.
        compact = width < 550
        self.version_row.setVisible(not compact)
        self.notes_title.setVisible(not compact)
        self.subtitle.setText('Phiên bản ' + self._version_text if compact else 'Thông tin bản phát hành mới')
        tiny = width < 440
        narrowest = width < 280
        very_compact = width < 350
        if very_compact != self._compact_notes:
            self._compact_notes = very_compact
            self.notes_view.setStyleSheet(self._notes_style(3 if very_compact else 10))
        self.root.setSpacing(3 if very_compact else 7)
        for divider in self._dividers:
            divider.setFixedHeight(4 if very_compact else 14)
        if self._notice_icon:
            self._notice_icon.setVisible(not very_compact)
        heading_font = self.heading.font()
        heading_font.setPixelSize(18 if very_compact else (23 if compact else 27))
        self.heading.setFont(heading_font)
        self.heading.setText('Cập nhật ' + self._version_text if tiny else 'Thông báo cập nhật')
        self.subtitle.setVisible(not tiny)
        self.notes_view.setMinimumHeight(35 if very_compact else (55 if tiny else 90))
        self.notes_view.setMaximumHeight(115 if compact else (100 if width < 650 else 155))
        if tiny:
            # Three stacked 52px buttons would crowd out all text on a phone-
            # sized window. Keep short captions in one reachable action row.
            self.footer.setDirection(QBoxLayout.Direction.LeftToRight)
            for index in range(self.footer.count()):
                button = self.footer.itemAt(index).widget()
                if isinstance(button, StarlitButton):
                    button.setMinimumHeight(44)
                    button.caption_wrap = narrowest
                    action_font = button.font()
                    action_font.setPixelSize(12 if narrowest else (13 if width < 350 else 16))
                    button.setFont(action_font)
                    if button.text() in ('Cập nhật ngay', 'Cập nhật', 'Cập\nnhật'):
                        button.setText('Cập\nnhật' if narrowest else 'Cập nhật')
                    elif button.text() in ('Tắt trong 24 giờ', 'Ẩn 24h', 'Ẩn\n24h'):
                        button.setText('Ẩn\n24h' if narrowest else 'Ẩn 24h')
        else:
            for index in range(self.footer.count()):
                button = self.footer.itemAt(index).widget()
                if isinstance(button, StarlitButton):
                    button.setMinimumHeight(52)
                    button.caption_wrap = True
                    action_font = button.font()
                    action_font.setPixelSize(16)
                    button.setFont(action_font)
                    if button.text() in ('Cập nhật', 'Cập\nnhật'):
                        button.setText('Cập nhật ngay')
                    elif button.text() in ('Ẩn 24h', 'Ẩn\n24h'):
                        button.setText('Tắt trong 24 giờ')
