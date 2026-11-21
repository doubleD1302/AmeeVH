"""Copyable error reports for the PC launcher.

``build_report`` turns an exception (or a known situation code) plus the launcher's current state into one
``ErrorReport``: a plain-language explanation with concrete steps for the dialog, and a complete plain-text
report the user can paste to the developers with a single click.

Privacy: Windows profile paths are replaced by %USERPROFILE%, URL query strings are dropped, proxy credentials are
never printed and no tokens/secrets exist in the data collected here.
"""
from __future__ import annotations

import ctypes
import logging
import os
import platform
import re
import shutil
import sys
import time
import traceback
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from . import error_catalog
from .config import LAUNCHER_VERSION
from .net_probe import format_probe

log = logging.getLogger('launcher.error_report')

_URL_QUERY = re.compile(r'(https?://[^\s?#\'"<>]+)[?#][^\s\'"<>]*')


def _home_variants():
    out = []
    for raw in (os.environ.get('USERPROFILE'), str(Path.home())):
        if raw:
            norm = str(raw).rstrip('\\/')
            if len(norm) >= 4:
                out.append(norm)
    return sorted(set(out), key=len, reverse=True)


def redact(text):
    """Remove account-identifying path prefixes and URL query strings from ``text``."""
    out = str(text)
    for home in _home_variants():
        for variant in (home, home.replace('\\', '/')):
            out = re.sub(re.escape(variant), '%USERPROFILE%', out, flags=re.IGNORECASE)
    return _URL_QUERY.sub(r'\1', out)


def safe_url(url):
    """scheme://host/path only (no credentials, query or fragment)."""
    try:
        u = urllib.parse.urlparse(str(url))
        if not u.scheme or not u.hostname:
            return '(không có)' if not url else '(địa chỉ không hợp lệ)'
        port = f':{u.port}' if u.port else ''
        return f'{u.scheme}://{u.hostname}{port}{u.path}'
    except ValueError:
        return '(địa chỉ không hợp lệ)'


def new_report_id():
    n, digits, out = int(time.time() * 1000), '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', ''
    while n:
        n, r = divmod(n, 36)
        out = digits[r] + out
    return out or '0'


@dataclass
class ErrorContext:
    """Snapshot of launcher state at failure time. Every field is optional."""
    action: str = ''                 # what the user was doing, e.g. "Cài Việt hoá"
    operation: str = ''              # internal operation kind
    progress: str = ''               # last progress line
    path_manager: Any = None
    game: Any = None                 # core.types.GameInfo
    sync: Optional[dict] = None      # MainWindow._github_sync_state
    channel: Optional[dict] = None   # MainWindow._channel
    probe: Optional[dict] = None     # net_probe.run_probe() result
    extra: dict = field(default_factory=dict)


@dataclass
class ErrorReport:
    code: str
    report_id: str
    title: str
    summary: str
    steps: tuple
    level: str
    message: str
    text: str
    wrapper: str = ''
    probe_text: str = ''

    @property
    def is_error(self):
        return self.level == 'error'

    @property
    def code_line(self):
        return f'Mã lỗi: {self.code} · #{self.report_id}'

    def dialog_details(self):
        """Text for the scrollable area of the dialog (steps + short technical block)."""
        parts = []
        if self.steps:
            parts.append('CÁCH XỬ LÝ')
            parts.extend(f'{i}. {s}' for i, s in enumerate(self.steps, 1))
            parts.append('')
        parts.append(self.code_line)
        parts.append('Bấm "Sao chép mã lỗi" để chép toàn bộ thông tin chẩn đoán gửi cho người hỗ trợ.')
        if self.message and self.message.strip() and self.message.strip() != self.summary.strip():
            parts.extend(['', 'CHI TIẾT KỸ THUẬT', redact(self.message)])
        return '\n'.join(parts)


# --------------------------------------------------------------------------- section builders
def _yn(value):
    return 'Có' if value else 'Không'


def _free_gb(path):
    try:
        return f'{shutil.disk_usage(path).free / (1024 ** 3):.1f} GB'
    except Exception:  # noqa: BLE001
        return 'không đọc được'


