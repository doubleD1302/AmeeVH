# -*- coding: utf-8 -*-
"""
Adaptive scrim & translucent surface calculator driven by core/bg_sync.LuminanceProfile.

Matches Preview r5 adaptive light/dark/bundled backdrop scrims and computes
top-left elliptical radial vignette for floating unboxed logo legibility.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QRadialGradient, QTransform

from ...core.bg_sync import BackgroundFrame, LuminanceProfile
from .tokens import OV_TOKENS, rgba_qcolor


@dataclass(frozen=True)
class AdaptiveScrimSpec:
    mode: Literal["light", "dark"]
    vertical_stops: tuple[tuple[float, QColor], ...]
    radial_logo_vignette: tuple[QPointF, float, float, QColor] | None
    chrome_fill: QColor
    nav_fill: QColor
    panel_fill: QColor
    dock_fill: QColor
    panel_border: QColor
    hero_zoom: float
    hero_focus: tuple[float, float]


def _alpha_byte(alpha: float) -> int:
    return max(0, min(255, round(float(alpha) * 255)))


def compute_scrim_spec(frame: BackgroundFrame | LuminanceProfile | None) -> AdaptiveScrimSpec:
    """Compute exact AdaptiveScrimSpec from a BackgroundFrame or LuminanceProfile."""
    if frame is None:
        lum = LuminanceProfile(y_all=0.55, y_top=0.60, y_bottom=0.52, mode="light")
        source_label = "bundled_master"
    elif isinstance(frame, LuminanceProfile):
        lum = frame
        source_label = "unknown"
    else:
        lum = frame.luminance
        source_label = getattr(frame, "source_label", "") or ""

    is_bundled = source_label == "bundled_master"
    is_light = lum.mode == "light" or lum.y_top >= 0.58

    top_alpha = float(lum.top_scrim_alpha if lum.top_scrim_alpha is not None else 0.45)
    bottom_alpha = float(lum.bottom_scrim_alpha if lum.bottom_scrim_alpha is not None else 0.58)

    if is_light:
        mode: Literal["light", "dark"] = "light"
        if is_bundled:
            radial_alpha = 0.36
            radial_rx, radial_ry = 0.56, 0.40
            v_top = max(0.66, top_alpha)
            v_mid1 = 0.24
            v_mid2 = 0.14
            v_bot = max(0.62, bottom_alpha * 0.90)
            stop2_pos, stop3_pos = 0.30, 0.62
        else:
            radial_alpha = 0.44
            radial_rx, radial_ry = 0.58, 0.42
            v_top = 0.72 if lum.y_top >= 0.68 else max(0.62, top_alpha)
            v_mid1 = 0.28
            v_mid2 = 0.10
            v_bot = max(0.68, bottom_alpha * 0.95)
            stop2_pos, stop3_pos = 0.24, 0.55

        radial = (
            QPointF(0.16, 0.18),
            radial_rx,
            radial_ry,
            QColor(10, 24, 52, _alpha_byte(radial_alpha)),
        )
        stops = (
            (0.0, QColor(6, 16, 34, _alpha_byte(v_top))),
            (stop2_pos, QColor(8, 20, 42, _alpha_byte(v_mid1))),
            (stop3_pos, QColor(8, 20, 42, _alpha_byte(v_mid2))),
            (1.0, QColor(6, 16, 34, _alpha_byte(v_bot))),
        )
        chrome_fill = rgba_qcolor(OV_TOKENS.CHROME_LIGHT)
        nav_fill = rgba_qcolor(OV_TOKENS.NAV_LIGHT)
        panel_fill = rgba_qcolor(OV_TOKENS.PANEL_LIGHT)
        dock_fill = rgba_qcolor(OV_TOKENS.DOCK_LIGHT)
    else:
        mode = "dark"
        if lum.y_top >= 0.45:
            radial = (
                QPointF(0.16, 0.18),
                0.54,
                0.38,
                QColor(10, 24, 52, _alpha_byte(0.24)),
            )
        else:
            radial = None

        v_top = max(0.26, min(0.56, top_alpha + 0.11 if top_alpha <= 0.45 else top_alpha))
        v_bot = max(0.42, min(0.64, bottom_alpha))
        stops = (
            (0.0, QColor(6, 14, 28, _alpha_byte(v_top))),
            (0.26, QColor(8, 18, 36, _alpha_byte(0.18))),
            (0.58, QColor(8, 18, 36, _alpha_byte(0.10))),
            (1.0, QColor(6, 14, 28, _alpha_byte(v_bot))),
        )
        chrome_fill = rgba_qcolor(OV_TOKENS.CHROME_DARK)
        nav_fill = rgba_qcolor(OV_TOKENS.NAV_DARK)
        panel_fill = rgba_qcolor(OV_TOKENS.PANEL_DARK)
        dock_fill = rgba_qcolor(OV_TOKENS.DOCK_DARK)

    hero_zoom = 1.0 if is_bundled else 1.07
    hero_focus = (0.5, 0.5) if is_bundled else (0.88, 0.92)

    return AdaptiveScrimSpec(
        mode=mode,
        vertical_stops=stops,
        radial_logo_vignette=radial,
        chrome_fill=chrome_fill,
        nav_fill=nav_fill,
        panel_fill=panel_fill,
        dock_fill=dock_fill,
        panel_border=rgba_qcolor(OV_TOKENS.PANEL_BORDER_RGBA),
        hero_zoom=hero_zoom,
        hero_focus=hero_focus,
    )


def paint_adaptive_scrim(painter: QPainter, rect: QRectF, spec: AdaptiveScrimSpec) -> None:
    """Paint vertical adaptive scrim and optional top-left elliptical logo vignette."""
    if rect.isEmpty():
        return

    painter.save()
    painter.setPen(QColor(0, 0, 0, 0))

    # 1. Vertical linear scrim
    linear = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    for pos, color in spec.vertical_stops:
        linear.setColorAt(max(0.0, min(1.0, float(pos))), color)
    painter.fillRect(rect, QBrush(linear))

    # 2. Optional elliptical radial vignette behind floating hero logo
    if spec.radial_logo_vignette is not None:
        center_norm, rx_norm, ry_norm, peak_color = spec.radial_logo_vignette
        cx = rect.left() + center_norm.x() * rect.width()
        cy = rect.top() + center_norm.y() * rect.height()
        rx = max(1.0, rx_norm * rect.width())
        ry = max(1.0, ry_norm * rect.height())

        radial = QRadialGradient(QPointF(0.0, 0.0), 1.0)
        radial.setColorAt(0.0, peak_color)
        radial.setColorAt(1.0, QColor(peak_color.red(), peak_color.green(), peak_color.blue(), 0))

        brush = QBrush(radial)
        transform = QTransform()
        transform.translate(cx, cy)
        transform.scale(rx, ry)
        brush.setTransform(transform)
        painter.fillRect(rect, brush)

    painter.restore()
