"""Asset management and caching for Stella Sora Launcher."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPixmap

logger = logging.getLogger("launcher.assets")


class AssetManager:
    """Loads, caches, and provides UI pixmaps, icons, and theme tokens."""

    _instance: Optional[AssetManager] = None

    def __init__(self, resource_dir: Path):
        self.resource_dir = resource_dir
        if (resource_dir / "ui").exists():
            self.ui_dir = resource_dir / "ui"
            self.branding_dir = resource_dir / "branding"
        elif (resource_dir / "resources" / "ui").exists():
            self.ui_dir = resource_dir / "resources" / "ui"
            self.branding_dir = resource_dir / "resources" / "branding"
        else:
            self.ui_dir = resource_dir
            self.branding_dir = resource_dir

        self._pixmap_cache: Dict[str, QPixmap] = {}
        self._icon_cache: Dict[str, QIcon] = {}
        self.tokens: dict = {}
        self._load_tokens()

    @classmethod
    def initialize(cls, resource_dir: Path) -> AssetManager:
        cls._instance = cls(resource_dir)
        return cls._instance

    @classmethod
    def get(cls) -> AssetManager:
        if cls._instance is None:
            raise RuntimeError("AssetManager has not been initialized.")
        return cls._instance

    def _load_tokens(self) -> None:
        tokens_path = self.ui_dir / "design_tokens.json"
        if tokens_path.is_file():
            try:
                with open(tokens_path, "r", encoding="utf-8") as f:
                    self.tokens = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load design tokens: {e}")

    def get_pixmap(self, relative_path: str) -> QPixmap:
        """Get or load a pixmap by relative path inside resources/ui."""
        if relative_path in self._pixmap_cache:
            return self._pixmap_cache[relative_path]

        full_path = self.ui_dir / relative_path
        if not full_path.is_file():
            # Try branding directory
            full_path = self.branding_dir / relative_path

        if not full_path.is_file():
            logger.warning(f"Asset not found: {relative_path}")
            pm = QPixmap(32, 32)
            pm.fill(QColor(100, 100, 100, 128))
            self._pixmap_cache[relative_path] = pm
            return pm

        pm = QPixmap(str(full_path))
        self._pixmap_cache[relative_path] = pm
        return pm

    def get_background(self) -> QPixmap:
        return self.get_pixmap("background.png")

    def get_logo(self) -> QPixmap:
        return self.get_pixmap("logo.png")

    def get_app_icon(self) -> QIcon:
        icon_path = self.branding_dir / "app_icon.ico"
        if not icon_path.is_file():
            icon_path = self.branding_dir / "app_icon.png"
        return QIcon(str(icon_path))

    def get_component_pixmap(self, category: str, name: str, scale: int = 1) -> QPixmap:
        scale_dir = "2x" if scale >= 2 else "1x"
        rel_path = f"png/{scale_dir}/{category}/{name}.png"
        return self.get_pixmap(rel_path)

    def get_icon_pixmap(self, icon_name: str, color_variant: str = "cyan") -> QPixmap:
        """Retrieve an icon pixmap, e.g. icon_name='close', color_variant='cyan'."""
        filename = f"{icon_name}_{color_variant}.png"
        return self.get_component_pixmap("icons", f"{icon_name}_{color_variant}")

    def get_icon(self, icon_name: str) -> QIcon:
        """Create a QIcon with normal/hover/disabled states from available variants."""
        if icon_name in self._icon_cache:
            return self._icon_cache[icon_name]

        icon = QIcon()
        cyan_pm = self.get_icon_pixmap(icon_name, "cyan")
        white_pm = self.get_icon_pixmap(icon_name, "white")
        ink_pm = self.get_icon_pixmap(icon_name, "ink")

        if not cyan_pm.isNull():
            icon.addPixmap(cyan_pm, QIcon.Mode.Normal)
        if not white_pm.isNull():
            icon.addPixmap(white_pm, QIcon.Mode.Active)
            icon.addPixmap(white_pm, QIcon.Mode.Selected)
        if not ink_pm.isNull():
            icon.addPixmap(ink_pm, QIcon.Mode.Disabled)

        self._icon_cache[icon_name] = icon
        return icon
