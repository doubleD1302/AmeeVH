# -*- coding: utf-8 -*-
"""
GuideScreen — Light Porcelain searchable Guide & FAQ screen.

Dynamically loads PathManager.resource_dir / "support" / "help_content.json"
(4 sections & 15 FAQs in v2.0.0 — zero hardcoded counts), renders 3-step horizontal
stepper, topic underline tabs, Hairline step tables, and unified FaqAccordionRow list.
Collapses 2-column split cleanly into 1 column below 900 DIP.
"""
from __future__ import annotations

import html
import json
import weakref
from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.config import PathManager
from ..theme.tokens import LAYOUT_TOKENS, PORCELAIN_TOKENS
from ..theme.typography import (
    FS_BODY,
    FS_BODY_SM,
    FS_CAPTION,
    FS_META,
    nfc,
    ui_font,
)
from ..widgets import (
    AssetRenderer,
    PorcelainSectionBar,
    PorcelainWindowFrame,
    get_asset_renderer,
)

try:
    from shiboken6 import isValid as _qt_is_valid
except ImportError:  # pragma: no cover
    def _qt_is_valid(_obj: object) -> bool:
        return True

_TOPIC_SHORT_LABELS: dict[str, str] = {
    "start": "Bắt đầu",
    "install": "Cài đặt",
    "update": "Cập nhật",
    "restore": "Khôi phục",
}


