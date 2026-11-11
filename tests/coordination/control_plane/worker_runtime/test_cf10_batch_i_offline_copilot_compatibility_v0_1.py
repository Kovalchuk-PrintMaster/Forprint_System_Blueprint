from __future__ import annotations
import hashlib
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock
from scripts.coordination.control_plane.worker_runtime import (
    cf10_batch_i_offline_copilot_compatibility_v0_1 as c,
    cf10_batch_i_offline_copilot_child_v0_1 as child,
)

UNIT='forprint-cf10-batchi-0123456789abcdef.service'
ROOT='/run/'+UNIT[:-8]

class ContractTests(unittest.TestCase):
    def test_source_refers_to_existing_canonical_r115(self):
        x=c.source_check()
        self.assertFalse(x['no_live_admission']==False)
        self.assertTrue(x['g1_g5_open'])
        self.assertEqual(x['binary_sha256'],'985f0e1b1b3e734bc996324651307a076ae3deae21e3fa9f9af917983ce309c4')
    def test_immutable_single_command(self):
        p=c.plan(unit=UNIT,root=ROOT)
        self.assertEqual(p['only_argv'],['--version'])
        self.assertEqual(p['properties']['RestrictAddressFamilies'],'AF_UNIX')
        self.assertEqual(p['properties']['IPAddressDeny'],'any')
        self.assertEqual(p['properties']['ProtectHome'],'yes')
        self.assertEqual(p['properties']['InaccessiblePaths'],'/var/lib/forprint-runner')
        self.assertFalse(p['live_admission'])
        self.assertFalse(p['provider_auth_used'])
    def test_unit_untrusted_scope(self):
        for x in ('forprint-cf10-batchh-0123456789abcdef.service',
                  UNIT.replace('service','timer'),'forprint-cf10-batchi-0123456789abcde.service',
                  UNIT+';bad'):
            with self.assertRaises(c.OfflineHold):c.plan(unit=x,root=ROOT)
    def test_root_untrusted_scope(self):
        for r in ('/run/other','/tmp/'+UNIT,'/run/'+UNIT,ROOT+'/sub'):
            with self.assertRaises(c.OfflineHold):c.plan(unit=UNIT,root=r)
    def test_exact_sha_plan_stable(self):
        self.assertEqual(c.plan(unit=UNIT,root=ROOT),c.plan(unit=UNIT,root=ROOT))
    def test_source_pin_drift_fails(self):
        with mock.patch.object(c.r115,'COPILOT_PILOT_SHA256','0'*64):
            with self.assertRaises(c.OfflineHold):c.source_check()
    def test_nonroot_fails_before_executable(self):
        with mock.patch.object(c.os,'geteuid',return_value=1000):
            with self.assertRaises(c.OfflineHold):c.verify_pinned_binary()

    def obs(self):
        return {'schema':'cf10_batch_i_offline_cli_result_v0_1','uid':996,'gid':992,
                'result_status':'PASS_OFFLINE_VERSION','exit_code':0,'version_found':True,
                'stdout_sha256':hashlib.sha256(b'x').hexdigest(),
                'stderr_sha256':hashlib.sha256(b'').hexdigest(),
                'stdout_length':1,'stderr_length':0,
                'ipv4_denied_errno':97,'ipv6_denied_errno':97,
                'fake_credential_errno':13,'client_pid':1234,
                'binary_command':'PINNED_COPILOT_VERSION_ONLY'}
    def test_valid_observation(self):
        self.assertEqual(c.review_observation(self.obs())['exit_code'],0)
    def test_bad_observations_fail_closed(self):
        x=self.obs()
        edits={
          'uid':0,'gid':0,'result_status':'HOLD_VERSION','exit_code':1,
          'version_found':False,'stdout_sha256':'bad','stderr_sha256':'x',
          'stdout_length':99999,'stderr_length':99999,'ipv4_denied_errno':0,
          'ipv6_denied_errno':101,'fake_credential_errno':2,
          'client_pid':0,'binary_command':'RUN_COPILOT_PROMPT','schema':'other'}
        for key,bad in edits.items():
            with self.subTest(key=key):
                y={**x,key:bad}
                with self.assertRaises(c.OfflineHold):c.review_observation(y)
    def test_extra_or_missing_observation_denied(self):
        x=self.obs(); x['token']='fake'
        with self.assertRaises(c.OfflineHold):c.review_observation(x)
        x=self.obs();x.pop('stdout_sha256')
        with self.assertRaises(c.OfflineHold):c.review_observation(x)
    def test_bool_is_not_int(self):
        x=self.obs();x['exit_code']=False
        with self.assertRaises(c.OfflineHold):c.review_observation(x)

class ChildOfflineTests(unittest.TestCase):
    def test_offline_version_real_local_stub_only(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);bin=root/'fake-cli';bin.write_text('#!/bin/sh\necho "copilot 1.0.107"\n')
            bin.chmod(0o755)
            result=child.offline_version(binary=str(bin),home=root)
            self.assertEqual(result['result_status'],'PASS_OFFLINE_VERSION')
            self.assertTrue(result['version_found'])
            self.assertEqual(result['exit_code'],0)
    def test_offline_version_wrong_version_holds(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);bin=root/'fake-cli';bin.write_text('#!/bin/sh\necho "copilot 1.0.106"\n')
            bin.chmod(0o755)
            result=child.offline_version(binary=str(bin),home=root)
            self.assertEqual(result['result_status'],'HOLD_VERSION')
    def test_offline_version_error_holds(self):
        with tempfile.TemporaryDirectory() as td:
            result=child.offline_version(binary='/missing/forprint-copilot',home=Path(td))
            self.assertEqual(result['result_status'],'HOLD_OFFLINE_PROCESS')
    def test_offline_version_env_is_not_inherited(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);bin=root/'fake-cli'
            bin.write_text('#!/bin/sh\n[ -z "$GH_TOKEN" ] && [ -z "$HTTPS_PROXY" ] && echo "1.0.107"\n')
            bin.chmod(0o755)
            with mock.patch.dict(child.os.environ,{'GH_TOKEN':'SENTINEL','HTTPS_PROXY':'SENTINEL'}):
                result=child.offline_version(binary=str(bin),home=root)
            self.assertEqual(result['result_status'],'PASS_OFFLINE_VERSION')
    def test_fake_denied_missing_not_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(child.credential_denial(str(Path(td)/'missing')),2)
    def test_ipv4_socket_success_is_zero_not_pass(self):
        with mock.patch.object(child.socket,'socket') as maker:
            self.assertEqual(child.prohibited_family(child.socket.AF_INET),0)
            maker.return_value.close.assert_called_once()
    def test_transport_only_unix(self):
        self.assertEqual(child.BIN,'/usr/local/bin/forprint-copilot-1.0.107')
        self.assertEqual(child.EXPECTED_VERSION,'1.0.107')

