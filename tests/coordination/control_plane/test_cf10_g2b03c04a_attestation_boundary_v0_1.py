"""Pure metadata-only governance tests. Does not read external trust files."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SOURCE=Path(__file__).resolve().parents[3]/'scripts/coordination/control_plane/cf10_g2b03c04a_attestation_boundary_v0_1.py'
spec=importlib.util.spec_from_file_location('cf10_g2b03c04a_candidate',SOURCE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
HEAD='d72357ebf51877ddf4ed5e89623e7f1d90f96913'


def prior():
    return {'source_head':HEAD,'status':'VERSIONED_BINDING_CANDIDATE_REVIEW_REQUIRED_NON_AUTHORIZING',
            'mode':'inspect','blockers':[],'b3_regression_passed_count':62,
            'launch_allowed':False,'independent_dynamic_coverage_verified':False,
            'runtime_binding_authorized':False,'authority_granted':False}

def metadata():
    return {'directory':{'status':'METADATA_PRESENT_NON_ATTESTING'},
            'files':{n:{'status':'MISSING'} for n in m.TRUST_FILES},
            'external_file_content_read':False,'signature_verified':False,'coverage_attested':False}

class BoundaryTests(unittest.TestCase):
    def result(self,pm=None,mm=None,published=True,head=HEAD):
        p=prior(); d=metadata()
        if pm: pm(p)
        if mm: mm(d)
        return m.classify(prior=p,head=head,metadata=d,source_published=published)

    def test_missing_all_files_is_reportable_but_no_authority(self):
        r=self.result()
        self.assertEqual(r['status'],'ATTESTATION_BOUNDARY_GAPS_RECORDED_NON_AUTHORIZING')
        self.assertGreaterEqual(len(r['required_evidence_gaps']),8)
        for field in ('signature_cryptographically_verified','independent_dynamic_coverage_verified',
                      'writer_enrollment_verified','worker_drain_or_restart_verified','launch_allowed',
                      'ledger_mutated','worker_launched','authority_granted'):
            self.assertIs(r[field],False)

    def test_metadata_present_is_still_non_attesting(self):
        r=self.result(mm=lambda x:x['files'].update({n:{'status':'METADATA_PRESENT_NON_ATTESTING'} for n in m.TRUST_FILES}))
        self.assertFalse(r['current_signed_head_approved'])
        self.assertFalse(r['independent_dynamic_coverage_verified'])

    def test_wrong_head_blocks(self):
        self.assertIn('CANONICAL_HEAD_OR_BINDING_DRIFT',self.result(head='f'*40)['blockers'])

    def test_head_drift_blocks(self):
        self.assertIn('CANONICAL_HEAD_OR_BINDING_DRIFT',self.result(pm=lambda x:x.update(source_head='e'*40))['blockers'])

    def test_unpublished_source_blocks(self):
        self.assertIn('SELF_SOURCE_NOT_PUBLISHED',self.result(published=False)['blockers'])

    def test_bad_predecessor_status_blocks(self):
        self.assertIn('VERSIONED_BINDING_CANDIDATE_NOT_VERIFIED',self.result(pm=lambda x:x.update(status='BLOCKED'))['blockers'])

    def test_launch_mode_predecessor_denied(self):
        self.assertIn('VERSIONED_BINDING_CANDIDATE_NOT_VERIFIED',self.result(pm=lambda x:x.update(mode='launch-preflight'))['blockers'])

    def test_fake_positive_predecessor_authority_denied(self):
        self.assertIn('VERSIONED_BINDING_CANDIDATE_NOT_VERIFIED',self.result(pm=lambda x:x.update(authority_granted=True))['blockers'])

    def test_fake_positive_predecessor_dynamic_denied(self):
        self.assertIn('VERSIONED_BINDING_CANDIDATE_NOT_VERIFIED',self.result(pm=lambda x:x.update(independent_dynamic_coverage_verified=True))['blockers'])

    def test_wrong_b3_count_denied(self):
        self.assertIn('VERSIONED_BINDING_CANDIDATE_NOT_VERIFIED',self.result(pm=lambda x:x.update(b3_regression_passed_count=61))['blockers'])

    def test_unsafe_metadata_denied(self):
        r=self.result(mm=lambda x:x['files']['signed_decision_v0_1.json'].update(status='UNSAFE'))
        self.assertEqual(r['status'],'BLOCKED_NON_AUTHORIZING')
        self.assertIn('EXTERNAL_AUTHORITY_PATH_UNSAFE',r['blockers'])

    def test_missing_inventory_denied(self):
        self.assertIn('EXTERNAL_TRUST_FILE_INVENTORY_INCOMPLETE',
            self.result(mm=lambda x:x['files'].pop('trust_root_v0_1.json'))['blockers'])

    def test_false_content_read_denied(self):
        self.assertIn('FALSE_EXTERNAL_ATTESTATION_CLAIM',self.result(mm=lambda x:x.update(external_file_content_read=True))['blockers'])

    def test_false_signed_claim_denied(self):
        self.assertIn('FALSE_EXTERNAL_ATTESTATION_CLAIM',self.result(mm=lambda x:x.update(signature_verified=True))['blockers'])

    def test_false_coverage_claim_denied(self):
        self.assertIn('FALSE_EXTERNAL_ATTESTATION_CLAIM',self.result(mm=lambda x:x.update(coverage_attested=True))['blockers'])

    def test_relative_path_denied(self):
        self.assertEqual(m.path_metadata(Path('relative.json'))['status'],'UNSAFE')

    def test_real_symlink_denied_even_if_target_missing(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t)
            (base/'link').symlink_to('/etc')
            self.assertEqual(m.path_metadata(base/'link'/'forprint').get('status'),'UNSAFE')

    def test_no_payload_access_from_metadata_routine(self):
        with mock.patch.object(Path,'open',side_effect=AssertionError('external opened')):
            r=m.authority_metadata(root=Path('/nonexistent-forprint-metadata-directory'))
            self.assertFalse(r['external_file_content_read'])

    def test_report_create_only_and_hashes(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'tmp').mkdir()
            folder,h=m.save_report(root,self.result())
            self.assertEqual(len(h),64)
            self.assertEqual((folder/'report.json').stat().st_mode & 0o777,0o600)
            self.assertTrue((folder/'SHA256SUMS').is_file())
            self.assertEqual(json.loads((folder/'report.json').read_text())['authority_granted'],False)

    def test_report_rejects_symlink_tmp(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'real').mkdir();(root/'tmp').symlink_to(root/'real')
            with self.assertRaises(m.BoundaryBlocked):m.save_report(root,self.result())

if __name__=='__main__':unittest.main()
