# -*- coding: utf-8 -*-
"""
OverviewScreen — Official Atmospheric HUD for Stella Sora Việt Hóa PC Launcher v2.0.

Implements Preview r5 layout:
- Floating ultra-HD game logo (zero dark backing box, zero QGraphicsEffect)
- Unboxed star free-translation subtitle button emitting support_requested
- Translucent dark-navy Latest Notices GlassCard with Common_Line_03.png divider & 3 flat rows
- Translucent dark-navy Action Control Dock with metadata row, PathSelector, 9-slice CTAs
  (btn_common_db_l_1 / btn_common_db_l_2), conditional blocker/official-notice link,
  inline ProgressPanel, and unified 3-column bottom utility strip
- Responsive compact breakpoint (width < 1000 or height < 620 DIP) inside a vertical QScrollArea
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QEvent, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
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

from ...core.types import GameInfo, NotificationItem, OperationEvent, OperationPhase
from ..theme.adaptive_scrim import AdaptiveScrimSpec
from ..theme.tokens import LAYOUT_TOKENS, OV_TOKENS, rgba_css
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
    ActionButton,
    AssetRenderer,
    GlassCard,
    PathSelector,
    PlatformTag,
    ProgressPanel,
    StatusInline,
    get_asset_renderer,
)

_LOGO_ASPECT = 2152.0 / 856.0


def _category_label(category: str) -> str:
    cat = (category or "").strip().lower()
    if cat in ("release", "project"):
        return "Phát hành"
    if cat == "guide":
        return "Hướng dẫn"
    return "Lưu ý"


class _HeroLogoWidget(QWidget):
    """Paints branding/logo_ultrahd_2152x856.png directly from master with subtle QPainter shadow."""

    def __init__(
        self,
        *,
        asset_renderer: AssetRenderer,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self._target_h = 82
        self.setAutoFillBackground(False)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._sync_size()

    def set_logo_height(self, height_dip: int) -> None:
        h = max(48, int(height_dip))
        if h != self._target_h:
            self._target_h = h
            self._sync_size()
            self.update()

    def _sync_size(self) -> None:
        w = max(120, round(self._target_h * _LOGO_ASPECT))
        self.setFixedSize(w, self._target_h)

    def paintEvent(self, event) -> None:  # noqa: N802
        master = self._renderer.get_master_pixmap("branding/logo_ultrahd_2152x856.png")
        if master.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        rect = QRectF(self.rect())
        # Subtle pure-QPainter shadow directly from tinted master (no QGraphicsDropShadowEffect)
        shadow = self._renderer.get_tinted_pixmap(
            "branding/logo_ultrahd_2152x856.png", QColor(8, 20, 44, 110)
        )
        if not shadow.isNull():
            self._renderer.paint_contain(
                painter,
                rect.translated(0.0, 2.5),
                shadow,
                align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            )

        self._renderer.paint_contain(
            painter,
            rect,
            master,
            align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        painter.end()


class _CyanCircleDot(QWidget):
    """7x7 #25C8CE circle indicator at 0.45 opacity for the 3rd compact notice row."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(11, 11)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        c = QColor(OV_TOKENS.CYAN_ACCENT)
        c.setAlphaF(0.45)
        painter.setBrush(c)
        painter.drawEllipse(QRectF(2.0, 2.0, 7.0, 7.0))
        painter.end()


