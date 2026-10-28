"""Pinned historical Git-object recovery: synthetic local remotes; no network."""
from __future__ import annotations

import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.coordination.control_plane import cf10_stable_release_roots_v0_1 as g2


def git(root, *args, rc=0):
    p = subprocess.run(['git', *args], cwd=root, capture_output=True, text=True)
    if p.returncode != rc:
        raise AssertionError(f'git {args}: got rc={p.returncode}, wanted={rc}: {p.stderr}')
    return p.stdout.strip()


class PinRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cf10_g2a_recovery_')
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.seed = base / 'seed'; self.seed.mkdir()
        self.remote = base / 'origin.git'; git(base, 'init', '--bare', '-q', str(self.remote))
        git(self.seed, 'init', '-q')
        git(self.seed, 'checkout', '-q', '-b', g2.BRANCH)
        git(self.seed, 'config', 'user.name', 'Synthetic')
        git(self.seed, 'config', 'user.email', 'synthetic@example.invalid')
        (self.seed/'Makefile').write_text(g2.Q1_MARKER+'\nQUARANTINED_NEEDS_INDEPENDENT_REBIND\ncf10-make-surface-policy-check:\n\t@true\n')
        git(self.seed, 'add', 'Makefile'); git(self.seed, 'commit','-qm','base')
        pins = {}
        for kind in ('gate', 'writer'):
            rel = f'scripts/coordination/synthetic_{kind}.py'
            p = self.seed/rel; p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(f'{kind} source\n')
            git(self.seed, 'add', rel); git(self.seed, 'commit', '-qm',kind)
            pins[kind]={'head':git(self.seed,'rev-parse','HEAD'),
                        'ref':f'refs/heads/cf10/test-{kind}', 'source':rel,
                        'git_blob_oid':g2.blob_oid(p.read_bytes())}
        (self.seed/'VERSION').write_text('new canonical tip\n')
        git(self.seed, 'add', 'VERSION'); git(self.seed, 'commit', '-qm', 'main tip')
        self.head=git(self.seed,'rev-parse','HEAD')
        git(self.seed,'remote','add','origin',str(self.remote))
        git(self.seed,'push','-q','origin',f'HEAD:refs/heads/{g2.BRANCH}')
        for kind, pin in pins.items():
            git(self.seed, 'push', '-q', 'origin', f"{pin['head']}:{pin['ref']}")
        self.root=base/'canonical'
        git(base, 'clone','-q','--depth','1','--single-branch','--branch',g2.BRANCH,
            self.remote.as_uri(),str(self.root))
        self.base=base/'stable'
        self.pinpatch=patch.object(g2,'RELEASES',pins);self.pinpatch.start();self.addCleanup(self.pinpatch.stop)
        self.originpatch=patch.object(g2,'ORIGIN',self.remote.as_uri());self.originpatch.start();self.addCleanup(self.originpatch.stop)
        self.basepatch=patch.object(g2,'BASE',self.base);self.basepatch.start();self.addCleanup(self.basepatch.stop)

    def test_reports_precise_missing_release_before_recovery(self):
        with self.assertRaisesRegex(g2.ReviewBlocked, 'PINNED_RELEASE_OBJECT_MISSING_OR_INVALID'):
            g2.root_identity(self.root,self.head,network=True)
        view=g2.root_identity(self.root,self.head,network=True,allow_missing_local_pins=True)
        self.assertFalse(view['pinned_git_objects_verified'])
        self.assertEqual(view['pinned_git_objects_missing'],['gate','writer'])

    def test_operator_recovery_is_exact_and_idempotent(self):
        before=git(self.root,'status','--porcelain=v1')
        added=g2.recover_pinned_source_objects(self.root,self.head)
        self.assertEqual(added,['gate','writer'])
        self.assertEqual(git(self.root,'rev-parse','HEAD'),self.head)
        self.assertEqual(git(self.root,'status','--porcelain=v1'),before)
        self.assertTrue(g2.root_identity(self.root,self.head,network=True)['pinned_git_objects_verified'])
        self.assertEqual(g2.recover_pinned_source_objects(self.root,self.head),[])

    def test_ref_tampering_fails_without_replacing(self):
        git(self.root,'update-ref',g2.pinned_ref('gate'),self.head)
        with self.assertRaisesRegex(g2.ReviewBlocked,'PINNED_LOCAL_REF_DRIFT:gate'):
            g2.recover_pinned_source_objects(self.root,self.head)
        self.assertEqual(git(self.root,'rev-parse',g2.pinned_ref('gate')),self.head)

    def test_remote_ref_drift_fails_before_import(self):
        git(self.seed,'push','-q','--force','origin',f'{self.head}:{g2.RELEASES["gate"]["ref"]}')
        with self.assertRaisesRegex(g2.ReviewBlocked,'RELEASE_REMOTE_REF_DRIFT:gate'):
            g2.recover_pinned_source_objects(self.root,self.head)
        self.assertEqual(git(self.root,'rev-parse','--verify','--quiet',g2.pinned_ref('gate'),rc=1),'')

    def test_clone_recovery_requires_explicit_provision_and_no_authority(self):
        # The real CLI already requires --confirm-provision; synthetic mock of base-parent DAC.
        with patch.object(g2,'ensure_base_dirs',side_effect=lambda b:b.mkdir(parents=True,exist_ok=True)), \
             patch.object(g2.os,'geteuid',return_value=0):
            result=g2.provision(self.root,self.head,confirm=True,hostname='s01',base=self.base)
        self.assertEqual(result['state'],'STABLE_RELEASES_READY_FOR_INDEPENDENT_REBIND_NON_AUTHORIZING')
        self.assertEqual(result['operator_imported_pinned_sources'],['gate','writer'])
        self.assertEqual(result['operator_provisioned_release_kinds'],['gate','writer'])
        self.assertFalse(result['authority_granted'])
        self.assertFalse(result['root_signed_activation_renewed'])
        self.assertFalse(result['make_launch_gate_unquarantined'])
        self.assertEqual(git(self.root,'rev-parse','HEAD'),self.head)

    def test_no_hidden_import_in_inspect(self):
        doc=g2.review(self.root,self.head,network=True,base=self.base)
        self.assertEqual(doc['state'],'BLOCKED_NON_AUTHORIZING')
        self.assertFalse((self.root/'.git/refs/forprint').exists())

if __name__=='__main__':unittest.main()
