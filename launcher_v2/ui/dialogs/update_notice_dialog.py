# -*- coding: utf-8 -*-
"""
UpdateNoticeDialog — Light Porcelain release & update notice modal (v1.3.4 exit codes).

Exact constructor & return codes:
  UpdateNoticeDialog(version, notes, parent=None, has_launcher_update=False, has_translation_update=False)
  - done(2): snooze 24h ('Tắt trong 24 giờ')
  - done(3): launcher update ('Cập nhật ngay')
  - done(4): translation update ('Cập nhật Việt hoá')
  - accept() / Accepted: dismiss ('Để sau' / 'Đóng')
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..theme.tokens import PORCELAIN_TOKENS
from ..theme.typography import FS_BODY, nfc, ui_font
from ..widgets import (
    ActionButton,
    AssetRenderer,
    HairlineKeyValueTable,
    PorcelainDialog,
    PorcelainSectionBar,
    get_asset_renderer,
)


def _activate_subtree_layouts(widget: QWidget | None) -> None:
    if widget is None:
        return
    for child in widget.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
        _activate_subtree_layouts(child)
    lay = widget.layout()
    if lay is not None:
        lay.invalidate()
        lay.activate()
    widget.updateGeometry()


class _BodyScrollArea(QScrollArea):
    """Scroll area that keeps desktop content-hugging sizeHint while allowing compact shrink."""

    def sizeHint(self) -> QSize:  # noqa: N802
        base = super().sizeHint()
        inner = self.widget()
        if inner is not None:
            win = self.window()
            win_w = (win.width() - 4) if win is not None else 0
            vp_w = self.viewport().width() if self.isVisible() else 0
            target_w = max(240, win_w if (win is not None and win_w > 0) else vp_w)
            h = inner.heightForWidth(target_w) if inner.hasHeightForWidth() else inner.sizeHint().height()
            if h <= 0:
                h = inner.sizeHint().height()
            return QSize(base.width(), max(64, h))
        return base

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        base = super().minimumSizeHint()
        return QSize(min(240, base.width()), 64)


class UpdateNoticeDialog(PorcelainDialog):
    """Release notice modal preserving v1.3.4 exit codes (2, 3, 4, Accepted)."""

    def __init__(
        self,
        version: str,
        notes: str,
        parent: QWidget | None = None,
        has_launcher_update: bool = False,
        has_translation_update: bool = False,
        *,
        asset_renderer: AssetRenderer | None = None,
    ) -> None:
        self._renderer = asset_renderer or get_asset_renderer()
        ver_str = str(version or "").strip() or "—"
        super().__init__(
            title="Thông báo cập nhật",
            meta=f"Phiên bản {ver_str}",
            icon_path="game/btn_main_system_notice.png",
            icon_size=(22, 22),
            target_width=PORCELAIN_TOKENS.MODAL_WIDTH_UPDATE_NOTICE,
            asset_renderer=self._renderer,
            parent=parent,
        )
        self.setObjectName("updateNoticeDialog")
        self._version_text = ver_str
        p = PORCELAIN_TOKENS

        self.scroll_area = _BodyScrollArea(self.frame)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setStyleSheet(f"background: {p.WHITE}; border: none;")

        body = QWidget(self.scroll_area)
        body.setStyleSheet(f"background: {p.WHITE};")
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.setSpacing(0)

        ver_wrap = QWidget(body)
        ver_wrap.setStyleSheet(f"background: {p.PORCELAIN_BG}; border-bottom: 1px solid {p.HAIRLINE};")
        vw_lay = QVBoxLayout(ver_wrap)
        vw_lay.setContentsMargins(18, 12, 18, 12)
        vw_lay.setSpacing(0)
        self.version_table = HairlineKeyValueTable(ver_wrap)
        self.version_table.set_kv_rows([("PHIÊN BẢN", ver_str, "mono")], key_width_pct=0.28)
        vw_lay.addWidget(self.version_table)
        b_lay.addWidget(ver_wrap)
        self._ver_wrap = ver_wrap

        self._notes_section_bar = PorcelainSectionBar("Nội dung cập nhật", body)
        b_lay.addWidget(self._notes_section_bar)

        notes_wrap = QWidget(body)
        notes_wrap.setStyleSheet(f"background: {p.WHITE};")
        nw_lay = QVBoxLayout(notes_wrap)
        nw_lay.setContentsMargins(18, 12, 18, 14)
        nw_lay.setSpacing(0)

        self.notes_view = QPlainTextEdit(notes_wrap)
        self.notes_view.setObjectName("porcelainNotes")
        self.notes_view.setAccessibleName(nfc("Nội dung bản phát hành"))
        self.notes_view.setReadOnly(True)
        self.notes_view.setFont(ui_font(FS_BODY, 400))
        self.notes_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.notes_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.notes_view.setMinimumHeight(140)
        self.notes_view.setMaximumHeight(260)
        clean_notes = nfc((notes or "").strip()) or nfc("Bản phát hành chưa cung cấp mô tả thay đổi.")
        self.notes_view.setPlainText(clean_notes)
        nw_lay.addWidget(self.notes_view)
        b_lay.addWidget(notes_wrap, 1)

        self.scroll_area.setWidget(body)
        self.set_body(self.scroll_area)

        # Footer (exact v1.3.4 exit codes: 2=snooze 24h, 3=launcher update, 4=translation update, Accepted=dismiss)
        footer = QWidget(self.frame)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(0, 0, 0, 0)
        f_lay.setSpacing(10)

        self.btn_snooze = ActionButton(
            "Tắt trong 24 giờ",
            variant="light_secondary",
            height=34,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_snooze.clicked.connect(lambda: self.done(2))
        f_lay.addWidget(self.btn_snooze)
        f_lay.addStretch(1)

        if has_launcher_update:
            self.btn_later = ActionButton(
                "Để sau",
                variant="light_secondary",
                height=34,
                asset_renderer=self._renderer,
                parent=footer,
            )
            self.btn_later.clicked.connect(self.accept)
            f_lay.addWidget(self.btn_later)

            self.btn_primary = ActionButton(
                "Cập nhật ngay",
                variant="light_cyan",
                icon_path="game/btn_icon_download.png",
                icon_size=(14, 14),
                icon_tint=p.NAVY_TEXT,
                height=34,
                asset_renderer=self._renderer,
                parent=footer,
            )
            self.btn_primary.clicked.connect(lambda: self.done(3))
            self.btn_primary.setDefault(True)
            f_lay.addWidget(self.btn_primary)
        elif has_translation_update:
            self.btn_later = ActionButton(
                "Để sau",
                variant="light_secondary",
                height=34,
                asset_renderer=self._renderer,
                parent=footer,
            )
            self.btn_later.clicked.connect(self.accept)
            f_lay.addWidget(self.btn_later)

            self.btn_primary = ActionButton(
                "Cập nhật Việt hoá",
                variant="light_cyan",
                icon_path="game/btn_icon_download.png",
                icon_size=(14, 14),
                icon_tint=p.NAVY_TEXT,
                height=34,
                asset_renderer=self._renderer,
                parent=footer,
            )
            self.btn_primary.clicked.connect(lambda: self.done(4))
            self.btn_primary.setDefault(True)
            f_lay.addWidget(self.btn_primary)
        else:
            self.btn_later = None
            self.btn_primary = ActionButton(
                "Đóng",
                variant="light_cyan",
                height=34,
                asset_renderer=self._renderer,
                parent=footer,
            )
            self.btn_primary.clicked.connect(self.accept)
            self.btn_primary.setDefault(True)
            f_lay.addWidget(self.btn_primary)

        self.set_footer(footer)
        self._sync_scroll_geometry()
        self.adjustSize()

    def _sync_scroll_geometry(self) -> None:
        _activate_subtree_layouts(self.scroll_area.widget())
        self.scroll_area.updateGeometry()
        self.frame.body_container.updateGeometry()
        self.frame.updateGeometry()
        self.updateGeometry()
        if self.frame.layout() is not None:
            self.frame.layout().activate()
        if self.layout() is not None:
            self.layout().activate()

    def compact_layout(self, available_width: int, available_height: int | None = None) -> None:
        clamped_w = max(320, min(self._target_width, int(available_width) - 32))
        self.setFixedWidth(clamped_w)
        if available_height is not None:
            max_h = max(240, int(available_height) - 32)
            self.setMaximumHeight(max_h)
            header_h = max(48, self.frame.header_bar.sizeHint().height())
            footer_h = max(52, self.frame.footer_container.sizeHint().height())
            ver_h = max(48, self._ver_wrap.sizeHint().height())
            sec_h = max(32, self._notes_section_bar.sizeHint().height())
            overhead = header_h + footer_h + ver_h + sec_h + 28
            avail_notes = max_h - overhead
            if avail_notes >= 140:
                self.notes_view.setMinimumHeight(140)
                self.notes_view.setMaximumHeight(min(260, avail_notes))
            else:
                target_h = max(64, avail_notes)
                self.notes_view.setMinimumHeight(target_h)
                self.notes_view.setMaximumHeight(max(target_h, min(260, avail_notes)))
            self._sync_scroll_geometry()
            self.adjustSize()
            if self.height() > max_h:
                self.resize(self.width(), max_h)
        else:
            self.setMaximumHeight(16777215)
            self.notes_view.setMinimumHeight(140)
            self.notes_view.setMaximumHeight(260)
            self._sync_scroll_geometry()
            self.adjustSize()

    def refresh_dpr(self) -> None:
        self.frame.refresh_dpr()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()
