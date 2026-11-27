# -*- coding: utf-8 -*-
"""
UpdateGuardDialog — Authentic Stella Sora game-asset mandatory update guard modal.

Designed with authentic curated Stella Sora UI sprites:
- Navy gradient header with mirrored `game/zs_common_pop_01.png` halftone & 5px Coral bar
- `game/zs_sf_popup_head_1.png` (Tyrant chibi popup) + `game/zs_stage_warning_icon.png` hero badge
- `game/Common_Line_03.png` luminous game divider
- `game/btn_common_db_l_3.png` 9-slice Coral CTA (`faceted_coral`) + `game/btn_icon_back.png`
- `game/btn_common_stop.png` secondary abort button (HARD-BLOCK: zero bypass option)
"""
from __future__ import annotations

import os
import sys
from typing import Any, Optional

from PySide6.QtCore import QEvent, QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPixmap, QTransform
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.game_guard import GameUpdateSignal
from ..theme.tokens import PORCELAIN_TOKENS
from ..theme.typography import FS_BODY, FS_BODY_SM, FS_CAPTION, FS_MODAL_HERO, nfc, ui_font
from ..widgets import (
    AccentBannerStrip,
    ActionButton,
    AssetRenderer,
    HairlineKeyValueTable,
    PorcelainDialog,
    PorcelainSectionBar,
    get_asset_renderer,
)


class _GuardBodyScrollArea(QScrollArea):
    """Content-hugging scroll area matching ConfirmationDialog so the alert opens at full height."""

    def sizeHint(self) -> QSize:  # noqa: N802
        base = super().sizeHint()
        inner = self.widget()
        if inner is not None:
            win = self.window()
            win_w = (win.width() - 4) if win is not None else 0
            vp_w = self.viewport().width() if self.isVisible() else 0
            target_w = max(320, win_w if (win is not None and win_w > 0) else vp_w)
            h = inner.heightForWidth(target_w) if inner.hasHeightForWidth() else inner.sizeHint().height()
            if h <= 0:
                h = inner.sizeHint().height()
            return QSize(base.width(), max(220, h))
        return base

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        base = super().minimumSizeHint()
        return QSize(min(300, base.width()), 120)


