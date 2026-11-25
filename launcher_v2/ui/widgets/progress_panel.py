# -*- coding: utf-8 -*-
"""
Inline recessed ProgressPanel bound directly to core/types.OperationEvent.

Displays spinner_00..11.svg (frozen on reduced_motion), phase message, tabular %,
progress bar, tabular MB / MB/s / ETA, inline file-stage segments, and Cancel button.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ...core.types import OperationEvent, OperationPhase
from ..theme.tokens import OV_TOKENS, rgba_qcolor
from ..theme.typography import FS_BODY_SM, FS_CAPTION, FS_META, nfc, ui_font
from .asset_renderer import AssetRenderer, get_asset_renderer


def format_eta(eta_seconds: float | None) -> str:
    if eta_seconds is None or eta_seconds < 0:
        return "--"
    secs = max(0, round(float(eta_seconds)))
    if secs < 60:
        return f"{secs} giây"
    mins, rem = divmod(secs, 60)
    if mins < 60:
        return f"{mins}p {rem:02d}s"
    hours, rem_m = divmod(mins, 60)
    return f"{hours}g {rem_m:02d}p"


class _ProgressTrack(QWidget):
    """6px rounded progress track with #25C8CE -> #34D399 gradient fill."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ratio = 0.0
        self.setFixedHeight(6)

    def set_ratio(self, ratio: float) -> None:
        self._ratio = max(0.0, min(1.0, float(ratio)))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())

        track_path = QPainterPath()
        track_path.addRoundedRect(rect, 3.0, 3.0)
        painter.fillPath(track_path, rgba_qcolor(OV_TOKENS.PROGRESS_TRACK_RGBA))

        if self._ratio > 0.0:
            fill_w = max(6.0, rect.width() * self._ratio) if self._ratio > 0.01 else rect.width() * self._ratio
            fill_w = min(rect.width(), fill_w)
            fill_rect = QRectF(rect.left(), rect.top(), fill_w, rect.height())
            grad = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
            grad.setColorAt(0.0, QColor(OV_TOKENS.CYAN_ACCENT))
            grad.setColorAt(1.0, QColor(OV_TOKENS.PROGRESS_END_GREEN))

            painter.save()
            painter.setClipPath(track_path)
            painter.fillRect(fill_rect, QBrush(grad))
            painter.restore()
        painter.end()


