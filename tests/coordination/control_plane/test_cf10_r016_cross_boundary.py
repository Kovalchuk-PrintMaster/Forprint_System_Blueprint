import tempfile,unittest,os
from pathlib import Path
from scripts.coordination.control_plane import cf10_canonical_boundary_v0_1 as boundary
from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipts
from scripts.coordination.control_plane import cf10_recovery_reconciliation_v0_1 as recovery
A='cf10-u180j-a050'; TASK='cf10-project-change-impact-and-freshness-control-v0-1';H='a'*40;D='b'*64

@unittest.skipUnless(os.geteuid()==0,'root-owned disposable receipt fixture only')
class CrossBoundary(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)
  self.runtime=self.base/'runtime';self.repo=self.runtime/'forprint_system_blueprint'/'worker-01'/A/'workspace'/'repo';self.repo.mkdir(parents=True)
  (self.repo/'index.txt').write_text('alpha');(self.repo/'.git').mkdir()
  self.private=self.base/'private';self.private.mkdir(mode=0o700)
  self.kw={'task':TASK,'attempt':A,'head':H,'handoff':D,'worktree':str(self.repo),'runtime_root':str(self.runtime)}
 def tearDown(self):self.tmp.cleanup()
 def claim(self):return receipts.claim(private_store=self.private,attempt_id=A,head=H,handoff_sha256=D)
 def event(self,s):return receipts.append_observation(private_store=self.private,attempt_id=A,expected_head=H,event=s)
 def test_01_root_claim_and_baseline_no_authority(self):
  b=boundary.capture_bound_baseline(**self.kw);r=self.claim()
  self.assertFalse(b['operator_authority_granted']);self.assertFalse(r['worker_launched'])
 def test_02_claim_duplicate_blocked(self):
  self.claim()
  with self.assertRaises(receipts.ReceiptBlocked):self.claim()
 def test_03_root_chain_after_simulated_stop(self):
  self.claim()
  for e in ('LAUNCH_REQUESTED','SERVICE_OBSERVED','STOP_REQUESTED','QUIESCENCE_OBSERVED_CANDIDATE'):self.event(e)
  read=receipts.observe(private_store=self.private,attempt_id=A,expected_head=H)
  self.assertEqual(read['event_count'],4);self.assertFalse(read['worker_result_accepted'])
 def test_04_fake_credential_authority_not_accepted(self):
  self.claim();r=recovery.simulate_events(attempt_id=A,source_head=H,handoff_sha256=D,events=list(recovery.ORDERED))
  with self.assertRaises(recovery.ReconciliationBlocked):recovery.reconcile(receipt=r,attempt_id=A,source_head=H,handoff_sha256=D,credentials={'attempt_id':A,'source_head':H,'production_credentials_released':True})
 def test_05_untrusted_git_not_delta_authority(self):
  baseline=boundary.capture_bound_baseline(**self.kw)
  (self.repo/'.git'/'HEAD').write_text('tampered')
  obs={'attempt_id':A,'source_head':H,'production_quiescence_proven':False}
  result=boundary.evaluate_candidate_delta(baseline=baseline,supervisor_observation=obs,**self.kw)
  self.assertFalse(result['candidate_files_changed']);self.assertFalse(result['worker_result_accepted'])
 def test_06_edit_candidate_still_blocked(self):
  baseline=boundary.capture_bound_baseline(**self.kw);(self.repo/'index.txt').write_text('modified')
  result=boundary.evaluate_candidate_delta(baseline=baseline,supervisor_observation={'attempt_id':A,'source_head':H,'production_quiescence_proven':False},**self.kw)
  self.assertTrue(result['candidate_files_changed']);self.assertFalse(result['result_verification_allowed'])
 def test_07_forged_quiescence_rejected(self):
  b=boundary.capture_bound_baseline(**self.kw)
  with self.assertRaises(boundary.BoundaryError):boundary.evaluate_candidate_delta(baseline=b,supervisor_observation={'attempt_id':A,'source_head':H,'production_quiescence_proven':True},**self.kw)
 def test_08_root_receipt_tampered_prevents_trusted_read(self):
  self.claim();self.event('LAUNCH_REQUESTED');p=self.private/A/'event_0001.json';p.write_text('{}')
  with self.assertRaises(Exception):receipts.observe(private_store=self.private,attempt_id=A,expected_head=H)

if __name__=='__main__':unittest.main()
