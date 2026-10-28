"""Synthetic G2b-01 checks: no real s01 signer, Gate, evidence, remote, or runtime writes."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as a


class G2b01Tests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(prefix='g2b01_test_')
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)

    def make_coverage(self, data=None):
        if data is None:
            data={'schema_version':'forprint_execution_attempt_writer_deployment_evidence_v0_2',
                  'status':'READY_FOR_INDEPENDENT_REVIEW','technical_blockers':[],
                  'gate_publication':{'remote':a.ORIGIN,'ref':a.g2.RELEASES['gate']['ref'],'commit':a.g2.RELEASES['gate']['head']},
                  'writer_publication':{'remote':a.ORIGIN,'ref':a.g2.RELEASES['writer']['ref'],'commit':a.g2.RELEASES['writer']['head']}}
        p=self.root/'coverage.json'
        p.write_text(json.dumps(data))
        return p

    def test_01_known_sha_pinned(self):
        self.assertEqual(len(a.EXPECTED_COVERAGE_SHA256),64)
        self.assertEqual(a.EVIDENCE_ID,'cf10-g2a-stable-releases-f37abe98-20261028')

    def test_02_missing_historical_is_review_only(self):
        r=a.coverage_probe(self.root/'missing.json','historical_coverage')
        self.assertEqual(r['status'],'MISSING')

    def test_03_bad_historical_sha_is_blocked(self):
        r=a.coverage_probe(self.make_coverage(),'historical_coverage')
        self.assertEqual((r['status'],r['detail']),('BLOCKED','COVERAGE_SHA256_DRIFT'))

    def test_04_correct_sha_and_profile_pass(self):
        p=self.make_coverage();sha=hashlib.sha256(p.read_bytes()).hexdigest()
        with mock.patch.object(a,'EXPECTED_COVERAGE_SHA256',sha):
            r=a.coverage_probe(p,'historical_coverage')
        self.assertEqual(r['status'],'PASS')

    def test_05_profile_mismatch_blocked(self):
        p=self.make_coverage({'schema_version':'other','status':'READY_FOR_INDEPENDENT_REVIEW','technical_blockers':[]})
        with mock.patch.object(a,'EXPECTED_COVERAGE_SHA256',hashlib.sha256(p.read_bytes()).hexdigest()):
            r=a.coverage_probe(p,'historical_coverage')
        self.assertEqual(r['detail'],'COVERAGE_SCHEMA_DRIFT')

    def test_06_publication_drift_blocked(self):
        p=self.make_coverage();d=json.loads(p.read_text());d['writer_publication']['commit']='0'*40;p.write_text(json.dumps(d))
        with mock.patch.object(a,'EXPECTED_COVERAGE_SHA256',hashlib.sha256(p.read_bytes()).hexdigest()):
            r=a.coverage_probe(p,'historical_coverage')
        self.assertTrue(r['detail'].startswith('COVERAGE_PUBLICATION_PIN_DRIFT'))

    def test_07_unsafe_symlink_rejected(self):
        p=self.make_coverage();link=self.root/'symlink.json';link.symlink_to(p)
        self.assertEqual(a.coverage_probe(link,'historical_coverage')['status'],'BLOCKED')

    def test_08_sensitive_signed_payload_not_read(self):
        signed=self.root/'signed.json';signed.write_bytes(b'{"secret":"must-not-be-read"}')
        with mock.patch.object(a,'regular_private_or_stable',side_effect=AssertionError('should never read')):
            result=a.signer_probe(signed)
        self.assertNotIn('secret',json.dumps(result))
        self.assertIn(result['status'],('REVIEW','BLOCKED'))

    def test_09_missing_signed_is_not_authority(self):
        self.assertEqual(a.signer_probe(self.root/'missing')['status'],'MISSING')

    def test_10_quarantine_stable_roots_pass(self):
        make='\n'.join([*(str(a.g2.stable_path(k)) for k in ('gate','writer')),
                        str(a.STABLE_COVERAGE),
                        'CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND',
                        'CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND',
                        'governed-worker-cycle-launch: cf10-s01-runtime-launch-preflight'])
        texts={'Makefile':make,
               'scripts/coordination/control_plane/s01_writer_runtime_binding_v0_1.py':
               'COVERAGE_EVIDENCE_NOT_FROM_GATE_TMP gate_root / "tmp"',
               'scripts/coordination/control_plane/s01_writer_runtime_binding_v0_2.py':
               'from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_1 as inventory'}
        r=a.make_boundary_probe(texts)
        self.assertEqual([x['status'] for x in r],['PASS','REVIEW'])

    def test_11_no_quarantine_blocked(self):
        t={'Makefile':'nope','scripts/coordination/control_plane/s01_writer_runtime_binding_v0_1.py':'',
           'scripts/coordination/control_plane/s01_writer_runtime_binding_v0_2.py':''}
        self.assertEqual(a.make_boundary_probe(t)[0]['status'],'BLOCKED')

    def test_12_no_source_blocked(self):
        self.assertEqual(a.make_boundary_probe({})[0]['status'],'BLOCKED')

    def test_13_review_never_grants_authority(self):
        sample=a.row('x','PASS','ok')
        with mock.patch.object(a,'canonical_probe',return_value=(sample,{})), \
             mock.patch.object(a,'release_probe',return_value=sample), \
             mock.patch.object(a,'coverage_probe',return_value=sample), \
             mock.patch.object(a,'signer_probe',return_value=sample):
            result=a.review(self.root,'0'*40,self.root/'old',verify_vault=False)
        self.assertFalse(result['authority_granted']);self.assertFalse(result['worker_launched'])
        self.assertFalse(result['historical_evidence_copied']);self.assertFalse(result['new_signed_head_authorized'])

    def test_14_missing_coverage_nonauthorizing_review(self):
        sample=a.row('x','PASS','ok')
        def coverage(path,name):return a.row(name,'MISSING','not found')
        with mock.patch.object(a,'canonical_probe',return_value=(sample,{'x':'y'})), \
             mock.patch.object(a,'make_boundary_probe',return_value=[sample]), \
             mock.patch.object(a,'release_probe',return_value=sample), \
             mock.patch.object(a,'coverage_probe',side_effect=coverage), \
             mock.patch.object(a,'signer_probe',return_value=sample):
            result=a.review(self.root,'0'*40,self.root/'old',verify_vault=False)
        self.assertEqual(result['status'],'INVENTORY_REVIEW_REQUIRED_NON_AUTHORIZING')

    def test_15_blocked_conflict_failclosed(self):
        blocked=a.row('x','BLOCKED','sha drift')
        with mock.patch.object(a,'canonical_probe',return_value=(blocked,{})), \
             mock.patch.object(a,'release_probe',return_value=blocked), \
             mock.patch.object(a,'coverage_probe',return_value=blocked), \
             mock.patch.object(a,'signer_probe',return_value=blocked):
            result=a.review(self.root,'0'*40,self.root/'old',verify_vault=False)
        self.assertEqual(result['status'],'BLOCKED_NON_AUTHORIZING')

    def test_16_scratch_report_only(self):
        (self.root/'tmp').mkdir()
        d=a.save_scratch(self.root,{'status':'INVENTORY_REVIEW_REQUIRED_NON_AUTHORIZING','checks':[a.row('x','MISSING','not found')]})
        self.assertEqual(sorted(p.name for p in d.iterdir()),['SHA256SUMS','report.json','summary.txt'])
        self.assertIn('AUTHORITY_GRANTED=false',(d/'summary.txt').read_text())
        self.assertFalse((self.root/'generated').exists())

    def test_17_symlink_scratch_blocked(self):
        (self.root/'tmp').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(a.ReviewBlocked):a.save_scratch(self.root,{'status':'test','checks':[]})

    def test_18_file_mode_600(self):
        (self.root/'tmp').mkdir();d=a.save_scratch(self.root,{'status':'test','checks':[]})
        self.assertEqual((d/'report.json').stat().st_mode & 0o777,0o600)

    def test_19_expected_sha_required(self):
        with mock.patch.object(a,'git_read',return_value='whatever'):
            r,_=a.canonical_probe(self.root,'invalid')
        self.assertEqual(r['status'],'BLOCKED')

    def test_20_regular_file_mode_guard(self):
        p=self.root/'file';p.write_bytes(b'x');p.chmod(0o666)
        with self.assertRaises(a.ReviewBlocked):a.regular_private_or_stable(p,100)

    def test_21_canonical_missing_repo_blocked(self):
        r,_=a.canonical_probe(self.root,'a'*40)
        self.assertEqual(r['status'],'BLOCKED')

    def test_22_vault_not_coverage(self):
        with mock.patch.object(a.vault,'verify_registered',return_value={'state':'VERIFIED_REGISTERED_NON_AUTHORIZING','sha256':'1'*64}):
            r=a.vault_probe()
        self.assertEqual(r['status'],'PASS');self.assertIn('NOT_COVERAGE_REBIND',r['detail'])

    def test_23_vault_missing_blocked(self):
        with mock.patch.object(a.vault,'verify_registered',side_effect=a.vault.VaultBlocked('missing')):
            r=a.vault_probe()
        self.assertEqual(r['status'],'BLOCKED')

if __name__=='__main__':unittest.main()
