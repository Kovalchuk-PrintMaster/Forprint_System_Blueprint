import unittest
from copy import deepcopy
from scripts.coordination.control_plane import cf10_recovery_reconciliation_v0_1 as m
A='cf10-u180j-a050'; H='a'*40; D='b'*64
KW={'attempt_id':A,'source_head':H,'handoff_sha256':D}

class Recovery(unittest.TestCase):
    def events(self,*events):return m.simulate_events(**KW,events=list(events))
    def check(self,r,**more):return m.reconcile(receipt=r,**KW,**more)
    def test_01_claim_only(self):self.assertIn('NO_SPAWN',self.check(self.events('CLAIM_CONSUMED'))['state'])
    def test_02_request_no_service(self):self.assertIn('UNKNOWN',self.check(self.events('CLAIM_CONSUMED','LAUNCH_REQUESTED'))['state'])
    def test_03_service_no_stop(self):self.assertIn('RUNNING',self.check(self.events('CLAIM_CONSUMED','LAUNCH_REQUESTED','SERVICE_OBSERVED'))['state'])
    def test_04_stop_no_quiescence(self):self.assertIn('TEARDOWN',self.check(self.events('CLAIM_CONSUMED','LAUNCH_REQUESTED','SERVICE_OBSERVED','STOP_REQUESTED'))['state'])
    def test_05_quiescence_candidate_still_blocked(self):
        r=self.check(self.events(*m.ORDERED));self.assertEqual(r['state'],'BLOCKED_PENDING_INDEPENDENT_PRODUCTION_PROOFS')
    def test_06_no_restart(self):self.assertFalse(self.check(self.events('CLAIM_CONSUMED'))['automatic_retry'])
    def test_07_no_result(self):self.assertFalse(self.check(self.events(*m.ORDERED))['worker_result_accepted'])
    def test_08_no_release(self):self.assertFalse(self.check(self.events(*m.ORDERED))['release_allowed'])
    def test_09_no_launch(self):self.assertFalse(self.check(self.events(*m.ORDERED))['launch_allowed'])
    def test_10_empty(self):
        with self.assertRaises(m.ReconciliationBlocked):self.events()
    def test_11_wrong_first(self):
        with self.assertRaises(m.ReconciliationBlocked):self.events('LAUNCH_REQUESTED')
    def test_12_out_of_order(self):
        with self.assertRaises(m.ReconciliationBlocked):self.events('CLAIM_CONSUMED','SERVICE_OBSERVED')
    def test_13_duplicate(self):
        with self.assertRaises(m.ReconciliationBlocked):self.events('CLAIM_CONSUMED','CLAIM_CONSUMED')
    def test_14_illegal(self):
        with self.assertRaises(m.ReconciliationBlocked):self.events('CLAIM_CONSUMED','RETRY')
    def test_15_tamper(self):
        r=self.events('CLAIM_CONSUMED');r['events'].append('LAUNCH_REQUESTED')
        with self.assertRaises(m.ReconciliationBlocked):self.check(r)
    def test_16_wrong_head(self):
        with self.assertRaises(m.ReconciliationBlocked):m.reconcile(receipt=self.events('CLAIM_CONSUMED'),**{**KW,'source_head':'c'*40})
    def test_17_wrong_attempt(self):
        with self.assertRaises(m.ReconciliationBlocked):m.reconcile(receipt=self.events('CLAIM_CONSUMED'),**{**KW,'attempt_id':'cf10-u180j-a051'})
    def test_18_wrong_handoff(self):
        with self.assertRaises(m.ReconciliationBlocked):m.reconcile(receipt=self.events('CLAIM_CONSUMED'),**{**KW,'handoff_sha256':'c'*64})
    def test_19_fake_production_receipt(self):
        r=self.events('CLAIM_CONSUMED');r['production_evidence']=True
        with self.assertRaises(m.ReconciliationBlocked):self.check(r)
    def test_20_fake_quiescence(self):
        with self.assertRaises(m.ReconciliationBlocked):self.check(self.events(*m.ORDERED),supervisor={**{'attempt_id':A,'source_head':H},'production_quiescence_proven':True})
    def test_21_fake_credentials(self):
        with self.assertRaises(m.ReconciliationBlocked):self.check(self.events(*m.ORDERED),credentials={'attempt_id':A,'source_head':H,'production_credentials_released':True})
    def test_22_fake_delta(self):
        with self.assertRaises(m.ReconciliationBlocked):self.check(self.events(*m.ORDERED),delta={'attempt_id':A,'source_head':H,'delta_accepted':True})
    def test_23_unbound(self):
        with self.assertRaises(m.ReconciliationBlocked):self.check(self.events('CLAIM_CONSUMED'),supervisor={'attempt_id':'invalid','source_head':H})
    def test_24_proof_not_authority(self):
        with self.assertRaises(m.ReconciliationBlocked):self.check(self.events('CLAIM_CONSUMED'),delta={'attempt_id':A,'source_head':H,'worker_result_accepted':True})
    def test_25_handoff_regex(self):
        with self.assertRaises(m.ReconciliationBlocked):m.simulate_events(**{**KW,'handoff_sha256':'invalid'},events=['CLAIM_CONSUMED'])
    def test_26_review(self):self.assertEqual(self.check(self.events('CLAIM_CONSUMED','REVIEW_REQUIRED'))['state'],'BLOCKED_OPERATOR_REVIEW')
    def test_27_unproven(self):
        r=self.events('CLAIM_CONSUMED','LAUNCH_REQUESTED','SERVICE_OBSERVED','STOP_REQUESTED','QUIESCENCE_UNPROVEN')
        self.assertEqual(self.check(r)['state'],'BLOCKED_QUIESCENCE_UNKNOWN')
    def test_28_unproven_and_proven_contradiction(self):
        with self.assertRaises(m.ReconciliationBlocked):self.events(*m.ORDERED,'QUIESCENCE_UNPROVEN')
    def test_29_unexpected_receipt_key(self):
        r=self.events('CLAIM_CONSUMED');r['approval']=True
        with self.assertRaises(m.ReconciliationBlocked):self.check(r)
    def test_30_sequencing_with_review(self):
        r=self.events('CLAIM_CONSUMED','LAUNCH_REQUESTED','SERVICE_OBSERVED','REVIEW_REQUIRED')
        self.assertEqual(self.check(r)['state'],'BLOCKED_OPERATOR_REVIEW')

if __name__=='__main__':unittest.main()
