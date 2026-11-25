"""3-Tier Official Background Sync & Zone Luminance Profiler (pure Python, zero Qt)."""
from __future__ import annotations

import base64
import binascii
import ctypes
from dataclasses import dataclass
import hashlib
import http.client
import io
import json
import logging
import math
import os
from pathlib import Path
import re
import socket
import ssl
import stat
import struct
import threading
import time
from typing import Any, Callable, Iterator, Mapping
import urllib.error
import urllib.parse
import urllib.request
import uuid
import warnings
import zlib

from PIL import Image

try:
    from .tls import build_context as _tls_build_context
except ImportError:  # pragma: no cover - standalone before/without M3
    _tls_build_context = None

try:
    from .safety import atomic_json as _safety_atomic_json, sha256_file as _safety_sha256_file
except ImportError:  # pragma: no cover - standalone before/without M3
    _safety_atomic_json = None
    _safety_sha256_file = None

log = logging.getLogger("launcher_v2.bg_sync")

YOSTAR_API_BASE = "https://api-launcher-en.yo-star.com"
YOSTAR_BASE_CONFIG_URL = f"{YOSTAR_API_BASE}/api/launcher/base/config"
YOSTAR_AUTH_SALT = "DE7108E9B2842FD460F4777702727869"
YOSTAR_USER_AGENT = "axios/1.5.0"

ALLOWED_BG_HOSTS: tuple[str, ...] = ("yo-star.com", "stellasora.global")

MAX_BG_BYTES = 25 * 1024 * 1024
MAX_CONFIG_BYTES = 1 * 1024 * 1024
MAX_IDB_BLOB_BYTES = 35 * 1024 * 1024
MAX_ASAR_HEADER_BYTES = 32 * 1024 * 1024
MAX_CACHED_BACKGROUNDS = 2
MIN_BG_WIDTH = 800
MIN_BG_HEIGHT = 450
MAX_IMAGE_PIXELS = 64_000_000

BUNDLED_BG_REL = Path("branding") / "background_native_2048x1451.png"
DEFAULT_OFFICIAL_INSTALL_DIR = Path(r"C:\YostarGames\StellaSora_EN_Gamelauncher")
_APPDATA_ENV = os.environ.get("APPDATA")
DEFAULT_OFFICIAL_APPDATA_DIR = (
    Path(_APPDATA_ENV) / "StellaSora_EN_Gamelauncher"
    if _APPDATA_ENV
    else Path.home() / "AppData" / "Roaming" / "StellaSora_EN_Gamelauncher"
)

_CRC64_ECMA_POLY = 0xC96C5795D7870F42


def _make_crc64_table() -> tuple[int, ...]:
    table: list[int] = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ _CRC64_ECMA_POLY
            else:
                crc >>= 1
        table.append(crc)
    return tuple(table)


_CRC64_TABLE = _make_crc64_table()
_BASE64_VALID_RE = re.compile(rb"[A-Za-z0-9+/\r\n]+(?:==|=)?")
_VIDEO_EXTS = (".mp4", ".webm", ".mov", ".m4v")
_PILLOW_WARN_LOCK = threading.Lock()


def _build_ssl_context() -> ssl.SSLContext:
    if _tls_build_context is not None:
        return _tls_build_context()
    ctx = ssl.create_default_context()
    try:
        import certifi

        cafile = certifi.where()
        if cafile:
            ctx.load_verify_locations(cafile=cafile)
    except Exception:  # noqa: BLE001 - certifi is optional fallback
        pass
    return ctx


def _sha256_file(path: Path) -> str:
    if _safety_sha256_file is not None:
        return _safety_sha256_file(path)
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _clear_readonly_attr(path: Path) -> None:
    if not path.exists():
        return
    try:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
    except OSError:
        pass
    if os.name == "nt":
        try:
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.SetFileAttributesW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
            kernel32.SetFileAttributesW.restype = wintypes.BOOL
            kernel32.SetFileAttributesW(str(path), 0x80)
        except Exception:  # noqa: BLE001
            pass


