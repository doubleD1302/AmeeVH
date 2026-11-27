# -*- coding: utf-8 -*-
"""
SafetyExplainerDialog — Friendly Random-Chibi Safety Commitment & AI Self-Check Dialog for PC Launcher.

Explains sensitive Windows features (background tray watcher, HKCU autostart, atomic game patching,
and PyInstaller SmartScreen warnings) transparently with random authentic Stella Sora character chibis
and 1-click AI verification prompts pointing directly to the public GitHub repository.
"""
from __future__ import annotations

import random
import urllib.parse
from typing import Optional

from PySide6.QtCore import QEvent, QRectF, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QDesktopServices,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPixmap,
    QTransform,
)
from PIL import Image, ImageFilter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.config import DEFAULT_GITHUB_BRANCH, DEFAULT_GITHUB_REPO
from ..theme.tokens import PORCELAIN_TOKENS
from ..theme.typography import FS_BODY, FS_BODY_SM, FS_CAPTION, FS_META, FS_MODAL_HERO, mono_font, nfc, ui_font
from ..widgets import (
    ActionButton,
    AssetRenderer,
    PorcelainDialog,
    get_asset_renderer,
)

CHIBI_CAST: list[tuple[str, str, str]] = [
    ("103", "Amber", '"Cứ kiểm tra kỹ mọi thứ trước khi bật nhé, tớ đảm bảo sạch sẽ 100%!"'),
    ("107", "Tilia", '"Với danh dự Hiệp sĩ Chính Nghĩa, mọi quyền ở đây đều minh bạch rõ ràng!"'),
    ("110", "Firenze", '"Đừng tin lời suông — cậu cứ dán mã nguồn vào AI kiểm chứng tận mắt nhé."'),
    ("111", "Iris", '"Đừng lo lắng nhé, mình đã chuẩn bị sẵn hướng dẫn tự kiểm tra bằng AI rồi nè!"'),
    ("112", "Noya", '"Mọi dòng code đều mở công khai đó, cậu bấm 1 chạm là kiểm tra được ngay ♪"'),
    ("114", "Chaton", '"Chỉ canh đúng Stella Sora thôi, không tò mò mấy ứng dụng khác đâu nha~"'),
    ("117", "Jinglin", '"An toàn dữ liệu là trên hết! Cậu xem cam kết bên dưới là yên tâm liền."'),
    ("118", "Coronis", '"Tính năng nào cũng chỉ xin đúng quyền tối thiểu nhất, hoàn toàn có thể tự kiểm tra."'),
    ("119", "Nanoha", '"Cậu có thể tự nhờ ChatGPT, Gemini hay Claude đọc code xác nhận hộ đấy!"'),
    ("120", "Canace", '"Dựa theo mã nguồn công khai trên GitHub, mọi thứ đều có thể kiểm chứng độc lập."'),
    ("123", "Ann", '"Để tụi mình giải thích thật nhẹ nhàng để cậu yên tâm cài Việt hoá nha!"'),
    ("134", "Fuyuka", '"Mở code lên soi thoải mái luôn — minh bạch từ đầu đến cuối cho cậu yên tâm!"'),
]

