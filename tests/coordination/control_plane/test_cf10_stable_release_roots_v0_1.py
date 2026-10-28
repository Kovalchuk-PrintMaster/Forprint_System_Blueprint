"""Offline G2a synthetic provenance and fail-closed tests; no external writes."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from scripts.coordination.control_plane import cf10_stable_release_roots_v0_1 as g2


def git(path, *args):
    p = subprocess.run(['git', *args], cwd=path, capture_output=True, check=True)
    return p.stdout.decode().strip()


class G2aTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cf10_g2a_synth_')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'canonical'
        self.root.mkdir()
        git(self.root, 'init', '-q')
        git(self.root, 'checkout', '-q', '-b', g2.BRANCH)
        git(self.root, 'config', 'user.name', 'G2 Synthetic')
        git(self.root, 'config', 'user.email', 'synth@example.invalid')
        (self.root/'Makefile').write_text(g2.Q1_MARKER + '\n'
                 'QUARANTINED_NEEDS_INDEPENDENT_REBIND\ncf10-make-surface-policy-check:\n\t@true\n')
        (self.root/'generated').mkdir()
        git(self.root, 'add', 'Makefile')
        git(self.root, 'commit', '-qm', 'base')
        self.pins = {}
        for kind in ('gate', 'writer'):
            f = self.root / ('scripts/' + kind + '.py')
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes((kind + ' source\n').encode())
            git(self.root, 'add', str(f.relative_to(self.root)))
            git(self.root, 'commit', '-qm', kind)
            self.pins[kind] = {
                'head': git(self.root, 'rev-parse', 'HEAD'),
                'source': str(f.relative_to(self.root)),
                'ref': 'refs/heads/cf10/test-' + kind,
                'git_blob_oid': g2.blob_oid(f.read_bytes()),
            }
        self.head = git(self.root, 'rev-parse', 'HEAD')
        git(self.root, 'remote', 'add', 'origin', g2.ORIGIN)
        self.pinpatch = patch.object(g2, 'RELEASES', self.pins)
        self.pinpatch.start()
        self.addCleanup(self.pinpatch.stop)
        self.base = Path(self.tmp.name) / 'release' / 'cf10'

    def test_blob_oid_is_git_compatible(self):
        self.assertEqual(g2.blob_oid(b'hello\n'), hashlib.sha1(b'blob 6\x00hello\n').hexdigest())

    def test_q1_gate_is_required(self):
        txt = (self.root/'Makefile').read_text()
        (self.root/'Makefile').write_text(txt.replace('QUARANTINED_NEEDS_INDEPENDENT_REBIND','REMOVED'))
        git(self.root, 'add', 'Makefile')
        git(self.root, 'commit', '-qm', 'synthetic bypass attempt')
        self.head = git(self.root, 'rev-parse', 'HEAD')
        with self.assertRaisesRegex(g2.ReviewBlocked, 'Q1_QUARANTINE_NOT_INSTALLED'):
            g2.root_identity(self.root, self.head, network=False)

    def test_canonical_frozen_head(self):
        with self.assertRaisesRegex(g2.ReviewBlocked, 'CANONICAL_HEAD_DRIFT'):
            g2.root_identity(self.root, 'a'*40, network=False)

    def test_canonical_valid_local_release_objects(self):
        self.assertEqual(g2.root_identity(self.root, self.head, network=False)['canonical_head'], self.head)

    def test_not_yet_provisioned_is_not_pass(self):
        a = g2.review(self.root,self.head,network=False,base=self.base)
        self.assertEqual(a['state'],'RELEASE_ROOTS_NOT_PROVISIONED_NON_AUTHORIZING')
        self.assertEqual(a['checks']['gate']['status'],'MISSING')
        self.assertFalse(a['authority_granted'])

    def test_unapproved_path_blocked(self):
        a = g2.inspect_release(self.base/'other', 'gate', base=self.base)
        self.assertEqual(a['status'], 'BLOCKED')

    def test_symlink_release_blocked(self):
        target = g2.stable_path('gate',self.base)
        target.parent.mkdir(parents=True)
        target.symlink_to(self.root, target_is_directory=True)
        self.assertEqual(g2.inspect_release(target,'gate',base=self.base)['status'],'BLOCKED')

    def test_wrong_commit_release_fails_closed(self):
        target = g2.stable_path('gate',self.base)
        target.parent.mkdir(parents=True)
        subprocess.run(['git','clone','-q','--no-hardlinks',str(self.root),str(target)],check=True)
        git(target,'remote','set-url','origin',g2.ORIGIN)
        fake = types.SimpleNamespace(st_uid=0, st_mode=0o40750)
        real = Path.stat
        def patched(path, *args, **kwargs):
            if path == target: return fake
            return real(path,*args,**kwargs)
        with patch.object(Path, 'stat', patched):
            x=g2.inspect_release(target,'gate',base=self.base)
        self.assertEqual(x['status'],'BLOCKED')
        self.assertIn('HEAD_DRIFT', x['reason'])

    def test_exact_release_root_passes_when_root_owned(self):
        target = g2.stable_path('gate',self.base)
        target.parent.mkdir(parents=True)
        subprocess.run(['git','clone','-q','--no-hardlinks',str(self.root),str(target)],check=True)
        git(target,'remote','set-url','origin',g2.ORIGIN)
        git(target,'checkout','-q','--detach',self.pins['gate']['head'])
        fake = types.SimpleNamespace(st_uid=0, st_mode=0o40750)
        real = Path.stat
        def patched(path, *args, **kwargs):
            if path == target: return fake
            return real(path,*args,**kwargs)
        with patch.object(Path, 'stat', patched):
            x=g2.inspect_release(target,'gate',base=self.base)
        self.assertEqual(x['status'],'PASS', x)

    def test_provision_requires_explicit_operator_flag(self):
        with self.assertRaisesRegex(g2.ReviewBlocked,'EXPLICIT_RELEASE_PROVISION_CONFIRMATION_REQUIRED'):
            g2.provision(self.root,self.head,confirm=False,hostname='s01')

    def test_provision_rejects_wrong_host(self):
        with patch.object(g2.os,'geteuid',return_value=0):
            with self.assertRaisesRegex(g2.ReviewBlocked,'ROOT_OPERATOR_ON_S01_REQUIRED'):
                g2.provision(self.root,self.head,confirm=True,hostname='not-s01')

    def test_approved_provision_base_is_fixed(self):
        with self.assertRaisesRegex(g2.ReviewBlocked,'ROOT_PROVISION_BASE_NOT_EXACTLY_APPROVED'):
            g2.ensure_base_dirs(self.base)

    def test_report_only_generated(self):
        data = g2.review(self.root,self.head,network=False,base=self.base)
        z=g2.report_zip(self.root,data)
        with ZipFile(z) as f:
            self.assertEqual(sorted(f.namelist()), ['SHA256SUMS','report.json','summary.txt'])
            self.assertFalse(f.testzip())
            self.assertIn('AUTHORITY_GRANTED=false',f.read('summary.txt').decode())
        self.assertEqual(z.stat().st_mode & 0o777,0o600)

    def test_report_generated_symlink_rejected(self):
        (self.root/'generated').rmdir()
        (self.root/'generated').symlink_to(self.root)
        with self.assertRaisesRegex(g2.ReviewBlocked,'GENERATED_REPORT_ROOT_UNAVAILABLE'):
            g2.report_zip(self.root,g2.review(self.root,self.head,network=False,base=self.base))

    def test_source_never_calls_worker_or_signer(self):
        source=Path(g2.__file__).read_text()
        for forbidden in ('subprocess.Popen(','.launch_cycle(', 'signing_key', 'signed_decision_v0_1.json'):
            self.assertNotIn(forbidden,source)

if __name__ == '__main__': unittest.main()
