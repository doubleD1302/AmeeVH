"""Short, bounded connectivity probe that explains *why* a network call failed.

It resolves names, opens plain TCP connections (no payload is sent), optionally
checks for a captive portal via plain HTTP, and captures the active TLS root
store summary from :mod:`launcher_v2.core.tls`.  Comparing GitHub's hosts with
a neutral control tells apart "no Internet", "broken DNS", "captive portal",
and "only GitHub is blocked".  Intended to run in a worker thread right after a
network-class failure; never call it from the UI thread.

100% pure Python (zero Qt / PySide6 imports).
"""
from __future__ import annotations

import os
import re
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

from . import tls
from .config import LAUNCHER_VERSION

DEFAULT_HOSTS: tuple[str, ...] = ('api.github.com', 'raw.githubusercontent.com', 'github.com')
PUBLISHER_HOSTS: tuple[str, ...] = ('nova-static.stellasora.global',)
CONTROL_DNS_HOST: str = 'www.microsoft.com'
CONTROL_TCP_ADDR: tuple[str, int] = ('1.1.1.1', 443)   # direct IP: works even when DNS is broken
CAPTIVE_PROBE_URL: str = 'http://www.msftconnecttest.com/connecttest.txt'
CAPTIVE_EXPECTED_BODY: bytes = b'Microsoft Connect Test'


def _default_resolver(host: str, port: int) -> str:
    info = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return info[0][4][0]


def _default_connector(addr: tuple[str, int], timeout: float) -> bool:
    with socket.create_connection(addr, timeout=timeout):
        return True


def _safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    if obj is None:
        return default
    try:
        return getattr(obj, attr, default)
    except Exception:  # noqa: BLE001
        return default


def _safe_str(value: Any, default: str = '') -> str:
    if value is None:
        return default
    if type(value) is str:
        return value
    try:
        s = str(value)
        return s if type(s) is str else (str.__str__(s) if isinstance(s, str) else default)
    except Exception:  # noqa: BLE001
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    try:
        return bool(value)
    except Exception:  # noqa: BLE001
        return default


def _safe_opt_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if type(value) is int:
        return value
    if isinstance(value, int):
        try:
            v = int(value)
            return v if type(v) is int else None
        except Exception:  # noqa: BLE001
            return None
    return None


def _safe_url_hostname(raw_url: Any) -> str:
    try:
        u_str = _safe_str(raw_url)
        return (urllib.parse.urlparse(u_str).hostname or '').lower()
    except Exception:  # noqa: BLE001
        return ''


def _fmt(exc: BaseException) -> str:
    win = _safe_opt_int(_safe_getattr(exc, 'winerror', None))
    eno = _safe_opt_int(_safe_getattr(exc, 'errno', None))
    if win is not None and win != 0:
        code = f' (WinError {win})'
    elif eno is not None and eno != 0:
        code = f' (errno {eno})'
    else:
        code = ''
    try:
        cls_name = type(exc).__name__
    except Exception:  # noqa: BLE001
        cls_name = 'Exception'
    return cls_name + code


def _redact_path(text: Any) -> str:
    out = _safe_str(text)
    candidates: list[str] = []
    home_raw: Optional[str] = None
    try:
        home_raw = str(Path.home())
    except Exception:  # noqa: BLE001
        home_raw = None
    for raw in (os.environ.get('USERPROFILE'), home_raw):
        if raw:
            norm = str(raw).rstrip('\\/')
            if len(norm) >= 4:
                candidates.append(norm)
    for home in sorted(set(candidates), key=len, reverse=True):
        for variant in (home, home.replace('\\', '/')):
            out = re.sub(re.escape(variant), '%USERPROFILE%', out, flags=re.IGNORECASE)
    return out


def _probe_host(host: str, port: int, timeout: float, resolver: Callable, connector: Callable, out: dict) -> None:
    rec: dict[str, Any] = {'dns': 'pending', 'ip': '', 'tcp': 'pending', 'detail': '', 'ms': None}
    out[host] = rec
    t0 = time.monotonic()
    try:
        rec['ip'] = resolver(host, port)
        rec['dns'] = 'ok'
    except Exception as exc:  # noqa: BLE001 - diagnostic only
        rec['dns'] = 'fail'
        rec['detail'] = _fmt(exc)
        rec['tcp'] = 'skip'
        return
    try:
        t1 = time.monotonic()
        connector((rec['ip'], port), timeout)
        rec['tcp'] = 'ok'
        rec['ms'] = int((time.monotonic() - t1) * 1000)
    except Exception as exc:  # noqa: BLE001
        rec['tcp'] = 'fail'
        rec['detail'] = _fmt(exc)
        rec['ms'] = int((time.monotonic() - t0) * 1000)