class _GuideTabBar(QWidget):
    """Underline topic bar matching Preview r5 #guide-topic-bar."""

    tab_changed = Signal(str)

    def __init__(self, tabs: list[tuple[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._active_key: str = tabs[0][0] if tabs else "all"

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(20)

        for key, label in tabs:
            btn = QPushButton(nfc(label), self)
            btn.setObjectName("guideUTab")
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

    def _apply_styles(self) -> None:
        p = PORCELAIN_TOKENS
        for key, btn in self._buttons.items():
            active = key == self._active_key
            btn.setFont(ui_font(FS_BODY, 700 if active else 500))
            border_c = p.CYAN_ACCENT if active else "transparent"
            color = p.NAVY_TEXT if active else p.SLATE_MUTED
            btn.setStyleSheet(
                f"QPushButton#guideUTab {{ border: none; border-bottom: 2.5px solid {border_c}; "
                f"border-radius: 0px; background: transparent; color: {color}; padding: 9px 2px; }}"
                f"QPushButton#guideUTab:hover {{ color: {p.NAVY_TEXT}; }}"
            )


class _GuideStepper(QFrame):
    """3-step horizontal onboarding strip (#EEF4FA, bottom 1px #D5E0EE)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("guideStepper")
        self.setStyleSheet(
            f"QFrame#guideStepper {{ background: {PORCELAIN_TOKENS.ICE_ZEBRA}; "
            f"border: none; border-bottom: 1px solid {PORCELAIN_TOKENS.HAIRLINE}; }}"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 9, 20, 9)
        lay.setSpacing(10)

        steps = [
            ("1", "Chọn thư mục", True),
            ("2", "Cài bản dịch", True),
            ("3", "Kiểm tra & Chơi", False),
        ]
        for idx, (num, text, done) in enumerate(steps):
            if idx > 0:
                line = QFrame(self)
                line.setFixedHeight(1)
                line.setStyleSheet(f"background: {PORCELAIN_TOKENS.HAIRLINE_INPUT}; border: none;")
                line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                lay.addWidget(line, 1)

            badge = QLabel(num, self)
            badge.setFixedSize(21, 21)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFont(ui_font(FS_CAPTION, 700, tabular=True))
            if done:
                badge.setStyleSheet(
                    f"background: {PORCELAIN_TOKENS.CYAN_ACCENT}; color: #082032; border-radius: 10px;"
                )
            else:
                badge.setStyleSheet(
                    f"background: {PORCELAIN_TOKENS.NAVY_SOLID}; color: #FFFFFF; border-radius: 10px;"
                )
            lay.addWidget(badge, 0)

            lbl = QLabel(nfc(text), self)
            lbl.setFont(ui_font(FS_BODY, 600))
            lbl.setStyleSheet(f"color: {PORCELAIN_TOKENS.NAVY_TEXT}; background: transparent;")
            lay.addWidget(lbl, 0)


class _GuideSearchBox(QFrame):
    """Search box frame with compact minimum width so narrow windows stay <= 760 DIP."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._preferred_width = 360

    def set_preferred_width(self, width: int) -> None:
        w = max(160, int(width))
        if w != self._preferred_width:
            self._preferred_width = w
            self.updateGeometry()

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(160, 30)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._preferred_width, 30)


class FaqAccordionRow(QFrame):
    """Collapsible hairline FAQ row inside unified #FFFFFF faq_table container."""

    expanded_changed = Signal(bool)

    def __init__(
        self,
        question: str,
        answer: str,
        *,
        expanded: bool = False,
        is_last: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._expanded = bool(expanded)
        self._is_last = bool(is_last)

        self.setObjectName("faqAccordionRow")
        bottom_border = "none" if self._is_last else f"1px solid {PORCELAIN_TOKENS.HAIRLINE}"
        self.setStyleSheet(
            f"QFrame#faqAccordionRow {{ background: {PORCELAIN_TOKENS.WHITE}; "
            f"border: none; border-bottom: {bottom_border}; }}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.header_btn = QFrame(self)
        self.header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn.mousePressEvent = lambda _e: self.toggle()  # type: ignore[method-assign]
        h_lay = QHBoxLayout(self.header_btn)
        h_lay.setContentsMargins(13, 9, 13, 9)
        h_lay.setSpacing(10)

        self.question_label = QLabel(nfc(question), self.header_btn)
        self.question_label.setFont(ui_font(FS_BODY, 600))
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet(f"color: {PORCELAIN_TOKENS.NAVY_TEXT}; background: transparent; border: none;")
        self.question_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        h_lay.addWidget(self.question_label, 1)

        self.toggle_label = QLabel("+" if not self._expanded else "−", self.header_btn)
        self.toggle_label.setFont(ui_font(15.0, 700))
        self.toggle_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        h_lay.addWidget(self.toggle_label, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self.header_btn)

        self.answer_label = QLabel(nfc(answer), self)
        self.answer_label.setFont(ui_font(FS_BODY_SM, 400))
        self.answer_label.setWordWrap(True)
        self.answer_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.answer_label.setStyleSheet(
            f"background: {PORCELAIN_TOKENS.WHITE}; color: {PORCELAIN_TOKENS.SLATE_BODY}; "
            f"padding: 9px 13px; border: none;"
        )
        lay.addWidget(self.answer_label)

        self.set_expanded(self._expanded)

    def is_expanded(self) -> bool:
        return self._expanded

    def toggle(self) -> None:
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = bool(expanded)
        self.answer_label.setVisible(self._expanded)
        self.toggle_label.setText("−" if self._expanded else "+")
        p = PORCELAIN_TOKENS
        if self._expanded:
            self.header_btn.setStyleSheet(
                f"background: {p.ICE_ZEBRA}; border: none; border-bottom: 1px solid {p.HAIRLINE_CELL};"
            )
            self.toggle_label.setStyleSheet(f"color: {p.CYAN_ACCENT}; background: transparent; border: none;")
        else:
            self.header_btn.setStyleSheet(f"background: {p.WHITE}; border: none;")
            self.toggle_label.setStyleSheet(f"color: {p.NAVY_SOLID}; background: transparent; border: none;")
        if self.layout() is not None:
            self.layout().invalidate()
        self.updateGeometry()
        self.expanded_changed.emit(self._expanded)


class GuideScreen(QWidget):
    """Porcelain Guide & FAQ screen dynamically backed by support/help_content.json."""

    close_requested = Signal()

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
        self._sections: list[dict[str, Any]] = []
        self._faqs: list[dict[str, Any]] = []
        self._topic: str = "all"
        self._query: str = ""
        self._faq_rows: list[FaqAccordionRow] = []
        self._last_layout_width: int = LAYOUT_TOKENS.DEFAULT_WIN_W
        self._is_collapsed: bool = False
        self._collapsed_sync_queued: bool = False

        self._load_help_content()

        self.setObjectName("guideScreen")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
        )
        outer.setSpacing(0)

        self.frame = PorcelainWindowFrame(
            "Hướng dẫn sử dụng",
            meta=f"{len(self._sections)} mục · {len(self._faqs)} câu hỏi thường gặp",
            icon_path="game/icon_dict_dictionary.png",
            icon_size=(26, 22),
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
        self.search_box = _GuideSearchBox(self.frame)
        self.search_box.setObjectName("guideSearchBox")
        self.search_box.setFixedHeight(30)
        self.search_box.setMinimumWidth(160)
        self.search_box.setMaximumWidth(380)
        self.search_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.search_box.setStyleSheet(
            f"QFrame#guideSearchBox {{ background: {PORCELAIN_TOKENS.WHITE}; "
            f"border: 1px solid {PORCELAIN_TOKENS.HAIRLINE_INPUT}; border-radius: 4px; }}"
        )
        sb_lay = QHBoxLayout(self.search_box)
        sb_lay.setContentsMargins(10, 0, 8, 0)
        sb_lay.setSpacing(7)

        self._search_icon = QLabel(self.search_box)
        self._search_icon.setFixedSize(14, 14)
        sb_lay.addWidget(self._search_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        self.search_input = QLineEdit(self.search_box)
        self.search_input.setPlaceholderText(nfc("Tìm hướng dẫn (Steam, khôi phục gốc, lỗi mạng...)"))
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

        # Topic Tabs (dynamically derived from loaded sections & FAQ count)
        tabs: list[tuple[str, str]] = [("all", "Tất cả")]
        for idx, sec in enumerate(self._sections):
            sec_id = str(sec.get("id") or "")
            tab_label = _TOPIC_SHORT_LABELS.get(sec_id, str(sec.get("title") or f"Mục {idx + 1}"))
            tabs.append((str(idx), tab_label))
        tabs.append(("faq", f"FAQ ({len(self._faqs)})"))

        self.tab_bar = _GuideTabBar(tabs, parent=self.frame)
        self.tab_bar.tab_changed.connect(self._on_topic_changed)
        self.frame.set_tabs_bar(self.tab_bar)

        # Body: 3-step stepper + responsive 2-col split
        body_root = QWidget(self.frame)
        body_root.setStyleSheet(f"background: {PORCELAIN_TOKENS.WHITE};")
        body_lay = QVBoxLayout(body_root)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        self.stepper = _GuideStepper(body_root)
        body_lay.addWidget(self.stepper)

        self.outer_scroll = QScrollArea(body_root)
        self.outer_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.outer_scroll.setWidgetResizable(True)
        self.outer_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.outer_scroll.setStyleSheet(f"background: {PORCELAIN_TOKENS.WHITE}; border: none;")
        body_lay.addWidget(self.outer_scroll, 1)

        split_host = QWidget(self.outer_scroll)
        split_host.setStyleSheet(f"background: {PORCELAIN_TOKENS.WHITE};")
        self._split_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, split_host)
        self._split_layout.setContentsMargins(0, 0, 0, 0)
        self._split_layout.setSpacing(0)

        # Left Column: Steps
        self.left_col = QFrame(split_host)
        self.left_col.setObjectName("guideLeftCol")
        self.left_col.setStyleSheet(
            f"QFrame#guideLeftCol {{ background: {PORCELAIN_TOKENS.WHITE}; "
            f"border: none; border-right: 1px solid {PORCELAIN_TOKENS.HAIRLINE}; }}"
        )
        left_col_lay = QVBoxLayout(self.left_col)
        left_col_lay.setContentsMargins(0, 0, 0, 0)
        left_col_lay.setSpacing(0)

        left_col_lay.addWidget(PorcelainSectionBar("Các bước thực hiện", self.left_col))

        self.left_scroll = QScrollArea(self.left_col)
        self.left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.left_scroll.setStyleSheet(f"background: {PORCELAIN_TOKENS.WHITE}; border: none;")

        self._sections_container = QWidget(self.left_scroll)
        self._sections_container.setStyleSheet(f"background: {PORCELAIN_TOKENS.WHITE};")
        self._sections_layout = QVBoxLayout(self._sections_container)
        self._sections_layout.setContentsMargins(0, 0, 0, 0)
        self._sections_layout.setSpacing(0)
        self.left_scroll.setWidget(self._sections_container)
        left_col_lay.addWidget(self.left_scroll, 1)
        self._split_layout.addWidget(self.left_col, 105)

        # Right Column: FAQ Accordion
        self.right_col = QFrame(split_host)
        self.right_col.setObjectName("guideRightCol")
        self.right_col.setStyleSheet(f"QFrame#guideRightCol {{ background: {PORCELAIN_TOKENS.PORCELAIN_BG}; border: none; }}")
        right_col_lay = QVBoxLayout(self.right_col)
        right_col_lay.setContentsMargins(0, 0, 0, 0)
        right_col_lay.setSpacing(0)

        right_col_lay.addWidget(PorcelainSectionBar("Câu hỏi thường gặp", self.right_col))

        self.right_scroll = QScrollArea(self.right_col)
        self.right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.right_scroll.setStyleSheet(f"background: {PORCELAIN_TOKENS.PORCELAIN_BG}; border: none;")

        faq_pad = QWidget(self.right_scroll)
        self._faq_pad = faq_pad
        faq_pad.setStyleSheet(f"background: {PORCELAIN_TOKENS.PORCELAIN_BG};")
        faq_pad_lay = QVBoxLayout(faq_pad)
        faq_pad_lay.setContentsMargins(14, 12, 14, 12)
        faq_pad_lay.setSpacing(0)

        self.faq_table = QFrame(faq_pad)
        self.faq_table.setObjectName("faqTableContainer")
        self.faq_table.setStyleSheet(
            f"QFrame#faqTableContainer {{ background: {PORCELAIN_TOKENS.WHITE}; "
            f"border: 1px solid {PORCELAIN_TOKENS.HAIRLINE}; border-radius: 4px; }}"
        )
        self._faq_layout = QVBoxLayout(self.faq_table)
        self._faq_layout.setContentsMargins(1, 1, 1, 1)
        self._faq_layout.setSpacing(0)
        faq_pad_lay.addWidget(self.faq_table)
        faq_pad_lay.addStretch(1)

        self.right_scroll.setWidget(faq_pad)
        right_col_lay.addWidget(self.right_scroll, 1)
        self._split_layout.addWidget(self.right_col, 95)

        self.outer_scroll.setWidget(split_host)
        self.frame.set_body(body_root)

        self.refresh_dpr()
        self._render_content()

    def _load_help_content(self) -> None:
        base = self._pm.resource_dir if self._pm is not None else self._renderer.resource_dir
        path = Path(base) / "support" / "help_content.json"
        if not path.is_file():
            self._sections = []
            self._faqs = []
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                self._sections = []
                self._faqs = []
                return
            raw_sec = data.get("sections")
            raw_faq = data.get("faq")
            self._sections = (
                [s for s in raw_sec if isinstance(s, dict)]
                if isinstance(raw_sec, list)
                else []
            )
            self._faqs = (
                [f for f in raw_faq if isinstance(f, dict)]
                if isinstance(raw_faq, list)
                else []
            )
        except (OSError, ValueError, TypeError):
            self._sections = []
            self._faqs = []

    @property
    def sections_count(self) -> int:
        return len(self._sections)

    @property
    def faq_count(self) -> int:
        return len(self._faqs)

    @property
    def faq_rows(self) -> list[FaqAccordionRow]:
        return list(self._faq_rows)

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

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if self._is_collapsed:
            self._sync_collapsed_scroll_heights()
            self._schedule_collapsed_sync()

    def _schedule_collapsed_sync(self) -> None:
        if not self._is_collapsed or self._collapsed_sync_queued:
            return
        self._collapsed_sync_queued = True
        self_ref = weakref.ref(self)

        def _tick() -> None:
            w = self_ref()
            if w is not None and _qt_is_valid(w):
                try:
                    w._run_scheduled_collapsed_sync()
                except RuntimeError:
                    pass

        QTimer.singleShot(0, _tick)

    def _run_scheduled_collapsed_sync(self) -> None:
        self._collapsed_sync_queued = False
        if self._is_collapsed:
            self._sync_collapsed_scroll_heights()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.compact_layout(self.width(), self.height())

    def compact_layout(self, width: int, height: int | None = None) -> None:
        w = int(width)
        self._last_layout_width = w
        collapse = w < LAYOUT_TOKENS.TWO_COL_COLLAPSE_THRESHOLD
        self._is_collapsed = collapse
        self._sync_meta_max_width()
        self.frame.meta_label.setVisible(w >= 860 and bool(self.frame.meta_label.text()))
        if w < 860:
            self.search_box.set_preferred_width(180)
        elif w < 1060:
            self.search_box.set_preferred_width(280)
        else:
            self.search_box.set_preferred_width(380)

        if collapse:
            self._split_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self.left_col.setStyleSheet(
                f"QFrame#guideLeftCol {{ background: {PORCELAIN_TOKENS.WHITE}; "
                f"border: none; border-bottom: 1px solid {PORCELAIN_TOKENS.HAIRLINE}; }}"
            )
            self.left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.left_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.right_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self._sync_collapsed_scroll_heights()
        else:
            self._split_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self.left_col.setStyleSheet(
                f"QFrame#guideLeftCol {{ background: {PORCELAIN_TOKENS.WHITE}; "
                f"border: none; border-right: 1px solid {PORCELAIN_TOKENS.HAIRLINE}; }}"
            )
            self.left_scroll.setMinimumHeight(0)
            self.left_scroll.setMaximumHeight(16777215)
            self.right_scroll.setMinimumHeight(0)
            self.right_scroll.setMaximumHeight(16777215)
            self.left_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.right_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def _sync_collapsed_scroll_heights(self) -> None:
        if not self._is_collapsed:
            return
        avail_w = self.outer_scroll.viewport().width()
        if avail_w <= 100:
            avail_w = max(240, self._last_layout_width - 2 * LAYOUT_TOKENS.VIEWPORT_PAD_X - 4)

        for row in self._faq_rows:
            if row.layout() is not None:
                row.layout().invalidate()
            row.updateGeometry()
        if self.faq_table.layout() is not None:
            self.faq_table.layout().invalidate()
            self.faq_table.updateGeometry()
            self.faq_table.layout().activate()
        else:
            self.faq_table.updateGeometry()

        for i in range(self._sections_layout.count()):
            w = self._sections_layout.itemAt(i).widget()
            if w is not None:
                if w.layout() is not None:
                    w.layout().invalidate()
                w.updateGeometry()

        for scroll, container in (
            (self.left_scroll, self._sections_container),
            (self.right_scroll, self._faq_pad),
        ):
            lay = container.layout()
            if lay is not None:
                lay.invalidate()
                container.updateGeometry()
                lay.activate()
                h_fw = lay.heightForWidth(avail_w) if lay.hasHeightForWidth() else 0
                needed_h = max(h_fw, container.sizeHint().height(), 60)
            else:
                needed_h = max(container.sizeHint().height(), 60)
            scroll.setFixedHeight(needed_h)
            scroll.updateGeometry()

        for col in (self.left_col, self.right_col):
            if col.layout() is not None:
                col.layout().invalidate()
                col.updateGeometry()
                col.layout().activate()

        host = self.outer_scroll.widget()
        if host is not None:
            host_lay = host.layout()
            if host_lay is not None:
                host_lay.invalidate()
                host.updateGeometry()
                host_lay.activate()
                host_h = host_lay.heightForWidth(avail_w) if host_lay.hasHeightForWidth() else 0
                host.resize(avail_w, max(host_h, host.sizeHint().height()))
            else:
                host.updateGeometry()
        self.outer_scroll.updateGeometry()

    def _on_search_changed(self, text: str) -> None:
        self._query = nfc(text).strip().lower()
        self.search_clear_btn.setVisible(bool(self._query))
        self._render_content()

    def _on_topic_changed(self, topic: str) -> None:
        self._topic = topic
        self._render_content()

    def _clear_layout(self, lay: QVBoxLayout) -> None:
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _render_content(self) -> None:
        q = self._query
        self._clear_layout(self._sections_layout)
        self._clear_layout(self._faq_layout)
        self._faq_rows.clear()

        visible_sections = 0
        if self._topic != "faq":
            for idx, sec in enumerate(self._sections):
                if self._topic != "all" and str(idx) != self._topic:
                    continue
                sec_title = nfc(str(sec.get("title") or ""))
                sec_sub = nfc(str(sec.get("subtitle") or ""))
                raw_kw = sec.get("keywords")
                if isinstance(raw_kw, list):
                    sec_kw = nfc(" ".join(str(k) for k in raw_kw if k is not None))
                else:
                    sec_kw = nfc(str(raw_kw or ""))
                raw_steps = sec.get("steps")
                steps = (
                    [st for st in raw_steps if isinstance(st, dict)]
                    if isinstance(raw_steps, list)
                    else []
                )
                matched_steps = [
                    st
                    for st in steps
                    if not q
                    or q in nfc(str(st.get("title") or "")).lower()
                    or q in nfc(str(st.get("detail") or "")).lower()
                    or q in sec_title.lower()
                    or q in sec_sub.lower()
                    or q in sec_kw.lower()
                ]
                if not matched_steps:
                    continue
                visible_sections += 1
                block = self._build_section_block(idx, sec_title, sec_sub, matched_steps)
                self._sections_layout.addWidget(block)
                block.show()

        if visible_sections == 0:
            msg = (
                "Đang hiển thị mục Câu hỏi thường gặp."
                if self._topic == "faq"
                else "Không tìm thấy hướng dẫn phù hợp."
            )
            empty_lbl = QLabel(nfc(msg), self._sections_container)
            empty_lbl.setFont(ui_font(FS_BODY, 500))
            empty_lbl.setStyleSheet(f"color: {PORCELAIN_TOKENS.SLATE_MUTED}; padding: 14px 16px;")
            self._sections_layout.addWidget(empty_lbl)
            empty_lbl.show()
        self._sections_layout.addStretch(1)

        matched_faqs: list[dict[str, Any]] = []
        for f in self._faqs:
            fq = nfc(str(f.get("question") or ""))
            fa = nfc(str(f.get("answer") or ""))
            raw_fkw = f.get("keywords")
            if isinstance(raw_fkw, list):
                fkw = nfc(" ".join(str(k) for k in raw_fkw if k is not None))
            else:
                fkw = nfc(str(raw_fkw or ""))
            if not q or q in fq.lower() or q in fa.lower() or q in fkw.lower():
                matched_faqs.append(f)

        if matched_faqs:
            for idx, f in enumerate(matched_faqs):
                row = FaqAccordionRow(
                    str(f.get("question") or ""),
                    str(f.get("answer") or ""),
                    expanded=(idx < 2 or bool(q)),
                    is_last=(idx == len(matched_faqs) - 1),
                    parent=self.faq_table,
                )
                row.expanded_changed.connect(lambda _exp: self._sync_collapsed_scroll_heights())
                self._faq_layout.addWidget(row)
                row.show()
                self._faq_rows.append(row)
        else:
            empty_faq = QLabel(nfc("Không tìm thấy câu hỏi phù hợp."), self.faq_table)
            empty_faq.setFont(ui_font(FS_BODY, 500))
            empty_faq.setStyleSheet(f"color: {PORCELAIN_TOKENS.SLATE_MUTED}; padding: 14px 16px;")
            self._faq_layout.addWidget(empty_faq)
            empty_faq.show()

        self.frame.set_meta(f"{visible_sections} mục · {len(matched_faqs)} câu hỏi thường gặp")
        self._sync_meta_max_width()
        self.frame.meta_label.setVisible(
            self._last_layout_width >= 860 and bool(self.frame.meta_label.text())
        )
        self._sync_collapsed_scroll_heights()
        self._schedule_collapsed_sync()

    def _build_section_block(
        self,
        idx: int,
        title: str,
        subtitle: str,
        steps: list[dict[str, Any]],
    ) -> QFrame:
        p = PORCELAIN_TOKENS
        block = QFrame(self._sections_container)
        block.setObjectName("guideSectionBlock")
        block.setStyleSheet(
            f"QFrame#guideSectionBlock {{ background: {p.WHITE}; border: none; "
            f"border-bottom: 1px solid {p.HAIRLINE}; }}"
        )
        lay = QVBoxLayout(block)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        head = QFrame(block)
        head.setStyleSheet(f"background: {p.NAVY_SOLID}; border: none;")
        h_lay = QHBoxLayout(head)
        h_lay.setContentsMargins(14, 6, 14, 6)
        h_lay.setSpacing(10)

        t_lbl = QLabel(nfc(f"{idx + 1}. {title}"), head)
        t_lbl.setFont(ui_font(FS_BODY, 700))
        t_lbl.setStyleSheet("color: #FFFFFF; background: transparent;")
        h_lay.addWidget(t_lbl, 0)

        s_lbl = QLabel(nfc(subtitle), head)
        s_lbl.setFont(ui_font(FS_CAPTION, 400))
        s_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        s_lbl.setStyleSheet("color: #CBD5E1; background: transparent;")
        s_lbl.setWordWrap(True)
        h_lay.addWidget(s_lbl, 1)
        lay.addWidget(head)

        for s_idx, st in enumerate(steps):
            bg = p.ICE_ROW_ALT if s_idx % 2 == 1 else p.WHITE
            bottom = "none" if s_idx == len(steps) - 1 else f"1px solid {p.HAIRLINE_CELL}"
            row = QFrame(block)
            row.setStyleSheet(f"background: {bg}; border: none; border-bottom: {bottom};")
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(0, 0, 0, 0)
            r_lay.setSpacing(0)

            num_lbl = QLabel(nfc(f"Bước {s_idx + 1}"), row)
            num_lbl.setFixedWidth(72)
            num_lbl.setFont(ui_font(FS_CAPTION, 700, tabular=True))
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            num_lbl.setStyleSheet(
                f"color: {p.CYAN_TEXT_DEEP}; background: transparent; padding: 7px 10px 7px 14px; "
                f"border-right: 1px solid {p.HAIRLINE_CELL};"
            )
            r_lay.addWidget(num_lbl, 0)

            st_title = html.escape(nfc(str(st.get("title", ""))))
            st_detail = html.escape(nfc(str(st.get("detail", ""))))
            body_lbl = QLabel(f"<b>{st_title}</b> {st_detail}", row)
            body_lbl.setFont(ui_font(FS_META, 400))
            body_lbl.setWordWrap(True)
            body_lbl.setTextFormat(Qt.TextFormat.RichText)
            body_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            body_lbl.setStyleSheet(
                f"color: {p.SLATE_BODY}; background: transparent; padding: 7px 14px 7px 12px;"
            )
            r_lay.addWidget(body_lbl, 1)

            lay.addWidget(row)

        return block
