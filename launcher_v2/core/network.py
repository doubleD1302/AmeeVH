"""Bounded JSON/network adapters and parallel download engine for Stella Sora."""
from __future__ import annotations

import collections
import errno
import hashlib
import http.client
import inspect
import json
import logging
import math
import os
import re
import shutil
import socket
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from concurrent.futures import CancelledError as FuturesCancelledError, ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from . import tls
from .config import LAUNCHER_VERSION
from .safety import InstallerError, atomic_json, manifest_sha256, normalize_manifest, relative_name, safe_path, sha256_file
from .types import NotificationItem, OperationEvent, OperationPhase, SupporterData

log = logging.getLogger(__name__)
_REAL_TIME_SLEEP = time.sleep
_TLS_LOCK = threading.Lock()

_FALLBACK_INTERNAL_MAP = {
    "ENDPOINT_INVALID": "E-CONFIG-CHANNEL",
    "ENDPOINT_UNAVAILABLE": "E-CONFIG-CHANNEL",
    "RELEASE_UNAVAILABLE": "E-RELEASE",
    "RATE_LIMITED": "E-HTTP-RATE",
    "SCHEMA_INVALID": "E-DATA-SCHEMA",
    "METADATA_UNVERIFIED": "E-DATA-UNVERIFIED",
    "RELEASE_ASSET_MISMATCH": "E-DATA-SCHEMA",
    "MANIFEST_MISSING": "E-MANIFEST-MISSING",
    "MANIFEST_INVALID": "E-MANIFEST-INVALID",
    "EMPTY_MANIFEST": "E-MANIFEST-INVALID",
    "VERSION_MISSING": "E-MANIFEST-INVALID",
    "VERSION_INVALID": "E-MANIFEST-VERSION",
    "PLATFORM_MISMATCH": "E-MANIFEST-PLATFORM",
    "PATH_TRAVERSAL": "E-SECURITY",
    "PATH_ESCAPE": "E-SECURITY",
    "PATH_NOT_ALLOWED": "E-SECURITY",
    "UNSAFE_PATH": "E-SECURITY",
    "UNTRUSTED_URL": "E-SECURITY",
    "ARCHIVE_INVALID": "E-SECURITY",
    "DOWNGRADE_BLOCKED": "E-DOWNGRADE",
    "HASH_MISMATCH": "E-DL-VERIFY",
    "SIZE_MISMATCH": "E-DL-VERIFY",
    "CORRUPT_PAYLOAD": "E-DL-VERIFY",
    "DOWNLOAD_INCOMPLETE": "E-DL-VERIFY",
    "DOWNLOAD_RANGE_INVALID": "E-DL-RANGE",
    "DOWNLOAD_TIMEOUT": "E-DL-TIMEOUT",
    "DOWNLOAD_INVALID": "E-DL-RESPONSE",
    "DOWNLOAD_RESPONSE_INVALID": "E-DL-RESPONSE",
    "DOWNLOAD_FAILED": "E-DL-FAILED",
    "PAYLOAD_UNAVAILABLE": "E-DL-FAILED",
    "NET_CAPTIVE": "E-NET-CAPTIVE",
    "PARALLEL_DL": "E-PARALLEL-DL",
    "CANCELLED": "E-CANCELLED",
}


@dataclass(frozen=True)
class _FallbackDiagnosis:
    code: str


def _fallback_diagnose(exc: BaseException) -> _FallbackDiagnosis:
    cur: Optional[BaseException] = exc
    seen: set[int] = set()
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, InstallerError):
            internal = getattr(cur, "code", "") or ""
            if internal not in ("DOWNLOAD_FAILED", "TRANSACTION_FAILED", "NETWORK"):
                mapped = _FALLBACK_INTERNAL_MAP.get(internal)
                if mapped:
                    return _FallbackDiagnosis(mapped)
        if isinstance(cur, urllib.error.HTTPError):
            if cur.code == 407:
                return _FallbackDiagnosis("E-NET-PROXY")
            return _FallbackDiagnosis(f"E-HTTP-{int(cur.code)}")
        if isinstance(cur, ssl.SSLCertVerificationError):
            return _FallbackDiagnosis("E-NET-TLS-CERT")
        if isinstance(cur, ssl.SSLError):
            return _FallbackDiagnosis("E-NET-TLS-CERT" if "CERTIFICATE" in str(cur).upper() else "E-NET-TLS")
        if isinstance(cur, socket.gaierror):
            return _FallbackDiagnosis("E-NET-DNS")
        if isinstance(cur, (socket.timeout, TimeoutError)):
            return _FallbackDiagnosis("E-NET-TIMEOUT")
        if isinstance(cur, ConnectionRefusedError):
            return _FallbackDiagnosis("E-NET-REFUSED")
        if isinstance(cur, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, http.client.IncompleteRead, http.client.RemoteDisconnected)):
            return _FallbackDiagnosis("E-NET-RESET")
        if isinstance(cur, (json.JSONDecodeError, UnicodeDecodeError)):
            return _FallbackDiagnosis("E-DATA-JSON")
        if isinstance(cur, urllib.error.URLError) and isinstance(cur.reason, BaseException):
            cur = cur.reason
            continue
        cur = cur.__cause__ or cur.__context__
    if isinstance(exc, InstallerError):
        mapped = _FALLBACK_INTERNAL_MAP.get(getattr(exc, "code", "") or "")
        if mapped:
            return _FallbackDiagnosis(mapped)
    return _FallbackDiagnosis("E-NET")


def _diagnose(exc: BaseException):
    try:
        from .error_catalog import diagnose as _catalog_diagnose
    except ModuleNotFoundError as imp_err:
        expected = f"{__package__}.error_catalog" if __package__ else "error_catalog"
        if imp_err.name in (expected, "error_catalog"):
            return _fallback_diagnose(exc)
        raise
    return _catalog_diagnose(exc)


def _ensure_tls_installed() -> None:
    if urllib.request._opener is not None:
        return
    with _TLS_LOCK:
        if urllib.request._opener is None:
            tls.install()


def _urlopen(req, timeout):
    _ensure_tls_installed()
    return urllib.request.urlopen(req, timeout=timeout)


def valid_url(url):
    try:
        if not isinstance(url, str):
            return False
        u = urllib.parse.urlparse(url)
        return u.scheme in ("https", "http") and bool(u.hostname) and not u.username and not u.password
    except ValueError:
        return False


def version_tuple(v):
    return tuple(int(n) for n in re.findall(r"\d+", str(v).split("-")[0]))


def _header_value(headers, name: str) -> str:
    if not headers:
        return ""
    if isinstance(headers, dict):
        target = name.lower()
        for k, v in headers.items():
            if str(k).lower() == target:
                return str(v or "")
        return ""
    getter = getattr(headers, "get", None)
    if callable(getter):
        return str(getter(name) or "")
    return ""


