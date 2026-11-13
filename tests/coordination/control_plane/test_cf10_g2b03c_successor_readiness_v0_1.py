"""G2b-03C pure policy unit tests. No external state, Worker, signature or ledger."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

S = (Path(__file__).resolve().parents[3] / 'scripts/coordination/control_plane'
     / 'cf10_g2b03c_successor_readiness_v0_1.py')
spec = importlib.util.spec_from_file_location('g2b03c_candidate', S)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

HEAD = 'c57dae308336052ee1709d10419c7577f502e787'
SHA = '15bb96b3fdb87186d8337dfa17391bfd5a5a951e2faae34c8c671734d4027b71'
TARGET = '/srv/software_development/forprint-releases/cf10/evidence/cf10_writer_coverage_gate3d90143_170494.json'


def prior():
    return {'state': mod.EXPECTED_CANDIDATE_STATE, 'blockers': [],
            'g2b02_planning_state': mod.EXPECTED_PLAN_STATE,
            'external_candidate_check': {'status': 'PASS', 'sha256': SHA, 'path': TARGET},
            'original_historical_check': {'status': 'PASS', 'sha256': SHA},
            'authority_granted': False, 'successor_dynamic_coverage_verified': False}


def checks():
    return {k: {'status': 'PASS'} for k in ('gate', 'writer', 'runtime_v1', 'runtime_v2', 'quarantine')}


class ClassifierTests(unittest.TestCase):
    def review(self, p=None, c=None, head=HEAD, path=TARGET, sha=SHA):
        return mod.classify(prior() if p is None else p, checks() if c is None else c,
                            head=head, candidate_path=path, candidate_sha=sha)

    def test_positive_is_design_only(self):
        r = self.review()
        self.assertEqual(r['status'], 'DESIGN_REVIEW_READY_NON_AUTHORIZING')
        for field in ('authority_granted','worker_launched','dynamic_coverage_verified','signature_verified',
                      'coverage_rebound','writer_gate_unquarantined','current_runtime_probed'):
            self.assertIs(r[field], False, field)

    def test_missing_provenance(self):
        p=prior(); p['state']='EXTERNAL_CANDIDATE_MISSING_NON_AUTHORIZING'
        self.assertIn('G2B03A_PROVENANCE_NOT_PASS', self.review(p)['blockers'])

    def test_fake_prior_authority(self):
        p=prior(); p['authority_granted']=True
        self.assertIn('PRIOR_FALSE_AUTHORITY_OR_DYNAMIC_CLAIM', self.review(p)['blockers'])

    def test_false_dynamic_claim(self):
        p=prior(); p['successor_dynamic_coverage_verified']=True
        self.assertEqual(self.review(p)['status'], 'BLOCKED_NON_AUTHORIZING')

    def test_candidate_sha_drift(self):
        p=prior(); p['external_candidate_check']['sha256']='0'*64
        self.assertIn('EXTERNAL_COVERAGE_PIN_NOT_VERIFIED', self.review(p)['blockers'])

    def test_candidate_path_drift(self):
        p=prior(); p['external_candidate_check']['path']='/tmp/injected.json'
        self.assertIn('EXTERNAL_COVERAGE_PIN_NOT_VERIFIED', self.review(p)['blockers'])

    def test_historical_sha_drift(self):
        p=prior(); p['original_historical_check']['sha256']='0'*64
        self.assertIn('HISTORICAL_COVERAGE_PIN_NOT_VERIFIED', self.review(p)['blockers'])

    def test_g2b02_missing(self):
        p=prior(); p['g2b02_planning_state']='BLOCKED_NON_AUTHORIZING'
        self.assertIn('G2B02_PLAN_NOT_PASS', self.review(p)['blockers'])

    def test_missing_source_token(self):
        self.assertEqual(mod.anchors('hello', ('hello','other')), {'status':'BLOCKED','missing':['other']})

    def test_gate_anchor_drift(self):
        c=checks(); c['gate']={'status':'BLOCKED'}
        self.assertIn('SOURCE_ANCHOR_NOT_VERIFIED:gate', self.review(c=c)['blockers'])

    def test_runtime_v1_anchor_drift(self):
        c=checks(); c['runtime_v1']={'status':'BLOCKED'}
        self.assertEqual(self.review(c=c)['status'], 'BLOCKED_NON_AUTHORIZING')

    def test_runtime_v2_anchor_drift(self):
        c=checks(); c['runtime_v2']={'status':'BLOCKED'}
        self.assertEqual(self.review(c=c)['status'], 'BLOCKED_NON_AUTHORIZING')

    def test_quarantine_anchor_drift(self):
        c=checks(); c['quarantine']={'status':'BLOCKED'}
        self.assertIn('SOURCE_ANCHOR_NOT_VERIFIED:quarantine', self.review(c=c)['blockers'])

    def test_bad_head(self):
        self.assertIn('EXPECTED_HEAD_INVALID', self.review(head='bad')['blockers'])

    def test_anchors_positive(self):
        self.assertEqual(mod.anchors('first second', ('first','second'))['status'], 'PASS')

    def test_report_files_are_create_only(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); (root/'tmp').mkdir()
            folder,digest=mod.write_report(root,self.review())
            self.assertTrue((folder/'SHA256SUMS').is_file())
            self.assertEqual(len(digest),64)
            self.assertEqual((folder/'report.json').stat().st_mode & 0o777,0o600)

    def test_report_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); real=root/'real';real.mkdir();(root/'tmp').symlink_to(real)
            with self.assertRaises(mod.ReadinessBlocked):
                mod.write_report(root,self.review())

if __name__ == '__main__': unittest.main()
