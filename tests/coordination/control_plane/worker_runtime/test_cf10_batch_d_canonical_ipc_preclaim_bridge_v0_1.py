"""Batch D: R115->R134->R030 preclaim bridge; no root/Worker/systemd.

Source-fixture imports use actual reviewed R115/R129/R134 implementations; the
only R030 dependencies replaced in this *local curated test* are unused
systemd/terminal modules unavailable outside s01. On s01 real deps exist.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import mock
import pytest

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r115_preclaim_executable_profile_v0_1 as r115,
    cf10_r134_ipc_preclaim_crosswalk_v0_1 as r134,
)

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]

def scenario():
    filepath=HERE/'test_cf10_r134_ipc_preclaim_crosswalk_v0_1.py'
    spec=importlib.util.spec_from_file_location('cf10_batch_d_existing_r134_fixture',filepath)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    inv,c=mod.source_pair()
    preview=[*inv['argv'][:7],
      json.dumps(c['candidate_mcp_config'],sort_keys=True,separators=(',', ':'),ensure_ascii=True),
      inv['argv'][8],r115.IPC_MODEL_TOOL,*inv['argv'][-8:]]
    return inv,c,preview

def route():
    # Real R030 code is executed; historical imports irrelevant to the
    # pure review seam are intentionally unavailable in local 59-file snapshot.
    prefix='scripts.coordination.control_plane.worker_runtime.'
    stubs={
        'scripts.coordination.control_plane.cf10_r026_trusted_systemd_readback_v0_1':SimpleNamespace(),
        prefix+'cf10_systemd_launcher_v0_1':SimpleNamespace(
            LIVE_CUTOVER_ENABLED=False,
            launch_after_owner_claim=lambda **kw:pytest.fail('Worker launch not allowed')),
        prefix+'cf10_systemd_terminal_bridge_v0_1':SimpleNamespace(),
        prefix+'cf10_r035_durable_witness_boundary_v0_1':SimpleNamespace(),
        prefix+'cf10_r138_canonical_terminal_handoff_v0_1':SimpleNamespace(),
    }
    filepath=ROOT/'scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py'
    s=importlib.util.spec_from_file_location('cf10_batch_d_r030_fixture',filepath)
    with mock.patch.dict(sys.modules,stubs):
        mod=importlib.util.module_from_spec(s)
        s.loader.exec_module(mod)
    return mod

def bound(inv,c):
    spec=binding.BoundedInput(task_prompt_id=inv['task_id'],attempt_id=inv['attempt_id'],
        source_head=c['source_head'],baseline_sha256='b'*64,handoff_sha256='c'*64,
        workspace=inv['workspace_repo'],runtime_root='/srv/software_development/forprint-worker-runtime',
        argv=tuple(inv['argv']),timeout_seconds=75)
    return spec,binding.bind_plan(spec)

def test_exact_readonly_preview_is_non_authorizing():
    inv,c,argv=scenario()
    review=r115.assert_guarded_ipc_preview(argv,inv['workspace_repo'])
    assert review['model_tool']=='ForPrintValidation-run_repo_head'
    assert review['attempt_id']==inv['attempt_id']
    assert review['source_head']==c['source_head']
    assert review['epoch']==c['epoch']
    assert review['argv_sha256']==hashlib.sha256('\0'.join(argv).encode()).hexdigest()
    assert all(review[k] is False for k in ('live_worker_authorized','claim_consumed',
        'kernel_witness_attested','credentials_isolated','egress_attested',
        'terminal_ledger_written'))
    assert json.dumps(review).find('fixture prompt')<0


def test_r134_reuses_the_exact_r115_guard():
    inv,c,_=scenario()
    review=r134.verify_source_only(invocation=inv,candidate=c)
    assert review['r115_guarded_ipc_preview_exact'] is True
    assert len(review['r115_guarded_ipc_mcp_config_sha256'])==64
    assert review['live_cutover_authorized'] is False
    assert review['legacy_r115_rejects_prospective_argv'] is True


def test_original_legacy_mode_is_still_reviewable_but_ipc_never_claimed():
    inv,c,preview=scenario()
    r115.assert_static_tool_and_mcp_boundary(inv['argv'],inv['workspace_repo'])
    with pytest.raises(r115.R115PreclaimBlocked,match='IPC_REVIEW_ONLY_G1_G5_OPEN_NO_LIVE_PRECLAIM'):
        r115.assert_pilot_preclaim(argv=preview,workspace=inv['workspace_repo'],
            systemd_command=['/usr/bin/systemd-run','--property=PrivateNetwork=no'])


@pytest.mark.parametrize('mutator',[
    lambda a: a.__setitem__(0,'/usr/bin/copilot'),
    lambda a: a.__setitem__(9,'view'),
    lambda a: a.insert(9,'edit'),
    lambda a: a.__setitem__(-4,'--no-sandbox'),
    lambda a: a.__setitem__(-5,'20'),
    lambda a: a.__setitem__(5,''),
    lambda a: a.__setitem__(7,'{"mcpServers":{},"mcpServers":{}}'),
    lambda a: a.__setitem__(7,json.dumps(json.loads(a[7]),indent=2)),
    lambda a: a.__setitem__(-1,'/tmp/unapproved'),
])
def test_noncanonical_argv_holds(mutator):
    inv,c,argv=scenario()
    mutator(argv)
    with pytest.raises(r115.R115PreclaimBlocked):
        r115.assert_guarded_ipc_preview(argv,inv['workspace_repo'])

@pytest.mark.parametrize('key,value',[
    ('command','/bin/sh'),('cwd','/tmp/not-workspace'),
    ('type','http'),('tools',['run_repo_head','run_repo_status']),
    ('args',[]),('env',{'TOKEN':'fake'}),
])
def test_proxy_wrong_server_spec_holds(key,value):
    inv,c,argv=scenario()
    obj=json.loads(argv[7]);obj['mcpServers']['ForPrintValidation'][key]=value
    argv[7]=json.dumps(obj,sort_keys=True,separators=(',', ':'),ensure_ascii=True)
    with pytest.raises(r115.R115PreclaimBlocked):
        r115.assert_guarded_ipc_preview(argv,inv['workspace_repo'])

@pytest.mark.parametrize('index,value',[
    (0,'/tmp/other-proxy.py'),(2,'/run/forprint-cf10-r125-0123456789abcdef/mcp-other.sock'),
    (4,'cf10-other-a999'),(6,'../bad'),(8,'g'*40),(10,'other-capsule'),
])
def test_proxy_argument_binding_holds(index,value):
    inv,c,argv=scenario()
    obj=json.loads(argv[7]);obj['mcpServers']['ForPrintValidation']['args'][index]=value
    argv[7]=json.dumps(obj,sort_keys=True,separators=(',', ':'),ensure_ascii=True)
    with pytest.raises(r115.R115PreclaimBlocked):
        r115.assert_guarded_ipc_preview(argv,inv['workspace_repo'])


def test_r030_is_one_canonical_non_authorizing_source_review_seam():
    inv,c,_=scenario();s,p=bound(inv,c)
    r030=route()
    out=r030.review_guarded_ipc_handoff(spec=s,plan=p,invocation=inv,candidate=c)
    assert out['schema_version']=='cf10_r030_guarded_ipc_handoff_review_v0_1'
    assert out['unit']==p['identity']['unit']
    assert out['canonical_argv_sha256']==p['identity']['argv_sha256']
    assert out['candidate_sha256']==c['candidate_sha256']
    assert all(out[k] is False for k in ('live_worker_authorized','claim_consumed','worker_started',
        'terminal_ledger_written','g1_g5_closed','automatic_retry'))
    assert 'fixture prompt' not in json.dumps(out)

@pytest.mark.parametrize('mutation',[
    'attempt','source_head','workspace','argv','task','plan','candidate_digest','switch'
])
def test_r030_drift_or_live_switch_fails_closed(mutation, monkeypatch):
    inv,c,_=scenario();s,p=bound(inv,c);r030=route()
    if mutation=='attempt':inv['attempt_id']='cf10-other-a998'
    if mutation=='source_head':c['source_head']='e'*40
    if mutation=='workspace':inv['workspace_repo']='/tmp/spoof'
    if mutation=='argv':inv['argv'][2]='different'
    if mutation=='task':inv['task_id']='other-task'
    if mutation=='plan':p['identity']['attempt_id']='cf10-other-a998'
    if mutation=='candidate_digest':c['candidate_sha256']='0'*64
    if mutation=='switch':monkeypatch.setattr(r030.backend,'LIVE_CUTOVER_ENABLED',True)
    with pytest.raises(r030.CanonicalCutoverBlocked):
        r030.review_guarded_ipc_handoff(spec=s,plan=p,invocation=inv,candidate=c)



def test_live_switch_fixture_releases_guard_even_after_exception():
    """A negative preview must never leak its temporary live flag into pytest."""
    r030=route()
    assert r030.backend.LIVE_CUTOVER_ENABLED is False
    with pytest.raises(RuntimeError, match='EXPECTED_FIXTURE_ERROR'):
        with mock.patch.object(r030.backend,'LIVE_CUTOVER_ENABLED',True):
            assert r030.backend.LIVE_CUTOVER_ENABLED is True
            raise RuntimeError('EXPECTED_FIXTURE_ERROR')
    assert r030.backend.LIVE_CUTOVER_ENABLED is False


def test_live_gate_false_after_batch_d_negative_cases():
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_systemd_launcher_v0_1 as backend,
    )
    assert backend.LIVE_CUTOVER_ENABLED is False

def test_review_never_enters_r030_runtime_or_root_lease():
    text=(ROOT/'scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py').read_text()
    part=text.split('def review_guarded_ipc_handoff(',1)[1].split('\ndef _trusted_runner(',1)[0]
    for forbidden in ('launch_after_owner_claim(', 'receipts.claim(', 'systemd-run',
       'root_release_marker(', 'subprocess.run(', 'open_socket(', 'commit(', 'git push'):
        assert forbidden not in part


def test_r129_exact_pinned_git_blob_tracks_r115_after_cutover():
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_r129_canonical_lifecycle_convergence_v0_1 as r129,
    )
    import subprocess
    path='scripts/coordination/control_plane/worker_runtime/cf10_r115_preclaim_executable_profile_v0_1.py'
    actual=subprocess.check_output(['git','hash-object',str(ROOT/path)],text=True).strip()
    assert r129.SOURCE_BLOBS[path]==actual
    assert len(actual)==40
