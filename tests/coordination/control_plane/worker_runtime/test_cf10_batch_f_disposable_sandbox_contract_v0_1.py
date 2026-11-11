"""Batch F source safeguards: real runtime evidence is separately required on s01."""
import dataclasses
import importlib
import unittest
from unittest import mock

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as r013
from scripts.coordination.control_plane.worker_runtime import (
    cf10_batch_f_disposable_sandbox_contract_v0_1 as f,
    cf10_batch_e_runtime_cutover_contract_v0_1 as e,
    cf10_systemd_launcher_v0_1 as launcher)

U='forprint-cf10-batchf-'+'1'*16+'.service'
R='/run/'+U[:-8]

class SandboxContractTests(unittest.TestCase):
    def test_positive_source_check(self):
        d=f.source_check();self.assertTrue(d['source_checked'])
        self.assertFalse(d['authority']);self.assertEqual(len(d['open_gates']),5)
    def test_positive_exact_properties(self):
        x=f.disposable_plan(unit=U,lab_dir=R,canary_file=R+'/fake_provider_credential.txt')
        p=x['properties']
        for k,v in [('PrivateNetwork','yes'),('RestrictAddressFamilies','AF_UNIX'),
                     ('IPAddressDeny','any'),('InaccessiblePaths','/var/lib/forprint-runner '+R+'/fake_provider_credential.txt'),
                     ('KillMode','control-group'),('NoNewPrivileges','yes'),
                     ('ProtectHome','yes'),('ProtectSystem','strict'),('Delegate','no')]:
            self.assertEqual(p[k],v)
        self.assertNotIn('StateDirectory',p)
        self.assertNotIn('StateDirectoryMode',p)
        self.assertEqual(p['Environment'],'HOME=/nonexistent')
        self.assertEqual(x['profile_sha256'],f.digest(p))
        for k in ('live_admission','copilot_executed','g1_g5_closed','claim_consumed',
                  'model_inference_possible','root_broker_live','kernel_terminal_proven'):
            self.assertIs(x[k],False)
    def test_reject_wrong_unit(self):
        for unit in (U.replace('batchf','worker'),U[:-2],U+';id','/run/'+U,U.upper()):
            with self.assertRaises(f.SandboxHold):
                f.disposable_plan(unit=unit,lab_dir=R,canary_file=R+'/fake_provider_credential.txt')
    def test_reject_incorrect_canary_and_lab(self):
        for canary in (R+'/fake_provider_credential.txt/../x','/root/.ssh/id_rsa','/tmp/c',R+'/other',R+'/fake_provider_credential.txt\n'):
            with self.assertRaises(f.SandboxHold):
                f.disposable_plan(unit=U,lab_dir=R,canary_file=canary)
        with self.assertRaises(f.SandboxHold):
            f.disposable_plan(unit=U,lab_dir=R+'/..',canary_file=R+'/fake_provider_credential.txt')
    def test_base_source_changed_fail_closed(self):
        mutated={**r013.EXPECTED_PROPERTIES,'ProtectHome':'no'}
        with mock.patch.object(r013,'EXPECTED_PROPERTIES',mutated):
            with self.assertRaises(f.SandboxHold):
                f.disposable_plan(unit=U,lab_dir=R,canary_file=R+'/fake_provider_credential.txt')
    def test_live_switch_changed_fail_closed(self):
        with mock.patch.object(launcher,'LIVE_CUTOVER_ENABLED',True):
            with self.assertRaises(f.SandboxHold):f.source_check()
        self.assertFalse(launcher.LIVE_CUTOVER_ENABLED)
    def test_batch_e_must_keep_5_open_gates(self):
        with mock.patch.object(e,'source_check',return_value={'live_worker_authorized':False,'open_gates':[]}):
            with self.assertRaises(f.SandboxHold):f.source_check()
    def test_fingerprint_stable(self):
        a=f.disposable_plan(unit=U,lab_dir=R,canary_file=R+'/fake_provider_credential.txt')
        b=f.disposable_plan(unit=U,lab_dir=R,canary_file=R+'/fake_provider_credential.txt')
        self.assertEqual(a,b)
    def test_no_real_execution_in_source_module(self):
        import inspect
        s=inspect.getsource(f)
        for token in ('subprocess.run(', 'systemd-run', 'receipt.claim(',
                      'os.system(', 'LIVE_CUTOVER_ENABLED=True'):
            self.assertNotIn(token,s)
    def test_open_gates_remain_distinct(self):
        self.assertEqual(len(set(f.GATES)),5)
        self.assertIn('INFERENCE_TRANSPORT_UNSOLVED',f.GATES[0])
        self.assertIn('KERNEL_TERMINAL_UNPROVEN',f.GATES[-1])

if __name__=='__main__':unittest.main()
