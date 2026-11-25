# -*- coding: utf-8 -*-
"""
Non-blocking bottom-center ToastBanner overlay with auto-dismiss and zero QGraphicsEffect.
"""
from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QRectF, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPalette, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from ..theme.tokens import PORCELAIN_TOKENS
from ..theme.typography import FS_BODY, nfc, ui_font


class ToastBanner(QFrame):
    """Floating non-blocking status toast centered near the bottom of its parent widget."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        reduced_motion: bool = False,
    ) -> None:
        super().__init__(parent)
        self._reduced_motion = bool(reduced_motion)
        self._tone = "success"
        self._opacity = 1.0

        self.setObjectName("toastBanner")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 8, 16, 8)
        lay.setSpacing(8)

        self.message_label = QLabel("", self)
        self.message_label.setFont(ui_font(FS_BODY, 600))
        self.message_label.setWordWrap(False)
        lay.addWidget(self.message_label)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.dismiss)

        self._fade_anim = QVariantAnimation(self)
        self._fade_anim.setDuration(0 if self._reduced_motion else 150)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.valueChanged.connect(self._on_fade_value)
        self._fade_anim.finished.connect(self._on_fade_finished)
        self._fading_out = False

        self.setVisible(False)

    def _on_fade_value(self, value) -> None:
        self._opacity = float(value)
        self._apply_label_opacity()
        self.update()

    def _on_fade_finished(self) -> None:
        if self._fading_out:
            self._fading_out = False
            self.setVisible(False)

    def _apply_label_opacity(self) -> None:
        _, _, fg = self._tone_colors()
        alpha_f = max(0.0, min(1.0, float(self._opacity)))
        alpha = max(0, min(255, round(alpha_f * 255)))
        faded = QColor(fg.red(), fg.green(), fg.blue(), alpha)
        pal = self.message_label.palette()
        pal.setColor(QPalette.ColorRole.WindowText, faded)
        self.message_label.setPalette(pal)
        self.message_label.setStyleSheet(
            f"color: rgba({fg.red()}, {fg.green()}, {fg.blue()}, {alpha_f:.4f}); background: transparent;"
        )

    def set_reduced_motion(self, enabled: bool) -> None:
        self._reduced_motion = bool(enabled)
        self._fade_anim.setDuration(0 if self._reduced_motion else 150)

    def _tone_colors(self) -> tuple[QColor, QColor, QColor]:
        p = PORCELAIN_TOKENS
        if self._tone in ("warn", "warning"):
            return QColor(p.TOAST_WARN_BG), QColor(p.TOAST_WARN_BORDER), QColor(p.TOAST_WARN_TEXT)
        if self._tone in ("error", "danger"):
            return QColor(p.TOAST_ERR_BG), QColor(p.TOAST_ERR_BORDER), QColor(p.TOAST_ERR_TEXT)
        if self._tone == "info":
            return QColor(p.TOAST_INFO_BG), QColor(p.TOAST_INFO_BORDER), QColor(p.TOAST_INFO_TEXT)
        return QColor(p.TOAST_BG), QColor(p.TOAST_BORDER), QColor(p.TOAST_TEXT)

    def show_message(
        self,
        text: str,
        *,
        tone: str = "success",
        duration_ms: int = 2600,
    ) -> None:
        self._tone = tone or "success"
        self.message_label.setText(nfc(text))
        self.message_label.setWordWrap(False)

        self._hide_timer.stop()
        self._fade_anim.stop()
        self._fading_out = False

        if self._reduced_motion:
            self._opacity = 1.0
        else:
            self._opacity = 0.0
        self._apply_label_opacity()

        self.adjustSize()
        self.reposition()

        self.show()
        self.raise_()
        self.update()

        if not self._reduced_motion:
            self._fade_anim.blockSignals(True)
            self._fade_anim.setCurrentTime(0)
            self._fade_anim.blockSignals(False)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.start()

        if duration_ms > 0:
            self._hide_timer.start(int(duration_ms))

    show_toast = show_message

    def dismiss(self) -> None:
        self._hide_timer.stop()
        if self.isHidden():
            return
        if self._reduced_motion:
            self._fade_anim.stop()
            self._fade_anim.setCurrentTime(0)
            self._fading_out = False
            self._opacity = 0.0
            self._apply_label_opacity()
            self.setVisible(False)
            return
        self._fade_anim.stop()
        self._fading_out = True
        self._fade_anim.blockSignals(True)
        self._fade_anim.setCurrentTime(0)
        self._fade_anim.blockSignals(False)
        self._fade_anim.setStartValue(self._opacity)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.start()

    def reposition(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        max_w = max(200, parent.width() - 48)
        self.message_label.setWordWrap(False)
        self.message_label.setMaximumWidth(16777215)
        if self.layout() is not None:
            self.layout().invalidate()
            self.layout().activate()
        hint = self.sizeHint()
        if hint.width() > max_w:
            self.message_label.setWordWrap(True)
            w = max_w
            avail_lbl_w = max(120, max_w - 32)
            lbl_h = self.message_label.heightForWidth(avail_lbl_w)
            if lbl_h <= 0:
                lbl_h = self.message_label.sizeHint().height()
            h = max(hint.height(), lbl_h + 16)
        else:
            w = hint.width()
            h = hint.height()
        x = max(12, (parent.width() - w) // 2)
        y = max(12, parent.height() - h - 18)
        self.setGeometry(x, y, w, h)
        if self.layout() is not None:
            self.layout().activate()

    def paintEvent(self, event) -> None:  # noqa: N802
        bg, border, _ = self._tone_colors()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setOpacity(max(0.0, min(1.0, self._opacity)))

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, float(PORCELAIN_TOKENS.CONTROL_RADIUS), float(PORCELAIN_TOKENS.CONTROL_RADIUS))
        painter.fillPath(path, bg)

        pen = QPen(border, 1.0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.end()