class _LuminousGameDivider(QWidget):
    """Crisp horizontal divider painted with authentic `game/Common_Line_03.png`."""

    def __init__(self, asset_renderer: AssetRenderer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self.setFixedHeight(10)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        rect = QRectF(self.rect())
        painter.fillRect(rect, QColor(PORCELAIN_TOKENS.WHITE))
        pix = self._renderer.get_master_pixmap("game/Common_Line_03.png")
        if not pix.isNull():
            painter.save()
            painter.setOpacity(0.88)
            painter.drawPixmap(
                QRectF(rect.left() + 12.0, rect.top() + 1.0, max(1.0, rect.width() - 24.0), rect.height() - 2.0),
                pix,
                QRectF(pix.rect()),
            )
            painter.restore()
        else:
            painter.fillRect(QRectF(rect.left(), rect.center().y(), rect.width(), 1.0), QColor(PORCELAIN_TOKENS.HAIRLINE))
        painter.end()


class _GameEmblemComposite(QWidget):
    """Renders `game/zs_sf_popup_head_1.png` with `game/zs_stage_warning_icon.png` alert badge."""

    def __init__(self, asset_renderer: AssetRenderer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self.setFixedSize(96, 96)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        dpr = max(1.0, float(self.devicePixelRatioF()))
        head = self._renderer.get_icon_pixmap("game/zs_sf_popup_head_1.png", (84, 84), dpr)
        if not head.isNull():
            painter.drawPixmap(QRectF(2.0, 4.0, 84.0, 84.0), head, QRectF(head.rect()))

        warn = self._renderer.get_icon_pixmap("game/zs_stage_warning_icon.png", (38, 36), dpr)
        if not warn.isNull():
            painter.drawPixmap(QRectF(56.0, 56.0, 38.0, 36.0), warn, QRectF(warn.rect()))

        star = self._renderer.get_icon_pixmap("game/zs_common_star_l_1.png", (16, 16), dpr)
        if not star.isNull():
            painter.drawPixmap(QRectF(0.0, 2.0, 16.0, 16.0), star, QRectF(star.rect()))
        painter.end()


class _GameAlertHeroBand(QWidget):
    """Porcelain-rose hero header with mirrored `game/zs_common_pop_01.png` halftone."""

    def __init__(
        self,
        headline: str,
        lead_text: str,
        asset_renderer: AssetRenderer,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 12)
        lay.setSpacing(14)

        self.emblem = _GameEmblemComposite(self._renderer, self)
        lay.addWidget(self.emblem, 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 2, 0, 0)
        text_col.setSpacing(6)

        self.headline_label = QLabel(nfc(headline), self)
        self.headline_label.setFont(ui_font(FS_MODAL_HERO, 700))
        self.headline_label.setWordWrap(True)
        self.headline_label.setStyleSheet(f"color: {PORCELAIN_TOKENS.DANGER_TEXT}; background: transparent;")
        text_col.addWidget(self.headline_label)

        self.lead_label = QLabel(nfc(lead_text), self)
        self.lead_label.setFont(ui_font(FS_BODY, 400))
        self.lead_label.setWordWrap(True)
        self.lead_label.setStyleSheet(f"color: {PORCELAIN_TOKENS.SLATE_BODY}; background: transparent;")
        text_col.addWidget(self.lead_label)
        text_col.addStretch(1)

        lay.addLayout(text_col, 1)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        rect = QRectF(self.rect())

        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, QColor("#FFF5F7"))
        grad.setColorAt(0.62, QColor("#FFFFFF"))
        grad.setColorAt(1.0, QColor("#EEF4FA"))
        painter.fillRect(rect, QBrush(grad))

        halftone = self._renderer.get_master_pixmap("game/zs_common_pop_01.png")
        if not halftone.isNull() and halftone.height() > 0:
            scale = rect.height() / float(halftone.height())
            draw_w = float(halftone.width()) * scale
            painter.save()
            painter.setOpacity(0.07)
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
        painter.end()


class UpdateGuardDialog(PorcelainDialog):
    """Mandatory Stella Sora update-protection alert (ZERO bypass option).

    Accept (`QDialog.DialogCode.Accepted`) means the user agrees to restore official
    Yostar files before updating. Reject means abort / do not launch game.
    """

    def __init__(
        self,
        *,
        notice: Optional[dict[str, Any]] = None,
        signal: Optional[GameUpdateSignal] = None,
        game_running: bool = False,
        launch_after_restore: bool = True,
        always_on_top: bool = False,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        self._renderer = asset_renderer or get_asset_renderer()
        self._always_on_top = bool(always_on_top)
        self._beeped = False
        self.game_running = bool(game_running)
        self.launch_after_restore = bool(launch_after_restore)

        title = "CẢNH BÁO CẬP NHẬT STELLA SORA"
        meta = (
            "Phát hiện hộp thoại tải bản vá ngay trong game"
            if signal is not None
            else "Máy chủ Yostar đã phát hành bản cập nhật mới"
        )

        super().__init__(
            title=title,
            meta=meta,
            icon_path="game/zs_stage_warning_icon_s.png",
            icon_size=(22, 22),
            variant="error",
            status_tag="Bắt buộc khôi phục gốc",
            target_width=600,
            asset_renderer=self._renderer,
            parent=parent,
        )
        self.setObjectName("updateGuardDialog")
        if self._always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        p = PORCELAIN_TOKENS
        self.scroll_area = _GuardBodyScrollArea(self.frame)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setStyleSheet(f"background: {p.WHITE}; border: none;")

        body = QWidget(self.scroll_area)
        body.setStyleSheet(f"background: {p.WHITE};")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        headline = (
            "DỪNG LẠI — KHÔNG bấm tải bản vá trong game!"
            if self.game_running
            else "Game có bản cập nhật mới — Bắt buộc khôi phục gốc trước!"
        )
        lead = (
            "Bản Việt hóa đã thay đổi tệp ngôn ngữ của Stella Sora nên trình cập nhật của Yostar "
            "sẽ báo lỗi xác minh (BinDiffPatchError) nếu bạn cập nhật ngay lúc này.\n"
            "Hãy để Launcher tự động tải lại dữ liệu gốc sạch từ máy chủ Yostar rồi mới cho game cập nhật."
        )
        self.hero_band = _GameAlertHeroBand(headline, lead, self._renderer, body)
        body_lay.addWidget(self.hero_band)

        self.luminous_divider = _LuminousGameDivider(self._renderer, body)
        body_lay.addWidget(self.luminous_divider)

        # Structured detection evidence table
        body_lay.addWidget(PorcelainSectionBar("Chi tiết phát hiện cập nhật", body))
        info_wrap = QWidget(body)
        info_wrap.setStyleSheet(f"background: {p.PORCELAIN_BG}; border-bottom: 1px solid {p.HAIRLINE};")
        iw_lay = QVBoxLayout(info_wrap)
        iw_lay.setContentsMargins(16, 10, 16, 10)
        iw_lay.setSpacing(0)

        rows = self._build_evidence_rows(notice=notice, signal=signal, game_running=self.game_running)
        self.evidence_table = HairlineKeyValueTable(info_wrap)
        self.evidence_table.set_kv_rows(rows, key_width_pct=0.33)
        iw_lay.addWidget(self.evidence_table)
        body_lay.addWidget(info_wrap)

        # Mandatory safety warning strip
        self.warning_strip = AccentBannerStrip(
            "Quy trình an toàn 2 bước",
            "1. Bấm nút đỏ bên dưới để khôi phục dữ liệu gốc của Yostar (giữ nguyên dữ liệu tài khoản).\n"
            "2. Vào game để tải bản vá chính thức hoàn tất, sau đó quay lại Launcher để cài lại bản Việt hóa.",
            tone="error",
            icon_path="game/zs_stage_warning_icon_s.png",
            asset_renderer=self._renderer,
            parent=body,
        )
        self.warning_strip.body_label.setFont(ui_font(FS_BODY_SM, 500))
        body_lay.addWidget(self.warning_strip)

        self.scroll_area.setWidget(body)
        self.set_body(self.scroll_area)

        # Footer — Hard-block: ONLY Restore (faceted_coral) or Abort/Close (ZERO bypass!)
        footer = QWidget(self.frame)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(0, 0, 0, 0)
        f_lay.setSpacing(10)

        hint_lbl = QLabel(nfc("Đã khóa vào game để tránh hỏng tệp"), footer)
        hint_lbl.setFont(ui_font(FS_CAPTION, 600))
        hint_lbl.setStyleSheet(f"color: {p.DANGER_TEXT}; background: transparent;")
        f_lay.addWidget(hint_lbl, 1, Qt.AlignmentFlag.AlignVCenter)

        abort_label = "Đóng (Không cập nhật)" if self.game_running else "Hủy (Không mở game)"
        self.btn_abort = ActionButton(
            abort_label,
            variant="light_secondary",
            icon_path="game/btn_common_stop.png",
            icon_size=(14, 14),
            icon_tint=p.NAVY_TEXT,
            height=40,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_abort.clicked.connect(self.reject)
        f_lay.addWidget(self.btn_abort)

        if self.game_running:
            restore_label = "Đóng game & Khôi phục gốc ngay"
        elif self.launch_after_restore:
            restore_label = "Khôi phục gốc & Mở game"
        else:
            restore_label = "Khôi phục dữ liệu gốc ngay"

        self.btn_restore = ActionButton(
            restore_label,
            variant="faceted_coral",
            icon_path="game/btn_icon_back.png",
            icon_size=(15, 15),
            icon_tint="#FFFFFF",
            height=42,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_restore.setDefault(True)
        self.btn_restore.clicked.connect(self.accept)
        f_lay.addWidget(self.btn_restore)

        self.set_footer(footer)
        self._sync_scroll_geometry()
        self.adjustSize()

    def _sync_scroll_geometry(self) -> None:
        inner = self.scroll_area.widget()
        if inner is not None and inner.layout() is not None:
            inner.layout().invalidate()
            inner.layout().activate()
            inner.updateGeometry()
        self.scroll_area.updateGeometry()
        self.frame.body_container.updateGeometry()
        self.frame.updateGeometry()
        self.updateGeometry()
        if self.frame.layout() is not None:
            self.frame.layout().activate()
        if self.layout() is not None:
            self.layout().activate()

    @staticmethod
    def _build_evidence_rows(
        *,
        notice: Optional[dict[str, Any]],
        signal: Optional[GameUpdateSignal],
        game_running: bool,
    ) -> list[tuple[str, str, str]]:
        rows: list[tuple[str, str, str]] = []
        n = notice or {}

        if signal is not None:
            rows.append(("Nguồn phát hiện", "Nhật ký Stella Sora trực tiếp (Player.log)", "warn"))
        elif n.get("source") == "player_log":
            rows.append(("Nguồn phát hiện", "Nhật ký lỗi bản vá Stella Sora (Player.log)", "warn"))
        else:
            rows.append(("Nguồn phát hiện", "Máy chủ tài nguyên chính thức Yostar", "info"))

        local_game = str((signal.local_game_version if signal else "") or n.get("local_game_version") or "")
        local_res = str((signal.local_resource_version if signal else "") or n.get("local_resource_version") or "")
        if local_game or local_res:
            parts = []
            if local_game and local_game != "unknown":
                parts.append(f"v{local_game}")
            if local_res and local_res != "unknown":
                parts.append(f"RES {local_res}")
            if parts:
                rows.append(("Bản đang cài trên máy", " · ".join(parts), "mono"))

        latest_game = str((signal.latest_game_version if signal else "") or n.get("latest_game_version") or "")
        latest_res = str((signal.latest_resource_version if signal else "") or n.get("latest_resource_version") or "")
        patch_tr = signal.patch_transition if signal else ""
        dl_size = signal.download_size if signal else ""

        new_parts = []
        if latest_game and latest_game != "unknown":
            new_parts.append(f"v{latest_game}")
        if latest_res and latest_res != "unknown":
            new_parts.append(f"RES {latest_res}")
        if patch_tr:
            new_parts.append(patch_tr)
        if dl_size:
            new_parts.append(dl_size)
        if new_parts:
            rows.append(("Bản cập nhật mới", " · ".join(new_parts), "danger"))

        if game_running:
            rows.append(("Trạng thái StellaSora.exe", "Đang chạy — sẽ tự đóng an toàn trước khi khôi phục", "danger"))
        else:
            rows.append(("Trạng thái StellaSora.exe", "Đã đóng — sẵn sàng khôi phục dữ liệu gốc", "ok"))

        detail = (signal.detail if signal else "") or str(n.get("detail") or "")
        if detail:
            rows.append(("Ghi nhận chi tiết", detail, "neutral"))
        return rows

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if self._always_on_top:
            self.raise_()
            self.activateWindow()
            if not self._beeped and sys.platform == "win32" and os.environ.get("QT_QPA_PLATFORM", "").lower() != "offscreen":
                self._beeped = True
                try:
                    import ctypes

                    ctypes.windll.user32.MessageBeep(0x30)  # MB_ICONEXCLAMATION
                except Exception:  # noqa: BLE001
                    pass

    def compact_layout(self, available_width: int, available_height: int | None = None) -> None:
        clamped_w = max(360, min(self._target_width, int(available_width) - 32))
        self.setFixedWidth(clamped_w)
        if available_height is not None:
            max_h = max(280, int(available_height) - 32)
            self.setMaximumHeight(max_h)
            self._sync_scroll_geometry()
            self.adjustSize()
            if self.height() > max_h:
                self.resize(self.width(), max_h)
        else:
            self.setMaximumHeight(16777215)
            self._sync_scroll_geometry()
            self.adjustSize()

    def refresh_dpr(self) -> None:
        self.frame.refresh_dpr()
        self.hero_band.emblem.update()
        self.luminous_divider.update()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()