class _ElidedNoticeTitle(QLabel):
    """Single-line elided title label inside Overview notice rows."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_text = nfc(text)
        self.setMinimumWidth(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_full_text(self, text: str) -> None:
        self._full_text = nfc(text)
        self.setToolTip(self._full_text)
        self._apply_elide()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_elide()

    def _apply_elide(self) -> None:
        avail = max(30, self.width() - 2)
        super().setText(self.fontMetrics().elidedText(self._full_text, Qt.TextElideMode.ElideRight, avail))


class _OverviewNoticeRow(QPushButton):
    """Flat 34 DIP notice row with bottom hairline and hover tint."""

    clicked_with_id = Signal(str)

    def __init__(
        self,
        item: NotificationItem,
        index: int,
        *,
        is_last: bool,
        asset_renderer: AssetRenderer,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._item_id = item.id
        self._renderer = asset_renderer
        self._index = index
        self._is_last = is_last

        self.setObjectName("ovNoticeRow")
        self.setFixedHeight(34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        hover_css = rgba_css(OV_TOKENS.ROW_HOVER_RGBA)
        border_rule = (
            "border-bottom: none;"
            if is_last
            else f"border-bottom: 1px solid {rgba_css(OV_TOKENS.HAIRLINE_ROW_RGBA)};"
        )
        self.setStyleSheet(
            f"QPushButton#ovNoticeRow {{ border: none; {border_rule} border-radius: 0px; "
            f"background: transparent; text-align: left; padding: 0 4px; }}"
            f"QPushButton#ovNoticeRow:hover {{ background: {hover_css}; }}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 0, 4, 0)
        lay.setSpacing(8)

        self.badge_holder = QWidget(self)
        badge_lay = QHBoxLayout(self.badge_holder)
        badge_lay.setContentsMargins(0, 0, 0, 0)
        badge_lay.setSpacing(0)

        self._sprite_lbl: Optional[QLabel] = None
        if index == 0:
            self._sprite_lbl = QLabel(self.badge_holder)
            self._sprite_lbl.setFixedSize(42, 15)
            badge_lay.addWidget(self._sprite_lbl)
        elif index == 1:
            self._sprite_lbl = QLabel(self.badge_holder)
            self._sprite_lbl.setFixedSize(11, 11)
            badge_lay.addWidget(self._sprite_lbl)
        else:
            badge_lay.addWidget(_CyanCircleDot(self.badge_holder))
        lay.addWidget(self.badge_holder, 0, Qt.AlignmentFlag.AlignVCenter)

        cat_lbl = QLabel(nfc(f"[{_category_label(item.category)}]"), self)
        cat_lbl.setFont(ui_font(FS_CAPTION, 700))
        cat_lbl.setStyleSheet(f"color: {OV_TOKENS.CAT_SKY}; background: transparent;")
        cat_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        lay.addWidget(cat_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        title_lbl = _ElidedNoticeTitle(item.title, self)
        title_lbl.setFont(ui_font(FS_BODY, 500))
        title_lbl.setStyleSheet(f"color: {OV_TOKENS.TEXT_NOTICE_ROW}; background: transparent;")
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        lay.addWidget(title_lbl, 1, Qt.AlignmentFlag.AlignVCenter)

        date_lbl = QLabel(nfc(item.date), self)
        date_lbl.setFont(ui_font(FS_CAPTION, 400, tabular=True))
        date_lbl.setStyleSheet(f"color: {OV_TOKENS.TEXT_MUTED}; background: transparent;")
        date_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        lay.addWidget(date_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        self.refresh_dpr()
        self.clicked.connect(lambda: self.clicked_with_id.emit(self._item_id))

    def refresh_dpr(self) -> None:
        if self._sprite_lbl is None:
            return
        dpr = max(1.0, float(self.devicePixelRatioF()))
        if self._index == 0:
            pix = self._renderer.get_icon_pixmap("game/zs_common_new_1.png", (42, 15), dpr)
        else:
            pix = self._renderer.get_icon_pixmap("game/zs_common_new_4.png", (11, 11), dpr)
        if not pix.isNull():
            self._sprite_lbl.setPixmap(pix)

    def sizeHint(self) -> QSize:  # noqa: N802
        lay = self.layout()
        w = lay.sizeHint().width() if lay is not None else 240
        return QSize(max(120, w), 34)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        lay = self.layout()
        w = lay.minimumSize().width() if lay is not None else 120
        return QSize(max(120, w), 34)


class _WrappingNoticeButton(QPushButton):
    """Clickable warning/notice link that wraps cleanly inside narrow docks without clipping."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self._text = ""
        self._icon_size = QSize(14, 14)

        self.setObjectName("ovWhyDisabledBtn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(
            "QPushButton#ovWhyDisabledBtn { border: none; background: transparent; padding: 0px; text-align: left; }"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 1, 0, 1)
        lay.setSpacing(6)

        self._icon_lbl = QLabel(self)
        self._icon_lbl.setFixedSize(self._icon_size)
        self._icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        lay.addWidget(self._icon_lbl, 0, Qt.AlignmentFlag.AlignTop)

        self._text_lbl = QLabel("", self)
        self._text_lbl.setFont(ui_font(FS_META, 500))
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setStyleSheet(
            f"color: {OV_TOKENS.WARN_AMBER}; background: transparent; border: none;"
        )
        self._text_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        lay.addWidget(self._text_lbl, 1, Qt.AlignmentFlag.AlignVCenter)

    def setText(self, text: str) -> None:  # noqa: N802
        self._text = nfc(text)
        self._text_lbl.setText(self._text)
        self.updateGeometry()

    def text(self) -> str:
        return self._text

    def setIcon(self, icon) -> None:  # noqa: N802
        pix = icon.pixmap(self._icon_size) if icon is not None else QPixmap()
        self._icon_lbl.setPixmap(pix)
        self._icon_lbl.setVisible(not pix.isNull())

    def setIconSize(self, size: QSize) -> None:  # noqa: N802
        self._icon_size = QSize(size)
        self._icon_lbl.setFixedSize(self._icon_size)

    def enterEvent(self, event) -> None:  # noqa: N802
        f = self._text_lbl.font()
        f.setUnderline(True)
        self._text_lbl.setFont(f)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        f = self._text_lbl.font()
        f.setUnderline(False)
        self._text_lbl.setFont(f)
        super().leaveEvent(event)

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        text_w = max(80, int(width) - self._icon_size.width() - 6)
        br = self._text_lbl.fontMetrics().boundingRect(
            QRect(0, 0, text_w, 2000),
            int(Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap),
            self._text,
        )
        return max(self._icon_size.height() + 2, br.height() + 2)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(120, self.heightForWidth(374))

    def sizeHint(self) -> QSize:  # noqa: N802
        avail_w = 0
        p = self.parentWidget()
        if p is not None and p.width() > 60:
            avail_w = max(160, p.width() - 36)
        unwrapped_w = (
            self._icon_size.width()
            + 6
            + self._text_lbl.fontMetrics().horizontalAdvance(self._text)
            + 2
        )
        target_w = min(unwrapped_w, avail_w) if avail_w > 0 else unwrapped_w
        target_w = max(120, target_w)
        return QSize(target_w, self.heightForWidth(target_w))


