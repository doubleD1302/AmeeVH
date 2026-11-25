# -*- coding: utf-8 -*-
"""
Universal Light Porcelain + Navy Header frame and frameless dialog base.

Enforces Stage 1r3/1r4/1r5 contracts:
- Single outer #F6F9FD surface with 1px cosmetic hairline border (zero nested rounded boxes).
- #264278 -> #1B3260 Navy header bar (48 DIP default, 56 DIP error variant w/ 5px #E11D48 left bar).
- Right-anchored horizontally mirrored zs_common_pop_01.png halftone at opacity 0.11.
- Automatic 1px x 22px rgba(255,255,255,0.18) vertical divider whenever header controls exist.
- Universal far-right 28x28 Close (×) button (btn_common_close_01.png, fallback asar_close.svg)
  and Escape shortcut emitting close_requested.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QKeyEvent,
    QKeySequence,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QShortcut,
    QTransform,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..theme.tokens import PORCELAIN_TOKENS, rgba_qcolor
from ..theme.typography import FS_HEADER, FS_META, nfc, ui_font
from .asset_renderer import AssetRenderer, get_asset_renderer
from .status_badge import HeaderStatusTag


class _PorcelainHeaderBar(QWidget):
    """Navy gradient header bar with mirrored halftone and bottom/left accent lines."""

    def __init__(
        self,
        *,
        variant: str = "default",
        asset_renderer: AssetRenderer,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._variant = variant
        self._renderer = asset_renderer
        self._drag_pos: Optional[QPoint] = None
        self._draggable_window: Optional[QWidget] = None
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._sync_height()

    def set_variant(self, variant: str) -> None:
        self._variant = variant or "default"
        self._sync_height()
        self.update()

    def set_drag_target(self, window: QWidget | None) -> None:
        self._draggable_window = window

    def _sync_height(self) -> None:
        min_h = (
            PORCELAIN_TOKENS.ERROR_HEADER_MIN_HEIGHT
            if self._variant == "error"
            else PORCELAIN_TOKENS.HEADER_MIN_HEIGHT
        )
        self.setMinimumHeight(min_h)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = PORCELAIN_TOKENS
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        rect = QRectF(self.rect())
        # Clip top corners to match outer 6px radius
        path = QPainterPath()
        r = float(p.WINDOW_RADIUS)
        path.moveTo(rect.left(), rect.bottom())
        path.lineTo(rect.left(), rect.top() + r)
        path.quadTo(rect.left(), rect.top(), rect.left() + r, rect.top())
        path.lineTo(rect.right() - r, rect.top())
        path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + r)
        path.lineTo(rect.right(), rect.bottom())
        path.closeSubpath()
        painter.setClipPath(path)

        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, QColor(p.NAVY_HEADER_TOP_LEFT))
        grad.setColorAt(1.0, QColor(p.NAVY_HEADER_BOTTOM_RIGHT))
        painter.fillRect(rect, QBrush(grad))

        # Mirrored Unity halftone anchored top-right at opacity 0.11
        halftone = self._renderer.get_master_pixmap("game/zs_common_pop_01.png")
        if not halftone.isNull() and halftone.height() > 0:
            scale = rect.height() / float(halftone.height())
            draw_w = float(halftone.width()) * scale
            painter.save()
            painter.setOpacity(0.11)
            transform = QTransform()
            transform.translate(rect.right(), rect.top())
            transform.scale(-1.0, 1.0)
            painter.setTransform(transform)
            painter.drawPixmap(
                QRectF(0.0, 0.0, draw_w, rect.height()),
                halftone,
                QRectF(0.0, 0.0, float(halftone.width()), float(halftone.height())),
            )
            painter.restore()

        # Accent stripes: 2px bottom (#12B8C4 default, #E11D48 error, #D97706 warning)
        if self._variant == "error":
            accent = QColor(p.CORAL_DANGER)
            painter.fillRect(
                QRectF(rect.left(), rect.top(), float(p.ERROR_HEADER_BORDER_LEFT), rect.height()),
                accent,
            )
        elif self._variant == "warning":
            accent = QColor(p.WARN_ACCENT)
            painter.fillRect(
                QRectF(rect.left(), rect.top(), float(p.ERROR_HEADER_BORDER_LEFT), rect.height()),
                accent,
            )
        else:
            accent = QColor(p.CYAN_ACCENT)

        painter.fillRect(
            QRectF(
                rect.left(),
                rect.bottom() - float(p.HEADER_BORDER_BOTTOM),
                rect.width(),
                float(p.HEADER_BORDER_BOTTOM),
            ),
            accent,
        )
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._draggable_window is not None and event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._draggable_window.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if (
            self._draggable_window is not None
            and self._drag_pos is not None
            and (event.buttons() & Qt.MouseButton.LeftButton)
        ):
            self._draggable_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class PorcelainWindowFrame(QFrame):
    """Universal Light Porcelain surface with Navy Header, controls divider, Close (×), and Esc."""

    close_requested = Signal()

    def __init__(
        self,
        title: str = "",
        *,
        subtitle: str = "",
        meta: str = "",
        icon_path: str | None = None,
        icon_size: tuple[int, int] = (22, 22),
        variant: str = "default",
        status_tag: str | None = None,
        is_modal: bool = False,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer or get_asset_renderer()
        self._is_modal = bool(is_modal)
        self._variant = variant or "default"
        self._icon_path = icon_path
        self._icon_size = icon_size

        self.setObjectName("porcelainWindowFrame")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        # 1. Navy Header Bar
        self.header_bar = _PorcelainHeaderBar(variant=self._variant, asset_renderer=self._renderer, parent=self)
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(18, 8, 18, 8)
        header_layout.setSpacing(10)

        self.icon_label = QLabel(self.header_bar)
        self.icon_label.setFixedSize(icon_size[0], icon_size[1])
        self.icon_label.setScaledContents(False)
        self.icon_label.setVisible(False)
        header_layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        # Title + optional stacked left-widget (used by SmartErrorDialog code badge row)
        self._title_col = QVBoxLayout()
        self._title_col.setContentsMargins(0, 0, 0, 0)
        self._title_col.setSpacing(2)

        self._header_left_slot = QHBoxLayout()
        self._header_left_slot.setContentsMargins(0, 0, 0, 0)
        self._header_left_slot.setSpacing(8)
        self._header_left_slot_widget: Optional[QWidget] = None
        self._title_col.addLayout(self._header_left_slot)

        self._title_row = QHBoxLayout()
        self._title_row.setContentsMargins(0, 0, 0, 0)
        self._title_row.setSpacing(10)

        self.title_label = QLabel(nfc(title), self.header_bar)
        self.title_label.setFont(ui_font(FS_HEADER, 700))
        self.title_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self._title_row.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.status_tag = HeaderStatusTag(status_tag or "", parent=self.header_bar)
        self.status_tag.setVisible(bool(status_tag))
        self._title_row.addWidget(self.status_tag, 0, Qt.AlignmentFlag.AlignVCenter)

        meta_text = meta or subtitle
        self.meta_label = QLabel(nfc(meta_text), self.header_bar)
        self.meta_label.setFont(ui_font(FS_META, 500))
        self.meta_label.setStyleSheet("color: #CBD5E1; background: transparent;")
        self.meta_label.setVisible(bool(meta_text))
        self._title_row.addWidget(self.meta_label, 0, Qt.AlignmentFlag.AlignVCenter)
        self._title_row.addStretch(1)

        self._title_col.addLayout(self._title_row)
        header_layout.addLayout(self._title_col, 1)

        # Header Right: custom controls + vertical divider + universal far-right Close (×)
        self.header_right_layout = QHBoxLayout()
        self.header_right_layout.setContentsMargins(0, 0, 0, 0)
        self.header_right_layout.setSpacing(10)

        self.header_controls_layout = QHBoxLayout()
        self.header_controls_layout.setContentsMargins(0, 0, 0, 0)
        self.header_controls_layout.setSpacing(8)
        self.header_right_layout.addLayout(self.header_controls_layout)

        self.header_divider = QFrame(self.header_bar)
        self.header_divider.setObjectName("headerControlsDivider")
        self.header_divider.setFixedSize(1, 22)
        self.header_divider.setStyleSheet("background: rgba(255, 255, 255, 0.18); border: none;")
        self.header_divider.setVisible(False)
        self.header_right_layout.addWidget(self.header_divider, 0, Qt.AlignmentFlag.AlignVCenter)

        self.close_button = QPushButton(self.header_bar)
        self.close_button.setObjectName("porcelainCloseBtn")
        self.close_button.setFixedSize(28, 28)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.setToolTip(nfc("Đóng (Esc)"))
        self.close_button.setFlat(True)
        self.close_button.setStyleSheet(
            "QPushButton#porcelainCloseBtn { border: none; border-radius: 4px; background: transparent; padding: 0; }"
            "QPushButton#porcelainCloseBtn:hover { background: rgba(255, 255, 255, 0.16); }"
            "QPushButton#porcelainCloseBtn:pressed { background: rgba(255, 255, 255, 0.24); }"
        )
        self.close_button.clicked.connect(self.close_requested.emit)
        self.header_right_layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignVCenter)

        header_layout.addLayout(self.header_right_layout, 0)
        root.addWidget(self.header_bar)

        # 2. Optional Underline Tabs Slot (#FFFFFF + #D5E0EE bottom hairline)
        self.tabs_container = QFrame(self)
        self.tabs_container.setObjectName("porcelainTabsHost")
        self.tabs_container.setStyleSheet(
            f"QFrame#porcelainTabsHost {{ background: {PORCELAIN_TOKENS.WHITE}; "
            f"border: none; border-bottom: 1px solid {PORCELAIN_TOKENS.HAIRLINE}; }}"
        )
        self.tabs_layout = QVBoxLayout(self.tabs_container)
        self.tabs_layout.setContentsMargins(18, 0, 18, 0)
        self.tabs_layout.setSpacing(0)
        self.tabs_container.setVisible(False)
        root.addWidget(self.tabs_container)

        # 3. Body Container
        self.body_container = QWidget(self)
        self.body_container.setObjectName("porcelainBodyHost")
        self.body_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._body_layout = QVBoxLayout(self.body_container)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(0)
        root.addWidget(self.body_container, 1)

        # 4. Optional Footer Slot (#EEF4FA + #D5E0EE top hairline)
        self.footer_container = QFrame(self)
        self.footer_container.setObjectName("porcelainFooterHost")
        self.footer_container.setStyleSheet(
            f"QFrame#porcelainFooterHost {{ background: {PORCELAIN_TOKENS.ICE_ZEBRA}; "
            f"border: none; border-top: 1px solid {PORCELAIN_TOKENS.HAIRLINE}; }}"
        )
        self.footer_layout = QVBoxLayout(self.footer_container)
        self.footer_layout.setContentsMargins(18, 11, 18, 11)
        self.footer_layout.setSpacing(0)
        self.footer_container.setVisible(False)
        root.addWidget(self.footer_container)

        # Esc shortcut -> close_requested
        self._esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self._esc_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._esc_shortcut.activated.connect(self.close_requested.emit)

        self._refresh_icons()

    def _current_dpr(self) -> float:
        try:
            return max(1.0, float(self.devicePixelRatioF()))
        except Exception:  # noqa: BLE001
            return 1.0

    def _refresh_icons(self) -> None:
        dpr = self._current_dpr()
        if self._icon_path:
            pix = self._renderer.get_icon_pixmap(self._icon_path, self._icon_size, dpr)
            if not pix.isNull():
                self.icon_label.setPixmap(pix)
                self.icon_label.setVisible(True)
            else:
                self.icon_label.setVisible(False)
        else:
            self.icon_label.setVisible(False)

        close_icon = self._renderer.get_icon("game/btn_common_close_01.png", (20, 20), dpr)
        if close_icon.isNull():
            close_icon = self._renderer.get_icon("game/asar_close.svg", (16, 16), dpr)
        self.close_button.setIcon(close_icon)
        self.close_button.setIconSize(QSize(20, 20))

    def refresh_dpr(self) -> None:
        self._refresh_icons()

    def set_title(self, title: str) -> None:
        self.title_label.setText(nfc(title))

    def set_meta(self, meta: str) -> None:
        txt = nfc(meta)
        self.meta_label.setText(txt)
        self.meta_label.setVisible(bool(txt))

    def set_status_tag(self, tag: str | None) -> None:
        txt = nfc(tag or "")
        self.status_tag.setText(txt)
        self.status_tag.setVisible(bool(txt))

    def set_variant(self, variant: str) -> None:
        self._variant = variant or "default"
        self.header_bar.set_variant(self._variant)

    def set_icon(self, icon_path: str | None, icon_size: tuple[int, int] = (22, 22)) -> None:
        self._icon_path = icon_path
        self._icon_size = icon_size
        self.icon_label.setFixedSize(icon_size[0], icon_size[1])
        self._refresh_icons()

    def set_header_left_widget(self, widget: QWidget | None) -> None:
        if self._header_left_slot_widget is not None:
            self._header_left_slot.removeWidget(self._header_left_slot_widget)
            self._header_left_slot_widget.setParent(None)
        self._header_left_slot_widget = widget
        if widget is not None:
            self._header_left_slot.addWidget(widget)

    def add_header_control(self, widget: QWidget) -> None:
        """Append a control left of the automatic vertical divider and far-right Close button."""
        self.header_controls_layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        self.header_divider.setVisible(self.header_controls_layout.count() > 0)

    def clear_header_controls(self) -> None:
        while self.header_controls_layout.count():
            item = self.header_controls_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        self.header_divider.setVisible(False)

    def set_tabs_bar(self, widget: QWidget | None) -> None:
        while self.tabs_layout.count():
            item = self.tabs_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        if widget is not None:
            self.tabs_layout.addWidget(widget)
            self.tabs_container.setVisible(True)
        else:
            self.tabs_container.setVisible(False)

    def body_layout(self) -> QVBoxLayout:
        return self._body_layout

    def set_body(self, widget: QWidget) -> None:
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        self._body_layout.addWidget(widget)

    def set_footer(self, widget: QWidget | None) -> None:
        while self.footer_layout.count():
            item = self.footer_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        if widget is not None:
            self.footer_layout.addWidget(widget)
            self.footer_container.setVisible(True)
        else:
            self.footer_container.setVisible(False)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            event.accept()
            self.close_requested.emit()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = PORCELAIN_TOKENS
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        r = float(p.WINDOW_RADIUS)

        border_rgba = p.MODAL_BORDER_RGBA if self._is_modal else p.WINDOW_BORDER_RGBA
        painter.setBrush(QColor(p.PORCELAIN_BG))
        pen = QPen(rgba_qcolor(border_rgba), 1.0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, r, r)
        painter.end()


class PorcelainDialog(QDialog):
    """Frameless Light Porcelain modal dialog base wrapping PorcelainWindowFrame."""

    def __init__(
        self,
        title: str = "",
        *,
        subtitle: str = "",
        meta: str = "",
        icon_path: str | None = None,
        icon_size: tuple[int, int] = (22, 22),
        variant: str = "default",
        status_tag: str | None = None,
        target_width: int = 640,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._target_width = int(target_width)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.frame = PorcelainWindowFrame(
            title=title,
            subtitle=subtitle,
            meta=meta,
            icon_path=icon_path,
            icon_size=icon_size,
            variant=variant,
            status_tag=status_tag,
            is_modal=True,
            asset_renderer=asset_renderer,
            parent=self,
        )
        self.frame.header_bar.set_drag_target(self)
        self.frame.close_requested.connect(self.reject)
        outer.addWidget(self.frame)

        self.setMaximumWidth(self._target_width)
        self.resize(self._target_width, self.sizeHint().height())

    @property
    def close_button(self) -> QPushButton:
        return self.frame.close_button

    def add_header_control(self, widget: QWidget) -> None:
        self.frame.add_header_control(widget)

    def set_header_left_widget(self, widget: QWidget | None) -> None:
        self.frame.set_header_left_widget(widget)

    def set_tabs_bar(self, widget: QWidget | None) -> None:
        self.frame.set_tabs_bar(widget)

    def set_body(self, widget: QWidget) -> None:
        self.frame.set_body(widget)

    def set_footer(self, widget: QWidget | None) -> None:
        self.frame.set_footer(widget)

    def compact_layout(self, available_width: int, available_height: int | None = None) -> None:
        clamped_w = max(320, min(self._target_width, int(available_width) - 32))
        self.setFixedWidth(clamped_w)
        if available_height is not None:
            self.setMaximumHeight(max(240, int(available_height) - 24))
        self.adjustSize()
