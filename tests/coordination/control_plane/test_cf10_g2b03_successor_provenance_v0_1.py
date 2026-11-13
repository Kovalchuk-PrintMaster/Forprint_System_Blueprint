"""G2b-03A synthetic tests — no s01, signing, actual Gate invocation or provision."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.coordination.control_plane import cf10_g2b03_successor_provenance_v0_1 as m

class G2b03aTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='g2b03a_synthetic_')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.good_plan={'status':'SUCCESSOR_GATE_DESIGN_REVIEW_REQUIRED_NON_AUTHORIZING','blockers':[]}
        self.good_history={'status':'PASS','sha256':m.inv.EXPECTED_COVERAGE_SHA256}

    def evaluate(self,provenance):
        return m.evaluate(prior_plan=self.good_plan, provenance=provenance,history=self.good_history)

    def test_01_fixed_candidate_path(self):
        self.assertEqual(str(m.CANDIDATE), '/srv/software_development/forprint-releases/cf10/evidence/cf10_writer_coverage_gate3d90143_170494.json')

    def test_02_missing_candidate_non_authorizing(self):
        with mock.patch.object(m,'CANDIDATE',self.root/'absent'):
            r=m.candidate_probe(self.root/'absent')
        self.assertEqual(r['status'],'MISSING')
        self.assertEqual(self.evaluate(r)['state'],'EXTERNAL_CANDIDATE_MISSING_NON_AUTHORIZING')
        self.assertFalse(self.evaluate(r)['authority_granted'])

    def test_03_different_candidate_path_blocked(self):
        r=m.candidate_probe(self.root/'bad-path')
        self.assertEqual(r['status'],'BLOCKED')

    def test_04_symlink_candidate_blocked(self):
        t=self.root/'real';t.write_bytes(b'x')
        link=self.root/'link';link.symlink_to(t)
        with mock.patch.object(m,'CANDIDATE',link):
            r=m.candidate_probe(link)
        self.assertEqual(r['status'],'BLOCKED')

    def test_05_symlink_parent_blocked(self):
        actual=self.root/'real-parent';actual.mkdir()
        parent=self.root/'linked-parent';parent.symlink_to(actual,target_is_directory=True)
        link=parent/'evidence.json'
        with mock.patch.object(m,'CANDIDATE',link):
            r=m.candidate_probe(link)
        self.assertEqual(r['status'],'BLOCKED')

    def test_06_valid_source_bytes_and_profile_pass(self):
        raw=b'fixture exact bytes';sha=hashlib.sha256(raw).hexdigest();path=self.root/'external'
        with mock.patch.object(m,'CANDIDATE',path),mock.patch.object(m,'read_candidate',return_value=raw), \
             mock.patch.object(m.inv,'EXPECTED_COVERAGE_SHA256',sha), \
             mock.patch.object(m.inv,'coverage_probe',return_value={'status':'PASS'}), \
             mock.patch.object(Path,'exists',return_value=True):
            r=m.candidate_probe(path)
        self.assertEqual(r['status'],'PASS');self.assertEqual(r['sha256'],sha)

    def test_07_wrong_sha_blocked(self):
        raw=b'wrong';path=self.root/'external'
        with mock.patch.object(m,'CANDIDATE',path),mock.patch.object(m,'read_candidate',return_value=raw), \
             mock.patch.object(m.inv,'EXPECTED_COVERAGE_SHA256','a'*64):
            # Need candidate path to appear present to avoid MISSING branch.
            with mock.patch.object(Path,'exists',return_value=True):
                r=m.candidate_probe(path)
        self.assertEqual(r['status'],'BLOCKED')

    def test_08_wrong_profile_blocked(self):
        raw=b'fixture';path=self.root/'external';sha=hashlib.sha256(raw).hexdigest()
        with mock.patch.object(m,'CANDIDATE',path),mock.patch.object(m,'read_candidate',return_value=raw), \
             mock.patch.object(m.inv,'EXPECTED_COVERAGE_SHA256',sha), \
             mock.patch.object(m.inv,'coverage_probe',return_value={'status':'BLOCKED','detail':'schema drift'}), \
             mock.patch.object(Path,'exists',return_value=True):
            r=m.candidate_probe(path)
        self.assertEqual(r['status'],'BLOCKED')

    def test_09_prerequisite_wrong_blocks(self):
        d=m.evaluate(prior_plan={'status':'BLOCKED_NON_AUTHORIZING','blockers':['x']},
                     provenance={'status':'MISSING'},history=self.good_history)
        self.assertEqual(d['state'],'BLOCKED_NON_AUTHORIZING')

    def test_10_historical_unverified_blocks(self):
        d=m.evaluate(prior_plan=self.good_plan,provenance={'status':'MISSING'},
                     history={'status':'MISSING','sha256':None})
        self.assertIn('HISTORICAL_COVERAGE_UNVERIFIED',d['blockers'])

    def test_11_candidate_conflict_blocks(self):
        self.assertEqual(self.evaluate({'status':'BLOCKED'})['state'],'BLOCKED_NON_AUTHORIZING')

    def test_12_candidate_pass_still_nonauthorizing(self):
        d=self.evaluate({'status':'PASS','sha256':m.inv.EXPECTED_COVERAGE_SHA256})
        self.assertEqual(d['state'],'PROVENANCE_CANDIDATE_VERIFIED_NON_AUTHORIZING')
        for field in ('authority_granted','external_evidence_rebound','worker_launched',
                      'successor_dynamic_coverage_verified','signed_operator_approval_verified',
                      'independent_gate_verifier_accepted'):
            self.assertIs(d[field],False)

    def test_13_mismatched_external_and_original_sha_blocks(self):
        self.assertEqual(self.evaluate({'status':'PASS','sha256':'b'*64})['state'],'BLOCKED_NON_AUTHORIZING')

    def test_14_unknown_status_blocks(self):
        self.assertEqual(self.evaluate({'status':'READY'})['state'],'BLOCKED_NON_AUTHORIZING')

    def test_15_private_scratch_report(self):
        (self.root/'tmp').mkdir()
        d=m.write_report(self.root,self.evaluate({'status':'MISSING'}))
        self.assertEqual(sorted(x.name for x in d.iterdir()),['SHA256SUMS','report.json','summary.txt'])
        for x in ('report.json','summary.txt','SHA256SUMS'):
            self.assertEqual((d/x).stat().st_mode&0o777,0o600)
        for line in (d/'SHA256SUMS').read_text().splitlines():
            sha,name=line.split()
            self.assertEqual(sha,hashlib.sha256((d/name).read_bytes()).hexdigest())
        self.assertFalse((self.root/'generated').exists())

    def test_16_symlink_scratch_rejected(self):
        (self.root/'tmp').symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(m.EvidenceBlocked):
            m.write_report(self.root,self.evaluate({'status':'MISSING'}))

    def test_17_report_nonauthorizing(self):
        (self.root/'tmp').mkdir()
        path=m.write_report(self.root,self.evaluate({'status':'MISSING'}))
        data=json.loads((path/'report.json').read_text())
        self.assertFalse(data['independent_gate_or_writer_executed'])
        self.assertFalse(data['historical_evidence_copied'])

    def test_18_no_direct_provision_interface(self):
        self.assertFalse(hasattr(m,'provision'))
        self.assertFalse(hasattr(m,'activate'))

    def test_19_original_historical_verification_required(self):
        with mock.patch.object(m.inv,'review',return_value={'status':'INVENTORY_REVIEW_REQUIRED_NON_AUTHORIZING','checks':[{'id':'historical_coverage','status':'MISSING'}]}), \
             mock.patch.object(m.plan,'independent_sources',return_value={}), \
             mock.patch.object(m.plan,'plan_from_observations',return_value=self.good_plan), \
             mock.patch.object(m,'candidate_probe',return_value={'status':'MISSING'}):
            d=m.audit(self.root,'0'*40,self.root/'history')
        self.assertEqual(d['state'],'BLOCKED_NON_AUTHORIZING')

    def test_20_cli_missing_head_fails(self):
        self.assertEqual(m.main(['--root',str(self.root),'--expected-head','abc','--no-report']),2)

if __name__=='__main__':unittest.main()
