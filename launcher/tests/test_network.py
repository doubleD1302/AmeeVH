from pathlib import Path
from contextlib import contextmanager
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import tempfile
import threading
import unittest
from unittest.mock import patch

from launcher.core.network import NetworkService
from launcher.core.safety import InstallerError


class DownloadResponse:
    def __init__(self, data, status=200, headers=None):
        self.bio = io.BytesIO(data)
        self.status = status
        self.headers = headers or {}

    def read(self, n):
        return self.bio.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


@contextmanager
def interrupted_http_download(content, first_size):
    """Real HTTPResponse.read(n): an early socket EOF need not raise IncompleteRead."""
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            requested_range = self.headers.get('Range')
            requests.append(requested_range)
            if len(requests) == 1:
                self.send_response(200)
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(content[:first_size])
                self.wfile.flush()
                self.close_connection = True
                return
            start = int(requested_range.removeprefix('bytes=').removesuffix('-'))
            self.send_response(206)
            self.send_header('Content-Length', str(len(content) - start))
            self.send_header('Content-Range', f'bytes {start}-{len(content)-1}/{len(content)}')
            self.end_headers()
            self.wfile.write(content[start:])

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.05), daemon=True)
    worker.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/payload.bin', requests
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)


class TestNetworkService(unittest.TestCase):
    def setUp(self):
        self.net = NetworkService()

    def test_default_notifications_available_offline(self):
        fallback = Path(__file__).resolve().parents[1] / "resources" / "ui" / "notifications.json"
        notifs = self.net.fetch_notifications(fallback)
        self.assertTrue(len(notifs) >= 1)

    def test_supporter_data_strictly_unavailable_empty(self):
        supp_data = self.net.get_supporter_data()
        self.assertEqual(supp_data.status, "unavailable")
        self.assertEqual(len(supp_data.supporters), 0)
        self.assertIn("chưa có nguồn dữ liệu", supp_data.qr_placeholder_text)

    def test_check_for_updates_offline(self):
        res = self.net.check_for_updates("1.0.5")
        self.assertFalse(res["has_update"])
        self.assertIsNone(res["latest_version"])

    def test_download_already_completed(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "test.bin"
            content = b"1234567890"
            dest.write_bytes(content)
            sha = hashlib.sha256(content).hexdigest()

            # Should return immediately without any network calls
            out = self.net.download("https://example.com/test.bin", dest, len(content), sha=sha)
            self.assertEqual(out, dest)
            self.assertEqual(out.read_bytes(), content)

    def test_download_resumes_after_timeout(self):
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "test_resume.bin"
            full_data = b"Hello, resilient download world!"
            size = len(full_data)
            sha = hashlib.sha256(full_data).hexdigest()

            call_count = 0

            class MockResp:
                def __init__(self, data, status):
                    self.bio = io.BytesIO(data)
                    self.status = status
                    self.headers = {'Content-Range': f'bytes 10-{size-1}/{size}'} if status == 206 else {}

                def read(self, n=256*1024):
                    return self.bio.read(n)

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            def fake_urlopen(req, timeout=None):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # First attempt: stream first 10 bytes then simulate a read timeout
                    class TimeoutResp:
                        def __init__(self):
                            self.read_once = False
                            self.status = 200

                        def read(self, n=256*1024):
                            if not self.read_once:
                                self.read_once = True
                                return full_data[:10]
                            raise TimeoutError("The read operation timed out")

                        def __enter__(self):
                            return self

                        def __exit__(self, *args):
                            pass
                    return TimeoutResp()
                else:
                    # Second attempt: check Range header
                    range_hdr = req.get_header("Range")
                    self.assertEqual(range_hdr, "bytes=10-")
                    return MockResp(full_data[10:], 206)

            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                out = self.net.download("https://example.com/resilient.bin", dest, size, sha=sha)
                self.assertEqual(out, dest)
                self.assertEqual(out.read_bytes(), full_data)
                self.assertEqual(call_count, 2)

    def test_download_recovers_short_eof_over_real_http(self):
        size, received = 26210913, 26011641
        data = (b'StellaSora-download-fixture-' * (size // 26 + 1))[:size]
        self.assertEqual(len(data), size)
        with tempfile.TemporaryDirectory() as td, interrupted_http_download(data, received) as (url, requests):
            dest = Path(td) / 'screenshot.bin'
            with patch('launcher.core.network.time.sleep'):
                self.net.download(url, dest, size, hashlib.sha256(data).hexdigest())
            self.assertEqual(requests, [None, f'bytes={received}-'])
            self.assertEqual(dest.read_bytes(), data)

    def test_download_resumes_multiple_short_responses(self):
        data = b'0123456789'
        responses = [DownloadResponse(data[:3]),
                     DownloadResponse(data[3:7], 206, {'Content-Range': 'bytes 3-9/10'}),
                     DownloadResponse(data[7:], 206, {'Content-Range': 'bytes 7-9/10'})]
        with tempfile.TemporaryDirectory() as td, patch('launcher.core.network.time.sleep'), patch('urllib.request.urlopen', side_effect=responses) as opened:
            dest = Path(td) / 'multiple.bin'
            self.net.download('https://example.com/payload', dest, len(data), hashlib.sha256(data).hexdigest())
            self.assertEqual([c.args[0].get_header('Range') for c in opened.call_args_list], [None, 'bytes=3-', 'bytes=7-'])
            self.assertEqual(dest.read_bytes(), data)

    def test_download_restarts_if_server_ignores_range(self):
        data = b'0123456789'
        with tempfile.TemporaryDirectory() as td, patch('launcher.core.network.time.sleep'), patch('urllib.request.urlopen', side_effect=[DownloadResponse(data[:4]), DownloadResponse(data)]) as opened:
            dest = Path(td) / 'restart.bin'
            self.net.download('https://example.com/payload', dest, len(data), hashlib.sha256(data).hexdigest())
            self.assertEqual(opened.call_args_list[1].args[0].get_header('Range'), 'bytes=4-')
            self.assertEqual(dest.read_bytes(), data)

    def test_download_rejects_bad_ranges_before_appending_and_restarts(self):
        data = b'0123456789'
        bad_headers = [{}, {'Content-Range': 'nonsense'},
                       {'Content-Range': 'bytes 3-9/10'},
                       {'Content-Range': 'bytes 4-9/11'},
                       {'Content-Range': 'bytes 4-10/10'},
                       {'Content-Range': 'bytes 4-3/10'},
                       {'Content-Range': 'bytes 4-9/10', 'Content-Length': '7'}]
        for headers in bad_headers:
            with self.subTest(headers=headers), tempfile.TemporaryDirectory() as td, patch('launcher.core.network.time.sleep'), patch('urllib.request.urlopen', side_effect=[DownloadResponse(data[:4]), DownloadResponse(b'BADBAD', 206, headers), DownloadResponse(data)]) as opened:
                dest = Path(td) / 'invalid_range.bin'
                self.net.download('https://example.com/payload', dest, len(data), hashlib.sha256(data).hexdigest())
                self.assertIsNone(opened.call_args_list[2].args[0].get_header('Range'))
                self.assertEqual(dest.read_bytes(), data)

    def test_download_short_eof_exhaustion_is_bounded_and_preserves_partial(self):
        data = b'0123456789'
        with tempfile.TemporaryDirectory() as td, patch('launcher.core.network.time.sleep'), patch('urllib.request.urlopen', side_effect=lambda *a, **kw: DownloadResponse(data[:4])) as opened:
            dest = Path(td) / 'bounded.bin'
            with self.assertRaises(InstallerError) as cm:
                self.net.download('https://example.com/payload', dest, len(data), max_retries=3)
            self.assertEqual(cm.exception.code, 'DOWNLOAD_FAILED')
            self.assertEqual(opened.call_count, 3)
            self.assertFalse(dest.exists())
            self.assertEqual(dest.with_name('bounded.bin.10.part').read_bytes(), data[:4])

    def test_download_next_user_retry_reuses_saved_prefix(self):
        data = b'0123456789'
        sha = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / 'retry.bin'
            with patch('urllib.request.urlopen', return_value=DownloadResponse(data[:4])):
                with self.assertRaises(InstallerError):
                    self.net.download('https://example.com/payload', dest, len(data), sha, max_retries=1)
            with patch('urllib.request.urlopen', return_value=DownloadResponse(data[4:], 206, {'Content-Range': 'bytes 4-9/10'})) as opened:
                self.net.download('https://example.com/payload', dest, len(data), sha)
            self.assertEqual(opened.call_args.args[0].get_header('Range'), 'bytes=4-')
            self.assertEqual(dest.read_bytes(), data)
            self.assertFalse(list(Path(td).glob('*.part')))

    def test_download_hash_mismatch_is_fatal_and_removes_partial(self):
        data = b'0123456789'
        sha = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as td, patch('urllib.request.urlopen', return_value=DownloadResponse(b'XXXXXXXXXX')) as opened:
            dest = Path(td) / 'hash.bin'
            with self.assertRaises(InstallerError) as cm:
                self.net.download('https://example.com/payload', dest, len(data), sha)
            self.assertEqual(cm.exception.code, 'HASH_MISMATCH')
            self.assertEqual(opened.call_count, 1)
            self.assertFalse(dest.exists())
            self.assertFalse(list(Path(td).glob('*.part')))

    def test_download_rejects_complete_smaller_http_object_before_reading(self):
        response = DownloadResponse(b'object', headers={'Content-Length': '26011641'})
        with tempfile.TemporaryDirectory() as td, patch('urllib.request.urlopen', return_value=response) as opened:
            with self.assertRaises(InstallerError) as cm:
                self.net.download('https://example.com/payload', Path(td) / 'data.arcx', 26210913)
            self.assertEqual(cm.exception.code, 'SIZE_MISMATCH')
            self.assertIn('26011641/26210913', str(cm.exception))
            self.assertEqual(response.bio.tell(), 0)
            self.assertEqual(opened.call_count, 1)

    def test_prepare_payload_rejects_stale_release_binding_before_download(self):
        data_sha = '3605edbb969e83e3ad104f1d1ebef35693223cf8a619aea4130ce212311aca3c'
        stale_sha = 'bc57df547138628e0b598a701591103d2ee5b716f44b5b1515bbcadc320c8bd0'
        release_url = 'https://example.com/releases/data_patched_vi.arcx'
        release = {'assets': [{'name': 'data_patched_vi.arcx', 'size': 26011641,
                              'digest': 'sha256:' + data_sha, 'browser_download_url': release_url}]}
        for size, sha, custom in [(26210913, stale_sha, False), (26011641, stale_sha, False),
                                  (26210913, data_sha, True)]:
            raw = {'version': 'v1.2.0', 'client_game_version': '2.0.1', 'resource_version': '*',
                   'files': {'Persistent_Store/Tables/data.arcx': {'source': 'data_patched_vi.arcx', 'size': size, 'sha256': sha}}}
            if custom:
                raw['files']['Persistent_Store/Tables/data.arcx']['url'] = release_url
            binding = {'source': 'explicit_custom_manifest' if custom else 'release_asset'}
            with self.subTest(size=size, sha=sha, custom=custom), tempfile.TemporaryDirectory() as td, patch.object(self.net, 'release', return_value=release), patch.object(self.net, '_manifest_for_release', return_value=(raw, binding)), patch.object(self.net, 'download') as downloaded:
                with self.assertRaises(InstallerError) as cm:
                    self.net.prepare_payload(Path(td), 'https://example.com/custom.json' if custom else None)
                self.assertEqual(cm.exception.code, 'RELEASE_ASSET_MISMATCH')
                downloaded.assert_not_called()

    def test_prepare_payload_preserves_independent_custom_file_url(self):
        data = b'custom valid data'
        custom_url = 'https://custom.example.com/data_patched_vi.arcx'
        raw = {'version': 'custom', 'client_game_version': '2.0.1', 'resource_version': '*',
               'files': {'Persistent_Store/Tables/data.arcx': {'source': 'data_patched_vi.arcx', 'size': len(data),
                         'sha256': hashlib.sha256(data).hexdigest(), 'url': custom_url}}}
        release = {'assets': [{'name': 'data_patched_vi.arcx', 'size': 999,
                              'digest': 'sha256:' + 'a' * 64, 'browser_download_url': 'https://release.example.com/data_patched_vi.arcx'}]}

        def download(url, dest, size, sha, *args):
            self.assertEqual(url, custom_url)
            self.assertEqual(size, len(data))
            Path(dest).write_bytes(data)
            return Path(dest)

        with tempfile.TemporaryDirectory() as td, patch.object(self.net, 'release', return_value=release), patch.object(self.net, '_manifest_for_release', return_value=(raw, {'source': 'explicit_custom_manifest'})), patch.object(self.net, 'download', side_effect=download):
            stage = self.net.prepare_payload(Path(td), 'https://custom.example.com/manifest.json')
            self.assertEqual((stage / 'data_patched_vi.arcx').read_bytes(), data)

    def test_prepare_payload_supports_legacy_null_files(self):
        data = b'verified legacy data'
        sha = hashlib.sha256(data).hexdigest()
        url = 'https://example.com/data_patched_vi.arcx'
        raw = {'version': '1.2.0', 'client_game_version': '2.0.1', 'resource_version': '*',
               'files': None, 'data_arcx': {'filename': 'data_patched_vi.arcx',
                                           'size_bytes': len(data), 'sha256': sha}}
        release = {'assets': [{'name': 'data_patched_vi.arcx', 'size': len(data),
                               'digest': 'sha256:' + sha, 'browser_download_url': url}]}
        def download(source, destination, size, digest, *args):
            self.assertEqual((source, size, digest), (url, len(data), sha))
            Path(destination).write_bytes(data)
            return Path(destination)
        with tempfile.TemporaryDirectory() as td, patch.object(self.net, 'release', return_value=release), \
             patch.object(self.net, '_manifest_for_release', return_value=(raw, {'source': 'release_asset'})), \
             patch.object(self.net, 'download', side_effect=download):
            stage = self.net.prepare_payload(Path(td))
            self.assertEqual((stage / 'data_patched_vi.arcx').read_bytes(), data)

    def test_download_oversize_is_fatal_and_preserves_existing_destination(self):
        with tempfile.TemporaryDirectory() as td, patch('urllib.request.urlopen', return_value=DownloadResponse(b'01234567890')) as opened:
            dest = Path(td) / 'oversize.bin'
            dest.write_bytes(b'previous')
            with self.assertRaises(InstallerError) as cm:
                self.net.download('https://example.com/payload', dest, 10)
            self.assertEqual(cm.exception.code, 'SIZE_MISMATCH')
            self.assertEqual(opened.call_count, 1)
            self.assertEqual(dest.read_bytes(), b'previous')
            self.assertFalse(list(Path(td).glob('*.part')))


    def test_payload_stage_cleaned_after_install_success_and_failure(self):
        data=b'payload'; digest=hashlib.sha256(data).hexdigest()
        raw={'version':'1.2.0','client_game_version':'2.0.1','resource_version':'*',
             'files':{'Persistent_Store/Tables/data.arcx':{'source':'data.arcx','size':len(data),'sha256':digest,'url':'https://example.test/data'}}}
        def download(url,dest,*args):
            Path(dest).write_bytes(data)
            return Path(dest)
        with tempfile.TemporaryDirectory() as td, patch.object(self.net,'release',return_value={'assets':[]}), \
             patch.object(self.net,'_manifest_for_release',return_value=(raw,{'source':'release_asset'})), \
             patch.object(self.net,'download',side_effect=download):
            with self.net.payload_for_install(td) as first:
                self.assertTrue((first/'data.arcx').exists())
                with self.net.payload_for_install(td) as second:
                    self.assertNotEqual(first,second)
                    self.assertTrue(first.exists())
                self.assertFalse(second.exists())
                self.assertTrue(first.exists())
            self.assertFalse(first.exists())
            with self.assertRaisesRegex(RuntimeError,'install failed'):
                with self.net.payload_for_install(td) as failed:
                    self.assertTrue(failed.exists())
                    raise RuntimeError('install failed')
            self.assertFalse(failed.exists())
            self.assertTrue((Path(td)/'shared_downloads').exists())

    def test_payload_prepare_failure_cleans_only_partial_stage(self):
        data=b'payload'; digest=hashlib.sha256(data).hexdigest()
        raw={'version':'1.2.0','client_game_version':'2.0.1','resource_version':'*',
             'files':{'Persistent_Store/Tables/data.arcx':{'source':'data.arcx','size':len(data),'sha256':digest,'url':'https://example.test/data'}}}
        with tempfile.TemporaryDirectory() as td, patch.object(self.net,'release',return_value={'assets':[]}), \
             patch.object(self.net,'_manifest_for_release',return_value=(raw,{'source':'release_asset'})), \
             patch.object(self.net,'download',side_effect=RuntimeError('network failed')):
            other=Path(td)/('payload_'+'a'*32);other.mkdir();(other/'sentinel').write_text('other')
            with self.assertRaisesRegex(RuntimeError,'network failed'):
                self.net.prepare_payload(td)
            self.assertEqual([p.name for p in Path(td).glob('payload_*')],[other.name])
            self.assertTrue((other/'sentinel').exists())

    def test_user_owned_payload_never_deleted(self):
        with tempfile.TemporaryDirectory() as td:
            local=Path(td)/('payload_'+'a'*32);local.mkdir(); (local/'user-file').write_text('keep')
            with self.assertRaisesRegex(RuntimeError,'install failed'):
                with self.net.payload_for_install(td,local) as payload:
                    self.assertEqual(payload,local)
                    raise RuntimeError('install failed')
            self.assertTrue((local/'user-file').exists())

    def test_cleanup_rejects_paths_outside_cache(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'cache';root.mkdir();outside=Path(td)/('payload_'+'a'*32);outside.mkdir()
            (outside/'sentinel').write_text('keep')
            self.net._cleanup_owned_stage(root,outside)
            self.assertTrue((outside/'sentinel').exists())


if __name__ == "__main__":
    unittest.main()
