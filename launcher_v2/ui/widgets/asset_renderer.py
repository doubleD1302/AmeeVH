# -*- coding: utf-8 -*-
"""
Direct master-to-device QPainter renderer, Unity 9-slice mapper, DPR-keyed SVG
cache, runtime SourceIn tinting, pixel-exact QR painter, and Pillow blur helper.
"""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Optional

from PIL import Image, ImageFilter
from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from ...core.safety import sha256_file
from ..theme.tokens import PORCELAIN_TOKENS

logger = logging.getLogger(__name__)

# Verified Unity btn_common_db_l_1/2/3 insets (382x117 -> 14,10,14,12 DIP)
FACETED_BTN_SRC_INSETS: tuple[int, int, int, int] = (30, 24, 30, 28)
FACETED_BTN_DST_INSETS: tuple[float, float, float, float] = (14.0, 10.0, 14.0, 12.0)

_DEFAULT_RENDERER: Optional["AssetRenderer"] = None


def unity_border_to_qt_insets(m_border: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Convert Unity Sprite.m_Border (Left, Bottom, Right, Top) -> Qt (Left, Top, Right, Bottom)."""
    left, bottom, right, top = m_border
    return (int(left), int(top), int(right), int(bottom))


def _default_resource_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "resources"


def _to_qsize(size: QSize | tuple[int, int]) -> QSize:
    if isinstance(size, QSize):
        return size
    return QSize(int(size[0]), int(size[1]))


class AssetRenderer:
    """High-DPI crisp asset renderer backed by curated launcher_v2/resources."""

    _MAX_BLUR_CACHE_ENTRIES: int = 8

    def __init__(self, resource_dir: Path | str | None = None) -> None:
        self.resource_dir = Path(resource_dir) if resource_dir is not None else _default_resource_dir()
        self._manifest: dict[str, dict] = {}
        self._master_cache: dict[str, QPixmap] = {}
        self._tinted_cache: dict[tuple[str, str], QPixmap] = {}
        self._dpi_cache: dict[tuple[str, int, int, float, str], QPixmap] = {}
        self._blur_cache: dict[tuple[int, int, int, int], QPixmap] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        manifest_path = self.resource_dir / "game" / "manifest.json"
        if not manifest_path.is_file():
            return
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            for item in raw.get("assets", []):
                fname = item.get("file")
                if isinstance(fname, str) and fname:
                    self._manifest[fname] = item
        except (OSError, ValueError) as exc:
            logger.warning("Could not load game asset manifest %s: %s", manifest_path, exc)

    def asset_meta(self, rel_or_name: str) -> dict | None:
        name = Path(rel_or_name).name
        return self._manifest.get(name)

    def unity_border(self, rel_or_name: str) -> tuple[int, int, int, int] | None:
        meta = self.asset_meta(rel_or_name)
        if not meta:
            return None
        b = meta.get("m_Border")
        if isinstance(b, (list, tuple)) and len(b) == 4:
            return unity_border_to_qt_insets((int(b[0]), int(b[1]), int(b[2]), int(b[3])))
        return None

    def resolve_path(self, rel_path: str | Path) -> Path:
        p = Path(rel_path)
        if p.is_absolute() and p.is_file():
            return p
        rel_str = str(rel_path).replace("\\", "/").lstrip("/")
        candidates = [
            self.resource_dir / rel_str,
            self.resource_dir / "game" / rel_str,
            self.resource_dir / "icons" / rel_str,
            self.resource_dir / "branding" / rel_str,
            self.resource_dir / "spinner" / rel_str,
            self.resource_dir / "support" / rel_str,
        ]
        for cand in candidates:
            if cand.is_file():
                return cand
        return self.resource_dir / rel_str

    def resolve_variant(self, rel_path: str, *, surface: str = "dark") -> str:
        """Select light- or dark-polarity asset variant automatically when available."""
        name = Path(rel_path).name
        stem = Path(name).stem
        suffix = Path(name).suffix.lower()

        if surface == "light":
            if suffix == ".svg" and stem.startswith("asar_") and not stem.endswith("_navy"):
                cand_name = f"{stem}_navy.svg"
                if (self.resource_dir / "game" / cand_name).is_file():
                    return f"game/{cand_name}"
            if stem.endswith("_light") and suffix == ".png":
                cand_name = f"{stem[:-6]}.png"
                if (self.resource_dir / "game" / cand_name).is_file():
                    return f"game/{cand_name}"
        else:
            if suffix == ".svg" and stem.startswith("asar_") and stem.endswith("_navy"):
                cand_name = f"{stem[:-5]}.svg"
                if (self.resource_dir / "game" / cand_name).is_file():
                    return f"game/{cand_name}"
            if suffix == ".png" and not stem.endswith("_light"):
                cand_name = f"{stem}_light.png"
                if (self.resource_dir / "game" / cand_name).is_file():
                    return f"game/{cand_name}"
        return rel_path

    def invalidate_dpi_cache(self) -> None:
        """Clear DPR-keyed raster caches when window DPI or screen changes."""
        self._dpi_cache.clear()
        self._blur_cache.clear()

    def get_master_pixmap(self, rel_path: str | Path) -> QPixmap:
        """Load and cache native-resolution master QPixmap without intermediate downscaling."""
        resolved = self.resolve_path(rel_path)
        key = str(resolved)
        cached = self._master_cache.get(key)
        if cached is not None and not cached.isNull():
            return cached
        pix = QPixmap(str(resolved)) if resolved.is_file() else QPixmap()
        if not pix.isNull():
            self._master_cache[key] = pix
        return pix

    def get_tinted_pixmap(self, rel_path: str | Path, color: QColor | str) -> QPixmap:
        """Tint a master pixmap using runtime QPainter CompositionMode_SourceIn."""
        qcolor = QColor(color)
        resolved = self.resolve_path(rel_path)
        cache_key = (str(resolved), qcolor.name(QColor.NameFormat.HexArgb))
        cached = self._tinted_cache.get(cache_key)
        if cached is not None and not cached.isNull():
            return cached

        master = self.get_master_pixmap(resolved)
        if master.isNull():
            return QPixmap()

        out = QPixmap(master.size())
        out.fill(Qt.GlobalColor.transparent)
        painter = QPainter(out)
        painter.drawPixmap(0, 0, master)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(out.rect(), qcolor)
        painter.end()

        self._tinted_cache[cache_key] = out
        return out

    def get_svg_pixmap(
        self,
        rel_path: str | Path,
        logical_size: QSize | tuple[int, int],
        dpr: float = 1.0,
        *,
        tint: QColor | str | None = None,
    ) -> QPixmap:
        """Render an SVG directly at logical_size * dpr and cache by DPR key."""
        sz = _to_qsize(logical_size)
        w = max(1, sz.width())
        h = max(1, sz.height())
        eff_dpr = max(1.0, float(dpr))
        tint_key = QColor(tint).name(QColor.NameFormat.HexArgb) if tint is not None else ""
        resolved = self.resolve_path(rel_path)
        cache_key = (str(resolved), w, h, round(eff_dpr, 2), tint_key)

        cached = self._dpi_cache.get(cache_key)
        if cached is not None and not cached.isNull():
            return cached

        if not resolved.is_file():
            return QPixmap()

        renderer = QSvgRenderer(str(resolved))
        if not renderer.isValid():
            return QPixmap()

        px_w = max(1, round(w * eff_dpr))
        px_h = max(1, round(h * eff_dpr))
        img = QImage(px_w, px_h, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        renderer.render(painter, QRectF(0.0, 0.0, float(px_w), float(px_h)))
        if tint is not None:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(img.rect(), QColor(tint))
        painter.end()

        pix = QPixmap.fromImage(img)
        pix.setDevicePixelRatio(eff_dpr)
        self._dpi_cache[cache_key] = pix
        return pix

    def get_icon_pixmap(
        self,
        rel_path: str | Path,
        logical_size: QSize | tuple[int, int],
        dpr: float = 1.0,
        *,
        tint: QColor | str | None = None,
    ) -> QPixmap:
        """Render SVG or PNG icon crisply at exact logical_size * dpr."""
        resolved = self.resolve_path(rel_path)
        if resolved.suffix.lower() == ".svg":
            return self.get_svg_pixmap(resolved, logical_size, dpr, tint=tint)

        sz = _to_qsize(logical_size)
        w = max(1, sz.width())
        h = max(1, sz.height())
        eff_dpr = max(1.0, float(dpr))
        tint_key = QColor(tint).name(QColor.NameFormat.HexArgb) if tint is not None else ""
        cache_key = (str(resolved), w, h, round(eff_dpr, 2), tint_key)

        cached = self._dpi_cache.get(cache_key)
        if cached is not None and not cached.isNull():
            return cached

        src = self.get_tinted_pixmap(resolved, tint) if tint is not None else self.get_master_pixmap(resolved)
        if src.isNull():
            return QPixmap()

        px_w = max(1, round(w * eff_dpr))
        px_h = max(1, round(h * eff_dpr))
        img = QImage(px_w, px_h, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.paint_contain(painter, QRectF(0.0, 0.0, float(px_w), float(px_h)), src)
        painter.end()

        pix = QPixmap.fromImage(img)
        pix.setDevicePixelRatio(eff_dpr)
        self._dpi_cache[cache_key] = pix
        return pix

    def get_icon(
        self,
        rel_path: str | Path,
        logical_size: QSize | tuple[int, int] = (16, 16),
        dpr: float = 1.0,
        *,
        tint: QColor | str | None = None,
    ) -> QIcon:
        return QIcon(self.get_icon_pixmap(rel_path, logical_size, dpr, tint=tint))

    def paint_cover(
        self,
        painter: QPainter,
        target_rect: QRectF | QRect,
        pixmap: QPixmap,
        *,
        focus: tuple[float, float] = (0.5, 0.5),
        zoom: float = 1.0,
    ) -> None:
        """Draw pixmap aspect-filled directly from master into target_rect."""
        rect = QRectF(target_rect)
        if rect.isEmpty() or pixmap.isNull() or pixmap.width() <= 0 or pixmap.height() <= 0:
            return

        pw = float(pixmap.width())
        ph = float(pixmap.height())
        tw = rect.width()
        th = rect.height()
        if tw <= 0.0 or th <= 0.0:
            return

        scale = max(tw / pw, th / ph) * max(1.0, float(zoom))
        src_w = min(pw, tw / scale)
        src_h = min(ph, th / scale)
        fx = max(0.0, min(1.0, float(focus[0])))
        fy = max(0.0, min(1.0, float(focus[1])))
        src_x = max(0.0, min(pw - src_w, (pw - src_w) * fx))
        src_y = max(0.0, min(ph - src_h, (ph - src_h) * fy))

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(rect, pixmap, QRectF(src_x, src_y, src_w, src_h))
        painter.restore()

    def paint_contain(
        self,
        painter: QPainter,
        target_rect: QRectF | QRect,
        pixmap: QPixmap,
        *,
        align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
    ) -> None:
        """Draw pixmap aspect-contained directly from master into target_rect."""
        rect = QRectF(target_rect)
        if rect.isEmpty() or pixmap.isNull() or pixmap.width() <= 0 or pixmap.height() <= 0:
            return

        pw = float(pixmap.width())
        ph = float(pixmap.height())
        scale = min(rect.width() / pw, rect.height() / ph)
        dw = pw * scale
        dh = ph * scale

        if align & Qt.AlignmentFlag.AlignLeft:
            dx = rect.left()
        elif align & Qt.AlignmentFlag.AlignRight:
            dx = rect.right() - dw
        else:
            dx = rect.left() + (rect.width() - dw) * 0.5

        if align & Qt.AlignmentFlag.AlignTop:
            dy = rect.top()
        elif align & Qt.AlignmentFlag.AlignBottom:
            dy = rect.bottom() - dh
        else:
            dy = rect.top() + (rect.height() - dh) * 0.5

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(QRectF(dx, dy, dw, dh), pixmap, QRectF(0.0, 0.0, pw, ph))
        painter.restore()

    def draw_nine_slice(
        self,
        painter: QPainter,
        target_rect: QRectF | QRect,
        pixmap: QPixmap,
        insets: tuple[int, int, int, int],
        dst_insets: tuple[float, float, float, float] | None = None,
        *,
        from_unity_border: bool = False,
    ) -> None:
        """Paint a crisp 9-slice sprite with proportional corner clamping."""
        rect = QRectF(target_rect)
        if rect.isEmpty() or pixmap.isNull() or pixmap.width() <= 0 or pixmap.height() <= 0:
            return

        qt_src = unity_border_to_qt_insets(insets) if from_unity_border else insets
        sl, st, sr, sb = (max(0, int(v)) for v in qt_src)
        pw = pixmap.width()
        ph = pixmap.height()

        # Clamp source insets so corners never invert inside the source texture
        if sl + sr > pw and (sl + sr) > 0:
            factor = pw / float(sl + sr)
            sl = int(sl * factor)
            sr = pw - sl
        if st + sb > ph and (st + sb) > 0:
            factor = ph / float(st + sb)
            st = int(st * factor)
            sb = ph - st

        if dst_insets is None:
            dl, dt, dr, db = float(sl), float(st), float(sr), float(sb)
        else:
            dl, dt, dr, db = (max(0.0, float(v)) for v in dst_insets)

        rw = rect.width()
        rh = rect.height()
        if dl + dr > rw and (dl + dr) > 0.0:
            factor = rw / (dl + dr)
            dl *= factor
            dr *= factor
        if dt + db > rh and (dt + db) > 0.0:
            factor = rh / (dt + db)
            dt *= factor
            db *= factor

        scw = float(max(0, pw - sl - sr))
        sch = float(max(0, ph - st - sb))
        dcw = max(0.0, rw - dl - dr)
        dch = max(0.0, rh - dt - db)

        sx_coords = (0.0, float(sl), float(pw - sr))
        sw_sizes = (float(sl), scw, float(sr))
        sy_coords = (0.0, float(st), float(ph - sb))
        sh_sizes = (float(st), sch, float(sb))

        dx_coords = (rect.left(), rect.left() + dl, rect.right() - dr)
        dw_sizes = (dl, dcw, dr)
        dy_coords = (rect.top(), rect.top() + dt, rect.bottom() - db)
        dh_sizes = (dt, dch, db)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        for row in range(3):
            sh = sh_sizes[row]
            dh = dh_sizes[row]
            if sh <= 0.0 or dh <= 0.0:
                continue
            for col in range(3):
                sw = sw_sizes[col]
                dw = dw_sizes[col]
                if sw <= 0.0 or dw <= 0.0:
                    continue
                srect = QRectF(sx_coords[col], sy_coords[row], sw, sh)
                drect = QRectF(dx_coords[col], dy_coords[row], dw, dh)
                painter.drawPixmap(drect, pixmap, srect)
        painter.restore()

    def paint_qr(
        self,
        painter: QPainter,
        target_rect: QRectF | QRect,
        qr_path: Path | str,
        expected_sha256: str,
        dpr: float = 1.0,
        *,
        quiet_zone: int = 20,
    ) -> bool:
        """Verify SHA256 and paint a pixel-exact QR code inside >=20 DIP white quiet zone."""
        rect = QRectF(target_rect)
        if rect.isEmpty():
            return False

        resolved = self.resolve_path(qr_path)
        if not resolved.is_file():
            return False

        try:
            actual_sha = sha256_file(resolved).lower()
        except OSError:
            return False
        if not expected_sha256 or actual_sha != expected_sha256.strip().lower():
            logger.warning(
                "QR SHA256 mismatch for %s (expected=%s actual=%s)",
                resolved,
                expected_sha256,
                actual_sha,
            )
            return False

        pix = self.get_master_pixmap(resolved)
        if pix.isNull() or pix.width() <= 0 or pix.height() <= 0:
            return False

        qz = max(20.0, float(quiet_zone))
        inner_w = max(0.0, rect.width() - 2.0 * qz)
        inner_h = max(0.0, rect.height() - 2.0 * qz)
        avail = min(inner_w, inner_h)
        if avail <= 0.0:
            return False

        eff_dpr = max(1.0, float(dpr))
        native_min = min(pix.width(), pix.height())
        max_logical = math.floor(native_min / eff_dpr)
        side = float(min(avail, max(1.0, float(max_logical))))

        painter.save()
        # Opaque #FFFFFF quiet zone container with 1px #D5E0EE hairline border
        painter.setPen(QColor(PORCELAIN_TOKENS.HAIRLINE))
        painter.setBrush(QColor(PORCELAIN_TOKENS.WHITE))
        painter.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))

        qr_x = rect.left() + (rect.width() - side) * 0.5
        qr_y = rect.top() + (rect.height() - side) * 0.5
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.drawPixmap(
            QRectF(qr_x, qr_y, side, side),
            pix,
            QRectF(0.0, 0.0, float(pix.width()), float(pix.height())),
        )
        painter.restore()
        return True

    def blur_backdrop_pixmap(
        self,
        source_pixmap: QPixmap,
        radius: int = 8,
        *,
        reduced_motion: bool = False,
        software_rendering: bool = False,
    ) -> QPixmap:
        """Create a 4x-downscaled Pillow Gaussian blur snapshot (no QGraphicsBlurEffect).

        Returns a null QPixmap when reduced_motion or software_rendering is active so
        callers fall back cleanly to a solid translucent scrim.
        """
        if reduced_motion or software_rendering or source_pixmap.isNull():
            return QPixmap()

        w = source_pixmap.width()
        h = source_pixmap.height()
        if w <= 0 or h <= 0:
            return QPixmap()

        r = max(1, int(radius))
        cache_key = (int(source_pixmap.cacheKey()), r, w, h)
        cached = self._blur_cache.get(cache_key)
        if cached is not None and not cached.isNull():
            self._blur_cache[cache_key] = self._blur_cache.pop(cache_key)
            return cached

        qimg = source_pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        raw_bytes = bytes(qimg.constBits())
        pil_img = Image.frombuffer(
            "RGBA",
            (qimg.width(), qimg.height()),
            raw_bytes,
            "raw",
            "RGBA",
            qimg.bytesPerLine(),
            1,
        ).copy()

        down_w = max(1, qimg.width() // 4)
        down_h = max(1, qimg.height() // 4)
        blurred = (
            pil_img.resize((down_w, down_h), Image.Resampling.BILINEAR)
            .filter(ImageFilter.GaussianBlur(radius=r))
            .resize((qimg.width(), qimg.height()), Image.Resampling.BILINEAR)
        )
        out_bytes = blurred.tobytes("raw", "RGBA")
        out_qimg = QImage(out_bytes, qimg.width(), qimg.height(), qimg.width() * 4, QImage.Format.Format_RGBA8888).copy()
        out_pix = QPixmap.fromImage(out_qimg)
        out_pix.setDevicePixelRatio(source_pixmap.devicePixelRatio())
        self._blur_cache[cache_key] = out_pix
        while len(self._blur_cache) > self._MAX_BLUR_CACHE_ENTRIES:
            oldest_key = next(iter(self._blur_cache))
            del self._blur_cache[oldest_key]
        return out_pix


def get_asset_renderer(resource_dir: Path | str | None = None) -> AssetRenderer:
    """Return a shared AssetRenderer instance (re-instantiating if resource_dir changes)."""
    global _DEFAULT_RENDERER
    if _DEFAULT_RENDERER is None:
        _DEFAULT_RENDERER = AssetRenderer(resource_dir)
    elif resource_dir is not None and Path(resource_dir) != _DEFAULT_RENDERER.resource_dir:
        _DEFAULT_RENDERER = AssetRenderer(resource_dir)
    return _DEFAULT_RENDERER
