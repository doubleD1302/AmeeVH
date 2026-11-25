# -*- coding: utf-8 -*-
"""
Unified Stella Sora ActionButton with 8 variants, 9-slice faceted Unity sprites,
fontMetrics()-driven sizeHint (never clipping Vietnamese text), and reduced_motion support.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Property, QEasingCurve, QRectF, QSize, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QPushButton, QSizePolicy, QWidget

from ..theme.tokens import OV_TOKENS, PORCELAIN_TOKENS, rgba_qcolor
from ..theme.typography import FS_BODY, FS_BODY_SM, FS_CTA, FS_CTA_SM, FS_META, nfc, ui_font
from .asset_renderer import (
    FACETED_BTN_DST_INSETS,
    FACETED_BTN_SRC_INSETS,
    AssetRenderer,
    get_asset_renderer,
)

VALID_BUTTON_VARIANTS = (
    "faceted_cyan",
    "faceted_ice",
    "faceted_coral",
    "light_cyan",
    "light_secondary",
    "navy_solid",
    "header_white",
    "flat_toolbar",
)


class ActionButton(QPushButton):
    """Unified button supporting 9-slice faceted CTAs and Light Porcelain actions."""

    def __init__(
        self,
        text: str = "",
        *,
        variant: str = "light_secondary",
        icon_path: str | None = None,
        icon_size: tuple[int, int] = (15, 15),
        icon_tint: QColor | str | None = None,
        height: int | None = None,
        right_divider: bool = False,
        left_aligned: bool = False,
        reduced_motion: bool = False,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(nfc(text), parent)
        self._variant = variant if variant in VALID_BUTTON_VARIANTS else "light_secondary"
        self._icon_path = icon_path
        self._icon_size = (int(icon_size[0]), int(icon_size[1]))
        self._icon_tint = icon_tint
        self._right_divider = bool(right_divider)
        self._left_aligned = bool(left_aligned)
        self._reduced_motion = bool(reduced_motion)
        self._renderer = asset_renderer or get_asset_renderer()
        self._hovered = False
        self._pressed = False
        self._hover_progress = 0.0

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(0 if self._reduced_motion else 120)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim_value)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._apply_variant_typography(height_override=height)

    def _on_anim_value(self, value) -> None:
        self._hover_progress = float(value)
        self.update()

    def _apply_variant_typography(self, *, height_override: int | None = None) -> None:
        v = self._variant
        if v == "faceted_cyan":
            self.setFont(ui_font(FS_CTA, 700))
            default_h = 46
        elif v in ("faceted_ice", "faceted_coral"):
            self.setFont(ui_font(FS_CTA_SM, 700))
            default_h = 46
        elif v == "light_cyan":
            self.setFont(ui_font(FS_BODY_SM, 700))
            default_h = 32
        elif v == "light_secondary":
            self.setFont(ui_font(FS_BODY_SM, 600))
            default_h = 32
        elif v == "navy_solid":
            self.setFont(ui_font(FS_BODY_SM, 600))
            default_h = 35
        elif v == "header_white":
            self.setFont(ui_font(FS_BODY_SM, 600))
            default_h = 30
        else:  # flat_toolbar
            self.setFont(ui_font(FS_BODY_SM, 600))
            default_h = 36
        self.setFixedHeight(int(height_override if height_override is not None else default_h))

    def setText(self, text: str) -> None:  # noqa: N802
        super().setText(nfc(text))
        self.updateGeometry()
        self.update()

    def set_variant(self, variant: str, *, height: int | None = None) -> None:
        if variant in VALID_BUTTON_VARIANTS:
            self._variant = variant
            self._apply_variant_typography(height_override=height)
            self.updateGeometry()
            self.update()

    def set_icon(
        self,
        icon_path: str | None,
        *,
        icon_size: tuple[int, int] | None = None,
        icon_tint: QColor | str | None = None,
    ) -> None:
        self._icon_path = icon_path
        if icon_size is not None:
            self._icon_size = (int(icon_size[0]), int(icon_size[1]))
        if icon_tint is not None or icon_path is None:
            self._icon_tint = icon_tint
        self.updateGeometry()
        self.update()

    def set_reduced_motion(self, enabled: bool) -> None:
        self._reduced_motion = bool(enabled)
        self._anim.setDuration(0 if self._reduced_motion else 120)

    def _hover_to(self, target: float) -> None:
        if self._reduced_motion:
            self._anim.stop()
            self._hover_progress = target
            self.update()
            return
        self._anim.stop()
        self._anim.setStartValue(self._hover_progress)
        self._anim.setEndValue(target)
        self._anim.start()

    def enterEvent(self, event) -> None:  # noqa: N802
        self._hovered = True
        self._hover_to(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hovered = False
        self._pressed = False
        self._hover_to(0.0)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def _horizontal_padding(self) -> int:
        if self._variant.startswith("faceted_"):
            return 16
        if self._variant == "flat_toolbar":
            return 10
        return 14

    def _icon_gap(self) -> int:
        return 7 if (self._icon_path and self.text()) else 0

    def sizeHint(self) -> QSize:  # noqa: N802
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self.text()) if self.text() else 0
        icon_w = self._icon_size[0] if self._icon_path else 0
        pad = self._horizontal_padding() * 2
        w = max(self.minimumWidth(), text_w + icon_w + self._icon_gap() + pad + 4)
        h = max(self.minimumHeight(), self.height() if self.height() > 0 else 32)
        return QSize(w, h)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return self.sizeHint()

    def _resolve_colors(self) -> tuple[QColor, QColor, QColor, QColor]:
        """Return (bg, border, bottom_border, text_color) for non-9-slice variants."""
        p = PORCELAIN_TOKENS
        v = self._variant
        if v == "light_cyan":
            bg = QColor("#30DCE2") if self._hovered else QColor(p.CYAN_CTA)
            return bg, QColor(p.CYAN_CTA_BORDER), QColor(p.CYAN_CTA_BOTTOM), QColor(OV_TOKENS.CTA_CYAN_TEXT)
        if v == "light_secondary":
            bg = QColor(p.ICE_ZEBRA) if self._hovered else QColor(p.WHITE)
            return bg, QColor(p.HAIRLINE_INPUT), QColor(p.BTN_SEC_BOTTOM), QColor(p.NAVY_TEXT)
        if v == "navy_solid":
            bg = QColor(p.NAVY_HOVER) if self._hovered else QColor(p.NAVY_SOLID)
            return bg, QColor(p.NAVY_BORDER), QColor(p.NAVY_BOTTOM_EDGE), QColor("#FFFFFF")
        if v == "header_white":
            alpha = 255 if self._hovered else 240
            return (
                QColor(255, 255, 255, alpha),
                QColor(255, 255, 255, 140),
                QColor(255, 255, 255, 140),
                QColor(p.NAVY_TEXT),
            )
        # flat_toolbar
        bg = rgba_qcolor(OV_TOKENS.TOOLBAR_HOVER_RGBA) if self._hovered else QColor(0, 0, 0, 0)
        return bg, QColor(0, 0, 0, 0), QColor(0, 0, 0, 0), QColor(OV_TOKENS.TEXT_NOTICE_ROW)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        if not self.isEnabled():
            painter.setOpacity(0.50)

        rect = QRectF(self.rect())
        v = self._variant

        if v.startswith("faceted_"):
            sprite_map = {
                "faceted_cyan": "game/btn_common_db_l_1.png",
                "faceted_ice": "game/btn_common_db_l_2.png",
                "faceted_coral": "game/btn_common_db_l_3.png",
            }
            text_map = {
                "faceted_cyan": QColor(OV_TOKENS.CTA_CYAN_TEXT),
                "faceted_ice": QColor(OV_TOKENS.CTA_ICE_TEXT),
                "faceted_coral": QColor("#FFFFFF"),
            }
            pix = self._renderer.get_master_pixmap(sprite_map[v])
            if not pix.isNull():
                self._renderer.draw_nine_slice(
                    painter,
                    rect,
                    pix,
                    FACETED_BTN_SRC_INSETS,
                    FACETED_BTN_DST_INSETS,
                    from_unity_border=False,
                )
                if self._hover_progress > 0.0 and self.isEnabled():
                    painter.save()
                    painter.setOpacity(0.08 * self._hover_progress)
                    painter.fillRect(rect.adjusted(2, 2, -2, -2), QColor("#FFFFFF"))
                    painter.restore()
            else:
                bg = QColor(PORCELAIN_TOKENS.CYAN_CTA if v == "faceted_cyan" else PORCELAIN_TOKENS.WHITE)
                painter.fillRect(rect, bg)
            text_color = text_map[v]
        elif v == "flat_toolbar":
            bg, _, _, text_color = self._resolve_colors()
            if bg.alpha() > 0:
                painter.fillRect(rect, bg)
            if self._right_divider:
                painter.fillRect(
                    QRectF(rect.right() - 1.0, rect.top(), 1.0, rect.height()),
                    rgba_qcolor(OV_TOKENS.TOOLBAR_DIVIDER_RGBA),
                )
        else:
            bg, border, bottom_border, text_color = self._resolve_colors()
            draw_rect = rect.adjusted(0.5, 0.5, -0.5, -0.5)
            path = QPainterPath()
            path.addRoundedRect(draw_rect, float(PORCELAIN_TOKENS.CONTROL_RADIUS), float(PORCELAIN_TOKENS.CONTROL_RADIUS))
            painter.fillPath(path, bg)

            # Crisp 2px bottom bevel edge clipped inside rounded rect
            painter.save()
            painter.setClipPath(path)
            painter.fillRect(
                QRectF(draw_rect.left(), draw_rect.bottom() - 2.0, draw_rect.width(), 2.0),
                bottom_border,
            )
            painter.restore()

            pen = QPen(border, 1.0)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        # Draw icon + text centered (or left-aligned for quick-fix grid buttons)
        dpr = max(1.0, float(self.devicePixelRatioF()))
        icon_pix = None
        if self._icon_path:
            icon_pix = self._renderer.get_icon_pixmap(
                self._icon_path, self._icon_size, dpr, tint=self._icon_tint
            )

        text = self.text()
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(text) if text else 0
        iw = float(self._icon_size[0]) if (icon_pix is not None and not icon_pix.isNull()) else 0.0
        ih = float(self._icon_size[1]) if iw > 0.0 else 0.0
        gap = float(self._icon_gap()) if (iw > 0.0 and text) else 0.0
        total_w = iw + gap + float(text_w)

        y_offset = 1.0 if self._pressed else 0.0
        if self._left_aligned:
            start_x = rect.left() + float(self._horizontal_padding())
        else:
            start_x = rect.left() + max(4.0, (rect.width() - total_w) * 0.5)

        if iw > 0.0 and icon_pix is not None:
            iy = rect.top() + (rect.height() - ih) * 0.5 + y_offset
            painter.drawPixmap(QRectF(start_x, iy, iw, ih), icon_pix, QRectF(icon_pix.rect()))
            start_x += iw + gap

        if text:
            painter.setFont(self.font())
            painter.setPen(text_color)
            avail_w = max(0.0, rect.right() - start_x - 6.0)
            elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, round(avail_w))
            text_rect = QRectF(start_x, rect.top() + y_offset, avail_w, rect.height())
            painter.drawText(
                text_rect,
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                elided,
            )

        painter.end()
