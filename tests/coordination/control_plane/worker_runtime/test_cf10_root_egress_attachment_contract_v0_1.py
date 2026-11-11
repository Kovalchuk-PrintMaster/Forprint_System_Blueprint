#!/usr/bin/env python3
"""Adversarial tests for the inert CF10 root egress attachment contract."""
import copy
import importlib
import os
import unittest

MODULE_NAME='scripts.coordination.control_plane.worker_runtime.cf10_root_egress_attachment_contract_v0_1'
try:
    a=importlib.import_module(MODULE_NAME)
except ModuleNotFoundError:
    # Package selftests before source-only installation: import alongside this file.
    a=importlib.import_module('cf10_root_egress_attachment_contract_v0_1')

class AttachmentTests(unittest.TestCase):
    def setUp(self): self.good=a.test_vector()
    def hold(self, obj):
        with self.assertRaises(a.AttachmentHold): a.plan_attachment(**obj)
    def test_valid_inert(self):
        obj=a.plan_attachment(**self.good)
        self.assertEqual(obj['schema'],a.SCHEMA)
        self.assertEqual(len(obj['open_gates']),5)
        self.assertFalse(obj['authority'])
        self.assertFalse(obj['inference_enabled'])
        self.assertFalse(obj['credentials_delegated'])
        self.assertFalse(obj['external_egress_enabled'])
        self.assertFalse(obj['dispatcher_integrated'])
        self.assertFalse(obj['terminal_proven'])
        self.assertFalse(obj['automatic_retry'])
        self.assertFalse(obj['provider_native_sandbox_counts_as_isolation'])
        self.assertTrue(obj['source_only'])
        self.assertEqual(len(obj['candidate_sha256']),64)
    def test_deterministic(self):
        self.assertEqual(a.plan_attachment(**self.good),a.plan_attachment(**self.good))
    def test_binding_changes_sha(self):
        x=copy.deepcopy(self.good);x['frozen']['frozen_preclaim_sha256']='f'*64
        self.assertNotEqual(a.plan_attachment(**x)['candidate_sha256'],a.plan_attachment(**self.good)['candidate_sha256'])
    def test_fields_fail_closed(self):
        for which in self.good:
            with self.subTest(which=which):
                x=copy.deepcopy(self.good);x[which]['unapproved_extra']='x';self.hold(x)
                x=copy.deepcopy(self.good);x[which].pop(next(iter(x[which])));self.hold(x)
    def test_preclaim_binding(self):
        for bad in ['x','cf10-u180j-a054\n','cf10-u180j-a54',None,1]:
            with self.subTest(bad=bad):
                x=copy.deepcopy(self.good);x['frozen']['attempt_id']=bad;self.hold(x)
    def test_source_head(self):
        for bad in ['','A'*40,'a'*39,'a'*41,None]:
            with self.subTest(bad=bad):
                x=copy.deepcopy(self.good);x['frozen']['source_head']=bad;self.hold(x)
    def test_preclaim_and_crosswalk(self):
        for key in ('frozen_preclaim_sha256','crosswalk_sha256'):
            for bad in ('A'*64,'a'*63,'','a'*65):
                with self.subTest(key=key,bad=bad):
                    x=copy.deepcopy(self.good);x['frozen'][key]=bad;self.hold(x)
    def test_unknown_provider(self):
        for provider in ('claude_cli','codex_cli','anything','github-copilot'):
            with self.subTest(provider=provider):
                x=copy.deepcopy(self.good);x['provider']['provider_id']=provider;self.hold(x)
    def test_provider_route_and_hash(self):
        for route in ('AUTO_FALLBACK','R078','LOCAL_EXEC'):
            x=copy.deepcopy(self.good);x['provider']['adapter_route']=route;self.hold(x)
        x=copy.deepcopy(self.good);x['provider']['provider_selection_sha256']='a'*40;self.hold(x)
    def test_root_routes(self):
        changes={'adapter':'NEW_PARALLEL_BROKER','lease':'PRODUCTION_LEASE',
                 'external_revoke':'NONE','session_fence':'NONE',
                 'lineage_independently_proven':True}
        for k,bad in changes.items():
            with self.subTest(k=k):
                x=copy.deepcopy(self.good);x['root_ipc'][k]=bad;self.hold(x)
    def test_egress_denials(self):
        changes={'route':'DIRECT_NETWORK','upstream_policy':'ALLOW_ANY',
                 'approved_hosts':['api.github.com'], 'egress_tested':True,
                 'credentials_delegated':True}
        for k,bad in changes.items():
            with self.subTest(k=k):
                x=copy.deepcopy(self.good);x['egress'][k]=bad;self.hold(x)
    def test_runtime_fail_closed(self):
        changes={'runner_uid':0,'runner_gid':0,'binary_sha256':'f'*64,
                 'private_network':False,'direct_external_ip_blocked':False,
                 'inference_enabled':True,'worker_claim_used':True,
                 'live_dispatch_enabled':True}
        for k,bad in changes.items():
            with self.subTest(k=k):
                x=copy.deepcopy(self.good);x['runtime'][k]=bad;self.hold(x)
    def test_secret_keys_rejected(self):
        for key in ('token','access_token','secret','credential','password','api_key','authorization'):
            x=copy.deepcopy(self.good);x['frozen'][key]='dummy';self.hold(x)
    def test_nested_secret_deny(self):
        x=copy.deepcopy(self.good);x['provider']['provider_selection_sha256']={'token':'x'};self.hold(x)
    def test_bool_int_confusion(self):
        for k in ('runner_uid','runner_gid'):
            x=copy.deepcopy(self.good);x['runtime'][k]=True;self.hold(x)
    def test_provider_selection_tamper(self):
        x=copy.deepcopy(self.good);x['provider']['provider_selection_sha256']='0'*64
        self.assertNotEqual(a.plan_attachment(**x)['candidate_sha256'],a.plan_attachment(**self.good)['candidate_sha256'])
    def test_no_os_effects(self):
        self.assertFalse(hasattr(a,'launch_worker'))
        self.assertFalse(hasattr(a,'open_egress'))
        self.assertFalse(hasattr(a,'commit'))
    def test_canonical_paths_are_read_only_deps(self):
        self.assertIn('r140',a.CANONICAL_FILES)
        self.assertIn('batch_j',a.CANONICAL_FILES)
        self.assertEqual(len(set(a.CANONICAL_FILES.values())),len(a.CANONICAL_FILES))

if __name__=='__main__':unittest.main()
