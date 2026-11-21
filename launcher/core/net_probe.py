"""Short, bounded connectivity probe that explains *why* a network call failed.

It only resolves names and opens plain TCP connections (no payload is sent).  Comparing GitHub's hosts with a
neutral control tells apart "no Internet", "broken DNS" and "only GitHub is blocked".  Intended to run in a worker
thread right after a network-class failure; never call it from the UI thread.
"""
from __future__ import annotations

import socket
import threading
import time

DEFAULT_HOSTS = ('api.github.com', 'raw.githubusercontent.com', 'github.com')
CONTROL_DNS_HOST = 'www.microsoft.com'
CONTROL_TCP_ADDR = ('1.1.1.1', 443)   # direct IP: works even when DNS is broken


def _default_resolver(host, port):
    info = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return info[0][4][0]


def _default_connector(addr, timeout):
    with socket.create_connection(addr, timeout=timeout):
        return True


def _fmt(exc):
    win = getattr(exc, 'winerror', None)
    eno = getattr(exc, 'errno', None)
    code = f' (WinError {win})' if win else (f' (errno {eno})' if eno else '')
    return type(exc).__name__ + code


def _probe_host(host, port, timeout, resolver, connector, out):
    rec = {'dns': 'pending', 'ip': '', 'tcp': 'pending', 'detail': '', 'ms': None}
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


def _probe_control(timeout, resolver, connector, out):
    rec = {'dns': 'pending', 'tcp': 'pending'}
    out['__control__'] = rec

    def dns():
        try:
            resolver(CONTROL_DNS_HOST, 443)
            rec['dns'] = 'ok'
        except Exception:  # noqa: BLE001
            rec['dns'] = 'fail'

    def tcp():
        try:
            connector(CONTROL_TCP_ADDR, timeout)
            rec['tcp'] = 'ok'
        except Exception:  # noqa: BLE001
            rec['tcp'] = 'fail'

    for fn in (dns, tcp):
        threading.Thread(target=fn, daemon=True).start()


def verdict(hosts, control):
    """(verdict_code, Vietnamese sentence) from per-host results and the control result."""
    states = list(hosts.values())
    if states and all(h['tcp'] == 'ok' for h in states):
        return 'ok', 'Lúc kiểm tra, máy kết nối tới GitHub bình thường. Lỗi có thể chỉ xảy ra thoáng qua; hãy thử lại.'
    ctrl_dns = control.get('dns') == 'ok'
    ctrl_tcp = control.get('tcp') == 'ok'
    failed = [name for name, h in hosts.items() if h['tcp'] != 'ok']
    where = ', '.join(failed)
    if not ctrl_dns and not ctrl_tcp:
        return 'offline', 'Máy đang không có Internet: ngay cả điểm kiểm tra chung cũng không kết nối được. Hãy kiểm tra Wi-Fi/dây mạng.'
    dns_failed = [name for name, h in hosts.items() if h['dns'] != 'ok']
    if dns_failed:
        if ctrl_dns:
            return 'dns_blocked', f'Internet vẫn hoạt động nhưng không tra được địa chỉ ({where}). GitHub có thể bị chặn ở DNS của mạng bạn; thử đổi DNS hoặc dùng VPN.'
        return 'dns_broken', 'Máy vẫn ra được Internet qua địa chỉ IP nhưng DNS đang hỏng, nên không tìm ra GitHub. Hãy đổi DNS sang 1.1.1.1 / 8.8.8.8.'
    if ctrl_tcp or ctrl_dns:
        return 'blocked', f'Internet vẫn hoạt động nhưng kết nối tới GitHub ({where}) bị chặn hoặc quá chậm. Hãy kiểm tra tường lửa, diệt virus, VPN/proxy hoặc đổi mạng.'
    return 'offline', 'Không kết nối được. Hãy kiểm tra mạng.'


def run_probe(hosts=DEFAULT_HOSTS, port=443, timeout=3.5, deadline=8.0, resolver=None, connector=None):
    """Probe ``hosts`` plus a control and return a plain dict (see :func:`verdict`).

    ``resolver(host, port) -> ip`` and ``connector((ip, port), timeout)`` are injectable for tests.  The whole call
    returns within roughly ``deadline`` seconds even when name resolution hangs (worker threads are daemons).
    """
    resolver = resolver or _default_resolver
    connector = connector or _default_connector
    results: dict = {}
    threads = []
    t0 = time.monotonic()
    for host in hosts:
        th = threading.Thread(target=_probe_host, args=(host, port, timeout, resolver, connector, results), daemon=True)
        th.start()
        threads.append(th)
    _probe_control(timeout, resolver, connector, results)
    end = t0 + deadline
    for th in threads:
        th.join(max(0.0, end - time.monotonic()))
    # give the two control sub-threads whatever time is left
    while time.monotonic() < end and (results['__control__']['dns'] == 'pending' or results['__control__']['tcp'] == 'pending'):
        time.sleep(0.05)
    control = dict(results.pop('__control__'))
    hosts_out = {}
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
    code, text = verdict(hosts_out, control)
    return {'hosts': hosts_out, 'control': control, 'verdict': code, 'verdict_text': text,
            'duration_ms': int((time.monotonic() - t0) * 1000)}


def format_probe(probe):
    """Report lines for a probe dict."""
    if not probe:
        return []
    lines = []
    for host, rec in probe.get('hosts', {}).items():
        dns = f"DNS {'ok ' + rec['ip'] if rec['dns'] == 'ok' else 'LỖI'}"
        tcp = {'ok': f"TCP:443 ok ({rec.get('ms')} ms)", 'fail': 'TCP:443 LỖI', 'skip': 'TCP:443 bỏ qua'}.get(rec['tcp'], 'TCP:443 ?')
        extra = f" — {rec['detail']}" if rec.get('detail') else ''
        lines.append(f'  {host}: {dns}; {tcp}{extra}')
    c = probe.get('control', {})
    lines.append(f"  Điểm đối chứng: DNS {c.get('dns', '?')}; TCP 1.1.1.1:443 {c.get('tcp', '?')}")
    lines.append(f"  Kết luận tự động ({probe.get('verdict', '?')}): {probe.get('verdict_text', '')}")
    return lines