def _probe_control(timeout: float, resolver: Callable, connector: Callable, out: dict) -> None:
    rec = {'dns': 'pending', 'tcp': 'pending'}
    out['__control__'] = rec

    def dns() -> None:
        try:
            resolver(CONTROL_DNS_HOST, 443)
            rec['dns'] = 'ok'
        except Exception:  # noqa: BLE001
            rec['dns'] = 'fail'

    def tcp() -> None:
        try:
            connector(CONTROL_TCP_ADDR, timeout)
            rec['tcp'] = 'ok'
        except Exception:  # noqa: BLE001
            rec['tcp'] = 'fail'

    for fn in (dns, tcp):
        threading.Thread(target=fn, daemon=True).start()


def _get_header(headers: Any, name: str) -> str:
    if headers is None:
        return ''
    target_low = name.lower()
    if isinstance(headers, dict):
        try:
            for k, v in headers.items():
                if str(k).lower() == target_low:
                    return '' if v is None else str(v)
        except Exception:  # noqa: BLE001
            return ''
        return ''
    getter = _safe_getattr(headers, 'get', None)
    if callable(getter):
        try:
            val = getter(name)
            if val is None and name != target_low:
                val = getter(target_low)
            return '' if val is None else str(val)
        except Exception:  # noqa: BLE001
            return ''
    return ''


def _inspect_http_response(obj: Any, url: str) -> tuple[Optional[int], str, bytes, str, bool, bool]:
    status = _safe_opt_int(_safe_getattr(obj, 'status', None))
    if status is None:
        status = _safe_opt_int(_safe_getattr(obj, 'code', None))
    if status is None:
        getcode = _safe_getattr(obj, 'getcode', None)
        if callable(getcode):
            try:
                status = _safe_opt_int(getcode())
            except Exception:  # noqa: BLE001
                status = None
    headers = _safe_getattr(obj, 'headers', None)
    raw_ct = _get_header(headers, 'Content-Type')
    ct = raw_ct.split(';', 1)[0].strip().lower()
    try:
        read_fn = _safe_getattr(obj, 'read', None)
        raw_body = read_fn(4096) if callable(read_fn) else b''
    except Exception:  # noqa: BLE001
        raw_body = b''
    body = bytes(raw_body) if isinstance(raw_body, (bytes, bytearray)) else b''
    final_url = url
    geturl = _safe_getattr(obj, 'geturl', None)
    if callable(geturl):
        try:
            u_val = geturl()
            if u_val is not None:
                u_str = _safe_str(u_val)
                if u_str:
                    final_url = u_str
        except Exception:  # noqa: BLE001
            final_url = url
    orig_host = _safe_url_hostname(url)
    final_host = _safe_url_hostname(final_url) or orig_host
    try:
        is_redir = status in (301, 302, 303, 307, 308)
    except Exception:  # noqa: BLE001
        is_redir = False
    if is_redir:
        loc = _get_header(headers, 'Location').strip()
        if loc:
            try:
                loc_url = urllib.parse.urljoin(_safe_str(final_url), loc)
                loc_host = _safe_url_hostname(loc_url)
                if loc_host and loc_host != orig_host:
                    final_host = loc_host
            except Exception:  # noqa: BLE001
                pass
    head = bytes(body[:512]).lstrip(b' \t\r\n\xef\xbb\xbf').lower()
    is_html = ct in ('text/html', 'application/xhtml+xml') or head.startswith((b'<!doctype html', b'<html'))
    redirected_diff = bool(final_host and orig_host and final_host != orig_host and bytes(body).strip() != CAPTIVE_EXPECTED_BODY)
    return status, ct, bytes(body), final_host or orig_host, is_html, redirected_diff


