# -*- coding: utf-8 -*-
"""
ConfirmationDialog — Light Porcelain action confirmation modal (v1.3.4 API compatible).

Preserves exact constructor signature:
  ConfirmationDialog(title, message, confirm_label='Xác nhận', cancel_label='Hủy bỏ',
                     is_danger=False, show_shortcut_option=False, shortcut_default=True, parent=None)
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..theme.tokens import PORCELAIN_TOKENS
from ..theme.typography import FS_BODY, FS_BODY_SM, nfc, ui_font
from ..widgets import (
    AccentBannerStrip,
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


class ConfirmationDialog(PorcelainDialog):
    """Light Porcelain modal for confirming install, rollback, restore, or recovery actions."""

    def __init__(
        self,
        title: str,
        message: str,
        confirm_label: str = "Xác nhận",
        cancel_label: str = "Hủy bỏ",
        is_danger: bool = False,
        show_shortcut_option: bool = False,
        shortcut_default: bool = True,
        parent: QWidget | None = None,
        *,
        asset_renderer: AssetRenderer | None = None,
    ) -> None:
        self._renderer = asset_renderer or get_asset_renderer()
        title_str = nfc(title)
        upper_title = title_str.upper()
        is_install = "CÀI" in upper_title
        is_restore = "KHÔI PHỤC" in upper_title or "HOÀN NGUYÊN" in upper_title

        if is_danger:
            icon_path = "game/zs_stage_warning_icon_s.png"
            variant = "error"
        elif is_install:
            icon_path = "game/btn_icon_download.png"
            variant = "default"
        elif is_restore:
            icon_path = "game/btn_icon_back.png"
            variant = "default"
        else:
            icon_path = "game/asar_info.svg"
            variant = "default"

        super().__init__(
            title=title_str,
            meta="Vui lòng kiểm tra thông tin trước khi thực hiện",
            icon_path=icon_path,
            icon_size=(20, 20),
            variant=variant,
            target_width=PORCELAIN_TOKENS.MODAL_WIDTH_CONFIRM,
            asset_renderer=self._renderer,
            parent=parent,
        )
        self.setObjectName("confirmationDialog")
        p = PORCELAIN_TOKENS

        # Parse Thư mục: / Backup: lines into structured KV rows
        lines = [ln.strip() for ln in (message or "").splitlines() if ln.strip()]
        folder_path = ""
        backup_path = ""
        desc_lines: list[str] = []
        for ln in lines:
            if ln.startswith("Thư mục:"):
                folder_path = ln.split("Thư mục:", 1)[1].strip()
            elif ln.startswith("Backup:"):
                backup_path = ln.split("Backup:", 1)[1].strip()
            else:
                desc_lines.append(ln)

        self.scroll_area = _BodyScrollArea(self.frame)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setStyleSheet(f"background: {p.WHITE}; border: none;")

        body = QWidget(self.scroll_area)
        body.setStyleSheet(f"background: {p.WHITE};")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        kv_rows: list[tuple[str, str, str]] = []
        if folder_path:
            kv_rows.append(("Vị trí cài đặt game", folder_path, "mono"))
        if backup_path:
            kv_rows.append(("Bản sao lưu", backup_path, "mono"))

        if kv_rows:
            body_lay.addWidget(PorcelainSectionBar("Thông tin mục tiêu", body))
            target_wrap = QWidget(body)
            target_wrap.setStyleSheet(f"background: {p.PORCELAIN_BG}; border-bottom: 1px solid {p.HAIRLINE};")
            tw_lay = QVBoxLayout(target_wrap)
            tw_lay.setContentsMargins(16, 12, 16, 12)
            tw_lay.setSpacing(0)
            self.target_table = HairlineKeyValueTable(target_wrap)
            self.target_table.set_kv_rows(kv_rows, key_width_pct=0.34)
            tw_lay.addWidget(self.target_table)
            body_lay.addWidget(target_wrap)

        if desc_lines:
            desc_band = QFrame(body)
            desc_band.setStyleSheet(
                f"background: {p.WHITE}; border: none; border-bottom: 1px solid {p.HAIRLINE};"
            )
            d_lay = QVBoxLayout(desc_band)
            d_lay.setContentsMargins(18, 14, 18, 14)
            d_lay.setSpacing(8)
            self.message_label = QLabel(nfc("\n\n".join(desc_lines)), desc_band)
            self.message_label.setFont(ui_font(FS_BODY, 400))
            self.message_label.setWordWrap(True)
            self.message_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.message_label.setStyleSheet(f"color: {p.SLATE_BODY}; background: transparent;")
            d_lay.addWidget(self.message_label)
            body_lay.addWidget(desc_band)

        if is_install:
            body_lay.addWidget(PorcelainSectionBar("Quy trình cài đặt an toàn", body))
            safety_wrap = QWidget(body)
            safety_wrap.setStyleSheet(f"background: {p.PORCELAIN_BG}; border-bottom: 1px solid {p.HAIRLINE};")
            sw_lay = QVBoxLayout(safety_wrap)
            sw_lay.setContentsMargins(16, 10, 16, 10)
            self.safety_table = HairlineKeyValueTable(safety_wrap)
            self.safety_table.set_kv_rows(
                [
                    ("Sao lưu an toàn", "Tự động tạo bản lưu toàn vẹn trước khi nạp dữ liệu mới."),
                    ("Nạp dữ liệu chuẩn", "Cài đặt thoại, bảng text, kỹ năng và giao diện Việt hóa."),
                    ("Hỗ trợ khôi phục", "Dễ dàng quay lại bản gốc sạch của Yostar bất kỳ lúc nào."),
                ],
                key_width_pct=0.32,
            )
            sw_lay.addWidget(self.safety_table)
            body_lay.addWidget(safety_wrap)

        has_shortcut = bool(show_shortcut_option or is_install)
        self.shortcut_checkbox: QCheckBox | None = None
        if has_shortcut:
            sc_band = QFrame(body)
            sc_band.setStyleSheet(
                f"background: {p.WHITE}; border: none; border-bottom: 1px solid {p.HAIRLINE};"
            )
            sc_lay = QHBoxLayout(sc_band)
            sc_lay.setContentsMargins(18, 10, 18, 10)
            self.shortcut_checkbox = QCheckBox(nfc("Thêm lối tắt vào màn hình chính"), sc_band)
            self.shortcut_checkbox.setObjectName("porcelainCheck")
            self.shortcut_checkbox.setFont(ui_font(FS_BODY, 600))
            self.shortcut_checkbox.setChecked(bool(shortcut_default))
            self.shortcut_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            sc_lay.addWidget(self.shortcut_checkbox)
            sc_lay.addStretch(1)
            body_lay.addWidget(sc_band)

        caution_text = (
            "Thao tác này có thể thay đổi dữ liệu game. Hãy đảm bảo StellaSora.exe đã đóng hoàn toàn."
            if is_danger or is_install or is_restore
            else "Bạn có thể hủy bỏ nếu chưa muốn thực hiện ngay lúc này."
        )
        self.caution_strip = AccentBannerStrip(
            "",
            caution_text,
            tone="warn" if is_danger else "info",
            icon_path="game/zs_stage_warning_icon_s.png" if is_danger else "game/asar_info_navy.svg",
            asset_renderer=self._renderer,
            parent=body,
        )
        self.caution_strip.body_label.setFont(ui_font(FS_BODY_SM, 500))
        body_lay.addWidget(self.caution_strip)

        self.scroll_area.setWidget(body)
        self.set_body(self.scroll_area)

        # Footer
        footer = QWidget(self.frame)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(0, 0, 0, 0)
        f_lay.setSpacing(10)
        f_lay.addStretch(1)

        self.btn_cancel = ActionButton(
            cancel_label,
            variant="light_secondary",
            height=34,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_cancel.setMinimumWidth(96)
        self.btn_cancel.clicked.connect(self.reject)
        f_lay.addWidget(self.btn_cancel)

        self.btn_confirm = ActionButton(
            confirm_label,
            variant="faceted_coral" if is_danger else "light_cyan",
            height=34,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_confirm.setMinimumWidth(116)
        self.btn_confirm.clicked.connect(self.accept)
        self.btn_confirm.setDefault(True)
        f_lay.addWidget(self.btn_confirm)

        self.set_footer(footer)
        self._sync_scroll_geometry()
        self.adjustSize()

    def create_shortcut_requested(self) -> bool:
        if self.shortcut_checkbox is None:
            return False
        return bool(self.shortcut_checkbox.isChecked())

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
            self._sync_scroll_geometry()
            self.adjustSize()
            if self.height() > max_h:
                self.resize(self.width(), max_h)
        else:
            self.setMaximumHeight(16777215)
            self._sync_scroll_geometry()
            self.adjustSize()

    def refresh_dpr(self) -> None:
        self.frame.refresh_dpr()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()
