# -*- coding: utf-8 -*-
"""
GameSelectionDialog — Light Porcelain multi-client & wrong-folder hint modal.

Matches Preview r5 (#modal-game-selection):
- 760px target width
- #264278 Navy header with playerhead_main_bbb.png, title & discovered count, far-right × + Esc
- Conditional #FFF8E1 left-amber-accented wrong-folder hint banner with 'Dùng thư mục này'
- Unified hairline radio list inspecting Steam (AppID 4813850) / Yostar installs via GameDetector
- Footer with 'Chọn thủ công...', 'Hủy', 'Chọn bản này'
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...core.game_detection import STELLA_SORA_STEAM_APP_ID, GameDetector
from ...core.types import GameInfo
from ..theme.tokens import PORCELAIN_TOKENS
from ..theme.typography import FS_BODY, FS_META, mono_font, nfc, ui_font
from ..widgets import (
    AccentBannerStrip,
    ActionButton,
    AssetRenderer,
    PlatformTag,
    PorcelainDialog,
    StatusInline,
    get_asset_renderer,
)


class _RadioIndicator(QWidget):
    """Crisp custom-painted 17x17 radio circle matching Preview r5 .gi-radio."""

    def __init__(self, selected: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected = bool(selected)
        self.setFixedSize(19, 19)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_selected(self, selected: bool) -> None:
        self._selected = bool(selected)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = PORCELAIN_TOKENS
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        cx = self.width() * 0.5
        cy = self.height() * 0.5
        border = QColor(p.CYAN_ACCENT if self._selected else "#94A3B8")
        pen = QPen(border, 2.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(int(cx - 7.5), int(cy - 7.5), 15, 15)
        if self._selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(p.CYAN_ACCENT))
            painter.drawEllipse(int(cx - 4.5), int(cy - 4.5), 9, 9)
        painter.end()


class _GameInstallRow(QPushButton):
    """Unified hairline installation row with #D7F1F6 + 3px #12B8C4 selection bar."""

    row_clicked = Signal(str)
    row_double_clicked = Signal(str)

    def __init__(
        self,
        entry: dict[str, Any],
        info: GameInfo,
        *,
        is_last: bool,
        asset_renderer: AssetRenderer,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self._path_str = str(entry.get("path") or "")
        self._is_last = bool(is_last)
        self._selected = False

        self.setObjectName("gameInstallRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(15, 12, 15, 12)
        lay.setSpacing(12)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(4)

        badges = QHBoxLayout()
        badges.setContentsMargins(0, 0, 0, 0)
        badges.setSpacing(7)

        self._emblem = QLabel(self)
        self._emblem.setFixedSize(16, 16)
        self._emblem.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        badges.addWidget(self._emblem, 0, Qt.AlignmentFlag.AlignVCenter)

        plat_raw = str(entry.get("platform") or info.platform or "standalone").lower()
        is_steam = plat_raw == "steam"
        self.platform_tag = PlatformTag("Steam" if is_steam else "Yostar", surface="light", parent=self)
        self.platform_tag.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        badges.addWidget(self.platform_tag, 0, Qt.AlignmentFlag.AlignVCenter)

        ver = info.version if info.version and info.version != "unknown" else "Chưa rõ"
        res = info.resource_version if info.resource_version and info.resource_version != "unknown" else "—"
        sub_txt = f"AppID {STELLA_SORA_STEAM_APP_ID}" if is_steam else "Bản chính thức"
        ver_lbl = QLabel(nfc(f"{sub_txt} · {ver} · Res {res}"), self)
        ver_lbl.setFont(ui_font(FS_META, 500, tabular=True))
        ver_lbl.setStyleSheet(f"color: {PORCELAIN_TOKENS.SLATE_MUTED}; background: transparent;")
        ver_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        badges.addWidget(ver_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        if info.has_vietnamese:
            vv = info.vietnamese_version or ""
            patch_lbl = f"Đã cài {vv}".strip() if vv.startswith("v") else (f"Đã cài v{vv}" if vv else "Đã cài Việt hoá")
            patch_tone = "ok"
        elif info.receipt_stale:
            patch_lbl = "Cần cài lại"
            patch_tone = "warn"
        elif info.official_restore:
            patch_lbl = "Bản gốc EN"
            patch_tone = "muted"
        else:
            patch_lbl = "Bản gốc EN"
            patch_tone = "muted"

        self.patch_badge = StatusInline(
            patch_lbl,
            tone=patch_tone,
            surface="light",
            asset_renderer=self._renderer,
            parent=self,
        )
        self.patch_badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        badges.addWidget(self.patch_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        badges.addStretch(1)
        left_col.addLayout(badges)

        path_lbl = QLabel(nfc(self._path_str), self)
        path_lbl.setFont(mono_font(FS_BODY, 600))
        path_lbl.setWordWrap(True)
        path_lbl.setStyleSheet(f"color: {PORCELAIN_TOKENS.NAVY_TEXT}; background: transparent;")
        path_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        left_col.addWidget(path_lbl)
        lay.addLayout(left_col, 1)

        self.radio = _RadioIndicator(False, self)
        lay.addWidget(self.radio, 0, Qt.AlignmentFlag.AlignVCenter)

        self.clicked.connect(lambda: self.row_clicked.emit(self._path_str))
        self.refresh_dpr()
        self._apply_style()

    def path_str(self) -> str:
        return self._path_str

    def set_selected(self, selected: bool) -> None:
        self._selected = bool(selected)
        self.radio.set_selected(self._selected)
        self._apply_style()

    def _apply_style(self) -> None:
        p = PORCELAIN_TOKENS
        bg = p.ICE_SELECTED if self._selected else p.WHITE
        left_c = p.CYAN_ACCENT if self._selected else "transparent"
        bottom = "none" if self._is_last else f"1px solid {p.HAIRLINE_CELL}"
        self.setStyleSheet(
            f"QPushButton#gameInstallRow {{ background: {bg}; border: none; "
            f"border-left: 3px solid {left_c}; border-bottom: {bottom}; "
            f"border-radius: 0px; text-align: left; }}"
            f"QPushButton#gameInstallRow:hover {{ background: {p.ICE_SELECTED if self._selected else p.ICE_HOVER}; }}"
        )

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        super().mouseDoubleClickEvent(event)
        self.row_double_clicked.emit(self._path_str)

    def refresh_dpr(self) -> None:
        dpr = max(1.0, float(self.devicePixelRatioF()))
        pix = self._renderer.get_icon_pixmap("game/zs_agent_logo_1.png", (16, 16), dpr)
        if not pix.isNull():
            self._emblem.setPixmap(pix)

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        lay = self.layout()
        return lay.hasHeightForWidth() if lay is not None else False

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        lay = self.layout()
        if lay is not None and lay.hasHeightForWidth():
            return max(48, lay.heightForWidth(width))
        return max(48, self.sizeHint().height())

    def sizeHint(self) -> QSize:  # noqa: N802
        lay = self.layout()
        if lay is not None:
            sh = lay.sizeHint()
            return QSize(max(240, sh.width()), max(48, sh.height()))
        return QSize(320, 56)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        lay = self.layout()
        if lay is not None:
            sh = lay.minimumSize()
            return QSize(max(180, sh.width()), max(48, sh.height()))
        return QSize(180, 48)


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


class GameSelectionDialog(PorcelainDialog):
    """Modal dialog for choosing among Steam/Yostar installs or accepting a wrong-folder hint."""

    def __init__(
        self,
        installations: list[dict[str, Any]],
        parent: QWidget | None = None,
        *,
        wrong_path: str | Path | None = None,
        hint_path: str | Path | None = None,
        backup_root: str | Path | None = None,
        asset_renderer: AssetRenderer | None = None,
    ) -> None:
        self._renderer = asset_renderer or get_asset_renderer()
        self._installations = list(installations or [])
        self._wrong_path = str(wrong_path) if wrong_path else ""
        self._hint_path = str(hint_path) if hint_path else ""
        self.selected_path: Optional[str] = (
            str(self._installations[0]["path"]) if self._installations else (self._hint_path or None)
        )
        self.manual_selected: bool = False
        self._rows: list[_GameInstallRow] = []
        self._list_scroll: Optional[QScrollArea] = None

        count = len(self._installations)
        if count > 0:
            meta_txt = f"Tìm thấy {count} bản cài trên máy (Yostar & Steam)"
        elif self._hint_path:
            meta_txt = "Thư mục đã chọn không chứa StellaSora.exe"
        else:
            meta_txt = "Chọn thư mục chứa StellaSora.exe"

        super().__init__(
            title="Chọn bản cài Stella Sora",
            meta=meta_txt,
            icon_path="game/playerhead_main_bbb.png",
            icon_size=(28, 42),
            target_width=PORCELAIN_TOKENS.MODAL_WIDTH_GAME_SELECT,
            asset_renderer=self._renderer,
            parent=parent,
        )
        self.setObjectName("gameSelectionDialog")
        p = PORCELAIN_TOKENS

        self._body_scroll = _BodyScrollArea(self.frame)
        self._body_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._body_scroll.setWidgetResizable(True)
        self._body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._body_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._body_scroll.setStyleSheet(f"background: {p.PORCELAIN_BG}; border: none;")

        body = QWidget(self._body_scroll)
        body.setStyleSheet(f"background: {p.PORCELAIN_BG};")
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(0, 0, 0, 0)
        b_lay.setSpacing(0)

        # Conditional Wrong-Folder Hint Banner
        self.hint_banner: Optional[AccentBannerStrip] = None
        if self._hint_path:
            wrong_txt = self._wrong_path or "(thư mục vừa chọn)"
            self.hint_banner = AccentBannerStrip(
                "Bạn đã chọn nhầm thư mục:",
                f"Thư mục {wrong_txt} không có StellaSora.exe. Đổi sang thư mục gốc {self._hint_path}?",
                tone="warn",
                icon_path="game/asar_info_navy.svg",
                asset_renderer=self._renderer,
                parent=body,
            )
            self.btn_accept_hint = ActionButton(
                "Dùng thư mục này",
                variant="navy_solid",
                height=30,
                asset_renderer=self._renderer,
                parent=self.hint_banner,
            )
            self.btn_accept_hint.clicked.connect(self._on_accept_hint)
            self.hint_banner.set_right_widget(self.btn_accept_hint)
            b_lay.addWidget(self.hint_banner)

        list_wrap = QWidget(body)
        list_wrap.setStyleSheet(f"background: {p.PORCELAIN_BG};")
        lw_lay = QVBoxLayout(list_wrap)
        lw_lay.setContentsMargins(18, 14, 18, 14)
        lw_lay.setSpacing(0)

        table_frame = QFrame(list_wrap)
        table_frame.setObjectName("gameInstallTableFrame")
        table_frame.setStyleSheet(
            f"QFrame#gameInstallTableFrame {{ background: {p.WHITE}; "
            f"border: 1px solid {p.HAIRLINE_STRONG}; border-radius: 4px; }}"
        )
        tf_lay = QVBoxLayout(table_frame)
        tf_lay.setContentsMargins(1, 1, 1, 1)
        tf_lay.setSpacing(0)

        detector_root = (
            Path(backup_root)
            if backup_root
            else (Path(self._installations[0]["path"]) if self._installations else Path.cwd())
        )
        detector = GameDetector(detector_root)

        if self._installations:
            scroll = _BodyScrollArea(table_frame)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setStyleSheet(f"background: {p.WHITE}; border: none;")
            self._list_scroll = scroll

            rows_host = QWidget(scroll)
            rows_host.setStyleSheet(f"background: {p.WHITE};")
            rh_lay = QVBoxLayout(rows_host)
            rh_lay.setContentsMargins(0, 0, 0, 0)
            rh_lay.setSpacing(0)

            for idx, entry in enumerate(self._installations):
                try:
                    info = detector.detect_info(entry["path"])
                except Exception:  # noqa: BLE001
                    info = GameInfo(installed=True, game_path=Path(str(entry["path"])))
                row = _GameInstallRow(
                    entry,
                    info,
                    is_last=(idx == len(self._installations) - 1),
                    asset_renderer=self._renderer,
                    parent=rows_host,
                )
                row.row_clicked.connect(self._select_path)
                row.row_double_clicked.connect(self._select_and_accept)
                rh_lay.addWidget(row)
                self._rows.append(row)

            scroll.setWidget(rows_host)
            if len(self._installations) > 4:
                scroll.setFixedHeight(310)
            else:
                scroll.setMinimumHeight(min(280, max(74, len(self._installations) * 74)))
            tf_lay.addWidget(scroll)
        else:
            empty_lbl = QLabel(
                nfc("Không tìm thấy bản cài đặt nào tự động. Bạn có thể chọn thư mục thủ công bên dưới."),
                table_frame,
            )
            empty_lbl.setFont(ui_font(FS_BODY, 500))
            empty_lbl.setWordWrap(True)
            empty_lbl.setStyleSheet(f"color: {p.SLATE_MUTED}; padding: 16px;")
            tf_lay.addWidget(empty_lbl)

        lw_lay.addWidget(table_frame)
        b_lay.addWidget(list_wrap)
        self._body_scroll.setWidget(body)
        self.set_body(self._body_scroll)

        # Footer
        footer = QWidget(self.frame)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(0, 0, 0, 0)
        f_lay.setSpacing(8)

        self.btn_manual = ActionButton(
            "Chọn thủ công...",
            variant="light_secondary",
            icon_path="game/asar_path_navy.svg",
            icon_size=(14, 14),
            height=32,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_manual.clicked.connect(self._on_manual_browse)
        f_lay.addWidget(self.btn_manual)
        f_lay.addStretch(1)

        self.btn_cancel = ActionButton(
            "Hủy",
            variant="light_secondary",
            height=32,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_cancel.clicked.connect(self.reject)
        f_lay.addWidget(self.btn_cancel)

        self.btn_confirm = ActionButton(
            "Chọn bản này",
            variant="light_cyan",
            height=32,
            asset_renderer=self._renderer,
            parent=footer,
        )
        self.btn_confirm.setEnabled(bool(self.selected_path))
        self.btn_confirm.setDefault(True)
        self.btn_confirm.clicked.connect(self.accept)
        f_lay.addWidget(self.btn_confirm)

        self.set_footer(footer)
        if self._rows:
            self._select_path(self._rows[0].path_str())
        self._sync_scroll_geometry()
        self.adjustSize()

    def _select_path(self, path_str: str) -> None:
        self.selected_path = path_str
        for row in self._rows:
            row.set_selected(row.path_str() == path_str)
        self.btn_confirm.setEnabled(bool(self.selected_path))

    def _select_and_accept(self, path_str: str) -> None:
        self._select_path(path_str)
        self.accept()

    def _on_accept_hint(self) -> None:
        if self._hint_path:
            self.selected_path = self._hint_path
            self.accept()

    def _on_manual_browse(self) -> None:
        start = self.selected_path or self._hint_path or "C:/"
        chosen = QFileDialog.getExistingDirectory(self, nfc("Chọn thư mục có StellaSora.exe"), start)
        if chosen:
            self.selected_path = chosen
            self.manual_selected = True
            self.accept()

    def _sync_scroll_geometry(self) -> None:
        if self._list_scroll is not None:
            _activate_subtree_layouts(self._list_scroll.widget())
            self._list_scroll.updateGeometry()
        _activate_subtree_layouts(self._body_scroll.widget())
        self._body_scroll.updateGeometry()
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
            if self._list_scroll is not None and self._installations:
                count = len(self._installations)
                desktop_h = 310 if count > 4 else min(280, max(74, count * 74))
                content_w = max(240, clamped_w - 2)
                header_h = max(48, self.frame.header_bar.sizeHint().height())
                footer_h = max(52, self.frame.footer_container.sizeHint().height())
                hint_h = 0
                if self.hint_banner is not None:
                    hint_h = (
                        self.hint_banner.heightForWidth(content_w)
                        if self.hint_banner.hasHeightForWidth()
                        else self.hint_banner.sizeHint().height()
                    )
                    if hint_h <= 0:
                        hint_h = self.hint_banner.sizeHint().height()
                overhead = header_h + footer_h + hint_h + 32
                avail_for_scroll = max_h - overhead
                if avail_for_scroll >= desktop_h:
                    if count > 4:
                        self._list_scroll.setFixedHeight(310)
                    else:
                        self._list_scroll.setMinimumHeight(desktop_h)
                        self._list_scroll.setMaximumHeight(16777215)
                else:
                    target_scroll_h = max(84, min(desktop_h, avail_for_scroll))
                    self._list_scroll.setFixedHeight(target_scroll_h)
            self._sync_scroll_geometry()
            self.adjustSize()
            if self.height() > max_h:
                self.resize(self.width(), max_h)
        else:
            self.setMaximumHeight(16777215)
            if self._list_scroll is not None and self._installations:
                count = len(self._installations)
                desktop_h = 310 if count > 4 else min(280, max(74, count * 74))
                if count > 4:
                    self._list_scroll.setFixedHeight(310)
                else:
                    self._list_scroll.setMinimumHeight(desktop_h)
                    self._list_scroll.setMaximumHeight(16777215)
            self._sync_scroll_geometry()
            self.adjustSize()

    def refresh_dpr(self) -> None:
        self.frame.refresh_dpr()
        for row in self._rows:
            row.refresh_dpr()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.refresh_dpr()
