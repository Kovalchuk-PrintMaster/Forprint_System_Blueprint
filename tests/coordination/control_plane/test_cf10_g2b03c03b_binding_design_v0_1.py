"""G2b03C03B pure policy/fixture runner tests. No canonical, Worker or signed state."""
import importlib.util
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import tempfile
import sys
import subprocess

S=Path(__file__).resolve().parents[3]/'scripts/coordination/control_plane/cf10_g2b03c03b_binding_design_v0_1.py'
spec=importlib.util.spec_from_file_location('c03b_design',S)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
HEAD='c9fe8d390fe952b7000107ee13161cdd7d9e9656'

def prior():
    return {'source_head':HEAD,'status':'WRITER_DELTA_COMPATIBILITY_REVIEW_REQUIRED_NON_AUTHORIZING',
            'blockers':[],'authority_granted':False,'b3_behavior_independently_verified':False,
            'delta_review':{'classification':'B3_INSERTION_ONLY_COMPATIBILITY_REVIEW_REQUIRED',
                            'recognized_b3_augmentation':True,'hunks':[{}, {}, {}]}}

def fixture():
    return {'status':'PASS','returncode':0,'test_paths':list(mod.TESTS),'passed_count':43,
            'stdout_sha256':'a'*64,'stderr_sha256':'b'*64}

def pubs(): return {x:'f'*64 for x in mod.SOURCE_SET}

class ContractTests(TestCase):
    def call(self,p=None,f=None,files=None):
        return mod.classify(prior() if p is None else p,fixture() if f is None else f,
                            pubs() if files is None else files,head=HEAD)
    def test_review_is_never_authority(self):
        x=self.call()
        self.assertEqual(x['status'],'B3_REGRESSION_PASS_BINDING_DESIGN_REVIEW_REQUIRED_NON_AUTHORIZING')
        for key in ('authority_granted','dynamic_coverage_verified','worker_launched',
                    'signed_renewal_performed','b3_behavior_independently_attested',
                    'successor_binding_implemented','writer_gate_unquarantined'):
            self.assertIs(x[key],False,key)
    def test_wrong_prior_status(self):
        p=prior();p['status']='BLOCKED_NON_AUTHORIZING'
        self.assertIn('PRIOR_DELTA_REVIEW_UNVERIFIED',self.call(p=p)['blockers'])
    def test_wrong_head(self):
        p=prior();p['source_head']='0'*40
        self.assertIn('CANONICAL_HEAD_OR_DELTA_BINDING_DRIFT',self.call(p=p)['blockers'])
    def test_prior_authority(self):
        p=prior();p['authority_granted']=True
        self.assertEqual(self.call(p=p)['status'],'BLOCKED_NON_AUTHORIZING')
    def test_no_delta(self):
        p=prior();p['delta_review']['hunks']=[{},{}]
        self.assertIn('B3_DELTA_PROFILE_UNEXPECTED',self.call(p=p)['blockers'])
    def test_extra_untrusted_source(self):
        s=pubs();s['test_extra.py']='f'*64
        self.assertIn('EXACT_PUBLISHED_TEST_AND_SOURCE_SET_NOT_VERIFIED',self.call(files=s)['blockers'])
    def test_missing_published_source(self):
        s=pubs();s.pop(next(iter(s)))
        self.assertEqual(self.call(files=s)['status'],'BLOCKED_NON_AUTHORIZING')
    def test_unhashed_source(self):
        s=pubs();s[next(iter(s))]='no'
        self.assertEqual(self.call(files=s)['status'],'BLOCKED_NON_AUTHORIZING')
    def test_fixture_fail(self):
        f=fixture();f['returncode']=1;f['status']='BLOCKED'
        self.assertIn('B3_FOCUSED_REGRESSION_NOT_PROVEN',self.call(f=f)['blockers'])
    def test_no_case_count(self):
        f=fixture();f['passed_count']=0
        self.assertEqual(self.call(f=f)['status'],'BLOCKED_NON_AUTHORIZING')
    def test_fixture_wrong_files(self):
        f=fixture();f['test_paths']=['/tmp/unauthorized.py']
        self.assertEqual(self.call(f=f)['status'],'BLOCKED_NON_AUTHORIZING')
    def test_fixture_missing_digest(self):
        f=fixture();f['stderr_sha256']=''
        self.assertEqual(self.call(f=f)['status'],'BLOCKED_NON_AUTHORIZING')
    def test_create_only_report(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'tmp').mkdir();out=mod.create_output(root)
            mod.write_create_only(out,'fixture_stdout.txt',b'42 passed')
            mod.write_create_only(out,'fixture_stderr.txt',b'')
            dig=mod.save_report(out,self.call())
            self.assertEqual(len(dig),64)
            self.assertEqual((out/'report.json').stat().st_mode & 0o777,0o600)
            self.assertEqual(len((out/'SHA256SUMS').read_text().splitlines()),4)
            with self.assertRaises(FileExistsError):mod.write_create_only(out,'report.json',b'mutated')
    def test_refuse_symlink_scratch(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); (root/'real').mkdir();(root/'tmp').symlink_to(root/'real')
            with self.assertRaises(mod.DesignBlocked):mod.create_output(root)
    def test_fixture_runner_synthetic_stdout(self):
        class P:
            returncode=0;stdout=b'48 passed in 1.5s\n';stderr=b''
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);out=root/'out';out.mkdir()
            with patch.object(subprocess,'run',return_value=P()) as mock:
                x=mod.run_fixtures(root,out,python=sys.executable)
                cmd=mock.call_args.args[0]
            self.assertEqual(x['status'],'PASS')
            self.assertEqual(x['passed_count'],48)
            self.assertEqual(tuple(cmd[-2:]),mod.TESTS)
            self.assertTrue((out/'fixture_stdout.txt').is_file())
    def test_fixture_runner_synthetic_failure(self):
        class P:
            returncode=1;stdout=b'1 failed, 47 passed\n';stderr=b''
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);out=root/'out';out.mkdir()
            with patch.object(subprocess,'run',return_value=P()):x=mod.run_fixtures(root,out)
            self.assertEqual(x['status'],'BLOCKED')
            self.assertEqual(x['returncode'],1)
    def test_timeout_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);out=root/'out';out.mkdir()
            with patch.object(subprocess,'run',side_effect=subprocess.TimeoutExpired(['pytest'],2,output=b'partial',stderr=b'')):
                x=mod.run_fixtures(root,out)
            self.assertEqual(x['returncode'],124)
            self.assertEqual(x['status'],'BLOCKED')

if __name__=='__main__':
    import unittest;unittest.main()
