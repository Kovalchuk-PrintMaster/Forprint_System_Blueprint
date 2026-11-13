"""Synthetic G2b02 planning tests; no Gate verifier or real operator state executed."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.coordination.control_plane import cf10_g2b02_binding_plan_v0_1 as m

GATE='\n'.join(('PLAN_MUST_BE_REGULAR_PROJECT_TMP_FILE',
    'expected_parent = (root / "tmp").resolve()',
    'file.parent.resolve() != expected_parent', 'def verify_coverage(',
    'gate.validate_coverage(doc)'))
WRITER='\n'.join(('def verify_signed_decision(', 'def validate_coverage(',
    'signed_decision_v0_1.json', 'writer_coverage_v0_1.json',
    "'external_approval'",'coverage_sha256'))
V1='coverage_path.parent.resolve() != (gate_root / "tmp").resolve()\nCOVERAGE_EVIDENCE_NOT_FROM_GATE_TMP'
V2='s01_writer_runtime_binding_v0_1 as inventory\nSIGNED_RUNTIME_EXTENSION_MISSING'

def audit(status='INVENTORY_REVIEW_REQUIRED_NON_AUTHORIZING'):
    checks=[{'id':n,'status':'PASS','detail':'ok'} for n in m.NEEDED]
    checks.extend(({'id':'stable_coverage_target','status':'MISSING','detail':'not_rebound'},
                   {'id':'legacy_coverage_path_dependency','status':'REVIEW','detail':'old_tmp'},
                   {'id':'external_signed_decision','status':'REVIEW','detail':'metadata_only'}))
    return {'status':status,'checks':checks,'coverage_evidence_rebound':False,'new_signed_head_authorized':False}

def sources():
    return {'gate_verifier':m.gate_contract(GATE),'writer_activation':m.writer_contract(WRITER),
            'runtime_binding':{'status':'PASS','finding':'RUNTIME_V1_REQUIRES_GATE_TMP_V2_DEPENDS_ON_V1'}}

class G2b02Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='g2b02_synth_')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_01_gate_pinned_legacy_constraint(self):
        r=m.gate_contract(GATE);self.assertEqual(r['status'],'PASS')
        self.assertIs(r['supports_stable_evidence_path'],False)

    def test_02_gate_missing_anchor_blocked(self):
        self.assertEqual(m.gate_contract(GATE.replace('PLAN_MUST_BE_REGULAR_PROJECT_TMP_FILE',''))['status'],'BLOCKED')

    def test_03_writer_signature_independent(self):
        r=m.writer_contract(WRITER);self.assertEqual(r['status'],'PASS')
        self.assertIs(r['signature_verified_by_this_plan'],False)

    def test_04_writer_missing_anchor_blocked(self):
        self.assertEqual(m.writer_contract(WRITER.replace('coverage_sha256',''))['status'],'BLOCKED')

    def test_05_runtime_legacy_constraint(self):
        with mock.patch.object(m.inventory,'exact_published_file',side_effect=[V1,V2]):
            self.assertEqual(m.runtime_contract(self.root,'0'*40)['status'],'PASS')

    def test_06_runtime_binding_drift_blocked(self):
        with mock.patch.object(m.inventory,'exact_published_file',side_effect=[V1,'invalid']):
            self.assertEqual(m.runtime_contract(self.root,'0'*40)['status'],'BLOCKED')

    def test_07_runtime_published_bytes_missing(self):
        with mock.patch.object(m.inventory,'exact_published_file',side_effect=m.inventory.ReviewBlocked('missing')):
            self.assertEqual(m.runtime_contract(self.root,'0'*40)['status'],'BLOCKED')

    def test_08_all_observations_result_is_still_review(self):
        r=m.plan_from_observations(audit(),sources())
        self.assertEqual(r['status'],'SUCCESSOR_GATE_DESIGN_REVIEW_REQUIRED_NON_AUTHORIZING')
        self.assertEqual(r['blockers'],[])
        self.assertFalse(r['authority_granted'])
        self.assertEqual(r['recommended_architecture']['strategy'],'NEW_INDEPENDENT_GATE_VERIFIER_RELEASE_REQUIRED')

    def test_09_missing_historical_proof_blocks(self):
        a=audit();next(x for x in a['checks'] if x['id']=='historical_coverage')['status']='MISSING'
        self.assertIn('REQUIRED_G2B01_PASS_MISSING:historical_coverage',m.plan_from_observations(a,sources())['blockers'])

    def test_10_bad_historical_sha_blocks(self):
        a=audit('BLOCKED_NON_AUTHORIZING');next(x for x in a['checks'] if x['id']=='historical_coverage')['status']='BLOCKED'
        self.assertEqual(m.plan_from_observations(a,sources())['status'],'BLOCKED_NON_AUTHORIZING')

    def test_11_stable_evidence_bad_bytes_blocks(self):
        a=audit();next(x for x in a['checks'] if x['id']=='stable_coverage_target')['status']='BLOCKED'
        self.assertIn('STABLE_EVIDENCE_TARGET_UNEXPECTED',m.plan_from_observations(a,sources())['blockers'])

    def test_12_unverified_external_decision_blocks(self):
        a=audit();next(x for x in a['checks'] if x['id']=='external_signed_decision')['status']='MISSING'
        self.assertIn('EXTERNAL_SIGNED_DECISION_REQUIRES_METADATA_REVIEW',m.plan_from_observations(a,sources())['blockers'])

    def test_13_legacy_path_profile_changed_blocks(self):
        a=audit();next(x for x in a['checks'] if x['id']=='legacy_coverage_path_dependency')['status']='PASS'
        self.assertIn('LEGACY_BINDING_PROFILE_UNEXPECTED',m.plan_from_observations(a,sources())['blockers'])

    def test_14_untrusted_authority_claim_blocks(self):
        a=audit();a['coverage_evidence_rebound']=True
        self.assertEqual(m.plan_from_observations(a,sources())['status'],'BLOCKED_NON_AUTHORIZING')

    def test_15_source_drift_blocks(self):
        s=sources();s['gate_verifier']['status']='BLOCKED'
        self.assertIn('PINNED_OR_RUNTIME_SOURCE_UNVERIFIED:gate_verifier',m.plan_from_observations(audit(),s)['blockers'])

    def test_16_scratch_only_no_generated_output(self):
        (self.root/'tmp').mkdir()
        out=m.safe_save(self.root,m.plan_from_observations(audit(),sources()))
        files=sorted(p.name for p in out.iterdir())
        self.assertEqual(files,['SHA256SUMS','report.json','summary.txt'])
        self.assertEqual((out/'report.json').stat().st_mode & 0o777,0o600)
        self.assertFalse((self.root/'generated').exists())
        with (out/'SHA256SUMS').open() as f:
            for line in f:
                h,n=line.split();self.assertEqual(hashlib.sha256((out/n).read_bytes()).hexdigest(),h)

    def test_17_symlink_scratch_fail_closed(self):
        (self.root/'tmp').symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(m.ReviewBlocked):m.safe_save(self.root,{'status':'x','blockers':[]})

    def test_18_pinned_git_blob_oid_drift_rejected(self):
        with mock.patch.object(m.releases,'git',return_value=b'imposter'):
            with self.assertRaises(m.ReviewBlocked):m.verified_git_blob(self.root,'gate')

    def test_19_pinned_git_blob_match(self):
        raw=GATE.encode()
        old=m.releases.RELEASES['gate']['git_blob_oid']
        with mock.patch.object(m.releases,'git',return_value=raw),mock.patch.dict(m.releases.RELEASES['gate'],{'git_blob_oid':m.releases.blob_oid(raw)}):
            self.assertEqual(m.verified_git_blob(self.root,'gate'),GATE)
        self.assertEqual(m.releases.RELEASES['gate']['git_blob_oid'],old)

    def test_20_no_verifier_execution_on_static_source_review(self):
        with mock.patch.object(m,'verified_git_blob',side_effect=[GATE,WRITER]):
            with mock.patch.object(m.inventory,'exact_published_file',side_effect=[V1,V2]):
                s=m.independent_sources(self.root,'0'*40)
        self.assertTrue(all(r['status']=='PASS' for r in s.values()))

    def test_21_no_mutation_in_plan(self):
        r=m.plan_from_observations(audit(),sources())
        for key in ('signature_verified','signature_payload_read','independent_verifier_executed',
                    'historical_evidence_copied','vault_mutated','git_mutated','worker_launched',
                    'signed_renewal_performed','authority_granted'):
            self.assertIs(r[key],False,key)

if __name__=='__main__':unittest.main()
