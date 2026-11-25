# -*- coding: utf-8 -*-
"""
SmartErrorDialog — Light Porcelain intelligent Error Assistant modal.

Matches Preview r5 (#modal-error-dialog):
- 820px target width (collapses 2-col grids to 1-col below 720 DIP)
- #264278 Navy header with 5px left + 2px bottom severity accent (#E11D48 error / #D97706 warn / #12B8C4 info)
- zs_stage_warning_icon.png, coral code pill, #report_id, title, playerhead_main_b.png, far-right × + Esc
- Summary + numbered steps
- THÔNG TIN KIỂM TRA 3x3 hairline grid (ErrorReport.context_rows)
- Live async net_probe readout panel (set_probe_running / set_probe_result updating DNS / Kết nối cell in-place)
- CÁCH SỬA ĐỀ XUẤT (up to 4 primary actions from quick_fix.plan_actions) + THAO TÁC KHÁC
  (remaining actions from quick_fix.secondary_actions — all 8 canonical actions in 1 click)
- PII-redacted clipboard copy & .txt/.json export_report
"""
from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.error_report import ErrorContext, ErrorReport, copy_text_native, export_report
from ...core.net_probe import format_probe
from ...core.quick_fix import QuickFixAction, plan_actions, secondary_actions
from ..theme.tokens import PORCELAIN_TOKENS
from ..theme.typography import (
    FS_BODY,
    FS_BODY_SM,
    FS_CAPTION,
    FS_META,
    FS_SUBTITLE,
    mono_font,
    nfc,
    ui_font,
)
from ..widgets import (
    ActionButton,
    AssetRenderer,
    HairlineKeyValueTable,
    PorcelainDialog,
    get_asset_renderer,
)

_PRIMARY_ICON_MAP: dict[str, tuple[str, str | None]] = {
    "close_game": ("game/asar_power.svg", None),
    "relaunch_admin": ("game/btn_login_repair_light.png", None),
    "probe_network": ("game/asar_proxy.svg", None),
    "open_game_dir": ("game/asar_path.svg", None),
    "switch_safe_graphics": ("game/btn_icon_main_setting.png", None),
    "reset_config": ("game/btn_icon_reset.png", "#FFFFFF"),
    "restore_official": ("game/btn_icon_back.png", "#FFFFFF"),
    "copy_report": ("game/btn_icon_copy.png", "#FFFFFF"),
}

_SECONDARY_ICON_MAP: dict[str, tuple[str, str | None]] = {
    "close_game": ("game/asar_power_navy.svg", None),
    "relaunch_admin": ("game/btn_login_repair.png", None),
    "probe_network": ("game/asar_proxy_navy.svg", None),
    "open_game_dir": ("game/asar_path_navy.svg", None),
    "switch_safe_graphics": ("game/asar_set_navy.svg", None),
    "reset_config": ("game/btn_icon_reset.png", PORCELAIN_TOKENS.NAVY_TEXT),
    "restore_official": ("game/btn_icon_back.png", PORCELAIN_TOKENS.NAVY_TEXT),
    "copy_report": ("game/btn_icon_copy.png", PORCELAIN_TOKENS.NAVY_TEXT),
}

_PROBE_VERDICT_MAP: dict[str, tuple[str, str]] = {
    "ok": ("GitHub: Kết nối tốt", "ok"),
    "offline": ("Mất Internet hoàn toàn", "danger"),
    "dns_blocked": ("Lỗi DNS GitHub · 1.1.1.1 OK", "warn"),
    "dns_broken": ("DNS hỏng · IP trực tiếp OK", "warn"),
    "blocked": ("Kết nối tới GitHub bị chặn", "danger"),
    "captive_portal": ("Captive Portal (cần đăng nhập Wi-Fi)", "danger"),
}


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


