# -*- coding: utf-8 -*-
"""
ShortcutWizardDialog — Authentic Stella Sora Game-Asset 4-Step Chibi Shortcut Onboarding & Launch Reminder (PC).

Mirrors Android's 4-step Chibi Shortcut Wizard so PC & Android share the exact same safe update-guard UX:
- Step 1: Recommend launching Stella Sora via the round `Chơi Stella VH` Desktop shortcut (0.2s Yostar check,
          zero background tray needed). If already present on Desktop -> Launch Safely / View Guide / Enter Launcher.
- Step 2: Check Desktop for `Chơi Stella VH.lnk`.
- Step 3: Mandatory guided 1-click creation + auto re-check on Desktop (with Chibi Tilia / Chaton + safe fallback).
- Step 4: Celebration & clear launch instructions with Chibi Noya + enlarged synced `shortcut_vh_icon.png`.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from PIL import Image, ImageFilter
from PySide6.QtCore import QEvent, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QImage,
    QLinearGradient,
    QPainter,
    QPixmap,
    QTransform,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..theme.tokens import PORCELAIN_TOKENS
from ..theme.typography import FS_BODY, FS_BODY_SM, FS_CAPTION, FS_META, FS_MODAL_HERO, nfc, ui_font
from ..widgets import (
    AccentBannerStrip,
    ActionButton,
    AssetRenderer,
    PorcelainDialog,
    get_asset_renderer,
)

_SW_LAUNCH_GUIDES: list[tuple[str, str, str, str]] = [
    (
        "111",
        "Iris",
        "Trợ lý Stella Sora",
        '"Chào Bạo Chúa! Desktop đã có lối tắt Chơi Stella VH rồi — nhớ mở game bằng biểu tượng tròn này để tự kiểm tra cập nhật an toàn nhé!"',
    ),
    (
        "112",
        "Noya",
        "Hướng dẫn viên",
        '"Chào mừng trở lại ♪ Nhớ nhấp đúp lối tắt Chơi Stella VH trên Desktop nhé — vừa tránh lỗi cập nhật vừa không cần chạy ngầm tốn RAM!"',
    ),
    (
        "103",
        "Amber",
        "Đội cận vệ",
        '"Trước khi vào game, nhớ dùng lối tắt Chơi Stella VH nha! Đừng mở trực tiếp biểu tượng gốc để tránh dính lỗi xác minh tệp!"',
    ),
    (
        "107",
        "Tilia",
        "Hiệp sĩ Chính Nghĩa",
        '"Với danh dự Hiệp sĩ, mở bằng Chơi Stella VH chỉ tốn 0,2 giây kiểm tra Yostar — an toàn và cực gọn nhẹ!"',
    ),
    (
        "123",
        "Ann",
        "Người đồng hành",
        '"Lối tắt Chơi Stella VH đang sẵn sàng rồi nè! Bấm nút xanh bên dưới để vào game an toàn ngay nha~"',
    ),
    (
        "134",
        "Fuyuka",
        "Đội hỗ trợ",
        '"Mở game bằng Chơi Stella VH giúp bản Việt Hoá luôn an toàn mỗi khi Yostar phát hành bản vá mới đó!"',
    ),
]

_LAUNCH_GUIDE_IDX: int = 0


def _load_lanczos_pixmap(
    renderer: AssetRenderer,
    rel_path: str,
    target_px: int,
    dpr: float,
    *,
    sharpen: bool = True,
) -> QPixmap:
    resolved = renderer.resolve_path(rel_path)
    if not resolved.is_file():
        return QPixmap()
    try:
        with Image.open(resolved) as src:
            im = src.convert("RGBA")
            im = im.resize((target_px, target_px), Image.Resampling.LANCZOS)
            if sharpen:
                im = im.filter(ImageFilter.UnsharpMask(radius=0.6, percent=40, threshold=3))
            raw = im.tobytes("raw", "RGBA")
            qimg = QImage(raw, target_px, target_px, target_px * 4, QImage.Format.Format_RGBA8888).copy()
        pix = QPixmap.fromImage(qimg)
        pix.setDevicePixelRatio(dpr)
        return pix
    except Exception:
        dip = max(16, round(target_px / max(1.0, dpr)))
        return renderer.get_icon_pixmap(rel_path, (dip, dip), dpr)


class _CrispImageBadge(QWidget):
    """Renders a crisp Lanczos-resampled RGBA icon (shortcut icon or Chibi) with zero clipping."""

    def __init__(
        self,
        rel_path: str,
        size_dip: int,
        asset_renderer: AssetRenderer,
        *,
        framed: bool = False,
        dimmed: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self._rel_path = rel_path
        self._size_dip = int(size_dip)
        self._framed = bool(framed)
        self._dimmed = bool(dimmed)
        self._cache: dict[tuple[str, int], QPixmap] = {}
        pad = 8 if framed else 0
        self.setFixedSize(self._size_dip + pad, self._size_dip + pad)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def set_image(self, rel_path: str) -> None:
        self._rel_path = rel_path
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = PORCELAIN_TOKENS
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        if self._framed:
            rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
            painter.setBrush(QColor("#FFFFFF"))
            painter.setPen(QColor(p.CYAN_ACCENT))
            painter.drawRoundedRect(rect, 16.0, 16.0)
            offset = 4.0
        else:
            offset = 0.0

        dpr = max(1.0, float(self.devicePixelRatioF()))
        target_px = max(32, round(self._size_dip * dpr))
        key = (self._rel_path, target_px)
        pix = self._cache.get(key)
        if pix is None or pix.isNull():
            pix = _load_lanczos_pixmap(self._renderer, self._rel_path, target_px, dpr)
            self._cache[key] = pix

        if not pix.isNull():
            if self._dimmed:
                painter.setOpacity(0.55)
            painter.drawPixmap(
                QRectF(offset, offset, float(self._size_dip), float(self._size_dip)),
                pix,
                QRectF(pix.rect()),
            )
        painter.end()


class _ChibiSpeechBand(QWidget):
    """Porcelain-cyan hero band with Stella Sora halftone, Chibi avatar, speaker badge & dialogue."""

    def __init__(self, asset_renderer: AssetRenderer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 13, 18, 12)
        lay.setSpacing(14)

        self.chibi = _CrispImageBadge(
            "chibis/chibi_111.webp", 88, self._renderer, framed=True, parent=self
        )
        lay.addWidget(self.chibi, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setContentsMargins(0, 2, 0, 0)
        col.setSpacing(5)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(8)

        self.name_pill = QLabel(nfc("Iris"), self)
        self.name_pill.setFont(ui_font(FS_CAPTION, 700))
        self.name_pill.setStyleSheet(
            f"background: {PORCELAIN_TOKENS.NAVY_SOLID}; color: #FFFFFF; "
            "border-radius: 9px; padding: 2px 10px;"
        )
        meta_row.addWidget(self.name_pill, 0)

        self.role_lbl = QLabel(nfc("Hướng dẫn viên Stella Sora"), self)
        self.role_lbl.setFont(ui_font(FS_CAPTION, 600))
        self.role_lbl.setStyleSheet(f"color: {PORCELAIN_TOKENS.CYAN_TEXT_DEEP}; background: transparent;")
        meta_row.addWidget(self.role_lbl, 1)
        col.addLayout(meta_row)

        self.step_heading = QLabel(nfc("Hãy dùng Lối tắt Chơi Stella VH"), self)
        self.step_heading.setFont(ui_font(FS_MODAL_HERO, 700))
        self.step_heading.setWordWrap(True)
        self.step_heading.setStyleSheet(f"color: {PORCELAIN_TOKENS.NAVY_TEXT}; background: transparent;")
        col.addWidget(self.step_heading)

        self.speech_lbl = QLabel("", self)
        self.speech_lbl.setFont(ui_font(FS_BODY_SM, 500))
        self.speech_lbl.setWordWrap(True)
        self.speech_lbl.setStyleSheet(f"color: {PORCELAIN_TOKENS.SLATE_BODY}; background: transparent;")
        col.addWidget(self.speech_lbl)

        lay.addLayout(col, 1)

    def set_dialogue(self, chibi_id: str, name: str, role: str, heading: str, speech: str) -> None:
        self.chibi.set_image(f"chibis/chibi_{chibi_id}.webp")
        self.name_pill.setText(nfc(name))
        self.role_lbl.setText(nfc(role))
        self.step_heading.setText(nfc(heading))
        self.speech_lbl.setText(nfc(speech))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        rect = QRectF(self.rect())

        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, QColor("#E3F8FB"))
        grad.setColorAt(0.55, QColor("#F5F9FE"))
        grad.setColorAt(1.0, QColor("#FFF7EB"))
        painter.fillRect(rect, QBrush(grad))

        halftone = self._renderer.get_master_pixmap("game/zs_common_pop_01.png")
        if not halftone.isNull() and halftone.height() > 0:
            scale = rect.height() / float(halftone.height())
            draw_w = float(halftone.width()) * scale
            painter.save()
            painter.setOpacity(0.07)
            tr = QTransform()
            tr.translate(rect.right(), rect.top())
            tr.scale(-1.0, 1.0)
            painter.setTransform(tr)
            painter.drawPixmap(
                QRectF(0.0, 0.0, draw_w, rect.height()),
                halftone,
                QRectF(0.0, 0.0, float(halftone.width()), float(halftone.height())),
            )
            painter.restore()
        painter.fillRect(
            QRectF(rect.left(), rect.bottom() - 1.0, rect.width(), 1.0),
            QColor(PORCELAIN_TOKENS.HAIRLINE),
        )
        painter.end()


class _StepNumberBadge(QLabel):
    def __init__(self, num: int, parent: QWidget | None = None) -> None:
        super().__init__(str(num), parent)
        self.setFixedSize(22, 22)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(ui_font(FS_CAPTION, 700))
        self.setStyleSheet(
            f"background: {PORCELAIN_TOKENS.NAVY_SOLID}; color: #FFFFFF; border-radius: 11px;"
        )


class ShortcutWizardDialog(PorcelainDialog):
    """4-step Stella Sora Chibi Shortcut Onboarding & Launch Reminder Dialog for PC Launcher."""

    def __init__(
        self,
        *,
        check_shortcut_fn: Callable[[], dict[str, Any]],
        create_shortcut_fn: Callable[[], tuple[bool, str]],
        trigger: str = "launch",
        game_installed: bool = True,
        mandatory_if_missing: bool = True,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        self._renderer = asset_renderer or get_asset_renderer()
        self._check_fn = check_shortcut_fn
        self._create_fn = create_shortcut_fn
        self._trigger = trigger
        self._game_installed = bool(game_installed)
        self._status: dict[str, Any] = dict(self._safe_check())
        self._mandatory: bool = bool(
            mandatory_if_missing and self._game_installed and not self._is_shortcut_ready()
        )
        self._step: int = 1
        self._check_failed_once: bool = False
        self._create_error_msg: str = ""
        self._create_attempts: int = 0
        self.launch_game_requested: bool = False

        super().__init__(
            title="Lối tắt Chơi Stella VH",
            meta="Bảo vệ cập nhật không cần chạy ngầm",
            icon_path="icons/shield_cyan.svg",
            icon_size=(20, 20),
            variant="info",
            status_tag="Khuyên dùng",
            target_width=620,
            asset_renderer=self._renderer,
            parent=parent,
        )
        self._scan_timer = QTimer(self)
        self._scan_timer.setSingleShot(True)
        self._scan_timer.timeout.connect(self._finish_desktop_check)
        self.setObjectName("shortcutWizardDialog")
        self.setFixedWidth(620)

        p = PORCELAIN_TOKENS
        root = QWidget(self.frame)
        root.setStyleSheet(f"background: {p.WHITE};")
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # 1. Chibi Dialogue Hero Band
        self.hero = _ChibiSpeechBand(self._renderer, root)
        root_lay.addWidget(self.hero)

        # 2. Scrollable Step Body
        self.scroll = QScrollArea(root)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setMinimumHeight(290)
        self.scroll.setMaximumHeight(410)
        self.scroll.setStyleSheet(f"background: {p.WHITE}; border: none;")

        body = QWidget(self.scroll)
        body.setStyleSheet(f"background: {p.WHITE};")
        self._body_lay = QVBoxLayout(body)
        self._body_lay.setContentsMargins(18, 14, 18, 14)
        self._body_lay.setSpacing(12)

        # ---- Step 1 Panel: Visual Comparison + Benefit Summary ----
        self.step1_widget = QWidget(body)
        s1_lay = QVBoxLayout(self.step1_widget)
        s1_lay.setContentsMargins(0, 0, 0, 0)
        s1_lay.setSpacing(10)

        self.step1_ready_banner = AccentBannerStrip(
            "Desktop đã có lối tắt Chơi Stella VH ✓",
            "Biểu tượng tròn mới nhất đã được đồng bộ với Android. Bạn có thể mở Stella Sora an toàn ngay bên dưới!",
            tone="ok",
            icon_path="game/btn_icon_tick.png",
            icon_tint=p.OK_TEXT,
            asset_renderer=self._renderer,
            parent=self.step1_widget,
        )
        s1_lay.addWidget(self.step1_ready_banner)

        compare_box = QFrame(self.step1_widget)
        compare_box.setObjectName("swCompareBox")
        compare_box.setStyleSheet(
            f"QFrame#swCompareBox {{ background: {p.PORCELAIN_BG}; border: 1px solid {p.HAIRLINE}; border-radius: 10px; }}"
        )
        cmp_lay = QHBoxLayout(compare_box)
        cmp_lay.setContentsMargins(14, 12, 14, 12)
        cmp_lay.setSpacing(12)

        # Left: Recommended VH Shortcut Icon
        good_col = QVBoxLayout()
        good_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        good_col.setSpacing(5)
        self.good_icon = _CrispImageBadge(
            "branding/shortcut_vh_icon.png", 96, self._renderer, framed=False, parent=compare_box
        )
        good_col.addWidget(self.good_icon, 0, Qt.AlignmentFlag.AlignCenter)
        good_tag = QLabel(nfc("✓ NÊN BẤM: Chơi Stella VH"), compare_box)
        good_tag.setFont(ui_font(FS_CAPTION, 700))
        good_tag.setStyleSheet(
            f"background: #DCFCE7; color: {p.OK_TEXT}; border-radius: 8px; padding: 3px 10px;"
        )
        good_col.addWidget(good_tag, 0, Qt.AlignmentFlag.AlignCenter)
        good_sub = QLabel(nfc("Kiểm tra Yostar 0,2s · Chặn lỗi cập nhật"), compare_box)
        good_sub.setFont(ui_font(FS_META, 400))
        good_sub.setStyleSheet(f"color: {p.SLATE_MUTED}; background: transparent;")
        good_col.addWidget(good_sub, 0, Qt.AlignmentFlag.AlignCenter)
        cmp_lay.addLayout(good_col, 1)

        # Divider
        vdiv = QFrame(compare_box)
        vdiv.setFixedWidth(1)
        vdiv.setStyleSheet(f"background: {p.HAIRLINE}; border: none;")
        cmp_lay.addWidget(vdiv)

        # Right: Dimmed Original Game Icon
        bad_col = QVBoxLayout()
        bad_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bad_col.setSpacing(5)
        self.orig_icon = _CrispImageBadge(
            "game/zs_sf_popup_head_1.png", 76, self._renderer, framed=True, dimmed=True, parent=compare_box
        )
        bad_col.addWidget(self.orig_icon, 0, Qt.AlignmentFlag.AlignCenter)
        bad_tag = QLabel(nfc("✕ TRÁNH BẤM: Biểu tượng game gốc"), compare_box)
        bad_tag.setFont(ui_font(FS_CAPTION, 700))
        bad_tag.setStyleSheet(
            f"background: #FEE2E2; color: {p.DANGER_TEXT}; border-radius: 8px; padding: 3px 10px;"
        )
        bad_col.addWidget(bad_tag, 0, Qt.AlignmentFlag.AlignCenter)
        bad_sub = QLabel(nfc("Dễ bị lỗi tệp khi Yostar ra bản vá mới"), compare_box)
        bad_sub.setFont(ui_font(FS_META, 400))
        bad_sub.setStyleSheet(f"color: {p.SLATE_MUTED}; background: transparent;")
        bad_col.addWidget(bad_sub, 0, Qt.AlignmentFlag.AlignCenter)
        cmp_lay.addLayout(bad_col, 1)

        s1_lay.addWidget(compare_box)

        why_note = QLabel(
            nfc(
                "• Khi game có bản vá mới từ Yostar, bấm thẳng vào game đã cài Việt Hoá dễ gặp lỗi xác minh (BinDiffPatchError).\n"
                "• Dùng lối tắt Chơi Stella VH giúp Launcher kiểm tra nhanh chỉ 0,2 giây rồi vào thẳng game — KHÔNG cần bật chạy ngầm khay hệ thống 24/7."
            ),
            self.step1_widget,
        )
        why_note.setFont(ui_font(FS_BODY_SM, 400))
        why_note.setWordWrap(True)
        why_note.setStyleSheet(f"color: {p.SLATE_BODY}; background: transparent;")
        s1_lay.addWidget(why_note)
        self._body_lay.addWidget(self.step1_widget)

        # ---- Step 2 Panel: Checking Desktop ----
        self.step2_widget = QWidget(body)
        s2_lay = QVBoxLayout(self.step2_widget)
        s2_lay.setContentsMargins(0, 20, 0, 20)
        s2_lay.setSpacing(10)
        s2_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.s2_icon = _CrispImageBadge(
            "branding/shortcut_vh_icon.png", 92, self._renderer, framed=False, parent=self.step2_widget
        )
        s2_lay.addWidget(self.s2_icon, 0, Qt.AlignmentFlag.AlignCenter)
        s2_lbl = QLabel(nfc("Đang quét màn hình chính Desktop để tìm lối tắt Chơi Stella VH…"), self.step2_widget)
        s2_lbl.setFont(ui_font(FS_BODY, 600))
        s2_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s2_lbl.setStyleSheet(f"color: {p.NAVY_TEXT}; background: transparent;")
        s2_lay.addWidget(s2_lbl)
        self._body_lay.addWidget(self.step2_widget)

        # ---- Step 3 Panel: Mandatory Guided Creation ----
        self.step3_widget = QWidget(body)
        s3_lay = QVBoxLayout(self.step3_widget)
        s3_lay.setContentsMargins(0, 0, 0, 0)
        s3_lay.setSpacing(10)

        self.step3_alert = AccentBannerStrip(
            "Chưa tìm thấy lối tắt Chơi Stella VH trên Desktop",
            "Hãy làm theo 3 bước cực nhanh bên dưới để đặt lối tắt bảo vệ ra màn hình chính Windows nhé!",
            tone="warn",
            icon_path="game/zs_stage_warning_icon_s.png",
            asset_renderer=self._renderer,
            parent=self.step3_widget,
        )
        s3_lay.addWidget(self.step3_alert)

        s3_card = QFrame(self.step3_widget)
        s3_card.setObjectName("swStep3Card")
        s3_card.setStyleSheet(
            f"QFrame#swStep3Card {{ background: {p.PORCELAIN_BG}; border: 1px solid {p.HAIRLINE}; border-radius: 10px; }}"
        )
        s3_row = QHBoxLayout(s3_card)
        s3_row.setContentsMargins(14, 12, 14, 12)
        s3_row.setSpacing(14)

        self.s3_icon = _CrispImageBadge(
            "branding/shortcut_vh_icon.png", 92, self._renderer, framed=False, parent=s3_card
        )
        s3_row.addWidget(self.s3_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        steps_col = QVBoxLayout()
        steps_col.setSpacing(8)
        for num, text_line in (
            (1, 'Bấm nút xanh "Tạo lối tắt Chơi Stella VH trên Desktop" bên dưới.'),
            (2, "Launcher tự đặt biểu tượng tròn có cờ Việt Nam + chữ ▶ CHƠI ra màn hình chính."),
            (3, "Hệ thống tự kiểm tra lại ngay để xác nhận lối tắt đã sẵn sàng!"),
        ):
            r = QHBoxLayout()
            r.setSpacing(8)
            r.addWidget(_StepNumberBadge(num, s3_card), 0, Qt.AlignmentFlag.AlignTop)
            lbl = QLabel(nfc(text_line), s3_card)
            lbl.setFont(ui_font(FS_BODY_SM, 500))
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {p.NAVY_TEXT}; background: transparent;")
            r.addWidget(lbl, 1)
            steps_col.addLayout(r)
        s3_row.addLayout(steps_col, 1)
        s3_lay.addWidget(s3_card)

        self.step3_err_banner = AccentBannerStrip(
            "Không tự ghi được lên Desktop",
            "",
            tone="error",
            icon_path="game/zs_stage_warning_icon_s.png",
            asset_renderer=self._renderer,
            parent=self.step3_widget,
        )
        self.step3_err_banner.setVisible(False)
        s3_lay.addWidget(self.step3_err_banner)
        self._body_lay.addWidget(self.step3_widget)

        # ---- Step 4 Panel: Launch Instructions ----
        self.step4_widget = QWidget(body)
        s4_lay = QVBoxLayout(self.step4_widget)
        s4_lay.setContentsMargins(0, 0, 0, 0)
        s4_lay.setSpacing(10)

        self.step4_ok = AccentBannerStrip(
            "Đã xác nhận lối tắt Chơi Stella VH trên Desktop ✓",
            "Từ giờ bạn chỉ cần nhấp đúp biểu tượng tròn này ngoài Desktop để mở Stella Sora an toàn!",
            tone="ok",
            icon_path="game/btn_icon_tick.png",
            icon_tint=p.OK_TEXT,
            asset_renderer=self._renderer,
            parent=self.step4_widget,
        )
        s4_lay.addWidget(self.step4_ok)

        s4_card = QFrame(self.step4_widget)
        s4_card.setObjectName("swStep4Card")
        s4_card.setStyleSheet(
            f"QFrame#swStep4Card {{ background: {p.ICE_ZEBRA}; border: 1px solid #A9D8E6; border-radius: 10px; }}"
        )
        s4_row = QHBoxLayout(s4_card)
        s4_row.setContentsMargins(14, 12, 14, 12)
        s4_row.setSpacing(14)

        self.s4_icon = _CrispImageBadge(
            "branding/shortcut_vh_icon.png", 98, self._renderer, framed=False, parent=s4_card
        )
        s4_row.addWidget(self.s4_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        guide_col = QVBoxLayout()
        guide_col.setSpacing(7)
        for num, line in (
            (1, "Nhấp đúp biểu tượng tròn Chơi Stella VH ngoài màn hình chính Windows."),
            (2, "Lối tắt tự kiểm tra máy chủ Yostar trong 0,2 giây — nếu không có bản vá mới, game sẽ mở ngay lập tức!"),
            (3, "Nếu Yostar vừa cập nhật, Launcher sẽ chặn kịp lúc và hiện nút Khôi phục gốc 1 chạm để tránh lỗi tệp."),
        ):
            r = QHBoxLayout()
            r.setSpacing(8)
            r.addWidget(_StepNumberBadge(num, s4_card), 0, Qt.AlignmentFlag.AlignTop)
            lbl = QLabel(nfc(line), s4_card)
            lbl.setFont(ui_font(FS_BODY_SM, 500))
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {p.NAVY_TEXT}; background: transparent;")
            r.addWidget(lbl, 1)
            guide_col.addLayout(r)
        s4_row.addLayout(guide_col, 1)
        s4_lay.addWidget(s4_card)
        self._body_lay.addWidget(self.step4_widget)

        self.lock_note = QLabel(
            nfc("🔒 Hãy hoàn tất bước tạo lối tắt Chơi Stella VH để bảo vệ bản Việt Hoá trước khi vào Launcher."),
            body,
        )
        self.lock_note.setFont(ui_font(FS_CAPTION, 600))
        self.lock_note.setWordWrap(True)
        self.lock_note.setStyleSheet(f"color: {p.WARN_ICON}; background: transparent;")
        self._body_lay.addWidget(self.lock_note)
        self._body_lay.addStretch(1)

        self.scroll.setWidget(body)
        root_lay.addWidget(self.scroll, 1)
        self.set_body(root)

        # 3. Footer
        footer = QWidget(self.frame)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(0, 0, 0, 0)
        f_lay.setSpacing(8)

        self.btn_tertiary = QPushButton(nfc("Vào Launcher"), footer)
        self.btn_tertiary.setFlat(True)
        self.btn_tertiary.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tertiary.setFont(ui_font(FS_BODY_SM, 600))
        self.btn_tertiary.setStyleSheet(
            f"QPushButton {{ border: none; background: transparent; color: {p.SLATE_MUTED}; padding: 4px 6px; }}"
            f"QPushButton:hover {{ color: {p.NAVY_TEXT}; text-decoration: underline; }}"
        )
        self.btn_tertiary.clicked.connect(self._on_tertiary)
        f_lay.addWidget(self.btn_tertiary)

        f_lay.addStretch(1)

        self.btn_secondary = ActionButton(
            "Xem hướng dẫn",
            variant="light_secondary",
            height=38,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_secondary.clicked.connect(self._on_secondary)
        f_lay.addWidget(self.btn_secondary)

        self.btn_primary = ActionButton(
            "Kiểm tra lối tắt ngay",
            variant="faceted_cyan",
            icon_path="game/btn_icon_play.png",
            icon_size=(15, 15),
            icon_tint="#153462",
            height=40,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_primary.setDefault(True)
        self.btn_primary.clicked.connect(self._on_primary)
        f_lay.addWidget(self.btn_primary)

        self.set_footer(footer)

        # Wire close button to obey mandatory lock
        try:
            self.close_button.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        self.close_button.clicked.connect(self._try_close)

        self._render_step()
        self.setFixedWidth(620)
        self.adjustSize()

    def _safe_check(self) -> dict[str, Any]:
        try:
            res = self._check_fn()
            return dict(res) if isinstance(res, dict) else {}
        except Exception:
            return {}

    def _is_shortcut_ready(self) -> bool:
        return bool(self._status.get("exists") and self._status.get("ready", True))

    def _can_dismiss(self) -> bool:
        return (not self._mandatory) or (self._step == 4) or self._is_shortcut_ready() or (self._create_attempts >= 2)

    def _try_close(self) -> None:
        if self._can_dismiss():
            self.reject()

    def reject(self) -> None:  # noqa: N802
        if not self._can_dismiss():
            return
        self._scan_timer.stop()
        super().reject()

    def _render_step(self) -> None:
        global _LAUNCH_GUIDE_IDX
        ready = self._is_shortcut_ready()
        can_close = self._can_dismiss()
        self.close_button.setVisible(can_close)
        self.lock_note.setVisible(not can_close)

        self.step1_widget.setVisible(self._step == 1)
        self.step2_widget.setVisible(self._step == 2)
        self.step3_widget.setVisible(self._step == 3)
        self.step4_widget.setVisible(self._step == 4)

        self.btn_tertiary.setVisible(False)
        self.btn_secondary.setVisible(False)
        self.btn_primary.setVisible(True)
        self.btn_primary.setEnabled(True)

        if self._step == 1:
            self.step1_ready_banner.setVisible(ready)
            if ready:
                cid, name, role, quote = _SW_LAUNCH_GUIDES[_LAUNCH_GUIDE_IDX % len(_SW_LAUNCH_GUIDES)]
                if self._trigger == "launch":
                    _LAUNCH_GUIDE_IDX = (_LAUNCH_GUIDE_IDX + 1) % len(_SW_LAUNCH_GUIDES)
                self.frame.set_status_tag("Gợi ý mở game an toàn")
                self.hero.set_dialogue(cid, name, role, "Mở game bằng Lối tắt Việt Hoá", quote)
                self.btn_primary.setText(nfc("Mở Stella Sora ngay (An toàn)"))
                self.btn_secondary.setText(nfc("Xem hướng dẫn lối tắt"))
                self.btn_secondary.setVisible(True)
                self.btn_tertiary.setText(nfc("Vào Launcher (Cài / Cập nhật VH)"))
                self.btn_tertiary.setVisible(True)
            else:
                self.frame.set_status_tag("Bảo vệ cập nhật · Bước 1/4")
                self.hero.set_dialogue(
                    "111",
                    "Iris",
                    "Hướng dẫn viên Stella Sora",
                    "Hãy dùng Lối tắt Chơi Stella VH",
                    '"Chào Bạo Chúa! Để tránh lỗi xác minh tệp khi game cập nhật — và KHÔNG cần bật chạy ngầm khay hệ thống 24/7 — hãy luôn mở game bằng lối tắt Chơi Stella VH trên Desktop nhé!"',
                )
                self.btn_primary.setText(nfc("Kiểm tra lối tắt trên Desktop ngay"))
                if not self._mandatory:
                    self.btn_tertiary.setText(nfc("Vào Launcher"))
                    self.btn_tertiary.setVisible(True)

        elif self._step == 2:
            self.frame.set_status_tag("Kiểm tra Desktop · Bước 2/4")
            self.hero.set_dialogue(
                "103",
                "Amber",
                "Đội kiểm tra thiết bị",
                "Đang kiểm tra màn hình chính…",
                '"Đợi tớ một xíu nhé! Tớ đang kiểm tra xem trên Desktop máy bạn đã có lối tắt Chơi Stella VH chưa nè…"',
            )
            self.btn_primary.setVisible(False)

        elif self._step == 3:
            self.frame.set_status_tag("Cài đặt bắt buộc · Bước 3/4")
            if self._check_failed_once:
                self.hero.set_dialogue(
                    "114",
                    "Chaton",
                    "Đội nhắc nhở thân thiện",
                    "Tạo lối tắt Chơi Stella VH",
                    '"Ơ kìa, mình kiểm tra lại vẫn chưa thấy lối tắt Chơi Stella VH ngoài Desktop! Bấm nút xanh bên dưới để tụi mình tạo ngay cho bạn nhé~"',
                )
                self.step3_alert.set_content(
                    "Kiểm tra lại vẫn chưa thấy lối tắt trên Desktop",
                    "Hãy bấm nút xanh bên dưới để tạo lối tắt Chơi Stella VH rồi xác nhận lại nhé!",
                    tone="warn",
                )
            else:
                self.hero.set_dialogue(
                    "107",
                    "Tilia",
                    "Hiệp sĩ Chính Nghĩa",
                    "Tạo lối tắt Chơi Stella VH",
                    '"Tớ kiểm tra rồi — trên Desktop CHƯA có lối tắt Chơi Stella VH! Bấm 1 chạm bên dưới để tạo ngay nhé, chỉ mất 2 giây thôi!"',
                )
                self.step3_alert.set_content(
                    "Chưa tìm thấy lối tắt Chơi Stella VH trên Desktop",
                    "Hãy bấm nút xanh bên dưới để đặt lối tắt bảo vệ ra màn hình chính Windows nhé!",
                    tone="warn",
                )
            if self._create_error_msg:
                self.step3_err_banner.set_content(
                    "Không tự ghi được lên Desktop",
                    self._create_error_msg
                    + "\n(Kiểm tra quyền ghi Desktop / Controlled Folder Access, hoặc bấm 'Để sau' để vào Launcher.)",
                    tone="error",
                )
                self.step3_err_banner.setVisible(True)
            else:
                self.step3_err_banner.setVisible(False)

            self.btn_primary.setText(nfc("Tạo lối tắt Chơi Stella VH trên Desktop"))
            self.btn_secondary.setText(nfc("Kiểm tra lại Desktop"))
            self.btn_secondary.setVisible(True)
            if can_close:
                self.btn_tertiary.setText(nfc("Để sau · Vào Launcher"))
                self.btn_tertiary.setVisible(True)

        elif self._step == 4:
            self.frame.set_status_tag("Hoàn tất · Bước 4/4")
            self.hero.set_dialogue(
                "112",
                "Noya",
                "Hướng dẫn viên Stella Sora",
                "Cách mở game bằng Lối tắt VH",
                '"Hoan hô! Lối tắt Chơi Stella VH đã sẵn sàng ngoài Desktop rồi ♪ Từ giờ bạn cứ nhấp đúp đúng biểu tượng tròn này để vào game an toàn nhé!"',
            )
            self.btn_primary.setText(nfc("Mở Stella Sora ngay (An toàn)"))
            self.btn_secondary.setText(nfc("Hoàn tất · Vào Launcher"))
            self.btn_secondary.setVisible(True)

        self.scroll.verticalScrollBar().setValue(0)

    def start_desktop_check(self, *, from_retry: bool = False, delay_ms: int = 320) -> None:
        self._pending_retry = bool(from_retry)
        self._step = 2
        self._render_step()
        if delay_ms <= 0:
            self._finish_desktop_check()
        else:
            self._scan_timer.start(delay_ms)

    def _finish_desktop_check(self) -> None:
        self._status = dict(self._safe_check())
        if self._is_shortcut_ready():
            self._mandatory = False
            self._check_failed_once = False
            self._create_error_msg = ""
            self._step = 4
        else:
            self._check_failed_once = bool(getattr(self, "_pending_retry", False))
            self._step = 3
        self._render_step()

    def _on_primary(self) -> None:
        if self._step == 1:
            if self._is_shortcut_ready():
                self.launch_game_requested = True
                self.accept()
            else:
                self.start_desktop_check(from_retry=False)
        elif self._step == 3:
            self._create_attempts += 1
            try:
                ok, msg = self._create_fn()
            except Exception as exc:  # noqa: BLE001
                ok, msg = False, str(exc)
            if ok:
                self._create_error_msg = ""
                self.start_desktop_check(from_retry=False, delay_ms=220)
            else:
                self._create_error_msg = str(msg or "Không thể tạo lối tắt trên Desktop.")
                self._render_step()
        elif self._step == 4:
            self.launch_game_requested = True
            self.accept()

    def _on_secondary(self) -> None:
        if self._step == 1:
            self._step = 4
            self._render_step()
        elif self._step == 3:
            self.start_desktop_check(from_retry=True)
        elif self._step == 4:
            self.accept()

    def _on_tertiary(self) -> None:
        if self._can_dismiss():
            self.reject()

    def refresh_dpr(self) -> None:
        self.frame.refresh_dpr()
        for w in (self.hero.chibi, self.good_icon, self.orig_icon, self.s2_icon, self.s3_icon, self.s4_icon):
            w.update()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()
