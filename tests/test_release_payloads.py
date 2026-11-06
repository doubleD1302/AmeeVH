import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.verify_release_payloads import verify_release_payloads


class ReleasePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dist = Path(self.temp.name)
        data = b'verified game table'
        digest = hashlib.sha256(data).hexdigest()
        (self.dist / 'data_patched_vi.arcx').write_bytes(data)
        self.manifest = {'files': {'Persistent_Store/Tables/data.arcx': {
            'source': 'data_patched_vi.arcx', 'size': len(data), 'sha256': digest}},
            'data_arcx': {'path': 'Persistent_Store/Tables/data.arcx',
                          'size_bytes': len(data), 'sha256': digest}}
        self.save()

    def save(self):
        (self.dist / 'patch_manifest.json').write_text(json.dumps(self.manifest), encoding='utf8')
        names = [p.name for p in self.dist.iterdir() if p.name != 'SHA256SUMS.txt']
        (self.dist / 'SHA256SUMS.txt').write_text(''.join(
            hashlib.sha256((self.dist / name).read_bytes()).hexdigest() + '  ' + name + '\n'
            for name in names), encoding='utf8')

    def verify(self):
        return verify_release_payloads(self.dist, ('patch_manifest.json',))

    def test_consistent_payload_passes(self):
        self.assertEqual(self.verify()['files_verified'], 1)

    def test_stale_files_entry_fails_despite_correct_alias_and_sums(self):
        self.manifest['files']['Persistent_Store/Tables/data.arcx']['size'] += 199272
        self.save()
        with self.assertRaisesRegex(ValueError, 'metadata mismatch'):
            self.verify()

    def test_same_size_wrong_hash_fails(self):
        self.manifest['files']['Persistent_Store/Tables/data.arcx']['sha256'] = '0' * 64
        self.save()
        with self.assertRaisesRegex(ValueError, 'metadata mismatch'):
            self.verify()

    def test_inconsistent_alias_fails(self):
        self.manifest['data_arcx']['sha256'] = '0' * 64
        self.save()
        with self.assertRaisesRegex(ValueError, 'data_arcx'):
            self.verify()

    def test_stale_checksum_fails(self):
        (self.dist / 'data_patched_vi.arcx').write_bytes(b'changed')
        raw = (self.dist / 'data_patched_vi.arcx').read_bytes()
        entry = self.manifest['files']['Persistent_Store/Tables/data.arcx']
        entry.update(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        self.manifest.pop('data_arcx')
        (self.dist / 'patch_manifest.json').write_text(json.dumps(self.manifest), encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'SHA256SUMS mismatch'):
            self.verify()

    def test_android_list_and_bundle_member_verified(self):
        payload = b'android bundle bytes'
        path = 'Persistent_Store/AssetBundles/icon.en.unity3d'
        with zipfile.ZipFile(self.dist / 'bundles.zip', 'w') as archive:
            archive.writestr(path, payload)
        archive_data = (self.dist / 'bundles.zip').read_bytes()
        self.manifest['files'] = [dict(entry, path=path) for path, entry in self.manifest['files'].items()]
        self.manifest['files'].append({'path': path, 'size': len(payload),
                                       'sha256': hashlib.sha256(payload).hexdigest()})
        self.manifest['package_zip'] = {'filename': 'bundles.zip', 'size': len(archive_data),
                                        'sha256': hashlib.sha256(archive_data).hexdigest()}
        self.manifest['total_size'] = sum(f['size'] for f in self.manifest['files'])
        self.save()
        self.assertEqual(self.verify()['files_verified'], 2)
        self.manifest['total_size'] += 1
        self.save()
        with self.assertRaisesRegex(ValueError, 'total_size'):
            self.verify()


if __name__ == '__main__':
    unittest.main()