class SmartErrorDialog(PorcelainDialog):
    """Light Porcelain error assistant with 3x3 context table, live probe panel, and 8 quick fixes."""

    def __init__(
        self,
        report: ErrorReport,
        ctx: Optional[ErrorContext] = None,
        controller: Any = None,
        parent: QWidget | None = None,
        *,
        asset_renderer: AssetRenderer | None = None,
    ) -> None:
        self._renderer = asset_renderer or get_asset_renderer()
        self.report = report
        self.ctx = ctx
        self._controller = controller
        self._context_rows: list[dict[str, str]] = [dict(r) for r in (report.context_rows or ())]
        self._action_buttons: dict[str, ActionButton] = {}
        self.primary_buttons: list[ActionButton] = []
        self.secondary_buttons: list[ActionButton] = []
        self._primary_actions: list[QuickFixAction] = []
        self._secondary_actions: list[QuickFixAction] = []
        self._grid_cols: int = 2

        lvl = (report.level or "error").strip().lower()
        variant = "error" if lvl == "error" else ("warning" if lvl == "warning" else "default")

        super().__init__(
            title=report.title or "Đã xảy ra sự cố",
            icon_path="game/zs_stage_warning_icon.png",
            icon_size=(38, 38),
            variant=variant,
            target_width=PORCELAIN_TOKENS.MODAL_WIDTH_ERROR,
            asset_renderer=self._renderer,
            parent=parent,
        )
        self.setObjectName("smartErrorDialog")
        p = PORCELAIN_TOKENS

        # Header badge row above title: coral/amber code pill + #report_id
        badge_wrap = QWidget(self.frame.header_bar)
        bw_lay = QHBoxLayout(badge_wrap)
        bw_lay.setContentsMargins(0, 0, 0, 0)
        bw_lay.setSpacing(8)

        pill_bg = p.CORAL_DANGER if lvl == "error" else (p.WARN_ACCENT if lvl == "warning" else p.CYAN_ACCENT)
        self.code_badge = QLabel(nfc(report.code or "E-UNKNOWN"), badge_wrap)
        self.code_badge.setFont(mono_font(FS_CAPTION, 700))
        self.code_badge.setStyleSheet(
            f"background: {pill_bg}; color: #FFFFFF; border-radius: 3px; padding: 2px 7px;"
        )
        bw_lay.addWidget(self.code_badge)

        self.report_id_label = QLabel(nfc(f"#{report.report_id}"), badge_wrap)
        self.report_id_label.setFont(mono_font(FS_META, 500))
        self.report_id_label.setStyleSheet("color: #CBD5E1; background: transparent;")
        bw_lay.addWidget(self.report_id_label)
        bw_lay.addStretch(1)
        self.set_header_left_widget(badge_wrap)

        # Decorative Tyrant helper sprite next to × close button (no divider)
        self._helper_avatar = QLabel(self.frame.header_bar)
        self._helper_avatar.setFixedSize(29, 44)
        self.add_header_control(self._helper_avatar)
        self.frame.header_divider.setVisible(False)

        # Scrollable body so 1366x768 & 200% DPI never clip
        self.scroll_area = _BodyScrollArea(self.frame)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setStyleSheet(f"background: {p.PORCELAIN_BG}; border: none;")

        body = QWidget(self.scroll_area)
        body.setStyleSheet(f"background: {p.PORCELAIN_BG};")
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.setSpacing(0)

        # 1. Summary & Numbered Steps Band
        summary_band = QFrame(body)
        summary_band.setObjectName("errSummaryBand")
        summary_band.setStyleSheet(
            f"QFrame#errSummaryBand {{ background: {p.WHITE}; border: none; "
            f"border-bottom: 1px solid {p.HAIRLINE}; }}"
        )
        sb_lay = QVBoxLayout(summary_band)
        sb_lay.setContentsMargins(20, 13, 20, 13)
        sb_lay.setSpacing(6)

        self.summary_label = QLabel(nfc(report.summary or report.message or ""), summary_band)
        self.summary_label.setFont(ui_font(FS_SUBTITLE, 600))
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.summary_label.setStyleSheet(f"color: {p.NAVY_TEXT}; background: transparent;")
        sb_lay.addWidget(self.summary_label)

        if report.steps:
            steps_txt = "\n".join(f"{idx}. {st}" for idx, st in enumerate(report.steps, 1))
            self.steps_label = QLabel(nfc(steps_txt), summary_band)
            self.steps_label.setFont(ui_font(FS_BODY_SM, 400))
            self.steps_label.setWordWrap(True)
            self.steps_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.steps_label.setStyleSheet(f"color: {p.SLATE_BODY}; background: transparent; padding-left: 4px;")
            sb_lay.addWidget(self.steps_label)
        b_lay.addWidget(summary_band)

        # 2. THÔNG TIN KIỂM TRA 3x3 Hairline Table
        diag_section = QWidget(body)
        diag_section.setStyleSheet(f"background: {p.PORCELAIN_BG};")
        ds_lay = QVBoxLayout(diag_section)
        ds_lay.setContentsMargins(20, 12, 20, 6)
        ds_lay.setSpacing(6)

        ds_lay.addWidget(self._make_caption("Thông tin kiểm tra", diag_section))
        self.diag_table = HairlineKeyValueTable(diag_section)
        if self._context_rows:
            self.diag_table.set_diagnostic_rows(self._context_rows)
        ds_lay.addWidget(self.diag_table)

        # Live Async net_probe Panel
        self.probe_panel = QFrame(diag_section)
        self.probe_panel.setObjectName("errProbePanel")
        self.probe_panel.setStyleSheet(
            f"QFrame#errProbePanel {{ background: {p.ICE_ROW_ALT}; border: 1px solid {p.HAIRLINE}; "
            f"border-left: 3px solid {p.CYAN_ACCENT}; }}"
        )
        pp_lay = QVBoxLayout(self.probe_panel)
        pp_lay.setContentsMargins(12, 8, 12, 8)
        pp_lay.setSpacing(3)

        self.probe_verdict_label = QLabel("", self.probe_panel)
        self.probe_verdict_label.setFont(ui_font(FS_BODY_SM, 700))
        self.probe_verdict_label.setWordWrap(True)
        self.probe_verdict_label.setStyleSheet(f"color: {p.NAVY_TEXT}; background: transparent; border: none;")
        pp_lay.addWidget(self.probe_verdict_label)

        self.probe_lines_label = QLabel("", self.probe_panel)
        self.probe_lines_label.setFont(mono_font(11.0, 400))
        self.probe_lines_label.setWordWrap(True)
        self.probe_lines_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.probe_lines_label.setStyleSheet(f"color: {p.SLATE_BODY}; background: transparent; border: none;")
        pp_lay.addWidget(self.probe_lines_label)

        self.probe_panel.setVisible(False)
        ds_lay.addWidget(self.probe_panel)
        b_lay.addWidget(diag_section)

        # 3. CÁCH SỬA ĐỀ XUẤT & THAO TÁC KHÁC (8 canonical quick-fix actions)
        qf_section = QWidget(body)
        qf_section.setStyleSheet(f"background: {p.PORCELAIN_BG};")
        qf_lay = QVBoxLayout(qf_section)
        qf_lay.setContentsMargins(20, 8, 20, 14)
        qf_lay.setSpacing(6)

        qf_lay.addWidget(self._make_caption("Cách sửa đề xuất", qf_section))
        self._primary_grid = QGridLayout()
        self._primary_grid.setContentsMargins(0, 0, 0, 0)
        self._primary_grid.setSpacing(7)
        qf_lay.addLayout(self._primary_grid)

        sec_cap = self._make_caption("Thao tác khác", qf_section)
        sec_cap.setContentsMargins(0, 6, 0, 0)
        qf_lay.addWidget(sec_cap)

        self._secondary_grid = QGridLayout()
        self._secondary_grid.setContentsMargins(0, 0, 0, 0)
        self._secondary_grid.setSpacing(7)
        qf_lay.addLayout(self._secondary_grid)

        self._primary_actions = plan_actions(report.code, ctx)
        self._secondary_actions = secondary_actions(report.code, ctx)
        self._build_action_buttons(qf_section)
        self._reflow_action_grids(2)

        b_lay.addWidget(qf_section)
        self.scroll_area.setWidget(body)
        self.set_body(self.scroll_area)

        # 4. Footer: PII-redacted Copy + Export (.txt/.json) + Đóng
        footer = QWidget(self.frame)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(0, 0, 0, 0)
        f_lay.setSpacing(8)

        self.btn_copy_footer = ActionButton(
            "Sao chép báo lỗi",
            variant="light_secondary",
            icon_path="game/btn_icon_copy.png",
            icon_size=(14, 14),
            icon_tint=p.NAVY_TEXT,
            height=32,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_copy_footer.clicked.connect(self._on_copy_clicked)
        f_lay.addWidget(self.btn_copy_footer)

        self.btn_export_report = ActionButton(
            "Xuất báo cáo (.txt/.json)",
            variant="light_secondary",
            icon_path="game/asar_path_navy.svg",
            icon_size=(14, 14),
            height=32,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_export_report.clicked.connect(self._on_export_clicked)
        f_lay.addWidget(self.btn_export_report)

        f_lay.addStretch(1)

        self.btn_close = ActionButton(
            "Đóng",
            variant="light_secondary",
            height=32,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_close.setMinimumWidth(90)
        self.btn_close.clicked.connect(self.accept)
        f_lay.addWidget(self.btn_close)

        self.set_footer(footer)

        # Show initial probe results if ctx.probe already populated
        if ctx is not None and getattr(ctx, "probe", None):
            self.set_probe_result(ctx.probe)

        self.refresh_dpr()
        self._sync_scroll_geometry()
        self.adjustSize()

    def _make_caption(self, text: str, parent: QWidget) -> QLabel:
        lbl = QLabel(nfc(text).upper(), parent)
        lbl.setFont(ui_font(FS_CAPTION, 700))
        lbl.setStyleSheet(f"color: {PORCELAIN_TOKENS.SLATE_MUTED}; background: transparent;")
        return lbl

    def _build_action_buttons(self, parent: QWidget) -> None:
        for act in self._primary_actions:
            icon_path, icon_tint = _PRIMARY_ICON_MAP.get(act.action_id, ("game/asar_info.svg", None))
            btn = ActionButton(
                act.label,
                variant="navy_solid",
                icon_path=icon_path,
                icon_size=(14, 14),
                icon_tint=icon_tint,
                height=35,
                left_aligned=True,
                asset_renderer=self._renderer,
                parent=parent,
            )
            self._configure_action_button(btn, act)
            self.primary_buttons.append(btn)
            self._action_buttons[act.action_id] = btn

        for act in self._secondary_actions:
            icon_path, icon_tint = _SECONDARY_ICON_MAP.get(act.action_id, ("game/asar_info_navy.svg", None))
            btn = ActionButton(
                act.label,
                variant="light_secondary",
                icon_path=icon_path,
                icon_size=(14, 14),
                icon_tint=icon_tint,
                height=31,
                left_aligned=True,
                asset_renderer=self._renderer,
                parent=parent,
            )
            self._configure_action_button(btn, act)
            self.secondary_buttons.append(btn)
            self._action_buttons[act.action_id] = btn

    def _configure_action_button(self, btn: ActionButton, act: QuickFixAction) -> None:
        if not act.enabled:
            btn.setEnabled(False)
            btn.setToolTip(nfc(act.disabled_reason or act.description))
        elif act.description:
            btn.setToolTip(nfc(act.description))
        btn.clicked.connect(lambda _chk=False, a=act: self._on_quick_fix_clicked(a))

    def _reflow_action_grids(self, cols: int) -> None:
        self._grid_cols = max(1, int(cols))
        for grid, buttons in (
            (self._primary_grid, self.primary_buttons),
            (self._secondary_grid, self.secondary_buttons),
        ):
            while grid.count():
                grid.takeAt(0)
            for c in range(2):
                grid.setColumnStretch(c, 1 if c < self._grid_cols else 0)
            for idx, btn in enumerate(buttons):
                r = idx // self._grid_cols
                c = idx % self._grid_cols
                grid.addWidget(btn, r, c)

    def _on_quick_fix_clicked(self, action: QuickFixAction) -> None:
        if action.action_id == "copy_report":
            self._on_copy_clicked()
            return
        if self._controller is not None and hasattr(self._controller, "execute_quick_fix"):
            self._controller.execute_quick_fix(action, self)

    def _on_copy_clicked(self) -> None:
        text = self.report.text or ""
        copy_text_native(text)
        cb = QGuiApplication.clipboard()
        if cb is not None:
            cb.setText(text)
        self.mark_report_copied()
        if self._controller is not None and hasattr(self._controller, "toast_requested"):
            self._controller.toast_requested.emit(nfc("Đã sao chép gói báo lỗi (đã ẩn thông tin cá nhân)"), "success")

    def mark_report_copied(self) -> None:
        copy_btn = self._action_buttons.get("copy_report")
        if copy_btn is not None:
            copy_btn.setText("Đã sao chép ✓")
        self.btn_copy_footer.setText("Đã sao chép ✓")

    def _on_export_clicked(self) -> None:
        default_name = f"StellaSora_Error_{self.report.code}_{self.report.report_id}.txt"
        dest, selected_filter = QFileDialog.getSaveFileName(
            self,
            nfc("Xuất báo cáo lỗi"),
            default_name,
            nfc("Tệp văn bản (*.txt);;Tệp JSON (*.json)"),
        )
        if not dest:
            return
        fmt = "json" if (dest.lower().endswith(".json") or "JSON" in (selected_filter or "")) else "txt"
        try:
            saved = export_report(self.report, dest, fmt=fmt)
            if self._controller is not None and hasattr(self._controller, "toast_requested"):
                self._controller.toast_requested.emit(nfc(f"Đã xuất báo cáo: {saved.name}"), "success")
        except Exception as exc:  # noqa: BLE001
            if self._controller is not None and hasattr(self._controller, "toast_requested"):
                self._controller.toast_requested.emit(nfc(f"Không xuất được báo cáo: {exc}"), "error")

    def set_probe_running(self) -> None:
        p = PORCELAIN_TOKENS
        self.probe_panel.setStyleSheet(
            f"QFrame#errProbePanel {{ background: {p.ICE_ROW_ALT}; border: 1px solid {p.HAIRLINE}; "
            f"border-left: 3px solid {p.CYAN_ACCENT}; }}"
        )
        self.probe_verdict_label.setText(nfc("Đang kiểm tra kết nối DNS, cổng 443, Captive Portal & TLS..."))
        self.probe_lines_label.setText("")
        self.probe_panel.setVisible(True)
        btn = self._action_buttons.get("probe_network")
        if btn is not None:
            btn.setEnabled(False)
            btn.setText("Đang kiểm tra kết nối...")
        self._sync_scroll_geometry()
        if self.isVisible():
            self.adjustSize()

    def set_probe_result(self, probe: dict[str, Any] | None) -> None:
        p = PORCELAIN_TOKENS
        btn = self._action_buttons.get("probe_network")
        if btn is not None:
            btn.setEnabled(True)
            btn.setText("Kiểm tra kết nối & DNS")

        if not isinstance(probe, dict):
            return

        if self.ctx is not None:
            try:
                self.ctx.probe = probe
            except Exception:  # noqa: BLE001
                pass

        verdict = str(probe.get("verdict") or "")
        verdict_text = str(probe.get("verdict_text") or "")
        dns_val, dns_tone = _PROBE_VERDICT_MAP.get(
            verdict,
            (verdict_text or "Đã kiểm tra kết nối", "ok" if verdict == "ok" else "warn"),
        )

        # Update 'DNS / Kết nối' cell in 3x3 diagnostic grid in-place
        updated = False
        for row in self._context_rows:
            if row.get("label") == "DNS / Kết nối":
                row["value"] = dns_val
                row["tone"] = dns_tone
                updated = True
                break
        if updated and self._context_rows:
            self.diag_table.set_diagnostic_rows(self._context_rows)

        # Update inline probe readout panel
        accent = p.OK_ACCENT if dns_tone == "ok" else (p.WARN_ACCENT if dns_tone == "warn" else p.CORAL_DANGER)
        bg = p.OK_TINT if dns_tone == "ok" else (p.WARN_TINT if dns_tone == "warn" else p.ICE_ROW_ALT)
        self.probe_panel.setStyleSheet(
            f"QFrame#errProbePanel {{ background: {bg}; border: 1px solid {p.HAIRLINE}; "
            f"border-left: 3px solid {accent}; }}"
        )
        self.probe_verdict_label.setText(nfc(verdict_text or dns_val))
        lines = format_probe(probe)
        self.probe_lines_label.setText(nfc("\n".join(lines)))
        self.probe_panel.setVisible(True)
        self._sync_scroll_geometry()
        if self.isVisible():
            self.adjustSize()

    def action_button(self, action_id: str) -> Optional[ActionButton]:
        return self._action_buttons.get(action_id)

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
        target_cols = 1 if clamped_w < 720 else 2
        if target_cols != self._grid_cols:
            self._reflow_action_grids(target_cols)
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
        avatar = self._renderer.get_icon_pixmap("game/playerhead_main_b.png", (29, 44), dpr)
        if not avatar.isNull():
            self._helper_avatar.setPixmap(avatar)
        self.frame.refresh_dpr()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()