def _is_html_content_type(headers) -> bool:
    ct = _header_value(headers, "Content-Type").split(";", 1)[0].strip().lower()
    return ct in ("text/html", "application/xhtml+xml")


def _is_html_body(data: bytes) -> bool:
    if not data:
        return False
    head = data[:512].lstrip(b" \t\r\n\xef\xbb\xbf").lower()
    return head.startswith((b"<!doctype html", b"<html"))


def _is_cancelled(cancel_event: Optional[threading.Event], should_cancel: Optional[Callable[[], bool]]) -> bool:
    return bool((cancel_event is not None and cancel_event.is_set()) or (should_cancel is not None and should_cancel()))


def _is_disk_io_error(exc: BaseException) -> bool:
    cur: Optional[BaseException] = exc
    seen: set[int] = set()
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, (urllib.error.URLError, http.client.HTTPException, TimeoutError, ConnectionError, ssl.SSLError, socket.gaierror)):
            return False
        if isinstance(cur, OSError):
            eno = getattr(cur, "errno", None)
            win = getattr(cur, "winerror", None)
            if isinstance(cur, PermissionError) or eno in (errno.ENOSPC, errno.EACCES, errno.EPERM, errno.EROFS, errno.EIO, errno.EMFILE, errno.ENFILE) or win in (5, 32, 33, 39, 112):
                return True
        cur = cur.__cause__ or cur.__context__
    return False


class _PoolAborted(Exception):
    """Internal sentinel used when a sibling worker exits after another worker failed."""


class _WorkerProgressSink:
    _is_worker_sink = True

    def __init__(self, aggregator: "DownloadProgressAggregator", key: str, label: str):
        self._aggregator = aggregator
        self._key = key
        self._label = label

    def __call__(self, event: OperationEvent) -> None:
        if event.completed <= 0:
            self._aggregator.reset_file(self._key, 0)
        else:
            self._aggregator.update_file(self._key, event.completed, self._label)


