# -*- coding: utf-8 -*-
"""
InstallCompletedDialog — Light Porcelain post-install summary modal (v1.3.4 compatible).

Exact constructor signature:
  InstallCompletedDialog(game_info, install_result, shortcut_created_initially=False,
                         shortcut_preference=None, parent=None)
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.shortcut import create_game_shortcut, get_desktop_path
from ..theme.tokens import PORCELAIN_TOKENS
from ..theme.typography import FS_BODY, FS_BODY_SM, nfc, ui_font
from ..widgets import (
    AccentBannerStrip,
    ActionButton,
    AssetRenderer,
    HairlineKeyValueTable,
    PorcelainDialog,
    PorcelainSectionBar,
    StatusInline,
    get_asset_renderer,
)


def _activate_subtree_layouts(widget: QWidget | None) -> None:
    if widget is None:
        return
    for child in widget.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
        _activate_subtree_layouts(child)
    lay = widget.layout()
    if lay is not None:
        lay.invalidate()
        lay.activate()
    widget.updateGeometry()


class _BodyScrollArea(QScrollArea):
    """Scroll area that keeps desktop content-hugging sizeHint while allowing compact shrink."""

    def sizeHint(self) -> QSize:  # noqa: N802
        base = super().sizeHint()
        inner = self.widget()
        if inner is not None:
            win = self.window()
            win_w = (win.width() - 4) if win is not None else 0
            vp_w = self.viewport().width() if self.isVisible() else 0
            target_w = max(240, win_w if (win is not None and win_w > 0) else vp_w)
            h = inner.heightForWidth(target_w) if inner.hasHeightForWidth() else inner.sizeHint().height()
            if h <= 0:
                h = inner.sizeHint().height()
            return QSize(base.width(), max(64, h))
        return base

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        base = super().minimumSizeHint()
        return QSize(min(240, base.width()), 64)


class InstallCompletedDialog(PorcelainDialog):
    """Post-install completion modal with desktop shortcut creation and Launch CTA."""

    def __init__(
        self,
        game_info,
        install_result,
        shortcut_created_initially: bool = False,
        shortcut_preference: bool | None = None,
        parent: QWidget | None = None,
        *,
        asset_renderer: AssetRenderer | None = None,
    ) -> None:
        self._renderer = asset_renderer or get_asset_renderer()
        self.game_info = game_info
        self.install_result = dict(install_result) if isinstance(install_result, dict) else {}
        self.launch_game_clicked: bool = False

        super().__init__(
            title="Cài đặt hoàn tất",
            meta="Dữ liệu Việt hóa Stella Sora đã được cài đặt thành công!",
            icon_path="game/btn_icon_tick.png",
            icon_size=(20, 20),
            target_width=PORCELAIN_TOKENS.MODAL_WIDTH_COMPLETED,
            asset_renderer=self._renderer,
            parent=parent,
        )
        self.setObjectName("installCompletedDialog")
        p = PORCELAIN_TOKENS

        self.scroll_area = _BodyScrollArea(self.frame)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setStyleSheet(f"background: {p.WHITE}; border: none;")

        body = QWidget(self.scroll_area)
        body.setStyleSheet(f"background: {p.WHITE};")
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.setSpacing(0)

        # 1. Kết quả cài đặt
        res_bar = PorcelainSectionBar("Kết quả cài đặt Việt hóa", body)
        res_bar.set_right_widget(
            StatusInline("Thành công", tone="ok", surface="light", asset_renderer=self._renderer, parent=res_bar)
        )
        b_lay.addWidget(res_bar)

        msg = str(self.install_result.get("message") or "Đã nạp toàn bộ tệp bản dịch thành công.")
        kv_rows: list[tuple[str, str] | tuple[str, str, str]] = [
            ("Trạng thái", msg, "ok"),
        ]
        if self.install_result.get("version"):
            kv_rows.append(("Phiên bản dịch", str(self.install_result["version"]), "mono"))
        if self.install_result.get("files_count") is not None:
            kv_rows.append(("Số tệp đã nạp", f"{self.install_result['files_count']} tệp"))
        if game_info is not None and getattr(game_info, "game_path", None):
            kv_rows.append(("Thư mục game", str(game_info.game_path), "mono"))

        res_wrap = QWidget(body)
        res_wrap.setStyleSheet(f"background: {p.PORCELAIN_BG}; border-bottom: 1px solid {p.HAIRLINE};")
        rw_lay = QVBoxLayout(res_wrap)
        rw_lay.setContentsMargins(16, 12, 16, 12)
        self.result_table = HairlineKeyValueTable(res_wrap)
        self.result_table.set_kv_rows(kv_rows, key_width_pct=0.32)
        rw_lay.addWidget(self.result_table)
        b_lay.addWidget(res_wrap)

        # 2. Lối tắt màn hình chính (Desktop Shortcut)
        b_lay.addWidget(PorcelainSectionBar("Lối tắt màn hình chính (Desktop)", body))

        sc_band = QFrame(body)
        sc_band.setStyleSheet(f"background: {p.WHITE}; border: none; border-bottom: 1px solid {p.HAIRLINE};")
        sc_lay = QHBoxLayout(sc_band)
        sc_lay.setContentsMargins(18, 12, 18, 12)
        sc_lay.setSpacing(10)

        self.cb_shortcut = QCheckBox(nfc("Thêm lối tắt vào màn hình chính"), sc_band)
        self.cb_shortcut.setObjectName("porcelainCheck")
        self.cb_shortcut.setFont(ui_font(FS_BODY, 600))
        self.cb_shortcut.setCursor(Qt.CursorShape.PointingHandCursor)
        initial_checked = (
            bool(shortcut_created_initially)
            if shortcut_preference is None
            else bool(shortcut_preference)
        )
        self.cb_shortcut.setChecked(initial_checked)
        sc_lay.addWidget(self.cb_shortcut, 1)

        self.btn_create_now = ActionButton(
            "Tạo lối tắt ngay",
            variant="light_secondary",
            icon_path="game/asar_path_navy.svg",
            icon_size=(14, 14),
            height=30,
            asset_renderer=self._renderer,
            parent=sc_band,
        )
        self.btn_create_now.clicked.connect(self._create_shortcut_now)
        sc_lay.addWidget(self.btn_create_now, 0)
        b_lay.addWidget(sc_band)

        init_status = (
            'Đã tạo lối tắt "Stella Sora Việt Hóa" trên màn hình chính.'
            if shortcut_created_initially
            else 'Tích chọn hoặc bấm "Tạo lối tắt ngay" nếu bạn muốn đặt biểu tượng khởi động game ngoài Desktop.'
        )
        self.shortcut_strip = AccentBannerStrip(
            "",
            init_status,
            tone="ok" if shortcut_created_initially else "info",
            icon_path="game/btn_icon_tick.png" if shortcut_created_initially else "game/asar_info_navy.svg",
            icon_tint=p.OK_TEXT if shortcut_created_initially else None,
            asset_renderer=self._renderer,
            parent=body,
        )
        self.shortcut_strip.body_label.setFont(ui_font(FS_BODY_SM, 500))
        b_lay.addWidget(self.shortcut_strip)

        self.scroll_area.setWidget(body)
        self.set_body(self.scroll_area)

        # 3. Footer
        footer = QWidget(self.frame)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(0, 0, 0, 0)
        f_lay.setSpacing(10)
        f_lay.addStretch(1)

        self.btn_close = ActionButton(
            "Đóng",
            variant="light_secondary",
            height=34,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_close.setMinimumWidth(96)
        self.btn_close.clicked.connect(self._on_close)
        f_lay.addWidget(self.btn_close)

        self.btn_launch = ActionButton(
            "Mở game ngay",
            variant="light_cyan",
            icon_path="game/btn_icon_play.png",
            icon_size=(14, 14),
            icon_tint=p.NAVY_TEXT,
            height=34,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_launch.setMinimumWidth(136)
        self.btn_launch.clicked.connect(self._on_launch)
        self.btn_launch.setDefault(True)
        f_lay.addWidget(self.btn_launch)

        self.set_footer(footer)
        self.refresh_dpr()
        self._sync_scroll_geometry()
        self.adjustSize()

    def _create_shortcut_now(self) -> None:
        if not self.game_info or not getattr(self.game_info, "game_path", None):
            self.shortcut_strip.set_content(
                "", "Không xác định được thư mục game để tạo lối tắt.", tone="warn"
            )
            return
        ok, msg = create_game_shortcut(self.game_info.game_path)
        if ok:
            self.shortcut_strip.set_content(
                "", 'Đã tạo lối tắt "Stella Sora Việt Hóa" trên màn hình chính thành công!', tone="ok"
            )
            self.cb_shortcut.setChecked(True)
        else:
            self.shortcut_strip.set_content("", msg, tone="warn")

    def _ensure_shortcut(self) -> None:
        if (
            self.cb_shortcut.isChecked()
            and self.game_info
            and getattr(self.game_info, "game_path", None)
        ):
            desktop = get_desktop_path()
            lnk = desktop / "Stella Sora Việt Hóa.lnk"
            if not lnk.exists():
                create_game_shortcut(self.game_info.game_path)

    def _on_close(self) -> None:
        self._ensure_shortcut()
        self.accept()

    def _on_launch(self) -> None:
        self._ensure_shortcut()
        self.launch_game_clicked = True
        self.accept()

    def _sync_scroll_geometry(self) -> None:
        _activate_subtree_layouts(self.scroll_area.widget())
        self.scroll_area.updateGeometry()
        self.frame.body_container.updateGeometry()
        self.frame.updateGeometry()
        self.updateGeometry()
        if self.frame.layout() is not None:
            self.frame.layout().activate()
        if self.layout() is not None:
            self.layout().activate()

    def compact_layout(self, available_width: int, available_height: int | None = None) -> None:
        clamped_w = max(320, min(self._target_width, int(available_width) - 32))
        self.setFixedWidth(clamped_w)
        if available_height is not None:
            max_h = max(240, int(available_height) - 32)
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
        dpr = max(1.0, float(self.devicePixelRatioF()))
        tick = self._renderer.get_icon_pixmap(
            "game/btn_icon_tick.png", (20, 20), dpr, tint="#6EE7B7"
        )
        if not tick.isNull():
            self.frame.icon_label.setPixmap(tick)
        self.frame.refresh_dpr()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()