class OverviewScreen(QWidget):
    """Main Overview atmospheric HUD screen matching Preview r5."""

    install_requested = Signal()
    launch_requested = Signal()
    verify_requested = Signal()
    rollback_requested = Signal()
    check_updates_requested = Signal()
    cancel_operation_requested = Signal()
    detect_games_requested = Signal()
    browse_game_requested = Signal()
    open_notifications_requested = Signal(object)  # Optional[str] notification_id
    open_error_requested = Signal(str)
    official_restore_requested = Signal()
    support_requested = Signal()
    path_copied = Signal(str)
    open_folder_requested = Signal(str)

    def __init__(
        self,
        *,
        asset_renderer: AssetRenderer | None = None,
        reduced_motion: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer or get_asset_renderer()
        self._reduced_motion = bool(reduced_motion)
        self._game_info = GameInfo()
        self._has_pending_recovery = False
        self._translation_state: dict = {}
        self._official_notice: Optional[dict] = None
        self._op_active = False
        self._notice_rows: list[_OverviewNoticeRow] = []
        self._is_compact = False
        self._why_mode: str = ""
        self._why_code: str = ""

        self.setObjectName("overviewScreen")
        self.setAutoFillBackground(False)
        self.setStyleSheet("QWidget#overviewScreen { background: transparent; }")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("overviewScrollArea")
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setAutoFillBackground(False)
        self.scroll_area.viewport().setAutoFillBackground(False)
        self.scroll_area.viewport().setStyleSheet("background: transparent;")
        self.scroll_area.setStyleSheet("QScrollArea#overviewScrollArea { background: transparent; border: none; }")
        self.scroll_area.verticalScrollBar().valueChanged.connect(
            lambda _v: self.window().update() if self.window() is not None else None
        )
        outer.addWidget(self.scroll_area)

        self._viewport_widget = QWidget(self.scroll_area)
        self._viewport_widget.setObjectName("overviewViewport")
        self._viewport_widget.setAutoFillBackground(False)
        self._viewport_widget.setStyleSheet("QWidget#overviewViewport { background: transparent; }")
        self.scroll_area.setWidget(self._viewport_widget)

        self._grid_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self._viewport_widget)
        self._grid_layout.setContentsMargins(
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
        )
        self._grid_layout.setSpacing(20)

        # ---------------- Left Column: Hero Logo + Subtitle + Compact Notices ----------------
        self.left_col = QWidget(self._viewport_widget)
        self.left_col.setAutoFillBackground(False)
        self.left_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._left_layout = QVBoxLayout(self.left_col)
        self._left_layout.setContentsMargins(0, 8, 0, 0)
        self._left_layout.setSpacing(12)

        hero_block = QVBoxLayout()
        hero_block.setContentsMargins(0, 0, 0, 0)
        hero_block.setSpacing(8)

        self.hero_logo = _HeroLogoWidget(asset_renderer=self._renderer, parent=self.left_col)
        hero_block.addWidget(self.hero_logo, 0, Qt.AlignmentFlag.AlignLeft)

        self.free_subtitle_btn = QPushButton(nfc("Bản Việt hóa miễn phí · Không thương mại"), self.left_col)
        self.free_subtitle_btn.setObjectName("overviewFreeSubtitleBtn")
        self.free_subtitle_btn.setFont(ui_font(FS_SUBTITLE, 600))
        self.free_subtitle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.free_subtitle_btn.setFlat(True)
        self.free_subtitle_btn.setToolTip(nfc("Xem thông tin bản Việt hóa miễn phí"))
        self.free_subtitle_btn.setStyleSheet(
            f"QPushButton#overviewFreeSubtitleBtn {{ border: none; background: transparent; "
            f"color: #FFFFFF; padding: 2px 0px; text-align: left; }}"
            f"QPushButton#overviewFreeSubtitleBtn:hover {{ color: {OV_TOKENS.LINK_SKY_HOVER}; "
            f"text-decoration: underline; }}"
        )
        self.free_subtitle_btn.clicked.connect(self.support_requested.emit)
        hero_block.addWidget(self.free_subtitle_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self._left_layout.addLayout(hero_block)
        self._left_stretch = self._left_layout.addStretch(1)

        # Latest Notices Panel
        self.notif_compact_panel = GlassCard(
            variant="panel", asset_renderer=self._renderer, parent=self.left_col
        )
        self.notif_compact_panel.setMaximumWidth(560)
        self.notif_compact_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        nc_lay = self.notif_compact_panel.content_layout()

        head_row = QHBoxLayout()
        head_row.setContentsMargins(0, 0, 0, 0)
        head_row.setSpacing(8)

        self._notif_head_icon = QLabel(self.notif_compact_panel)
        self._notif_head_icon.setFixedSize(18, 18)
        head_row.addWidget(self._notif_head_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        notif_title = QLabel(nfc("Thông báo mới"), self.notif_compact_panel)
        notif_title.setFont(ui_font(14.0, 700))
        notif_title.setStyleSheet("color: #FFFFFF; background: transparent;")
        head_row.addWidget(notif_title, 0, Qt.AlignmentFlag.AlignVCenter)
        head_row.addStretch(1)

        self.view_all_notifs_btn = QPushButton(nfc("Tất cả"), self.notif_compact_panel)
        self.view_all_notifs_btn.setObjectName("ovAllNotifsBtn")
        self.view_all_notifs_btn.setFont(ui_font(FS_BODY, 600))
        self.view_all_notifs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_all_notifs_btn.setFlat(True)
        self.view_all_notifs_btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.view_all_notifs_btn.setStyleSheet(
            f"QPushButton#ovAllNotifsBtn {{ border: none; background: transparent; "
            f"color: {OV_TOKENS.LINK_SKY}; padding: 2px 4px; }}"
            f"QPushButton#ovAllNotifsBtn:hover {{ color: {OV_TOKENS.LINK_SKY_HOVER}; "
            f"text-decoration: underline; }}"
        )
        self.view_all_notifs_btn.clicked.connect(lambda: self.open_notifications_requested.emit(None))
        head_row.addWidget(self.view_all_notifs_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        nc_lay.addLayout(head_row)

        self.notif_compact_panel.add_luminous_divider()

        self.notif_list_host = QWidget(self.notif_compact_panel)
        self.notif_list_host.setAutoFillBackground(False)
        self._notif_list_layout = QVBoxLayout(self.notif_list_host)
        self._notif_list_layout.setContentsMargins(0, 0, 0, 0)
        self._notif_list_layout.setSpacing(0)
        nc_lay.addWidget(self.notif_list_host)

        self._empty_notif_label = QLabel(nfc("Chưa có thông báo."), self.notif_list_host)
        self._empty_notif_label.setFont(ui_font(FS_BODY_SM, 400))
        self._empty_notif_label.setStyleSheet(f"color: {OV_TOKENS.TEXT_MUTED}; padding: 8px 4px; background: transparent;")
        self._notif_list_layout.addWidget(self._empty_notif_label)

        self._left_layout.addWidget(self.notif_compact_panel)
        self._grid_layout.addWidget(self.left_col, 1)

        # ---------------- Right Column: Action Control Dock ----------------
        self.right_col = QWidget(self._viewport_widget)
        self.right_col.setAutoFillBackground(False)
        self.right_col.setFixedWidth(454)
        self.right_col.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._right_layout = QVBoxLayout(self.right_col)
        self._right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_layout.setSpacing(0)
        self._right_layout.addStretch(1)

        self.action_dock_panel = GlassCard(
            variant="dock", asset_renderer=self._renderer, parent=self.right_col
        )
        dock_lay = self.action_dock_panel.content_layout()
        dock_lay.setContentsMargins(0, 16, 0, 0)
        dock_lay.setSpacing(0)

        dock_inner = QWidget(self.action_dock_panel)
        dock_inner.setAutoFillBackground(False)
        inner_lay = QVBoxLayout(dock_inner)
        inner_lay.setContentsMargins(18, 0, 18, 10)
        inner_lay.setSpacing(11)

        # 1. Metadata Row
        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(7)

        self._platform_emblem = QLabel(dock_inner)
        self._platform_emblem.setFixedSize(18, 18)
        meta_row.addWidget(self._platform_emblem, 0, Qt.AlignmentFlag.AlignVCenter)

        self.platform_tag = PlatformTag("Chưa rõ", surface="dark", parent=dock_inner)
        meta_row.addWidget(self.platform_tag, 0, Qt.AlignmentFlag.AlignVCenter)

        self.version_label = QLabel(nfc("Chưa xác định"), dock_inner)
        self.version_label.setFont(ui_font(FS_META, 500, tabular=True))
        self.version_label.setStyleSheet(f"color: {OV_TOKENS.TEXT_SECONDARY}; background: transparent;")
        meta_row.addWidget(self.version_label, 1, Qt.AlignmentFlag.AlignVCenter)

        self.patch_status_inline = StatusInline(
            "Chưa cài", tone="muted", surface="dark", asset_renderer=self._renderer, parent=dock_inner
        )
        meta_row.addWidget(self.patch_status_inline, 0, Qt.AlignmentFlag.AlignVCenter)
        inner_lay.addLayout(meta_row)

        # 2. PathSelector
        self.path_selector = PathSelector(
            None,
            caption="Thư mục game",
            placeholder="Chưa chọn thư mục game",
            asset_renderer=self._renderer,
            parent=dock_inner,
        )
        self.path_selector.detect_requested.connect(self.detect_games_requested.emit)
        self.path_selector.browse_requested.connect(self.browse_game_requested.emit)
        self.path_selector.path_copied.connect(self.path_copied.emit)
        self.path_selector.open_folder_requested.connect(self.open_folder_requested.emit)
        inner_lay.addWidget(self.path_selector)

        # 3. Primary CTA Row (ratio 1.45 : 1, height 46 DIP)
        cta_row = QHBoxLayout()
        cta_row.setContentsMargins(0, 0, 0, 0)
        cta_row.setSpacing(10)

        self.btn_install_patch = ActionButton(
            "Cài Việt hoá",
            variant="faceted_cyan",
            icon_path="game/btn_icon_download.png",
            icon_size=(15, 15),
            icon_tint=OV_TOKENS.CTA_ICE_TEXT,
            height=46,
            reduced_motion=self._reduced_motion,
            asset_renderer=self._renderer,
            parent=dock_inner,
        )
        self.btn_install_patch.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_install_patch.clicked.connect(self.install_requested.emit)
        cta_row.addWidget(self.btn_install_patch, 145)

        self.btn_launch_game = ActionButton(
            "Chơi game",
            variant="faceted_ice",
            icon_path="game/btn_icon_play.png",
            icon_size=(15, 15),
            icon_tint=OV_TOKENS.CTA_ICE_TEXT,
            height=46,
            reduced_motion=self._reduced_motion,
            asset_renderer=self._renderer,
            parent=dock_inner,
        )
        self.btn_launch_game.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_launch_game.clicked.connect(self.launch_requested.emit)
        cta_row.addWidget(self.btn_launch_game, 100)
        inner_lay.addLayout(cta_row)

        # 4. Conditional Blocker / Official Notice Link
        self.why_disabled_btn = _WrappingNoticeButton(dock_inner)
        self.why_disabled_btn.clicked.connect(self._on_why_clicked)
        self.why_disabled_btn.setVisible(False)
        inner_lay.addWidget(self.why_disabled_btn)

        # 5. Inline ProgressPanel
        self.progress_panel = ProgressPanel(
            reduced_motion=self._reduced_motion,
            asset_renderer=self._renderer,
            parent=dock_inner,
        )
        self.progress_panel.cancel_requested.connect(self.cancel_operation_requested.emit)
        inner_lay.addWidget(self.progress_panel)

        dock_lay.addWidget(dock_inner)

        # 6. Unified 3-Column Bottom Utility Strip (flush edge-to-edge)
        self.secondary_toolbar = QFrame(self.action_dock_panel)
        self.secondary_toolbar.setObjectName("ovSecondaryToolbar")
        self.secondary_toolbar.setStyleSheet(
            f"QFrame#ovSecondaryToolbar {{ background: transparent; border: none; "
            f"border-top: 1px solid {rgba_css(OV_TOKENS.TOOLBAR_DIVIDER_RGBA)}; }}"
        )
        tb_lay = QHBoxLayout(self.secondary_toolbar)
        tb_lay.setContentsMargins(0, 0, 0, 0)
        tb_lay.setSpacing(0)

        self.btn_verify_files = ActionButton(
            "Kiểm tra tệp",
            variant="flat_toolbar",
            icon_path="game/btn_common_check.png",
            icon_size=(18, 18),
            height=36,
            right_divider=True,
            reduced_motion=self._reduced_motion,
            asset_renderer=self._renderer,
            parent=self.secondary_toolbar,
        )
        self.btn_verify_files.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_verify_files.clicked.connect(self.verify_requested.emit)
        tb_lay.addWidget(self.btn_verify_files, 1)

        self.btn_restore_vanilla = ActionButton(
            "Khôi phục gốc",
            variant="flat_toolbar",
            icon_path="game/btn_icon_back.png",
            icon_size=(14, 14),
            height=36,
            right_divider=True,
            reduced_motion=self._reduced_motion,
            asset_renderer=self._renderer,
            parent=self.secondary_toolbar,
        )
        self.btn_restore_vanilla.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_restore_vanilla.clicked.connect(self.rollback_requested.emit)
        tb_lay.addWidget(self.btn_restore_vanilla, 1)

        self.btn_check_updates = ActionButton(
            "Tìm bản mới",
            variant="flat_toolbar",
            icon_path="game/btn_common_refresh.png",
            icon_size=(14, 14),
            icon_tint="#FFFFFF",
            height=36,
            right_divider=False,
            reduced_motion=self._reduced_motion,
            asset_renderer=self._renderer,
            parent=self.secondary_toolbar,
        )
        self.btn_check_updates.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_check_updates.clicked.connect(self.check_updates_requested.emit)
        tb_lay.addWidget(self.btn_check_updates, 1)

        dock_lay.addWidget(self.secondary_toolbar)
        self._right_layout.addWidget(self.action_dock_panel)
        self._grid_layout.addWidget(self.right_col, 0)

        self.refresh_dpr()
        self._sync_action_states()

    def _on_why_clicked(self) -> None:
        if self._why_mode == "blocker" and self._why_code:
            self.open_error_requested.emit(self._why_code)
        elif self._why_mode == "official":
            self.official_restore_requested.emit()

    def refresh_dpr(self) -> None:
        dpr = max(1.0, float(self.devicePixelRatioF()))
        self.free_subtitle_btn.setIcon(
            self._renderer.get_icon("game/zs_common_star_l_1.png", (17, 17), dpr)
        )
        self.free_subtitle_btn.setIconSize(QSize(17, 17))

        head_pix = self._renderer.get_icon_pixmap("game/btn_main_system_notice.png", (18, 18), dpr)
        if not head_pix.isNull():
            self._notif_head_icon.setPixmap(head_pix)

        self.view_all_notifs_btn.setIcon(
            self._renderer.get_icon(
                "game/btn_icon_main_next.png", (9, 13), dpr, tint=OV_TOKENS.LINK_SKY
            )
        )
        self.view_all_notifs_btn.setIconSize(QSize(9, 13))

        emblem_pix = self._renderer.get_icon_pixmap("game/zs_agent_logo_1.png", (18, 18), dpr)
        if not emblem_pix.isNull():
            self._platform_emblem.setPixmap(emblem_pix)

        self.why_disabled_btn.setIcon(
            self._renderer.get_icon("game/zs_stage_warning_icon_s.png", (14, 14), dpr)
        )
        self.why_disabled_btn.setIconSize(QSize(14, 14))

        self.path_selector._refresh_icons()
        for row in self._notice_rows:
            row.refresh_dpr()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.compact_layout(self.width(), self.height())

    def compact_layout(self, width: int, height: int | None = None) -> None:
        w = int(width)
        h = int(height) if height is not None else self.height()
        # MainShell passes body dimensions (shell minus 1px border on each side and top chrome).
        # Compare body dimensions against shell breakpoints minus chrome so 1280x720 DIP (1920x1080 @ 150%,
        # 1200x704 shell -> 1198x616 body) stays in 2-column desktop mode while 1093x614 & 960x540 compact.
        body_compact_w = LAYOUT_TOKENS.COMPACT_WIDTH_THRESHOLD - 2
        body_compact_h = LAYOUT_TOKENS.COMPACT_HEIGHT_THRESHOLD - (
            LAYOUT_TOKENS.TITLEBAR_HEIGHT + LAYOUT_TOKENS.NAV_RAIL_HEIGHT + 2
        )
        compact = w < body_compact_w or (h > 0 and h < body_compact_h)
        if compact:
            self._grid_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self._grid_layout.setSpacing(14)
            self.hero_logo.set_logo_height(64)
            self.left_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            self.right_col.setMinimumWidth(0)
            self.right_col.setMaximumWidth(min(454, max(300, w - 36)))
            self.right_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            self.notif_compact_panel.setMaximumWidth(16777215)
        else:
            self._grid_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self._grid_layout.setSpacing(20)
            self.hero_logo.set_logo_height(64 if w < 1100 else 82)
            self.left_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            dock_w = 410 if w < 1100 else 454
            self.right_col.setFixedWidth(dock_w)
            self.right_col.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
            self.notif_compact_panel.setMaximumWidth(560)
        self._is_compact = compact

    def apply_scrim_spec(self, spec: AdaptiveScrimSpec) -> None:
        self.notif_compact_panel.apply_scrim_spec(spec)
        self.action_dock_panel.apply_scrim_spec(spec)

    def set_reduced_motion(self, enabled: bool) -> None:
        self._reduced_motion = bool(enabled)
        self.progress_panel.set_reduced_motion(self._reduced_motion)
        for btn in (
            self.btn_install_patch,
            self.btn_launch_game,
            self.btn_verify_files,
            self.btn_restore_vanilla,
            self.btn_check_updates,
        ):
            btn.set_reduced_motion(self._reduced_motion)

    def set_notifications(self, items: list[NotificationItem]) -> None:
        for row in self._notice_rows:
            self._notif_list_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self._notice_rows.clear()

        top = list(items[:3])
        self._empty_notif_label.setVisible(len(top) == 0)
        for idx, item in enumerate(top):
            row = _OverviewNoticeRow(
                item,
                idx,
                is_last=(idx == len(top) - 1),
                asset_renderer=self._renderer,
                parent=self.notif_list_host,
            )
            row.clicked_with_id.connect(self.open_notifications_requested.emit)
            self._notif_list_layout.addWidget(row)
            self._notice_rows.append(row)

    def set_game_info(self, game_info: GameInfo, has_pending_recovery: bool = False) -> None:
        self._game_info = game_info
        self._has_pending_recovery = bool(has_pending_recovery)

        plat = (game_info.platform or "unknown").strip().lower()
        if plat == "steam":
            self.platform_tag.setText("Steam")
        elif plat == "standalone":
            self.platform_tag.setText("Yostar")
        else:
            self.platform_tag.setText("Chưa rõ")

        ver = game_info.version if game_info.version and game_info.version != "unknown" else "Chưa rõ"
        res = (
            game_info.resource_version
            if game_info.resource_version and game_info.resource_version != "unknown"
            else "—"
        )
        if game_info.installed:
            self.version_label.setText(nfc(f"{ver} · Res {res}"))
        else:
            self.version_label.setText(nfc("Chưa phát hiện game"))

        if game_info.installed:
            if game_info.receipt_stale:
                self.patch_status_inline.set_status("Cần cài lại", tone="warn")
            elif game_info.has_vietnamese:
                vv = game_info.vietnamese_version or ""
                lbl = f"Đã cài {vv}".strip() if vv.startswith("v") else f"Đã cài v{vv}".strip()
                if not vv:
                    lbl = "Đã cài Việt hoá"
                self.patch_status_inline.set_status(lbl, tone="ok")
            elif game_info.official_restore:
                self.patch_status_inline.set_status("Bản gốc EN", tone="muted")
            else:
                self.patch_status_inline.set_status("Chưa cài", tone="muted")
        else:
            self.patch_status_inline.set_status("Chưa chọn game", tone="muted")

        self.path_selector.set_path(str(game_info.game_path) if game_info.game_path else None)
        self._sync_action_states()

    def set_translation_state(self, state: dict) -> None:
        self._translation_state = dict(state or {})
        self._sync_action_states()

    def set_official_notice(self, notice: dict | None) -> None:
        self._official_notice = dict(notice) if isinstance(notice, dict) else None
        self._sync_action_states()

    def set_operation_active(
        self,
        active: bool,
        *,
        cancellable: bool = True,
        initial_message: str = "",
    ) -> None:
        self._op_active = bool(active)
        self.progress_panel.set_active(
            self._op_active,
            cancellable=cancellable,
            initial_message=initial_message,
        )
        self._sync_action_states()

    def set_operation_event(self, event: OperationEvent) -> None:
        self.progress_panel.set_event(event)
        is_active_phase = event.phase not in (
            OperationPhase.IDLE,
            OperationPhase.DONE,
            OperationPhase.ERROR,
        )
        if is_active_phase:
            if not self._op_active:
                self._op_active = True
                self._sync_action_states()
        else:
            if event.phase == OperationPhase.IDLE:
                self.progress_panel.set_active(False)
            if self._op_active:
                self._op_active = False
                self._sync_action_states()

    def _sync_action_states(self) -> None:
        g = self._game_info
        ts = self._translation_state
        blocker_code = str(ts.get("blocker_code") or "").strip()
        can_install = ts.get("can_install", True) if ts else True

        if not g.installed or not g.has_vietnamese:
            self.btn_install_patch.setText("Cài Việt hoá")
        elif ts.get("available") or g.receipt_stale:
            self.btn_install_patch.setText("Cập nhật Việt hoá")
        else:
            self.btn_install_patch.setText("Cài lại Việt hoá")

        busy = self._op_active
        self.path_selector.set_controls_enabled(not busy)
        self.btn_install_patch.setEnabled((not busy) and bool(can_install))
        self.btn_launch_game.setEnabled((not busy) and bool(g.installed))
        self.btn_verify_files.setEnabled((not busy) and bool(g.installed))
        self.btn_restore_vanilla.setEnabled((not busy) and bool(g.installed))
        self.btn_check_updates.setEnabled(not busy)

        # Conditional blocker / official notice row
        if blocker_code:
            self._why_mode = "blocker"
            self._why_code = blocker_code
            if blocker_code == "E-PKG-MISMATCH":
                mk = str(ts.get("mismatch_kind") or "")
                lg = str(ts.get("local_game") or "")
                sg = str(ts.get("supported_game") or "")
                if mk == "game_older" and lg and sg:
                    why_txt = f"Game đang ở v{lg} (cần v{sg}) — Mở game cập nhật trước rồi cài"
                elif mk == "game_newer" and lg and sg:
                    why_txt = f"Game v{lg} mới hơn bản dịch v{sg} — Xem hướng dẫn"
                else:
                    why_txt = f"Phiên bản game chưa khớp gói dịch [{blocker_code}] — Xem cách sửa"
            else:
                why_txt = f"Không thể cài [{blocker_code}] — Xem cách sửa"
            self.why_disabled_btn.setText(nfc(why_txt))
            self.why_disabled_btn.setVisible(True)
        elif self._official_notice and (
            self._official_notice.get("needs_restore") or self._official_notice.get("update_available")
        ):
            self._why_mode = "official"
            self._why_code = ""
            self.why_disabled_btn.setText(
                nfc("Game có bản cập nhật mới — Khôi phục bản gốc trước khi chạy")
            )
            self.why_disabled_btn.setVisible(True)
        else:
            self._why_mode = ""
            self._why_code = ""
            self.why_disabled_btn.setVisible(False)