class DownloadProgressAggregator:
    """Thread-safe progress aggregator with 2.5s sliding-window EWMA speed, ETA, and ~10 Hz throttle."""

    def __init__(
        self,
        items: Optional[list[tuple[str, int, int]]] = None,
        event_cb: Optional[Callable[[OperationEvent], None]] = None,
        operation_id: str = "download",
        default_message: str = "Đang tải gói bản dịch...",
        window_seconds: float = 2.5,
        emit_interval: float = 0.1,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._lock = threading.Lock()
        self._event_cb = event_cb
        self._operation_id = operation_id
        self._default_message = default_message
        self._window_seconds = float(window_seconds)
        self._emit_interval = float(emit_interval)
        self._clock = clock

        self._sizes: dict[str, int] = {}
        self._bytes: dict[str, int] = {}
        self._done: dict[str, bool] = {}
        if items:
            for key, size, initial_bytes in items:
                s = max(0, int(size))
                init = min(s, max(0, int(initial_bytes)))
                self._sizes[key] = s
                self._bytes[key] = init
                self._done[key] = False
        self._total_bytes: int = sum(self._sizes.values())
        self._files_total: int = len(self._sizes)
        self._samples: collections.deque[tuple[float, int]] = collections.deque()
        self._start_ts: float = self._clock()
        self._last_ewma_ts: Optional[float] = None
        self._ewma_speed: float = 0.0
        self._last_emit_ts: float = 0.0
        self._emitted_once: bool = False

    def _compute_metrics_locked(self, now: float) -> tuple[int, float, Optional[float], int]:
        cutoff = now - self._window_seconds
        while self._samples and self._samples[0][0] <= cutoff:
            self._samples.popleft()
        window_bytes = sum(b for _, b in self._samples)
        if window_bytes <= 0:
            inst_speed = 0.0
        else:
            window_start = max(self._start_ts, cutoff)
            dt_window = max(now - window_start, 0.05)
            inst_speed = window_bytes / dt_window
        if self._last_ewma_ts is None:
            self._ewma_speed = inst_speed
            self._last_ewma_ts = now
        else:
            dt_step = now - self._last_ewma_ts
            if dt_step > 0:
                alpha = 1.0 - math.exp(-dt_step / 1.0)
                self._ewma_speed = alpha * inst_speed + (1.0 - alpha) * self._ewma_speed
                self._last_ewma_ts = now
        speed_bps = self._ewma_speed if self._ewma_speed >= 1.0 else 0.0
        bytes_done = sum(self._bytes.values())
        remaining = max(0, self._total_bytes - bytes_done)
        eta_seconds = (remaining / speed_bps) if speed_bps > 1024.0 else None
        files_completed = sum(1 for v in self._done.values() if v)
        return bytes_done, speed_bps, eta_seconds, files_completed

    def reset_file(self, key: str, current_bytes: int = 0) -> None:
        with self._lock:
            if key not in self._sizes:
                return
            self._bytes[key] = min(self._sizes[key], max(0, int(current_bytes)))
            self._done[key] = False

    def update_file(self, key: str, current_bytes: int, message: Optional[str] = None, force: bool = False) -> None:
        evt: Optional[OperationEvent] = None
        with self._lock:
            if key not in self._sizes:
                return
            now = self._clock()
            clamped = min(self._sizes[key], max(0, int(current_bytes)))
            delta = clamped - self._bytes[key]
            if delta > 0:
                self._samples.append((now, delta))
            self._bytes[key] = clamped
            bytes_done, speed_bps, eta_seconds, files_completed = self._compute_metrics_locked(now)
            if self._event_cb and (force or not self._emitted_once or (now - self._last_emit_ts >= self._emit_interval)):
                self._last_emit_ts = now
                self._emitted_once = True
                evt = OperationEvent(
                    self._operation_id,
                    OperationPhase.DOWNLOAD,
                    message or self._default_message,
                    bytes_done,
                    self._total_bytes,
                    "bytes",
                    speed_bps=speed_bps,
                    eta_seconds=eta_seconds,
                    files_completed=files_completed,
                    files_total=self._files_total,
                )
        if evt is not None and self._event_cb:
            self._event_cb(evt)

    def complete_file(self, key: str, message: Optional[str] = None) -> None:
        evt: Optional[OperationEvent] = None
        with self._lock:
            if key not in self._sizes:
                return
            now = self._clock()
            self._bytes[key] = self._sizes[key]
            self._done[key] = True
            bytes_done, speed_bps, eta_seconds, files_completed = self._compute_metrics_locked(now)
            if self._event_cb:
                self._last_emit_ts = now
                self._emitted_once = True
                evt = OperationEvent(
                    self._operation_id,
                    OperationPhase.DOWNLOAD,
                    message or key,
                    bytes_done,
                    self._total_bytes,
                    "bytes",
                    speed_bps=speed_bps,
                    eta_seconds=eta_seconds,
                    files_completed=files_completed,
                    files_total=self._files_total,
                )
        if evt is not None and self._event_cb:
            self._event_cb(evt)

    def finish(self, message: str = "Hoàn tất tải gói.") -> None:
        evt: Optional[OperationEvent] = None
        with self._lock:
            now = self._clock()
            for key, size in self._sizes.items():
                self._bytes[key] = size
                self._done[key] = True
            bytes_done, speed_bps, _eta, files_completed = self._compute_metrics_locked(now)
            if self._event_cb:
                self._last_emit_ts = now
                self._emitted_once = True
                evt = OperationEvent(
                    self._operation_id,
                    OperationPhase.DOWNLOAD,
                    message,
                    bytes_done,
                    self._total_bytes,
                    "bytes",
                    speed_bps=speed_bps,
                    eta_seconds=0.0 if self._total_bytes > 0 else None,
                    files_completed=files_completed,
                    files_total=self._files_total,
                )
        if evt is not None and self._event_cb:
            self._event_cb(evt)

    def worker_callback(self, key: str, label: str) -> Callable[[OperationEvent], None]:
        return _WorkerProgressSink(self, key, label)


class NetworkService:
    def __init__(self, update_url=None, notifications_url=None, cache_dir=None, timeout=15, max_workers: int = 4):
        self.update_url = update_url
        self.notifications_url = notifications_url
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.timeout = timeout
        self.max_workers = max(1, min(4, int(max_workers)))
        self.notification_status = "unavailable"
        self.notification_message = "Chưa tải thông báo."
        self.connection_status = "Chưa kiểm tra kết nối"
        self.notification_version = None
        self._last_release = None
        self._last_release_ts = 0.0
        self._release_lock = threading.Lock()
        self._tls_local = threading.local()

    def _json(self, url, expected_sha=None, expected_size=None):
        if not valid_url(url):
            raise InstallerError("Endpoint không phải HTTP/HTTPS hợp lệ.", "ENDPOINT_INVALID")
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"StellaSora-Launcher/{LAUNCHER_VERSION}", "Accept": "application/json"},
        )
        with _urlopen(req, timeout=self.timeout) as r:
            data = r.read(4 * 1024 * 1024 + 1)
            if len(data) > 4 * 1024 * 1024:
                raise InstallerError("JSON máy chủ quá lớn.", "SCHEMA_INVALID")
            if _is_html_content_type(getattr(r, "headers", None)) or _is_html_body(data):
                raise InstallerError(
                    "Phát hiện trang đăng nhập mạng (Captive Portal) thay vì dữ liệu JSON từ máy chủ.",
                    "NET_CAPTIVE",
                )
            if expected_size is not None and len(data) != expected_size:
                raise InstallerError("Metadata tải về không đúng kích thước đã công bố.", "SIZE_MISMATCH")
            if expected_sha and hashlib.sha256(data).hexdigest() != expected_sha.lower():
                raise InstallerError("Metadata tải về không khớp SHA256 của bản phát hành.", "HASH_MISMATCH")
            result = json.loads(data.decode("utf8"))
            if not isinstance(result, dict):
                raise InstallerError("Máy chủ trả JSON sai định dạng.", "SCHEMA_INVALID")
            return result

    def _notifications(self, d):
        raw = d.get("announcements", d.get("notifications"))
        if not isinstance(raw, list):
            raise InstallerError("Thông báo thiếu danh sách announcements.", "SCHEMA_INVALID")
        out = []
        ids = set()
        for e in raw:
            if not isinstance(e, dict) or not all(isinstance(e.get(k), str) for k in ("id", "title", "content")) or e["id"] in ids:
                raise InstallerError("Thông báo chứa mục không hợp lệ/trùng ID.", "SCHEMA_INVALID")
            ids.add(e["id"])
            link = e.get("link_url") or e.get("url")
            if link and not valid_url(link):
                link = None
            out.append(
                NotificationItem(
                    e["id"],
                    e["title"],
                    str(e.get("summary", e["content"][:160])),
                    e["content"],
                    str(e.get("category", e.get("type", "notice"))),
                    str(e.get("badge", e.get("type", "Thông báo"))),
                    str(e.get("date", "")),
                    link,
                    bool(e.get("is_unread", False)),
                )
            )
        return out

    def fetch_notifications(self, fallback_path=None):
        cache = self.cache_dir / "notifications.json" if self.cache_dir else None
        failure = ""
        if self.notifications_url:
            try:
                d = self._json(self.notifications_url)
                items = self._notifications(d)
                self.notification_version = str(d.get("version", "Chưa công bố"))
                if cache:
                    atomic_json(cache, d)
                self.notification_status = "online" if items else "empty"
                self.notification_message = "Thông báo trực tuyến" if items else "Máy chủ hiện chưa có thông báo."
                self.connection_status = "Kết nối thành công"
                return items
            except Exception as e:
                failure = str(e)
                self.connection_status = "Lỗi kết nối thông báo"
        for path, label in ((cache, "cached"), (Path(fallback_path) if fallback_path else None, "bundled")):
            if path and path.is_file():
                try:
                    d = json.loads(path.read_text(encoding="utf8"))
                    items = self._notifications(d)
                    self.notification_version = str(d.get("version", "Chưa công bố"))
                    self.notification_status = label
                    self.notification_message = ("Bản lưu ngoại tuyến" if label == "cached" else "Thông báo đi kèm launcher") + (
                        ". Không tải được dữ liệu mới: " + failure if failure else ""
                    )
                    return items
                except Exception as e:
                    failure = str(e)
        self.notification_status = "error" if failure else "empty"
        self.notification_message = "Không đọc được thông báo: " + failure if failure else "Chưa có thông báo."
        return []

    def _validate_release(self, d):
        if not isinstance(d, dict) or not isinstance(d.get("tag_name"), str) or not isinstance(d.get("assets"), list):
            raise InstallerError("Bản phát hành thiếu thông tin hợp lệ.", "SCHEMA_INVALID")
        if d.get("draft") or d.get("prerelease"):
            raise InstallerError("Kênh đang trỏ đến bản nháp/thử nghiệm.", "RELEASE_UNAVAILABLE")
        for a in d["assets"]:
            if (
                not isinstance(a, dict)
                or not isinstance(a.get("name"), str)
                or not isinstance(a.get("size"), int)
                or isinstance(a.get("size"), bool)
                or not valid_url(a.get("browser_download_url", ""))
            ):
                raise InstallerError("Thông tin tệp phát hành không hợp lệ.", "SCHEMA_INVALID")
        return d

    def release(self):
        if not self.update_url:
            raise InstallerError("Chưa cấu hình kênh cập nhật.", "ENDPOINT_UNAVAILABLE")
        try:
            d = self._validate_release(self._json(self.update_url))
            with self._release_lock:
                self._last_release = d
                self._last_release_ts = time.monotonic()
            if self.cache_dir:
                try:
                    atomic_json(self.cache_dir / "release.json", d)
                except OSError:
                    pass
            self.connection_status = "Kết nối thành công"
            return d
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                with self._release_lock:
                    if self._last_release is not None and (time.monotonic() - self._last_release_ts) < 900:
                        self.connection_status = "Dùng bộ nhớ đệm (GitHub giới hạn lượt gọi)"
                        return self._last_release
                if self.cache_dir:
                    cached = self.cache_dir / "release.json"
                    try:
                        if cached.is_file() and (time.time() - cached.stat().st_mtime) < 900:
                            d = self._validate_release(json.loads(cached.read_text(encoding="utf8")))
                            with self._release_lock:
                                self._last_release = d
                                self._last_release_ts = time.monotonic()
                            self.connection_status = "Dùng bộ nhớ đệm (GitHub giới hạn lượt gọi)"
                            return d
                    except (OSError, ValueError, InstallerError):
                        pass
                raise InstallerError(
                    f"GitHub đang tạm giới hạn lượt truy cập API (HTTP {exc.code}). Vui lòng đợi vài phút rồi thử lại.",
                    "RATE_LIMITED",
                ) from exc
            raise

    def _asset_digest(self, asset, required=False):
        value = asset.get("digest", "")
        if re.fullmatch("sha256:[0-9a-fA-F]{64}", str(value)):
            return value[7:].lower()
        if required:
            raise InstallerError("Tệp phát hành chưa có SHA256 để xác minh: " + asset.get("name", "metadata"), "METADATA_UNVERIFIED")
        return None

    def _manifest_for_release(self, release, manifest_url=None):
        if release is None:
            if manifest_url:
                return self._json(manifest_url), {"source": "explicit_custom_manifest"}
            raise InstallerError("Chưa đọc được bản phát hành trực tuyến.", "RELEASE_UNAVAILABLE")
        matches = [a for a in release["assets"] if a["name"] in ("patch_manifest.json", "stella_patch_manifest.json")]
        asset = (
            next((a for a in release["assets"] if manifest_url and a["browser_download_url"] == manifest_url), None)
            if manifest_url
            else (matches[0] if matches else None)
        )
        if asset:
            digest = self._asset_digest(asset, True)
            raw = self._json(asset["browser_download_url"], digest, asset["size"])
            return raw, {"source": "release_asset", "asset": asset["name"], "sha256": digest, "size": asset["size"], "release_tag": release["tag_name"]}
        if manifest_url:
            return self._json(manifest_url), {"source": "explicit_custom_manifest", "release_tag": release["tag_name"]}
        raise InstallerError("Bản phát hành chưa có bảng kê tệp tương thích.", "MANIFEST_MISSING")

    def _windows_manifest(self, raw):
        manifest = normalize_manifest(raw)
        platform = str(manifest.get("platform", "windows")).lower()
        if platform not in ("windows", "win", "pc"):
            raise InstallerError("Bảng kê không dành cho Windows.", "PLATFORM_MISMATCH")
        return manifest

    def check_for_updates(self, current_version="0.9.8", release_data=None):
        base = {
            "status": "unavailable",
            "has_update": False,
            "latest_version": None,
            "download_url": None,
            "message": "Chưa có kênh cập nhật launcher đã xác minh.",
        }
        if not self.update_url:
            return base
        try:
            d = release_data if release_data is not None else self.release()
            latest = d["tag_name"]
            new = version_tuple(latest) > version_tuple(current_version)
            assets = d.get("assets", [])
            asset = None
            for a in assets:
                n = a.get("name", "").lower()
                if a.get("name", "").endswith(".exe") and not n.startswith("helper"):
                    if any(k in n for k in ("launcher", "windows", "stellasora")):
                        asset = a
                        break
            if not asset:
                for a in assets:
                    if a.get("name", "").endswith(".exe") and not a.get("name", "").lower().startswith("helper"):
                        asset = a
                        break
            digest = self._asset_digest(asset) if asset else None
            if asset and not digest:
                sums_asset = next((a for a in assets if a.get("name") == "SHA256SUMS.txt"), None)
                if sums_asset and valid_url(sums_asset.get("browser_download_url", "")):
                    try:
                        sreq = urllib.request.Request(
                            sums_asset["browser_download_url"],
                            headers={"User-Agent": f"StellaSora-Launcher/{LAUNCHER_VERSION}"},
                        )
                        with _urlopen(sreq, timeout=self.timeout) as sresp:
                            stext = sresp.read(64 * 1024).decode("utf-8", errors="ignore")
                            for sline in stext.splitlines():
                                sparts = sline.strip().split()
                                if len(sparts) >= 2 and re.fullmatch(r"[0-9a-fA-F]{64}", sparts[0]):
                                    sname = sparts[1].lstrip("*")
                                    if sname == asset["name"] or (sname == "StellaSora_Launcher.exe" and "launcher" in asset["name"].lower()):
                                        digest = sparts[0].lower()
                                        break
                    except Exception:
                        pass
            actionable = bool(new and asset and digest)
            return {
                **base,
                "status": "online",
                "has_update": new,
                "latest_version": latest,
                "download_url": asset["browser_download_url"] if actionable else None,
                "asset": asset,
                "sha256": digest if actionable else None,
                "message": (
                    "Có bản cập nhật launcher "
                    + latest
                    + (". Có thể tự động tải và cập nhật." if actionable else "; chưa có tệp được xác minh để tự cập nhật.")
                )
                if new
                else f"Launcher hiện tại ({current_version}) là phiên bản mới nhất.",
                "changelog": d.get("body", ""),
            }
        except Exception as exc:
            return {**base, "status": "error", "message": "Không kiểm tra được cập nhật: " + str(exc), "error_code": _diagnose(exc).code}

    def sync_channel(self, fallback_path, current_version="0.9.8", manifest_url=None, check_launcher=True):
        items = self.fetch_notifications(fallback_path)
        release = None
        release_status = "error"
        release_error = ""
        release_error_code = ""
        manifest_status = "unavailable"
        manifest_error = ""
        manifest_error_code = ""
        translation_version = None
        file_count = None
        translation_scope = None
        cache_warning = ""
        translation_game = None
        translation_resource = None
        m_sha = None
        legacy_m_sha = None

        try:
            release = self.release()
            release_status = "online"
            if self.cache_dir:
                try:
                    atomic_json(self.cache_dir / "release.json", release)
                except OSError as exc:
                    cache_warning = "Đã đọc trực tuyến nhưng chưa lưu được bản dự phòng: " + str(exc)
        except Exception as exc:
            release_error = str(exc)
            release_error_code = _diagnose(exc).code
            cached = self.cache_dir / "release.json" if self.cache_dir else None
            if cached and cached.is_file():
                try:
                    release = self._validate_release(json.loads(cached.read_text(encoding="utf8")))
                    release_status = "cached"
                except (OSError, ValueError, InstallerError):
                    pass

        update = {"status": release_status, "has_update": False, "download_url": None, "message": "Chưa lấy được thông tin launcher trực tuyến."}
        if release_status == "online":
            update = (
                self.check_for_updates(current_version, release)
                if check_launcher
                else {"status": "not_checked", "has_update": False, "download_url": None, "message": "Đã tắt kiểm tra launcher lúc mở. Bạn vẫn có thể kiểm tra thủ công."}
            )
            try:
                raw, binding = self._manifest_for_release(release, manifest_url)
                manifest = self._windows_manifest(raw)
                translation_version = manifest["version"]
                file_count = len(manifest["files"])
                translation_game = manifest["client_game_version"]
                translation_resource = manifest["resource_version"]
                translation_scope = "images_only" if all(path.startswith("Persistent_Store/AssetBundles/") for path in manifest["files"]) else "declared_files"
                m_sha = manifest_sha256(manifest)
                legacy_m_sha = hashlib.sha256(json.dumps({**manifest, "source_metadata": binding}, sort_keys=True).encode("utf-8")).hexdigest()
                manifest_status = "online"
            except Exception as exc:
                manifest_status = "error"
                manifest_error = str(exc)
                manifest_error_code = _diagnose(exc).code

        if manifest_url and release_status != "online":
            try:
                raw, binding = self._manifest_for_release(None, manifest_url)
                manifest = self._windows_manifest(raw)
                translation_version = manifest["version"]
                file_count = len(manifest["files"])
                translation_game = manifest["client_game_version"]
                translation_resource = manifest["resource_version"]
                translation_scope = "images_only" if all(path.startswith("Persistent_Store/AssetBundles/") for path in manifest["files"]) else "declared_files"
                m_sha = manifest_sha256(manifest)
                legacy_m_sha = hashlib.sha256(json.dumps({**manifest, "source_metadata": binding}, sort_keys=True).encode("utf-8")).hexdigest()
                manifest_status = "online"
            except Exception as exc:
                manifest_status = "error"
                manifest_error = str(exc)
                manifest_error_code = _diagnose(exc).code

        fresh = self.notification_status in ("online", "empty") and release_status == "online" and manifest_status == "online"
        return {
            "notifications": items,
            "notification_status": self.notification_status,
            "notification_message": self.notification_message,
            "notification_version": self.notification_version,
            "release_status": release_status,
            "release_version": release.get("tag_name") if release else None,
            "release_notes": str(release.get("body") or "")[:8000] if release_status == "online" else "",
            "release_error": release_error,
            "release_error_code": release_error_code,
            "translation_version": translation_version,
            "translation_game": translation_game,
            "translation_resource": translation_resource,
            "manifest_status": manifest_status,
            "manifest_error": manifest_error,
            "manifest_error_code": manifest_error_code,
            "manifest_sha256": m_sha,
            "legacy_manifest_sha256": legacy_m_sha,
            "translation_file_count": file_count,
            "translation_scope": translation_scope,
            "cache_warning": cache_warning,
            "update": update,
            "fresh": fresh,
            "message": "Đã đọc thông tin mới từ GitHub." if fresh else "Đồng bộ chưa đầy đủ. Xem trạng thái từng nguồn bên dưới.",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def _check_abort(self, cancel_event: Optional[threading.Event], should_cancel: Optional[Callable[[], bool]]) -> None:
        if _is_cancelled(cancel_event, should_cancel):
            raise InstallerError("Đã huỷ tải tệp.", "CANCELLED")
        pool_abort = getattr(self._tls_local, "pool_abort", None)
        if pool_abort is not None and pool_abort.is_set():
            raise _PoolAborted()

    def _supports_cancel_kwargs(self) -> bool:
        fn = self.download
        if getattr(fn, "__func__", None) is NetworkService.download:
            return True
        side_effect = getattr(fn, "side_effect", None)
        if callable(side_effect):
            fn = side_effect
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return False
        for p in sig.parameters.values():
            if p.kind == inspect.Parameter.VAR_KEYWORD or p.name in ("cancel_event", "should_cancel"):
                return True
        return False

    def download(
        self,
        url,
        dest,
        size,
        sha=None,
        event_cb=None,
        operation_id="download",
        max_retries=5,
        cancel_event: Optional[threading.Event] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
    ):
        if not valid_url(url) or not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise InstallerError("Thiếu URL/kích thước tải hợp lệ.", "DOWNLOAD_INVALID")
        self._check_abort(cancel_event, should_cancel)
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_file() and dest.stat().st_size == size:
            if not sha or sha256_file(dest) == sha.lower():
                if event_cb:
                    if getattr(event_cb, "_is_worker_sink", False):
                        event_cb(OperationEvent(operation_id, OperationPhase.DOWNLOAD, dest.name, size, size, "bytes"))
                    else:
                        event_cb(
                            OperationEvent(
                                operation_id,
                                OperationPhase.DOWNLOAD,
                                dest.name,
                                size,
                                size,
                                "bytes",
                                files_completed=1,
                                files_total=1,
                            )
                        )
                return dest
        tag = sha[:12] if sha else str(size)
        part = dest.with_name(f"{dest.name}.{tag}.part")
        standalone_agg: Optional[DownloadProgressAggregator] = None
        emit_cb = event_cb
        if event_cb is not None and not getattr(event_cb, "_is_worker_sink", False):
            init_part = part.stat().st_size if part.is_file() and 0 < part.stat().st_size < size else 0
            standalone_agg = DownloadProgressAggregator([(dest.name, size, init_part)], event_cb, operation_id, dest.name)
            emit_cb = standalone_agg.worker_callback(dest.name, dest.name)

        stream_timeout = max(45, self.timeout)
        total_deadline = time.monotonic() + max(900, int(size / 15000))
        chunk_size = 256 * 1024
        attempt = 0
        last_error = None
        last_exc = None
        while attempt < max_retries:
            self._check_abort(cancel_event, should_cancel)
            if time.monotonic() > total_deadline:
                break
            attempt += 1
            current_size = part.stat().st_size if part.is_file() else 0
            if current_size > size:
                part.unlink(missing_ok=True)
                current_size = 0
                if emit_cb:
                    emit_cb(OperationEvent(operation_id, OperationPhase.DOWNLOAD, dest.name, 0, size, "bytes"))
            elif current_size == size:
                if not sha or sha256_file(part) == sha.lower():
                    os.replace(part, dest)
                    if standalone_agg is not None:
                        standalone_agg.complete_file(dest.name, dest.name)
                    elif emit_cb:
                        emit_cb(OperationEvent(operation_id, OperationPhase.DOWNLOAD, dest.name, size, size, "bytes"))
                    return dest
                part.unlink(missing_ok=True)
                current_size = 0
                if emit_cb:
                    emit_cb(OperationEvent(operation_id, OperationPhase.DOWNLOAD, dest.name, 0, size, "bytes"))
            headers = {"User-Agent": f"StellaSora-Launcher/{LAUNCHER_VERSION}", "Accept-Encoding": "identity"}
            if current_size > 0:
                headers["Range"] = f"bytes={current_size}-"
            try:
                log.info(
                    "Download attempt=%s/%s file=%s host=%s offset=%s expected=%s",
                    attempt,
                    max_retries,
                    dest.name,
                    urllib.parse.urlparse(url).hostname,
                    current_size,
                    size,
                )
                req = urllib.request.Request(url, headers=headers)
                with _urlopen(req, timeout=stream_timeout) as resp:
                    status = getattr(resp, "status", 200)
                    response_headers = getattr(resp, "headers", {})
                    if status in (200, 206) and _is_html_content_type(response_headers):
                        raise InstallerError(
                            "Phát hiện trang đăng nhập mạng (Captive Portal) thay vì tệp cần tải.",
                            "NET_CAPTIVE",
                        )
                    response_limit = size
                    if status == 206:
                        match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", _header_value(response_headers, "Content-Range"))
                        if not match:
                            raise InstallerError("Máy chủ trả phạm vi tải tiếp không hợp lệ.", "DOWNLOAD_RANGE_INVALID")
                        start, end, total = map(int, match.groups())
                        length = _header_value(response_headers, "Content-Length") or None
                        if (
                            start != current_size
                            or total != size
                            or not 0 <= start <= end < size
                            or (length is not None and (not re.fullmatch(r"\d+", length) or int(length) != end - start + 1))
                        ):
                            raise InstallerError("Phạm vi tải tiếp không khớp tệp cần tải.", "DOWNLOAD_RANGE_INVALID")
                        response_limit = end + 1
                        mode = "ab" if current_size > 0 else "wb"
                    elif status == 200:
                        length = _header_value(response_headers, "Content-Length") or None
                        if length is not None and (not re.fullmatch(r"\d+", length) or int(length) != size):
                            raise InstallerError(
                                f"Máy chủ công bố kích thước tệp khác bảng kê ({length}/{size} bytes).",
                                "SIZE_MISMATCH",
                            )
                        if current_size:
                            log.info("Download server ignored Range; restarting file=%s", dest.name)
                            if emit_cb:
                                emit_cb(OperationEvent(operation_id, OperationPhase.DOWNLOAD, dest.name, 0, size, "bytes"))
                        current_size = 0
                        mode = "wb"
                    else:
                        raise InstallerError("Máy chủ trả trạng thái tải không hợp lệ.", "DOWNLOAD_RESPONSE_INVALID")

                    first_chunk = resp.read(chunk_size)
                    if first_chunk and _is_html_body(first_chunk):
                        raise InstallerError(
                            "Phát hiện trang đăng nhập mạng (Captive Portal) thay vì tệp cần tải.",
                            "NET_CAPTIVE",
                        )

                    self._check_abort(cancel_event, should_cancel)
                    with part.open(mode) as out:
                        n = current_size
                        try:
                            chunk = first_chunk
                            while chunk:
                                self._check_abort(cancel_event, should_cancel)
                                if time.monotonic() > total_deadline:
                                    raise InstallerError("Tải quá thời hạn cho phép. Vui lòng thử lại.", "DOWNLOAD_TIMEOUT")
                                n += len(chunk)
                                if n > response_limit:
                                    raise InstallerError("Máy chủ trả về dung lượng lớn hơn dự kiến.", "SIZE_MISMATCH")
                                out.write(chunk)
                                if emit_cb:
                                    emit_cb(OperationEvent(operation_id, OperationPhase.DOWNLOAD, dest.name, n, size, "bytes"))
                                self._check_abort(cancel_event, should_cancel)
                                chunk = resp.read(chunk_size)
                        finally:
                            out.flush()
                            os.fsync(out.fileno())
                self._check_abort(cancel_event, should_cancel)
                if part.stat().st_size != size:
                    raise InstallerError(f"Tải chưa đủ dữ liệu ({part.stat().st_size}/{size} bytes).", "DOWNLOAD_INCOMPLETE")
                if sha and sha256_file(part) != sha.lower():
                    part.unlink(missing_ok=True)
                    raise InstallerError("Tệp tải về không khớp mã SHA256.", "HASH_MISMATCH")
                os.replace(part, dest)
                if standalone_agg is not None:
                    standalone_agg.complete_file(dest.name, dest.name)
                return dest
            except _PoolAborted:
                raise
            except (TimeoutError, urllib.error.URLError, http.client.HTTPException, ConnectionError, OSError) as exc:
                if isinstance(exc, urllib.error.HTTPError):
                    detail = f"HTTP {exc.code}"
                elif isinstance(exc, urllib.error.URLError):
                    detail = f"URLError: {exc.reason}"
                else:
                    detail = type(exc).__name__
                last_error = f"Lỗi kết nối: {detail}."
                last_exc = exc
                if isinstance(exc, urllib.error.HTTPError) and exc.code == 416:
                    part.unlink(missing_ok=True)
                log.warning("Download interrupted attempt=%s/%s file=%s reason=%s", attempt, max_retries, dest.name, detail)
            except InstallerError as exc:
                if exc.code in ("CANCELLED", "NET_CAPTIVE"):
                    raise
                if exc.code not in ("DOWNLOAD_INCOMPLETE", "DOWNLOAD_RANGE_INVALID"):
                    part.unlink(missing_ok=True)
                    raise
                last_error = str(exc)
                last_exc = exc
                log.warning("Download retry attempt=%s/%s file=%s code=%s detail=%s", attempt, max_retries, dest.name, exc.code, str(exc))
                if exc.code == "DOWNLOAD_RANGE_INVALID":
                    part.unlink(missing_ok=True)
            except Exception as exc:
                last_error = type(exc).__name__
                last_exc = exc
                self._check_abort(cancel_event, should_cancel)
                break
            self._check_abort(cancel_event, should_cancel)
            if attempt >= max_retries or time.monotonic() > total_deadline:
                break
            backoff = min(8.0, 0.75 * (2 ** (attempt - 1)))
            if time.sleep is _REAL_TIME_SLEEP and cancel_event is not None:
                cancel_event.wait(backoff)
            else:
                time.sleep(backoff)
            self._check_abort(cancel_event, should_cancel)
        err_msg = str(last_error) if last_error else "Lỗi kết nối mạng."
        raise InstallerError(f"Tải tệp không thành công sau {attempt} lần thử ({err_msg}).", "DOWNLOAD_FAILED") from last_exc

    @staticmethod
    def _prune_shared_downloads(downloads_dir: Path, keep_names: set[str]):
        """Removes stale unreferenced download blobs while keeping current manifest items and recent (<24h) .part files."""
        try:
            now_wall = time.time()
            for item in downloads_dir.iterdir():
                if not item.is_file() or item.name in keep_names:
                    continue
                if item.name.endswith(".part"):
                    try:
                        if (now_wall - item.stat().st_mtime) < 86400:
                            continue
                    except OSError:
                        continue
                try:
                    item.unlink(missing_ok=True)
                except OSError:
                    pass
        except OSError:
            pass

    def _invoke_download(
        self,
        url: str,
        dest: Path,
        size: int,
        sha: Optional[str],
        event_cb,
        operation_id: str,
        cancel_event: Optional[threading.Event],
        should_cancel: Optional[Callable[[], bool]],
    ):
        if (cancel_event is not None or should_cancel is not None) and self._supports_cancel_kwargs():
            return self.download(
                url,
                dest,
                size,
                sha,
                event_cb,
                operation_id,
                cancel_event=cancel_event,
                should_cancel=should_cancel,
            )
        return self.download(url, dest, size, sha, event_cb, operation_id)

    def prepare_payload(
        self,
        cache_root,
        manifest_url=None,
        event_cb=None,
        operation_id="download",
        cancel_event: Optional[threading.Event] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
    ):
        if _is_cancelled(cancel_event, should_cancel):
            raise InstallerError("Đã huỷ tải gói bản dịch.", "CANCELLED")
        try:
            release = self.release()
        except Exception:
            if not manifest_url:
                raise
            release = None
        raw, binding = self._manifest_for_release(release, manifest_url)
        manifest = self._windows_manifest(raw)
        stage = Path(cache_root) / ("payload_" + uuid.uuid4().hex)
        stage.mkdir(parents=True)
        try:
            if _is_cancelled(cancel_event, should_cancel):
                raise InstallerError("Đã huỷ tải gói bản dịch.", "CANCELLED")
            downloads_dir = Path(cache_root) / "shared_downloads"
            downloads_dir.mkdir(parents=True, exist_ok=True)
            release_assets = {a["name"]: a for a in release["assets"]} if release else {}
            assets = release_assets if binding["source"] == "release_asset" else {}
            package = raw.get("package_zip", {}) if isinstance(raw.get("package_zip"), dict) else {}
            if binding["source"] == "explicit_custom_manifest" and package.get("filename"):
                candidate = release_assets.get(package["filename"])
                digest = package.get("sha256")
                size = package.get("size_bytes") if package.get("size_bytes") is not None else package.get("size")
                if (
                    candidate
                    and isinstance(digest, str)
                    and re.fullmatch("[0-9a-fA-F]{64}", digest)
                    and isinstance(size, int)
                    and not isinstance(size, bool)
                    and size > 0
                    and candidate["size"] == size
                    and self._asset_digest(candidate) == digest.lower()
                ):
                    assets = {package["filename"]: candidate}
                    binding = {**binding, "explicit_package_asset": package["filename"], "explicit_package_sha256": digest.lower()}

            file_urls = {}
            raw_files = raw.get("files") or {}
            for rel, meta in manifest["files"].items():
                original = raw_files.get(rel, {})
                url = original.get("url") or original.get("download_url")
                asset = assets.get(Path(meta["source"]).name)
                if asset:
                    asset_digest = self._asset_digest(asset)
                    if not url:
                        url = asset["browser_download_url"]
                    elif (
                        binding.get("source") == "release_asset"
                        and url != asset["browser_download_url"]
                        and "/releases/download/" in url
                        and asset["size"] == meta["size"]
                        and (not asset_digest or asset_digest == meta["sha256"].lower())
                    ):
                        url = asset["browser_download_url"]
                source_asset = next((a for a in release_assets.values() if a["browser_download_url"] == url), None) if url else None
                if source_asset:
                    digest = self._asset_digest(source_asset)
                    if source_asset["size"] != meta["size"] or (digest and digest != meta["sha256"].lower()):
                        raise InstallerError(
                            f"Bản phát hành không đồng bộ: {source_asset['name']} có kích thước hoặc SHA256 khác bảng kê ({source_asset['size']}/{meta['size']} bytes). Vui lòng báo người phát hành cập nhật gói tải.",
                            "RELEASE_ASSET_MISMATCH",
                        )
                file_urls[rel] = url

            keep_names: set[str] = set()
            zasset = (
                assets.get(package.get("filename"))
                if package.get("filename")
                else next((a for a in assets.values() if "AssetBundles" in a["name"] and a["name"].endswith(".zip")), None)
            )
            bundle_entries = {r: v for r, v in manifest["files"].items() if r.startswith("Persistent_Store/AssetBundles/")}
            if bundle_entries and zasset:
                zip_digest = self._asset_digest(zasset)
                declared_digest = package.get("sha256") or raw.get("asset_bundles_package_sha256")
                declared_size = (
                    package.get("size_bytes")
                    if package.get("size_bytes") is not None
                    else (package.get("size") if package.get("size") is not None else raw.get("asset_bundles_package_size"))
                )
                if declared_digest is not None and (not isinstance(declared_digest, str) or not re.fullmatch("[0-9a-fA-F]{64}", declared_digest)):
                    raise InstallerError("Mã xác minh gói ảnh không hợp lệ.", "MANIFEST_INVALID")
                if declared_size is not None and (not isinstance(declared_size, int) or isinstance(declared_size, bool) or declared_size <= 0):
                    raise InstallerError("Kích thước gói ảnh không hợp lệ.", "MANIFEST_INVALID")
                if declared_digest and zip_digest and declared_digest.lower() != zip_digest:
                    raise InstallerError("Gói ảnh không khớp bảng kê của bản phát hành.", "HASH_MISMATCH")
                if declared_size is not None and declared_size != zasset["size"]:
                    raise InstallerError("Kích thước gói ảnh không khớp bản phát hành.", "SIZE_MISMATCH")
                archive_name = f"{zasset['name']}_{declared_digest or zip_digest}.zip"
                keep_names.add(archive_name)
                archive_cached = downloads_dir / archive_name
                archive = self._invoke_download(
                    zasset["browser_download_url"],
                    archive_cached,
                    zasset["size"],
                    declared_digest or zip_digest,
                    event_cb,
                    operation_id,
                    cancel_event,
                    should_cancel,
                )
                with zipfile.ZipFile(archive) as z:
                    members = {}
                    seen = set()
                    for info in z.infolist():
                        if info.is_dir():
                            continue
                        name = relative_name(info.filename)
                        if name.casefold() in seen:
                            raise InstallerError("Archive trùng tên tệp.", "ARCHIVE_INVALID")
                        seen.add(name.casefold())
                        if (info.external_attr >> 16) & 0o170000 == 0o120000:
                            raise InstallerError("Archive có symlink.", "PATH_ESCAPE")
                        members[name] = info
                    for rel, meta in bundle_entries.items():
                        if _is_cancelled(cancel_event, should_cancel):
                            raise InstallerError("Đã huỷ tải gói bản dịch.", "CANCELLED")
                        options = [meta["source"], Path(meta["source"]).name, "AssetBundles/" + Path(meta["source"]).name]
                        info = next((members[x] for x in options if x in members), None)
                        if info is None or info.file_size != meta["size"]:
                            raise InstallerError("Bundle thiếu/sai kích thước trong archive.", "CORRUPT_PAYLOAD")
                        target = safe_path(stage, meta["source"])
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with z.open(info) as src, target.open("xb") as out:
                            shutil.copyfileobj(src, out, 256 * 1024)
                        if sha256_file(target) != meta["sha256"]:
                            raise InstallerError("Bundle sai SHA256: " + rel, "HASH_MISMATCH")

            unique_downloads: dict[str, tuple[str, Path, int, str, str]] = {}
            copy_tasks: list[tuple[Path, Path]] = []
            for rel, meta in manifest["files"].items():
                cached_name = f"{Path(meta['source']).name}_{meta['sha256']}"
                keep_names.add(cached_name)
                target = safe_path(stage, meta["source"])
                if target.is_file():
                    continue
                url = file_urls[rel]
                if not url:
                    raise InstallerError(
                        "Gói chưa cung cấp đường dẫn tải cho "
                        + rel
                        + ". Nguồn tùy chỉnh cần đường dẫn tệp trực tiếp hoặc một gói ZIP được khai báo đúng tên, kích thước và mã xác minh.",
                        "PAYLOAD_UNAVAILABLE",
                    )
                cached_item = downloads_dir / cached_name
                if cached_name not in unique_downloads:
                    unique_downloads[cached_name] = (url, cached_item, meta["size"], meta["sha256"], Path(meta["source"]).name)
                copy_tasks.append((cached_item, target))

            if unique_downloads:
                agg_items: list[tuple[str, int, int]] = []
                for cached_name, (_url, cached_item, size, sha, _label) in unique_downloads.items():
                    tag = sha[:12] if sha else str(size)
                    part = cached_item.with_name(f"{cached_item.name}.{tag}.part")
                    if cached_item.is_file() and cached_item.stat().st_size == size:
                        initial = size
                    elif part.is_file() and 0 < part.stat().st_size < size:
                        initial = part.stat().st_size
                    else:
                        initial = 0
                    agg_items.append((cached_name, size, initial))

                agg = DownloadProgressAggregator(agg_items, event_cb=event_cb, operation_id=operation_id)
                pending_list = list(unique_downloads.items())
                pool_workers = min(self.max_workers, max(1, len(pending_list)))
                pool_abort = threading.Event()
                errors_lock = threading.Lock()
                real_errors: list[BaseException] = []
                cancelled_seen = False

                def _run_one(key: str, dl_url: str, dest_path: Path, size: int, sha: str, label: str) -> None:
                    self._tls_local.pool_abort = pool_abort
                    try:
                        if _is_cancelled(cancel_event, should_cancel):
                            raise InstallerError("Đã huỷ tải gói bản dịch.", "CANCELLED")
                        if pool_abort.is_set():
                            raise _PoolAborted()
                        self._invoke_download(
                            dl_url,
                            dest_path,
                            size,
                            sha,
                            agg.worker_callback(key, label),
                            operation_id,
                            cancel_event,
                            should_cancel,
                        )
                        agg.complete_file(key, label)
                    finally:
                        self._tls_local.pool_abort = None

                with ThreadPoolExecutor(max_workers=pool_workers) as executor:
                    futures = [
                        executor.submit(_run_one, key, dl_url, dest_path, size, sha, label)
                        for key, (dl_url, dest_path, size, sha, label) in pending_list
                    ]
                    for fut in as_completed(futures):
                        try:
                            fut.result()
                        except (_PoolAborted, FuturesCancelledError):
                            pass
                        except BaseException as exc:
                            with errors_lock:
                                if (isinstance(exc, InstallerError) and exc.code == "CANCELLED") or _is_cancelled(cancel_event, should_cancel):
                                    cancelled_seen = True
                                else:
                                    real_errors.append(exc)
                            pool_abort.set()
                            for other in futures:
                                other.cancel()

                if cancelled_seen or _is_cancelled(cancel_event, should_cancel):
                    raise InstallerError("Đã huỷ tải gói bản dịch.", "CANCELLED")
                if real_errors:
                    primary = real_errors[0]
                    if len(pending_list) == 1:
                        raise primary
                    if all(isinstance(e, InstallerError) and e.code == "NET_CAPTIVE" for e in real_errors):
                        raise primary
                    if len(real_errors) >= 2 or any(_is_disk_io_error(e) for e in real_errors):
                        raise InstallerError(f"Quá trình tải song song bị gián đoạn: {primary}", "PARALLEL_DL") from primary
                    raise primary
                agg.finish()

            for cached_item, target in copy_tasks:
                if _is_cancelled(cancel_event, should_cancel):
                    raise InstallerError("Đã huỷ tải gói bản dịch.", "CANCELLED")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cached_item, target)

            self._prune_shared_downloads(downloads_dir, keep_names)
            manifest["source_metadata"] = binding
            atomic_json(stage / "patch_manifest.json", manifest)
            return stage
        except BaseException:
            self._cleanup_owned_stage(cache_root, stage)
            raise

    @staticmethod
    def _cleanup_owned_stage(cache_root, stage):
        path = Path(stage)
        try:
            root = Path(cache_root).resolve()
            if path.is_symlink() or not re.fullmatch(r"payload_[0-9a-f]{32}", path.name):
                raise ValueError("Not an owned payload stage")
            resolved = path.resolve()
            if resolved.parent != root or resolved.name != path.name:
                raise ValueError("Payload stage is outside the cache root")
            if path.exists():
                shutil.rmtree(path)
        except (OSError, ValueError) as exc:
            log.warning("Could not clean payload stage %s: %s", path.name, type(exc).__name__)

    @contextmanager
    def payload_for_install(
        self,
        cache_root,
        local=None,
        manifest_url=None,
        event_cb=None,
        operation_id="download",
        cancel_event: Optional[threading.Event] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
    ):
        if local:
            yield Path(local)
            return
        stage = self.prepare_payload(
            cache_root,
            manifest_url,
            event_cb,
            operation_id,
            cancel_event=cancel_event,
            should_cancel=should_cancel,
        )
        try:
            yield stage
        finally:
            self._cleanup_owned_stage(cache_root, stage)

    def get_supporter_data(self):
        return SupporterData(
            status="unavailable",
            supporters=[],
            qr_placeholder_text="Thông tin thanh toán do người dùng cung cấp. Danh sách người đồng hành hiện chưa có nguồn dữ liệu.",
        )
