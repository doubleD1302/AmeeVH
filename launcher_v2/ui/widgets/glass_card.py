# -*- coding: utf-8 -*-
"""
Translucent Overview dark-navy GlassCard and Unity luminous divider.

Paints dynamic AdaptiveScrimSpec fills, 6px rounded surface, 1px subtle border,
and crisp 2px #25C8CE top accent edge without nested per-row rounded borders.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget

from ..theme.adaptive_scrim import AdaptiveScrimSpec
from ..theme.tokens import OV_TOKENS, rgba_qcolor
from .asset_renderer import AssetRenderer, get_asset_renderer


class LuminousDivider(QWidget):
    """Renders Stella Sora's Common_Line_03.png divider at height 6 DIP, opacity 0.45."""

    def __init__(
        self,
        *,
        rel_path: str = "game/Common_Line_03.png",
        opacity: float = 0.45,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._rel_path = rel_path
        self._opacity = float(opacity)
        self._renderer = asset_renderer or get_asset_renderer()
        self.setFixedHeight(6)

    def paintEvent(self, event) -> None:  # noqa: N802
        pix = self._renderer.get_master_pixmap(self._rel_path)
        if pix.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setOpacity(self._opacity)
        painter.drawPixmap(
            QRectF(self.rect()),
            pix,
            QRectF(0.0, 0.0, float(pix.width()), float(pix.height())),
        )
        painter.end()


class GlassCard(QFrame):
    """Overview translucent HUD panel or Action Control Dock with 2px #25C8CE top accent."""

    def __init__(
        self,
        *,
        variant: str = "panel",
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._variant = variant if variant in ("panel", "dock") else "panel"
        self._renderer = asset_renderer or get_asset_renderer()
        self._fill = rgba_qcolor(
            OV_TOKENS.DOCK_LIGHT if self._variant == "dock" else OV_TOKENS.PANEL_LIGHT
        )
        self._border = rgba_qcolor(OV_TOKENS.PANEL_BORDER_RGBA)

        self.setObjectName("glassCardDock" if self._variant == "dock" else "glassCardPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        self._layout = QVBoxLayout(self)
        if self._variant == "dock":
            self._layout.setContentsMargins(18, 16, 18, 10)
            self._layout.setSpacing(11)
        else:
            self._layout.setContentsMargins(15, 12, 15, 10)
            self._layout.setSpacing(7)

    def content_layout(self) -> QVBoxLayout:
        return self._layout

    def apply_scrim_spec(self, spec: AdaptiveScrimSpec) -> None:
        self._fill = spec.dock_fill if self._variant == "dock" else spec.panel_fill
        self._border = spec.panel_border
        self.update()

    def add_luminous_divider(
        self,
        *,
        rel_path: str = "game/Common_Line_03.png",
        opacity: float = 0.45,
    ) -> LuminousDivider:
        div = LuminousDivider(
            rel_path=rel_path,
            opacity=opacity,
            asset_renderer=self._renderer,
            parent=self,
        )
        div.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._layout.addWidget(div)
        return div

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        r = float(OV_TOKENS.PANEL_RADIUS)

        path = QPainterPath()
        path.addRoundedRect(rect, r, r)

        # Translucent navy fill + 1px border
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._fill)
        painter.drawPath(path)

        # 2px #25C8CE top accent clipped cleanly to the rounded card shape
        painter.save()
        painter.setClipPath(path)
        painter.fillRect(
            QRectF(rect.left(), rect.top(), rect.width(), float(OV_TOKENS.PANEL_TOP_BORDER)),
            QColor(OV_TOKENS.CYAN_ACCENT),
        )
        painter.restore()

        pen = QPen(self._border, 1.0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.end()
