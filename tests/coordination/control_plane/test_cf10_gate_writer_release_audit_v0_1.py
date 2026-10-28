"""Offline, synthetic and non-authorizing release-object audit tests."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

HERE = Path(__file__).resolve()
# Supports original project layout and package-local offline fixture.
ROOT = HERE.parents[3] if HERE.parents[2].name == 'tests' else None
try:
    from scripts.coordination.control_plane import cf10_gate_writer_release_audit_v0_1 as mod
except ModuleNotFoundError:
    import sys
    candidates = [HERE.parents[i] / 'scripts/coordination/control_plane/cf10_gate_writer_release_audit_v0_1.py'
                  for i in range(2,6)]
    target = next((p for p in candidates if p.is_file()), None)
    if target is None: raise
    spec=importlib.util.spec_from_file_location('release_audit',target)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


def cli(path,*args):
    p=subprocess.run(['git',*args],cwd=path,capture_output=True,text=True,check=False)
    if p.returncode:raise AssertionError(p.stderr + repr(args))
    return p.stdout.strip()

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='cf10_release_test_')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'repo';self.root.mkdir()
        cli(self.root,'init','-q')
        cli(self.root,'checkout','-q','-b',mod.BRANCH)
        cli(self.root,'config','user.name','Synthetic')
        cli(self.root,'config','user.email','synthetic@example.invalid')
        (self.root/'tmp').mkdir(); (self.root/'generated').mkdir()
        (self.root/'Makefile').write_text('ALL=ready\n')
        (self.root/'README.md').write_text('synthetic\n')
        cli(self.root,'add','Makefile','README.md');cli(self.root,'commit','-qm','base')
        self.releases={}
        for kind,file in [('gate','scripts/coordination/execution_attempt_writer_coverage_v0_1.py'),
                          ('writer','scripts/coordination/execution_attempt_writer_activation_v0_1.py')]:
            p=self.root/file;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('# synthetic source '+kind+'\n')
            cli(self.root,'add',file);cli(self.root,'commit','-qm',kind)
            commit=cli(self.root,'rev-parse','HEAD')
            self.releases[kind]={'commit':commit,'ref':'refs/heads/test-'+kind,
                                'module_path':file,
                                'blob_oid':mod.blob_oid(p.read_bytes())}
        self.head=cli(self.root,'rev-parse','HEAD')
        cli(self.root,'remote','add','origin','synthetic-remote')
        self.pin=patch.object(mod,'RELEASES',self.releases);self.pin.start();self.addCleanup(self.pin.stop)
        self.remote=patch.object(mod,'REPO','synthetic-remote');self.remote.start();self.addCleanup(self.remote.stop)

    def test_verified_git_blobs_local(self):
        rows=mod.audit(self.root,self.head,probe_remote=False)
        d={r['id']:r['state'] for r in rows}
        self.assertEqual(d['gate_git_object'],'PASS')
        self.assertEqual(d['writer_git_object'],'PASS')
        self.assertEqual(d['gate_remote_ref'],'REVIEW')
        self.assertEqual(d['writer_remote_ref'],'REVIEW')
        self.assertEqual(d['make_launch_wiring'],'REVIEW')
        self.assertEqual(d['independent_operator_rebind'],'REVIEW')
        self.assertEqual(mod.summary(rows)[0],'REVIEW_REQUIRED_NON_AUTHORIZING')

    def test_missing_local_release_fails_closed(self):
        changed=dict(self.releases['gate'],commit='0'*40)
        self.releases['gate']=changed
        rows=mod.audit(self.root,self.head,probe_remote=False)
        self.assertEqual(next(r for r in rows if r['id']=='gate_git_object')['state'],'BLOCKED')

    def test_blob_drift_fails_closed(self):
        self.releases['writer']=dict(self.releases['writer'],blob_oid='f'*40)
        rows=mod.audit(self.root,self.head,probe_remote=False)
        self.assertEqual(next(r for r in rows if r['id']=='writer_git_object')['state'],'BLOCKED')

    def test_head_drift_fails_closed(self):
        rows=mod.audit(self.root,'0'*40,probe_remote=False)
        self.assertEqual(next(r for r in rows if r['id']=='canonical_identity')['state'],'BLOCKED')

    def test_dirty_index_fails_closed(self):
        (self.root/'README.md').write_text('tracked-change\n')
        cli(self.root,'add','README.md')
        rows=mod.audit(self.root,self.head,probe_remote=False)
        self.assertEqual(next(r for r in rows if r['id']=='canonical_identity')['state'],'BLOCKED')

    def test_no_tmp_release_roots(self):
        x=mod.stable_root_check(self.root/'tmp'/'release',self.releases['gate'])
        self.assertEqual(x['state'],'BLOCKED')
        self.assertIn('INSIDE_TMP',x['detail'])

    def test_missing_stable_roots_are_unknown_not_pass(self):
        x=mod.stable_root_check(None,self.releases['gate'])
        self.assertEqual(x['state'],'NOT_YET_TESTABLE')

    def test_stable_release_under_system_tmp_not_misrepresented_as_permanent(self):
        # Synthetic Git fixtures live under OS /tmp; a permanent release must not.
        x=mod.stable_root_check(self.root,self.releases['writer'])
        self.assertEqual(x['state'],'BLOCKED')
        self.assertIn('INSIDE_TMP',x['detail'])

    def test_save_reports_only_under_generated_area(self):
        report={'status':'REVIEW_REQUIRED_NON_AUTHORIZING','checks':[],
                'authority':{'granted':False}}
        z=mod.save(self.root,Path('generated/proposals'),report)
        self.assertTrue(z.is_file())
        with ZipFile(z) as f:
            self.assertEqual(sorted(f.namelist()),['SHA256SUMS','report.json','summary.txt'])
            self.assertIn('AUTHORITY_GRANTED=false',f.read('summary.txt').decode())
        with self.assertRaisesRegex(ValueError,'OUTSIDE_GENERATED_AREA'):
            mod.save(self.root,Path('other-reports'),report)

    def test_no_implicit_authority(self):
        rows=mod.audit(self.root,self.head,probe_remote=False)
        state,_=mod.summary(rows)
        self.assertNotEqual(state,'READY_FOR_WORKER_LAUNCH')
        self.assertNotEqual(state,'PASS_AUTHORIZING')

    def test_blob_oid_canonical_bytes(self):
        self.assertEqual(mod.blob_oid(b'hello\n'),hashlib.sha1(b'blob 6\x00hello\n').hexdigest())

    def test_untrusted_mode_and_symlink(self):
        p=self.root/'generated'/'link';p.symlink_to(self.root/'README.md')
        with self.assertRaises(ValueError):mod.read_regular(p)

if __name__=='__main__':unittest.main()
