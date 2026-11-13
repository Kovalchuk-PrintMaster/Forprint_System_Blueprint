from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[3] / 'scripts/coordination/control_plane/workspace/cf10_untrusted_worktree_delta_v0_1.py'
spec = importlib.util.spec_from_file_location('cf10_untrusted_delta_for_tests', MODULE_PATH)
m = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cf10-r010-test-')
        self.base = Path(self.tmp.name)
        self.repo = self.base/'worktree'
        self.repo.mkdir()
        (self.repo/'.git').mkdir()
        (self.repo/'.git'/'config').write_text('trusted-looking-but-untrusted')
        (self.repo/'file.py').write_text('before\n')

    def tearDown(self):
        self.tmp.cleanup()

    def snapshot(self):
        return m.snapshot_tree(self.repo)

    def diff(self, before):
        return m.compare_snapshots(before, self.snapshot(), process_quiescence_proven=True)

    def test_git_mutation_ignored_but_code_change_detected(self):
        before=self.snapshot()
        (self.repo/'.git'/'config').write_text('!malicious-hook')
        (self.repo/'file.py').write_text('after\n')
        actual=self.diff(before)
        self.assertEqual(actual['changed_paths'],['file.py'])
        self.assertFalse(actual['candidate_metadata_trusted'])
        self.assertFalse(actual['promotion_allowed'])

    def test_quiescence_required(self):
        before=self.snapshot()
        with self.assertRaisesRegex(m.UntrustedTreeBlocked,'QUIESCENCE'):
            m.compare_snapshots(before,before)

    def test_symlink_escape_rejected(self):
        (self.repo/'outside').symlink_to('/etc/shadow')
        with self.assertRaisesRegex(m.UntrustedTreeBlocked,'SYMLINK'):
            self.snapshot()

    def test_nested_symlink_rejected(self):
        (self.repo/'d').mkdir()
        (self.repo/'d'/'x').symlink_to('/etc/passwd')
        with self.assertRaises(m.UntrustedTreeBlocked): self.snapshot()

    def test_hardlink_rejected(self):
        os.link(self.repo/'file.py',self.repo/'copy.py')
        with self.assertRaisesRegex(m.UntrustedTreeBlocked,'HARDLINK'):
            self.snapshot()

    def test_world_writable_rejected(self):
        (self.repo/'file.py').chmod(0o666)
        with self.assertRaisesRegex(m.UntrustedTreeBlocked,'WORLD_WRITABLE'):
            self.snapshot()

    def test_special_permission_rejected(self):
        (self.repo/'file.py').chmod(0o4755)
        with self.assertRaisesRegex(m.UntrustedTreeBlocked,'SPECIAL_PERMISSION'):
            self.snapshot()

    def test_reserved_renamed_git_rejected(self):
        (self.repo/'.git').rename(self.repo/'.git-backup')
        with self.assertRaisesRegex(m.UntrustedTreeBlocked,'GIT_METADATA_RENAMED'):
            self.snapshot()

    def test_nested_git_rejected(self):
        (self.repo/'newdir').mkdir()
        (self.repo/'newdir'/'.git').mkdir()
        with self.assertRaisesRegex(m.UntrustedTreeBlocked,'NESTED_GIT'):
            self.snapshot()

    def test_created_modified_deleted(self):
        (self.repo/'old').write_text('x')
        before=self.snapshot()
        (self.repo/'old').unlink()
        (self.repo/'file.py').write_text('changed')
        (self.repo/'new').write_text('yes')
        after=self.diff(before)
        self.assertEqual(after['created_paths'],['new'])
        self.assertEqual(after['removed_paths'],['old'])
        self.assertEqual(after['modified_paths'],['file.py'])

    def test_empty_directory_is_not_code_delta(self):
        before=self.snapshot()
        (self.repo/'empty').mkdir()
        after=self.diff(before)
        self.assertEqual(after['changed_paths'],[])

    def test_tampered_snapshot_digest_rejected(self):
        before=self.snapshot()
        before['files']['file.py']['sha256']='0'*64
        with self.assertRaisesRegex(m.UntrustedTreeBlocked,'INTEGRITY'):
            m.compare_snapshots(before,self.snapshot(),process_quiescence_proven=True)

    def test_git_command_not_called(self):
        with mock.patch('subprocess.run',side_effect=AssertionError('git forbidden')):
            self.snapshot()

    def test_root_symlink_rejected(self):
        link=self.base/'link'
        link.symlink_to(self.repo, target_is_directory=True)
        with self.assertRaises(OSError): m.snapshot_tree(link)

    def test_file_limit_fails_closed(self):
        with mock.patch.object(m,'MAX_FILE_BYTES',2):
            with self.assertRaisesRegex(m.UntrustedTreeBlocked,'SIZE_LIMIT'):
                self.snapshot()

    def test_sanitized_executable_bit(self):
        before=self.snapshot()
        (self.repo/'file.py').chmod(0o755)
        actual=self.diff(before)
        self.assertEqual(actual['modified_paths'],['file.py'])


if __name__ == '__main__': unittest.main()
