"""Synthetic fail-closed G2b-03C/04B proof-contract tests, no live authority calls."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import json
import tempfile
import unittest

S=Path(__file__).resolve().parents[3]/'scripts/coordination/control_plane/cf10_g2b03c04b_dynamic_coverage_proof_contract_v0_1.py'
spec=importlib.util.spec_from_file_location('g2b03c04b_test',S)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
HEAD='af03ad2a7aec0f709a77a5259daeabf3cd8bcca8'
REL='scripts/coordination/control_plane/governed_worker_cycle.py'

def prior():
 return {'canonical_head':HEAD,'status':'ATTESTATION_BOUNDARY_GAPS_RECORDED_NON_AUTHORIZING',
         'blockers':[],'authority_granted':False,'independent_dynamic_coverage_verified':False,
         'signature_cryptographically_verified':False,'launch_allowed':False,
         'external_authority_metadata_only':{
             'files':{n:{'status':'METADATA_PRESENT_NON_ATTESTING'} for n in m.TRUST_FILES},
             'directory':{'status':'METADATA_PRESENT_NON_ATTESTING'},
             'external_file_content_read':False,'signature_verified':False,'coverage_attested':False}}

def process():return {'state':'OBSERVED','unreadable_count':0,'observed':[],'absence_of_processes_proven':False}
def static():return {'scan_method':'AST_BOUNDED_NON_EXHAUSTIVE','source_sha256':{REL:'a'*64},
                     'candidates':[],'dynamic_imports_and_callbacks_proven':False,'full_writer_set_proven':False}

class Tests(unittest.TestCase):
 def result(self,mut=None):
  p,proc,s=prior(),process(),static()
  if mut: mut(p,proc,s)
  return m.classify(prior=p,head=HEAD,process=proc,static=s,tracked=(REL,),self_published=True)
 def blocked(self,change,tag):
  x=self.result(change); self.assertEqual(x['status'],'BLOCKED_NON_AUTHORIZING');self.assertIn(tag,x['blockers']);self.assertFalse(x['authority_granted'])
 def test_current_b3_locator_inherited_from_04a(self):
  from pathlib import Path
  from unittest.mock import patch
  root=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
  report=root/'tmp/cf10_g2b03c03b_review_20261029T172009048920Z/report.json'
  # Pure locator check is done in 04A; 04B must call that check, never
  # retain a second frozen hardcoded 2026-10-28-only gate.
  self.assertIn('previous.report_locator_allowed',Path(m.__file__).read_text())
  self.assertNotIn('b3_report!=root/B3_REPORT_REL',Path(m.__file__).read_text())

 def test_contract_ready_but_no_writer_proof(self):
  x=self.result();self.assertEqual(x['status'],'DYNAMIC_COVERAGE_PROOF_CONTRACT_MAPPED_NON_AUTHORIZING');self.assertEqual(x['proof_requirements_satisfied'],0)
  self.assertEqual(len(x['proof_requirements']),8)
  for key in ('all_writer_processes_enrolled','all_writer_entrypoints_verified','running_writer_drain_or_restart_verified','independent_dynamic_coverage_verified','signature_verified','launch_allowed','authority_granted'):
   self.assertIs(x[key],False,key)
 def test_no_process_not_absence_proof(self):
  self.assertIs(self.result()['process_observation']['absence_of_writers_proven'],False)
 def test_observed_pids_not_enrollment_proof(self):
  x=self.result(lambda p,proc,s:proc['observed'].append({'pid':333,'entrypoint':['governed_worker_cycle.py']}))
  self.assertEqual(x['process_observation']['observed_recognized_count'],1)
  self.assertFalse(x['all_writer_processes_enrolled'])
 def test_wrong_prior_head(self):self.blocked(lambda p,proc,s:p.update(canonical_head='f'*40),'SOURCE_HEAD_NOT_BOUND')
 def test_wrong_prior_status(self):self.blocked(lambda p,proc,s:p.update(status='BLOCKED_NON_AUTHORIZING'),'G2B03C04A_METADATA_BOUNDARY_NOT_VERIFIED')
 def test_unverified_predecessor(self):self.blocked(lambda p,proc,s:p.update(independent_dynamic_coverage_verified=True),'G2B03C04A_METADATA_BOUNDARY_NOT_VERIFIED')
 def test_predecessor_authority_forged(self):self.blocked(lambda p,proc,s:p.update(authority_granted=True),'G2B03C04A_METADATA_BOUNDARY_NOT_VERIFIED')
 def test_false_signed_claim(self):self.blocked(lambda p,proc,s:p.update(signature_cryptographically_verified=True),'G2B03C04A_METADATA_BOUNDARY_NOT_VERIFIED')
 def test_metadata_unsafe(self):self.blocked(lambda p,proc,s:p['external_authority_metadata_only']['files']['signed_decision_v0_1.json'].update(status='UNSAFE'),'EXTERNAL_FILE_UNSAFE_OR_UNKNOWN:signed_decision_v0_1.json')
 def test_missing_metadata_is_gap(self):
  x=self.result(lambda p,proc,s:p['external_authority_metadata_only']['files']['signed_decision_v0_1.json'].update(status='MISSING'))
  self.assertEqual(x['status'],'DYNAMIC_COVERAGE_PROOF_CONTRACT_MAPPED_NON_AUTHORIZING')
  self.assertIn('EXTERNAL_EVIDENCE_MISSING:signed_decision_v0_1.json',x['findings'])
 def test_missing_inventory_blocked(self):self.blocked(lambda p,proc,s:p['external_authority_metadata_only']['files'].pop('trust_root_v0_1.json'),'EXTERNAL_TRUST_INVENTORY_DRIFT')
 def test_false_metadata_read(self):self.blocked(lambda p,proc,s:p['external_authority_metadata_only'].update(external_file_content_read=True),'FALSE_EXTERNAL_AUTHORITY_CLAIM')
 def test_process_unreadable(self):self.blocked(lambda p,proc,s:proc.update(unreadable_count=1),'PROCESS_SNAPSHOT_NOT_RELIABLE_FOR_OBSERVATION')
 def test_process_unknown(self):self.blocked(lambda p,proc,s:proc.update(state='UNKNOWN'),'PROCESS_SNAPSHOT_NOT_RELIABLE_FOR_OBSERVATION')
 def test_false_absence_claim(self):self.blocked(lambda p,proc,s:proc.update(absence_of_processes_proven=True),'PROCESS_SNAPSHOT_NOT_RELIABLE_FOR_OBSERVATION')
 def test_false_ast_completeness(self):self.blocked(lambda p,proc,s:s.update(full_writer_set_proven=True),'STATIC_CANDIDATE_SOURCE_PROFILE_INVALID')
 def test_wrong_static_sources(self):self.blocked(lambda p,proc,s:s.update(source_sha256={'other.py':'a'*64}),'STATIC_CANDIDATE_SOURCE_PROFILE_INVALID')
 def test_ast_candidate_collect(self):
  src='from x import append_record\nappend_record(1)\nobject.append_record(2)\n'
  x=m.static_append_candidates({REL:src})
  self.assertEqual([z['line'] for z in x['candidates']],[2,3]);self.assertFalse(x['full_writer_set_proven'])
 def test_ast_syntax_fail_closed(self):
  with self.assertRaises(m.ProofContractBlocked):m.static_append_candidates({REL:'def bad('})
 def test_ast_source_path_reject(self):
  with self.assertRaises(m.ProofContractBlocked):m.static_append_candidates({'/etc/foo.py':'pass'})
 def test_ast_source_too_large(self):
  with self.assertRaises(m.ProofContractBlocked):m.static_append_candidates({REL:'a'*2_000_001})
 def test_report_create_only(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'tmp').mkdir()
   out,hash=m.save_report(root,self.result());self.assertEqual(len(hash),64)
   self.assertEqual((out/'report.json').stat().st_mode&0o777,0o600)
   self.assertFalse(json.loads((out/'report.json').read_text())['authority_granted'])
 def test_report_reject_tmp_symlink(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'real').mkdir();(root/'tmp').symlink_to(root/'real')
   with self.assertRaises(m.ProofContractBlocked):m.save_report(root,self.result())
 def test_invalid_published_flag(self):
  x=m.classify(prior=prior(),head=HEAD,process=process(),static=static(),tracked=(REL,),self_published=False)
  self.assertIn('PROOF_SOURCE_NOT_EXACT_PUBLISHED',x['blockers'])

if __name__=='__main__':unittest.main()
