# -*- coding: utf-8 -*-
"""
SupportScreen — Active Light Porcelain donation view (used when SUPPORT_DONATION_ENABLED=True).

Loads resources/support/payment_methods.json, verifies core.safety.sha256_file(qr_path)
against method['qr_sha256'] BEFORE painting QR, paints pixel-exact QR codes with
SmoothPixmapTransform=False inside >=20 DIP #FFFFFF quiet zone, and omits any
team/credits section per Stage 1 r5 user directive.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QEvent, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter
from PySide6.QtWidgets import (
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.config import PathManager
from ...core.error_report import copy_text_native
from ...core.safety import sha256_file
from ..theme.tokens import LAYOUT_TOKENS, PORCELAIN_TOKENS
from ..theme.typography import (
    FS_BODY,
    FS_BODY_SM,
    FS_CAPTION,
    FS_META,
    FS_SUBTITLE,
    nfc,
    ui_font,
)
from ..widgets import (
    AccentBannerStrip,
    ActionButton,
    AssetRenderer,
    HairlineKeyValueTable,
    PorcelainSectionBar,
    PorcelainWindowFrame,
    get_asset_renderer,
)


class _MethodTabBar(QWidget):
    """Underline payment-method tab strip."""

    method_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._active_id: str = ""
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(16, 0, 16, 0)
        self._lay.setSpacing(20)
        self.setStyleSheet(
            f"background: {PORCELAIN_TOKENS.WHITE}; border-bottom: 1px solid {PORCELAIN_TOKENS.HAIRLINE};"
        )

    def set_methods(self, methods: list[dict[str, Any]], active_id: str) -> None:
        while self._lay.count():
            item = self._lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._buttons.clear()
        self._active_id = active_id

        for m in methods:
            mid = str(m.get("id") or "")
            label = f"{m.get('label', '')} ({m.get('provider', '')})"
            btn = QPushButton(nfc(label), self)
            btn.setObjectName("supportMethodTab")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFlat(True)
            btn.clicked.connect(lambda _chk=False, k=mid: self.select(k, emit=True))
            self._lay.addWidget(btn)
            self._buttons[mid] = btn
        self._lay.addStretch(1)
        self._apply_styles()

    def select(self, method_id: str, *, emit: bool = False) -> None:
        if method_id not in self._buttons:
            return
        changed = method_id != self._active_id
        self._active_id = method_id
        self._apply_styles()
        if emit and changed:
            self.method_selected.emit(method_id)

    def _apply_styles(self) -> None:
        p = PORCELAIN_TOKENS
        for mid, btn in self._buttons.items():
            active = mid == self._active_id
            btn.setFont(ui_font(FS_BODY, 700 if active else 500))
            border_c = p.CYAN_ACCENT if active else "transparent"
            color = p.NAVY_TEXT if active else p.SLATE_MUTED
            btn.setStyleSheet(
                f"QPushButton#supportMethodTab {{ border: none; border-bottom: 2.5px solid {border_c}; "
                f"border-radius: 0px; background: transparent; color: {color}; padding: 9px 2px; }}"
                f"QPushButton#supportMethodTab:hover {{ color: {p.NAVY_TEXT}; }}"
            )


class QrCodeWidget(QWidget):
    """Pixel-exact SHA256-verified QR painter with >=20 DIP pure-white quiet zone."""

    QUIET_ZONE_DIP: int = 20
    MAX_QR_LOGICAL_DIP: int = 210

    def __init__(
        self,
        *,
        asset_renderer: AssetRenderer,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self._qr_path: Optional[Path] = None
        self._expected_sha256: str = ""
        self._verified: bool = False
        self._error_message: str = ""
        self._last_logical_side: int = 0
        self.setFixedSize(
            self.MAX_QR_LOGICAL_DIP + 2 * self.QUIET_ZONE_DIP,
            self.MAX_QR_LOGICAL_DIP + 2 * self.QUIET_ZONE_DIP,
        )

    @property
    def is_verified(self) -> bool:
        return self._verified

    @property
    def error_message(self) -> str:
        return self._error_message

    @property
    def last_logical_side(self) -> int:
        return self._last_logical_side

    def verify_integrity(self) -> bool:
        if self._qr_path is None:
            self._verified = False
            self._error_message = "Không tìm thấy tệp mã QR."
            return False
        resolved = self._renderer.resolve_path(self._qr_path)
        if not resolved.is_file():
            self._verified = False
            self._error_message = "Không tìm thấy tệp mã QR."
            return False
        try:
            actual = sha256_file(resolved).lower()
        except OSError:
            self._verified = False
            self._error_message = "Không đọc được tệp mã QR."
            return False
        expected = (self._expected_sha256 or "").strip().lower()
        if not expected or actual != expected:
            self._verified = False
            self._error_message = "Không xác minh được mã QR (SHA256 không khớp)."
            return False
        pix = self._renderer.get_master_pixmap(resolved)
        if pix.isNull() or pix.width() <= 0 or pix.height() <= 0:
            self._verified = False
            self._error_message = "Tệp mã QR không hợp lệ."
            return False
        self._verified = True
        self._error_message = ""
        return True

    def set_qr(self, qr_path: Path | str | None, expected_sha256: str) -> bool:
        self._qr_path = Path(qr_path) if qr_path else None
        self._expected_sha256 = str(expected_sha256 or "").strip().lower()
        ok = self.verify_integrity()
        self.update()
        return ok

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        rect = QRectF(self.rect())
        p = PORCELAIN_TOKENS

        if not self.verify_integrity() or self._qr_path is None:
            painter.setPen(QColor(p.HAIRLINE))
            painter.setBrush(QColor(p.WHITE))
            painter.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))
            painter.setFont(ui_font(FS_BODY_SM, 600))
            painter.setPen(QColor(p.DANGER_TEXT))
            painter.drawText(
                rect.adjusted(18.0, 18.0, -18.0, -18.0),
                int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap),
                nfc(self._error_message or "Không xác minh được mã QR."),
            )
            painter.end()
            return

        resolved = self._renderer.resolve_path(self._qr_path)
        pix = self._renderer.get_master_pixmap(resolved)
        dpr = max(1.0, float(self.devicePixelRatioF()))
        native_min = min(pix.width(), pix.height())
        max_logical = max(1, math.floor(native_min / dpr))
        avail = min(
            max(0.0, rect.width() - 2.0 * self.QUIET_ZONE_DIP),
            max(0.0, rect.height() - 2.0 * self.QUIET_ZONE_DIP),
        )
        side = min(self.MAX_QR_LOGICAL_DIP, max_logical, int(avail))
        self._last_logical_side = side

        # Delegate SHA256-checked, >=20 DIP white quiet-zone, SmoothPixmapTransform=False paint
        # with target rect sized so side matches min(210, floor(native_px / dpr))
        ok = self._renderer.paint_qr(
            painter,
            rect,
            resolved,
            self._expected_sha256,
            dpr,
            quiet_zone=max(self.QUIET_ZONE_DIP, int((rect.width() - side) * 0.5)),
        )
        if not ok:
            painter.setPen(QColor(p.DANGER_TEXT))
            painter.setFont(ui_font(FS_BODY_SM, 600))
            painter.drawText(
                rect.adjusted(18.0, 18.0, -18.0, -18.0),
                int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap),
                nfc("Không xác minh được mã QR (SHA256 không khớp)."),
            )
        painter.end()


class SupportScreen(QWidget):
    """Active donation screen displayed when SUPPORT_DONATION_ENABLED=True."""

    close_requested = Signal()
    toast_requested = Signal(str, str)

    def __init__(
        self,
        *,
        path_manager: PathManager | None = None,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._pm = path_manager
        self._renderer = asset_renderer or get_asset_renderer(
            path_manager.resource_dir if path_manager is not None else None
        )
        self._recipient_name: str = ""
        self._reminder: str = "Bản Việt hoá luôn luôn miễn phí."
        self._methods: list[dict[str, Any]] = []
        self._active_method_id: str = ""

        self._load_payment_methods()

        self.setObjectName("supportScreen")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
        )
        outer.setSpacing(0)

        self.frame = PorcelainWindowFrame(
            "Ủng hộ dự án",
            meta="Dự án phi lợi nhuận · Tự nguyện",
            icon_path="game/Common_Favour_Heart.png",
            icon_size=(22, 22),
            asset_renderer=self._renderer,
            parent=self,
        )
        self.frame.close_requested.connect(self.close_requested.emit)
        outer.addWidget(self.frame)

        body_scroll = QScrollArea(self.frame)
        body_scroll.setFrameShape(QFrame.Shape.NoFrame)
        body_scroll.setWidgetResizable(True)
        body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body_scroll.setStyleSheet(f"background: {PORCELAIN_TOKENS.WHITE}; border: none;")

        body = QWidget(body_scroll)
        body.setStyleSheet(f"background: {PORCELAIN_TOKENS.WHITE};")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        # Free Affirmation Banner
        p = PORCELAIN_TOKENS
        banner = QFrame(body)
        banner.setObjectName("supportFreeBanner")
        banner.setStyleSheet(
            f"QFrame#supportFreeBanner {{ background: {p.OK_TINT}; "
            f"border: none; border-left: 4px solid {p.OK_ACCENT}; border-bottom: 1px solid {p.OK_BORDER}; }}"
        )
        b_lay = QHBoxLayout(banner)
        b_lay.setContentsMargins(18, 8, 18, 8)
        b_lay.setSpacing(14)

        self._banner_chibi = QLabel(banner)
        self._banner_chibi.setFixedSize(40, 44)
        b_lay.addWidget(self._banner_chibi, 0, Qt.AlignmentFlag.AlignVCenter)

        b_copy = QVBoxLayout()
        b_copy.setContentsMargins(0, 0, 0, 0)
        b_copy.setSpacing(2)

        b_title_row = QHBoxLayout()
        b_title_row.setContentsMargins(0, 0, 0, 0)
        b_title_row.setSpacing(7)

        self._banner_star = QLabel(banner)
        self._banner_star.setFixedSize(17, 17)
        b_title_row.addWidget(self._banner_star, 0, Qt.AlignmentFlag.AlignVCenter)

        b_title = QLabel(nfc("Bản Việt hóa Stella Sora hoàn toàn miễn phí"), banner)
        b_title.setFont(ui_font(13.5, 700))
        b_title.setStyleSheet(f"color: {p.OK_TEXT}; background: transparent;")
        b_title_row.addWidget(b_title, 1)
        b_copy.addLayout(b_title_row)

        b_sub = QLabel(
            nfc("Mọi đóng góp đều tự nguyện để hỗ trợ nhóm duy trì dự án — không giới hạn bất kỳ tính năng nào."),
            banner,
        )
        b_sub.setFont(ui_font(FS_BODY_SM, 400))
        b_sub.setWordWrap(True)
        b_sub.setStyleSheet(f"color: {p.OK_SUB}; background: transparent;")
        b_copy.addWidget(b_sub)
        b_lay.addLayout(b_copy, 1)
        body_lay.addWidget(banner)

        # 2-Column Split (1.2 : 0.95)
        self._grid_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(0)

        # Left Column: Kênh ủng hộ + 3-row KV table + Copy + Anti-scam reminder (NO team credits)
        self.left_col = QFrame(body)
        self.left_col.setObjectName("supportLeftCol")
        self.left_col.setStyleSheet(
            f"QFrame#supportLeftCol {{ background: {p.PORCELAIN_BG}; "
            f"border: none; border-right: 1px solid {p.HAIRLINE}; }}"
        )
        left_lay = QVBoxLayout(self.left_col)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        left_lay.addWidget(PorcelainSectionBar("Kênh ủng hộ", self.left_col))

        self.method_tabs = _MethodTabBar(self.left_col)
        self.method_tabs.method_selected.connect(self._on_method_selected)
        left_lay.addWidget(self.method_tabs)

        bank_wrap = QWidget(self.left_col)
        bank_wrap.setStyleSheet(f"background: {p.PORCELAIN_BG};")
        bw_lay = QVBoxLayout(bank_wrap)
        bw_lay.setContentsMargins(16, 12, 16, 12)
        bw_lay.setSpacing(10)

        self.account_table = HairlineKeyValueTable(bank_wrap)
        bw_lay.addWidget(self.account_table)

        act_row = QHBoxLayout()
        act_row.setContentsMargins(0, 0, 0, 0)
        act_row.setSpacing(10)

        self.btn_copy_account = ActionButton(
            "Sao chép số tài khoản",
            variant="light_cyan",
            icon_path="game/btn_icon_copy.png",
            icon_size=(14, 14),
            icon_tint=p.NAVY_TEXT,
            height=32,
            asset_renderer=self._renderer,
            parent=bank_wrap,
        )
        self.btn_copy_account.clicked.connect(self._copy_active_account)
        act_row.addWidget(self.btn_copy_account)

        self.account_note_label = QLabel("", bank_wrap)
        self.account_note_label.setFont(ui_font(FS_META, 500))
        self.account_note_label.setWordWrap(True)
        self.account_note_label.setStyleSheet(f"color: {p.SLATE_MUTED}; background: transparent;")
        act_row.addWidget(self.account_note_label, 1)
        bw_lay.addLayout(act_row)

        left_lay.addWidget(bank_wrap)

        self.reminder_strip = AccentBannerStrip(
            self._reminder,
            "Người chơi không phải trả phí để tải hoặc sử dụng. Cảnh giác mọi hành vi mua bán trái phép.",
            tone="info",
            icon_path="game/asar_info_navy.svg",
            asset_renderer=self._renderer,
            parent=self.left_col,
        )
        left_lay.addWidget(self.reminder_strip)
        left_lay.addStretch(1)

        self._grid_layout.addWidget(self.left_col, 120)

        # Right Column: Pixel-Exact QR Panel
        self.right_col = QFrame(body)
        self.right_col.setObjectName("supportRightCol")
        self.right_col.setStyleSheet(f"QFrame#supportRightCol {{ background: {p.WHITE}; border: none; }}")
        right_lay = QVBoxLayout(self.right_col)
        right_lay.setContentsMargins(22, 18, 22, 18)
        right_lay.setSpacing(12)

        qr_head = QHBoxLayout()
        qr_head.setContentsMargins(0, 0, 0, 0)
        qr_head.setSpacing(8)

        self.qr_badge_label = QLabel("", self.right_col)
        self.qr_badge_label.setFont(ui_font(FS_BODY, 700))
        self.qr_badge_label.setStyleSheet(f"color: {p.NAVY_TEXT}; background: transparent;")
        qr_head.addWidget(self.qr_badge_label, 1)

        self._qr_verify_icon = QLabel(self.right_col)
        self._qr_verify_icon.setFixedSize(12, 12)
        qr_head.addWidget(self._qr_verify_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        self.qr_verify_label = QLabel(nfc("Đã xác thực"), self.right_col)
        self.qr_verify_label.setFont(ui_font(FS_META, 700))
        self.qr_verify_label.setStyleSheet(f"color: {p.OK_TEXT}; background: transparent;")
        qr_head.addWidget(self.qr_verify_label, 0, Qt.AlignmentFlag.AlignVCenter)
        right_lay.addLayout(qr_head)

        right_lay.addStretch(1)

        self.qr_widget = QrCodeWidget(asset_renderer=self._renderer, parent=self.right_col)
        right_lay.addWidget(self.qr_widget, 0, Qt.AlignmentFlag.AlignHCenter)

        self.qr_caption_label = QLabel(
            nfc("Quét bằng ứng dụng ngân hàng hoặc ví điện tử."),
            self.right_col,
        )
        self.qr_caption_label.setFont(ui_font(FS_BODY_SM, 400))
        self.qr_caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_caption_label.setWordWrap(True)
        self.qr_caption_label.setStyleSheet(f"color: {p.SLATE_MUTED}; background: transparent;")
        right_lay.addWidget(self.qr_caption_label, 0, Qt.AlignmentFlag.AlignHCenter)

        right_lay.addStretch(1)
        self._grid_layout.addWidget(self.right_col, 95)

        body_lay.addLayout(self._grid_layout, 1)
        body_scroll.setWidget(body)
        self.frame.set_body(body_scroll)

        self.refresh_dpr()
        self.method_tabs.set_methods(self._methods, self._active_method_id)
        self._render_active_method()

    def _support_dir(self) -> Path:
        base = self._pm.resource_dir if self._pm is not None else self._renderer.resource_dir
        return Path(base) / "support"

    def _load_payment_methods(self) -> None:
        path = self._support_dir() / "payment_methods.json"
        if not path.is_file():
            self._methods = []
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._recipient_name = str(data.get("recipient_name") or "")
            self._reminder = str(data.get("reminder") or self._reminder)
            self._methods = [m for m in data.get("methods", []) if isinstance(m, dict)]
            if self._methods:
                self._active_method_id = str(self._methods[0].get("id") or "")
        except (OSError, ValueError):
            self._methods = []

    @property
    def methods(self) -> list[dict[str, Any]]:
        return list(self._methods)

    def select_method(self, method_id: str) -> None:
        self._active_method_id = method_id
        self.method_tabs.select(method_id, emit=False)
        self._render_active_method()

    def _on_method_selected(self, method_id: str) -> None:
        self._active_method_id = method_id
        self._render_active_method()

    def _active_method(self) -> Optional[dict[str, Any]]:
        for m in self._methods:
            if str(m.get("id") or "") == self._active_method_id:
                return m
        return self._methods[0] if self._methods else None

    def _render_active_method(self) -> None:
        m = self._active_method()
        p = PORCELAIN_TOKENS
        if m is None:
            self.account_table.set_kv_rows(
                [("Trạng thái", "Không có dữ liệu kênh ủng hộ.", "warn")],
                key_width_pct=0.38,
            )
            self.btn_copy_account.setEnabled(False)
            self.qr_widget.set_qr(None, "")
            self._sync_qr_badge(False)
            return

        provider = str(m.get("provider") or "")
        label = str(m.get("label") or "")
        recipient = str(m.get("recipient_name") or self._recipient_name)
        acc_num = m.get("account_number")
        acc_masked = m.get("account_masked") or ""
        display_acc = str(acc_num) if acc_num else str(acc_masked)

        self.account_table.set_kv_rows(
            [
                ("Ngân hàng / Ví", f"{provider} ({label})"),
                ("Chủ tài khoản", recipient),
                ("Số tài khoản", display_acc, "mono"),
            ],
            key_width_pct=0.38,
        )

        has_number = bool(acc_num)
        self.btn_copy_account.setEnabled(has_number)
        self.account_note_label.setText(
            nfc(
                "Số tài khoản khớp với mã QR"
                if has_number
                else "Số ví ẩn một phần — vui lòng quét mã QR trực tiếp"
            )
        )

        self.qr_badge_label.setText(nfc(f"{provider} · {label}"))
        qr_file = str(m.get("qr_file") or "")
        expected_sha = str(m.get("qr_sha256") or "")
        qr_path = (self._support_dir() / qr_file) if qr_file else None
        ok = self.qr_widget.set_qr(qr_path, expected_sha)
        self._sync_qr_badge(ok)

    def _sync_qr_badge(self, ok: bool) -> None:
        p = PORCELAIN_TOKENS
        dpr = max(1.0, float(self.devicePixelRatioF()))
        if ok:
            self.qr_verify_label.setText(nfc("Đã xác thực"))
            self.qr_verify_label.setStyleSheet(f"color: {p.OK_TEXT}; background: transparent;")
            pix = self._renderer.get_icon_pixmap(
                "game/btn_icon_tick.png", (12, 12), dpr, tint=p.OK_TEXT
            )
            self._qr_verify_icon.setPixmap(pix)
            self._qr_verify_icon.setVisible(not pix.isNull())
        else:
            self.qr_verify_label.setText(nfc("Lỗi xác thực"))
            self.qr_verify_label.setStyleSheet(f"color: {p.DANGER_TEXT}; background: transparent;")
            pix = self._renderer.get_icon_pixmap("game/zs_stage_warning_icon_s.png", (12, 12), dpr)
            self._qr_verify_icon.setPixmap(pix)
            self._qr_verify_icon.setVisible(not pix.isNull())

    def _copy_active_account(self) -> None:
        m = self._active_method()
        if not m or not m.get("account_number"):
            return
        acc = str(m["account_number"])
        copy_text_native(acc)
        cb = QGuiApplication.clipboard()
        if cb is not None:
            cb.setText(acc)
        self.toast_requested.emit(
            nfc(f"Đã sao chép số tài khoản {m.get('provider', '')}: {acc}"),
            "success",
        )

    def refresh_dpr(self) -> None:
        dpr = max(1.0, float(self.devicePixelRatioF()))
        chibi = self._renderer.get_icon_pixmap("game/playerhead_main_ccc.png", (40, 44), dpr)
        if not chibi.isNull():
            self._banner_chibi.setPixmap(chibi)
        star = self._renderer.get_icon_pixmap("game/zs_common_star_l_1.png", (17, 17), dpr)
        if not star.isNull():
            self._banner_star.setPixmap(star)
        self._sync_qr_badge(self.qr_widget.is_verified)
        self.qr_widget.update()
        self.frame.refresh_dpr()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.compact_layout(self.width(), self.height())

    def compact_layout(self, width: int, height: int | None = None) -> None:
        p = PORCELAIN_TOKENS
        if int(width) < LAYOUT_TOKENS.TWO_COL_COLLAPSE_THRESHOLD:
            self._grid_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self.left_col.setStyleSheet(
                f"QFrame#supportLeftCol {{ background: {p.PORCELAIN_BG}; "
                f"border: none; border-bottom: 1px solid {p.HAIRLINE}; }}"
            )
        else:
            self._grid_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self.left_col.setStyleSheet(
                f"QFrame#supportLeftCol {{ background: {p.PORCELAIN_BG}; "
                f"border: none; border-right: 1px solid {p.HAIRLINE}; }}"
            )