class ProgressPanel(QFrame):
    """Inline recessed download/patch progress strip bound to OperationEvent."""

    cancel_requested = Signal()

    def __init__(
        self,
        *,
        reduced_motion: bool = False,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer or get_asset_renderer()
        self._reduced_motion = bool(reduced_motion)
        self._spinner_index = 0
        self._cancellable = True
        self._active = False
        self._phase: OperationPhase = OperationPhase.IDLE

        self.setObjectName("progressPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(15, 9, 12, 9)
        root.setSpacing(6)

        # Row 1: Spinner + Phase message + Percentage
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(7)

        self.spinner_label = QLabel(self)
        self.spinner_label.setFixedSize(12, 12)
        top_row.addWidget(self.spinner_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.phase_label = QLabel(nfc("Đang chuẩn bị..."), self)
        self.phase_label.setFont(ui_font(FS_BODY_SM, 600))
        self.phase_label.setStyleSheet(f"color: {OV_TOKENS.DL_PHASE_TEXT}; background: transparent;")
        top_row.addWidget(self.phase_label, 1, Qt.AlignmentFlag.AlignVCenter)

        self.percent_label = QLabel("0%", self)
        self.percent_label.setFont(ui_font(FS_BODY_SM, 700, tabular=True))
        self.percent_label.setStyleSheet(f"color: {OV_TOKENS.CYAN_ACCENT}; background: transparent;")
        top_row.addWidget(self.percent_label, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(top_row)

        # Row 2: Progress Track
        self.track = _ProgressTrack(self)
        root.addWidget(self.track)

        # Row 3: Tabular metrics + Cancel button
        metrics_row = QHBoxLayout()
        metrics_row.setContentsMargins(0, 0, 0, 0)
        metrics_row.setSpacing(8)

        self.metrics_label = QLabel("0.0 / 0.0 MB", self)
        self.metrics_label.setFont(ui_font(FS_META, 500, tabular=True))
        self.metrics_label.setStyleSheet(f"color: {OV_TOKENS.TEXT_SECONDARY}; background: transparent;")
        metrics_row.addWidget(self.metrics_label, 1, Qt.AlignmentFlag.AlignVCenter)

        self.cancel_button = QPushButton(nfc("Hủy"), self)
        self.cancel_button.setObjectName("dlCancelBtn")
        self.cancel_button.setFont(ui_font(FS_CAPTION, 600))
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setStyleSheet(
            f"QPushButton#dlCancelBtn {{ border: none; border-radius: 3px; "
            f"background: rgba(225, 29, 72, 0.22); color: {OV_TOKENS.CORAL_TEXT_LIGHT}; "
            f"padding: 2px 9px; }}"
            f"QPushButton#dlCancelBtn:hover {{ background: rgba(225, 29, 72, 0.38); }}"
            f"QPushButton#dlCancelBtn:disabled {{ opacity: 0.45; }}"
        )
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        metrics_row.addWidget(self.cancel_button, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(metrics_row)

        # Row 4: Inline file / stage status strip
        self.stage_label = QLabel("", self)
        self.stage_label.setFont(ui_font(FS_CAPTION, 500))
        self.stage_label.setStyleSheet(f"color: {OV_TOKENS.TEXT_MUTED}; background: transparent;")
        self.stage_label.setWordWrap(True)
        self.stage_label.setVisible(False)
        root.addWidget(self.stage_label)

        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(90)
        self._spinner_timer.timeout.connect(self._advance_spinner)

        self._render_spinner_frame(0)
        self.setVisible(False)

    def set_reduced_motion(self, enabled: bool) -> None:
        self._reduced_motion = bool(enabled)
        if self._reduced_motion:
            self._spinner_timer.stop()
            self._spinner_index = 0
            self._render_spinner_frame(0)
        elif self._active and self._phase not in (
            OperationPhase.IDLE,
            OperationPhase.DONE,
            OperationPhase.ERROR,
        ):
            self._spinner_timer.start()

    def _render_spinner_frame(self, index: int) -> None:
        dpr = max(1.0, float(self.devicePixelRatioF()))
        rel = f"spinner/spinner_{index % 12:02d}.svg"
        pix = self._renderer.get_svg_pixmap(rel, (12, 12), dpr, tint=OV_TOKENS.CYAN_ACCENT)
        if not pix.isNull():
            self.spinner_label.setPixmap(pix)

    def _advance_spinner(self) -> None:
        self._spinner_index = (self._spinner_index + 1) % 12
        self._render_spinner_frame(self._spinner_index)

    def set_active(self, active: bool, *, cancellable: bool = True, initial_message: str = "") -> None:
        self._active = bool(active)
        if not self._active:
            self._phase = OperationPhase.IDLE
        self._cancellable = bool(cancellable)
        self.cancel_button.setVisible(self._cancellable)
        self.cancel_button.setEnabled(self._cancellable)
        if initial_message:
            self.phase_label.setText(nfc(initial_message))
        self.setVisible(self._active)
        if self._active and not self._reduced_motion:
            self._spinner_timer.start()
        else:
            self._spinner_timer.stop()
            self._spinner_index = 0
            self._render_spinner_frame(0)

    def set_event(self, event: OperationEvent) -> None:
        """Update UI telemetry from an OperationEvent."""
        self._phase = event.phase
        if not self._active and event.phase not in (OperationPhase.IDLE, OperationPhase.DONE):
            self.set_active(True, cancellable=self._cancellable)

        self.phase_label.setText(nfc(event.message or event.phase.value))
        pct = event.percentage
        self.percent_label.setText(f"{pct:.0f}%")
        self.track.set_ratio(pct / 100.0)

        if event.unit == "bytes" and event.total > 0:
            done_mb = event.completed / (1024.0 * 1024.0)
            total_mb = event.total / (1024.0 * 1024.0)
            speed_mb = max(0.0, float(event.speed_bps)) / (1024.0 * 1024.0)
            eta_txt = format_eta(event.eta_seconds)
            if event.speed_bps > 0:
                self.metrics_label.setText(
                    nfc(f"{done_mb:.1f} / {total_mb:.1f} MB · {speed_mb:.1f} MB/s · Còn {eta_txt}")
                )
            else:
                self.metrics_label.setText(nfc(f"{done_mb:.1f} / {total_mb:.1f} MB"))
        elif event.total > 0:
            unit_label = "tệp" if event.unit == "items" else event.unit
            self.metrics_label.setText(nfc(f"{event.completed} / {event.total} {unit_label}"))
        else:
            self.metrics_label.setText("")

        # Inline file / stage status breadcrumb
        parts: list[str] = []
        if event.files_total > 0:
            parts.append(f"{event.files_completed}/{event.files_total} tệp")
        if event.phase == OperationPhase.DOWNLOAD:
            parts.append("Đang tải gói")
        elif event.phase == OperationPhase.VERIFY:
            parts.append("SHA256")
        elif event.phase == OperationPhase.BACKUP:
            parts.append("Sao lưu gốc")
        elif event.phase == OperationPhase.APPLY:
            parts.append("Áp dụng bản vá")
        elif event.phase == OperationPhase.READBACK:
            parts.append("Xác thực ghi")
        elif event.phase == OperationPhase.ROLLBACK:
            parts.append("Hoàn nguyên")

        stage_text = nfc(" · ".join(parts))
        self.stage_label.setText(stage_text)
        self.stage_label.setVisible(bool(stage_text))

        is_cancellable_phase = (
            event.phase in (OperationPhase.PREFLIGHT, OperationPhase.DOWNLOAD)
            or (event.phase == OperationPhase.ROLLBACK and event.unit == "bytes")
        )
        self.cancel_button.setVisible(self._cancellable and is_cancellable_phase)

        if event.phase in (OperationPhase.IDLE, OperationPhase.DONE, OperationPhase.ERROR):
            self._spinner_timer.stop()
            self._spinner_index = 0
            self._render_spinner_frame(0)
        elif self._active and not self._reduced_motion and not self._spinner_timer.isActive():
            self._spinner_timer.start()

    # Alias for callers using update_event
    update_event = set_event

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, float(OV_TOKENS.CONTROL_RADIUS), float(OV_TOKENS.CONTROL_RADIUS))
        painter.fillPath(path, rgba_qcolor(OV_TOKENS.RECESSED_DL_RGBA))

        painter.save()
        painter.setClipPath(path)
        painter.fillRect(
            QRectF(rect.left(), rect.top(), 3.0, rect.height()),
            QColor(OV_TOKENS.CYAN_ACCENT),
        )
        painter.restore()
        painter.end()
