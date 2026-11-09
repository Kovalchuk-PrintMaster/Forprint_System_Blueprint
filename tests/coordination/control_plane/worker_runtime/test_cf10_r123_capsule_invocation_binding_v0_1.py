"""R123 source-only crosswalk: pinned capsule + exact R118 invocation, no launch."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r115_preclaim_executable_profile_v0_1 as pre,
    cf10_r123_capsule_invocation_binding_v0_1 as m,
)

class BindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='r123-fixture-')
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name) / 'forprint-worker'
        self.p = patch.object(pre, 'PILOT_MCP_BASE_WORKSPACE', base)
        self.p.start(); self.addCleanup(self.p.stop)
        self.workspace = base / 'cf10-fixture-a123' / 'workspace' / 'repo'
        self.workspace.mkdir(parents=True)
        self.script = self.workspace / pre.PILOT_MCP_SCRIPT
        self.script.parent.mkdir(parents=True)
        self.script.write_bytes(b'canonical-mcp-from-pinned-head\n')
        self.script.chmod(0o640)
        self.readback = {
            'status': 'PASS_NON_AUTHORIZING_DURABLE_SOURCE',
            'capsule_id': m.CAPSULE_ID, 'capsule_head': m.capsule.PINNED_HEAD,
            'capsule_files':427,
            'mcp_source_sha256':hashlib.sha256(self.script.read_bytes()).hexdigest(),
            'validation_suite_sha256':'1'*64,
        }
        self.mock_readback = patch.object(m,'verify_capsule_readback',return_value=self.readback)
        self.mock_readback.start();self.addCleanup(self.mock_readback.stop)
        attempt=self.workspace.parents[1].name
        tools=list(pre.PILOT_MCP_BASE_TOOLS)
        args=[str(self.script),'--attempt-id',attempt,
              '--task-id','cf10-fixture-task','--work-front-id','wf-fixture',
              '--decision-id','d'*64,'--workspace-repo',str(self.workspace),
              '--evidence-root',str(self.workspace.parents[1]/'evidence'/'structured_command')]
        self.spec={'type':'local','command':str(m.capsule.PROJECT/'.venv_blueprint/bin/python'),
                   'args':args,'tools':tools,'cwd':str(self.workspace)}
        self.argv=self.render()
        self.inv=self.invocation()

    def render(self):
        cfg={'mcpServers':{'ForPrintValidation':self.spec}}
        tools=['view','edit','apply_patch', *['ForPrintValidation-'+x for x in self.spec['tools']]]
        return [str(pre.COPILOT_PILOT_PATH),'-p','TASK','--silent','--model','auto',
                '--additional-mcp-config',json.dumps(cfg,sort_keys=True),
                '--available-tools',*tools,'--allow-all-tools','--disable-builtin-mcps',
                '--max-ai-credits','30','--no-auto-update','--sandbox','-C',str(self.workspace)]

    def invocation(self):
        argv=self.argv
        return {'schema_version':'forprint_worker_runtime_launch_invocation_v0_1',
                'workspace_repo':str(self.workspace),'provider_id':'github_copilot_cli',
                'command_representation':'ARGV_NO_SHELL','attempt_id':'cf10-fixture-a123',
                'task_id':'cf10-fixture-task','work_front_id':'wf-fixture','decision_id':'d'*64,
                'argv':argv,'argv_sha256':hashlib.sha256('\0'.join(argv).encode()).hexdigest(),
                'authority':{'adapter_grants_authority':False},'effects':{'worker_process_started':False}}
    def bind(self):return m.crosswalk_invocation(invocation=self.inv)
    def test_exact_candidate_is_non_authorizing(self):
        rec=self.bind()
        self.assertEqual(rec['capsule_id'],m.CAPSULE_ID)
        self.assertFalse(any(rec['authority'].values()))
        self.assertEqual(rec['state'],'SOURCE_CROSSWALK_CANDIDATE_NON_AUTHORIZING')
        self.assertEqual(rec['mcp_source_sha256'],self.readback['mcp_source_sha256'])
        self.assertNotIn('TASK',json.dumps(rec))
        self.assertNotIn('GH_TOKEN',json.dumps(rec))
        self.assertEqual(m.verify_record(record=rec,invocation=self.inv),rec)
    def test_digest_changes_if_context_changes(self):
        before=self.bind();self.inv['task_id']='other'
        with self.assertRaisesRegex(m.BindingBlocked,'CONTEXT_DRIFT'):self.bind()
        self.assertEqual(before['attempt_id'],'cf10-fixture-a123')
    def test_wrong_capsule_rejected(self):
        # Non-authorizing utility calls the R122 readback itself; callers do
        # not get to inject a forged readback document.
        with self.assertRaises(m.BindingBlocked):m.crosswalk_invocation(invocation=self.inv,capsule_id='git-other')
        # Mock is intentionally replaced for strict ID test.
    def test_workspace_mcp_modified_rejected(self):
        self.script.write_bytes(b'drift');self.script.chmod(0o640)
        with self.assertRaisesRegex(m.BindingBlocked,'NOT_CAPSULE_SOURCE'):self.bind()
    def test_symlink_script_rejected(self):
        self.script.unlink();self.script.symlink_to('/etc/hosts')
        with self.assertRaises(m.BindingBlocked):self.bind()
    def test_group_writable_script_rejected(self):
        self.script.chmod(0o660)
        with self.assertRaisesRegex(m.BindingBlocked,'OWNER_MODE'):self.bind()
    def test_no_unreviewed_tool(self):
        self.spec['tools'].append('run_shell');self.inv['argv']=self.render();self.inv['argv_sha256']=hashlib.sha256('\0'.join(self.inv['argv']).encode()).hexdigest()
        with self.assertRaisesRegex(m.BindingBlocked,'PRECLAIM'):self.bind()
    def test_no_extra_mcp_server(self):
        cfg=json.loads(self.inv['argv'][7]);cfg['mcpServers']['Remote']={'url':'http://localhost:3000'}
        self.inv['argv'][7]=json.dumps(cfg)
        self.inv['argv_sha256']=hashlib.sha256('\0'.join(self.inv['argv']).encode()).hexdigest()
        with self.assertRaisesRegex(m.BindingBlocked,'PRECLAIM'):self.bind()
    def test_argv_sha_matters(self):
        self.inv['argv_sha256']='f'*64
        with self.assertRaisesRegex(m.BindingBlocked,'ARG V_SHA'.replace(' ','')):self.bind()
    def test_no_authority_widening(self):
        self.inv['authority']['adapter_grants_authority']=True
        with self.assertRaisesRegex(m.BindingBlocked,'AUTHORITY'):self.bind()
    def test_started_worker_does_not_qualify(self):
        self.inv['effects']['worker_process_started']=True
        with self.assertRaisesRegex(m.BindingBlocked,'AUTHORITY'):self.bind()
    def test_duplicate_config_json_keys(self):
        self.inv['argv'][7]='{"mcpServers":{},"mcpServers":{}}'
        self.inv['argv_sha256']=hashlib.sha256('\0'.join(self.inv['argv']).encode()).hexdigest()
        with self.assertRaises(m.BindingBlocked):self.bind()
    def test_replay_record_drift(self):
        rec=self.bind();rec['attempt_id']='cf10-other-a999'
        with self.assertRaisesRegex(m.BindingBlocked,'RECORD_SOURCE'):m.verify_record(record=rec,invocation=self.inv)
    def test_no_kernel_claim_or_live_adapter_hooks(self):
        self.assertFalse(m.DENIALS['capsule_executed_as_mcp'])
        self.assertFalse(m.DENIALS['inference_tool_egress_separated'])
        self.assertFalse(m.DENIALS['mcp_kernel_isolation_attested'])
        self.assertNotIn('subprocess',Path(m.__file__).read_text())
        import inspect
        source=inspect.getsource(m.crosswalk_invocation)
        self.assertIn('verify_capsule_readback',source)
        self.assertIn('assert_static_tool_and_mcp_boundary',source)

    def test_readback_requires_exact_manifest_and_id(self):
        with patch.object(m,'verify_capsule_readback') as fake:
            fake.return_value={**self.readback,'capsule_files':426}
            with self.assertRaisesRegex(m.BindingBlocked,'UNTRUSTED_CAPSULE_READBACK'):self.bind()

if __name__=='__main__':unittest.main()
