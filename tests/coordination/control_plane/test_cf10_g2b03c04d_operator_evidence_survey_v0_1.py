"""04D synthetic non-authorizing controls, no real s01, trust files, or Worker calls."""
from __future__ import annotations
import importlib.util,json,os
from pathlib import Path
import tempfile
import unittest

SOURCE=Path(__file__).resolve().parents[3]/'scripts/coordination/control_plane/cf10_g2b03c04d_operator_evidence_survey_v0_1.py'
spec=importlib.util.spec_from_file_location('g2b03c04d_synthetic',SOURCE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
HEAD='0c6dfc9fe8ce614739b162a118b0802fc573a4bf'
REQ=(('COMPLETE_CURRENT_WRITER_ENTRYPOINTS','source'),('ALL_WRITER_PROCESSES_ENROLLED','process'),
 ('RUNNING_WRITER_RESTART_OR_DRAIN','restart'),('SCHEDULED_MANUAL_REMOTE_WRITERS','scope'),
 ('CANONICAL_LOCK_AND_LEDGER_EXCLUSIVITY','lock'),('INDEPENDENT_DYNAMIC_PROOF','independent'),
 ('SIGNED_COVERAGE_APPROVAL','signature'),('RUNTIME_BINDING_AND_QUARANTINE_ACCEPTANCE','make'))

def predecessor():
 return {'schema_version':'cf10_g2b03c04c_evidence_readback_v0_1',
 'source_head':HEAD,'status':'INDEPENDENT_EVIDENCE_READBACK_READY_FOR_OPERATOR_PROOFS_NON_AUTHORIZING',
 'blockers':[],'proofs_submitted':0,'proofs_attested':0,'authority_granted':False,
 'independent_dynamic_coverage_verified':False,'launch_allowed':False,
 'operator_proof_intake':[{'id':key,'operator_evidence_required':description,'state':'NOT_SUBMITTED',
 'independent_evidence_id':None,'evidence_sha256':None,'review_authority':'NOT_VERIFIED'} for key,description in REQ]}

def schedule():return {'matches':[],'findings':[],'full_scheduler_scope_proven':False,
 'remote_or_manual_writers_proven':False,'external_authority_payloads_read':False,
 'counts':{'files_read':0,'links_skipped':0,'bytes_read':0,'out_of_scope_skipped':0}}
def live():return {'processes':{'state':'OBSERVED','unreadable_count':0,'observed':[],
 'absence_of_processes_proven':False},'ledger':{'state':'DIRECTORY'},
 'mount':{'state':'OBSERVED','network_or_fuse_surface':False},'acl':{'state':'OBSERVED'}}

class TestSurvey(unittest.TestCase):
 def result(self,p=None,s=None,l=None,head=HEAD,source=True):
  return m.classify(prior=predecessor() if p is None else p,head=head,requirements=REQ,
      schedule=schedule() if s is None else s,live=live() if l is None else l,source_ok=source)
 def error(self,p=None,s=None,l=None,head=HEAD,source=True,blocker=None):
  r=self.result(p,s,l,head,source)
  self.assertEqual(r['status'],'BLOCKED_NON_AUTHORIZING');self.assertIn(blocker,r['blockers'])
  self.assertFalse(r['authority_granted']);self.assertFalse(r['launch_allowed'])
 def test_success_only_non_authorizing_capture(self):
  v=self.result();self.assertEqual(v['status'],'OPERATOR_EVIDENCE_SURVEY_CAPTURED_WITH_GAPS_NON_AUTHORIZING')
  self.assertEqual(v['proof_rows'],8);self.assertEqual(v['proofs_submitted'],0)
  for key in ('proofs_attested','independent_dynamic_coverage_verified','all_writer_processes_enrolled',
     'writer_drain_restart_verified','signature_cryptographically_verified','runtime_binding_authorized',
     'launch_allowed','ledger_append_allowed','worker_launched','authority_granted'):
   self.assertIn(v[key],[0,False])
 def test_template_exact_count_and_no_evidence(self):
  rows=self.result()['proof_template']['requirements']
  self.assertEqual([a['id'] for a in rows],[x[0] for x in REQ])
  self.assertTrue(all(a['state']=='NOT_SUBMITTED' and a['evidence_reference'] is None and
      a['review_state']=='NOT_VERIFIED' for a in rows))
 def test_zero_process_does_not_prove_coverage(self):
  self.assertFalse(self.result()['all_writer_processes_enrolled'])
 def test_multiple_observed_processes_still_no_authority(self):
  x=live();x['processes']['observed']=[{'pid':n,'entrypoint':['x']} for n in (99,100)]
  self.assertFalse(self.result(l=x)['independent_dynamic_coverage_verified'])
 def test_previous_head_mismatch(self):
  x=predecessor();x['source_head']='f'*40
  self.error(p=x,blocker='FROZEN_04C_PREDECESSOR_NOT_VERIFIED')
 def test_wrong_status(self):
  x=predecessor();x['status']='ATTESTED'
  self.error(p=x,blocker='FROZEN_04C_PREDECESSOR_NOT_VERIFIED')
 def test_forged_prior_authority(self):
  x=predecessor();x['authority_granted']=True
  self.error(p=x,blocker='FROZEN_04C_PREDECESSOR_NOT_VERIFIED')
 def test_forged_prior_coverage(self):
  x=predecessor();x['independent_dynamic_coverage_verified']=True
  self.error(p=x,blocker='FROZEN_04C_PREDECESSOR_NOT_VERIFIED')
 def test_prior_submitted_unsupported(self):
  x=predecessor();x['proofs_submitted']=1
  self.error(p=x,blocker='FROZEN_04C_PREDECESSOR_NOT_VERIFIED')
 def test_missing_proof(self):
  x=predecessor();x['operator_proof_intake'].pop()
  self.error(p=x,blocker='04C_OPERATOR_PROOF_MATRIX_DRIFT')
 def test_reordered_proof(self):
  x=predecessor();x['operator_proof_intake'].reverse()
  self.error(p=x,blocker='04C_OPERATOR_PROOF_MATRIX_DRIFT')
 def test_forged_proof_status(self):
  x=predecessor();x['operator_proof_intake'][0]['state']='ATTESTED'
  self.error(p=x,blocker='04C_OPERATOR_PROOF_MATRIX_DRIFT')
 def test_fake_proof_reference(self):
  x=predecessor();x['operator_proof_intake'][0]['independent_evidence_id']='forged'
  self.error(p=x,blocker='04C_OPERATOR_PROOF_MATRIX_DRIFT')
 def test_invalid_current_head(self):
  self.error(head='invalid',blocker='CURRENT_SOURCE_PUBLICATION_UNVERIFIED')
 def test_self_not_published(self):
  self.error(source=False,blocker='CURRENT_SOURCE_PUBLICATION_UNVERIFIED')
 def test_schedule_false_completeness(self):
  x=schedule();x['full_scheduler_scope_proven']=True
  self.error(s=x,blocker='SCHEDULE_SURVEY_SEMANTICS_UNSAFE')
 def test_schedule_claim_reads_trust(self):
  x=schedule();x['external_authority_payloads_read']=True
  self.error(s=x,blocker='SCHEDULE_SURVEY_SEMANTICS_UNSAFE')
 def test_process_unreadable(self):
  x=live();x['processes']['unreadable_count']=1
  self.error(l=x,blocker='LOCAL_RUNTIME_OBSERVATION_UNRELIABLE')
 def test_process_false_absence(self):
  x=live();x['processes']['absence_of_processes_proven']=True
  self.error(l=x,blocker='LOCAL_RUNTIME_OBSERVATION_UNRELIABLE')
 def test_wrong_mount(self):
  x=live();x['mount']['network_or_fuse_surface']=True
  self.error(l=x,blocker='LOCAL_RUNTIME_OBSERVATION_UNRELIABLE')
 def test_schedule_read_only_matches_and_exclusion(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);systemd=base/'systemd';systemd.mkdir();cron=base/'cron';cron.mkdir()
   (systemd/'active.service').write_text('ExecStart=/usr/bin/python governed_worker_cycle.py\n')
   (systemd/'forprint-google-drive-backup.service').write_text('governed_worker_cycle\n')
   (systemd/'unrelated.service').write_text('ExecStart=/bin/true\n')
   (cron/'jobs').write_text('*/5 * * * * echo cf10\n')
   out=m.survey_schedule((systemd,cron))
   self.assertEqual(len(out['matches']),2)
   self.assertEqual(out['counts']['out_of_scope_skipped'],1)
   self.assertFalse(out['full_scheduler_scope_proven'])
   self.assertTrue(all(v['classification'].endswith('NOT_WRITER_ENROLLMENT') for v in out['matches']))
   self.assertEqual(out['counts']['files_read'],3)
 def test_schedule_symlink_skipped(self):
  with tempfile.TemporaryDirectory() as t:
   a=Path(t);(a/'real').write_text('cf10');(a/'unit').symlink_to(a/'real')
   out=m.survey_schedule((a,))
   self.assertEqual(out['counts']['links_skipped'],1)
   self.assertEqual(len(out['matches']),1)
 def test_schedule_limit_warning(self):
  with tempfile.TemporaryDirectory() as t:
   a=Path(t);(a/'unit').write_text('cf10')
   old=m.MAX_FILES;m.MAX_FILES=0
   try:out=m.survey_schedule((a,))
   finally:m.MAX_FILES=old
   self.assertIn('SCHEDULE_SURVEY_LIMIT_REACHED',out['findings'])
 def test_schedule_parent_symlink_unsafe(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);(base/'real').mkdir();(base/'alias').symlink_to(base/'real')
   out=m.survey_schedule((base/'alias',))
   self.assertTrue(any(x.startswith('UNSAFE_SCHEDULE_ROOT:') for x in out['findings']))
 def test_prior_exact_path_first(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with self.assertRaises(m.SurveyBlocked):m.load_predecessor(r,r/'other.json',m.PRIOR_SHA)
 def test_prior_wrong_digest_first(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   with self.assertRaises(m.SurveyBlocked):m.load_predecessor(r,r/m.PRIOR_REL,'0'*64)
 def test_create_only_private_files(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'tmp').mkdir()
   p,d=m.save(root,self.result())
   self.assertEqual(len(d),64);self.assertEqual((p/'report.json').stat().st_mode&0o777,0o600)
   self.assertTrue((p/'operator_proof_intake_template.json').is_file())
   self.assertEqual(json.loads((p/'report.json').read_text())['authority_granted'],False)
 def test_tmp_symlink_denied(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);(root/'real').mkdir();(root/'tmp').symlink_to(root/'real')
   with self.assertRaises(m.SurveyBlocked):m.save(root,self.result())

if __name__=='__main__':unittest.main()
