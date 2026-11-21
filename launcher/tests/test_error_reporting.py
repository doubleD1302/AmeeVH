"""Plain-language error codes, copyable reports, connectivity probe and the install-blocker UI."""
import ast
import errno
import http.client
import http.server
import shutil
import subprocess
import threading
import urllib.request
import json
import os
import socket
import ssl
import sys
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from launcher.core import error_catalog as ec
from launcher.core import net_probe
from launcher.core import tls
from launcher.core.game_detection import find_game_exe_hint
from launcher.core.error_report import ErrorContext, build_report, redact, safe_url
from launcher.core.network import NetworkService
from launcher.core.safety import InstallerError
from launcher.core.types import GameInfo
from launcher.core.update_notice import translation_state

CORE = ROOT / 'launcher' / 'core'


def _raised_internal_codes():
    """Every literal code passed to InstallerError/OfficialResourceError/CancelledError anywhere in core/."""
    found = {}
    for path in sorted(CORE.glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf8'))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, 'attr', '')
            if name not in ('InstallerError', 'OfficialResourceError', 'CancelledError'):
                continue
            candidates = list(node.args[1:2]) + [k.value for k in node.keywords if k.arg == 'code']
            for arg in candidates:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    found.setdefault(arg.value, f'{path.name}:{node.lineno}')
    return found


class CatalogTests(unittest.TestCase):
    def test_every_raised_code_is_mapped_to_a_catalog_entry(self):
        missing = {}
        for code, where in _raised_internal_codes().items():
            if code == 'INSTALL_ERR':          # default of InstallerError(), classified from its text/cause instead
                continue
            target = ec.INTERNAL_MAP.get(code)
            if target is None:
                missing[code] = where
        self.assertEqual(missing, {}, 'InstallerError codes without a plain-language mapping')

    def test_catalog_entries_are_complete_and_consistent(self):
        for code in ec.all_codes():
            info = ec.lookup(code)
            self.assertTrue(code.startswith('E-'), code)
            self.assertTrue(info.title.strip() and info.summary.strip(), code)
            if info.level == 'error':
                self.assertGreaterEqual(len(info.steps), 1, f'{code} needs at least one step')
            for step in info.steps:
                self.assertTrue(step.strip(), code)
        for internal, target in ec.INTERNAL_MAP.items():
            self.assertIn(target, ec.all_codes(), f'{internal} -> {target}')

    def test_unknown_and_http_codes_resolve(self):
        self.assertEqual(ec.lookup('E-DOES-NOT-EXIST').code, 'E-UNKNOWN')
        self.assertEqual(ec.lookup('E-HTTP-429').code, 'E-HTTP-429')
        self.assertIn('giới hạn', ec.lookup('E-HTTP-429').title)
        self.assertIn('404', ec.lookup('E-HTTP-404').title + '404')
        self.assertIn('sự cố', ec.lookup('E-HTTP-503').title)
        self.assertIn('từ chối', ec.lookup('E-HTTP-418').title)

    def test_publisher_wording_does_not_blame_github(self):
        info = ec.lookup('E-NET-DNS', 'publisher')
        self.assertNotIn('GitHub', info.title + info.summary + ' '.join(info.steps))
        self.assertIn('nhà phát hành', info.title)


class ClassificationTests(unittest.TestCase):
    def code(self, exc, **kw):
        return ec.diagnose(exc, **kw).code

    def test_network_exceptions(self):
        self.assertEqual(self.code(urllib.error.URLError(socket.gaierror(11001, 'getaddrinfo failed'))), 'E-NET-DNS')
        self.assertEqual(self.code(urllib.error.URLError(socket.timeout('timed out'))), 'E-NET-TIMEOUT')
        self.assertEqual(self.code(TimeoutError('timed out')), 'E-NET-TIMEOUT')
        self.assertEqual(self.code(urllib.error.URLError(ConnectionRefusedError(10061, 'refused'))), 'E-NET-REFUSED')
        self.assertEqual(self.code(ConnectionResetError(10054, 'reset')), 'E-NET-RESET')
        self.assertEqual(self.code(http.client.IncompleteRead(b'ab')), 'E-NET-RESET')
        self.assertEqual(self.code(urllib.error.URLError(ssl.SSLCertVerificationError('CERTIFICATE_VERIFY_FAILED'))), 'E-NET-TLS-CERT')
        self.assertEqual(self.code(ssl.SSLError('handshake failure')), 'E-NET-TLS')
        self.assertEqual(self.code(urllib.error.URLError(OSError('Tunnel connection failed: 407 Proxy Authentication Required'))), 'E-NET-PROXY')

    def test_proxy_authentication_is_a_proxy_problem(self):
        self.assertEqual(self.code(urllib.error.HTTPError('https://x', 407, 'Proxy Authentication Required', http.client.HTTPMessage(), None)), 'E-NET-PROXY')

    def test_windows_socket_errors(self):
        blocked = OSError(10013, 'forbidden by its access permissions')
        blocked.winerror = 10013
        self.assertEqual(self.code(urllib.error.URLError(blocked)), 'E-NET-BLOCKED')
        unreachable = OSError(10051, 'network unreachable')
        unreachable.winerror = 10051
        self.assertEqual(self.code(urllib.error.URLError(unreachable)), 'E-NET-OFFLINE')

    def test_http_status(self):
        hdrs = http.client.HTTPMessage()
        for status, expected in ((403, 'E-HTTP-403'), (429, 'E-HTTP-429'), (404, 'E-HTTP-404'), (502, 'E-HTTP-502')):
            self.assertEqual(self.code(urllib.error.HTTPError('https://x', status, 'm', hdrs, None)), expected)
        # a plain InstallerError carrying the message still resolves through the text heuristics
        self.assertEqual(ec.classify_text('Máy chủ trả HTTP 503 (github.com).'), 'E-HTTP-503')
        self.assertEqual(ec.classify_text('HTTP Error 403: rate limit exceeded'), 'E-HTTP-403')

    def test_filesystem_exceptions(self):
        self.assertEqual(self.code(OSError(errno.ENOSPC, 'No space left on device')), 'E-STORAGE')
        self.assertEqual(self.code(PermissionError(errno.EACCES, 'denied')), 'E-FILE-DENIED')
        locked = PermissionError(errno.EACCES, 'used by another process')
        locked.winerror = 32
        self.assertEqual(self.code(locked), 'E-FILE-IN-USE')
        self.assertEqual(self.code(PermissionError(errno.EACCES, 'denied')), 'E-FILE-DENIED')
        self.assertEqual(self.code(FileNotFoundError(errno.ENOENT, 'missing')), 'E-FILE-MISSING')
        self.assertEqual(self.code(json.JSONDecodeError('x', '<html>', 0)), 'E-DATA-JSON')

    def test_installer_codes_map_to_plain_codes(self):
        for internal, expected in (
            ('HASH_MISMATCH', 'E-DL-VERIFY'), ('GAME_RUNNING', 'E-GAME-RUNNING'), ('INVALID_ROOT', 'E-NO-EXE'),
            ('PREIMAGE_CONFLICT', 'E-FILE-CHANGED'), ('DISK_FULL', 'E-STORAGE'), ('FILE_MISMATCH', 'E-FILE-MISMATCH'),
            ('FILE_ACCESS_DENIED', 'E-FILE-DENIED'), ('MANIFEST_MISSING', 'E-MANIFEST-MISSING'),
        ):
            self.assertEqual(self.code(InstallerError('x', internal)), expected, internal)

    def test_receipt_codes_depend_on_the_real_situation(self):
        self.assertEqual(self.code(InstallerError('Chưa có biên bản cài đặt hợp lệ để kiểm tệp.', 'NOT_VERIFIED')), 'E-NO-RECEIPT')
        self.assertEqual(self.code(InstallerError('Biên bản không khớp thư mục hoặc định dạng.', 'NOT_VERIFIED')), 'E-RECEIPT-MISMATCH')

    def test_wrappers_report_the_real_cause(self):
        try:
            try:
                raise urllib.error.URLError(socket.gaierror(11001, 'getaddrinfo failed'))
            except Exception as cause:
                raise InstallerError('Tải tệp không thành công sau 5 lần thử (Lỗi kết nối).', 'DOWNLOAD_FAILED') from cause
        except InstallerError as exc:
            d = ec.diagnose(exc)
        self.assertEqual(d.code, 'E-NET-DNS')
        self.assertEqual(d.wrapper, 'DOWNLOAD_FAILED')
        locked = PermissionError(errno.EACCES, 'used')
        locked.winerror = 32
        try:
            try:
                raise locked
            except OSError as cause:
                raise InstallerError('Cài đặt thất bại; đã phục hồi', 'TRANSACTION_FAILED') from cause
        except InstallerError as exc:
            d = ec.diagnose(exc)
        self.assertEqual((d.code, d.wrapper), ('E-FILE-IN-USE', 'TRANSACTION_FAILED'))
        # a wrapper with no usable cause still has a code of its own
        self.assertEqual(ec.diagnose(InstallerError('x', 'TRANSACTION_FAILED')).code, 'E-INSTALL-ROLLED-BACK')
        self.assertEqual(ec.diagnose(InstallerError('x', 'DOWNLOAD_FAILED')).code, 'E-DL-FAILED')

    def test_unknown_python_errors_are_internal_not_misleading(self):
        self.assertEqual(self.code(KeyError('boom')), 'E-INTERNAL')
        self.assertEqual(self.code(InstallerError('???')), 'E-UNKNOWN')
        self.assertEqual(self.code(None, fallback='E-NO-RECEIPT'), 'E-NO-RECEIPT')

    def test_download_keeps_the_underlying_network_cause(self):
        with tempfile.TemporaryDirectory() as tmp:
            svc = NetworkService(timeout=1)
            err = urllib.error.URLError(socket.gaierror(11001, 'getaddrinfo failed'))
            with mock.patch('launcher.core.network.urllib.request.urlopen', side_effect=err), \
                    mock.patch('launcher.core.network.time.sleep'):
                with self.assertRaises(InstallerError) as ctx:
                    svc.download('https://example.invalid/a.bin', Path(tmp) / 'a.bin', 10, max_retries=2)
        self.assertEqual(ctx.exception.code, 'DOWNLOAD_FAILED')
        self.assertEqual(ec.diagnose(ctx.exception).code, 'E-NET-DNS')

    def test_official_resource_errors_use_publisher_wording(self):
        from launcher.core.official_resources import OfficialResourceError
        d = ec.diagnose(OfficialResourceError('Không kết nối được máy chủ tài nguyên chính thức: getaddrinfo failed', 'NETWORK'))
        self.assertEqual(d.code, 'E-NET-DNS')
        self.assertEqual(d.subject, 'publisher')
        self.assertNotIn('GitHub', d.info.title)


class ReportTests(unittest.TestCase):
    def test_report_has_code_id_steps_and_full_text(self):
        exc = urllib.error.URLError(socket.gaierror(11001, 'getaddrinfo failed'))
        r = build_report(exc=exc, action='Cài Việt hoá', ctx=ErrorContext(action='Cài Việt hoá', operation='install'))
        self.assertEqual(r.code, 'E-NET-DNS')
        self.assertIn(r.report_id, r.text)
        self.assertTrue(r.text.startswith('STELLA SORA VIỆT HOÁ — MÃ LỖI E-NET-DNS'))
        for needle in ('Windows PC', 'Đang làm: Cài Việt hoá', 'Chuỗi lỗi', 'getaddrinfo', '--- Hệ thống ---', '--- Game ---', '--- GitHub'):
            self.assertIn(needle, r.text)
        self.assertGreaterEqual(len(r.steps), 2)
        self.assertIn('Mã lỗi: E-NET-DNS', r.code_line)
        self.assertIn('CÁCH XỬ LÝ', r.dialog_details())

    def test_report_collects_game_sync_and_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = GameInfo(installed=True, game_path=Path(tmp), platform='steam', version='2.1.0', resource_version='123')
            sync = {'message': 'x', 'fresh': False, 'release_status': 'error', 'release_error': 'boom', 'release_error_code': 'E-NET-DNS',
                    'manifest_status': 'unavailable'}
            probe = net_probe.run_probe(('api.github.com',), resolver=lambda h, p: (_ for _ in ()).throw(socket.gaierror(11001, 'x')),
                                        connector=lambda a, t: True, deadline=2)
            ctx = ErrorContext(action='Cài Việt hoá', game=game, sync=sync, probe=probe,
                               channel={'repo': 'a/b', 'branch': 'main', 'release_url': 'https://api.github.com/repos/a/b/releases/latest?token=SECRET'})
            r = build_report('E-NET-DNS', ctx=ctx)
        self.assertIn('steam', r.text)
        self.assertIn('Biên bản cài: KHÔNG CÓ', r.text)
        self.assertIn('Lỗi bản phát hành [E-NET-DNS]', r.text)
        self.assertIn('Đo kết nối mạng', r.text)
        self.assertIn('Kiểm tra tự động', r.summary)
        self.assertNotIn('SECRET', r.text)

    def test_redaction_of_account_paths_and_query_strings(self):
        home = str(Path.home())
        text = redact(f'{home}\\AppData\\x and {home.replace(chr(92), "/")}/y https://h.example/p?access_token=ABC#frag')
        self.assertNotIn(home, text)
        self.assertIn('%USERPROFILE%', text)
        self.assertNotIn('ABC', text)
        self.assertEqual(safe_url('https://user:pw@api.github.com/a/b?x=1#f'), 'https://api.github.com/a/b')

    def test_build_report_never_raises_on_hostile_context(self):
        class Boom:
            def __getattr__(self, name):
                raise RuntimeError('nope')
        r = build_report('E-UNKNOWN', exc=ValueError('x'), ctx=ErrorContext(game=Boom(), path_manager=Boom(), sync={'probe': 1}, channel=Boom()))
        self.assertTrue(r.code)
        self.assertIn('MÃ LỖI', r.text)
        self.assertIn('không đọc được mục này', r.text)    # only the broken section is lost
        self.assertIn('Chuỗi lỗi', r.text)

    def test_soft_situations_are_not_shown_as_errors(self):
        self.assertEqual(build_report('E-NO-RECEIPT').level, 'info')
        self.assertEqual(build_report('E-GAME-RUNNING').level, 'warning')
        self.assertEqual(build_report('E-NET-DNS').level, 'error')



@unittest.skipUnless(shutil.which('openssl'), 'openssl CLI needed to create a throw-away certificate')
class TlsFallbackTests(unittest.TestCase):
    """The merged trust store accepts a root that the default (Windows-only) context rejects."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.cert, cls.key = d / 'ca.pem', d / 'key.pem'
        subprocess.run(
            ['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(cls.key), '-out', str(cls.cert), '-days', '2',
             '-subj', '/CN=localhost', '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1', '-addext', 'basicConstraints=critical,CA:TRUE'],
            check=True, capture_output=True,
        )
        server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_ctx.load_cert_chain(str(cls.cert), str(cls.key))

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body = b'{"ok": true}'
                self.send_response(200)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        cls.httpd = http.server.HTTPServer(('127.0.0.1', 0), Handler)
        cls.httpd.socket = server_ctx.wrap_socket(cls.httpd.socket, server_side=True)
        cls.url = f'https://127.0.0.1:{cls.httpd.server_address[1]}/'
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.tmp.cleanup()

    def test_default_trust_rejects_an_unknown_root_as_a_certificate_error(self):
        with self.assertRaises(urllib.error.URLError) as ctx:
            urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context())).open(self.url, timeout=5)
        self.assertEqual(ec.diagnose(ctx.exception).code, 'E-NET-TLS-CERT')

    def test_merged_trust_accepts_it_and_stays_strict(self):
        merged = tls.build_context(extra_cafile=self.cert)
        self.assertEqual(merged.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(merged.check_hostname)
        with urllib.request.build_opener(urllib.request.HTTPSHandler(context=merged)).open(self.url, timeout=5) as resp:
            self.assertEqual(resp.status, 200)

    def test_info_counts_the_extra_roots(self):
        info = tls.info(extra_cafile=self.cert)
        self.assertEqual(info['extra_roots'], 1)
        self.assertGreaterEqual(info['trusted_roots'], info['system_roots'] + 1)

    def test_install_sets_the_process_wide_opener(self):
        previous = urllib.request._opener
        try:
            tls.install(extra_cafile=self.cert)
            with urllib.request.urlopen(self.url, timeout=5) as resp:   # plain urlopen, as every launcher call does
                self.assertEqual(resp.status, 200)
        finally:
            urllib.request._opener = previous


class TlsWithoutCertifiTests(unittest.TestCase):
    def test_missing_certifi_never_breaks_the_launcher(self):
        with mock.patch.dict(sys.modules, {'certifi': None}):
            ctx = tls.build_context()
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(ctx.check_hostname)


class GameFolderHintTests(unittest.TestCase):
    def test_parent_and_child_folders_point_to_the_real_game_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / 'StellaSora_EN'
            (game / 'StellaSora_Data').mkdir(parents=True)
            (game / 'StellaSora.exe').write_bytes(b'MZ')
            self.assertEqual(find_game_exe_hint(root), game)                       # picked the parent
            self.assertEqual(find_game_exe_hint(game / 'StellaSora_Data'), game)   # picked a sub-folder
            self.assertIsNone(find_game_exe_hint(root / 'nowhere'))


class ProbeTests(unittest.TestCase):
    HOSTS = ('api.github.com', 'github.com')

    def run_probe(self, resolver, connector, **kw):
        return net_probe.run_probe(self.HOSTS, resolver=resolver, connector=connector, deadline=kw.pop('deadline', 3), **kw)

    def test_everything_reachable(self):
        p = self.run_probe(lambda h, port: '1.2.3.4', lambda addr, t: True)
        self.assertEqual(p['verdict'], 'ok')

    def test_only_github_dns_is_blocked(self):
        def resolver(host, port):
            if 'github' in host:
                raise socket.gaierror(11001, 'x')
            return '1.2.3.4'
        p = self.run_probe(resolver, lambda addr, t: True)
        self.assertEqual(p['verdict'], 'dns_blocked')
        self.assertEqual(p['hosts']['api.github.com']['dns'], 'fail')

    def test_dns_broken_but_ip_reachable(self):
        def resolver(host, port):
            raise socket.gaierror(11001, 'x')
        p = self.run_probe(resolver, lambda addr, t: True)
        self.assertEqual(p['verdict'], 'dns_broken')

    def test_no_internet_at_all(self):
        def resolver(host, port):
            raise socket.gaierror(11001, 'x')
        def connector(addr, t):
            raise OSError('unreachable')
        self.assertEqual(self.run_probe(resolver, connector)['verdict'], 'offline')

    def test_github_blocked_while_internet_works(self):
        def connector(addr, t):
            if addr[0] == '9.9.9.9':
                raise TimeoutError('t')
            return True
        p = self.run_probe(lambda h, port: '9.9.9.9' if 'github' in h else '1.2.3.4', connector)
        self.assertEqual(p['verdict'], 'blocked')

    def test_hanging_resolver_is_bounded(self):
        def resolver(host, port):
            time.sleep(5)
        t0 = time.monotonic()
        p = self.run_probe(resolver, lambda a, t: True, deadline=0.6)
        self.assertLess(time.monotonic() - t0, 2.5)
        self.assertEqual(p['hosts']['github.com']['dns'], 'fail')
        self.assertIn('Kết luận tự động', '\n'.join(net_probe.format_probe(p)))


class BlockerStateTests(unittest.TestCase):
    GAME = GameInfo(installed=True, game_path=Path('.'), version='2.1.0', resource_version='1')

    def state(self, sync, game=None):
        return translation_state(sync, game or self.GAME)

    def test_not_synced_yet_is_pending_not_an_error(self):
        st = self.state({'message': 'Đang đọc…', 'fresh': False})
        self.assertEqual(st['blocker_code'], 'E-SYNC-PENDING')
        self.assertFalse(st['can_install'])

    def test_release_unreachable_uses_the_recorded_code(self):
        st = self.state({'release_status': 'error', 'manifest_status': 'unavailable', 'release_error': 'x', 'release_error_code': 'E-NET-TIMEOUT'})
        self.assertEqual(st['blocker_code'], 'E-NET-TIMEOUT')

    def test_release_error_text_is_classified_when_no_code_recorded(self):
        st = self.state({'release_status': 'error', 'manifest_status': 'unavailable', 'release_error': '<urlopen error [Errno 11001] getaddrinfo failed>'})
        self.assertEqual(st['blocker_code'], 'E-NET-DNS')

    def test_cached_release_is_not_good_enough(self):
        st = self.state({'release_status': 'cached', 'manifest_status': 'unavailable', 'release_error': 'timed out'})
        self.assertEqual(st['blocker_code'], 'E-NET-TIMEOUT')

    def test_manifest_problem_with_working_release(self):
        st = self.state({'release_status': 'online', 'manifest_status': 'error', 'manifest_error': 'Bản phát hành chưa có bảng kê', 'manifest_error_code': 'E-MANIFEST-MISSING'})
        self.assertEqual(st['blocker_code'], 'E-MANIFEST-MISSING')

    def test_bad_channel_config_and_worker_failure(self):
        self.assertEqual(self.state({'message': 'x', 'configuration_error': 'Kho sai'})['blocker_code'], 'E-CONFIG-CHANNEL')
        self.assertEqual(self.state({'message': 'x', 'error_code': 'E-NET-TLS-CERT'})['blocker_code'], 'E-NET-TLS-CERT')

    def test_online_but_no_game_folder(self):
        online = {'release_status': 'online', 'manifest_status': 'online', 'translation_version': '1.3.2'}
        self.assertEqual(self.state(online, GameInfo())['blocker_code'], 'E-NO-GAME-FOLDER')

    def test_healthy_state_has_no_blocker(self):
        online = {'release_status': 'online', 'manifest_status': 'online', 'translation_version': '1.3.2',
                  'translation_game': '2.1.0', 'translation_resource': '1'}
        st = self.state(online)
        self.assertTrue(st['can_install'])
        self.assertNotIn('blocker_code', st)


class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        from launcher.ui.assets import AssetManager
        from launcher.ui.typography import register_fonts
        cls.app = QApplication.instance() or QApplication([])
        res = ROOT / 'launcher' / 'resources'
        register_fonts(res)
        AssetManager.initialize(res)

    def test_message_dialog_copies_the_full_report(self):
        from launcher.ui.views.message_dialog import MessageDialog
        report = build_report(exc=urllib.error.URLError(socket.gaierror(11001, 'getaddrinfo failed')), action='Cài Việt hoá')
        dlg = MessageDialog('Cài Việt hoá', '', report=report)
        self.assertEqual(dlg.copy_btn.text(), 'Sao chép mã lỗi')
        self.assertIn(report.code, dlg.subtitle.text())
        self.assertIn(report.report_id, dlg.subtitle.text())
        dlg._copy_to_clipboard()
        copied = self.app.clipboard().text()
        self.assertEqual(copied, report.text)
        self.assertTrue(copied.startswith('STELLA SORA VIỆT HOÁ — MÃ LỖI E-NET-DNS'))
        self.assertIn('Đã sao chép', dlg.copied_label.text())

    def test_legacy_message_dialog_is_unchanged(self):
        from launcher.ui.views.message_dialog import MessageDialog
        dlg = MessageDialog('Lỗi', 'Nội dung', 'Chi tiết', is_error=True)
        self.assertEqual(dlg.copy_btn.text(), 'Sao chép')
        dlg._copy_to_clipboard()
        self.assertEqual(self.app.clipboard().text(), 'Nội dung\nChi tiết')

    def test_install_blocker_link_follows_the_real_reason(self):
        from launcher.ui.views.overview_view import OverviewView
        v = OverviewView()
        clicks = []
        v.blocker_requested.connect(lambda: clicks.append(1))
        v.update_game_status(GameInfo())
        self.assertEqual(v.install_blocker_code(), 'E-NO-GAME-FOLDER')
        v.update_game_status(GameInfo(installed=True, game_path=Path('.'), is_running=True))
        self.assertEqual(v.install_blocker_code(), 'E-GAME-RUNNING')
        v.update_game_status(GameInfo(installed=True, game_path=Path('.')))
        v.set_install_allowed(False, 'x', 'E-NET-DNS')
        self.assertEqual(v.install_blocker_code(), 'E-NET-DNS')
        self.assertFalse(v.btn_blocker.isHidden())
        self.assertIn('E-NET-DNS', v.btn_blocker.text())
        self.assertFalse(v.btn_install.isEnabled())
        v.btn_blocker.click()
        self.assertEqual(clicks, [1])
        v.set_install_allowed(True, 'ok')
        self.assertEqual(v.install_blocker_code(), '')
        self.assertTrue(v.btn_blocker.isHidden())
        self.assertTrue(v.btn_install.isEnabled())
        v.set_busy(True)
        v.set_install_allowed(False, 'x', 'E-NET')
        self.assertTrue(v.btn_blocker.isHidden())      # busy: the reason is simply "an operation is running"



class MainWindowFlowTests(unittest.TestCase):
    """Real MainWindow flows with the modal dialog captured instead of executed (no network, no event loop)."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        from launcher.ui.assets import AssetManager
        from launcher.ui.typography import register_fonts
        cls.app = QApplication.instance() or QApplication([])
        res = ROOT / 'launcher' / 'resources'
        register_fonts(res)
        AssetManager.initialize(res)

    def setUp(self):
        from launcher.core.config import PathManager, ConfigManager
        from launcher.ui.main_window import MainWindow
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.game = self.tmp / 'game'
        self.game.mkdir()
        (self.game / 'StellaSora.exe').write_bytes(b'MZ')
        pm = PathManager(ROOT / 'launcher' / 'resources', self.tmp / 'appdata')
        self.win = MainWindow(pm, ConfigManager(pm))
        self.shown = []
        self.win._show = lambda d: self.shown.append(d) or 0
        self.win._apply_game_info(GameInfo(installed=True, game_path=self.game, platform='steam', version='2.1.0', resource_version='1'))
        patcher = mock.patch('launcher.ui.main_window.is_game_process_running', return_value=False)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.win.close()
        self._tmp.cleanup()

    def last_code(self):
        self.assertTrue(self.shown, 'no dialog was shown')
        return self.shown[-1].report.code

    def test_verify_before_any_install_explains_instead_of_alarming(self):
        self.win._on_verify_clicked()
        self.assertEqual(self.last_code(), 'E-NO-RECEIPT')
        self.assertEqual(self.shown[-1].report.level, 'info')
        self.assertIn('Cài Việt hoá', ' '.join(self.shown[-1].report.steps))

    def test_receipt_that_belongs_to_another_folder_is_called_out(self):
        (self.game / '.vietnamese_patch_receipt.json').write_text(json.dumps({'schema': 2, 'game_root': 'X:\elsewhere', 'files': {'a': {}}}), encoding='utf8')
        self.win._apply_game_info(GameInfo(installed=True, game_path=self.game))
        self.win._on_verify_clicked()
        self.assertEqual(self.last_code(), 'E-RECEIPT-MISMATCH')

    def test_game_running_and_no_folder(self):
        info = self.win.current_game_info
        info.is_running = True
        with mock.patch('launcher.ui.main_window.is_game_process_running', return_value=True):
            self.win._on_verify_clicked()
        self.assertEqual(self.last_code(), 'E-GAME-RUNNING')
        self.win._apply_game_info(GameInfo())
        self.win._on_install_clicked()
        self.assertEqual(self.last_code(), 'E-NO-GAME-FOLDER')

    def test_failed_operation_is_classified_from_the_exception(self):
        try:
            try:
                raise urllib.error.URLError(socket.gaierror(11001, 'getaddrinfo failed'))
            except Exception as cause:
                raise InstallerError('Tải tệp không thành công sau 5 lần thử (Lỗi kết nối).', 'DOWNLOAD_FAILED') from cause
        except InstallerError as exc:
            self.win.active_operation_id = 'op1'
            self.win.operation_kind = 'install'
            self.win._finish('op1', False, {'message': str(exc), 'error_code': exc.code, 'exc': exc})
        self.assertEqual(self.last_code(), 'E-NET-DNS')
        report = self.shown[-1].report
        self.assertIn('[install]', report.text)
        self.assertIn('DOWNLOAD_FAILED', report.text)
        self.assertEqual(self.shown[-1].copy_btn.text(), 'Sao chép mã lỗi')

    def test_failed_operation_without_exception_uses_internal_code_map(self):
        self.win.active_operation_id = 'op2'
        self.win.operation_kind = 'verify'
        self.win._finish('op2', False, {'message': 'Tệp không khớp bản đã cài: a', 'error_code': 'FILE_MISMATCH'})
        self.assertEqual(self.last_code(), 'E-FILE-MISMATCH')

    def test_github_sync_failure_blocks_install_with_the_exact_reason(self):
        exc = urllib.error.URLError(socket.gaierror(11001, 'getaddrinfo failed'))
        self.win._background_finish(self.win._github_identity, False, {'message': str(exc), 'exc': exc})
        state = self.win._refresh_translation_state()
        self.assertEqual(state['blocker_code'], 'E-NET-DNS')
        view = self.win.overview_view
        self.assertEqual(view.install_blocker_code(), 'E-NET-DNS')
        self.assertFalse(view.btn_install.isEnabled())
        self.win._explain_install_blocker()
        self.assertEqual(self.last_code(), 'E-NET-DNS')

    def test_partial_sync_uses_recorded_codes(self):
        sync = {'release_status': 'error', 'manifest_status': 'unavailable', 'release_error': 'timed out', 'release_error_code': 'E-NET-TIMEOUT',
                'notification_status': 'bundled', 'notification_message': '', 'notifications': [], 'notification_version': None,
                'probe': {'hosts': {}, 'control': {'dns': 'ok', 'tcp': 'ok'}, 'verdict': 'blocked', 'verdict_text': 'GitHub bị chặn.'}}
        self.win._background_finish(self.win._github_identity, True, dict(sync))
        self.win._explain_install_blocker()
        self.assertEqual(self.last_code(), 'E-NET-TIMEOUT')
        self.assertIn('GitHub bị chặn.', self.shown[-1].report.text)

    def test_manual_check_shows_the_reason_not_a_generic_message(self):
        self.win._manual_translation_check = True
        exc = ssl.SSLCertVerificationError('CERTIFICATE_VERIFY_FAILED')
        with mock.patch('launcher.ui.main_window.QTimer.singleShot', side_effect=lambda ms, fn: fn()):
            self.win._background_finish(self.win._github_identity, False, {'message': str(exc), 'exc': exc})
        self.assertEqual(self.last_code(), 'E-NET-TLS-CERT')

    def test_unhandled_exception_hook_shows_internal_error_once(self):
        self.win.show_unhandled(KeyError('boom'))
        self.assertEqual(self.last_code(), 'E-INTERNAL')
        self.assertIn('KeyError', self.shown[-1].report.text)


    def test_local_payload_problem_has_its_own_code_and_the_right_fix(self):
        empty = self.tmp / 'payload'
        empty.mkdir()
        self.win.config_manager.set('payload_path', str(empty))
        state = self.win._refresh_translation_state()
        self.assertEqual(state['blocker_code'], 'E-LOCAL-PAYLOAD')
        self.assertFalse(state['can_install'])
        self.assertEqual(self.win.overview_view.install_blocker_code(), 'E-LOCAL-PAYLOAD')
        self.win._explain_install_blocker()
        report = self.shown[-1].report
        self.assertEqual(report.code, 'E-LOCAL-PAYLOAD')
        self.assertIn('Gói cục bộ', ' '.join(report.steps))
        self.assertIn(str(empty), report.message)

    def test_picking_the_parent_folder_says_where_the_game_really_is(self):
        self.win.active_operation_id = 'op3'
        self.win.operation_kind = 'select_root'
        self.win._finish('op3', True, {'game': GameInfo(installed=False, game_path=self.tmp)})
        self.assertEqual(self.last_code(), 'E-NO-EXE')
        self.assertIn(str(self.game), self.shown[-1].report.summary)
        self.assertIn('Hãy chọn thư mục đó', self.shown[-1].report.summary)

    def test_no_receipt_after_restoring_original_data_is_explained(self):
        self.win._apply_game_info(GameInfo(installed=True, game_path=self.game, official_restore={'restored_at': '2026-11-21T05:03:49+00:00'}))
        self.win._on_verify_clicked()
        self.assertEqual(self.last_code(), 'E-NO-RECEIPT')
        self.assertIn('khôi phục dữ liệu gốc', self.shown[-1].report.summary)


if __name__ == '__main__':
    unittest.main()
