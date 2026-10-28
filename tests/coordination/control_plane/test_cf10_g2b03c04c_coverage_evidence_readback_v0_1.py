"""04C non-authorizing readback tests; no real s01/worker/ledger/authority calls."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

PATH=Path(__file__).resolve().parents[3]/'scripts/coordination/control_plane/cf10_g2b03c04c_coverage_evidence_readback_v0_1.py'
spec=importlib.util.spec_from_file_location('g2b03c04c_test',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
HEAD='0c07e3ab83f9dd838a9bf19eb6e25f708f812028'
PROOFS=[('COMPLETE_CURRENT_WRITER_ENTRYPOINTS','entrypoints'),
        ('ALL_WRITER_PROCESSES_ENROLLED','enrollment'),
        ('RUNNING_WRITER_RESTART_OR_DRAIN','drain'),
        ('SCHEDULED_MANUAL_REMOTE_WRITERS','scope'),
        ('CANONICAL_LOCK_AND_LEDGER_EXCLUSIVITY','lock'),
        ('INDEPENDENT_DYNAMIC_PROOF','independent'),
        ('SIGNED_COVERAGE_APPROVAL','signed'),
        ('RUNTIME_BINDING_AND_QUARANTINE_ACCEPTANCE','acceptance')]
module='scripts.coordination.control_plane.cf10_g2b03c04b_dynamic_coverage_proof_contract_v0_1'
fake=types.ModuleType(module)
fake.PROOF_REQUIREMENTS=tuple(PROOFS)

def evidence(head=HEAD, count=0):
    return {'source_head':head,'status':'DYNAMIC_COVERAGE_PROOF_CONTRACT_MAPPED_NON_AUTHORIZING',
        'blockers':[],'authority_granted':False,'independent_dynamic_coverage_verified':False,
        'signature_verified':False,'launch_allowed':False,'proof_requirements_satisfied':0,
        'proof_requirements':[{'id':i,'status':'NOT_ATTESTED','required_evidence':v} for i,v in PROOFS],
        'static_inventory':{'candidates':[{'file':'x','line':1}]*4,'full_writer_set_proven':False,'source_sha256':{'x':'b'*64}},
        'process_observation':{'observed_recognized_count':count,'unreadable_count':0,
            'absence_of_writers_proven':False,'scan_is_complete_dynamic_attestation':False},'findings':[]}

class Tests(unittest.TestCase):
    def outcome(self,archived=None,fresh=None,head=HEAD,self_published=True):
        return m.classify(archived=archived or evidence(),fresh=fresh or evidence(),head=head,
                          self_published=self_published,proof_requirements=tuple(PROOFS))
    def test_positive_readback_still_all_eight_unattested(self):
        r=self.outcome()
        self.assertEqual(r['status'],'INDEPENDENT_EVIDENCE_READBACK_READY_FOR_OPERATOR_PROOFS_NON_AUTHORIZING')
        self.assertEqual(len(r['operator_proof_intake']),8)
        self.assertEqual(r['frozen_static_candidate_count'],4)
        self.assertEqual(r['proofs_attested'],0)
        for key in ('independent_dynamic_coverage_verified','launch_allowed','signature_cryptographically_verified','authority_granted','ledger_append_allowed','worker_launched'):
            self.assertIs(r[key],False)
    def test_snapshot_count_change_is_finding_not_authority(self):
        r=self.outcome(fresh=evidence(count=5))
        self.assertIn('PROCESS_COUNT_CHANGED_SINCE_04B_REQUIRES_OPERATOR_REVIEW',r['findings'])
        self.assertFalse(r['writer_process_enrollment_verified'])
    def test_prior_head_drift_blocks(self):
        r=self.outcome(archived=evidence(head='a'*40))
        self.assertIn('PRIOR_HEAD_NOT_PINNED',r['blockers'])
    def test_invalid_current_head_blocks(self):
        self.assertIn('PRIOR_HEAD_NOT_PINNED',self.outcome(head='broken')['blockers'])
    def test_unpublished_self_blocks(self):
        self.assertIn('SELF_SOURCE_NOT_PUBLISHED',self.outcome(self_published=False)['blockers'])
    def test_prior_wrong_state_blocks(self):
        x=evidence();x['status']='BLOCKED_NON_AUTHORIZING'
        self.assertIn('ARCHIVED_04B_PROOF_CONTRACT_INVALID',self.outcome(archived=x)['blockers'])
    def test_fresh_wrong_state_blocks(self):
        x=evidence();x['status']='BLOCKED_NON_AUTHORIZING'
        self.assertIn('FRESH_04B_PROOF_CONTRACT_INVALID',self.outcome(fresh=x)['blockers'])
    def test_prior_false_authority_blocks(self):
        x=evidence();x['authority_granted']=True
        self.assertIn('ARCHIVED_04B_PROOF_CONTRACT_INVALID',self.outcome(archived=x)['blockers'])
    def test_fresh_false_signature_blocks(self):
        x=evidence();x['signature_verified']=True
        self.assertIn('FRESH_04B_PROOF_CONTRACT_INVALID',self.outcome(fresh=x)['blockers'])
    def test_archive_fake_coverage_blocks(self):
        x=evidence();x['independent_dynamic_coverage_verified']=True
        self.assertIn('ARCHIVED_04B_PROOF_CONTRACT_INVALID',self.outcome(archived=x)['blockers'])
    def test_fresh_wrong_proof_count_blocks(self):
        x=evidence();x['proof_requirements_satisfied']=1
        self.assertIn('FRESH_04B_PROOF_CONTRACT_INVALID',self.outcome(fresh=x)['blockers'])
    def test_missing_proof_blocks(self):
        x=evidence();x['proof_requirements'].pop()
        self.assertIn('ARCHIVED_REQUIREMENTS_MISMATCH',self.outcome(archived=x)['blockers'])
    def test_unverified_status_tamper_blocks(self):
        x=evidence();x['proof_requirements'][2]['status']='ATTESTED'
        self.assertIn('ARCHIVED_REQUIREMENTS_MISMATCH',self.outcome(archived=x)['blockers'])
    def test_wrong_evidence_description_blocks(self):
        x=evidence();x['proof_requirements'][0]['required_evidence']='test says pass'
        self.assertIn('ARCHIVED_REQUIREMENTS_MISMATCH',self.outcome(archived=x)['blockers'])
    def test_static_source_drift_blocks(self):
        x=evidence();x['static_inventory']['source_sha256']['x']='c'*64
        self.assertIn('STATIC_SOURCE_OR_CANDIDATE_DRIFT',self.outcome(fresh=x)['blockers'])
    def test_static_false_completeness_blocks(self):
        x=evidence();x['static_inventory']['full_writer_set_proven']=True
        self.assertIn('STATIC_SOURCE_OR_CANDIDATE_DRIFT',self.outcome(fresh=x)['blockers'])
    def test_false_process_absence_blocks(self):
        x=evidence();x['process_observation']['absence_of_writers_proven']=True
        self.assertIn('PROCESS_OBSERVATION_SEMANTICS_INVALID',self.outcome(fresh=x)['blockers'])
    def test_unreadable_process_blocks(self):
        x=evidence();x['process_observation']['unreadable_count']=1
        self.assertIn('PROCESS_OBSERVATION_SEMANTICS_INVALID',self.outcome(fresh=x)['blockers'])
    def test_report_path_not_exact(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(m.EvidenceReadbackBlocked):m.load_prior(Path(t),Path(t)/'other.json',m.PRIOR_SHA256)
    def test_report_sha_not_pinned(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(m.EvidenceReadbackBlocked):m.load_prior(Path(t),Path(t)/m.PRIOR_REPORT_REL,'f'*64)
    def test_report_symlink_refused(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);a=root/'a';a.write_text('{}');b=root/'b';b.symlink_to(a)
            with self.assertRaises(m.EvidenceReadbackBlocked):m.private_read(b)
    def test_report_group_writable_refused(self):
        if os.getuid()!=0:
            self.skipTest('root ownership is required')
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);os.chmod(root,0o700)
            p=root/'x';p.write_text('x');os.chmod(p,0o660)
            with self.assertRaises(m.EvidenceReadbackBlocked):m.private_read(p)
    def test_report_create_only(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'tmp').mkdir()
            out,d=m.save(root,self.outcome())
            self.assertEqual(len(d),64)
            self.assertEqual((out/'report.json').stat().st_mode&0o777,0o600)
            self.assertFalse(json.loads((out/'report.json').read_text())['authority_granted'])
    def test_report_tmp_symlink_denied(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'real').mkdir();(root/'tmp').symlink_to(root/'real')
            with self.assertRaises(m.EvidenceReadbackBlocked):m.save(root,self.outcome())

if __name__=='__main__':unittest.main()
