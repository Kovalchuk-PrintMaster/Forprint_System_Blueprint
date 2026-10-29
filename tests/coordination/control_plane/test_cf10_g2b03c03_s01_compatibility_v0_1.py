"""Synthetic S01 gate compatibility cases; never launches Worker or signs anything."""
import importlib.util
import unittest
from pathlib import Path
from unittest import mock
import sys, types, tempfile

ROOT=Path(__file__).resolve().parents[3]/'scripts'/'coordination'/'control_plane'

def mod(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
A=mod('cf10_g2b03c03a_writer_delta_v0_1.py','private_a')
B=mod('cf10_g2b03c03b_binding_design_v0_1.py','private_b')
C=mod('s01_writer_runtime_binding_v0_3.py','private_c')
HEAD='82778fc1c51e27fc1354686f65d3415eeb00f938'
REL=A.REL
LOCK=A.LOCK_REL


def a_profile():
    return {'classification':A.S01_PROFILE,'recognized_s01_hardening':True,
            'recognized_b3_augmentation':True,'hunks':[{'kind':'insert'}]*6}

def writer_lock():
    return {'status':A.S01_LOCK_STATUS,'current_sha256':A.S01_LOCK_SHA256,
            'pinned_sha256':A.PINNED_LOCK_SHA256,'independently_attested':False}

def a_delta():
    return {'source_head':HEAD,'status':'S01_WRITER_HARDENING_COMPATIBILITY_REVIEW_REQUIRED_NON_AUTHORIZING',
            'blockers':[],'authority_granted':False,'b3_behavior_independently_verified':False,
            'writer_lock_review':writer_lock(), 'delta_review':a_profile()}

def fixture_b():
    return {'status':'PASS','returncode':0,'test_paths':list(B.TESTS),'passed_count':62,
            'stdout_sha256':'1'*64,'stderr_sha256':'2'*64}

def b_profile():
    return B.classify(a_delta(),fixture_b(),{rel:'a'*64 for rel in B.SOURCE_SET},head=HEAD)

def live():
    return {'status':'LIVE_OBSERVATION_REVIEW_REQUIRED_NON_AUTHORIZING',
            'source_head':HEAD,'blockers':[],'authority_granted':False,'dynamic_coverage_verified':False,
            'observed_s01_runtime':{'writer_source_comparison':{REL:False, LOCK:False,'ledger.py':True}}}

def c_profile(delta=None, report=None, runtime=None):
    return C.classify(head=HEAD,live=runtime or live(),delta=delta or a_delta(),b3=report or b_profile(),
                      source_match={'a':'b'*64},source_hashes={'c':'d'*64},mode='inspect')

class StrictBridgeTests(unittest.TestCase):
    def test_b_accepts_exact_s01_profile_non_authorizing(self):
        doc=b_profile();self.assertEqual(doc['status'],'B3_REGRESSION_PASS_BINDING_DESIGN_REVIEW_REQUIRED_NON_AUTHORIZING');self.assertEqual(doc['source_compatibility_profile'],'S01_FAIL_CLOSED');self.assertFalse(doc['authority_granted'])
    def test_b_missing_lock_blocked(self):
        d=a_delta();d.pop('writer_lock_review');x=B.classify(d,fixture_b(),{rel:'a'*64 for rel in B.SOURCE_SET},head=HEAD)
        self.assertIn('S01_FAIL_CLOSED_WRITER_PROFILE_NOT_VERIFIED',x['blockers'])
    def test_b_wrong_lock_hash_blocked(self):
        d=a_delta();d['writer_lock_review']['current_sha256']='0'*64;x=B.classify(d,fixture_b(),{rel:'a'*64 for rel in B.SOURCE_SET},head=HEAD)
        self.assertIn('S01_FAIL_CLOSED_WRITER_PROFILE_NOT_VERIFIED',x['blockers'])
    def test_b_extra_hunk_blocked(self):
        d=a_delta();d['delta_review']['hunks'].append({});x=B.classify(d,fixture_b(),{rel:'a'*64 for rel in B.SOURCE_SET},head=HEAD)
        self.assertIn('S01_FAIL_CLOSED_WRITER_PROFILE_NOT_VERIFIED',x['blockers'])
    def test_b_forged_authority_blocked(self):
        d=a_delta();d['authority_granted']=True;x=B.classify(d,fixture_b(),{rel:'a'*64 for rel in B.SOURCE_SET},head=HEAD)
        self.assertIn('PRIOR_DELTA_REVIEW_UNVERIFIED',x['blockers'])
    def test_b_wrong_tests_blocked(self):
        f=fixture_b();f['passed_count']=2;x=B.classify(a_delta(),f,{rel:'a'*64 for rel in B.SOURCE_SET},head=HEAD)
        self.assertIn('B3_FOCUSED_REGRESSION_NOT_PROVEN',x['blockers'])
    def test_c_exact_s01_non_authorizing(self):
        x=c_profile();self.assertEqual(x['status'],'VERSIONED_BINDING_CANDIDATE_REVIEW_REQUIRED_NON_AUTHORIZING');self.assertFalse(x['launch_allowed']);self.assertFalse(x['authority_granted']);self.assertFalse(x['independent_dynamic_coverage_verified'])
    def test_c_old_report_head_blocked(self):
        r=b_profile();r['expected_head']=C.PREDECESSOR_HEAD
        self.assertIn('B3_REGRESSION_EVIDENCE_NOT_ACCEPTABLE',c_profile(report=r)['blockers'])
    def test_c_old_report_profile_blocked(self):
        r=b_profile();r['source_compatibility_profile']='HISTORICAL_B3_ONLY'
        self.assertIn('B3_REGRESSION_EVIDENCE_NOT_ACCEPTABLE',c_profile(report=r)['blockers'])
    def test_c_missing_strict_lock_blocked(self):
        d=a_delta();d.pop('writer_lock_review');self.assertIn('B3_WRITER_DELTA_NOT_VERIFIED',c_profile(delta=d)['blockers'])
    def test_c_additional_writer_delta_blocked(self):
        l=live();l['observed_s01_runtime']['writer_source_comparison']['arbitrary.py']=False
        self.assertIn('WRITER_DELTA_SCOPE_CHANGED',c_profile(runtime=l)['blockers'])
    def test_c_failed_fixture_blocked(self):
        r=b_profile();r['focused_synthetic_regression']['returncode']=2
        self.assertIn('B3_REGRESSION_EVIDENCE_NOT_ACCEPTABLE',c_profile(report=r)['blockers'])
    def test_c_preflight_always_blocked(self):
        x=C.classify(head=HEAD,live=live(),delta=a_delta(),b3=b_profile(),source_match={'a':'b'*64},source_hashes={'c':'d'*64},mode='launch-preflight')
        self.assertEqual(x['status'],'BLOCKED_NON_AUTHORIZING');self.assertIn('MAKE_QUARANTINE_NOT_RELEASED',x['blockers']);self.assertFalse(x['launch_allowed'])

if __name__=='__main__':unittest.main()

# Tests added below are reattached explicitly to avoid relying on test order.
class ReportReaderTests(unittest.TestCase):
    def test_new_report_path_requires_known_project_family(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(C.BindingBlocked):
                C.load_b3_report(root,root/'tmp'/'unrelated'/'report.json','a'*64)
    def test_forged_digest_is_rejected_before_json(self):
        import tempfile,os
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            folder=root/'tmp'/'cf10_g2b03c03b_review_test';folder.mkdir(parents=True,mode=0o700)
            (folder/'report.json').write_text('{}')
            os.chmod(folder/'report.json',0o600)
            with self.assertRaises(C.BindingBlocked):
                C.load_b3_report(root,folder/'report.json','f'*64)


class PublishedWorkflowBridgeTests(unittest.TestCase):
    def _fake_modules(self, attrs):
        root = types.ModuleType('scripts')
        root.__path__ = []
        middle = types.ModuleType('scripts.coordination')
        middle.__path__ = []
        cp = types.ModuleType('scripts.coordination.control_plane')
        cp.__path__ = []
        for k,v in attrs.items():
            setattr(cp,k,v)
        return {'scripts':root, 'scripts.coordination':middle,
                'scripts.coordination.control_plane':cp}

    def test_b_audit_reaches_fixtures_with_exact_s01_approved_source(self):
        fake=self._fake_modules({'cf10_g2b03c03a_writer_delta_v0_1':
                                  types.SimpleNamespace(audit=lambda root,head:a_delta())})
        fixture=lambda root,out:fixture_b()
        with mock.patch.dict(sys.modules,fake), mock.patch.object(B,'published_set',return_value={p:'a'*64 for p in B.SOURCE_SET}):
            x=B.audit(Path('/mock/root'),HEAD,Path('/mock/out'),fixture_runner=fixture)
        self.assertEqual(x['status'],'B3_REGRESSION_PASS_BINDING_DESIGN_REVIEW_REQUIRED_NON_AUTHORIZING')
        self.assertEqual(x['source_compatibility_profile'],'S01_FAIL_CLOSED')
        self.assertFalse(x['authority_granted'])

    def test_b_audit_rejects_forged_s01_profile_before_fixtures(self):
        bad=a_delta();bad['delta_review']['classification']='B3_INSERTION_ONLY_COMPATIBILITY_REVIEW_REQUIRED'
        fake=self._fake_modules({'cf10_g2b03c03a_writer_delta_v0_1':
                                  types.SimpleNamespace(audit=lambda root,head:bad)})
        with mock.patch.dict(sys.modules,fake):
            with self.assertRaises(B.DesignBlocked):
                B.audit(Path('/mock/root'),HEAD,Path('/mock/out'),
                        fixture_runner=lambda r,o:self.fail('must not run fixtures'))

    def test_c_review_reuses_independently_checked_delta_audit(self):
        import ast, inspect
        tree=ast.parse(inspect.getsource(C.review))
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)
               and isinstance(n.func,ast.Attribute)
               and isinstance(n.func.value,ast.Name)
               and n.func.value.id=='delta_lib']
        self.assertEqual([x.func.attr for x in calls],['audit'])
        # Pure classification is separately tested for missing lock evidence.
        self.assertIn('B3_WRITER_DELTA_NOT_VERIFIED',
          c_profile(delta={k:v for k,v in a_delta().items() if k!='writer_lock_review'})['blockers'])
