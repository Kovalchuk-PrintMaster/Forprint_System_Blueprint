"""G2b03C/02 synthetic non-authorizing Gate negative fixtures; no live s01 state."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

S=Path(__file__).resolve().parents[3] / 'scripts/coordination/control_plane/cf10_g2b03c02_successor_gate_v0_1.py'
spec=importlib.util.spec_from_file_location('g2b03c02_candidate',S)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
HEAD='b0d952403c4688b8ea9ea7df06e1d06e744c3d6f'
SHA='15bb96b3fdb87186d8337dfa17391bfd5a5a951e2faae34c8c671734d4027b71'
TARGET='/srv/software_development/forprint-releases/cf10/evidence/cf10_writer_coverage_gate3d90143_170494.json'
WRITERS=('a.py','b.py')

def directory():return {'state':'DIRECTORY','uid':0,'group_writable':False,'other_writable':False}
def fixture():
    return (
      {'status':'DESIGN_REVIEW_READY_NON_AUTHORIZING','blockers':[], 'source_head':HEAD,
       'external_evidence_path':TARGET,'historical_coverage_sha256':SHA},
      {'state':'PROVENANCE_CANDIDATE_VERIFIED_NON_AUTHORIZING','blockers':[],
       'authority_granted':False,'successor_dynamic_coverage_verified':False,
       'external_candidate_check':{'status':'PASS','path':TARGET,'sha256':SHA}},
      {'host':'s01','deployment_root':'/srv/software_development/forprint-project/forprint_system_blueprint',
       'deployment_head':HEAD,
       'canonical_ledger':directory(),'canonical_parent':directory(),
       'coordination_ancestor':directory(),'continuity_ancestor':directory(),
       'mount':{'state':'OBSERVED','network_or_fuse_surface':False},
       'acl':{'state':'OBSERVED'},
       'processes':{'state':'OBSERVED','observed':[],'unreadable_count':0,'absence_of_processes_proven':False},
       'tracked_writers':WRITERS,'writer_source_comparison':{x:True for x in WRITERS},
       'release_checks':{'gate':'PASS','writer':'PASS'},
       'independent_authority':{x:'NOT_VERIFIED' for x in ('signed_decision','writer_enrollment','independent_operator_review','runtime_binding')}})

class Tests(unittest.TestCase):
    def review(self,modifier=None):
        s,p,l=fixture()
        if modifier: modifier(s,p,l)
        return mod.classify(source=s,provenance=p,live=l,expected_head=HEAD)
    def block(self,modification,reason):
        result=self.review(modification)
        self.assertEqual(result['status'],'BLOCKED_NON_AUTHORIZING')
        self.assertIn(reason,result['blockers'])
        self.assertIs(result['authority_granted'],False)
        self.assertIs(result['dynamic_coverage_verified'],False)
    def test_candidate_ready_for_review_not_attestation(self):
        r=self.review()
        self.assertEqual(r['status'],'LIVE_OBSERVATION_REVIEW_REQUIRED_NON_AUTHORIZING')
        for key in ('authority_granted','worker_launched','dynamic_coverage_verified','deployment_coverage_verified','signed_operator_approval_verified','make_launch_gate_unquarantined','ledger_mutated'):
            self.assertIs(r[key],False)
    def test_wrong_design_head(self):
        self.block(lambda s,p,l:s.update(source_head='0'*40),'SOURCE_READINESS_NOT_VERIFIED_FOR_HEAD')
    def test_bad_design_status(self):
        self.block(lambda s,p,l:s.update(status='BLOCKED_NON_AUTHORIZING'),'SOURCE_READINESS_NOT_VERIFIED_FOR_HEAD')
    def test_missing_external_candidate(self):
        self.block(lambda s,p,l:p.update(state='EXTERNAL_CANDIDATE_MISSING_NON_AUTHORIZING'),'EXTERNAL_PROVENANCE_NOT_VERIFIED')
    def test_candidate_sha_drift(self):
        self.block(lambda s,p,l:p['external_candidate_check'].update(sha256='0'*64),'CANDIDATE_BYTES_PATH_OR_PINS_DRIFT')
    def test_candidate_path_drift(self):
        self.block(lambda s,p,l:p['external_candidate_check'].update(path='/tmp/evil.json'),'CANDIDATE_BYTES_PATH_OR_PINS_DRIFT')
    def test_provenance_false_authority(self):
        self.block(lambda s,p,l:p.update(authority_granted=True),'EXTERNAL_PROVENANCE_NOT_VERIFIED')
    def test_legacy_false_dynamic(self):
        self.block(lambda s,p,l:p.update(successor_dynamic_coverage_verified=True),'EXTERNAL_PROVENANCE_NOT_VERIFIED')
    def test_wrong_host(self):
        self.block(lambda s,p,l:l.update(host='s02'),'S01_DEPLOYMENT_IDENTITY_UNVERIFIED')
    def test_head_drift(self):
        self.block(lambda s,p,l:l.update(deployment_head='f'*40),'RUNTIME_DEPLOYMENT_HEAD_DRIFT')
    def test_symlink_canonical(self):
        self.block(lambda s,p,l:l['canonical_ledger'].update(state='SYMLINK'),'CANONICAL_LEDGER_DAC_UNSAFE_OR_NOT_OBSERVED')
    def test_unsafe_dac(self):
        self.block(lambda s,p,l:l['canonical_ledger'].update(group_writable=True),'CANONICAL_LEDGER_DAC_UNSAFE_OR_NOT_OBSERVED')
    def test_unowned_parent(self):
        self.block(lambda s,p,l:l['canonical_parent'].update(uid=1000),'CANONICAL_PARENT_DAC_UNSAFE_OR_NOT_OBSERVED')
    def test_network_mount(self):
        self.block(lambda s,p,l:l['mount'].update(network_or_fuse_surface=True),'LEDGER_MOUNT_UNSAFE_OR_UNKNOWN')
    def test_unreadable_process(self):
        self.block(lambda s,p,l:l['processes'].update(unreadable_count=1),'PROCESS_OBSERVATION_UNRELIABLE')
    def test_false_process_absence(self):
        self.block(lambda s,p,l:l['processes'].update(absence_of_processes_proven=True),'PROCESS_PROOF_SEMANTICS_DRIFT')
    def test_wrong_gate_pin(self):
        self.block(lambda s,p,l:l['release_checks'].update(gate='BLOCKED'),'PINNED_RELEASE_NOT_VERIFIED:gate')
    def test_writer_inventory_incomplete(self):
        self.block(lambda s,p,l:l['writer_source_comparison'].pop('a.py'),'TRACKED_WRITER_INVENTORY_INCOMPLETE')
    def test_writer_source_unreadable(self):
        self.block(lambda s,p,l:l['writer_source_comparison'].update({'a.py':None}),'WRITER_SOURCE_UNREADABLE:a.py')
    def test_known_writer_diff_review_not_attestation(self):
        r=self.review(lambda s,p,l:l['writer_source_comparison'].update({'a.py':False}))
        self.assertEqual(r['status'],'LIVE_OBSERVATION_REVIEW_REQUIRED_NON_AUTHORIZING')
        self.assertIn('DEPLOYMENT_WRITER_DIFF_REQUIRES_REVIEW:a.py',r['review_findings'])
    def test_missing_acl_review(self):
        r=self.review(lambda s,p,l:l['acl'].update(state='NOT_INSPECTED_GETFACL_UNAVAILABLE'))
        self.assertIn('LEDGER_ACL_NOT_INDEPENDENTLY_VERIFIED',r['review_findings'])
        self.assertFalse(r['authority_granted'])
    def test_no_fake_signed_approval(self):
        self.block(lambda s,p,l:l['independent_authority'].update(signed_decision='SIGNED_PASS'),'AUTHORITY_SEMANTICS_DRIFT:signed_decision')
    def test_expired_signature_not_accepted(self):
        # The candidate may neither read nor validate signatures; any injected
        # "expired"/"valid" attestation is blocked, requiring independent Gate.
        self.block(lambda s,p,l:l['independent_authority'].update(signed_decision='EXPIRED'),'AUTHORITY_SEMANTICS_DRIFT:signed_decision')
    def test_report_creates_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'tmp').mkdir()
            folder,digest=mod.save_report(root,self.review())
            self.assertTrue((folder/'report.json').exists())
            self.assertTrue((folder/'SHA256SUMS').exists())
            self.assertEqual((folder/'report.json').stat().st_mode & 0o777,0o600)
            self.assertEqual(len(digest),64)
    def test_report_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'real').mkdir();(root/'tmp').symlink_to(root/'real')
            with self.assertRaises(mod.GateBlocked):mod.save_report(root,self.review())

if __name__=='__main__':unittest.main()
