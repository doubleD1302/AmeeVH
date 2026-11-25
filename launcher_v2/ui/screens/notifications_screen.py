# -*- coding: utf-8 -*-
"""
NotificationsScreen — Light Porcelain 2-column Master-Detail notification center.

Dynamically renders list[NotificationItem] & status (29 items NOTIF-037..NOTIF-001
from resources/notifications.json by default until online sync completes),
with category underline tabs, live search, notification-8be8201c.png watermark,
native copy via core.error_report.copy_text_native, and universal Close (×) + Esc.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QEvent, QModelIndex, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDesktopServices,
    QFontMetrics,
    QGuiApplication,
    QPainter,
    QPen,
    QStandardItem,
    QStandardItemModel,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QUrl

from ...core.error_report import copy_text_native
from ...core.network import NetworkService
from ...core.types import NotificationItem
from ..theme.tokens import LAYOUT_TOKENS, PORCELAIN_TOKENS
from ..theme.typography import (
    FS_BODY,
    FS_BODY_SM,
    FS_CAPTION,
    FS_DETAIL_TITLE,
    FS_META,
    FS_SUBTITLE,
    mono_font,
    nfc,
    ui_font,
)
from ..widgets import (
    ActionButton,
    AssetRenderer,
    PorcelainWindowFrame,
    get_asset_renderer,
)

_ROLE_ITEM = Qt.ItemDataRole.UserRole + 1
_ROLE_INDEX = Qt.ItemDataRole.UserRole + 2
_ROLE_IS_NEWEST = Qt.ItemDataRole.UserRole + 3


def _category_display(category: str) -> tuple[str, str]:
    cat = (category or "").strip().lower()
    if cat in ("release", "project"):
        return "PHÁT HÀNH", PORCELAIN_TOKENS.CYAN_TEXT_DEEP
    if cat == "guide":
        return "HƯỚNG DẪN", PORCELAIN_TOKENS.NAVY_SOLID
    return "LƯU Ý", PORCELAIN_TOKENS.WARN_ICON


def _matches_category(item_cat: str, filter_key: str) -> bool:
    if filter_key == "all":
        return True
    c = (item_cat or "").strip().lower()
    if filter_key == "release":
        return c in ("release", "project")
    if filter_key == "guide":
        return c == "guide"
    if filter_key == "notice":
        return c in ("notice", "feedback")
    return True


def _source_label_for_status(status: str) -> str:
    st = (status or "").strip().lower()
    if st == "online":
        return "GitHub main"
    if st == "cached":
        return "Bản lưu ngoại tuyến"
    if st == "bundled":
        return "Thông báo đi kèm"
    return "Ngoại tuyến"


class _UnderlineTabBar(QWidget):
    """Flat #FFFFFF underline tab strip matching Preview r5 .porcelain-tabs."""

    tab_changed = Signal(str)

    def __init__(self, tabs: list[tuple[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._active_key: str = tabs[0][0] if tabs else ""

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(20)

        for key, label in tabs:
            btn = QPushButton(nfc(label), self)
            btn.setObjectName("uTabBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFlat(True)
            btn.clicked.connect(lambda _chk=False, k=key: self.select_tab(k, emit=True))
            lay.addWidget(btn)
            self._buttons[key] = btn
        lay.addStretch(1)
        self._apply_styles()

    def select_tab(self, key: str, *, emit: bool = False) -> None:
        if key not in self._buttons:
            return
        changed = key != self._active_key
        self._active_key = key
        self._apply_styles()
        if emit and changed:
            self.tab_changed.emit(key)

    def active_tab(self) -> str:
        return self._active_key

    def _apply_styles(self) -> None:
        p = PORCELAIN_TOKENS
        for key, btn in self._buttons.items():
            is_active = key == self._active_key
            btn.setFont(ui_font(FS_BODY, 700 if is_active else 500))
            border_c = p.CYAN_ACCENT if is_active else "transparent"
            color = p.NAVY_TEXT if is_active else p.SLATE_MUTED
            btn.setStyleSheet(
                f"QPushButton#uTabBtn {{ border: none; border-bottom: 2.5px solid {border_c}; "
                f"border-radius: 0px; background: transparent; color: {color}; padding: 9px 2px; }}"
                f"QPushButton#uTabBtn:hover {{ color: {p.NAVY_TEXT}; }}"
            )


class _NotificationRowDelegate(QStyledItemDelegate):
    """Flat hairline master row delegate with 3px #12B8C4 selection bar & sprites."""

    def __init__(self, asset_renderer: AssetRenderer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        item = index.data(_ROLE_ITEM)
        if not isinstance(item, NotificationItem):
            super().paint(painter, option, index)
            return

        p = PORCELAIN_TOKENS
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        row = index.row()

        if selected:
            bg = QColor(p.ICE_SELECTED)
        elif hovered:
            bg = QColor(p.ICE_HOVER)
        elif row % 2 == 1:
            bg = QColor(p.ICE_ROW_ALT)
        else:
            bg = QColor(p.WHITE)

        painter.fillRect(option.rect, bg)

        if selected:
            painter.fillRect(option.rect.left(), option.rect.top(), 3, option.rect.height(), QColor(p.CYAN_ACCENT))

        pen = QPen(QColor(p.HAIRLINE), 1.0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawLine(option.rect.left(), option.rect.bottom(), option.rect.right(), option.rect.bottom())

        content = option.rect.adjusted(15, 10, -15, -10)
        top_h = 16
        x_cursor = float(content.left())

        is_newest = bool(index.data(_ROLE_IS_NEWEST))
        row_idx = int(index.data(_ROLE_INDEX) or 0)
        dpr = max(1.0, float(option.widget.devicePixelRatioF())) if option.widget else 1.0

        if is_newest:
            pix = self._renderer.get_icon_pixmap("game/zs_common_new_1.png", (42, 15), dpr)
            if not pix.isNull():
                painter.drawPixmap(
                    QRectF(x_cursor, content.top() + 0.5, 42.0, 15.0),
                    pix,
                    QRectF(pix.rect()),
                )
                x_cursor += 48.0
        elif row_idx < 3 or item.is_unread:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(p.CYAN_ACCENT))
            painter.drawEllipse(QRectF(x_cursor, content.top() + 4.5, 7.0, 7.0))
            x_cursor += 13.0

        cat_text, cat_hex = _category_display(item.category)
        cat_font = ui_font(FS_CAPTION, 700)
        painter.setFont(cat_font)
        painter.setPen(QColor(cat_hex))
        date_font = ui_font(FS_CAPTION, 400, tabular=True)
        date_w = QFontMetrics(date_font).horizontalAdvance(item.date) + 8
        cat_rect = QRectF(x_cursor, content.top(), max(40.0, content.right() - x_cursor - date_w), top_h)
        painter.drawText(cat_rect, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), nfc(cat_text))

        painter.setFont(date_font)
        painter.setPen(QColor(p.SLATE_MUTED))
        date_rect = QRectF(content.right() - date_w, content.top(), date_w, top_h)
        painter.drawText(date_rect, int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), nfc(item.date))

        # Title: up to 2 lines
        fg = index.data(Qt.ItemDataRole.ForegroundRole)
        title_color = fg.color() if isinstance(fg, QBrush) else (fg if isinstance(fg, QColor) else QColor(p.NAVY_TEXT))
        title_font = ui_font(FS_BODY, 600)
        painter.setFont(title_font)
        painter.setPen(title_color)
        fm = QFontMetrics(title_font)
        max_title_h = fm.lineSpacing() * 2 + 2
        title_rect = QRect(content.left(), content.top() + top_h + 4, content.width(), max_title_h)
        painter.drawText(
            title_rect,
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap),
            nfc(item.title),
        )
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        item = index.data(_ROLE_ITEM)
        if not isinstance(item, NotificationItem):
            return QSize(200, 66)
        title_font = ui_font(FS_BODY, 600)
        fm = QFontMetrics(title_font)
        w = option.rect.width() if option.rect.width() > 60 else 360
        avail_w = max(80, w - 30)
        br = fm.boundingRect(
            QRect(0, 0, avail_w, fm.lineSpacing() * 2 + 4),
            int(Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap),
            nfc(item.title),
        )
        h = 20 + 16 + 4 + min(fm.lineSpacing() * 2 + 2, br.height() + 2)
        return QSize(w, max(66, h))


class _WatermarkedDetailPane(QWidget):
    """Reading pane painting notification-8be8201c.png at top-right (opacity 0.14)."""

    def __init__(self, asset_renderer: AssetRenderer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(PORCELAIN_TOKENS.WHITE))
        watermark = self._renderer.get_master_pixmap("game/notification-8be8201c.png")
        if not watermark.isNull() and watermark.width() > 0:
            w = 170.0
            h = w * (float(watermark.height()) / float(watermark.width()))
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.setOpacity(0.14)
            painter.drawPixmap(
                QRectF(max(0.0, float(self.width()) - w), 0.0, w, h),
                watermark,
                QRectF(0.0, 0.0, float(watermark.width()), float(watermark.height())),
            )
            painter.restore()
        painter.end()


class _NotifSearchBox(QFrame):
    """Search box frame with compact minimum width for narrow (< 780 DIP) layouts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._preferred_width = 240

    def set_preferred_width(self, width: int) -> None:
        w = max(160, int(width))
        if w != self._preferred_width:
            self._preferred_width = w
            self.updateGeometry()

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(160, 30)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._preferred_width, 30)


class NotificationsScreen(QWidget):
    """Porcelain 2-column Master-Detail notification center."""

    close_requested = Signal()
    open_guide_requested = Signal()
    toast_requested = Signal(str, str)

    def __init__(
        self,
        *,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer or get_asset_renderer()
        self._all_items: list[NotificationItem] = []
        self._filtered_items: list[NotificationItem] = []
        self._status: str = "bundled"
        self._category: str = "all"
        self._query: str = ""
        self._selected_id: Optional[str] = None
        self._active_item: Optional[NotificationItem] = None
        self._last_layout_width: int = LAYOUT_TOKENS.DEFAULT_WIN_W

        self.setObjectName("notificationsScreen")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
        )
        outer.setSpacing(0)

        self.frame = PorcelainWindowFrame(
            "Thông báo",
            meta="Thông báo đi kèm · 0 bài",
            icon_path="game/zs_mail_mailbox.png",
            icon_size=(22, 22),
            asset_renderer=self._renderer,
            parent=self,
        )
        self.frame.meta_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self.frame.meta_label.setMinimumWidth(0)
        self.frame._title_row.setStretchFactor(self.frame.meta_label, 100)
        self._sync_meta_max_width()
        self.frame.close_requested.connect(self.close_requested.emit)
        outer.addWidget(self.frame)

        # Header Search Box
        self.search_box = _NotifSearchBox(self.frame)
        self.search_box.setObjectName("porcelainSearchBox")
        self.search_box.setFixedHeight(30)
        self.search_box.setMinimumWidth(160)
        self.search_box.setMaximumWidth(260)
        self.search_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.search_box.setStyleSheet(
            f"QFrame#porcelainSearchBox {{ background: {PORCELAIN_TOKENS.WHITE}; "
            f"border: 1px solid {PORCELAIN_TOKENS.HAIRLINE_INPUT}; border-radius: 4px; }}"
        )
        sb_lay = QHBoxLayout(self.search_box)
        sb_lay.setContentsMargins(10, 0, 8, 0)
        sb_lay.setSpacing(7)

        self._search_icon = QLabel(self.search_box)
        self._search_icon.setFixedSize(14, 14)
        sb_lay.addWidget(self._search_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        self.search_input = QLineEdit(self.search_box)
        self.search_input.setPlaceholderText(nfc("Tìm tiêu đề, phiên bản..."))
        self.search_input.setFont(ui_font(FS_BODY, 400))
        self.search_input.setStyleSheet(
            f"QLineEdit {{ border: none; background: transparent; color: {PORCELAIN_TOKENS.NAVY_TEXT}; }}"
        )
        self.search_input.textChanged.connect(self._on_search_changed)
        sb_lay.addWidget(self.search_input, 1)

        self.search_clear_btn = QPushButton(nfc("Xóa"), self.search_box)
        self.search_clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_clear_btn.setFont(ui_font(FS_CAPTION, 600))
        self.search_clear_btn.setStyleSheet(
            f"QPushButton {{ border: none; border-radius: 3px; background: {PORCELAIN_TOKENS.ICE_ZEBRA}; "
            f"color: {PORCELAIN_TOKENS.NAVY_TEXT}; padding: 2px 7px; }}"
        )
        self.search_clear_btn.setVisible(False)
        self.search_clear_btn.clicked.connect(lambda: self.search_input.clear())
        sb_lay.addWidget(self.search_clear_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self.frame.add_header_control(self.search_box)

        # Category Filter Tabs
        self.tab_bar = _UnderlineTabBar(
            [
                ("all", "Tất cả"),
                ("release", "Phát hành"),
                ("guide", "Hướng dẫn"),
                ("notice", "Lưu ý"),
            ],
            parent=self.frame,
        )
        self.tab_bar.tab_changed.connect(self._on_category_changed)
        self.frame.set_tabs_bar(self.tab_bar)

        # Master-Detail Split Body
        body = QWidget(self.frame)
        body.setStyleSheet(f"background: {PORCELAIN_TOKENS.WHITE};")
        self._split_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, body)
        self._split_layout.setContentsMargins(0, 0, 0, 0)
        self._split_layout.setSpacing(0)

        # Left Master Host (list + empty state)
        self.master_panel = QFrame(body)
        self.master_panel.setObjectName("notifMasterPanel")
        self.master_panel.setFixedWidth(390)
        self.master_panel.setStyleSheet(
            f"QFrame#notifMasterPanel {{ background: {PORCELAIN_TOKENS.WHITE}; "
            f"border: none; border-right: 1px solid {PORCELAIN_TOKENS.HAIRLINE}; }}"
        )
        master_lay = QVBoxLayout(self.master_panel)
        master_lay.setContentsMargins(0, 0, 0, 0)
        master_lay.setSpacing(0)

        self.master_stack = QStackedWidget(self.master_panel)
        self.master_list = QListView(self.master_stack)
        self.master_list.setObjectName("notifMasterList")
        self.master_list.setFrameShape(QFrame.Shape.NoFrame)
        self.master_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.master_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.master_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.master_list.setMouseTracking(True)
        self.master_list.setStyleSheet(
            f"QListView#notifMasterList {{ background: {PORCELAIN_TOKENS.WHITE}; border: none; outline: none; }}"
        )
        self._model = QStandardItemModel(self.master_list)
        self.master_list.setModel(self._model)
        self._delegate = _NotificationRowDelegate(self._renderer, self.master_list)
        self.master_list.setItemDelegate(self._delegate)
        self.master_list.selectionModel().currentChanged.connect(self._on_row_selected)
        self.master_stack.addWidget(self.master_list)

        empty_wrap = QWidget(self.master_stack)
        empty_lay = QVBoxLayout(empty_wrap)
        empty_lay.setContentsMargins(18, 18, 18, 18)
        self.empty_label = QLabel(nfc("Không có thông báo nào khớp từ khóa."), empty_wrap)
        self.empty_label.setFont(ui_font(FS_BODY, 500))
        self.empty_label.setStyleSheet(f"color: {PORCELAIN_TOKENS.SLATE_MUTED};")
        self.empty_label.setWordWrap(True)
        empty_lay.addWidget(self.empty_label)
        empty_lay.addStretch(1)
        self.master_stack.addWidget(empty_wrap)
        master_lay.addWidget(self.master_stack)
        self._split_layout.addWidget(self.master_panel, 0)

        # Right Detail Pane inside vertical scroll area
        self.detail_scroll = QScrollArea(body)
        self.detail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.detail_scroll.setStyleSheet(f"background: {PORCELAIN_TOKENS.WHITE}; border: none;")

        self.detail_pane = _WatermarkedDetailPane(self._renderer, self.detail_scroll)
        detail_lay = QVBoxLayout(self.detail_pane)
        detail_lay.setContentsMargins(26, 22, 26, 22)
        detail_lay.setSpacing(14)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(8)

        self.detail_cat_label = QLabel("", self.detail_pane)
        self.detail_cat_label.setFont(ui_font(FS_CAPTION, 700))
        self.detail_cat_label.setStyleSheet("background: transparent;")
        meta_row.addWidget(self.detail_cat_label)

        self.detail_id_label = QLabel("", self.detail_pane)
        self.detail_id_label.setFont(mono_font(FS_META, 500))
        self.detail_id_label.setStyleSheet(f"color: {PORCELAIN_TOKENS.SLATE_MUTED}; background: transparent;")
        meta_row.addWidget(self.detail_id_label)

        self.detail_date_label = QLabel("", self.detail_pane)
        self.detail_date_label.setFont(ui_font(FS_META, 500, tabular=True))
        self.detail_date_label.setStyleSheet(f"color: {PORCELAIN_TOKENS.SLATE_MUTED}; background: transparent;")
        meta_row.addWidget(self.detail_date_label)
        meta_row.addStretch(1)
        detail_lay.addLayout(meta_row)

        self.detail_title_label = QLabel("", self.detail_pane)
        self.detail_title_label.setFont(ui_font(FS_DETAIL_TITLE, 700))
        self.detail_title_label.setWordWrap(True)
        self.detail_title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.detail_title_label.setStyleSheet(f"color: {PORCELAIN_TOKENS.NAVY_TEXT}; background: transparent;")
        detail_lay.addWidget(self.detail_title_label)

        self.detail_body_label = QLabel("", self.detail_pane)
        self.detail_body_label.setFont(ui_font(13.5, 400))
        self.detail_body_label.setWordWrap(True)
        self.detail_body_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.detail_body_label.setStyleSheet(f"color: {PORCELAIN_TOKENS.SLATE_BODY}; background: transparent;")
        detail_lay.addWidget(self.detail_body_label)

        self.detail_link_btn = QPushButton("", self.detail_pane)
        self.detail_link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.detail_link_btn.setFlat(True)
        self.detail_link_btn.setFont(ui_font(FS_BODY_SM, 600))
        self.detail_link_btn.setStyleSheet(
            f"QPushButton {{ border: none; background: transparent; color: {PORCELAIN_TOKENS.CYAN_TEXT_DEEP}; "
            f"text-align: left; padding: 2px 0; }}"
            f"QPushButton:hover {{ text-decoration: underline; }}"
        )
        self.detail_link_btn.clicked.connect(self._open_active_link)
        self.detail_link_btn.setVisible(False)
        detail_lay.addWidget(self.detail_link_btn, 0, Qt.AlignmentFlag.AlignLeft)

        detail_lay.addStretch(1)

        actions_bar = QFrame(self.detail_pane)
        actions_bar.setObjectName("notifDetailActions")
        actions_bar.setStyleSheet(
            f"QFrame#notifDetailActions {{ background: transparent; border: none; "
            f"border-top: 1px solid {PORCELAIN_TOKENS.HAIRLINE}; padding-top: 12px; }}"
        )
        act_lay = QHBoxLayout(actions_bar)
        act_lay.setContentsMargins(0, 12, 0, 0)
        act_lay.setSpacing(10)

        self.btn_open_guide = ActionButton(
            "Xem hướng dẫn",
            variant="light_cyan",
            height=32,
            asset_renderer=self._renderer,
            parent=actions_bar,
        )
        self.btn_open_guide.clicked.connect(self.open_guide_requested.emit)
        act_lay.addWidget(self.btn_open_guide)

        self.btn_copy_notice = ActionButton(
            "Sao chép",
            variant="light_secondary",
            icon_path="game/btn_icon_copy.png",
            icon_size=(14, 14),
            icon_tint=PORCELAIN_TOKENS.NAVY_TEXT,
            height=32,
            asset_renderer=self._renderer,
            parent=actions_bar,
        )
        self.btn_copy_notice.clicked.connect(self._copy_active_notice)
        act_lay.addWidget(self.btn_copy_notice)
        act_lay.addStretch(1)
        detail_lay.addWidget(actions_bar)

        self.detail_scroll.setWidget(self.detail_pane)
        self._split_layout.addWidget(self.detail_scroll, 1)

        self.frame.set_body(body)
        self.refresh_dpr()
        self._load_bundled_fallback()

    def _load_bundled_fallback(self) -> None:
        notif_path = Path(self._renderer.resource_dir) / "notifications.json"
        if not notif_path.is_file():
            return
        try:
            raw = json.loads(notif_path.read_text(encoding="utf-8"))
            svc = NetworkService()
            items = svc._notifications(raw)
            self.set_notifications(items, status="bundled")
        except Exception:  # noqa: BLE001
            pass

    def _sync_meta_max_width(self) -> None:
        txt = self.frame.meta_label.text()
        max_w = max(0, self.frame.meta_label.fontMetrics().horizontalAdvance(txt) + 8)
        self.frame.meta_label.setMaximumWidth(max_w)

    def refresh_dpr(self) -> None:
        dpr = max(1.0, float(self.devicePixelRatioF()))
        pix = self._renderer.get_icon_pixmap(
            "game/zs_common_search.png", (14, 14), dpr, tint=PORCELAIN_TOKENS.NAVY_TEXT
        )
        if not pix.isNull():
            self._search_icon.setPixmap(pix)
        self.frame.refresh_dpr()
        self._sync_meta_max_width()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()
        elif event.type() == QEvent.Type.FontChange:
            self._sync_meta_max_width()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.compact_layout(self.width(), self.height())

    def compact_layout(self, width: int, height: int | None = None) -> None:
        w = int(width)
        self._last_layout_width = w
        self._sync_meta_max_width()
        self.frame.meta_label.setVisible(w >= 820 and bool(self.frame.meta_label.text()))
        if w < 780:
            self._split_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self.master_panel.setFixedWidth(16777215)
            self.master_panel.setMinimumWidth(0)
            self.master_panel.setFixedHeight(210)
            self.search_box.set_preferred_width(160)
        else:
            self._split_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self.master_panel.setMinimumHeight(0)
            self.master_panel.setMaximumHeight(16777215)
            self.master_panel.setFixedWidth(330 if w < 1100 else 390)
            self.search_box.set_preferred_width(200 if w < 1000 else 240)

    def set_notifications(self, items: list[NotificationItem], status: str = "bundled") -> None:
        self._all_items = list(items)
        self._status = status or "bundled"
        source = _source_label_for_status(self._status)
        self.frame.set_meta(f"{source} · {len(self._all_items)} bài")
        self._sync_meta_max_width()
        self.frame.meta_label.setVisible(
            self._last_layout_width >= 820 and bool(self.frame.meta_label.text())
        )
        self._rebuild_list()

    def select_notification(self, notif_id: str | None) -> None:
        if notif_id:
            self._selected_id = notif_id
            # If current filter hides it, switch back to "all"
            if not any(it.id == notif_id for it in self._filtered_items):
                self._category = "all"
                self.tab_bar.select_tab("all", emit=False)
                self._query = ""
                self.search_input.blockSignals(True)
                self.search_input.clear()
                self.search_input.blockSignals(False)
                self.search_clear_btn.setVisible(False)
                self._rebuild_list()
                return
        self._sync_selection()

    def _on_search_changed(self, text: str) -> None:
        self._query = nfc(text).strip().lower()
        self.search_clear_btn.setVisible(bool(self._query))
        self._rebuild_list()

    def _on_category_changed(self, key: str) -> None:
        self._category = key
        self._rebuild_list()

    def _rebuild_list(self) -> None:
        q = self._query
        filtered = [
            it
            for it in self._all_items
            if _matches_category(it.category, self._category)
            and (
                not q
                or q in nfc(it.title).lower()
                or q in nfc(it.summary).lower()
                or q in nfc(it.content).lower()
                or q in nfc(it.id).lower()
                or q in nfc(it.badge).lower()
            )
        ]
        self._filtered_items = filtered

        if filtered and not any(it.id == self._selected_id for it in filtered):
            self._selected_id = filtered[0].id

        newest_id = self._all_items[0].id if self._all_items else ""

        self._model.clear()
        for idx, item in enumerate(filtered):
            std = QStandardItem(nfc(item.title))
            std.setEditable(False)
            std.setForeground(QBrush(QColor(PORCELAIN_TOKENS.NAVY_TEXT)))
            std.setData(item, _ROLE_ITEM)
            std.setData(idx, _ROLE_INDEX)
            std.setData(item.id == newest_id, _ROLE_IS_NEWEST)
            self._model.appendRow(std)

        self.master_stack.setCurrentIndex(0 if filtered else 1)
        self._sync_selection()

    def _sync_selection(self) -> None:
        target_row = 0
        if self._selected_id:
            for idx, it in enumerate(self._filtered_items):
                if it.id == self._selected_id:
                    target_row = idx
                    break
        if self._filtered_items:
            q_idx = self._model.index(target_row, 0)
            self.master_list.setCurrentIndex(q_idx)
            self._render_detail(self._filtered_items[target_row])
        else:
            self._render_detail(None)

    def _on_row_selected(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            return
        item = current.data(_ROLE_ITEM)
        if isinstance(item, NotificationItem):
            self._selected_id = item.id
            self._render_detail(item)

    def _render_detail(self, item: NotificationItem | None) -> None:
        self._active_item = item
        if item is None:
            self.detail_cat_label.setText("")
            self.detail_id_label.setText("")
            self.detail_date_label.setText("")
            empty_title = (
                "Không có thông báo nào khớp bộ lọc."
                if self._all_items
                else "Chưa có thông báo"
            )
            self.detail_title_label.setText(nfc(empty_title))
            self.detail_body_label.setText("")
            self.detail_link_btn.setVisible(False)
            self.btn_copy_notice.setEnabled(False)
            return

        cat_text, cat_hex = _category_display(item.category)
        self.detail_cat_label.setText(nfc(cat_text))
        self.detail_cat_label.setStyleSheet(f"color: {cat_hex}; background: transparent;")
        self.detail_id_label.setText(nfc(item.id))
        self.detail_date_label.setText(nfc(f"· {item.date}") if item.date else "")
        self.detail_title_label.setText(nfc(item.title))
        self.detail_body_label.setText(nfc(item.content))

        link = (item.link_url or "").strip()
        if link.lower().startswith(("http://", "https://")):
            self.detail_link_btn.setText(nfc(f"Mở liên kết: {link}"))
            self.detail_link_btn.setVisible(True)
        else:
            self.detail_link_btn.setVisible(False)
        self.btn_copy_notice.setEnabled(True)

    def _open_active_link(self) -> None:
        if self._active_item and self._active_item.link_url:
            url = self._active_item.link_url.strip()
            if url.lower().startswith(("http://", "https://")):
                QDesktopServices.openUrl(QUrl(url))

    def _copy_active_notice(self) -> None:
        if self._active_item is None:
            return
        it = self._active_item
        payload = f"{it.title}\n{it.date} ({it.id})\n\n{it.content}"
        ok = copy_text_native(payload)
        cb = QGuiApplication.clipboard()
        if cb is not None:
            cb.setText(payload)
            ok = True
        if ok:
            self.toast_requested.emit(nfc(f"Đã sao chép thông báo {it.id}"), "success")
        else:
            self.toast_requested.emit(nfc("Không thể truy cập clipboard."), "warning")