def _is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin()) if sys.platform == 'win32' else False
    except Exception:  # noqa: BLE001
        return False


def _proxy_summary():
    try:
        proxies = urllib.request.getproxies()
    except Exception:  # noqa: BLE001
        return 'không đọc được'
    if not proxies:
        return 'không dùng proxy'
    out = []
    for scheme, value in sorted(proxies.items()):
        try:
            u = urllib.parse.urlparse(value if '//' in value else '//' + value)
            out.append(f'{scheme}={u.hostname}{":" + str(u.port) if u.port else ""}')
        except ValueError:
            out.append(f'{scheme}=?')
    return ', '.join(out)


def _system_lines(ctx):
    pm = ctx.path_manager
    lines = [
        f'Launcher: v{LAUNCHER_VERSION} ({"đã đóng gói .exe" if getattr(sys, "frozen", False) else "chạy từ mã nguồn"})',
        f'Windows: {platform.platform()} · {platform.machine()}',
        f'Quyền Quản trị: {_yn(_is_admin())}',
        f'Múi giờ: UTC{time.strftime("%z")} · Python {platform.python_version()}',
        f'Proxy hệ thống: {_proxy_summary()}',
    ]
    if pm is not None:
        try:
            app = pm.app_data_dir
            lines.append(f'Thư mục dữ liệu launcher: {app} (trống {_free_gb(app)})')
        except Exception:  # noqa: BLE001
            lines.append('Thư mục dữ liệu launcher: không truy cập được')
    return lines


def _game_lines(ctx):
    g = ctx.game
    if g is None:
        return ['Chưa có thông tin game.']
    path = getattr(g, 'game_path', None)
    lines = [
        f'Nhận diện thư mục game: {_yn(getattr(g, "installed", False))} (nguồn: {getattr(g, "detection_source", "?")})',
        f'Đường dẫn: {path if path else "chưa chọn"}',
        f'Nền tảng: {getattr(g, "platform", "?")} · game {getattr(g, "version", "?")} / tài nguyên {getattr(g, "resource_version", "?")}',
        f'Game đang chạy: {_yn(getattr(g, "is_running", False))}',
    ]
    if path:
        try:
            p = Path(path)
            lines.append(f'StellaSora.exe: {"có" if (p / "StellaSora.exe").is_file() else "KHÔNG THẤY"} · thư mục tồn tại: {_yn(p.is_dir())} · trống {_free_gb(p if p.exists() else p.anchor)}')
        except Exception:  # noqa: BLE001
            pass
    receipt = getattr(g, 'installed_receipt', None)
    if receipt:
        lines.append(
            f'Biên bản cài: có · bản dịch {receipt.get("version", "?")} · {len(receipt.get("files", {}) or {})} tệp · cài lúc {receipt.get("installed_at", "?")}'
        )
    else:
        lines.append('Biên bản cài: KHÔNG CÓ (chưa cài Việt hoá bằng launcher này, hoặc biên bản không khớp thư mục)')
    lines.append(f'Biên bản lỗi thời: {_yn(getattr(g, "receipt_stale", False))} · có bản dịch: {_yn(getattr(g, "has_vietnamese", False))} · số bản sao lưu: {getattr(g, "backup_count", 0)}')
    official = getattr(g, 'official_restore', None)
    if official:
        lines.append(f'Đã khôi phục dữ liệu gốc: {official.get("restored_at", "?")} (tài nguyên {official.get("official_resource_version", "?")})')
    return lines


