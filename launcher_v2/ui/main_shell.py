# -*- coding: utf-8 -*-
"""
MainShell — Frameless 1200x740 Light Porcelain / Atmospheric HUD shell for Launcher v2.0.

Enforces:
- 3-tier cross-fade background (QPainter master-to-device + AdaptiveScrim, 350ms or 0ms reduced_motion)
- Zero QGraphicsView / QGraphicsBlurEffect (Pillow downscale backdrop blur with solid scrim fallback)
- 42 DIP draggable custom title bar + 44 DIP underline navigation rail (zero pill borders)
- SUPPORT_DONATION_ENABLED=False routing Ủng hộ -> SupportLockedDialog over active screen
- Universal subscreen Close (×) + Esc -> Overview
- Multi-DPI screenChanged + DevicePixelRatioChange invalidation & screen clamping
"""
from __future__ import annotations

import weakref
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QEasingCurve, QEvent, QPoint, QRect, QRectF, QSize, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QMouseEvent, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..core import config as core_config
from ..core.bg_sync import BackgroundFrame, is_reduced_motion
from ..core.config import LAUNCHER_VERSION, ConfigManager, PathManager
from .dialogs import SupportLockedDialog
from .screens import (
    GuideScreen,
    NotificationsScreen,
    OverviewScreen,
    SettingsScreen,
    SupportScreen,
    ToolsScreen,
)
from .theme import (
    FS_BODY,
    FS_BODY_SM,
    FS_CAPTION,
    FS_CTA_SM,
    FS_META,
    FS_MICRO,
    LAYOUT_TOKENS,
    OV_TOKENS,
    PORCELAIN_TOKENS,
    AdaptiveScrimSpec,
    compute_scrim_spec,
    nfc,
    paint_adaptive_scrim,
    rgba_qcolor,
    ui_font,
)
from .widgets import AssetRenderer, ToastBanner, get_asset_renderer


class _ModalBackdropOverlay(QWidget):
    """Translucent scrim + optional Pillow-blurred snapshot behind modal dialogs."""

    def __init__(self, blurred_pixmap: QPixmap, parent: QWidget) -> None:
        super().__init__(parent)
        self._blurred = blurred_pixmap
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setGeometry(parent.rect())

    def set_blurred_pixmap(self, blurred_pixmap: QPixmap) -> None:
        self._blurred = blurred_pixmap
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        if not self._blurred.isNull():
            painter.drawPixmap(QRectF(self.rect()), self._blurred, QRectF(self._blurred.rect()))
        painter.fillRect(self.rect(), rgba_qcolor(PORCELAIN_TOKENS.MODAL_SCRIM_RGBA))
        painter.end()