def check_captive_portal(
    url: str = CAPTIVE_PROBE_URL,
    timeout: float = 3.0,
    opener: Optional[Callable] = None,
) -> dict[str, Any]:
    """Detect Wi-Fi/router captive portal redirection via plain HTTP. Never raises."""
    open_fn = opener or urllib.request.urlopen
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': f'StellaSora-Launcher/{LAUNCHER_VERSION}'},
        )
        with open_fn(req, timeout=timeout) as resp:
            status, ct, _body, final_host, is_html, redirected_diff = _inspect_http_response(resp, url)
            if status == 511 or is_html or redirected_diff:
                return {
                    'status': 'captive',
                    'detected': True,
                    'http_status': status,
                    'content_type': ct,
                    'final_host': final_host,
                    'detail': f'HTTP {status or "?"} ({ct or "unknown"}) -> {final_host}',
                }
            return {
                'status': 'clear',
                'detected': False,
                'http_status': status,
                'content_type': ct,
                'final_host': final_host,
                'detail': 'ok',
            }
    except urllib.error.HTTPError as exc:
        try:
            try:
                status, ct, _body, final_host, is_html, redirected_diff = _inspect_http_response(exc, url)
                if status is None:
                    status = _safe_opt_int(_safe_getattr(exc, 'code', None))
                if status == 511 or is_html or redirected_diff:
                    return {
                        'status': 'captive',
                        'detected': True,
                        'http_status': status,
                        'content_type': ct,
                        'final_host': final_host,
                        'detail': f'HTTP {status or "?"} ({ct or "unknown"}) -> {final_host}',
                    }
                return {
                    'status': 'error',
                    'detected': False,
                    'http_status': status,
                    'content_type': ct,
                    'final_host': final_host,
                    'detail': _fmt(exc),
                }
            except Exception as inner_exc:  # noqa: BLE001 - diagnostic only
                return {
                    'status': 'error',
                    'detected': False,
                    'http_status': _safe_opt_int(_safe_getattr(exc, 'code', None)),
                    'content_type': '',
                    'final_host': '',
                    'detail': _fmt(inner_exc),
                }
        finally:
            close_fn = _safe_getattr(exc, 'close', None)
            if callable(close_fn):
                try:
                    close_fn()
                except Exception:  # noqa: BLE001
                    pass
    except Exception as exc:  # noqa: BLE001 - diagnostic only
        return {
            'status': 'error',
            'detected': False,
            'http_status': None,
            'content_type': '',
            'final_host': '',
            'detail': _fmt(exc),
        }


def verdict(
    hosts: dict[str, dict[str, Any]],
    control: dict[str, str],
    captive: Optional[dict[str, Any]] = None,
) -> tuple[str, str]:
    """(verdict_code, Vietnamese sentence) from per-host results, control, and optional captive probe."""
    if isinstance(captive, dict) and _safe_bool(captive.get('detected')):
        return (
            'captive_portal',
            'Mạng đang chặn hoặc chuyển hướng tới trang đăng nhập (Captive Portal). Hãy mở trình duyệt đăng nhập Wi-Fi rồi thử lại.',
        )
    host_items: list[tuple[str, dict[str, Any]]] = []
    if isinstance(hosts, dict):
        try:
            raw_items = list(hosts.items())
        except Exception:  # noqa: BLE001
            raw_items = []
        for name, h in raw_items:
            hname = _safe_str(name, '?') or '?'
            hmap = h if isinstance(h, dict) else {}
            host_items.append((hname, hmap))
    if host_items and all(_safe_str(h.get('tcp')) == 'ok' for _, h in host_items):
        return 'ok', 'Lúc kiểm tra, máy kết nối tới GitHub bình thường. Lỗi có thể chỉ xảy ra thoáng qua; hãy thử lại.'
    ctrl_map = control if isinstance(control, dict) else {}
    ctrl_dns = _safe_str(ctrl_map.get('dns')) == 'ok'
    ctrl_tcp = _safe_str(ctrl_map.get('tcp')) == 'ok'
    failed = [name for name, h in host_items if _safe_str(h.get('tcp')) != 'ok']
    where = ', '.join(failed)
    if not ctrl_dns and not ctrl_tcp:
        return 'offline', 'Máy đang không có Internet: ngay cả điểm kiểm tra chung cũng không kết nối được. Hãy kiểm tra Wi-Fi/dây mạng.'
    dns_failed = [name for name, h in host_items if _safe_str(h.get('dns')) != 'ok']
    if dns_failed:
        if ctrl_dns:
            return 'dns_blocked', f'Internet vẫn hoạt động nhưng không tra được địa chỉ ({where}). GitHub có thể bị chặn ở DNS của mạng bạn; thử đổi DNS hoặc dùng VPN.'
        return 'dns_broken', 'Máy vẫn ra được Internet qua địa chỉ IP nhưng DNS đang hỏng, nên không tìm ra GitHub. Hãy đổi DNS sang 1.1.1.1 / 8.8.8.8.'
    if ctrl_tcp or ctrl_dns:
        return 'blocked', f'Internet vẫn hoạt động nhưng kết nối tới GitHub ({where}) bị chặn hoặc quá chậm. Hãy kiểm tra tường lửa, diệt virus, VPN/proxy hoặc đổi mạng.'
    return 'offline', 'Không kết nối được. Hãy kiểm tra mạng.'