def _sync_lines(ctx):
    s = ctx.sync or {}
    lines = []
    ch = ctx.channel or {}
    if ch:
        lines.append(f'Kho/nhánh: {ch.get("repo", "?")} @ {ch.get("branch", "?")}')
        lines.append(f'Địa chỉ phát hành: {safe_url(ch.get("release_url"))}')
        lines.append(f'Địa chỉ thông báo: {safe_url(ch.get("notifications_url"))}')
        if ch.get('manifest_url'):
            lines.append(f'Địa chỉ bảng kê tuỳ chọn: {safe_url(ch.get("manifest_url"))}')
        if ch.get('configuration_error'):
            lines.append(f'Lỗi cấu hình: {ch["configuration_error"]}')
    if not s:
        lines.append('Chưa đồng bộ GitHub lần nào.')
        return lines
    lines.append(f'Trạng thái chung: {s.get("message", "?")} (đã tươi: {_yn(s.get("fresh"))})')
    if 'release_status' in s:
        lines.append(f'Bản phát hành: {s.get("release_status")} · {s.get("release_version") or "chưa đọc được"}')
        if s.get('release_error'):
            lines.append(f'  Lỗi bản phát hành [{s.get("release_error_code", "?")}]: {s["release_error"]}')
    if 'manifest_status' in s:
        lines.append(
            f'Bảng kê bản dịch: {s.get("manifest_status")} · {s.get("translation_version") or "chưa xác minh"}'
            f' · game {s.get("translation_game") or "?"} / tài nguyên {s.get("translation_resource") or "?"} · {s.get("translation_file_count") if s.get("translation_file_count") is not None else "?"} tệp'
        )
        if s.get('manifest_error'):
            lines.append(f'  Lỗi bảng kê [{s.get("manifest_error_code", "?")}]: {s["manifest_error"]}')
    if 'notification_status' in s:
        lines.append(f'Thông báo: {s.get("notification_status")} · {s.get("notification_message", "")}')
    upd = s.get('update')
    if isinstance(upd, dict):
        lines.append(f'Cập nhật launcher: {upd.get("status")} · {upd.get("message", "")}')
    if s.get('cache_warning'):
        lines.append(f'Cảnh báo bộ nhớ đệm: {s["cache_warning"]}')
    if s.get('fetched_at'):
        lines.append(f'Đồng bộ lúc: {s["fetched_at"]}')
    return lines