class _MaximizeGlyphButton(QPushButton):
    """Titlebar maximize/restore button drawing the crisp 10x10px box matching Preview r5."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("", parent)
        self._hovered = False
        self._maximized = False
        self.setFixedSize(30, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setToolTip(nfc("Phóng to"))

    def set_maximized_state(self, maximized: bool) -> None:
        self._maximized = bool(maximized)
        self.setToolTip(nfc("Thu nhỏ lại" if self._maximized else "Phóng to"))
        self.update()

    def enterEvent(self, event) -> None:  # noqa: N802
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self._hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 31))
            painter.drawRoundedRect(QRectF(self.rect()), 4.0, 4.0)

        pen = QPen(QColor("#FFFFFF" if self._hovered else "#CACACA"), 1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        cx = self.width() * 0.5
        cy = self.height() * 0.5
        if self._maximized:
            painter.drawRoundedRect(QRectF(cx - 3.5, cy - 5.5, 8.0, 8.0), 1.2, 1.2)
            painter.drawRoundedRect(QRectF(cx - 5.5, cy - 3.5, 8.0, 8.0), 1.2, 1.2)
        else:
            painter.drawRoundedRect(QRectF(cx - 5.0, cy - 5.0, 10.0, 10.0), 1.5, 1.5)
        painter.end()


class _TitleBarWidget(QWidget):
    """42 DIP draggable custom window title bar with live sync dot & window controls."""

    minimize_requested = Signal()
    maximize_toggle_requested = Signal()
    close_requested = Signal()

    def __init__(self, asset_renderer: AssetRenderer, shell: "MainShell") -> None:
        super().__init__(shell)
        self._renderer = asset_renderer
        self._shell = shell
        self._drag_offset: Optional[QPoint] = None
        self._bg_color = rgba_qcolor(OV_TOKENS.CHROME_LIGHT)

        self.setObjectName("mainTitleBar")
        self.setFixedHeight(LAYOUT_TOKENS.TITLEBAR_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 12, 0)
        lay.setSpacing(8)

        self._icon_label = QLabel(self)
        self._icon_label.setFixedSize(20, 20)
        lay.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.title_label = QLabel(nfc("Stella Sora Việt Hóa"), self)
        self.title_label.setFont(ui_font(FS_CTA_SM, 700))
        self.title_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        lay.addWidget(self.title_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.ver_label = QLabel(nfc(f"v{LAUNCHER_VERSION}"), self)
        self.ver_label.setFont(ui_font(FS_META, 500, tabular=True))
        self.ver_label.setStyleSheet(f"color: {OV_TOKENS.TEXT_MUTED}; background: transparent;")
        lay.addWidget(self.ver_label, 0, Qt.AlignmentFlag.AlignVCenter)

        lay.addStretch(1)

        # Right: Sync status dot + label
        self.sync_dot = QFrame(self)
        self.sync_dot.setFixedSize(7, 7)
        self.sync_dot.setStyleSheet(f"background: {OV_TOKENS.SYNC_DOT}; border-radius: 3px; border: none;")
        lay.addWidget(self.sync_dot, 0, Qt.AlignmentFlag.AlignVCenter)

        self.sync_label = QLabel(nfc("GitHub: Chờ đồng bộ"), self)
        self.sync_label.setFont(ui_font(FS_META, 500))
        self.sync_label.setStyleSheet(f"color: {OV_TOKENS.TEXT_SECONDARY}; background: transparent;")
        lay.addWidget(self.sync_label, 0, Qt.AlignmentFlag.AlignVCenter)

        lay.addSpacing(4)

        # Window controls (30x26, gap 3px)
        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(3)

        self.btn_minimize = QPushButton(self)
        self.btn_minimize.setObjectName("winCtrlBtn")
        self.btn_minimize.setFixedSize(30, 26)
        self.btn_minimize.setFlat(True)
        self.btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_minimize.setToolTip(nfc("Thu nhỏ"))
        self.btn_minimize.setStyleSheet(
            "QPushButton#winCtrlBtn { border: none; border-radius: 4px; background: transparent; }"
            "QPushButton#winCtrlBtn:hover { background: rgba(255, 255, 255, 0.12); }"
        )
        self.btn_minimize.clicked.connect(self.minimize_requested.emit)
        controls.addWidget(self.btn_minimize)

        self.btn_maximize = _MaximizeGlyphButton(self)
        self.btn_maximize.clicked.connect(self.maximize_toggle_requested.emit)
        controls.addWidget(self.btn_maximize)

        self.btn_close = QPushButton(self)
        self.btn_close.setObjectName("winCtrlCloseBtn")
        self.btn_close.setFixedSize(30, 26)
        self.btn_close.setFlat(True)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip(nfc("Đóng"))
        self.btn_close.setStyleSheet(
            "QPushButton#winCtrlCloseBtn { border: none; border-radius: 4px; background: transparent; }"
            f"QPushButton#winCtrlCloseBtn:hover {{ background: {OV_TOKENS.CORAL_DANGER}; }}"
        )
        self.btn_close.clicked.connect(self.close_requested.emit)
        controls.addWidget(self.btn_close)

        lay.addLayout(controls)
        self.refresh_dpr()

    def set_chrome_color(self, color: QColor) -> None:
        self._bg_color = QColor(color)
        self.update()

    def set_sync_status(self, text: str, tone: str = "muted") -> None:
        self.sync_label.setText(nfc(text))
        color = {
            "ok": OV_TOKENS.SYNC_DOT,
            "busy": OV_TOKENS.CYAN_ACCENT,
            "warn": OV_TOKENS.WARN_AMBER,
            "error": OV_TOKENS.CORAL_DANGER,
        }.get(tone, OV_TOKENS.TEXT_MUTED)
        self.sync_dot.setStyleSheet(f"background: {color}; border-radius: 3px; border: none;")

    def refresh_dpr(self) -> None:
        dpr = max(1.0, float(self.devicePixelRatioF()))
        star = self._renderer.get_icon_pixmap("game/zs_common_star_l_2.png", (20, 20), dpr)
        if not star.isNull():
            self._icon_label.setPixmap(star)
        self.btn_minimize.setIcon(self._renderer.get_icon("game/asar_minus.svg", (14, 14), dpr))
        self.btn_minimize.setIconSize(QSize(14, 14))
        self.btn_close.setIcon(self._renderer.get_icon("game/asar_close.svg", (14, 14), dpr))
        self.btn_close.setIconSize(QSize(14, 14))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        r = self.rect()
        painter.fillRect(r, self._bg_color)
        painter.fillRect(0, r.height() - 1, r.width(), 1, QColor(255, 255, 255, 26))
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and not self._shell.isMaximized():
            self._drag_offset = event.globalPosition().toPoint() - self._shell.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_offset is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self._shell.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximize_toggle_requested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class _NavTabButton(QPushButton):
    """Underline-only navigation tab (zero pill borders) with optional unread badge."""

    def __init__(
        self,
        key: str,
        label: str,
        icon_path: str,
        *,
        icon_size: tuple[int, int] = (16, 16),
        with_badge: bool = False,
        asset_renderer: AssetRenderer,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.key = key
        self._base_icon_path = icon_path
        self._icon_size = icon_size
        self._renderer = asset_renderer
        self._active = False
        self._compact = False

        self.setObjectName("navUnderlineTab")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setFixedHeight(LAYOUT_TOKENS.NAV_RAIL_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(13, 0, 13, 0)
        self._lay.setSpacing(7)

        self._icon_lbl = QLabel(self)
        self._icon_lbl.setFixedSize(icon_size[0], icon_size[1])
        self._icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._lay.addWidget(self._icon_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        self._text_lbl = QLabel(nfc(label), self)
        self._text_lbl.setFont(ui_font(13.0, 500))
        self._text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._lay.addWidget(self._text_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        self.badge_label: Optional[QLabel] = None
        if with_badge:
            self.badge_label = QLabel("0", self)
            self.badge_label.setFont(ui_font(FS_MICRO, 700, tabular=True))
            self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.badge_label.setMinimumWidth(18)
            self.badge_label.setFixedHeight(16)
            self.badge_label.setStyleSheet(
                f"background: {OV_TOKENS.CYAN_BADGE_BG}; color: {OV_TOKENS.CYAN_BADGE_TEXT}; "
                f"border-radius: 3px; padding: 0 5px;"
            )
            self.badge_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.badge_label.setVisible(False)
            self._lay.addWidget(self.badge_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self._sync_style()
        self.refresh_dpr()

    def set_active(self, active: bool) -> None:
        self._active = bool(active)
        self._sync_style()
        self.refresh_dpr()
        self.updateGeometry()

    def set_compact(self, compact: bool) -> None:
        self._compact = bool(compact)
        pad_x = 9 if self._compact else 13
        self._lay.setContentsMargins(pad_x, 0, pad_x, 0)
        self._text_lbl.setFont(ui_font(12.0 if self._compact else 13.0, 700 if self._active else 500))
        self.updateGeometry()

    def set_badge_count(self, count: int) -> None:
        if self.badge_label is None:
            return
        n = max(0, int(count))
        self.badge_label.setText(str(n) if n < 100 else "99+")
        self.badge_label.setVisible(n > 0)
        self.updateGeometry()

    def _sync_style(self) -> None:
        border_c = OV_TOKENS.CYAN_ACCENT if self._active else "transparent"
        fg = "#FFFFFF" if self._active else OV_TOKENS.TEXT_SECONDARY
        self._text_lbl.setFont(ui_font(12.0 if self._compact else 13.0, 700 if self._active else 500))
        self._text_lbl.setStyleSheet(f"color: {fg}; background: transparent;")
        self.setStyleSheet(
            f"QPushButton#navUnderlineTab {{ border: none; border-bottom: 3px solid {border_c}; "
            f"border-radius: 0px; background: transparent; }}"
            f"QPushButton#navUnderlineTab:hover {{ background: rgba(255, 255, 255, 0.08); }}"
        )

    def refresh_dpr(self) -> None:
        dpr = max(1.0, float(self.devicePixelRatioF()))
        icon_path = self._base_icon_path
        if self.key == "overview":
            icon_path = "game/icon_stage_home_slc.png" if self._active else "game/icon_stage_home.png"
        pix = self._renderer.get_icon_pixmap(icon_path, self._icon_size, dpr)
        if not pix.isNull():
            self._icon_lbl.setPixmap(pix)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(max(44, self._lay.sizeHint().width()), LAYOUT_TOKENS.NAV_RAIL_HEIGHT)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(max(44, self._lay.minimumSize().width()), LAYOUT_TOKENS.NAV_RAIL_HEIGHT)


class _NavRailWidget(QWidget):
    """44 DIP top navigation rail with underline tabs + right 'Kiểm tra lỗi' trigger."""

    tab_clicked = Signal(str)
    diagnostics_clicked = Signal()

    def __init__(self, asset_renderer: AssetRenderer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._renderer = asset_renderer
        self._bg_color = rgba_qcolor(OV_TOKENS.NAV_LIGHT)
        self.tabs: dict[str, _NavTabButton] = {}

        self.setObjectName("mainNavRail")
        self.setFixedHeight(LAYOUT_TOKENS.NAV_RAIL_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(4)

        specs = [
            ("overview", "Tổng quan", "game/icon_stage_home_slc.png", (16, 16), False),
            ("notifications", "Thông báo", "game/btn_main_system_notice.png", (16, 16), True),
            ("guide", "Hướng dẫn", "game/icon_dict_dictionary.png", (18, 16), False),
            ("support", "Ủng hộ", "game/zs_mainchara_good_opinion.png", (16, 16), False),
            ("settings", "Cài đặt", "game/btn_icon_main_setting.png", (16, 16), False),
            ("tools", "Công cụ", "game/asar_tools.svg", (14, 14), False),
        ]
        for key, label, icon_path, icon_size, with_badge in specs:
            btn = _NavTabButton(
                key,
                label,
                icon_path,
                icon_size=icon_size,
                with_badge=with_badge,
                asset_renderer=self._renderer,
                parent=self,
            )
            btn.clicked.connect(lambda _chk=False, k=key: self.tab_clicked.emit(k))
            lay.addWidget(btn)
            self.tabs[key] = btn

        lay.addStretch(1)

        self.btn_error_assistant = QPushButton(nfc("Kiểm tra lỗi"), self)
        self.btn_error_assistant.setObjectName("navQuickErrorBtn")
        self.btn_error_assistant.setFixedHeight(30)
        self.btn_error_assistant.setFont(ui_font(FS_BODY_SM, 600))
        self.btn_error_assistant.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_error_assistant.setFlat(True)
        self.btn_error_assistant.setToolTip(nfc("Mở trợ lý kiểm tra & sửa lỗi"))
        self.btn_error_assistant.setStyleSheet(
            f"QPushButton#navQuickErrorBtn {{ border: none; border-radius: 4px; "
            f"background: transparent; color: {OV_TOKENS.WARN_AMBER}; padding: 0 8px; }}"
            f"QPushButton#navQuickErrorBtn:hover {{ background: rgba(251, 191, 36, 0.14); "
            f"text-decoration: underline; }}"
        )
        self.btn_error_assistant.clicked.connect(self.diagnostics_clicked.emit)
        lay.addWidget(self.btn_error_assistant, 0, Qt.AlignmentFlag.AlignVCenter)

        self.set_active_tab("overview")
        self.refresh_dpr()

    def set_nav_color(self, color: QColor) -> None:
        self._bg_color = QColor(color)
        self.update()

    def set_active_tab(self, key: str) -> None:
        for k, btn in self.tabs.items():
            btn.set_active(k == key)

    def set_compact(self, compact: bool) -> None:
        for btn in self.tabs.values():
            btn.set_compact(compact)

    def set_unread_count(self, count: int) -> None:
        notif_tab = self.tabs.get("notifications")
        if notif_tab is not None:
            notif_tab.set_badge_count(count)

    def refresh_dpr(self) -> None:
        dpr = max(1.0, float(self.devicePixelRatioF()))
        for btn in self.tabs.values():
            btn.refresh_dpr()
        self.btn_error_assistant.setIcon(
            self._renderer.get_icon("game/zs_stage_warning_icon_s.png", (14, 14), dpr)
        )
        self.btn_error_assistant.setIconSize(QSize(14, 14))

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        r = self.rect()
        painter.fillRect(r, self._bg_color)
        painter.fillRect(0, r.height() - 1, r.width(), 1, QColor(255, 255, 255, 26))
        painter.end()


class MainShell(QMainWindow):
    """Frameless main window shell orchestrating background canvas, nav rail, screens, and modals."""

    diagnostics_requested = Signal()

    def __init__(
        self,
        path_manager: PathManager,
        config_manager: ConfigManager,
        *,
        controller: Any = None,
        software_rendering: bool = False,
        asset_renderer: AssetRenderer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.pm = path_manager
        self.cm = config_manager
        self.controller = controller
        self._software_rendering = bool(software_rendering)
        self._renderer = asset_renderer or get_asset_renderer(self.pm.resource_dir)
        self._screen_hooked = False
        self._initial_clamp_done = False
        self._current_tab = "overview"
        self._active_modal: Optional[QDialog] = None
        self._modal_overlay: Optional[_ModalBackdropOverlay] = None
        self._modal_stack: list[tuple[QDialog, _ModalBackdropOverlay]] = []
        self._reduced_motion_override: Optional[bool] = None

        # Background cross-fade state
        self._current_bg_frame: Optional[BackgroundFrame] = None
        self._scrim_spec: AdaptiveScrimSpec = compute_scrim_spec(None)
        self._prev_bg_pixmap: QPixmap = QPixmap()
        self._next_bg_pixmap: QPixmap = self._renderer.get_master_pixmap("branding/background_native_2048x1451.png")
        self._fade_alpha: float = 1.0
        self._bg_anim = QVariantAnimation(self)
        self._bg_anim.setDuration(0 if self.is_reduced_motion() else 350)
        self._bg_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._bg_anim.valueChanged.connect(self._on_bg_fade_tick)
        self._bg_anim.finished.connect(self._on_bg_fade_finished)

        self.setObjectName("mainShellWindow")
        self.setWindowTitle(nfc(f"Stella Sora Việt Hóa v{LAUNCHER_VERSION}"))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self._apply_window_icon()

        central = QWidget(self)
        central.setObjectName("mainShellCentral")
        central.setAutoFillBackground(False)
        central.setStyleSheet("QWidget#mainShellCentral { background: transparent; }")
        self.setCentralWidget(central)

        root_lay = QVBoxLayout(central)
        root_lay.setContentsMargins(1, 1, 1, 1)
        root_lay.setSpacing(0)

        # 1. Custom 42 DIP Title Bar
        self.title_bar = _TitleBarWidget(self._renderer, self)
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.maximize_toggle_requested.connect(self._toggle_maximize)
        self.title_bar.close_requested.connect(self.close)
        root_lay.addWidget(self.title_bar)

        # 2. Custom 44 DIP Navigation Rail
        self.nav_rail = _NavRailWidget(self._renderer, self)
        self.nav_rail.tab_clicked.connect(self.navigate_to)
        self.nav_rail.diagnostics_clicked.connect(self._on_diagnostics_clicked)
        root_lay.addWidget(self.nav_rail)

        # 3. Modular Screen Stack (instantiated strictly via keyword args matching M5B)
        self.stack = QStackedWidget(central)
        self.stack.setObjectName("mainScreenStack")
        self.stack.setAutoFillBackground(False)
        self.stack.setStyleSheet("QStackedWidget#mainScreenStack { background: transparent; }")

        reduced = self.is_reduced_motion()
        self.overview_screen = OverviewScreen(
            asset_renderer=self._renderer,
            reduced_motion=reduced,
            parent=self.stack,
        )
        self.notifications_screen = NotificationsScreen(
            asset_renderer=self._renderer,
            parent=self.stack,
        )
        self.guide_screen = GuideScreen(
            path_manager=self.pm,
            asset_renderer=self._renderer,
            parent=self.stack,
        )
        self.settings_screen = SettingsScreen(
            path_manager=self.pm,
            config_manager=self.cm,
            asset_renderer=self._renderer,
            parent=self.stack,
        )
        self.tools_screen = ToolsScreen(
            path_manager=self.pm,
            asset_renderer=self._renderer,
            parent=self.stack,
        )
        self.support_screen: Optional[SupportScreen] = None

        self._tab_indices: dict[str, int] = {
            "overview": self.stack.addWidget(self.overview_screen),
            "notifications": self.stack.addWidget(self.notifications_screen),
            "guide": self.stack.addWidget(self.guide_screen),
            "settings": self.stack.addWidget(self.settings_screen),
            "tools": self.stack.addWidget(self.tools_screen),
        }
        if bool(getattr(core_config, "SUPPORT_DONATION_ENABLED", False)):
            self._ensure_support_screen()

        # Universal Close (×) + Esc on every subscreen returns to Overview
        shell_ref = weakref.ref(self)
        for sub in (
            self.notifications_screen,
            self.guide_screen,
            self.settings_screen,
            self.tools_screen,
        ):
            sub.close_requested.connect(
                lambda r=shell_ref: r().navigate_to("overview") if r() is not None else None
            )

        root_lay.addWidget(self.stack, 1)

        # 4. Non-blocking ToastBanner overlay
        self.toast_banner = ToastBanner(self, reduced_motion=reduced)

        self._apply_scrim_colors()
        self._clamp_to_screen(initial=True)

    def _apply_window_icon(self) -> None:
        for rel in ("branding/app_icon.ico", "branding/app_icon.png"):
            p = self._renderer.resolve_path(rel)
            if p.is_file():
                self.setWindowIcon(QIcon(str(p)))
                return

    def _ensure_support_screen(self) -> SupportScreen:
        if self.support_screen is None:
            self.support_screen = SupportScreen(
                path_manager=self.pm,
                asset_renderer=self._renderer,
                parent=self.stack,
            )
            shell_ref = weakref.ref(self)
            self.support_screen.close_requested.connect(
                lambda r=shell_ref: r().navigate_to("overview") if r() is not None else None
            )
            self.support_screen.toast_requested.connect(self.show_toast)
            self._tab_indices["support"] = self.stack.addWidget(self.support_screen)
        return self.support_screen

    def is_reduced_motion(self) -> bool:
        if self._reduced_motion_override is not None:
            return bool(self._reduced_motion_override)
        try:
            return is_reduced_motion(self.cm.data)
        except Exception:  # noqa: BLE001
            return bool(self.cm.get("reduced_motion", False))

    def is_noblur_mode(self) -> bool:
        try:
            gm = str(self.cm.get("graphics_mode", "auto") or "auto").lower()
            return gm in ("software", "noblur")
        except Exception:  # noqa: BLE001
            return False

    def set_reduced_motion(self, enabled: bool) -> None:
        eff = bool(enabled)
        self._reduced_motion_override = eff
        self._bg_anim.setDuration(0 if eff else 350)
        self.overview_screen.set_reduced_motion(eff)
        self.toast_banner.set_reduced_motion(eff)

    def set_controller(self, controller: Any) -> None:
        self.controller = controller

    def _on_diagnostics_clicked(self) -> None:
        self.diagnostics_requested.emit()
        if self.controller is not None and hasattr(self.controller, "open_diagnostics_dialog"):
            self.controller.open_diagnostics_dialog()

    def navigate_to(self, tab_key: str, *, notification_id: Optional[str] = None) -> None:
        key = (tab_key or "overview").strip().lower()
        if key == "support":
            if not bool(getattr(core_config, "SUPPORT_DONATION_ENABLED", False)):
                self.show_support_locked_dialog()
                return
            self._ensure_support_screen()
            if self.controller is not None and hasattr(self.controller, "is_busy") and self.controller.is_busy():
                pass

        if key in ("settings", "tools") and self.controller is not None:
            busy_fn = getattr(self.controller, "is_mutating_busy", None) or getattr(self.controller, "is_busy", None)
            if callable(busy_fn) and busy_fn():
                self.show_toast("Đang có thao tác chạy; vui lòng đợi hoàn tất.", tone="warn")
                return

        if key == "settings":
            self.settings_screen.refresh_from_config()
            if self._current_bg_frame is not None:
                self.settings_screen.set_bg_frame(self._current_bg_frame)
        elif key == "tools":
            self.tools_screen.refresh_live_metrics()
        elif key == "notifications" and notification_id is not None:
            self.notifications_screen.select_notification(notification_id)

        idx = self._tab_indices.get(key)
        if idx is None:
            key = "overview"
            idx = self._tab_indices["overview"]

        self._current_tab = key
        self.stack.setCurrentIndex(idx)
        self.nav_rail.set_active_tab(key)
        self._forward_compact_layout()
        self.stack.update()
        self.update()

    def current_tab(self) -> str:
        return self._current_tab

    def show_support_locked_dialog(self) -> int:
        dlg = SupportLockedDialog(asset_renderer=self._renderer, parent=self)
        return self.show_modal(dlg)

    def set_background_frame(self, frame: BackgroundFrame) -> None:
        self._current_bg_frame = frame
        self._scrim_spec = compute_scrim_spec(frame)
        self._apply_scrim_colors()

        img_path: Optional[Path] = None
        if frame.is_video and frame.still_fallback_path is not None and Path(frame.still_fallback_path).is_file():
            img_path = Path(frame.still_fallback_path)
        elif frame.image_path is not None and Path(frame.image_path).is_file():
            img_path = Path(frame.image_path)

        next_pix = (
            self._renderer.get_master_pixmap(img_path)
            if img_path is not None
            else self._renderer.get_master_pixmap("branding/background_native_2048x1451.png")
        )
        if next_pix.isNull():
            next_pix = self._renderer.get_master_pixmap("branding/background_native_2048x1451.png")

        self.settings_screen.set_bg_frame(frame)

        if (
            not self._next_bg_pixmap.isNull()
            and next_pix.cacheKey() == self._next_bg_pixmap.cacheKey()
            and self._fade_alpha >= 1.0
        ):
            self.update()
            return

        if self.is_reduced_motion() or self._next_bg_pixmap.isNull():
            self._bg_anim.stop()
            self._prev_bg_pixmap = QPixmap()
            self._next_bg_pixmap = next_pix
            self._fade_alpha = 1.0
            self.update()
            return

        self._bg_anim.stop()
        self._prev_bg_pixmap = self._next_bg_pixmap
        self._next_bg_pixmap = next_pix
        self._fade_alpha = 0.0
        self._bg_anim.setDuration(350)
        self._bg_anim.setStartValue(0.0)
        self._bg_anim.setEndValue(1.0)
        self._bg_anim.start()

    def _on_bg_fade_tick(self, value) -> None:
        self._fade_alpha = float(value)
        self.update()

    def _on_bg_fade_finished(self) -> None:
        self._fade_alpha = 1.0
        self._prev_bg_pixmap = QPixmap()
        self.update()

    def _apply_scrim_colors(self) -> None:
        self.title_bar.set_chrome_color(self._scrim_spec.chrome_fill)
        self.nav_rail.set_nav_color(self._scrim_spec.nav_fill)
        self.overview_screen.apply_scrim_spec(self._scrim_spec)

    def show_toast(self, message: str, tone: str = "success", duration_ms: int = 2600) -> None:
        self.toast_banner.show_message(message, tone=tone, duration_ms=duration_ms)

    def show_modal(self, dialog: QDialog) -> int:
        area = (self.screen() or QGuiApplication.primaryScreen()).availableGeometry()
        if hasattr(dialog, "compact_layout"):
            dialog.compact_layout(area.width(), area.height())

        # Clamp dialog size inside available screen geometry
        max_w = max(320, area.width() - 32)
        max_h = max(240, area.height() - 32)
        dialog.adjustSize()
        d_w = min(dialog.width(), max_w)
        d_h = min(dialog.height(), max_h)
        dialog.resize(d_w, d_h)

        # Center over shell, clamped within available screen geometry
        shell_center = self.frameGeometry().center() if self.isVisible() else area.center()
        x = max(area.left() + 8, min(shell_center.x() - d_w // 2, area.right() - d_w - 8))
        y = max(area.top() + 8, min(shell_center.y() - d_h // 2, area.bottom() - d_h - 8))
        dialog.move(x, y)

        focused = self.focusWidget()

        # Pillow downscale backdrop blur (automatically skipped when reduced_motion/noblur/software_rendering)
        blur_pix = QPixmap()
        if (
            self.isVisible()
            and not self._software_rendering
            and not self.is_reduced_motion()
            and not self.is_noblur_mode()
        ):
            try:
                snap = self.grab()
                blur_pix = self._renderer.blur_backdrop_pixmap(
                    snap,
                    radius=8,
                    reduced_motion=False,
                    software_rendering=False,
                )
            except Exception:  # noqa: BLE001
                blur_pix = QPixmap()

        overlay = _ModalBackdropOverlay(blur_pix, self)
        self._modal_stack.append((dialog, overlay))
        self._modal_overlay = overlay
        self._active_modal = dialog
        overlay.show()
        overlay.raise_()
        try:
            return int(dialog.exec())
        finally:
            if self._modal_stack and self._modal_stack[-1][0] is dialog:
                self._modal_stack.pop()
            else:
                self._modal_stack = [(d, o) for d, o in self._modal_stack if d is not dialog]
            if self._modal_stack:
                outer_dlg, outer_ov = self._modal_stack[-1]
                self._active_modal = outer_dlg
                self._modal_overlay = outer_ov
            else:
                self._active_modal = None
                self._modal_overlay = None
            overlay.hide()
            overlay.deleteLater()
            if not self._modal_stack and focused is not None:
                try:
                    focused.setFocus()
                except RuntimeError:
                    pass

    def show_unhandled(self, exc: BaseException) -> None:
        if self.controller is not None and hasattr(self.controller, "show_unhandled"):
            self.controller.show_unhandled(exc)

    def _toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
            self.title_bar.btn_maximize.set_maximized_state(False)
        else:
            self.showMaximized()
            self.title_bar.btn_maximize.set_maximized_state(True)

    def _clamp_to_screen(self, screen=None, *, initial: bool = False) -> None:
        if self.isMaximized() or self.isFullScreen():
            return
        scr = screen or self.screen() or QGuiApplication.primaryScreen()
        if scr is None:
            return
        area = scr.availableGeometry()
        max_w = max(320, area.width() - 16)
        max_h = max(280, area.height() - 16)
        min_w = min(900, max_w)
        min_h = min(520, max_h)
        self.setMinimumSize(min_w, min_h)

        if initial or not self._initial_clamp_done:
            w = min(LAYOUT_TOKENS.DEFAULT_WIN_W, max_w)
            h = min(LAYOUT_TOKENS.DEFAULT_WIN_H, max_h)
            self._initial_clamp_done = True
            self.resize(w, h)
            self.move(
                area.left() + max(0, (area.width() - w) // 2),
                area.top() + max(0, (area.height() - h) // 2),
            )
        else:
            w = max(min_w, min(self.width(), max_w))
            h = max(min_h, min(self.height(), max_h))
            self.resize(w, h)
            x = max(area.left(), min(self.x(), area.right() - w + 1))
            y = max(area.top(), min(self.y(), area.bottom() - h + 1))
            self.move(x, y)

        self._forward_compact_layout()

    def _forward_compact_layout(self) -> None:
        w = max(1, self.width())
        h = max(1, self.height())
        compact = (
            w < LAYOUT_TOKENS.COMPACT_WIDTH_THRESHOLD
            or h < LAYOUT_TOKENS.COMPACT_HEIGHT_THRESHOLD
        )
        self.nav_rail.set_compact(compact)

        body_w = max(280, w - 2)
        body_h = max(200, h - LAYOUT_TOKENS.TITLEBAR_HEIGHT - LAYOUT_TOKENS.NAV_RAIL_HEIGHT - 2)
        for scr in (
            self.overview_screen,
            self.notifications_screen,
            self.guide_screen,
            self.settings_screen,
            self.tools_screen,
            self.support_screen,
        ):
            if scr is not None and hasattr(scr, "compact_layout"):
                scr.compact_layout(body_w, body_h)

        modals = [d for d, _ov in self._modal_stack] or (
            [self._active_modal] if self._active_modal is not None else []
        )
        if modals:
            scr_obj = self.screen() or QGuiApplication.primaryScreen()
            if scr_obj is not None:
                avail = scr_obj.availableGeometry()
                for dlg in modals:
                    if hasattr(dlg, "compact_layout"):
                        dlg.compact_layout(avail.width(), avail.height())

    def _on_screen_changed(self, screen) -> None:
        self._renderer.invalidate_dpi_cache()
        self._clamp_to_screen(screen, initial=False)
        self._refresh_all_dpr()

    def _refresh_all_dpr(self) -> None:
        self.title_bar.refresh_dpr()
        self.nav_rail.refresh_dpr()
        for scr in (
            self.overview_screen,
            self.notifications_screen,
            self.guide_screen,
            self.settings_screen,
            self.tools_screen,
            self.support_screen,
        ):
            if scr is not None and hasattr(scr, "refresh_dpr"):
                scr.refresh_dpr()
        modals = [d for d, _ov in self._modal_stack] or (
            [self._active_modal] if self._active_modal is not None else []
        )
        for dlg in modals:
            if hasattr(dlg, "refresh_dpr"):
                dlg.refresh_dpr()
        self.update()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if not self._screen_hooked and self.windowHandle() is not None:
            self.windowHandle().screenChanged.connect(self._on_screen_changed)
            self._screen_hooked = True

    def event(self, event) -> bool:  # noqa: N802
        result = super().event(event)
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self._renderer.invalidate_dpi_cache()
            self._refresh_all_dpr()
            self._forward_compact_layout()
        return result

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._forward_compact_layout()
        for _dlg, ov in self._modal_stack:
            ov.setGeometry(self.rect())
        if self._modal_overlay is not None and all(ov is not self._modal_overlay for _d, ov in self._modal_stack):
            self._modal_overlay.setGeometry(self.rect())
        if self.toast_banner.isVisible():
            self.toast_banner.reposition()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if (
            event.key() == Qt.Key.Key_Escape
            and not self._modal_stack
            and self._active_modal is None
            and self._current_tab != "overview"
        ):
            self.navigate_to("overview")
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        rect = QRectF(self.rect())
        painter.fillRect(rect, QColor(OV_TOKENS.WINDOW_BG))

        paint_zoom = self._scrim_spec.hero_zoom
        paint_focus = self._scrim_spec.hero_focus
        if paint_zoom > 1.0:
            paint_zoom = max(paint_zoom, 1.18)
            paint_focus = (max(paint_focus[0], 0.92), max(paint_focus[1], 0.98))

        if not self._prev_bg_pixmap.isNull() and self._fade_alpha < 1.0:
            painter.save()
            painter.setOpacity(max(0.0, 1.0 - self._fade_alpha))
            self._renderer.paint_cover(
                painter,
                rect,
                self._prev_bg_pixmap,
                focus=paint_focus,
                zoom=paint_zoom,
            )
            painter.restore()

        if not self._next_bg_pixmap.isNull():
            painter.save()
            painter.setOpacity(max(0.0, min(1.0, self._fade_alpha)))
            self._renderer.paint_cover(
                painter,
                rect,
                self._next_bg_pixmap,
                focus=paint_focus,
                zoom=paint_zoom,
            )
            painter.restore()

        paint_adaptive_scrim(painter, rect, self._scrim_spec)

        # Crisp 1px outer window border
        pen = QPen(rgba_qcolor(OV_TOKENS.WINDOW_BORDER_RGBA), 1.0)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))
        painter.end()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.controller is not None:
            busy_fn = getattr(self.controller, "is_mutating_busy", None)
            mutating_busy = (
                bool(busy_fn())
                if callable(busy_fn)
                else (getattr(self.controller, "active_worker", None) is not None)
            )
            if mutating_busy:
                self.overview_screen.set_operation_active(
                    True,
                    cancellable=True,
                    initial_message="Đang có thao tác chạy. Hãy chờ hoàn tất hoặc bấm Hủy trước khi đóng.",
                )
                self.show_toast("Đang có thao tác chạy; vui lòng chờ hoàn tất.", tone="warn")
                event.ignore()
                return
            if hasattr(self.controller, "defer_close_for_background") and self.controller.defer_close_for_background():
                self.hide()
                event.ignore()
                return

        self._bg_anim.stop()
        self.tools_screen.shutdown_workers()
        if self.controller is not None and hasattr(self.controller, "shutdown_workers"):
            self.controller.shutdown_workers()
        event.accept()
