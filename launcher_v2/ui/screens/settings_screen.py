# -*- coding: utf-8 -*-
"""
SettingsScreen — Light Porcelain 2-column settings & v1.3.4 migration view.

Contracts enforced:
- Header controls strict left-to-right order:
  [Mặc định] -> [Lưu & Đồng bộ] -> [1px divider] -> far-right [×] (plus Esc)
- Binds DEFAULT_CONFIG (auto_restore_before_game_update defaults to False, NEVER hardcoded True)
- Validates github_repo/branch via core.config.derived_github_endpoints
- 3-way graphics_mode segmented control (auto, software, noblur)
- reduced_motion, auto_sync_official_bg with live background tier subtitle
- DỮ LIỆU & SAO LƯU live migration status + HairlineKeyValueTable with clean middle elision
- Corrupt config preservation mode (_corrupt) + Mở thư mục dữ liệu
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtWidgets import (
    QBoxLayout,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.bg_sync import BackgroundFrame
from ...core.config import (
    DEFAULT_CONFIG,
    DEFAULT_GITHUB_BRANCH,
    DEFAULT_GITHUB_REPO,
    VALID_GRAPHICS_MODES,
    ConfigManager,
    PathManager,
    derived_github_endpoints,
)
from ..theme.tokens import LAYOUT_TOKENS, PORCELAIN_TOKENS
from ..theme.typography import (
    FS_BODY,
    FS_BODY_SM,
    FS_CAPTION,
    FS_META,
    mono_font,
    nfc,
    ui_font,
)
from ..widgets import (
    AccentBannerStrip,
    ActionButton,
    AssetRenderer,
    HairlineKeyValueTable,
    PorcelainSectionBar,
    PorcelainWindowFrame,
    StatusInline,
    get_asset_renderer,
)


class _PathCellElider(QObject):
    """Elides long spaceless paths in HairlineKeyValueTable value cells without altering tooltip."""

    def __init__(self, label: QLabel, full_text: str) -> None:
        super().__init__(label)
        self._label = label
        self._full_text = nfc(full_text)
        label.setToolTip(self._full_text)
        label.setWordWrap(False)
        label.setMinimumWidth(60)
        label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        label.installEventFilter(self)
        self._apply()

    def _apply(self) -> None:
        avail = max(48, self._label.width() - 24)
        elided = self._label.fontMetrics().elidedText(
            self._full_text, Qt.TextElideMode.ElideMiddle, avail
        )
        self._label.setText(elided)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if watched is self._label and event.type() == QEvent.Type.Resize:
            self._apply()
        return False


class _SegmentedControl(QFrame):
    """Flat 3-way segmented control (#EEF4FA track, #264278 active segment)."""

    value_changed = Signal(str)

    def __init__(
        self,
        options: list[tuple[str, str]],
        *,
        initial: str = "auto",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("settingsSegmentedControl")
        p = PORCELAIN_TOKENS
        self.setStyleSheet(
            f"QFrame#settingsSegmentedControl {{ background: {p.ICE_ZEBRA}; "
            f"border: 1px solid {p.HAIRLINE_SEG}; border-radius: 4px; }}"
        )
        self._buttons: dict[str, QPushButton] = {}
        self._value = initial

        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(2)

        for key, label in options:
            btn = QPushButton(nfc(label), self)
            btn.setObjectName("segBtn")
            btn.setFixedHeight(27)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFlat(True)
            btn.clicked.connect(lambda _chk=False, k=key: self.set_value(k, emit=True))
            lay.addWidget(btn, 1)
            self._buttons[key] = btn

        self.set_value(initial, emit=False)

    def value(self) -> str:
        return self._value

    def set_value(self, key: str, *, emit: bool = False) -> None:
        if key not in self._buttons:
            key = next(iter(self._buttons), "auto")
        changed = key != self._value
        self._value = key
        p = PORCELAIN_TOKENS
        for k, btn in self._buttons.items():
            active = k == self._value
            btn.setFont(ui_font(FS_CAPTION, 600))
            if active:
                btn.setStyleSheet(
                    f"QPushButton#segBtn {{ border: none; border-radius: 3px; "
                    f"background: {p.NAVY_SOLID}; color: #FFFFFF; padding: 0 6px; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton#segBtn {{ border: none; border-radius: 3px; "
                    f"background: transparent; color: {p.SLATE_BODY}; padding: 0 6px; }}"
                    f"QPushButton#segBtn:hover {{ background: rgba(38, 66, 120, 0.08); }}"
                )
        if emit and changed:
            self.value_changed.emit(self._value)


class SettingsScreen(QWidget):
    """Porcelain Settings screen with validation, corrupt-config protection & migration info."""

    close_requested = Signal()
    browse_game_requested = Signal()
    save_and_sync_requested = Signal(dict)
    reset_defaults_requested = Signal()
    preserve_corrupt_requested = Signal()
    reduced_motion_toggled = Signal(bool)
    auto_sync_bg_toggled = Signal(bool)
    graphics_mode_changed = Signal(str)
    error_raised = Signal(str, str, object)  # action, error_code, exception
    toast_requested = Signal(str, str)

    def __init__(
        self,
        *,
        path_manager: PathManager | None = None,
        config_manager: ConfigManager | None = None,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._pm = path_manager
        self._cm = config_manager
        self._renderer = asset_renderer or get_asset_renderer(
            path_manager.resource_dir if path_manager is not None else None
        )
        self._bg_tier_label = "Tầng 3 Bundled Master (2048×1451)"
        self._advanced_open = False
        self._path_eliders: list[_PathCellElider] = []
        self._loading_ui = False

        self.setObjectName("settingsScreen")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
            LAYOUT_TOKENS.VIEWPORT_PAD_X,
            LAYOUT_TOKENS.VIEWPORT_PAD_Y,
        )
        outer.setSpacing(0)

        self.frame = PorcelainWindowFrame(
            "Cài đặt",
            meta="Tùy chỉnh thư mục, cập nhật và hiển thị",
            icon_path="game/asar_set.svg",
            icon_size=(22, 22),
            asset_renderer=self._renderer,
            parent=self,
        )
        self.frame.meta_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self.frame.meta_label.setMinimumWidth(0)
        self.frame._title_row.setStretchFactor(self.frame.meta_label, 100)
        self._sync_meta_max_width()
        self.frame.close_requested.connect(self.close_requested.emit)
        outer.addWidget(self.frame)

        # Header Controls: strict left-to-right order:
        # [Mặc định] -> [Lưu & Đồng bộ] -> [1px divider] -> [×]
        self.reset_button = ActionButton(
            "Mặc định",
            variant="header_white",
            icon_path="game/btn_icon_reset.png",
            icon_size=(14, 14),
            icon_tint=PORCELAIN_TOKENS.NAVY_TEXT,
            height=30,
            asset_renderer=self._renderer,
            parent=self.frame,
        )
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.frame.add_header_control(self.reset_button)

        self.sync_button = ActionButton(
            "Lưu & Đồng bộ",
            variant="light_cyan",
            icon_path="game/btn_common_refresh.png",
            icon_size=(14, 14),
            icon_tint=PORCELAIN_TOKENS.NAVY_TEXT,
            height=32,
            asset_renderer=self._renderer,
            parent=self.frame,
        )
        self.sync_button.clicked.connect(self._on_save_and_sync_clicked)
        self.frame.add_header_control(self.sync_button)

        # Body container: optional corrupt banner + 2-column scrollable grid
        p = PORCELAIN_TOKENS
        body_root = QWidget(self.frame)
        body_root.setStyleSheet(f"background: {p.WHITE};")
        body_root_lay = QVBoxLayout(body_root)
        body_root_lay.setContentsMargins(0, 0, 0, 0)
        body_root_lay.setSpacing(0)

        self.corrupt_banner = AccentBannerStrip(
            "Cấu hình bị hỏng — bản gốc đang được giữ nguyên",
            "Không thể lưu thay đổi lên tệp hỏng. Hãy bấm phục hồi để lưu bản lỗi sang tên khác và tạo cấu hình mới.",
            tone="warn",
            icon_path="game/zs_stage_warning_icon_s.png",
            asset_renderer=self._renderer,
            parent=body_root,
        )
        self.btn_preserve_corrupt = ActionButton(
            "Giữ bản lỗi và phục hồi cấu hình",
            variant="navy_solid",
            height=30,
            asset_renderer=self._renderer,
            parent=self.corrupt_banner,
        )
        self.btn_preserve_corrupt.clicked.connect(self._on_preserve_corrupt_clicked)
        self.corrupt_banner.set_right_widget(self.btn_preserve_corrupt)
        self.corrupt_banner.setVisible(False)
        body_root_lay.addWidget(self.corrupt_banner)

        self.scroll_area = QScrollArea(body_root)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"background: {p.WHITE}; border: none;")
        body_root_lay.addWidget(self.scroll_area, 1)

        grid_host = QWidget(self.scroll_area)
        grid_host.setStyleSheet(f"background: {p.WHITE};")
        self._grid_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, grid_host)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(0)

        # ---------------- Left Column ----------------
        self.left_col = QFrame(grid_host)
        self.left_col.setObjectName("settingsLeftCol")
        self.left_col.setStyleSheet(
            f"QFrame#settingsLeftCol {{ background: {p.WHITE}; border: none; border-right: 1px solid {p.HAIRLINE}; }}"
        )
        left_lay = QVBoxLayout(self.left_col)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        # Section 1: THƯ MỤC GAME & GÓI CÀI
        left_lay.addWidget(PorcelainSectionBar("Thư mục Game & Gói cài", self.left_col))

        # Game path
        row_gp, gp_lay = self._make_form_row(self.left_col)
        gp_lay.addWidget(self._make_field_label("Thư mục cài Stella Sora", row_gp))
        gp_input_row = QHBoxLayout()
        gp_input_row.setSpacing(6)
        self.game_path_input = QLineEdit(row_gp)
        self.game_path_input.setObjectName("porcelainInput")
        self.game_path_input.setReadOnly(True)
        self.game_path_input.setFont(mono_font(FS_META, 400))
        self.game_path_input.setFixedHeight(30)
        self.game_path_input.setPlaceholderText(nfc("Chưa chọn thư mục game"))
        gp_input_row.addWidget(self.game_path_input, 1)

        self.btn_browse_game = ActionButton(
            "Chọn",
            variant="light_secondary",
            icon_path="game/asar_path_navy.svg",
            icon_size=(14, 14),
            height=28,
            asset_renderer=self._renderer,
            parent=row_gp,
        )
        self.btn_browse_game.clicked.connect(self.browse_game_requested.emit)
        gp_input_row.addWidget(self.btn_browse_game)
        gp_lay.addLayout(gp_input_row)
        left_lay.addWidget(row_gp)

        # Payload path
        row_pp, pp_lay = self._make_form_row(self.left_col)
        pp_lay.addWidget(self._make_field_label("Gói cài đặt từ máy (ngoại tuyến)", row_pp))
        pp_input_row = QHBoxLayout()
        pp_input_row.setSpacing(6)
        self.payload_path_input = QLineEdit(row_pp)
        self.payload_path_input.setObjectName("porcelainInput")
        self.payload_path_input.setReadOnly(True)
        self.payload_path_input.setFont(mono_font(FS_META, 400))
        self.payload_path_input.setFixedHeight(30)
        self.payload_path_input.setPlaceholderText(nfc("Chưa chọn gói (.zip / manifest)"))
        pp_input_row.addWidget(self.payload_path_input, 1)

        self.btn_browse_payload = ActionButton(
            "Chọn",
            variant="light_secondary",
            height=28,
            asset_renderer=self._renderer,
            parent=row_pp,
        )
        self.btn_browse_payload.clicked.connect(self._browse_payload)
        pp_input_row.addWidget(self.btn_browse_payload)

        self.btn_clear_payload = ActionButton(
            "Xóa",
            variant="light_secondary",
            height=28,
            asset_renderer=self._renderer,
            parent=row_pp,
        )
        self.btn_clear_payload.clicked.connect(lambda: self.payload_path_input.setText(""))
        pp_input_row.addWidget(self.btn_clear_payload)
        pp_lay.addLayout(pp_input_row)
        left_lay.addWidget(row_pp)

        self.chk_auto_detect, row_ad = self._make_switch_row(
            "Tự tìm bản cài Yostar / Steam khi mở launcher", parent=self.left_col
        )
        left_lay.addWidget(row_ad)

        self.chk_desktop_shortcut, row_ds = self._make_switch_row(
            "Tạo lối tắt ngoài Desktop", parent=self.left_col
        )
        left_lay.addWidget(row_ds)

        # Section 2: NGUỒN TẢI & CẬP NHẬT
        left_lay.addWidget(PorcelainSectionBar("Nguồn tải & Cập nhật", self.left_col))

        row_gh = QFrame(self.left_col)
        row_gh.setStyleSheet(f"background: {p.WHITE}; border: none; border-bottom: 1px solid #E2EAF4;")
        gh_lay = QHBoxLayout(row_gh)
        gh_lay.setContentsMargins(14, 8, 14, 8)
        gh_lay.setSpacing(8)

        repo_col = QVBoxLayout()
        repo_col.setSpacing(4)
        repo_col.addWidget(self._make_field_label("Kho GitHub", row_gh))
        self.github_repo_input = QLineEdit(row_gh)
        self.github_repo_input.setObjectName("porcelainInput")
        self.github_repo_input.setFont(mono_font(FS_META, 400))
        self.github_repo_input.setFixedHeight(30)
        repo_col.addWidget(self.github_repo_input)
        gh_lay.addLayout(repo_col, 145)

        branch_col = QVBoxLayout()
        branch_col.setSpacing(4)
        branch_col.addWidget(self._make_field_label("Nhánh", row_gh))
        self.github_branch_input = QLineEdit(row_gh)
        self.github_branch_input.setObjectName("porcelainInput")
        self.github_branch_input.setFont(mono_font(FS_META, 400))
        self.github_branch_input.setFixedHeight(30)
        branch_col.addWidget(self.github_branch_input)
        gh_lay.addLayout(branch_col, 75)
        left_lay.addWidget(row_gh)

        # Collapsible Custom URLs
        adv_frame = QFrame(self.left_col)
        adv_frame.setStyleSheet(
            f"background: {p.ICE_ROW_ALT}; border: none; border-bottom: 1px solid #E2EAF4;"
        )
        adv_lay = QVBoxLayout(adv_frame)
        adv_lay.setContentsMargins(14, 7, 14, 7)
        adv_lay.setSpacing(7)

        self.adv_toggle_btn = QPushButton(nfc("▸ Đường dẫn tùy chỉnh (Nâng cao)"), adv_frame)
        self.adv_toggle_btn.setFont(ui_font(FS_META, 700))
        self.adv_toggle_btn.setFlat(True)
        self.adv_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.adv_toggle_btn.setStyleSheet(
            f"QPushButton {{ border: none; background: transparent; color: {p.CYAN_TEXT_DEEP}; "
            f"text-align: left; padding: 0px; }}"
        )
        self.adv_toggle_btn.clicked.connect(self._toggle_advanced)
        adv_lay.addWidget(self.adv_toggle_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.adv_body = QWidget(adv_frame)
        self.adv_body.setVisible(False)
        adv_b_lay = QVBoxLayout(self.adv_body)
        adv_b_lay.setContentsMargins(0, 2, 0, 2)
        adv_b_lay.setSpacing(6)

        adv_b_lay.addWidget(self._make_field_label("URL Manifest tùy chỉnh", self.adv_body))
        self.custom_manifest_input = QLineEdit(self.adv_body)
        self.custom_manifest_input.setObjectName("porcelainInput")
        self.custom_manifest_input.setFont(mono_font(FS_META, 400))
        self.custom_manifest_input.setFixedHeight(30)
        self.custom_manifest_input.setPlaceholderText(nfc("Mặc định theo GitHub Release"))
        adv_b_lay.addWidget(self.custom_manifest_input)

        adv_b_lay.addWidget(self._make_field_label("URL Thông báo tùy chỉnh", self.adv_body))
        self.custom_announcements_input = QLineEdit(self.adv_body)
        self.custom_announcements_input.setObjectName("porcelainInput")
        self.custom_announcements_input.setFont(mono_font(FS_META, 400))
        self.custom_announcements_input.setFixedHeight(30)
        self.custom_announcements_input.setPlaceholderText(nfc("Mặc định: launcher/notifications.json"))
        adv_b_lay.addWidget(self.custom_announcements_input)
        adv_lay.addWidget(self.adv_body)
        left_lay.addWidget(adv_frame)

        self.chk_check_updates, row_cu = self._make_switch_row(
            "Tự cập nhật launcher khi có bản mới", parent=self.left_col
        )
        left_lay.addWidget(row_cu)

        self.chk_check_official, row_co = self._make_switch_row(
            "Theo dõi bản cập nhật game từ Yostar", parent=self.left_col
        )
        left_lay.addWidget(row_co)

        self.chk_auto_restore, row_ar = self._make_switch_row(
            "Tự hoàn nguyên bản gốc trước khi game cập nhật",
            subtitle="Tránh lỗi tệp khi Yostar / Steam phát hành bản vá mới",
            highlight=True,
            parent=self.left_col,
        )
        left_lay.addWidget(row_ar)

        # Section 2b: BẢO VỆ CẬP NHẬT GAME
        guard_bar = PorcelainSectionBar("Bảo vệ cập nhật Game", self.left_col)
        self.btn_guard_safety = ActionButton(
            "An toàn · Check AI",
            variant="light_secondary",
            icon_path="icons/shield_ink.svg",
            icon_size=(13, 13),
            icon_tint=p.NAVY_TEXT,
            height=24,
            asset_renderer=self._renderer,
            parent=guard_bar,
        )
        self.btn_guard_safety.clicked.connect(self._open_safety_explainer)
        guard_bar.set_right_widget(self.btn_guard_safety)
        left_lay.addWidget(guard_bar)

        self.chk_guard_watch, row_gw = self._make_switch_row(
            "Cảnh báo ngay khi vào game có bản cập nhật",
            subtitle="Theo dõi máy chủ Yostar và nhật ký Player.log theo thời gian thực",
            highlight=True,
            parent=self.left_col,
        )
        left_lay.addWidget(row_gw)

        self.chk_guard_tray, row_gt = self._make_switch_row(
            "Thu gọn xuống khay hệ thống khi bấm đóng (×)",
            subtitle="Giữ lớp bảo vệ chạy ngầm để chặn lỗi cập nhật ngay cả khi mở game trực tiếp",
            parent=self.left_col,
        )
        left_lay.addWidget(row_gt)

        self.chk_guard_auto_close, row_gac = self._make_switch_row(
            "Tự động đóng game ngay khi phát hiện bản cập nhật",
            subtitle="Đóng StellaSora.exe trước khi hộp thoại trong game kịp tải bản vá",
            parent=self.left_col,
        )
        left_lay.addWidget(row_gac)

        self.chk_guard_autostart, row_gas = self._make_switch_row(
            "Tự chạy ngầm bảo vệ khi khởi động Windows",
            subtitle="Khởi động gọn dưới khay hệ thống (HKCU Run, không cần quyền Quản trị)",
            parent=self.left_col,
        )
        left_lay.addWidget(row_gas)
        left_lay.addStretch(1)

        self._grid_layout.addWidget(self.left_col, 1)

        # ---------------- Right Column ----------------
        self.right_col = QFrame(grid_host)
        self.right_col.setObjectName("settingsRightCol")
        self.right_col.setStyleSheet(f"QFrame#settingsRightCol {{ background: {p.WHITE}; border: none; }}")
        right_lay = QVBoxLayout(self.right_col)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        # Section 3: HIỂN THỊ & HÌNH NỀN
        right_lay.addWidget(PorcelainSectionBar("Hiển thị & Hình nền", self.right_col))

        row_gfx, gfx_lay = self._make_form_row(self.right_col)
        gfx_lay.addWidget(self._make_field_label("Chế độ đồ họa", row_gfx))
        self.gfx_segmented = _SegmentedControl(
            [
                ("auto", "Tự động"),
                ("software", "Tương thích (CPU)"),
                ("noblur", "Tắt làm mờ"),
            ],
            initial="auto",
            parent=row_gfx,
        )
        self.gfx_segmented.value_changed.connect(self._on_graphics_mode_changed)
        gfx_lay.addWidget(self.gfx_segmented)

        gfx_hint = QLabel(nfc("Chọn Tương thích nếu máy card cũ bị lỗi hiển thị."), row_gfx)
        gfx_hint.setFont(ui_font(FS_CAPTION, 400))
        gfx_hint.setWordWrap(True)
        gfx_hint.setStyleSheet(f"color: {p.SLATE_MUTED}; background: transparent;")
        gfx_lay.addWidget(gfx_hint)
        right_lay.addWidget(row_gfx)

        self.chk_reduced_motion, row_rm = self._make_switch_row(
            "Giảm hiệu ứng chuyển động",
            subtitle="Tắt chuyển cảnh và giảm làm mờ cho máy cấu hình nhẹ",
            parent=self.right_col,
        )
        self.chk_reduced_motion.toggled.connect(self._on_reduced_motion_toggled)
        right_lay.addWidget(row_rm)

        self.chk_auto_sync_bg, row_bg, self.bg_tier_subtitle_label = self._make_switch_row_with_sub(
            "Đồng bộ hình nền từ Official Launcher",
            subtitle=f"Đang dùng: {self._bg_tier_label}",
            parent=self.right_col,
        )
        self.chk_auto_sync_bg.toggled.connect(self._on_auto_sync_bg_toggled)
        right_lay.addWidget(row_bg)

        # Section 4: DỮ LIỆU & SAO LƯU
        mig_bar = PorcelainSectionBar("Dữ liệu & Sao lưu", self.right_col)
        self.migration_status_inline = StatusInline(
            "Sẵn sàng",
            tone="muted",
            surface="light",
            asset_renderer=self._renderer,
            parent=mig_bar,
        )
        mig_bar.set_right_widget(self.migration_status_inline)
        right_lay.addWidget(mig_bar)

        self.migration_table = HairlineKeyValueTable(self.right_col)
        right_lay.addWidget(self.migration_table)

        self.mig_preserved_strip = AccentBannerStrip(
            "Đã giữ nguyên: cấu hình, bản sao lưu và nhật ký cài đặt.",
            "",
            tone="ok",
            icon_path="game/btn_icon_tick.png",
            icon_tint=p.OK_TEXT,
            asset_renderer=self._renderer,
            parent=self.right_col,
        )
        right_lay.addWidget(self.mig_preserved_strip)

        mig_footer = QFrame(self.right_col)
        mig_footer.setStyleSheet(f"background: {p.WHITE}; border: none;")
        mf_lay = QHBoxLayout(mig_footer)
        mf_lay.setContentsMargins(14, 10, 14, 10)
        mf_lay.setSpacing(8)

        flag_hint = QLabel(
            "Hỗ trợ cờ <code>--app-data-dir</code> khi kiểm thử.",
            mig_footer,
        )
        flag_hint.setFont(ui_font(FS_CAPTION, 400))
        flag_hint.setTextFormat(Qt.TextFormat.RichText)
        flag_hint.setWordWrap(True)
        flag_hint.setStyleSheet(f"color: {p.SLATE_MUTED}; background: transparent;")
        mf_lay.addWidget(flag_hint, 1)

        self.btn_open_data_dir = ActionButton(
            "Mở thư mục dữ liệu",
            variant="light_secondary",
            icon_path="game/asar_path_navy.svg",
            icon_size=(14, 14),
            height=28,
            asset_renderer=self._renderer,
            parent=mig_footer,
        )
        self.btn_open_data_dir.clicked.connect(self._open_app_data_dir)
        mf_lay.addWidget(self.btn_open_data_dir, 0)
        right_lay.addWidget(mig_footer)
        right_lay.addStretch(1)

        self._grid_layout.addWidget(self.right_col, 1)

        self.scroll_area.setWidget(grid_host)
        self.frame.set_body(body_root)

        self.refresh_from_config()

    def _make_form_row(self, parent: QWidget) -> tuple[QFrame, QVBoxLayout]:
        row = QFrame(parent)
        row.setStyleSheet(f"background: {PORCELAIN_TOKENS.WHITE}; border: none; border-bottom: 1px solid #E2EAF4;")
        lay = QVBoxLayout(row)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(4)
        return row, lay

    def _make_field_label(self, text: str, parent: QWidget) -> QLabel:
        lbl = QLabel(nfc(text), parent)
        lbl.setFont(ui_font(FS_META, 600))
        lbl.setStyleSheet(f"color: {PORCELAIN_TOKENS.NAVY_TEXT}; background: transparent;")
        return lbl

    def _make_switch_row(
        self,
        title: str,
        *,
        subtitle: str = "",
        highlight: bool = False,
        parent: QWidget,
    ) -> tuple[QCheckBox, QFrame]:
        chk, frame, _ = self._make_switch_row_with_sub(
            title, subtitle=subtitle, highlight=highlight, parent=parent
        )
        return chk, frame

    def _make_switch_row_with_sub(
        self,
        title: str,
        *,
        subtitle: str = "",
        highlight: bool = False,
        parent: QWidget,
    ) -> tuple[QCheckBox, QFrame, Optional[QLabel]]:
        p = PORCELAIN_TOKENS
        frame = QFrame(parent)
        if highlight:
            frame.setStyleSheet(
                f"background: {p.HIGHLIGHT_STRIP_BG}; border: none; "
                f"border-left: 3px solid {p.CYAN_ACCENT}; border-bottom: 1px solid {p.HAIRLINE};"
            )
        else:
            frame.setStyleSheet(
                f"background: {p.WHITE}; border: none; border-bottom: 1px solid #E2EAF4;"
            )
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(10)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        title_lbl = QLabel(nfc(title), frame)
        title_lbl.setFont(ui_font(FS_BODY_SM, 700 if subtitle else 400))
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(
            f"color: {p.NAVY_TEXT if subtitle else p.SLATE_BODY}; background: transparent;"
        )
        text_col.addWidget(title_lbl)

        sub_lbl: Optional[QLabel] = None
        if subtitle:
            sub_lbl = QLabel(nfc(subtitle), frame)
            sub_lbl.setFont(ui_font(FS_CAPTION, 400))
            sub_lbl.setWordWrap(True)
            sub_lbl.setStyleSheet(f"color: {p.SLATE_MUTED}; background: transparent;")
            text_col.addWidget(sub_lbl)

        lay.addLayout(text_col, 1)

        chk = QCheckBox("", frame)
        chk.setObjectName("porcelainCheck")
        chk.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(chk, 0, Qt.AlignmentFlag.AlignVCenter)

        def _toggle_on_click(_ev) -> None:
            if chk.isEnabled():
                chk.toggle()

        frame.mousePressEvent = _toggle_on_click  # type: ignore[method-assign]
        return chk, frame, sub_lbl

    def _toggle_advanced(self) -> None:
        self._advanced_open = not self._advanced_open
        self.adv_body.setVisible(self._advanced_open)
        self.adv_toggle_btn.setText(
            nfc(f"{'▾' if self._advanced_open else '▸'} Đường dẫn tùy chỉnh (Nâng cao)")
        )

    def _browse_payload(self) -> None:
        start_dir = str(self._pm.app_data_dir) if self._pm is not None else ""
        chosen, _ = QFileDialog.getOpenFileName(
            self,
            nfc("Chọn gói bản dịch ngoại tuyến"),
            start_dir,
            nfc("Gói cài đặt (*.zip *.json);;Tất cả (*.*)"),
        )
        if chosen:
            self.payload_path_input.setText(nfc(chosen))

    def _open_app_data_dir(self) -> None:
        if self._pm is None:
            return
        target = self._pm.app_data_dir
        target.mkdir(parents=True, exist_ok=True)
        if hasattr(os, "startfile"):
            try:
                os.startfile(str(target))
            except OSError as exc:
                self.toast_requested.emit(nfc(f"Không mở được thư mục: {exc}"), "warning")

    def _current_cfg_dict(self) -> dict[str, Any]:
        if self._cm is not None:
            return self._cm.data
        return dict(DEFAULT_CONFIG)

    def bind_managers(self, path_manager: PathManager, config_manager: ConfigManager) -> None:
        self._pm = path_manager
        self._cm = config_manager
        self.refresh_from_config()

    def set_game_path(self, path: str | Path | None) -> None:
        self.game_path_input.setText(nfc(str(path or "")))

    def set_bg_frame(self, frame: BackgroundFrame | None) -> None:
        if frame is None:
            return
        label = frame.source_label or ""
        if frame.tier == 1:
            txt = "Tầng 1 Online (Official Live Key Art)"
        elif frame.tier == 2 and "asar" in label.lower():
            txt = "Tầng 2 ASAR (Official Light Key Art)"
        elif frame.tier == 2:
            txt = "Tầng 2 Cache Official"
        else:
            txt = f"Tầng 3 Bundled Master ({frame.width}×{frame.height})"
        self.set_bg_tier_label(txt)

    def set_bg_tier_label(self, label: str) -> None:
        self._bg_tier_label = nfc(label)
        if self.bg_tier_subtitle_label is not None:
            self.bg_tier_subtitle_label.setText(nfc(f"Đang dùng: {self._bg_tier_label}"))

    def refresh_from_config(self) -> None:
        self._loading_ui = True
        try:
            cfg = self._current_cfg_dict()
            is_corrupt = bool(getattr(self._cm, "_corrupt", False)) if self._cm is not None else False

            self.game_path_input.setText(nfc(str(cfg.get("game_path") or "")))
            self.payload_path_input.setText(nfc(str(cfg.get("payload_path") or "")))
            self.chk_auto_detect.setChecked(bool(cfg.get("auto_detect_game", True)))
            self.chk_desktop_shortcut.setChecked(bool(cfg.get("create_desktop_shortcut", True)))
            self.github_repo_input.setText(nfc(str(cfg.get("github_repo") or DEFAULT_GITHUB_REPO)))
            self.github_branch_input.setText(nfc(str(cfg.get("github_branch") or DEFAULT_GITHUB_BRANCH)))
            self.custom_manifest_input.setText(nfc(str(cfg.get("custom_manifest_url") or "")))
            self.custom_announcements_input.setText(nfc(str(cfg.get("custom_announcements_url") or "")))
            self.chk_check_updates.setChecked(bool(cfg.get("check_updates_on_start", True)))
            self.chk_check_official.setChecked(bool(cfg.get("check_official_on_start", True)))
            # Must read config default (False) — never hardcode True
            self.chk_auto_restore.setChecked(
                bool(cfg.get("auto_restore_before_game_update", False))
            )
            self.chk_guard_watch.setChecked(bool(cfg.get("guard_watch_game_updates", True)))
            self.chk_guard_tray.setChecked(bool(cfg.get("guard_background_tray", True)))
            self.chk_guard_auto_close.setChecked(bool(cfg.get("guard_auto_close_game_on_update", False)))
            self.chk_guard_autostart.setChecked(bool(cfg.get("guard_start_with_windows", False)))

            gm = str(cfg.get("graphics_mode") or "auto")
            if gm not in VALID_GRAPHICS_MODES:
                gm = "auto"
            self.gfx_segmented.set_value(gm, emit=False)
            self.chk_reduced_motion.setChecked(bool(cfg.get("reduced_motion", False)))
            self.chk_auto_sync_bg.setChecked(bool(cfg.get("auto_sync_official_bg", True)))

            # Corrupt config preservation mode
            self.corrupt_banner.setVisible(is_corrupt)
            editable = not is_corrupt
            for widget in (
                self.btn_browse_game,
                self.btn_browse_payload,
                self.btn_clear_payload,
                self.chk_auto_detect,
                self.chk_desktop_shortcut,
                self.github_repo_input,
                self.github_branch_input,
                self.custom_manifest_input,
                self.custom_announcements_input,
                self.chk_check_updates,
                self.chk_check_official,
                self.chk_auto_restore,
                self.chk_guard_watch,
                self.chk_guard_tray,
                self.chk_guard_auto_close,
                self.chk_guard_autostart,
                self.gfx_segmented,
                self.chk_reduced_motion,
                self.chk_auto_sync_bg,
                self.sync_button,
            ):
                widget.setEnabled(editable)

            self._refresh_migration_section(is_corrupt=is_corrupt)
        finally:
            self._loading_ui = False

    def _refresh_migration_section(self, *, is_corrupt: bool) -> None:
        if self._pm is None:
            legacy_str = r"%LOCALAPPDATA%\StellaSora_Launcher_Candidate_r02"
            current_str = r"%LOCALAPPDATA%\StellaSora_VietHoa_Launcher"
            status_text = "Sẵn sàng"
            status_tone = "muted"
            preserved_msg = "Đã giữ nguyên: cấu hình, bản sao lưu và nhật ký cài đặt."
            preserved_tone = "ok"
        else:
            legacy_str = str(self._pm.legacy_app_data_dir)
            current_str = str(self._pm.app_data_dir)
            status_text, status_tone, preserved_msg, preserved_tone = self._read_migration_status(
                self._pm, is_corrupt=is_corrupt
            )

        self.migration_status_inline.set_status(status_text, tone=status_tone)
        self.mig_preserved_strip.set_content(preserved_msg, "", tone=preserved_tone)

        self.migration_table.set_kv_rows(
            [
                ("Thư mục cũ (v1.3.4)", legacy_str, "mono"),
                ("Thư mục hiện tại", current_str, "mono"),
            ],
            key_width_pct=0.34,
        )
        # Apply middle elision on long spaceless paths inside HairlineKeyValueTable
        self._path_eliders.clear()
        grid = self.migration_table._grid
        for r in range(2):
            item = grid.itemAtPosition(r, 1)
            if item is not None and isinstance(item.widget(), QLabel):
                lbl: QLabel = item.widget()  # type: ignore[assignment]
                self._path_eliders.append(_PathCellElider(lbl, lbl.text()))

    def _read_migration_status(
        self, pm: PathManager, *, is_corrupt: bool
    ) -> tuple[str, str, str, str]:
        if is_corrupt:
            return (
                "Cấu hình lỗi (đã giữ nguyên)",
                "warn",
                "Phát hiện config.json lỗi; bản gốc được bảo toàn đến khi bạn phục hồi.",
                "warn",
            )
        if pm.is_custom_app_data:
            return (
                "Đang dùng --app-data-dir",
                "muted",
                "Chế độ thư mục dữ liệu độc lập (--app-data-dir); bỏ qua di trú tự động.",
                "info",
            )
        marker = pm.migration_marker_file
        if marker.is_file():
            try:
                data = json.loads(marker.read_text(encoding="utf-8"))
                st = str(data.get("status") or "")
                prev = str(data.get("previous_status") or "")
                eff = prev if st == "already_migrated" and prev else st
                if eff == "partial" or data.get("warning_code"):
                    return (
                        "Di trú có cảnh báo",
                        "warn",
                        "Một số tệp di trú từ v1.3.4 có cảnh báo; dữ liệu gốc vẫn nguyên vẹn.",
                        "warn",
                    )
                if eff == "migrated":
                    return (
                        "Đã chuyển từ v1.3.4",
                        "ok",
                        "Đã giữ nguyên: cấu hình, bản sao lưu và nhật ký cài đặt.",
                        "ok",
                    )
                if eff == "fresh_install":
                    return (
                        "Cài đặt mới",
                        "muted",
                        "Đã khởi tạo thư mục dữ liệu sạch cho launcher v2.0.",
                        "ok",
                    )
            except (OSError, ValueError):
                return (
                    "Di trú có cảnh báo",
                    "warn",
                    "Không đọc được dấu vết di trú; dữ liệu hiện tại vẫn giữ nguyên.",
                    "warn",
                )
        return (
            "Sẵn sàng",
            "muted",
            "Đã giữ nguyên: cấu hình, bản sao lưu và nhật ký cài đặt.",
            "ok",
        )

    def _on_graphics_mode_changed(self, mode: str) -> None:
        if self._loading_ui:
            return
        self.graphics_mode_changed.emit(mode)
        if mode == "software":
            self.toast_requested.emit(
                nfc("Đã chọn Tương thích (CPU) — áp dụng đầy đủ khi mở lại launcher."),
                "info",
            )
        else:
            self.toast_requested.emit(
                nfc("Đã đổi chế độ đồ họa — bấm Lưu & Đồng bộ để ghi cấu hình."),
                "info",
            )

    def _on_reduced_motion_toggled(self, checked: bool) -> None:
        if not self._loading_ui:
            self.reduced_motion_toggled.emit(bool(checked))

    def _on_auto_sync_bg_toggled(self, checked: bool) -> None:
        if not self._loading_ui:
            self.auto_sync_bg_toggled.emit(bool(checked))

    def _on_preserve_corrupt_clicked(self) -> None:
        if self._cm is not None:
            self._cm.preserve_corrupt_and_reset()
            self.refresh_from_config()
            self.toast_requested.emit(
                nfc("Đã giữ bản cấu hình lỗi và khôi phục cấu hình mặc định."),
                "success",
            )
        self.preserve_corrupt_requested.emit()

    def _on_reset_clicked(self) -> None:
        if self._cm is not None and getattr(self._cm, "_corrupt", False):
            self._on_preserve_corrupt_clicked()
            return
        self._loading_ui = True
        try:
            self.payload_path_input.setText(nfc(str(DEFAULT_CONFIG.get("payload_path", ""))))
            self.chk_auto_detect.setChecked(bool(DEFAULT_CONFIG["auto_detect_game"]))
            self.chk_desktop_shortcut.setChecked(bool(DEFAULT_CONFIG["create_desktop_shortcut"]))
            self.github_repo_input.setText(nfc(DEFAULT_GITHUB_REPO))
            self.github_branch_input.setText(nfc(DEFAULT_GITHUB_BRANCH))
            self.custom_manifest_input.setText(nfc(str(DEFAULT_CONFIG["custom_manifest_url"])))
            self.custom_announcements_input.setText(nfc(str(DEFAULT_CONFIG["custom_announcements_url"])))
            self.chk_check_updates.setChecked(bool(DEFAULT_CONFIG["check_updates_on_start"]))
            self.chk_check_official.setChecked(bool(DEFAULT_CONFIG["check_official_on_start"]))
            self.chk_auto_restore.setChecked(bool(DEFAULT_CONFIG["auto_restore_before_game_update"]))
            self.chk_guard_watch.setChecked(bool(DEFAULT_CONFIG["guard_watch_game_updates"]))
            self.chk_guard_tray.setChecked(bool(DEFAULT_CONFIG["guard_background_tray"]))
            self.chk_guard_auto_close.setChecked(bool(DEFAULT_CONFIG["guard_auto_close_game_on_update"]))
            self.chk_guard_autostart.setChecked(bool(DEFAULT_CONFIG["guard_start_with_windows"]))
            self.gfx_segmented.set_value(str(DEFAULT_CONFIG["graphics_mode"]), emit=False)
            self.chk_reduced_motion.setChecked(bool(DEFAULT_CONFIG["reduced_motion"]))
            self.chk_auto_sync_bg.setChecked(bool(DEFAULT_CONFIG["auto_sync_official_bg"]))
        finally:
            self._loading_ui = False

        if self._cm is not None:
            for k, v in DEFAULT_CONFIG.items():
                if k != "game_path":
                    self._cm.set(k, v)
            self._cm.set_channel(DEFAULT_GITHUB_REPO, DEFAULT_GITHUB_BRANCH)
            self._cm.save()
        self.reduced_motion_toggled.emit(bool(DEFAULT_CONFIG["reduced_motion"]))
        self.reset_defaults_requested.emit()
        self.toast_requested.emit(nfc("Đã khôi phục cài đặt mặc định"), "success")

    def collect_values(self) -> dict[str, Any]:
        return {
            "game_path": self.game_path_input.text().strip(),
            "payload_path": self.payload_path_input.text().strip(),
            "auto_detect_game": self.chk_auto_detect.isChecked(),
            "create_desktop_shortcut": self.chk_desktop_shortcut.isChecked(),
            "github_repo": self.github_repo_input.text().strip(),
            "github_branch": self.github_branch_input.text().strip(),
            "custom_manifest_url": self.custom_manifest_input.text().strip(),
            "custom_announcements_url": self.custom_announcements_input.text().strip(),
            "check_updates_on_start": self.chk_check_updates.isChecked(),
            "check_official_on_start": self.chk_check_official.isChecked(),
            "auto_restore_before_game_update": self.chk_auto_restore.isChecked(),
            "guard_watch_game_updates": self.chk_guard_watch.isChecked(),
            "guard_background_tray": self.chk_guard_tray.isChecked(),
            "guard_auto_close_game_on_update": self.chk_guard_auto_close.isChecked(),
            "guard_start_with_windows": self.chk_guard_autostart.isChecked(),
            "graphics_mode": self.gfx_segmented.value(),
            "reduced_motion": self.chk_reduced_motion.isChecked(),
            "auto_sync_official_bg": self.chk_auto_sync_bg.isChecked(),
        }

    def _on_save_and_sync_clicked(self) -> None:
        vals = self.collect_values()
        try:
            derived_github_endpoints(vals["github_repo"], vals["github_branch"])
        except ValueError as exc:
            self.error_raised.emit("Lưu cấu hình", "E-CONFIG-CHANNEL", exc)
            self.toast_requested.emit(nfc(str(exc)), "error")
            return

        if self._cm is not None:
            if getattr(self._cm, "_corrupt", False):
                self._on_preserve_corrupt_clicked()
                return
            for k, v in vals.items():
                if k not in ("github_repo", "github_branch"):
                    self._cm.set(k, v)
            self._cm.set_channel(vals["github_repo"], vals["github_branch"])
            if not self._cm.save():
                self.toast_requested.emit(nfc("Không lưu được tệp cấu hình."), "error")
                return

        self.reduced_motion_toggled.emit(bool(vals["reduced_motion"]))
        self.save_and_sync_requested.emit(vals)
        self.toast_requested.emit(nfc("Đã lưu cài đặt và đồng bộ dữ liệu"), "success")

    def _open_safety_explainer(self) -> None:
        from ..dialogs.safety_explainer_dialog import SafetyExplainerDialog

        repo = self.github_repo_input.text().strip() or DEFAULT_GITHUB_REPO
        branch = self.github_branch_input.text().strip() or DEFAULT_GITHUB_BRANCH
        dlg = SafetyExplainerDialog(
            initial_topic="guard",
            github_repo=repo,
            github_branch=branch,
            asset_renderer=self._renderer,
            parent=self.window(),
        )
        dlg.exec()

    def _sync_meta_max_width(self) -> None:
        txt = self.frame.meta_label.text()
        max_w = max(0, self.frame.meta_label.fontMetrics().horizontalAdvance(txt) + 8)
        self.frame.meta_label.setMaximumWidth(max_w)

    def refresh_dpr(self) -> None:
        self.frame.refresh_dpr()
        self._sync_meta_max_width()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()
        elif event.type() == QEvent.Type.FontChange:
            self._sync_meta_max_width()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.compact_layout(self.width(), self.height())

    def compact_layout(self, width: int, height: int | None = None) -> None:
        p = PORCELAIN_TOKENS
        w = int(width)
        self._sync_meta_max_width()
        self.frame.meta_label.setVisible(w >= 1100 and bool(self.frame.meta_label.text()))
        if w < LAYOUT_TOKENS.TWO_COL_COLLAPSE_THRESHOLD:
            self._grid_layout.setDirection(QBoxLayout.Direction.TopToBottom)
            self.left_col.setStyleSheet(
                f"QFrame#settingsLeftCol {{ background: {p.WHITE}; border: none; "
                f"border-bottom: 1px solid {p.HAIRLINE}; }}"
            )
        else:
            self._grid_layout.setDirection(QBoxLayout.Direction.LeftToRight)
            self.left_col.setStyleSheet(
                f"QFrame#settingsLeftCol {{ background: {p.WHITE}; border: none; "
                f"border-right: 1px solid {p.HAIRLINE}; }}"
            )
