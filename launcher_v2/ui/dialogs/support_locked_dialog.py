# -*- coding: utf-8 -*-
"""
SupportLockedDialog — Compact Light Porcelain modal displayed when SUPPORT_DONATION_ENABLED=False.

Matches Preview r5 (#modal-support-closed):
- 552px target width, content-hugging height (zero giant whitespace)
- #264278 Navy header with Common_Favour_Heart.png, 'Ủng hộ dự án', 'Tạm đóng' pill, far-right × + Esc
- Hero row with playerhead_main_ccc.png, zs_common_star_l_1.png, green free-affirmation strip
- Cyan-accented anti-scam notice strip with asar_info_navy.svg
- Footer with 'Dự án phi lợi nhuận · doubleD1302/AmeeVH' and 'Đã hiểu' CTA
- ZERO 'Đội ngũ thực hiện' / team credits
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..theme.tokens import PORCELAIN_TOKENS
from ..theme.typography import (
    FS_BODY,
    FS_BODY_SM,
    FS_META,
    FS_MODAL_HERO,
    FS_SUBTITLE,
    nfc,
    ui_font,
)
from ..widgets import (
    AccentBannerStrip,
    ActionButton,
    AssetRenderer,
    PorcelainDialog,
    get_asset_renderer,
)


class SupportLockedDialog(PorcelainDialog):
    """Compact centered notice dialog when donation/support is temporarily locked."""

    def __init__(
        self,
        *,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        self._renderer = asset_renderer or get_asset_renderer()
        super().__init__(
            title="Ủng hộ dự án",
            icon_path="game/Common_Favour_Heart.png",
            icon_size=(22, 22),
            status_tag="Tạm đóng",
            target_width=PORCELAIN_TOKENS.MODAL_WIDTH_SUPPORT_LOCKED,
            asset_renderer=self._renderer,
            parent=parent,
        )
        self.setObjectName("supportLockedDialog")
        p = PORCELAIN_TOKENS

        body = QWidget(self.frame)
        body.setStyleSheet(f"background: {p.WHITE};")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        # 1. Hero section: Chibi Ma Vương + title + green free affirmation
        hero = QFrame(body)
        hero.setObjectName("supportLockedHero")
        hero.setStyleSheet(
            f"QFrame#supportLockedHero {{ background: {p.WHITE}; border: none; "
            f"border-bottom: 1px solid {p.HAIRLINE}; }}"
        )
        hero_lay = QHBoxLayout(hero)
        hero_lay.setContentsMargins(22, 20, 22, 18)
        hero_lay.setSpacing(16)

        self._chibi_label = QLabel(hero)
        self._chibi_label.setFixedSize(74, 82)
        self._chibi_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_lay.addWidget(self._chibi_label, 0, Qt.AlignmentFlag.AlignVCenter)

        copy_col = QVBoxLayout()
        copy_col.setContentsMargins(0, 0, 0, 0)
        copy_col.setSpacing(8)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(7)

        self._star_title_icon = QLabel(hero)
        self._star_title_icon.setFixedSize(17, 17)
        title_row.addWidget(self._star_title_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        self.hero_title_label = QLabel(nfc("Chức năng ủng hộ hiện đang tạm đóng"), hero)
        self.hero_title_label.setFont(ui_font(FS_MODAL_HERO, 700))
        self.hero_title_label.setWordWrap(True)
        self.hero_title_label.setStyleSheet(f"color: {p.NAVY_TEXT}; background: transparent;")
        title_row.addWidget(self.hero_title_label, 1)
        copy_col.addLayout(title_row)

        affirmation = QFrame(hero)
        affirmation.setObjectName("supportAffirmationStrip")
        affirmation.setStyleSheet(
            f"QFrame#supportAffirmationStrip {{ background: {p.OK_TINT}; "
            f"border: none; border-left: 3px solid {p.OK_ACCENT}; }}"
        )
        aff_lay = QVBoxLayout(affirmation)
        aff_lay.setContentsMargins(11, 8, 11, 8)
        aff_lay.setSpacing(0)

        self.affirmation_label = QLabel(
            nfc(
                f"<strong style='color:{p.OK_TEXT};'>Bản Việt hóa Stella Sora luôn hoàn toàn miễn phí</strong> "
                f"<span style='color:{p.OK_SUB}; font-weight:500;'>(cho đến khi hết kinh phí duy trì)</span>"
            ),
            affirmation,
        )
        self.affirmation_label.setTextFormat(Qt.TextFormat.RichText)
        self.affirmation_label.setFont(ui_font(FS_SUBTITLE, 400))
        self.affirmation_label.setWordWrap(True)
        self.affirmation_label.setStyleSheet(f"color: {p.NAVY_TEXT}; background: transparent;")
        aff_lay.addWidget(self.affirmation_label)
        copy_col.addWidget(affirmation)

        hero_lay.addLayout(copy_col, 1)
        body_lay.addWidget(hero)

        # 2. Anti-scam notice strip
        self.notice_strip = AccentBannerStrip(
            "",
            "Người chơi không cần trả bất kỳ khoản phí nào để tải, cài đặt hay cập nhật. "
            "Hãy cảnh giác với mọi hành vi rao bán hoặc thu phí bản dịch.",
            tone="info",
            icon_path="game/asar_info_navy.svg",
            asset_renderer=self._renderer,
            parent=body,
        )
        self.notice_strip.body_label.setFont(ui_font(FS_BODY, 400))
        body_lay.addWidget(self.notice_strip)
        self.set_body(body)

        # 3. Footer
        footer = QWidget(self.frame)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(0, 0, 0, 0)
        f_lay.setSpacing(10)

        note_row = QHBoxLayout()
        note_row.setContentsMargins(0, 0, 0, 0)
        note_row.setSpacing(7)

        self._star_footer_icon = QLabel(footer)
        self._star_footer_icon.setFixedSize(14, 14)
        note_row.addWidget(self._star_footer_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        self.footer_note_label = QLabel(nfc("Dự án phi lợi nhuận · doubleD1302/AmeeVH"), footer)
        self.footer_note_label.setFont(ui_font(FS_META, 600))
        self.footer_note_label.setStyleSheet(f"color: {p.SLATE_MUTED}; background: transparent;")
        note_row.addWidget(self.footer_note_label, 1)
        f_lay.addLayout(note_row, 1)

        self.btn_acknowledge = ActionButton(
            "Đã hiểu",
            variant="light_cyan",
            height=34,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_acknowledge.setMinimumWidth(104)
        self.btn_acknowledge.clicked.connect(self.accept)
        self.btn_acknowledge.setDefault(True)
        f_lay.addWidget(self.btn_acknowledge, 0, Qt.AlignmentFlag.AlignVCenter)

        self.set_footer(footer)
        self.refresh_dpr()
        self.setFixedWidth(p.MODAL_WIDTH_SUPPORT_LOCKED)
        self.adjustSize()

    def compact_layout(self, available_width: int, available_height: int | None = None) -> None:
        super().compact_layout(available_width, available_height)
        if available_height is not None:
            max_h = max(240, int(available_height) - 32)
            self.setMaximumHeight(max_h)
            self.adjustSize()
            if self.height() > max_h:
                self.resize(self.width(), max_h)
        else:
            self.setMaximumHeight(16777215)
            self.adjustSize()

    def refresh_dpr(self) -> None:
        dpr = max(1.0, float(self.devicePixelRatioF()))
        chibi = self._renderer.get_icon_pixmap("game/playerhead_main_ccc.png", (74, 82), dpr)
        if not chibi.isNull():
            self._chibi_label.setPixmap(chibi)
        star_lg = self._renderer.get_icon_pixmap("game/zs_common_star_l_1.png", (17, 17), dpr)
        if not star_lg.isNull():
            self._star_title_icon.setPixmap(star_lg)
        star_sm = self._renderer.get_icon_pixmap("game/zs_common_star_l_1.png", (14, 14), dpr)
        if not star_sm.isNull():
            self._star_footer_icon.setPixmap(star_sm)
        self.frame.refresh_dpr()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()