PC_SAFETY_TOPICS: dict[str, dict[str, object]] = {
    "guard": {
        "tab": "Bảo vệ chạy ngầm",
        "title": "Bảo vệ cập nhật & Khởi động cùng Windows có an toàn?",
        "source_path": "launcher_v2/core/game_guard.py",
        "why": [
            "Chỉ kiểm tra máy chủ tài nguyên Yostar và đọc nhật ký Player.log của Stella Sora để phát hiện sớm bản cập nhật game.",
            "Thu gọn xuống khay hệ thống hoặc tự khởi động cùng Windows (HKCU Run) giúp chặn kịp lúc ngay cả khi bạn mở game trực tiếp không qua launcher.",
            "Tùy chọn tự đóng StellaSora.exe chỉ tắt đúng tiến trình game khi sắp dính lỗi xác minh bản vá, hoàn toàn có thể tắt trong Cài đặt.",
        ],
        "pledges": [
            "Không cần quyền Quản trị viên (Admin/UAC) — chỉ ghi đúng 1 khóa khởi động ở HKCU của riêng bạn.",
            "Tuyệt đối KHÔNG đọc bàn phím, chụp màn hình, đọc trình duyệt hay can thiệp bất kỳ ứng dụng nào khác.",
            "100% mã nguồn mở công khai trên GitHub — miễn phí, không quảng cáo, không thu thập dữ liệu cá nhân.",
        ],
        "prompt_files": [
            "launcher_v2/core/game_guard.py",
            "launcher_v2/ui/main_shell.py",
            "launcher_v2/core/shortcut.py",
        ],
        "prompt_focus": "tính năng Bảo vệ cập nhật chạy ngầm ở khay hệ thống, đọc Player.log và Tự khởi động cùng Windows (HKCU Run) của Stella Sora PC Launcher",
    },
    "files": {
        "tab": "Tệp game && Khôi phục",
        "title": "Cài Việt hóa & Khôi phục gốc chạm vào tệp nào?",
        "source_path": "launcher_v2/core/official_restore.py",
        "why": [
            "Chỉ cập nhật đúng tệp ngôn ngữ (data.arcx, lua.arcx), phụ đề (.srt) và gói ảnh đã xác minh SHA256 trong thư mục Persistent_Store của game.",
            "Mọi thao tác cài đặt đều tự động tạo bản sao lưu, đổi tên nguyên tử và hoàn tác sạch nếu xảy ra gián đoạn.",
            "Nút Khôi phục gốc tải trực tiếp tệp chính chủ nguyên bản từ máy chủ Yostar (kiểm tra MD5 từng tệp) để game cập nhật mượt mà.",
        ],
        "pledges": [
            "KHÔNG sửa StellaSora.exe, GameAssembly.dll hay bất kỳ tệp hệ thống Windows nào.",
            "KHÔNG đụng tới tệp đăng nhập, token tài khoản hay dữ liệu lưu cá nhân ngoài thư mục game bạn chọn.",
            "Mọi đường dẫn đều kiểm tra chống symlink / vượt thư mục trước khi ghi.",
        ],
        "prompt_files": [
            "launcher_v2/core/installer.py",
            "launcher_v2/core/official_restore.py",
            "launcher_v2/core/safety.py",
        ],
        "prompt_focus": "cơ chế cài Việt hóa và Khôi phục dữ liệu gốc chính chủ trong Stella Sora PC Launcher",
    },
    "defender": {
        "tab": "SmartScreen && Cập nhật",
        "title": "Vì sao Windows Defender đôi khi cảnh báo tệp .exe?",
        "source_path": "launcher_v2/core/self_update.py",
        "why": [
            "Dự án hoàn toàn miễn phí, phi thương mại nên không mua chứng chỉ số EV Code Signing (chi phí hàng trăm USD/năm).",
            "Các ứng dụng đóng gói bằng PyInstaller chưa có chữ ký trả phí thường bị Windows SmartScreen gắn nhãn 'Nhà phát hành không xác định' (nhận nhầm).",
            "Khi tự cập nhật launcher, app chỉ tải trực tiếp từ GitHub Release chính chủ và bắt buộc khớp 100% mã băm SHA256SUMS.txt trước khi chạy.",
        ],
        "pledges": [
            "Đóng gói minh bạch từ đúng mã nguồn mở trên GitHub bằng script build.py và StellaSora_Launcher_v2.spec công khai.",
            "Không chèn mã ẩn, không tải thực thi từ máy chủ lạ ngoài kho GitHub bạn nhìn thấy trong Cài đặt.",
            "Bạn hoàn toàn có thể tự dùng AI kiểm tra mã nguồn hoặc tự build lại file .exe từ mã nguồn mở.",
        ],
        "prompt_files": [
            "launcher_v2/core/self_update.py",
            "launcher_v2/build.py",
            "launcher_v2/StellaSora_Launcher_v2.spec",
        ],
        "prompt_focus": "cơ chế tự cập nhật và quy trình đóng gói file .exe PyInstaller của Stella Sora PC Launcher",
    },
}

