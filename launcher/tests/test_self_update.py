"""Isolated tests for safe self-update and legacy jobs; no real executable changed."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from launcher.core import self_update as updater
from launcher.core.safety import InstallerError, sha256_file


class SelfUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='stella_update_fixture_')
        self.root = Path(self.temp.name)
        self.source = self.root / 'new.exe'
        self.target = self.root / 'installed.exe'
        self.source.write_bytes(b'new-launcher')
        self.target.write_bytes(b'old-launcher')
        self.job = self.root / 'job.json'
        self.old_hash = sha256_file(self.target)
        self.new_hash = sha256_file(self.source)
        self.data = {'target':str(self.target), 'source':str(self.source), 'sha256':self.new_hash,
                     'preimage_sha256':self.old_hash, 'parent_pid':1234,
                     'parent_pids':[1234, 8888], 'timeout':5}
        self.write_job()

    def tearDown(self): self.temp.cleanup()
    def write_job(self): self.job.write_text(json.dumps(self.data), encoding='utf8')
    def result(self): return json.loads(self.job.with_suffix('.result.json').read_text(encoding='utf8'))

    def test_legacy_job_waits_only_parent_and_never_kills(self):
        class Proc:
            pid = 4321
            def poll(self): return None
        with patch.object(updater, '_wait_parent') as wait, patch.object(updater.subprocess, 'Popen', return_value=Proc()), \
             patch.object(updater.subprocess, 'run', side_effect=AssertionError('must not kill')), \
             patch.object(updater.time, 'sleep'):
            updater.apply_job(self.job)
        self.assertEqual(wait.call_args.args[0], 1234)
        self.assertEqual(self.target.read_bytes(), b'new-launcher')
        self.assertEqual(self.result()['status'], 'started')
        self.assertEqual(Path(self.result()['backup']).read_bytes(), b'old-launcher')

    def test_parent_timeout_keeps_target_and_reports(self):
        with patch.object(updater, '_wait_parent', side_effect=InstallerError('not closed','UPDATE_TIMEOUT')):
            with self.assertRaises(InstallerError) as e: updater.apply_job(self.job)
        self.assertEqual(e.exception.code, 'UPDATE_TIMEOUT')
        self.assertEqual(self.target.read_bytes(), b'old-launcher')
        self.assertEqual(self.result()['code'], 'UPDATE_TIMEOUT')

    def test_target_changed_while_waiting_is_not_overwritten(self):
        def change(*_): self.target.write_bytes(b'external edit')
        with patch.object(updater, '_wait_parent', side_effect=change):
            with self.assertRaises(InstallerError) as e: updater.apply_job(self.job)
        self.assertEqual(e.exception.code, 'PREIMAGE_CONFLICT')
        self.assertEqual(self.target.read_bytes(), b'external edit')

    def test_locked_target_times_out_without_renaming(self):
        replace = os.replace
        def locked(src, dst):
            if Path(src).name.startswith('.launcher_update_'): raise PermissionError('in use')
            return replace(src,dst)
        with patch.object(updater, '_wait_parent'), patch.object(updater.os, 'replace', side_effect=locked), \
             patch.object(updater.time, 'monotonic', side_effect=[0, 6]):
            with self.assertRaises(InstallerError) as e: updater.apply_job(self.job)
        self.assertEqual(e.exception.code, 'UPDATE_TIMEOUT')
        self.assertEqual(self.target.read_bytes(), b'old-launcher')
        self.assertEqual(Path(self.result()['backup']).read_bytes(), b'old-launcher')
        self.assertFalse(list(self.root.glob('*.old_*')))

    def test_failed_launch_rolls_back_atomically(self):
        with patch.object(updater, '_wait_parent'), patch.object(updater.subprocess, 'Popen', side_effect=OSError('cannot run')):
            with self.assertRaises(InstallerError) as e: updater.apply_job(self.job)
        self.assertEqual(e.exception.code, 'RELAUNCH_FAILED')
        self.assertEqual(self.target.read_bytes(), b'old-launcher')
        self.assertEqual(self.result()['status'], 'error')

    def test_external_change_after_replace_preserves_both_and_reports_recovery(self):
        def changed(*args, **kwargs):
            self.target.write_bytes(b'external edit')
            raise OSError('cannot run')
        with patch.object(updater, '_wait_parent'), patch.object(updater.subprocess, 'Popen', side_effect=changed):
            with self.assertRaises(InstallerError) as e: updater.apply_job(self.job)
        self.assertEqual(e.exception.code, 'UPDATE_RECOVERY_REQUIRED')
        self.assertEqual(self.target.read_bytes(), b'external edit')
        self.assertEqual(Path(self.result()['backup']).read_bytes(), b'old-launcher')
        self.assertEqual(self.result()['status'], 'recovery_required')

    def test_backup_is_not_deleted_by_cleanup(self):
        backup = self.root / 'x.exe.preupdate.123'
        backup.write_bytes(b'backup')
        updater.cleanup_update_artifacts(self.root)
        self.assertTrue(backup.exists())

    def test_unfrozen_schedule_does_not_mutate_executables(self):
        with patch.object(sys, 'frozen', False, create=True):
            with self.assertRaises(InstallerError) as e: updater.schedule_update(self.source, self.new_hash, self.root)
        self.assertEqual(e.exception.code, 'UPDATE_UNSUPPORTED')
        self.assertEqual(self.target.read_bytes(), b'old-launcher')

    @unittest.skipUnless(os.name == 'nt', 'Windows process handles')
    def test_wait_parent_only_waits_real_process(self):
        proc = subprocess.Popen([sys.executable, '-c', 'pass'])
        try:
            updater._wait_parent(proc.pid, updater.time.monotonic()+5)
            self.assertEqual(proc.wait(timeout=5), 0)
        finally:
            proc.wait(timeout=5)


if __name__ == '__main__': unittest.main()