def _atomic_replace(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            os.replace(src, dst)
            return
        except OSError as exc:
            winerror = getattr(exc, "winerror", None)
            if winerror == 5 and dst.exists():
                _clear_readonly_attr(dst)
            if winerror in (5, 32, 33) and attempt < 2:
                time.sleep((0.05, 0.15)[attempt])
                continue
            raise


def _atomic_json(path: Path, data: Any) -> None:
    if _safety_atomic_json is not None:
        _safety_atomic_json(path, data)
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp.open("x", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        _atomic_replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _scrim_top_alpha(y_top: float) -> float:
    if y_top >= 0.58:
        return 0.62
    if y_top >= 0.40:
        return 0.45
    return 0.26


def _scrim_bottom_alpha(y_bottom: float) -> float:
    if y_bottom >= 0.58:
        return 0.72
    if y_bottom >= 0.40:
        return 0.58
    return 0.42


def _card_glass_alpha(y_all: float) -> float:
    if y_all >= 0.58:
        return 0.86
    if y_all >= 0.40:
        return 0.80
    return 0.72


@dataclass(frozen=True)
class LuminanceProfile:
    """Zone luminance profile & adaptive glass/scrim opacities."""

    y_all: float
    y_top: float
    y_bottom: float
    mode: str
    top_scrim_alpha: float | None = None
    bottom_scrim_alpha: float | None = None
    card_glass_alpha: float | None = None

    def __post_init__(self) -> None:
        if self.top_scrim_alpha is None:
            object.__setattr__(self, "top_scrim_alpha", _scrim_top_alpha(self.y_top))
        if self.bottom_scrim_alpha is None:
            object.__setattr__(self, "bottom_scrim_alpha", _scrim_bottom_alpha(self.y_bottom))
        if self.card_glass_alpha is None:
            object.__setattr__(self, "card_glass_alpha", _card_glass_alpha(self.y_all))

    def to_dict(self) -> dict[str, Any]:
        return {
            "y_all": round(float(self.y_all), 6),
            "y_top": round(float(self.y_top), 6),
            "y_bottom": round(float(self.y_bottom), 6),
            "mode": self.mode,
            "top_scrim_alpha": round(float(self.top_scrim_alpha or 0.0), 4),
            "bottom_scrim_alpha": round(float(self.bottom_scrim_alpha or 0.0), 4),
            "card_glass_alpha": round(float(self.card_glass_alpha or 0.0), 4),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> LuminanceProfile:
        if not isinstance(raw, Mapping):
            raise ValueError("LuminanceProfile must be a mapping.")
        y_all = float(raw["y_all"])
        y_top = float(raw["y_top"])
        y_bottom = float(raw["y_bottom"])
        for val in (y_all, y_top, y_bottom):
            if not math.isfinite(val) or not (0.0 <= val <= 1.0):
                raise ValueError(f"Luminance out of [0, 1] range: {val}")
        mode = str(raw["mode"])
        if mode not in ("light", "dark"):
            raise ValueError(f"Invalid luminance mode: {mode}")

        def _opt_alpha(key: str) -> float | None:
            v = raw.get(key)
            if v is None:
                return None
            f = float(v)
            if not math.isfinite(f) or not (0.0 <= f <= 1.0):
                raise ValueError(f"Alpha out of [0, 1] range: {key}={f}")
            return f

        return cls(
            y_all=y_all,
            y_top=y_top,
            y_bottom=y_bottom,
            mode=mode,
            top_scrim_alpha=_opt_alpha("top_scrim_alpha"),
            bottom_scrim_alpha=_opt_alpha("bottom_scrim_alpha"),
            card_glass_alpha=_opt_alpha("card_glass_alpha"),
        )


@dataclass(frozen=True)
class BackgroundFrame:
    """Resolved launcher background frame."""

    tier: int
    source_label: str
    image_path: Path
    crc64: str
    etag: str
    width: int
    height: int
    luminance: LuminanceProfile
    warning_code: str | None = None
    image_format: str = ""
    is_video: bool = False
    still_fallback_path: Path | None = None

    def __post_init__(self) -> None:
        img_path = Path(self.image_path)
        object.__setattr__(self, "image_path", img_path)
        if self.still_fallback_path is not None:
            object.__setattr__(self, "still_fallback_path", Path(self.still_fallback_path))
        if not self.image_format:
            fmt = ""
            try:
                if img_path.is_file():
                    with img_path.open("rb") as fh:
                        fmt = detect_image_format(fh.read(16)) or ""
            except OSError:
                fmt = ""
            if not fmt:
                ext = img_path.suffix.lower().lstrip(".")
                fmt = "jpeg" if ext in ("jpg", "jpeg") else ext
            object.__setattr__(self, "image_format", fmt)

    @property
    def image_bytes(self) -> bytes:
        return Path(self.image_path).read_bytes()


def build_yostar_auth_header(
    data: str = "",
    version: str = "1.6.0",
    timestamp: int | None = None,
) -> str:
    """Build Yostar Launcher Authorization JSON string matching crypto.ts."""
    ts = int(time.time()) if timestamp is None else int(timestamp)
    head = {
        "game_tag": "StellaSora_EN",
        "time": ts,
        "version": version,
    }
    head_json = json.dumps(head, separators=(",", ":"), ensure_ascii=False)
    sign_str = f"{head_json}{data}{YOSTAR_AUTH_SALT}"
    sign = hashlib.md5(sign_str.encode("utf-8")).hexdigest()
    return json.dumps({"head": head, "sign": sign}, separators=(",", ":"), ensure_ascii=False)


def crc64_ecma(data: bytes, init: int = 0) -> int:
    """Compute CRC64-ECMA-182 (reflected polynomial 0xC96C5795D7870F42, ~0 init/xorout)."""
    crc = init ^ 0xFFFFFFFFFFFFFFFF
    table = _CRC64_TABLE
    for byte in data:
        crc = table[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFFFFFFFFFF


def crc64_ecma_file(path: Path) -> str:
    """Stream file in 1 MiB chunks and return decimal CRC64-ECMA string."""
    crc = 0
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            crc = crc64_ecma(chunk, init=crc)
    return str(crc)


def is_allowed_bg_url(url: str) -> bool:
    """Enforce strict HTTPS and official Yostar / Stella Sora host allowlist."""
    if not isinstance(url, str) or not url:
        return False
    if any(ord(ch) <= 0x20 or ord(ch) == 0x7F for ch in url):
        return False
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    if parsed.scheme.lower() != "https":
        return False
    if (
        "@" in parsed.netloc
        or "\\" in parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
    ):
        return False
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host:
        return False
    return any(host == dom or host.endswith("." + dom) for dom in ALLOWED_BG_HOSTS)


def detect_image_format(header: bytes) -> str | None:
    """Detect PNG, JPEG, or WEBP strictly from magic header bytes."""
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    return None


def _peek_image_dimensions_from_bytes(data: bytes) -> tuple[int, int] | None:
    """Best-effort fast PNG/JPEG/WEBP header dimension parser (returns None if inconclusive)."""
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        w, h = struct.unpack(">II", data[16:24])
        return int(w), int(h)
    if len(data) >= 30 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
            raw_w, raw_h = struct.unpack("<HH", data[26:30])
            return int(raw_w & 0x3FFF), int(raw_h & 0x3FFF)
        if chunk == b"VP8L" and data[20] == 0x2F:
            b0, b1, b2, b3 = data[21:25]
            bits = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
            return int((bits & 0x3FFF) + 1), int(((bits >> 14) & 0x3FFF) + 1)
        if chunk == b"VP8X":
            w = 1 + int.from_bytes(data[24:27], "little")
            h = 1 + int.from_bytes(data[27:30], "little")
            return int(w), int(h)
        return None
    if len(data) >= 4 and data[:3] == b"\xff\xd8\xff":
        pos = 2
        n = len(data)
        while pos + 4 <= n:
            if data[pos] != 0xFF:
                break
            while pos < n and data[pos] == 0xFF:
                pos += 1
            if pos >= n:
                break
            marker = data[pos]
            pos += 1
            if marker in (0xD8, 0xD9, 0x00) or (0xD0 <= marker <= 0xD7):
                continue
            if marker == 0xDA:
                break
            if pos + 2 > n:
                break
            seg_len = struct.unpack(">H", data[pos : pos + 2])[0]
            if seg_len < 2 or pos + seg_len > n:
                break
            if marker in (
                0xC0, 0xC1, 0xC2, 0xC3,
                0xC5, 0xC6, 0xC7,
                0xC9, 0xCA, 0xCB,
                0xCD, 0xCE, 0xCF,
            ):
                if seg_len >= 7:
                    h, w = struct.unpack(">HH", data[pos + 3 : pos + 7])
                    return int(w), int(h)
                return None
            pos += seg_len
    return None


def validate_image_file(
    path: Path,
    min_width: int = MIN_BG_WIDTH,
    min_height: int = MIN_BG_HEIGHT,
) -> tuple[str, int, int]:
    """Validate magic bytes, Pillow integrity, format parity, and minimum dimensions."""
    p = Path(path)
    if not p.is_file():
        raise ValueError(f"Image file does not exist: {p}")
    size = p.stat().st_size
    if size <= 0 or size > MAX_BG_BYTES:
        raise ValueError(f"Image size out of bounds: {size}")
    with p.open("rb") as fh:
        head = fh.read(65536)
    fmt = detect_image_format(head[:16])
    if fmt is None:
        raise ValueError("Unsupported or invalid image magic bytes.")
    peeked = _peek_image_dimensions_from_bytes(head)
    if peeked is not None:
        pw, ph = peeked
        if pw <= 0 or ph <= 0 or pw * ph > MAX_IMAGE_PIXELS:
            raise ValueError(f"Image pixel count exceeds limit: {pw}x{ph}")

    with _PILLOW_WARN_LOCK:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            warnings.filterwarnings("ignore", category=UserWarning, module=r"^PIL\.")
            try:
                with Image.open(p) as im:
                    pil_fmt = (im.format or "").lower()
                    if pil_fmt != fmt:
                        raise ValueError(f"Image format mismatch: magic={fmt}, pillow={pil_fmt}")
                    width, height = im.size
                    if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
                        raise ValueError(f"Image pixel count exceeds limit: {width}x{height}")
                with Image.open(p) as im:
                    im.verify()
            except Image.DecompressionBombError as exc:
                raise ValueError(f"Image exceeds decompression bomb limit: {exc}") from exc
            except (SyntaxError, EOFError, struct.error, zlib.error) as exc:
                raise ValueError(f"Corrupt image payload: {exc}") from exc

    if width < min_width or height < min_height:
        raise ValueError(f"Image dimensions too small: {width}x{height} < {min_width}x{min_height}")
    return fmt, int(width), int(height)


def compute_luminance_profile(source: Path | bytes | Image.Image) -> LuminanceProfile:
    """Compute BT.709 zone luminance on 160x90 BILINEAR RGB without deprecated Image.getdata()."""
    raw_bytes: bytes | None = None
    if isinstance(source, (bytes, bytearray, memoryview)):
        raw_bytes = bytes(source)
        peeked = _peek_image_dimensions_from_bytes(raw_bytes[:65536])
        if peeked is not None:
            pw, ph = peeked
            if pw <= 0 or ph <= 0 or pw * ph > MAX_IMAGE_PIXELS:
                raise ValueError(f"Image pixel count exceeds limit: {pw}x{ph}")
    elif not isinstance(source, Image.Image):
        src_path = Path(source)
        if src_path.is_file():
            with src_path.open("rb") as fh:
                head = fh.read(65536)
            peeked = _peek_image_dimensions_from_bytes(head)
            if peeked is not None:
                pw, ph = peeked
                if pw <= 0 or ph <= 0 or pw * ph > MAX_IMAGE_PIXELS:
                    raise ValueError(f"Image pixel count exceeds limit: {pw}x{ph}")

    with _PILLOW_WARN_LOCK:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            warnings.filterwarnings("ignore", category=UserWarning, module=r"^PIL\.")
            try:
                if isinstance(source, Image.Image):
                    w, h = source.size
                    if w <= 0 or h <= 0 or w * h > MAX_IMAGE_PIXELS:
                        raise ValueError(f"Image pixel count exceeds limit: {w}x{h}")
                    rgb = source if source.mode == "RGB" else source.convert("RGB")
                    small = rgb.resize((160, 90), Image.Resampling.BILINEAR)
                    try:
                        raw = small.tobytes()
                    finally:
                        small.close()
                        if rgb is not source:
                            rgb.close()
                elif raw_bytes is not None:
                    with Image.open(io.BytesIO(raw_bytes)) as im:
                        w, h = im.size
                        if w <= 0 or h <= 0 or w * h > MAX_IMAGE_PIXELS:
                            raise ValueError(f"Image pixel count exceeds limit: {w}x{h}")
                        rgb = im if im.mode == "RGB" else im.convert("RGB")
                        small = rgb.resize((160, 90), Image.Resampling.BILINEAR)
                        try:
                            raw = small.tobytes()
                        finally:
                            small.close()
                            if rgb is not im:
                                rgb.close()
                else:
                    with Image.open(Path(source)) as im:
                        w, h = im.size
                        if w <= 0 or h <= 0 or w * h > MAX_IMAGE_PIXELS:
                            raise ValueError(f"Image pixel count exceeds limit: {w}x{h}")
                        rgb = im if im.mode == "RGB" else im.convert("RGB")
                        small = rgb.resize((160, 90), Image.Resampling.BILINEAR)
                        try:
                            raw = small.tobytes()
                        finally:
                            small.close()
                            if rgb is not im:
                                rgb.close()
            except Image.DecompressionBombError as exc:
                raise ValueError(f"Image exceeds decompression bomb limit: {exc}") from exc
            except (SyntaxError, EOFError, struct.error, zlib.error) as exc:
                raise ValueError(f"Corrupt image payload: {exc}") from exc

    width, height = 160, 90
    top_rows = int(height * 0.20)  # 0..17 (18 rows)
    bottom_start = height // 2     # 45..89 (45 rows)

    sum_all = 0.0
    sum_top = 0.0
    sum_bottom = 0.0
    n_all = width * height
    n_top = width * top_rows
    n_bottom = width * (height - bottom_start)

    mv = memoryview(raw)
    top_limit_px = n_top
    bottom_start_px = width * bottom_start

    for px_idx in range(n_all):
        off = px_idx * 3
        y = (0.2126 * mv[off] + 0.7152 * mv[off + 1] + 0.0722 * mv[off + 2]) / 255.0
        sum_all += y
        if px_idx < top_limit_px:
            sum_top += y
        if px_idx >= bottom_start_px:
            sum_bottom += y

    y_all = round(sum_all / n_all, 6)
    y_top = round(sum_top / n_top, 6)
    y_bottom = round(sum_bottom / n_bottom, 6)
    mode = "light" if (y_all >= 0.52 or y_top >= 0.58) else "dark"
    return LuminanceProfile(y_all=y_all, y_top=y_top, y_bottom=y_bottom, mode=mode)


def is_reduced_motion(cfg: Mapping[str, Any] | None = None) -> bool:
    """Return True if config sets reduced_motion or Windows OS client animations are disabled."""
    if cfg is not None and bool(cfg.get("reduced_motion", False)):
        return True
    if os.name == "nt":
        try:
            enabled = ctypes.c_int(1)
            ok = ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(enabled), 0)
            if ok and enabled.value == 0:
                return True
        except Exception:  # noqa: BLE001
            pass
    return False


def _sanitize_cache_id(raw_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "", str(raw_id or ""))[:32]
    return cleaned or uuid.uuid4().hex[:12]


def _is_html_prefix(chunk: bytes) -> bool:
    head = chunk[:256].lstrip().lower()
    return head.startswith((b"<!doctype", b"<html", b"<head", b"<?xml"))


def _is_video_url(url: str) -> bool:
    if not url:
        return False
    try:
        path = urllib.parse.urlsplit(url).path.lower()
    except ValueError:
        return False
    return path.endswith(_VIDEO_EXTS)


class _DeadlineSocket:
    """Socket wrapper enforcing hard deadline and clamped read/send timeouts per I/O call."""

    def __init__(self, sock: Any, *, read_timeout: float, deadline: float) -> None:
        self._sock = sock
        self._read_timeout = max(0.001, float(read_timeout))
        self._deadline = float(deadline)
        self._io_refs = 0
        self._closed = False
        self._sock_closed = False

    def _clamp_timeout(self) -> None:
        rem = self._deadline - time.monotonic()
        if rem <= 0:
            raise TimeoutError("Background sync hard timeout exceeded.")
        self._sock.settimeout(max(0.001, min(self._read_timeout, rem)))

    def settimeout(self, timeout: float | None) -> None:
        if isinstance(timeout, (int, float)) and not isinstance(timeout, bool):
            self._read_timeout = max(0.001, float(timeout))
        self._sock.settimeout(timeout)

    def recv(self, *args: Any, **kwargs: Any) -> bytes:
        self._clamp_timeout()
        return self._sock.recv(*args, **kwargs)

    def recv_into(self, *args: Any, **kwargs: Any) -> int:
        self._clamp_timeout()
        return self._sock.recv_into(*args, **kwargs)

    def send(self, *args: Any, **kwargs: Any) -> int:
        self._clamp_timeout()
        return self._sock.send(*args, **kwargs)

    def sendall(self, *args: Any, **kwargs: Any) -> None:
        self._clamp_timeout()
        self._sock.sendall(*args, **kwargs)

    def makefile(self, *args: Any, **kwargs: Any) -> Any:
        return socket.socket.makefile(self, *args, **kwargs)

    def _decref_socketios(self) -> None:
        if self._io_refs > 0:
            self._io_refs -= 1
        if self._closed and self._io_refs <= 0 and not self._sock_closed:
            self._sock_closed = True
            self._sock.close()

    def close(self) -> None:
        self._closed = True
        if self._io_refs <= 0 and not self._sock_closed:
            self._sock_closed = True
            self._sock.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._sock, name)


def _tighten_response_socket_timeout(resp: Any, timeout_s: float) -> None:
    fp = getattr(resp, "fp", None)
    raw = getattr(fp, "raw", None)
    sock = getattr(raw, "_sock", None)
    if sock is not None:
        settimeout_fn = getattr(sock, "settimeout", None)
        if callable(settimeout_fn):
            try:
                settimeout_fn(max(0.001, float(timeout_s)))
            except OSError:
                pass


def _iter_response_chunks(
    resp: Any,
    *,
    max_bytes: int,
    chunk_size: int = 64 * 1024,
    deadline: float | None = None,
    read_timeout: float = 8.0,
) -> Iterator[bytes]:
    """Read response chunks via read1() (with read() fallback) enforcing hard deadline and byte cap."""
    read_fn = getattr(resp, "read1", None)
    if not callable(read_fn):
        read_fn = resp.read
    step = max(1, int(chunk_size))
    eff_read_timeout = max(0.001, float(read_timeout))
    total = 0
    while True:
        if deadline is not None:
            rem = deadline - time.monotonic()
            if rem <= 0:
                raise TimeoutError("Background sync hard timeout exceeded.")
            _tighten_response_socket_timeout(resp, min(eff_read_timeout, rem))
        to_read = min(step, max_bytes - total + 1)
        chunk = read_fn(to_read)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ValueError(f"Response exceeded {max_bytes} byte limit.")
        yield chunk


def _read_response_bounded(
    resp: Any,
    *,
    max_bytes: int,
    chunk_size: int = 16 * 1024,
    deadline: float | None = None,
    read_timeout: float = 8.0,
) -> bytes:
    """Read full bounded response body using deadline-aware chunk iteration."""
    buf = bytearray()
    for chunk in _iter_response_chunks(
        resp,
        max_bytes=max_bytes,
        chunk_size=chunk_size,
        deadline=deadline,
        read_timeout=read_timeout,
    ):
        buf.extend(chunk)
    return bytes(buf)


class _TimeoutHTTPSConnection(http.client.HTTPSConnection):
    """HTTPSConnection enforcing separate connect/TLS timeout vs socket read timeout and deadline."""

    def __init__(
        self,
        host: str,
        port: int | None = None,
        timeout: Any = None,
        *,
        connect_timeout: float = 4.0,
        read_timeout: float = 8.0,
        deadline: float | None = None,
        **kwargs: Any,
    ) -> None:
        del timeout
        self._connect_timeout = max(0.001, float(connect_timeout))
        self._read_timeout = max(0.001, float(read_timeout))
        self._deadline = deadline
        init_timeout = self._connect_timeout
        if self._deadline is not None:
            rem = self._deadline - time.monotonic()
            if rem > 0:
                init_timeout = max(0.001, min(self._connect_timeout, rem))
        super().__init__(host, port=port, timeout=init_timeout, **kwargs)

    def connect(self) -> None:
        if self._deadline is not None:
            rem = self._deadline - time.monotonic()
            if rem <= 0:
                raise TimeoutError("Background sync hard timeout exceeded.")
            self.timeout = max(0.001, min(self._connect_timeout, rem))
        else:
            self.timeout = self._connect_timeout
        super().connect()
        if self._deadline is not None:
            rem = self._deadline - time.monotonic()
            if rem <= 0:
                try:
                    self.close()
                except Exception:  # noqa: BLE001
                    pass
                raise TimeoutError("Background sync hard timeout exceeded.")
            eff_read = max(0.001, min(self._read_timeout, rem))
        else:
            eff_read = self._read_timeout
        if self.sock is not None:
            self.sock.settimeout(eff_read)
            if self._deadline is not None:
                self.sock = _DeadlineSocket(
                    self.sock,
                    read_timeout=eff_read,
                    deadline=self._deadline,
                )


class _TimeoutHTTPSHandler(urllib.request.HTTPSHandler):
    """HTTPSHandler wiring connect_timeout, read_timeout, and deadline into _TimeoutHTTPSConnection."""

    def __init__(
        self,
        *,
        context: ssl.SSLContext | None = None,
        connect_timeout: float = 4.0,
        read_timeout: float = 8.0,
        deadline: float | None = None,
    ) -> None:
        super().__init__(context=context)
        self._connect_timeout = max(0.001, float(connect_timeout))
        self._read_timeout = max(0.001, float(read_timeout))
        self._deadline = deadline

    def https_open(self, req: urllib.request.Request) -> Any:
        if self._deadline is not None:
            rem = self._deadline - time.monotonic()
            if rem <= 0:
                raise TimeoutError("Background sync hard timeout exceeded.")
            hop_connect = max(0.001, min(self._connect_timeout, rem))
            hop_read = max(0.001, min(self._read_timeout, rem))
            req.timeout = hop_read
        else:
            hop_connect = self._connect_timeout
            hop_read = self._read_timeout

        def _make_conn(host: str, **conn_kwargs: Any) -> _TimeoutHTTPSConnection:
            return _TimeoutHTTPSConnection(
                host,
                connect_timeout=hop_connect,
                read_timeout=hop_read,
                deadline=self._deadline,
                **conn_kwargs,
            )

        return self.do_open(
            _make_conn,
            req,
            context=self._context,
            check_hostname=self._check_hostname,
        )


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """HTTPRedirectHandler enforcing HTTPS + host allowlist, deadline, and stripping Authorization cross-host."""

    def __init__(
        self,
        *,
        deadline: float | None = None,
        read_timeout: float | None = None,
    ) -> None:
        super().__init__()
        self._deadline = deadline
        self._read_timeout = float(read_timeout) if read_timeout is not None else None

    @staticmethod
    def _close_fp(fp: Any) -> None:
        if fp is not None:
            try:
                fp.close()
            except Exception:  # noqa: BLE001
                pass

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        if self._deadline is not None:
            rem = self._deadline - time.monotonic()
            if rem <= 0:
                self._close_fp(fp)
                raise TimeoutError("Background sync hard timeout exceeded across redirects")

        if not is_allowed_bg_url(newurl):
            self._close_fp(fp)
            raise urllib.error.URLError(f"Disallowed redirect target URL: {newurl}")

        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is not None:
            old_split = urllib.parse.urlsplit(req.full_url)
            new_split = urllib.parse.urlsplit(newurl)
            old_host = (old_split.hostname or "").rstrip(".").lower()
            new_host = (new_split.hostname or "").rstrip(".").lower()
            if old_host != new_host or old_split.port != new_split.port:
                for hdr_dict in (new_req.headers, getattr(new_req, "unredirected_hdrs", None)):
                    if isinstance(hdr_dict, dict):
                        for key in list(hdr_dict.keys()):
                            if str(key).lower() == "authorization":
                                del hdr_dict[key]

            base_timeout = self._read_timeout
            if base_timeout is None:
                raw_to = getattr(req, "timeout", None)
                if isinstance(raw_to, (int, float)):
                    base_timeout = float(raw_to)
            if self._deadline is not None:
                rem = self._deadline - time.monotonic()
                if rem <= 0:
                    self._close_fp(fp)
                    raise TimeoutError("Background sync hard timeout exceeded across redirects")
                clamped = max(0.001, min(base_timeout, rem) if base_timeout is not None else rem)
                new_req.timeout = clamped
                # HTTPRedirectHandler.http_error_302 passes timeout=req.timeout to parent.open(new, ...).
                req.timeout = clamped
            elif base_timeout is not None:
                new_req.timeout = base_timeout
        return new_req


class BackgroundSyncService:
    """Non-blocking 3-tier Official Launcher background sync & local fallback."""

    def __init__(
        self,
        app_data_dir: Path,
        resource_dir: Path,
        official_install_dir: Path | None = None,
        official_appdata_dir: Path | None = None,
        *,
        reduced_motion: bool | None = None,
        opener: Any = None,
        connect_timeout: float = 4.0,
        read_timeout: float = 8.0,
        hard_timeout: float = 12.0,
    ) -> None:
        self.app_data_dir = Path(app_data_dir)
        self.resource_dir = Path(resource_dir)
        self.bg_cache_dir = self.app_data_dir / "bg_cache"
        self.meta_path = self.bg_cache_dir / "meta.json"
        self.official_install_dir = (
            Path(official_install_dir) if official_install_dir is not None else DEFAULT_OFFICIAL_INSTALL_DIR
        )
        self.official_appdata_dir = (
            Path(official_appdata_dir) if official_appdata_dir is not None else DEFAULT_OFFICIAL_APPDATA_DIR
        )
        self._reduced_motion_override = reduced_motion
        self._opener = opener
        self._connect_timeout = float(connect_timeout)
        self._read_timeout = float(read_timeout)
        self._hard_timeout = float(hard_timeout)
        self._lock = threading.Lock()
        self._bundled_dims_cache: tuple[int, int] | None = None
        self._bundled_lum_cache: LuminanceProfile | None = None
        self._bundled_fmt_cache: str = "png"

    def _effective_reduced_motion(self, reduced_motion: bool | None = None) -> bool:
        if reduced_motion is not None:
            return bool(reduced_motion)
        if self._reduced_motion_override is not None:
            return bool(self._reduced_motion_override)
        return is_reduced_motion()

    def _resolve_cache_image_path(self, raw_path: Any) -> Path | None:
        if not isinstance(raw_path, str) or not raw_path.strip():
            return None
        cache_root = self.bg_cache_dir.resolve()
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = cache_root / candidate
        try:
            resolved = candidate.resolve()
            resolved.relative_to(cache_root)
        except (OSError, ValueError):
            return None
        if not resolved.is_file():
            return None
        return resolved

    def _read_meta(self) -> dict[str, Any] | None:
        if not self.meta_path.is_file():
            return None
        try:
            data = json.loads(self.meta_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def _load_cached_frame(
        self,
        *,
        required_tier: int | None = None,
        fast_header_only: bool = False,
    ) -> BackgroundFrame | None:
        meta = self._read_meta()
        if meta is None:
            return None
        tier = meta.get("tier")
        if type(tier) is not int or tier not in (1, 2, 3):
            return None
        if required_tier is not None and tier != required_tier:
            return None
        img_path = self._resolve_cache_image_path(meta.get("image_path"))
        if img_path is None:
            return None
        source_label = str(meta.get("source_label") or ("online_official" if tier == 1 else "local_official_idb"))
        min_w, min_h = (640, 400) if (tier == 2 and source_label == "local_official_asar") else (MIN_BG_WIDTH, MIN_BG_HEIGHT)
        try:
            lum = LuminanceProfile.from_dict(meta.get("luminance", {}))
            if fast_header_only:
                with img_path.open("rb") as fh:
                    fmt = detect_image_format(fh.read(16))
                if fmt is None:
                    return None
                w = meta.get("width")
                h = meta.get("height")
                if (
                    type(w) is not int
                    or type(h) is not int
                    or w < min_w
                    or h < min_h
                    or w * h > MAX_IMAGE_PIXELS
                ):
                    return None
            else:
                fmt, w, h = validate_image_file(img_path, min_width=min_w, min_height=min_h)
        except (OSError, ValueError):
            return None

        return BackgroundFrame(
            tier=tier,
            source_label=source_label,
            image_path=img_path,
            crc64=str(meta.get("crc64") or ""),
            etag=str(meta.get("etag") or ""),
            width=w,
            height=h,
            luminance=lum,
            warning_code=None,
            image_format=fmt,
            is_video=False,
            still_fallback_path=None,
        )

    def _load_bundled_frame(self, warning_code: str | None = None) -> BackgroundFrame:
        bundled_path = self.resource_dir / BUNDLED_BG_REL
        with self._lock:
            if self._bundled_dims_cache is None or self._bundled_lum_cache is None:
                fmt, w, h = validate_image_file(bundled_path, min_width=1, min_height=1)
                lum = compute_luminance_profile(bundled_path)
                self._bundled_dims_cache = (w, h)
                self._bundled_lum_cache = lum
                self._bundled_fmt_cache = fmt
            else:
                w, h = self._bundled_dims_cache
                lum = self._bundled_lum_cache
                fmt = self._bundled_fmt_cache
        return BackgroundFrame(
            tier=3,
            source_label="bundled_master",
            image_path=bundled_path,
            crc64="",
            etag="",
            width=w,
            height=h,
            luminance=lum,
            warning_code=warning_code,
            image_format=fmt,
            is_video=False,
            still_fallback_path=None,
        )

    def load_initial(self) -> BackgroundFrame:
        """Instant Frame 0 lookup (< 16 ms, zero network I/O)."""
        with self._lock:
            cached = self._load_cached_frame(fast_header_only=True)
        if cached is not None:
            return cached
        return self._load_bundled_frame(warning_code=None)

    def _open_request(
        self,
        req: urllib.request.Request,
        timeout: float,
        *,
        connect_timeout: float | None = None,
        deadline: float | None = None,
    ) -> Any:
        eff_read = max(0.001, float(timeout))
        eff_connect = (
            min(self._connect_timeout, eff_read)
            if connect_timeout is None
            else max(0.001, float(connect_timeout))
        )
        if deadline is not None:
            rem = deadline - time.monotonic()
            if rem <= 0:
                raise TimeoutError("Background sync hard timeout exceeded.")
            eff_read = max(0.001, min(eff_read, rem))
            eff_connect = max(0.001, min(eff_connect, rem))
        if self._opener is not None:
            if callable(self._opener):
                resp = self._opener(req, timeout=eff_read)
            else:
                resp = self._opener.open(req, timeout=eff_read)
        else:
            if not is_allowed_bg_url(req.full_url):
                raise ValueError(f"Disallowed request URL: {req.full_url}")
            opener = urllib.request.OpenerDirector()
            opener.add_handler(urllib.request.ProxyHandler())
            opener.add_handler(urllib.request.UnknownHandler())
            opener.add_handler(
                _TimeoutHTTPSHandler(
                    context=_build_ssl_context(),
                    connect_timeout=eff_connect,
                    read_timeout=eff_read,
                    deadline=deadline,
                )
            )
            opener.add_handler(urllib.request.HTTPDefaultErrorHandler())
            opener.add_handler(_SafeRedirectHandler(deadline=deadline, read_timeout=self._read_timeout))
            opener.add_handler(urllib.request.HTTPErrorProcessor())
            resp = opener.open(req, timeout=eff_read)

        geturl_fn = getattr(resp, "geturl", None)
        if callable(geturl_fn):
            final_url = geturl_fn()
            if isinstance(final_url, str) and not is_allowed_bg_url(final_url):
                close_fn = getattr(resp, "close", None)
                if callable(close_fn):
                    try:
                        close_fn()
                    except Exception:  # noqa: BLE001
                        pass
                raise ValueError(f"Disallowed response URL: {final_url}")
        return resp

    def _prune_bg_cache_locked(self, active_path: Path) -> None:
        if not self.bg_cache_dir.is_dir():
            return
        active_resolved = active_path.resolve()
        historical: list[tuple[float, str, Path]] = []
        for entry in self.bg_cache_dir.iterdir():
            if not entry.is_file():
                continue
            name = entry.name
            if name == "meta.json" or name.startswith(".") or name.endswith(".tmp"):
                continue
            if entry.resolve() == active_resolved:
                continue
            if not name.startswith(("bg_", "local_")):
                continue
            if entry.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                continue
            try:
                mtime = entry.stat().st_mtime
            except OSError:
                continue
            historical.append((mtime, name, entry))

        historical.sort(key=lambda item: (item[0], item[1]), reverse=True)
        for _, _, old_file in historical[MAX_CACHED_BACKGROUNDS:]:
            try:
                old_file.unlink(missing_ok=True)
            except OSError:
                pass

    def _save_cached_image_locked(
        self,
        tmp_path: Path,
        *,
        prefix: str,
        cache_id: str,
        fmt: str,
        width: int,
        height: int,
        luminance: LuminanceProfile,
        tier: int,
        source_label: str,
        crc64: str,
        etag: str = "",
        url: str = "",
        still_fallback: bool = False,
    ) -> BackgroundFrame:
        ext = "jpg" if fmt == "jpeg" else fmt
        safe_id = _sanitize_cache_id(cache_id)
        dest = self.bg_cache_dir / f"{prefix}_{safe_id}.{ext}"
        _atomic_replace(tmp_path, dest)
        meta = {
            "tier": tier,
            "source_label": source_label,
            "image_path": dest.name,
            "crc64": crc64,
            "etag": etag,
            "url": url,
            "width": width,
            "height": height,
            "image_format": fmt,
            "luminance": luminance.to_dict(),
            "updated_at": int(time.time()),
        }
        _atomic_json(self.meta_path, meta)
        self._prune_bg_cache_locked(dest)
        return BackgroundFrame(
            tier=tier,
            source_label=source_label,
            image_path=dest,
            crc64=crc64,
            etag=etag,
            width=width,
            height=height,
            luminance=luminance,
            warning_code=None,
            image_format=fmt,
            is_video=False,
            still_fallback_path=dest if still_fallback else None,
        )

    @staticmethod
    def _resp_header(resp: Any, name: str) -> str:
        headers = getattr(resp, "headers", None)
        if headers is None:
            return ""
        if hasattr(headers, "get"):
            val = headers.get(name)
            if val is not None:
                return str(val)
            for k, v in headers.items():
                if str(k).lower() == name.lower():
                    return str(v)
        return ""

    @staticmethod
    def _resp_status(resp: Any) -> int:
        for attr in ("status", "code"):
            val = getattr(resp, attr, None)
            if type(val) is int:
                return val
        getcode = getattr(resp, "getcode", None)
        if callable(getcode):
            return int(getcode())
        return 200

    def _try_tier1(self, *, effective_reduced_motion: bool) -> BackgroundFrame | None:
        deadline = time.monotonic() + self._hard_timeout

        def _remaining() -> tuple[float, float]:
            rem = deadline - time.monotonic()
            if rem <= 0:
                raise TimeoutError("Background sync hard timeout exceeded.")
            return min(self._connect_timeout, rem), min(self._read_timeout, rem)

        cfg_req = urllib.request.Request(
            YOSTAR_BASE_CONFIG_URL,
            headers={
                "Content-Type": "application/json;charset=UTF-8",
                "Authorization": build_yostar_auth_header(),
                "User-Agent": YOSTAR_USER_AGENT,
            },
            method="GET",
        )
        conn_to, read_to = _remaining()
        with self._open_request(cfg_req, timeout=read_to, connect_timeout=conn_to, deadline=deadline) as resp:
            status = self._resp_status(resp)
            if status != 200:
                raise ValueError(f"Unexpected config HTTP status: {status}")
            ctype = self._resp_header(resp, "Content-Type").lower()
            if "text/html" in ctype:
                raise ValueError("Captive portal HTML Content-Type on config response.")
            try:
                raw_cfg = _read_response_bounded(
                    resp,
                    max_bytes=MAX_CONFIG_BYTES,
                    chunk_size=16 * 1024,
                    deadline=deadline,
                    read_timeout=self._read_timeout,
                )
            except ValueError as exc:
                raise ValueError("Config response exceeded size cap.") from exc
            if _is_html_prefix(raw_cfg):
                raise ValueError("Captive portal HTML body on config response.")
            payload = json.loads(raw_cfg.decode("utf-8"))

        if not isinstance(payload, dict) or payload.get("code") != 200 or not isinstance(payload.get("data"), dict):
            raise ValueError("Invalid Yostar base/config JSON payload.")
        data = payload["data"]

        raw_img_url = str(data.get("launcher_background_img") or "").strip()
        raw_video_url = str(data.get("launcher_background_video") or data.get("launcher_background_mp4") or "").strip()
        raw_poster_url = str(
            data.get("launcher_background_poster") or data.get("launcher_background_still") or ""
        ).strip()
        crc64 = str(data.get("launcher_background_img_crc64") or "").strip()

        video_offered = bool(raw_video_url) or _is_video_url(raw_img_url)
        img_url = raw_img_url
        if (not img_url and video_offered) or _is_video_url(img_url):
            if raw_poster_url and not _is_video_url(raw_poster_url):
                img_url = raw_poster_url
            else:
                # Video-only response with no companion still URL: downgrade to local/bundled still
                try:
                    t2_frame = self._try_tier2()
                except Exception as exc:  # noqa: BLE001
                    log.info("Tier 2 fallback during video downgrade failed: %s", exc)
                    t2_frame = None
                fallback_frame = t2_frame or self._load_bundled_frame(warning_code=None)
                return BackgroundFrame(
                    tier=fallback_frame.tier,
                    source_label=fallback_frame.source_label,
                    image_path=fallback_frame.image_path,
                    crc64=fallback_frame.crc64,
                    etag=fallback_frame.etag,
                    width=fallback_frame.width,
                    height=fallback_frame.height,
                    luminance=fallback_frame.luminance,
                    warning_code=fallback_frame.warning_code,
                    image_format=fallback_frame.image_format,
                    is_video=False,
                    still_fallback_path=fallback_frame.image_path,
                )

        if not is_allowed_bg_url(img_url):
            raise ValueError(f"Disallowed background URL: {img_url}")

        still_fallback_flag = bool(video_offered and effective_reduced_motion)

        with self._lock:
            meta = self._read_meta()
            cached = self._load_cached_frame(required_tier=1, fast_header_only=False)
            if (
                cached is not None
                and meta is not None
                and meta.get("url") == img_url
                and crc64
                and cached.crc64 == crc64
            ):
                if still_fallback_flag:
                    return BackgroundFrame(
                        tier=cached.tier,
                        source_label=cached.source_label,
                        image_path=cached.image_path,
                        crc64=cached.crc64,
                        etag=cached.etag,
                        width=cached.width,
                        height=cached.height,
                        luminance=cached.luminance,
                        warning_code=None,
                        image_format=cached.image_format,
                        is_video=False,
                        still_fallback_path=cached.image_path,
                    )
                return cached

        img_headers: dict[str, str] = {"User-Agent": YOSTAR_USER_AGENT}
        if cached is not None and meta is not None and meta.get("url") == img_url and cached.etag:
            img_headers["If-None-Match"] = cached.etag

        img_req = urllib.request.Request(img_url, headers=img_headers, method="GET")
        conn_to, read_to = _remaining()
        try:
            resp_cm = self._open_request(img_req, timeout=read_to, connect_timeout=conn_to, deadline=deadline)
        except urllib.error.HTTPError as exc:
            if exc.code == 304 and cached is not None:
                if still_fallback_flag:
                    return BackgroundFrame(
                        tier=cached.tier,
                        source_label=cached.source_label,
                        image_path=cached.image_path,
                        crc64=cached.crc64,
                        etag=cached.etag,
                        width=cached.width,
                        height=cached.height,
                        luminance=cached.luminance,
                        warning_code=None,
                        image_format=cached.image_format,
                        is_video=False,
                        still_fallback_path=cached.image_path,
                    )
                return cached
            raise

        with resp_cm as resp:
            status = self._resp_status(resp)
            if status == 304 and cached is not None:
                if still_fallback_flag:
                    return BackgroundFrame(
                        tier=cached.tier,
                        source_label=cached.source_label,
                        image_path=cached.image_path,
                        crc64=cached.crc64,
                        etag=cached.etag,
                        width=cached.width,
                        height=cached.height,
                        luminance=cached.luminance,
                        warning_code=None,
                        image_format=cached.image_format,
                        is_video=False,
                        still_fallback_path=cached.image_path,
                    )
                return cached
            if status != 200:
                raise ValueError(f"Unexpected image HTTP status: {status}")

            ctype = self._resp_header(resp, "Content-Type").lower()
            if "text/html" in ctype:
                raise ValueError("Captive portal HTML Content-Type on image response.")

            cl_raw = self._resp_header(resp, "Content-Length").strip()
            expected_len: int | None = None
            if cl_raw:
                try:
                    expected_len = int(cl_raw)
                except ValueError as exc:
                    raise ValueError(f"Invalid Content-Length header: {cl_raw}") from exc
                if expected_len <= 0 or expected_len > MAX_BG_BYTES:
                    raise ValueError(f"Content-Length out of bounds: {expected_len}")

            etag = self._resp_header(resp, "ETag").strip()
            oss_crc64 = self._resp_header(resp, "x-oss-hash-crc64ecma").strip()

            self.bg_cache_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = self.bg_cache_dir / f".bg_{uuid.uuid4().hex}.tmp"
            bytes_written = 0
            head_buf = bytearray()
            try:
                with tmp_path.open("wb") as out_fh:
                    try:
                        for chunk in _iter_response_chunks(
                            resp,
                            max_bytes=MAX_BG_BYTES,
                            chunk_size=64 * 1024,
                            deadline=deadline,
                            read_timeout=self._read_timeout,
                        ):
                            if len(head_buf) < 256:
                                head_buf.extend(chunk[: 256 - len(head_buf)])
                                if _is_html_prefix(bytes(head_buf)):
                                    raise ValueError("Captive portal HTML body on image response.")
                            bytes_written += len(chunk)
                            out_fh.write(chunk)
                    except ValueError as exc:
                        if "exceeded" in str(exc):
                            raise ValueError("Background image download exceeded 25 MB limit.") from exc
                        raise
                    out_fh.flush()

                if expected_len is not None and bytes_written != expected_len:
                    raise ValueError(f"Truncated image download: {bytes_written} != {expected_len}")

                actual_crc64 = crc64_ecma_file(tmp_path)
                if oss_crc64 and oss_crc64 != actual_crc64:
                    raise ValueError(f"OSS CRC64 mismatch: {actual_crc64} != {oss_crc64}")

                fmt, w, h = validate_image_file(tmp_path)
                lum = compute_luminance_profile(tmp_path)
                effective_crc = crc64 or oss_crc64 or actual_crc64

                with self._lock:
                    return self._save_cached_image_locked(
                        tmp_path,
                        prefix="bg",
                        cache_id=effective_crc,
                        fmt=fmt,
                        width=w,
                        height=h,
                        luminance=lum,
                        tier=1,
                        source_label="online_official",
                        crc64=effective_crc,
                        etag=etag,
                        url=img_url,
                        still_fallback=still_fallback_flag,
                    )
            finally:
                tmp_path.unlink(missing_ok=True)

    def _try_tier2_idb(self) -> BackgroundFrame | None:
        blob_root = self.official_appdata_dir / "IndexedDB" / "file__0.indexeddb.blob"
        if not blob_root.is_dir():
            return None

        candidates: list[tuple[float, str, Path]] = []
        for entry in blob_root.rglob("*"):
            if not entry.is_file():
                continue
            if entry.name.upper() == "LOCK" or entry.name.lower().endswith(".lock"):
                continue
            try:
                st = entry.stat()
            except OSError:
                continue
            if st.st_size <= 0 or st.st_size > MAX_IDB_BLOB_BYTES:
                continue
            candidates.append((st.st_mtime, entry.name, entry))

        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        for _, _, blob_path in candidates:
            try:
                blob = blob_path.read_bytes()
            except OSError:
                continue

            search_pos = 0
            while True:
                idx = blob.find(b"data:image/", search_pos)
                if idx == -1:
                    break
                b64_marker = blob.find(b";base64,", idx, idx + 48)
                if b64_marker == -1:
                    search_pos = idx + 11
                    continue
                b64_start = b64_marker + len(b";base64,")
                m = _BASE64_VALID_RE.match(blob, b64_start)
                if not m:
                    search_pos = b64_start
                    continue
                b64_slice = re.sub(rb"\s+", b"", m.group(0))
                if len(b64_slice) % 4 == 1 and b64_slice.endswith(b"=="):
                    b64_slice = b64_slice[:-1]
                search_pos = m.end()
                try:
                    decoded = base64.b64decode(b64_slice, validate=True)
                except (binascii.Error, ValueError):
                    continue
                if not decoded or len(decoded) > MAX_BG_BYTES:
                    continue
                if detect_image_format(decoded[:16]) is None:
                    continue

                self.bg_cache_dir.mkdir(parents=True, exist_ok=True)
                tmp_path = self.bg_cache_dir / f".idb_{uuid.uuid4().hex}.tmp"
                try:
                    tmp_path.write_bytes(decoded)
                    fmt, w, h = validate_image_file(tmp_path)
                    lum = compute_luminance_profile(tmp_path)
                    sha = _sha256_file(tmp_path)
                    crc64 = crc64_ecma_file(tmp_path)
                    with self._lock:
                        return self._save_cached_image_locked(
                            tmp_path,
                            prefix="local_idb",
                            cache_id=sha[:12],
                            fmt=fmt,
                            width=w,
                            height=h,
                            luminance=lum,
                            tier=2,
                            source_label="local_official_idb",
                            crc64=crc64,
                        )
                except (OSError, ValueError):
                    continue
                finally:
                    tmp_path.unlink(missing_ok=True)
        return None

    @staticmethod
    def _find_asar_node(tree: Mapping[str, Any], rel_path: str) -> Mapping[str, Any] | None:
        cursor: Any = tree
        for part in rel_path.split("/"):
            if not isinstance(cursor, Mapping):
                return None
            files = cursor.get("files")
            if not isinstance(files, Mapping):
                return None
            cursor = files.get(part)
        return cursor if isinstance(cursor, Mapping) else None

    def _try_tier2_asar(self) -> BackgroundFrame | None:
        asar_path = self.official_install_dir / "resources" / "app.asar"
        if not asar_path.is_file():
            return None
        try:
            file_size = asar_path.stat().st_size
            if file_size < 16:
                return None
            with asar_path.open("rb") as fh:
                hdr = fh.read(16)
                if len(hdr) != 16:
                    return None
                u0, total_hdr_sz, _u1, json_sz = struct.unpack("<4I", hdr)
                if (
                    u0 != 4
                    or total_hdr_sz < 8
                    or json_sz <= 0
                    or json_sz > MAX_ASAR_HEADER_BYTES
                    or json_sz > total_hdr_sz
                    or 8 + total_hdr_sz > file_size
                ):
                    return None
                raw_tree = fh.read(json_sz)
                if len(raw_tree) != json_sz:
                    return None
                tree = json.loads(raw_tree.decode("utf-8"))
                if not isinstance(tree, Mapping):
                    return None
                data_base_offset = 8 + total_hdr_sz

                for target_rel, min_w, min_h in (
                    ("out/renderer/assets/bg-df33ba5f.png", MIN_BG_WIDTH, MIN_BG_HEIGHT),
                    ("out/renderer/assets/bg-7cac1ac5.png", 640, 400),
                ):
                    node = self._find_asar_node(tree, target_rel)
                    if node is None:
                        continue
                    raw_bytes: bytes
                    if node.get("unpacked"):
                        unpacked_file = self.official_install_dir / "resources" / "app.asar.unpacked" / target_rel
                        if not unpacked_file.is_file() or unpacked_file.stat().st_size > MAX_BG_BYTES:
                            continue
                        raw_bytes = unpacked_file.read_bytes()
                    else:
                        if "offset" not in node or "size" not in node:
                            continue
                        raw_off = node["offset"]
                        raw_sz = node["size"]
                        if isinstance(raw_off, bool) or isinstance(raw_sz, bool):
                            continue
                        try:
                            offset = int(raw_off)
                            size = int(raw_sz)
                        except (TypeError, ValueError):
                            continue
                        if offset < 0 or size <= 0 or size > MAX_BG_BYTES:
                            continue
                        if data_base_offset + offset + size > file_size:
                            continue
                        fh.seek(data_base_offset + offset)
                        raw_bytes = fh.read(size)
                        if len(raw_bytes) != size:
                            continue

                    integrity = node.get("integrity")
                    if isinstance(integrity, Mapping) and str(integrity.get("algorithm", "")).upper() == "SHA256":
                        expected_hash = str(integrity.get("hash") or "").lower()
                        blocks = integrity.get("blocks")
                        if expected_hash and (not isinstance(blocks, list) or len(blocks) <= 1):
                            if hashlib.sha256(raw_bytes).hexdigest() != expected_hash:
                                continue

                    self.bg_cache_dir.mkdir(parents=True, exist_ok=True)
                    tmp_path = self.bg_cache_dir / f".asar_{uuid.uuid4().hex}.tmp"
                    try:
                        tmp_path.write_bytes(raw_bytes)
                        fmt, w, h = validate_image_file(tmp_path, min_width=min_w, min_height=min_h)
                        lum = compute_luminance_profile(tmp_path)
                        sha = _sha256_file(tmp_path)
                        crc64 = crc64_ecma_file(tmp_path)
                        with self._lock:
                            return self._save_cached_image_locked(
                                tmp_path,
                                prefix="local_asar",
                                cache_id=sha[:12],
                                fmt=fmt,
                                width=w,
                                height=h,
                                luminance=lum,
                                tier=2,
                                source_label="local_official_asar",
                                crc64=crc64,
                            )
                    except (OSError, ValueError):
                        continue
                    finally:
                        tmp_path.unlink(missing_ok=True)
        except (OSError, ValueError, struct.error):
            return None
        return None

    def _try_tier2(self) -> BackgroundFrame | None:
        try:
            idb_frame = self._try_tier2_idb()
            if idb_frame is not None:
                return idb_frame
        except Exception as exc:  # noqa: BLE001 - fall through to ASAR
            log.info("Tier 2a IDB fallback failed: %s", exc)
        try:
            return self._try_tier2_asar()
        except Exception as exc:  # noqa: BLE001 - non-fatal ASAR fallback
            log.info("Tier 2b ASAR fallback failed: %s", exc)
            return None

    def sync_blocking(
        self,
        auto_sync_enabled: bool = True,
        reduced_motion: bool | None = None,
    ) -> BackgroundFrame:
        """Deterministic synchronous Tier 1 -> Tier 2 -> Tier 3 waterfall."""
        eff_reduced = self._effective_reduced_motion(reduced_motion)

        if auto_sync_enabled:
            with self._lock:
                cached_tier1 = self._load_cached_frame(required_tier=1, fast_header_only=False)
            try:
                t1 = self._try_tier1(effective_reduced_motion=eff_reduced)
                if t1 is not None:
                    return t1
            except Exception as exc:  # noqa: BLE001 - non-fatal sync fallback
                log.info("Tier 1 official background sync failed: %s", exc)
            if cached_tier1 is not None:
                return cached_tier1

        try:
            t2 = self._try_tier2()
        except Exception as exc:  # noqa: BLE001 - non-fatal Tier 2 fallback
            log.info("Tier 2 official background fallback failed: %s", exc)
            t2 = None
        if t2 is not None:
            return t2

        return self._load_bundled_frame(warning_code="E-BG-SYNC" if auto_sync_enabled else None)

    @staticmethod
    def _frame_signature(frame: BackgroundFrame) -> tuple[Any, ...]:
        return (
            frame.tier,
            frame.source_label,
            str(frame.image_path),
            frame.crc64,
            frame.warning_code,
            frame.is_video,
            str(frame.still_fallback_path) if frame.still_fallback_path is not None else None,
        )

    def sync_async(
        self,
        on_ready: Callable[[BackgroundFrame], None],
        auto_sync_enabled: bool = True,
        reduced_motion: bool | None = None,
    ) -> threading.Thread:
        """Run sync_blocking on a daemon thread and notify on_ready only if frame/status changed."""
        initial = self.load_initial()

        def _worker() -> None:
            try:
                resolved = self.sync_blocking(
                    auto_sync_enabled=auto_sync_enabled,
                    reduced_motion=reduced_motion,
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("Unexpected background sync worker error: %s", exc)
                return
            if self._frame_signature(resolved) != self._frame_signature(initial):
                try:
                    on_ready(resolved)
                except Exception as exc:  # noqa: BLE001
                    log.warning("bg_sync on_ready callback failed: %s", exc)

        thread = threading.Thread(target=_worker, name="launcher_v2_bg_sync", daemon=True)
        thread.start()
        return thread
