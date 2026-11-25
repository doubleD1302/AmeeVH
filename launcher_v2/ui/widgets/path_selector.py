# -*- coding: utf-8 -*-
"""
Flat hairline-framed Unicode PathSelector with middle elision, tooltip,
Dò tìm / Chọn... triggers, and Explorer/Clipboard context menu.
"""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QAction, QColor, QGuiApplication, QPainter, QPainterPath
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget

from ..theme.tokens import OV_TOKENS, rgba_qcolor
from ..theme.typography import FS_BODY_SM, FS_META, FS_MICRO, mono_font, nfc, ui_font
from .asset_renderer import AssetRenderer, get_asset_renderer


class _MiddleElidedLabel(QLabel):
    """Monospace path label eliding long Unicode paths cleanly in the middle."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_text = nfc(text)
        self.setMinimumWidth(80)

    def full_text(self) -> str:
        return self._full_text

    def set_full_text(self, text: str) -> None:
        self._full_text = nfc(text)
        self._apply_elide()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_elide()

    def _apply_elide(self) -> None:
        avail = max(40, self.width() - 2)
        elided = self.fontMetrics().elidedText(self._full_text, Qt.TextElideMode.ElideMiddle, avail)
        super().setText(elided)


class PathSelector(QFrame):
    """Flat recessed Unicode path strip with Dò tìm / Chọn... and right-click menu."""

    detect_requested = Signal()
    browse_requested = Signal()
    path_copied = Signal(str)
    open_folder_requested = Signal(str)

    def __init__(
        self,
        initial_path: str | Path | None = None,
        *,
        caption: str = "Thư mục game",
        placeholder: str = "Chưa chọn thư mục game",
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer or get_asset_renderer()
        self._placeholder = nfc(placeholder)
        self._raw_path: str = ""

        self.setObjectName("pathSelector")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 7, 10, 7)
        outer.setSpacing(8)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)

        self.caption_label = QLabel(nfc(caption), self)
        self.caption_label.setFont(ui_font(FS_MICRO, 500))
        self.caption_label.setStyleSheet(f"color: {OV_TOKENS.TEXT_MUTED}; background: transparent;")
        text_col.addWidget(self.caption_label)

        self.path_label = _MiddleElidedLabel(self._placeholder, self)
        self.path_label.setFont(mono_font(FS_BODY_SM, 500))
        self.path_label.setStyleSheet(f"color: {OV_TOKENS.TEXT_PRIMARY}; background: transparent;")
        text_col.addWidget(self.path_label)
        outer.addLayout(text_col, 1)

        btn_group = QHBoxLayout()
        btn_group.setContentsMargins(0, 0, 0, 0)
        btn_group.setSpacing(0)

        self.detect_button = QPushButton(nfc("Dò tìm"), self)
        self.detect_button.setObjectName("pathFlatBtn")
        self.detect_button.setFont(ui_font(FS_META, 600))
        self.detect_button.setFixedHeight(26)
        self.detect_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.detect_button.setFlat(True)
        self.detect_button.setStyleSheet(
            "QPushButton#pathFlatBtn { border: none; border-radius: 3px; background: transparent; "
            "color: #E2E8F0; padding: 0 9px; }"
            "QPushButton#pathFlatBtn:hover { background: rgba(255, 255, 255, 0.10); color: #FFFFFF; }"
            "QPushButton#pathFlatBtn:disabled { color: #64748B; }"
        )
        self.detect_button.clicked.connect(self.detect_requested.emit)
        btn_group.addWidget(self.detect_button)

        divider = QFrame(self)
        divider.setFixedSize(1, 18)
        divider.setStyleSheet("background: rgba(255, 255, 255, 0.16); border: none;")
        btn_group.addWidget(divider)

        self.browse_button = QPushButton(nfc("Chọn..."), self)
        self.browse_button.setObjectName("pathFlatBtnRight")
        self.browse_button.setFont(ui_font(FS_META, 600))
        self.browse_button.setFixedHeight(26)
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_button.setFlat(True)
        self.browse_button.setStyleSheet(
            "QPushButton#pathFlatBtnRight { border: none; border-top-right-radius: 3px; "
            "border-bottom-right-radius: 3px; background: transparent; color: #E2E8F0; padding: 0 9px; }"
            "QPushButton#pathFlatBtnRight:hover { background: rgba(255, 255, 255, 0.10); color: #FFFFFF; }"
            "QPushButton#pathFlatBtnRight:disabled { color: #64748B; }"
        )
        self.browse_button.clicked.connect(self.browse_requested.emit)
        btn_group.addWidget(self.browse_button)

        outer.addLayout(btn_group, 0)

        self._refresh_icons()
        self.set_path(initial_path)

    def _refresh_icons(self) -> None:
        dpr = max(1.0, float(self.devicePixelRatioF()))
        self.detect_button.setIcon(self._renderer.get_icon("game/zs_common_search.png", (14, 14), dpr))
        self.detect_button.setIconSize(QSize(14, 14))
        self.browse_button.setIcon(self._renderer.get_icon("game/asar_path.svg", (14, 14), dpr))
        self.browse_button.setIconSize(QSize(14, 14))

    def set_path(self, path: str | Path | None) -> None:
        txt = nfc(str(path).strip()) if path else ""
        self._raw_path = txt
        if txt:
            self.path_label.set_full_text(txt)
            self.path_label.setToolTip(txt)
            self.setToolTip(txt)
        else:
            self.path_label.set_full_text(self._placeholder)
            self.path_label.setToolTip("")
            self.setToolTip("")

    def path(self) -> str:
        return self._raw_path

    def set_controls_enabled(self, enabled: bool) -> None:
        self.detect_button.setEnabled(bool(enabled))
        self.browse_button.setEnabled(bool(enabled))

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        menu.setObjectName("porcelainMenu")

        open_act = QAction(nfc("Mở thư mục trong Explorer"), menu)
        copy_act = QAction(nfc("Sao chép đầy đủ đường dẫn"), menu)

        has_path = bool(self._raw_path)
        open_act.setEnabled(has_path and Path(self._raw_path).exists())
        copy_act.setEnabled(has_path)

        open_act.triggered.connect(self._on_open_folder)
        copy_act.triggered.connect(self._on_copy_path)

        menu.addAction(open_act)
        menu.addAction(copy_act)
        menu.exec(self.mapToGlobal(pos))

    def _on_open_folder(self) -> None:
        if not self._raw_path:
            return
        self.open_folder_requested.emit(self._raw_path)
        target = Path(self._raw_path)
        if target.exists() and hasattr(os, "startfile"):
            try:
                os.startfile(str(target))
            except OSError:
                pass

    def _on_copy_path(self) -> None:
        if not self._raw_path:
            return
        cb = QGuiApplication.clipboard()
        if cb is not None:
            cb.setText(self._raw_path)
        self.path_copied.emit(self._raw_path)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, float(OV_TOKENS.CONTROL_RADIUS), float(OV_TOKENS.CONTROL_RADIUS))
        painter.fillPath(path, rgba_qcolor(OV_TOKENS.RECESSED_PATH_RGBA))
        painter.save()
        painter.setClipPath(path)
        painter.fillRect(
            QRectF(rect.left(), rect.bottom() - 1.0, rect.width(), 1.0),
            rgba_qcolor(OV_TOKENS.PATH_BORDER_RGBA),
        )
        painter.restore()
        painter.end()