def run_probe(
    hosts: tuple[str, ...] | list[str] = DEFAULT_HOSTS,
    port: int = 443,
    timeout: float = 3.5,
    deadline: float = 8.0,
    resolver: Optional[Callable] = None,
    connector: Optional[Callable] = None,
    captive_probe: Optional[Callable[[], dict[str, Any]]] = None,
    check_captive: Optional[bool] = None,
    include_tls: bool = True,
) -> dict[str, Any]:
    """Probe ``hosts`` plus control, optional captive portal, and TLS info within ``deadline`` seconds.

    ``resolver(host, port) -> ip``, ``connector((ip, port), timeout)``, and ``captive_probe() -> dict``
    are injectable for tests.  When ``resolver`` or ``connector`` is mocked and ``check_captive`` is
    ``None``, live captive-portal HTTP probing is automatically skipped so offline unit tests never
    hit the real network.
    """
    is_mocked = resolver is not None or connector is not None
    if check_captive is None:
        do_captive = (not is_mocked) or (captive_probe is not None)
    else:
        do_captive = _safe_bool(check_captive)

    eff_resolver = resolver or _default_resolver
    eff_connector = connector or _default_connector
    results: dict[str, Any] = {}
    threads: list[threading.Thread] = []
    t0 = time.monotonic()

    for host in hosts:
        th = threading.Thread(
            target=_probe_host,
            args=(host, port, timeout, eff_resolver, eff_connector, results),
            daemon=True,
        )
        th.start()
        threads.append(th)

    _probe_control(timeout, eff_resolver, eff_connector, results)

    captive_box: dict[str, Any] = {}
    captive_thread: Optional[threading.Thread] = None
    if do_captive:
        def _run_captive() -> None:
            try:
                if captive_probe is not None:
                    res = captive_probe()
                    captive_box['result'] = dict(res) if isinstance(res, dict) else {'status': 'error', 'detected': False, 'detail': str(res)}
                else:
                    captive_box['result'] = check_captive_portal(timeout=min(timeout, deadline))
            except Exception as exc:  # noqa: BLE001
                captive_box['result'] = {'status': 'error', 'detected': False, 'detail': _fmt(exc)}

        captive_thread = threading.Thread(target=_run_captive, daemon=True)
        captive_thread.start()

    end = t0 + deadline
    for th in threads:
        th.join(max(0.0, end - time.monotonic()))
    if captive_thread is not None:
        captive_thread.join(max(0.0, end - time.monotonic()))

    while time.monotonic() < end and (
        results['__control__']['dns'] == 'pending' or results['__control__']['tcp'] == 'pending'
    ):
        time.sleep(0.05)

    control = dict(results.pop('__control__'))
    hosts_out: dict[str, dict[str, Any]] = {}
    for host in hosts:
        rec = dict(results.get(host) or {'dns': 'pending', 'ip': '', 'tcp': 'pending', 'detail': '', 'ms': None})
        if rec['dns'] == 'pending':
            rec['dns'], rec['tcp'], rec['detail'] = 'fail', 'skip', 'không trả lời kịp (quá thời gian chờ DNS)'
        elif rec['tcp'] == 'pending':
            rec['tcp'], rec['detail'] = 'fail', 'không kết nối kịp (quá thời gian chờ)'
        hosts_out[host] = rec
    for key in ('dns', 'tcp'):
        if control.get(key) == 'pending':
            control[key] = 'fail'

    if do_captive:
        captive_result = captive_box.get('result') or {
            'status': 'error',
            'detected': False,
            'http_status': None,
            'content_type': '',
            'final_host': '',
            'detail': 'quá thời gian chờ kiểm tra Captive Portal',
        }
    else:
        captive_result = {
            'status': 'skipped',
            'detected': False,
            'http_status': None,
            'content_type': '',
            'final_host': '',
            'detail': 'bỏ qua',
        }

    tls_result: dict[str, Any] = {}
    if include_tls:
        try:
            tls_result = dict(tls.info())
        except Exception as exc:  # noqa: BLE001
            tls_result = {'error': _fmt(exc)}

    code, text = verdict(hosts_out, control, captive_result)
    return {
        'hosts': hosts_out,
        'control': control,
        'captive': captive_result,
        'tls': tls_result,
        'verdict': code,
        'verdict_text': text,
        'duration_ms': int((time.monotonic() - t0) * 1000),
    }


