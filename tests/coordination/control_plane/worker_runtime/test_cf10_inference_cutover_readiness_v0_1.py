"""U negative gates, evidence provenance and no authority escalation."""
import copy
import importlib
import unittest
from pathlib import Path

try:
 from scripts.coordination.control_plane.worker_runtime import cf10_inference_cutover_readiness_v0_1 as u
except ImportError:
 from importlib.util import spec_from_file_location, module_from_spec
 _spec=spec_from_file_location('cf10_u_payload',Path(__file__).with_name('cf10_inference_cutover_readiness_v0_1.py'))
 u=module_from_spec(_spec);_spec.loader.exec_module(u)

class TestReadiness(unittest.TestCase):
 def setUp(self):
  self.source=u.synthetic_baseline();self.digest=self.source['preflight']['dirty_fingerprint']
 def eval(self,source=None):return u.review(self.source if source is None else source,expected_dirty_fingerprint=self.digest)
 def test_source_check(self):
  self.assertFalse(u.source_check()['live_dispatch_enabled'])
 def test_valid_snapshot_review_only(self):
  r=self.eval();self.assertTrue(r['all_gates_open']);self.assertEqual(len(r['gates']),5)
  self.assertTrue(r['cli_executed_p']);self.assertFalse(r['inference_result_proven']);self.assertFalse(r['kernel_final_zero_proven'])
  self.assertFalse(r['live_dispatch_enabled']);self.assertFalse(r['automatic_retry'])
 def test_deterministic_sha(self):self.assertEqual(self.eval(),self.eval())
 def test_readiness_no_proxy_not_bypass(self):
  r=self.eval();self.assertFalse(r['cli_proxy_route_proven']);self.assertFalse(r['no_proxy_routing_conclusion_permitted'])
 def test_systemd_inactive_not_kernel_proof(self):
  self.assertTrue(self.eval()['systemd_disposable_inactive']);self.assertFalse(self.eval()['kernel_final_zero_proven'])
 def test_r140_does_not_impersonate_egress(self):self.assertTrue(self.eval()['r140_not_an_inference_proxy'])
 def test_authority_unchanged(self):
  for field in ('provider_authenticated','inference_result_proven','operator_authorization_granted','live_dispatch_enabled',
                'claim_consumed','production_modified','terminal_ledger_written','worker_result_accepted'):
   self.assertIs(self.eval()[field],False)
 def test_wrong_status_hold(self):
  v=copy.deepcopy(self.source);v['status']='PASS';self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_dirty_drift_hold(self):
  v=copy.deepcopy(self.source);v['preflight']['dirty_fingerprint']='0'*64;self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_head_drift_hold(self):
  v=copy.deepcopy(self.source);v['base_head']='a'*40;self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_phase_gap_hold(self):
  v=copy.deepcopy(self.source);v['child_phases'].pop();self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_unverified_version_hold(self):
  v=copy.deepcopy(self.source);v['child_observations']['offline_version']['exit_code']=1;self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_outside_egress_claim_hold(self):
  v=copy.deepcopy(self.source);v['authority']['external_egress']=True;self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_credential_claim_hold(self):
  v=copy.deepcopy(self.source);v['authority']['provider_credentials_used']=True;self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_proxy_count_mismatch_hold(self):
  v=copy.deepcopy(self.source);v['child_observations']['copilot']['proxy_wellformed_connect_count']=1
  self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_proxy_observed_not_inference_proof(self):
  v=copy.deepcopy(self.source);v['child_observations']['copilot']['proxy_wellformed_connect_count']=1
  v['child_observations']['copilot']['proxy_routing_evidence']=True
  r=self.eval(v);self.assertTrue(r['cli_proxy_route_proven']);self.assertFalse(r['inference_result_proven'])
 def test_kernel_false_success_rejected(self):
  v=copy.deepcopy(self.source);v['kernel']['pinned_fd_final_populated']='0';self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_runner_mode_hold(self):
  v=copy.deepcopy(self.source);v['runtime_layout']['dir_mode']='0700';self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_inactive_hold(self):
  v=copy.deepcopy(self.source);v['systemd_postflight']['active']='failed';self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_fake_credential_access_hold(self):
  v=copy.deepcopy(self.source);v['child_observations']['fake_credentials_denied']=False;self.assertRaises(u.ReadinessHold,self.eval,v)
 def test_source_is_inert(self):
  src=Path(u.__file__).read_text()
  for forbidden in ('subprocess.Popen(', 'systemd-run', 'git push', 'revoke_lease(', 'LIVE_CUTOVER_ENABLED=True'):
   self.assertNotIn(forbidden,src)

if __name__=='__main__':unittest.main()
