"""G2b03C03C negative fixtures: candidate never grants Writer or launch authority."""
from __future__ import annotations
import hashlib, importlib.util, json, os, pathlib, tempfile, unittest
from unittest import mock

S = pathlib.Path(__file__).resolve().parents[3] / 'scripts/coordination/control_plane/s01_writer_runtime_binding_v0_3.py'
spec=importlib.util.spec_from_file_location('binding_v03_fixture',S)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
H='9c314020359da15ad93392422eeb42e405b5cbb0'
SHA='a'*64
REL='scripts/coordination/control_plane/governed_worker_cycle.py'

def fixture():
    live={'status':'LIVE_OBSERVATION_REVIEW_REQUIRED_NON_AUTHORIZING','source_head':H,
          'blockers':[],'authority_granted':False,'dynamic_coverage_verified':False,
          'observed_s01_runtime':{'writer_source_comparison':{REL:False}}}
    delta={'status':'WRITER_DELTA_COMPATIBILITY_REVIEW_REQUIRED_NON_AUTHORIZING','source_head':H,
           'blockers':[],'authority_granted':False,
           'delta_review':{'classification':'B3_INSERTION_ONLY_COMPATIBILITY_REVIEW_REQUIRED'}}
    b3={'status':'B3_REGRESSION_PASS_BINDING_DESIGN_REVIEW_REQUIRED_NON_AUTHORIZING',
        'expected_head':m.PREDECESSOR_HEAD,'blockers':[],
        'authority_granted':False,'b3_behavior_independently_attested':False,
        'focused_synthetic_regression':{'passed_count':62,'returncode':0}}
    return live,delta,b3

class Tests(unittest.TestCase):
    def result(self, mutator=None,mode='inspect'):
        live,delta,b3=fixture()
        if mutator:mutator(live,delta,b3)
        return m.classify(head=H,live=live,delta=delta,b3=b3,
                          source_match={'x':SHA},source_hashes={'z':SHA},mode=mode)
    def blocked(self,fn,reason):
        r=self.result(fn)
        self.assertEqual(r['status'],'BLOCKED_NON_AUTHORIZING')
        self.assertIn(reason,r['blockers'])
        self.assertFalse(r['launch_allowed'])
    def test_inspect_still_requires_review(self):
        r=self.result()
        self.assertEqual(r['status'],'VERSIONED_BINDING_CANDIDATE_REVIEW_REQUIRED_NON_AUTHORIZING')
        for key in ('launch_allowed','ledger_append_allowed','runtime_binding_authorized',
                    'independent_dynamic_coverage_verified','independent_runtime_binding_attested',
                    'worker_launched','authority_granted','writer_gate_unquarantined'):
            self.assertIs(r[key],False)
    def test_preflight_always_blocks_even_good_fixtures(self):
        r=self.result(mode='launch-preflight')
        self.assertEqual(r['status'],'BLOCKED_NON_AUTHORIZING')
        self.assertIn('INDEPENDENT_SIGNED_RUNTIME_AND_DYNAMIC_WRITER_COVERAGE_REQUIRED',r['blockers'])
        self.assertIn('MAKE_QUARANTINE_NOT_RELEASED',r['blockers'])
    def test_live_blocker(self):self.blocked(lambda l,d,b:l.update(status='BLOCKED_NON_AUTHORIZING'),'SUCCESSOR_GATE_OBSERVATION_NOT_VERIFIED')
    def test_wrong_head(self):self.blocked(lambda l,d,b:l.update(source_head='f'*40),'SUCCESSOR_GATE_OBSERVATION_NOT_VERIFIED')
    def test_false_live_authority(self):self.blocked(lambda l,d,b:l.update(authority_granted=True),'SUCCESSOR_GATE_OBSERVATION_NOT_VERIFIED')
    def test_false_dynamic_claim(self):self.blocked(lambda l,d,b:l.update(dynamic_coverage_verified=True),'SUCCESSOR_GATE_OBSERVATION_NOT_VERIFIED')
    def test_bad_delta(self):self.blocked(lambda l,d,b:d['delta_review'].update(classification='UNEXPECTED_WRITER_DELTA_BLOCKED'),'B3_WRITER_DELTA_NOT_VERIFIED')
    def test_delta_identity(self):self.blocked(lambda l,d,b:d.update(source_head='e'*40),'B3_WRITER_DELTA_NOT_VERIFIED')
    def test_other_writer_drift(self):self.blocked(lambda l,d,b:l['observed_s01_runtime']['writer_source_comparison'].update({'other.py':False}),'WRITER_DELTA_SCOPE_CHANGED')
    def test_no_writer_drift(self):self.blocked(lambda l,d,b:l['observed_s01_runtime']['writer_source_comparison'].update({REL:True}),'WRITER_DELTA_SCOPE_CHANGED')
    def test_wrong_regression_count(self):self.blocked(lambda l,d,b:b['focused_synthetic_regression'].update(passed_count=61),'B3_REGRESSION_EVIDENCE_NOT_ACCEPTABLE')
    def test_false_attestation(self):self.blocked(lambda l,d,b:b.update(b3_behavior_independently_attested=True),'B3_REGRESSION_EVIDENCE_NOT_ACCEPTABLE')
    def test_regression_source_head(self):self.blocked(lambda l,d,b:b.update(expected_head='e'*40),'B3_REGRESSION_EVIDENCE_NOT_ACCEPTABLE')
    def test_regression_status(self):self.blocked(lambda l,d,b:b.update(status='BLOCKED_NON_AUTHORIZING'),'B3_REGRESSION_EVIDENCE_NOT_ACCEPTABLE')
    def test_report_requires_exact_path(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(m.BindingBlocked):
                m.load_b3_report(pathlib.Path(temp),pathlib.Path(temp)/'foreign.json',m.EXPECTED_REPORT_SHA)
    def test_report_requires_exact_external_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp)/m.FROZEN_B3_REPORT
            with self.assertRaises(m.BindingBlocked):
                m.load_b3_report(pathlib.Path(temp),p,'0'*64)
    def test_report_content_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp); folder=root/'tmp'/m.REPORT_NAME;folder.mkdir(parents=True,mode=0o700)
            (folder/'report.json').write_text('{}')
            os.chmod(folder/'report.json',0o600)
            with self.assertRaises(m.BindingBlocked):
                m.load_b3_report(root,folder/'report.json',m.EXPECTED_REPORT_SHA)
    def test_report_deny_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp);folder=root/'tmp'/m.REPORT_NAME;folder.mkdir(parents=True,mode=0o700)
            (folder/'real').write_text('hi');(folder/'report.json').symlink_to(folder/'real')
            with self.assertRaises(m.BindingBlocked):
                m.load_b3_report(root,folder/'report.json',m.EXPECTED_REPORT_SHA)
    def test_report_create_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp);(root/'tmp').mkdir()
            folder,sha=m.save_report(root,self.result())
            self.assertEqual(len(sha),64)
            self.assertTrue((folder/'SHA256SUMS').is_file())
            self.assertEqual((folder/'report.json').stat().st_mode & 0o777,0o600)
    def test_project_scratch_symlink_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp);(root/'real').mkdir();(root/'tmp').symlink_to(root/'real')
            with self.assertRaises(m.BindingBlocked):m.save_report(root,self.result())

if __name__=='__main__':unittest.main()