def format_probe(probe: Optional[dict[str, Any]]) -> list[str]:
    """Report lines for a probe dict."""
    if not isinstance(probe, dict):
        return []
    try:
        if len(probe) == 0:
            return []
    except Exception:  # noqa: BLE001
        return []
    lines = []
    hosts_map = probe.get('hosts')
    if isinstance(hosts_map, dict):
        try:
            host_items = list(hosts_map.items())
        except Exception:  # noqa: BLE001
            host_items = []
        for host, rec in host_items:
            if not isinstance(rec, dict):
                continue
            host_s = _safe_str(host, '?') or '?'
            dns_val = _safe_str(rec.get('dns'))
            dns = f"DNS {'ok ' + _safe_str(rec.get('ip')) if dns_val == 'ok' else 'LỖI'}"
            tcp_val = _safe_str(rec.get('tcp'))
            if tcp_val == 'ok':
                ms_raw = rec.get('ms')
                ms_s = _safe_str(ms_raw, 'None') if ms_raw is not None else 'None'
                tcp = f'TCP:443 ok ({ms_s} ms)'
            elif tcp_val == 'fail':
                tcp = 'TCP:443 LỖI'
            elif tcp_val == 'skip':
                tcp = 'TCP:443 bỏ qua'
            else:
                tcp = 'TCP:443 ?'
            detail_s = _safe_str(rec.get('detail'))
            extra = f' — {detail_s}' if detail_s else ''
            lines.append(f'  {host_s}: {dns}; {tcp}{extra}')
    c = probe.get('control') if isinstance(probe.get('control'), dict) else {}
    c_dns = _safe_str(c.get('dns', '?'), '?') or '?'
    c_tcp = _safe_str(c.get('tcp', '?'), '?') or '?'
    lines.append(f'  Điểm đối chứng: DNS {c_dns}; TCP 1.1.1.1:443 {c_tcp}')
    captive = probe.get('captive')
    if isinstance(captive, dict):
        cap_status = _safe_str(captive.get('status'))
        if cap_status and cap_status != 'skipped':
            cap_detail = _safe_str(captive.get('detail', ''))
            if _safe_bool(captive.get('detected')):
                lines.append(f'  Captive Portal: PHÁT HIỆN ({cap_detail})')
            else:
                lines.append(f'  Captive Portal: {cap_status} ({cap_detail})')
    tls_info = probe.get('tls')
    try:
        has_tls = isinstance(tls_info, dict) and len(tls_info) > 0
    except Exception:  # noqa: BLE001
        has_tls = False
    if has_tls:
        if 'error' in tls_info:
            lines.append(f"  TLS Root Store: lỗi ({_safe_str(tls_info.get('error'))})")
        else:
            bundle = _redact_path(_safe_str(tls_info.get('fallback_bundle', 'không có'), 'không có'))
            sys_r = _safe_str(tls_info.get('system_roots', '?'), '?')
            tru_r = _safe_str(tls_info.get('trusted_roots', '?'), '?')
            ext_r = _safe_str(tls_info.get('extra_roots', 0), '0')
            lines.append(
                f'  TLS Root Store: hệ thống {sys_r} · tổng {tru_r} '
                f'(+{ext_r} certifi: {bundle})'
            )
    verdict_code = _safe_str(probe.get('verdict', '?'), '?') or '?'
    verdict_text = _safe_str(probe.get('verdict_text', ''))
    lines.append(f'  Kết luận tự động ({verdict_code}): {verdict_text}')
    return lines