def _log_tail(ctx, count=30):
    pm = ctx.path_manager
    if pm is None:
        return []
    try:
        path = Path(pm.logs_dir) / 'launcher.log'
        if not path.is_file():
            return ['(chưa có tệp nhật ký)']
        with path.open('rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 24 * 1024))
            raw = f.read().decode('utf8', errors='replace')
        tail = raw.splitlines()[-count:]
        return [(line if len(line) <= 260 else line[:260] + '…') for line in tail]
    except Exception:  # noqa: BLE001
        return ['(không đọc được nhật ký)']


def _trace_lines(exc, limit=24):
    if not isinstance(exc, BaseException):
        return []
    try:
        lines = [ln for block in traceback.format_exception(type(exc), exc, exc.__traceback__) for ln in block.rstrip().splitlines()]
    except Exception:  # noqa: BLE001
        return []
    return lines[-limit:]


def _safe(section, ctx):
    """One broken section must never cost the user the whole report."""
    try:
        return section(ctx)
    except Exception as exc:  # noqa: BLE001
        return [f'(không đọc được mục này: {type(exc).__name__})']


def _compose_text(r, ctx, diag, trace):
    stamp = time.strftime('%Y-%m-%d %H:%M:%S') + f' (UTC{time.strftime("%z")})'
    out = [
        f'STELLA SORA VIỆT HOÁ — MÃ LỖI {r.code} (#{r.report_id})',
        f'Nền tảng: Windows PC · Launcher v{LAUNCHER_VERSION}',
        f'Thời gian: {stamp}',
        f'Đang làm: {ctx.action or ctx.operation or "(không rõ)"}' + (f' [{ctx.operation}]' if ctx.action and ctx.operation else ''),
        f'Bước cuối: {ctx.progress or "(không có)"}',
        '',
        f'Tiêu đề: {r.title}',
        f'Giải thích: {r.summary}',
        'Cách xử lý đã gợi ý: ' + ' | '.join(r.steps) if r.steps else 'Cách xử lý đã gợi ý: (không)',
        f'Thông báo gốc: {r.message or "(không có)"}',
    ]
    if diag is not None and diag.wrapper:
        out.append(f'Bao ngoài: {diag.wrapper} (launcher đã hoàn tác thay đổi nếu có)')
    if ctx.probe:
        out.extend(['', '--- Đo kết nối mạng lúc lỗi ---'] + format_probe(ctx.probe))
    out.extend(['', '--- Hệ thống ---'] + _safe(_system_lines, ctx))
    out.extend(['', '--- Game ---'] + _safe(_game_lines, ctx))
    out.extend(['', '--- GitHub / kênh cập nhật ---'] + _safe(_sync_lines, ctx))
    if ctx.extra:
        out.extend(['', '--- Thông tin thêm ---'] + [f'{k}: {v}' for k, v in ctx.extra.items()])
    if diag is not None and diag.chain:
        out.extend(['', '--- Chuỗi lỗi (ngoài → trong) ---'] + [f'{i + 1}. {line}' for i, line in enumerate(diag.chain)])
    if trace:
        out.extend(['', '--- Vết lỗi (rút gọn) ---'] + trace)
    out.extend(['', '--- Nhật ký launcher (30 dòng cuối) ---'] + _safe(_log_tail, ctx))
    return redact('\n'.join(out))


def build_report(code=None, *, exc=None, message='', action='', title='', ctx=None, subject=None, extra_summary=''):
    """Create an :class:`ErrorReport`. Never raises.

    ``exc`` wins over ``code``: the exception chain is classified (see ``error_catalog.diagnose``) and ``code`` is only
    a fallback. With no exception, ``code`` names a known situation from the catalog.
    """
    ctx = ctx or ErrorContext()
    if action and not ctx.action:
        ctx.action = action
    try:
        diag = error_catalog.diagnose(exc, fallback=code, subject=subject) if exc is not None else None
        if diag is not None:
            info, final_code = diag.info, diag.code
        else:
            final_code = code or 'E-UNKNOWN'
            info = error_catalog.lookup(final_code, subject or 'github')
        raw = message or (diag.message if diag is not None else '')
        probe_text = ''
        if ctx.probe and info.network:
            probe_text = ctx.probe.get('verdict_text', '')
        summary = info.summary
        if extra_summary:
            summary += '\n\n' + extra_summary
        if probe_text:
            summary += '\n\nKiểm tra tự động: ' + probe_text
        report = ErrorReport(
            code=final_code, report_id=new_report_id(), title=title or info.title, summary=summary, steps=info.steps,
            level=info.level, message=raw, text='', wrapper=diag.wrapper if diag else '', probe_text=probe_text,
        )
        report.text = _compose_text(report, ctx, diag, _trace_lines(exc))
        log.error('ERROR_REPORT id=%s code=%s action=%s message=%s', report.report_id, report.code, ctx.action or ctx.operation, redact(raw)[:400])
        return report
    except Exception as internal:  # noqa: BLE001 - the error path must never raise
        log.exception('Could not build error report')
        fallback_id = new_report_id()
        text = f'STELLA SORA VIỆT HOÁ — MÃ LỖI {code or "E-UNKNOWN"} (#{fallback_id})\n{redact(message)}\n(Không dựng được báo cáo đầy đủ: {internal!r})'
        info = error_catalog.lookup(code or 'E-UNKNOWN')
        return ErrorReport(code or 'E-UNKNOWN', fallback_id, title or info.title, info.summary, info.steps, info.level, message, text)


def copy_text_native(text):
    """Put ``text`` on the Windows clipboard without Qt (used before the UI exists). True on success."""
    if sys.platform != 'win32':
        return False
    try:
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE
        data = (text + '\0').encode('utf-16-le')
        handle = kernel32.GlobalAlloc(0x0002, len(data))
        if not handle:
            return False
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            kernel32.GlobalFree(handle)
            return False
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(handle)
        for _ in range(5):
            if user32.OpenClipboard(None):
                break
            time.sleep(0.05)
        else:
            kernel32.GlobalFree(handle)
            return False
        try:
            user32.EmptyClipboard()
            if not user32.SetClipboardData(13, handle):   # CF_UNICODETEXT
                kernel32.GlobalFree(handle)
                return False
            return True
        finally:
            user32.CloseClipboard()
    except Exception:  # noqa: BLE001
        return False
