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

import math
from typing import Optional

from PySide6.QtCore import QElapsedTimer, QPoint, QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QImage,
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


class MarqueeLabel(QLabel):
    """Single-line label that smoothly scrolls back-and-forth whenever text overflows its width."""

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
        *,
        text_color: str | None = None,
        min_width: int = 88,
        speed_px_s: float = 34.0,
        pause_s: float = 1.35,
    ) -> None:
        super().__init__(text, parent)
        self._text_color = QColor(text_color) if text_color else None
        self._min_w = max(32, int(min_width))
        self._speed_px_s = max(12.0, float(speed_px_s))
        self._pause_s = max(0.4, float(pause_s))
        self._offset_px: float = 0.0
        self._clock = QElapsedTimer()
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._on_tick)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._sync_marquee(reset=True)

    def _text_width(self) -> int:
        txt = self.text()
        if not txt:
            return 0
        return int(math.ceil(self.fontMetrics().horizontalAdvance(txt)))

    def _overflow_px(self) -> int:
        avail = max(0, self.contentsRect().width())
        if avail <= 0:
            return 0
        return max(0, self._text_width() - avail)

    def _max_shift_px(self) -> float:
        ov = self._overflow_px()
        return float(ov + 6) if ov > 2 else 0.0

    def sizeHint(self) -> QSize:  # noqa: N802
        fm = self.fontMetrics()
        tw = self._text_width()
        h = max(super().sizeHint().height(), fm.height() + 2)
        return QSize(tw + 2 if tw else 0, h)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        fm = self.fontMetrics()
        tw = self._text_width()
        h = max(16, fm.height() + 2)
        return QSize(min(self._min_w, tw + 2) if tw else 0, h)

    def setText(self, text: str) -> None:  # noqa: N802
        super().setText(text)
        self.updateGeometry()
        self._sync_marquee(reset=True)

    def setFont(self, font) -> None:  # noqa: N802
        super().setFont(font)
        self.updateGeometry()
        self._sync_marquee(reset=True)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._sync_marquee(reset=False)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._sync_marquee(reset=True)

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        if self._timer.isActive():
            self._timer.stop()

    def _sync_marquee(self, *, reset: bool) -> None:
        max_shift = self._max_shift_px()
        if max_shift > 0.0:
            self.setToolTip(self.text())
            if reset:
                self._offset_px = 0.0
                self._clock.restart()
            elif not self._clock.isValid():
                self._clock.start()
            if self.isVisible() and not self._timer.isActive():
                self._timer.start()
        else:
            self.setToolTip("")
            self._offset_px = 0.0
            if self._timer.isActive():
                self._timer.stop()
        self.update()

    def _on_tick(self) -> None:
        max_shift = self._max_shift_px()
        if max_shift <= 0.0 or not self.isVisible():
            self._offset_px = 0.0
            self._timer.stop()
            self.update()
            return
        travel_fwd = max(0.8, max_shift / self._speed_px_s)
        travel_back = max(0.65, max_shift / (self._speed_px_s * 1.25))
        cycle = self._pause_s + travel_fwd + self._pause_s + travel_back
        t = (self._clock.elapsed() / 1000.0) % cycle
        if t < self._pause_s:
            offset = 0.0
        elif t < self._pause_s + travel_fwd:
            frac = (t - self._pause_s) / travel_fwd
            offset = max_shift * (0.5 - 0.5 * math.cos(math.pi * frac))
        elif t < self._pause_s + travel_fwd + self._pause_s:
            offset = max_shift
        else:
            frac = (t - self._pause_s - travel_fwd - self._pause_s) / travel_back
            offset = max_shift * (0.5 + 0.5 * math.cos(math.pi * frac))
        if abs(offset - self._offset_px) >= 0.2:
            self._offset_px = offset
            self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        max_shift = self._max_shift_px()
        if max_shift <= 0.0:
            super().paintEvent(event)
            return
        rect = self.contentsRect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        dpr = max(1.0, float(self.devicePixelRatioF()))
        img_w = max(1, int(round(rect.width() * dpr)))
        img_h = max(1, int(round(rect.height() * dpr)))
        buf = QImage(img_w, img_h, QImage.Format.Format_ARGB32_Premultiplied)
        buf.setDevicePixelRatio(dpr)
        buf.fill(Qt.GlobalColor.transparent)

        p = QPainter(buf)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        p.setFont(self.font())
        color = self._text_color or self.palette().color(self.foregroundRole())
        p.setPen(color)
        fm = self.fontMetrics()
        baseline_y = (rect.height() + fm.ascent() - fm.descent()) / 2.0
        p.drawText(QPointF(-self._offset_px, baseline_y), self.text())

        fade = min(14.0, rect.width() * 0.14)
        if fade >= 2.0:
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
            grad = QLinearGradient(0.0, 0.0, float(rect.width()), 0.0)
            f_norm = fade / float(rect.width())
            left_clipped = self._offset_px > 1.0
            right_clipped = self._offset_px < (max_shift - 1.0)
            grad.setColorAt(0.0, QColor(0, 0, 0, 0 if left_clipped else 255))
            if left_clipped:
                grad.setColorAt(f_norm, QColor(0, 0, 0, 255))
            if right_clipped:
                grad.setColorAt(1.0 - f_norm, QColor(0, 0, 0, 255))
            grad.setColorAt(1.0, QColor(0, 0, 0, 0 if right_clipped else 255))
            p.fillRect(QRectF(0.0, 0.0, float(rect.width()), float(rect.height())), QBrush(grad))
        p.end()

        out = QPainter(self)
        out.drawImage(rect.topLeft(), buf)
        out.end()


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

        self.title_label = MarqueeLabel(nfc(title), self.header_bar, text_color="#FFFFFF", min_width=150)
        self.title_label.setFont(ui_font(FS_HEADER, 700))
        self.title_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        self._title_row.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.status_tag = HeaderStatusTag(status_tag or "", parent=self.header_bar)
        self.status_tag.setVisible(bool(status_tag))
        self._title_row.addWidget(self.status_tag, 0, Qt.AlignmentFlag.AlignVCenter)

        meta_text = meta or subtitle
        self.meta_label = MarqueeLabel(nfc(meta_text), self.header_bar, text_color="#CBD5E1", min_width=90)
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