_LAST_CHIBI_IDX: int = -1


class _ChibiAvatarButton(QPushButton):
    """Clickable rounded Stella Sora character chibi badge using Pillow Lanczos resampling for zero aliasing."""

    def __init__(self, asset_renderer: AssetRenderer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self._chibi_rel = "chibis/chibi_111.webp"
        self._pix_cache: dict[tuple[str, int], QPixmap] = {}
        self.setFixedSize(96, 96)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFlat(True)
        self.setToolTip(nfc("Bấm để đổi nhân vật chibi ngẫu nhiên"))

    def set_chibi(self, chibi_id: str) -> None:
        self._chibi_rel = f"chibis/chibi_{chibi_id}.webp"
        self.update()

    def _render_crisp_chibi(self, target_px: int, dpr: float) -> QPixmap:
        key = (self._chibi_rel, target_px)
        cached = self._pix_cache.get(key)
        if cached is not None and not cached.isNull():
            return cached
        resolved = self._renderer.resolve_path(self._chibi_rel)
        if not resolved.is_file():
            return QPixmap()
        try:
            with Image.open(resolved) as src:
                im = src.convert("RGBA")
                im = im.resize((target_px, target_px), Image.Resampling.LANCZOS)
                im = im.filter(ImageFilter.UnsharpMask(radius=0.65, percent=45, threshold=3))
                raw = im.tobytes("raw", "RGBA")
                qimg = QImage(raw, target_px, target_px, target_px * 4, QImage.Format.Format_RGBA8888).copy()
            pix = QPixmap.fromImage(qimg)
            pix.setDevicePixelRatio(dpr)
            self._pix_cache[key] = pix
            return pix
        except Exception:
            return self._renderer.get_icon_pixmap(self._chibi_rel, (88, 88), dpr)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = PORCELAIN_TOKENS
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(QColor(p.CYAN_ACCENT))
        painter.drawRoundedRect(rect, 16.0, 16.0)

        dpr = max(1.0, float(self.devicePixelRatioF()))
        target_px = max(88, round(88 * dpr))
        pix = self._render_crisp_chibi(target_px, dpr)
        if not pix.isNull():
            painter.drawPixmap(QRectF(4.0, 4.0, 88.0, 88.0), pix, QRectF(pix.rect()))
        painter.end()


class _SafetyHeroBand(QWidget):
    """Friendly porcelain-cyan hero header with random clickable Stella Sora chibi and quote."""

    def __init__(self, asset_renderer: AssetRenderer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 13, 18, 12)
        lay.setSpacing(14)

        self.chibi_btn = _ChibiAvatarButton(self._renderer, self)
        lay.addWidget(self.chibi_btn, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setContentsMargins(0, 1, 0, 0)
        col.setSpacing(5)

        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(0, 0, 0, 0)
        badge_row.setSpacing(8)

        self.char_pill = QLabel(nfc("Iris"), self)
        self.char_pill.setFont(ui_font(FS_CAPTION, 700))
        self.char_pill.setStyleSheet(
            f"background: {PORCELAIN_TOKENS.NAVY_SOLID}; color: #FFFFFF; "
            f"border-radius: 9px; padding: 2px 9px;"
        )
        badge_row.addWidget(self.char_pill, 0)

        tag = QLabel(nfc("An toàn & Minh bạch · Bấm chibi để đổi nhân vật"), self)
        tag.setFont(ui_font(FS_CAPTION, 500))
        tag.setStyleSheet(f"color: {PORCELAIN_TOKENS.SLATE_MUTED}; background: transparent;")
        badge_row.addWidget(tag, 1)
        col.addLayout(badge_row)

        self.headline = QLabel(self)
        self.headline.setFont(ui_font(FS_MODAL_HERO, 700))
        self.headline.setWordWrap(True)
        self.headline.setStyleSheet(f"color: {PORCELAIN_TOKENS.NAVY_TEXT}; background: transparent;")
        col.addWidget(self.headline)

        self.quote_label = QLabel(self)
        self.quote_label.setFont(ui_font(FS_BODY_SM, 500))
        self.quote_label.setWordWrap(True)
        self.quote_label.setStyleSheet(
            f"color: {PORCELAIN_TOKENS.CYAN_TEXT_DEEP}; font-style: italic; background: transparent;"
        )
        col.addWidget(self.quote_label)
        lay.addLayout(col, 1)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        rect = QRectF(self.rect())

        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, QColor("#E5F7FA"))
        grad.setColorAt(0.58, QColor("#F4F8FD"))
        grad.setColorAt(1.0, QColor("#FFF4F7"))
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
        painter.fillRect(
            QRectF(rect.left(), rect.bottom() - 1.0, rect.width(), 1.0),
            QColor(PORCELAIN_TOKENS.HAIRLINE),
        )
        painter.end()


class SafetyExplainerDialog(PorcelainDialog):
    """Friendly permission transparency + open-source AI verification dialog for PC Launcher."""

    def __init__(
        self,
        *,
        initial_topic: str = "guard",
        github_repo: str = DEFAULT_GITHUB_REPO,
        github_branch: str = DEFAULT_GITHUB_BRANCH,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        self._renderer = asset_renderer or get_asset_renderer()
        self._repo = (github_repo or DEFAULT_GITHUB_REPO).strip()
        self._branch = (github_branch or DEFAULT_GITHUB_BRANCH).strip()
        self._topic = initial_topic if initial_topic in PC_SAFETY_TOPICS else "guard"
        self._tab_buttons: dict[str, QPushButton] = {}
        self._prompt_open = False

        super().__init__(
            title="Giải thích quyền & Tự kiểm tra an toàn",
            meta="Tự kiểm chứng độc lập bằng AI",
            icon_path="icons/shield_cyan.svg",
            icon_size=(20, 20),
            variant="info",
            status_tag="Mã nguồn mở",
            target_width=640,
            asset_renderer=self._renderer,
            parent=parent,
        )
        self.setObjectName("safetyExplainerDialog")
        self.setFixedWidth(640)

        p = PORCELAIN_TOKENS
        root = QWidget(self.frame)
        root.setStyleSheet(f"background: {p.WHITE};")
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # 1. Random Stella Sora Chibi Hero Band
        self.hero = _SafetyHeroBand(self._renderer, root)
        self.hero.chibi_btn.clicked.connect(self._pick_random_chibi)
        root_lay.addWidget(self.hero)

        # 2. Topic Tabs
        tab_strip = QFrame(root)
        tab_strip.setStyleSheet(
            f"background: {p.PORCELAIN_BG}; border: none; border-bottom: 1px solid {p.HAIRLINE};"
        )
        tab_lay = QHBoxLayout(tab_strip)
        tab_lay.setContentsMargins(16, 8, 16, 8)
        tab_lay.setSpacing(6)
        for key, spec in PC_SAFETY_TOPICS.items():
            btn = QPushButton(nfc(str(spec["tab"])), tab_strip)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda _chk=False, k=key: self._select_topic(k))
            tab_lay.addWidget(btn, 1)
            self._tab_buttons[key] = btn
        root_lay.addWidget(tab_strip)

        # 3. Scrollable Content Area
        self.scroll = QScrollArea(root)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setMinimumHeight(350)
        self.scroll.setMaximumHeight(440)
        self.scroll.setStyleSheet(f"background: {p.WHITE}; border: none;")

        body = QWidget(self.scroll)
        body.setStyleSheet(f"background: {p.WHITE};")
        self._body_lay = QVBoxLayout(body)
        self._body_lay.setContentsMargins(18, 13, 18, 14)
        self._body_lay.setSpacing(11)

        # Section A: Why needed
        why_cap = QLabel(nfc("TÍNH NĂNG NÀY DÙNG ĐỂ LÀM GÌ?"), body)
        why_cap.setFont(ui_font(FS_CAPTION, 700))
        why_cap.setStyleSheet(f"color: {p.SLATE_MUTED}; background: transparent;")
        self._body_lay.addWidget(why_cap)

        self.why_label = QLabel(body)
        self.why_label.setFont(ui_font(FS_BODY_SM, 400))
        self.why_label.setWordWrap(True)
        self.why_label.setStyleSheet(f"color: {p.SLATE_BODY}; background: transparent;")
        self._body_lay.addWidget(self.why_label)

        # Section B: Safety Pledge Box
        pledge_box = QFrame(body)
        pledge_box.setObjectName("safetyPledgeBox")
        pledge_box.setStyleSheet(
            f"QFrame#safetyPledgeBox {{ background: #ECFAF4; border: 1px solid #A4DFC8; border-radius: 8px; }}"
        )
        pl_lay = QVBoxLayout(pledge_box)
        pl_lay.setContentsMargins(12, 10, 12, 10)
        pl_lay.setSpacing(6)

        pl_cap = QLabel(nfc("CAM KẾT AN TOÀN TUYỆT ĐỐI"), pledge_box)
        pl_cap.setFont(ui_font(FS_CAPTION, 700))
        pl_cap.setStyleSheet(f"color: {p.OK_TEXT}; background: transparent;")
        pl_lay.addWidget(pl_cap)

        self._pledge_host = QVBoxLayout()
        self._pledge_host.setContentsMargins(0, 0, 0, 0)
        self._pledge_host.setSpacing(5)
        pl_lay.addLayout(self._pledge_host)
        self._body_lay.addWidget(pledge_box)

        # Section C: AI Self-Check Box
        ai_box = QFrame(body)
        ai_box.setObjectName("aiCheckBox")
        ai_box.setStyleSheet(
            f"QFrame#aiCheckBox {{ background: {p.ICE_ZEBRA}; border: 1px solid #A9D8E6; border-radius: 8px; }}"
        )
        ai_lay = QVBoxLayout(ai_box)
        ai_lay.setContentsMargins(12, 10, 12, 10)
        ai_lay.setSpacing(6)

        ai_head = QHBoxLayout()
        ai_head.setContentsMargins(0, 0, 0, 0)
        ai_head.setSpacing(6)
        ai_star = QLabel(ai_box)
        ai_star.setFixedSize(16, 16)
        star_pix = self._renderer.get_icon_pixmap("game/zs_common_star_l_1.png", (16, 16), max(1.0, float(self.devicePixelRatioF())))
        if not star_pix.isNull():
            ai_star.setPixmap(star_pix)
        ai_head.addWidget(ai_star, 0)
        ai_title = QLabel(nfc("Tự kiểm tra độ an toàn bằng AI (ChatGPT / Gemini / Claude)"), ai_box)
        ai_title.setFont(ui_font(FS_BODY, 700))
        ai_title.setStyleSheet(f"color: {p.NAVY_TEXT}; background: transparent;")
        ai_head.addWidget(ai_title, 1)
        ai_lay.addLayout(ai_head)

        ai_desc = QLabel(
            nfc(
                "1. Bấm nút \"Chép prompt kiểm tra AI\" bên dưới (đã kèm sẵn link trực tiếp tới mã nguồn công khai trên GitHub).\n"
                "2. Dán vào ChatGPT, Gemini hoặc Claude để AI tự đọc mã nguồn và đánh giá độ an toàn độc lập cho bạn."
            ),
            ai_box,
        )
        ai_desc.setFont(ui_font(FS_BODY_SM, 400))
        ai_desc.setWordWrap(True)
        ai_desc.setStyleSheet(f"color: {p.SLATE_BODY}; background: transparent;")
        ai_lay.addWidget(ai_desc)

        self.prompt_toggle_btn = QPushButton(nfc("▸ Xem trước prompt & tệp mã nguồn"), ai_box)
        self.prompt_toggle_btn.setFlat(True)
        self.prompt_toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.prompt_toggle_btn.setFont(ui_font(FS_CAPTION, 700))
        self.prompt_toggle_btn.setStyleSheet(
            f"QPushButton {{ border: none; background: transparent; color: {p.CYAN_TEXT_DEEP}; text-align: left; padding: 2px 0; }}"
        )
        self.prompt_toggle_btn.clicked.connect(self._toggle_prompt_preview)
        ai_lay.addWidget(self.prompt_toggle_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.prompt_preview = QPlainTextEdit(ai_box)
        self.prompt_preview.setReadOnly(True)
        self.prompt_preview.setFont(mono_font(FS_META, 400))
        self.prompt_preview.setFixedHeight(112)
        self.prompt_preview.setStyleSheet(
            f"QPlainTextEdit {{ background: {p.WHITE}; color: {p.NAVY_TEXT}; "
            f"border: 1px solid {p.HAIRLINE}; border-radius: 5px; padding: 6px; }}"
        )
        self.prompt_preview.setVisible(False)
        ai_lay.addWidget(self.prompt_preview)
        self._body_lay.addWidget(ai_box)
        self._body_lay.addStretch(1)

        self.scroll.setWidget(body)
        root_lay.addWidget(self.scroll, 1)
        self.set_body(root)

        # 4. Footer
        footer = QWidget(self.frame)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(0, 0, 0, 0)
        f_lay.setSpacing(8)

        self.btn_source = ActionButton(
            "Xem mã nguồn GitHub",
            variant="light_secondary",
            icon_path="icons/external_link_ink.svg",
            icon_size=(14, 14),
            icon_tint=p.NAVY_TEXT,
            height=36,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_source.clicked.connect(self._open_source_code)
        f_lay.addWidget(self.btn_source)

        f_lay.addStretch(1)

        self.btn_copy_ai = ActionButton(
            "Chép prompt kiểm tra AI",
            variant="light_cyan",
            icon_path="game/btn_icon_copy.png",
            icon_size=(14, 14),
            icon_tint=p.NAVY_TEXT,
            height=36,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_copy_ai.clicked.connect(self._copy_ai_prompt)
        f_lay.addWidget(self.btn_copy_ai)

        self.btn_ok = ActionButton(
            "Đã hiểu",
            variant="navy_solid",
            height=36,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.accept)
        f_lay.addWidget(self.btn_ok)

        self.set_footer(footer)

        self._pick_random_chibi()
        self._select_topic(self._topic)
        self.setFixedWidth(640)
        self.adjustSize()

    def _pick_random_chibi(self) -> None:
        global _LAST_CHIBI_IDX
        choices = list(range(len(CHIBI_CAST)))
        if len(choices) > 1 and _LAST_CHIBI_IDX in choices:
            choices.remove(_LAST_CHIBI_IDX)
        idx = random.choice(choices)
        _LAST_CHIBI_IDX = idx
        cid, name, quote = CHIBI_CAST[idx]
        self.hero.chibi_btn.set_chibi(cid)
        self.hero.char_pill.setText(nfc(name))
        self.hero.quote_label.setText(nfc(quote))

    def _build_ai_prompt(self, topic_key: str) -> str:
        spec = PC_SAFETY_TOPICS.get(topic_key, PC_SAFETY_TOPICS["guard"])
        base = f"https://github.com/{self._repo}"
        branch_q = urllib.parse.quote(self._branch, safe="")
        files = spec["prompt_files"]
        file_lines = "\n".join(f"- {base}/blob/{branch_q}/{f}" for f in files)
        return (
            f"Hãy đóng vai chuyên gia bảo mật Windows & Python, kiểm tra giúp tôi {spec['prompt_focus']} "
            f"có an toàn không:\n"
            f"- Kho mã nguồn công khai: {base}\n"
            f"{file_lines}\n\n"
            "Hãy đọc kỹ các tệp trên và giải thích ngắn gọn, dễ hiểu cho người dùng phổ thông:\n"
            "1. Mã nguồn có dấu hiệu mã độc, đọc bàn phím/màn hình hay gửi dữ liệu cá nhân ra ngoài không?\n"
            "2. Các thao tác trên Registry/tệp game/tự cập nhật có an toàn và nằm đúng phạm vi mô tả không?\n"
            "3. Kết luận tổng thể: Có an toàn để sử dụng trên Windows không?"
        )

    def _select_topic(self, key: str) -> None:
        if key not in PC_SAFETY_TOPICS:
            key = "guard"
        self._topic = key
        spec = PC_SAFETY_TOPICS[key]
        p = PORCELAIN_TOKENS

        for k, btn in self._tab_buttons.items():
            active = k == key
            btn.setFont(ui_font(FS_CAPTION, 700 if active else 500))
            if active:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {p.NAVY_SOLID}; color: #FFFFFF; border: none; border-radius: 5px; padding: 0 8px; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {p.WHITE}; color: {p.SLATE_BODY}; border: 1px solid {p.HAIRLINE}; border-radius: 5px; padding: 0 8px; }}"
                    f"QPushButton:hover {{ background: {p.ICE_ZEBRA}; }}"
                )

        self.hero.headline.setText(nfc(str(spec["title"])))
        why_items = [f"• {line}" for line in spec["why"]]
        self.why_label.setText(nfc("\n".join(why_items)))

        # Rebuild pledge rows with authentic Stella Sora check icons
        while self._pledge_host.count():
            item = self._pledge_host.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        dpr = max(1.0, float(self.devicePixelRatioF()))
        tick_pix = self._renderer.get_icon_pixmap("game/btn_icon_tick.png", (14, 14), dpr, tint=p.OK_TEXT)
        for line in spec["pledges"]:
            row_w = QWidget()
            row_w.setStyleSheet("background: transparent;")
            r_lay = QHBoxLayout(row_w)
            r_lay.setContentsMargins(0, 0, 0, 0)
            r_lay.setSpacing(7)
            ic = QLabel(row_w)
            ic.setFixedSize(14, 14)
            if not tick_pix.isNull():
                ic.setPixmap(tick_pix)
            r_lay.addWidget(ic, 0, Qt.AlignmentFlag.AlignTop)
            txt = QLabel(nfc(str(line)), row_w)
            txt.setFont(ui_font(FS_BODY_SM, 500))
            txt.setWordWrap(True)
            txt.setStyleSheet(f"color: {p.NAVY_TEXT}; background: transparent;")
            r_lay.addWidget(txt, 1)
            self._pledge_host.addWidget(row_w)

        self.prompt_preview.setPlainText(nfc(self._build_ai_prompt(key)))
        self.btn_copy_ai.setText(nfc("Chép prompt kiểm tra AI"))
        self.scroll.verticalScrollBar().setValue(0)

    def _toggle_prompt_preview(self) -> None:
        self._prompt_open = not self._prompt_open
        self.prompt_preview.setVisible(self._prompt_open)
        self.prompt_toggle_btn.setText(
            nfc("▾ Ẩn xem trước prompt" if self._prompt_open else "▸ Xem trước prompt & tệp mã nguồn")
        )

    def _copy_ai_prompt(self) -> None:
        prompt = self._build_ai_prompt(self._topic)
        cb = QGuiApplication.clipboard()
        if cb is not None:
            cb.setText(prompt)
        self.btn_copy_ai.setText(nfc("Đã sao chép prompt ✓"))
        QTimer.singleShot(2500, self._reset_copy_label)

    def _reset_copy_label(self) -> None:
        try:
            self.btn_copy_ai.setText(nfc("Chép prompt kiểm tra AI"))
        except RuntimeError:
            pass

    def _open_source_code(self) -> None:
        spec = PC_SAFETY_TOPICS.get(self._topic, PC_SAFETY_TOPICS["guard"])
        rel = str(spec["source_path"]).lstrip("/")
        branch_q = urllib.parse.quote(self._branch, safe="")
        url = f"https://github.com/{self._repo}/blob/{branch_q}/{rel}"
        QDesktopServices.openUrl(QUrl(url))

    def refresh_dpr(self) -> None:
        self.frame.refresh_dpr()
        self.hero.chibi_btn.update()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()
