"""R144 joins R141/R143 live review before R140 lab forwarding.

All integration fixtures use actual source types but patched privileged
review side effects; R141/R142/R143 independently test kernel/Git details.
"""
from __future__ import annotations

from pathlib import Path
from contextlib import contextmanager
from unittest import mock
import socket

import pytest

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r140_root_ipc_broker_adapter_v0_1 as api,
    cf10_r141_held_ipc_bridge_origin_v0_1 as r141,
    cf10_r142_canonical_mcp_child_lineage_v0_1 as r142,
    cf10_r143_git_mcp_capsule_origin_v0_1 as r143,
)

HEAD='a'*40
ATTEMPT='cf10-u180j-a900'
UNIT=binding.unit_for(ATTEMPT,HEAD)
LEASE=Path('/run/forprint-cf10-r125-'+'e'*16+'/lease.json')



@contextmanager
def sockets():
    a,b=socket.socketpair()
    try:
        yield a,b
    finally:
        a.close();b.close()

def fixture_values():
    bridge=r141.BridgePin(pid=10491,pidfd=-1,unit=UNIT,start_ticks='123',
        executable=Path('/usr/bin/python3'),executable_dev_ino=(1,2),
        source=LEASE.parent/'bridge.py',source_inode=(1,2,4,'b'*64),
        source_sha256='b'*64,argv=('/usr/bin/python3','-I','-B',str(LEASE.parent/'bridge.py')))
    child=r142.MCPChildPin(pid=10492,pidfd=-1,bridge_pid=bridge.pid,unit=UNIT,
        start_ticks='125',exe_dev_ino=(1,2),source=LEASE.parent/'source_capsule'/r143.MCP,
        source_inode=(1,2,4,'c'*64),
        argv=('/usr/bin/python3','-I','-B',str(LEASE.parent/'source_capsule'/r143.MCP)),
        pipes=('pipe:[11]','pipe:[12]'))
    spec=binding.BoundedInput(task_prompt_id='unit-r144',attempt_id=ATTEMPT,
        source_head=HEAD,handoff_sha256='0'*64,baseline_sha256='1'*64,
        workspace='/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/'+ATTEMPT+'/workspace/repo',
        runtime_root='/srv/software_development/forprint-worker-runtime',
        argv=('/usr/bin/true',),timeout_seconds=30)
    inp=dict(invocation={},candidate={},attempt=ATTEMPT,epoch='epoch-01',
        head=HEAD,lease=LEASE,held_review={},spec=spec,
        plan={'identity':{'unit':UNIT}},witness=object(),bridge_pin=bridge,
        child_pin=child,frozen_source_commit=HEAD,timeout_seconds=3)
    return inp


def proof():
    return {'schema_version':r143.SCHEMA,
        'state':'POST_RELEASE_GIT_PINNED_MCP_REVIEW_ONLY',
        'root_release_readback_proven':False,
        'live_worker_authorized':False,'worker_result_accepted':False,
        'terminal_ledger_written':False,'automatic_retry':False,
        'g1_g5_closed':False,
        'origin':{'source_commit':HEAD,'unit':UNIT,
             'bridge_pid':10491,'mcp_pid':10492,
             'capsule_file_count':14,'mcp_blob_sha256':'c'*64,
             'capsule_manifest_sha256':'d'*64,
             'mcp_process_transport_lineage_proven':True,
             'git_object_source_verified_by_independent_caller':True,
             'copilot_process_tree_proven':False,'copilot_egress_attested':False,
             'credential_isolation_attested':False,'live_worker_authorized':False,
             'worker_result_accepted':False,'terminal_ledger_written':False,
             'g1_g5_closed':False,'automatic_retry':False}}


def relay():
    return {'schema_version':api.SCHEMA,'state':'ONE_READ_ONLY_MCP_SESSION_REVIEW_ONLY',
        'lease_revoked':True,'session_read_only_calls':1,
        'backend_lineage_independently_proven':False,
        'live_worker_authorized':False,'worker_result_accepted':False,
        'terminal_ledger_written':False,'g1_g5_closed':False,'automatic_retry':False}


def call(inputs=None,origin=None,session=None):
    data=fixture_values() if inputs is None else inputs
    original=proof() if origin is None else origin
    with sockets() as pair:  # sockets are real; no process spawned
        client,backend=pair
        with mock.patch.object(api,'_identity',return_value={'unit':UNIT,'attempt_id':ATTEMPT}),\
             mock.patch.object(r141,'review_post_release_bridge',return_value={'state':'post'} ) as bridge_review,\
             mock.patch.object(r143,'review_post_release_git_child',return_value=original) as mcp_review,\
             mock.patch.object(api,'_serve_lab_one',return_value=relay() if session is None else session) as forward,\
             mock.patch.object(api,'_revoke_on_hold') as revoked:
            try:
                result=api.serve_one(listener=client,trusted_mcp=backend,**data)
                return result,bridge_review.call_count,mcp_review.call_count,forward.call_count,revoked.call_count
            except api.BrokerHold:
                return None,bridge_review.call_count,mcp_review.call_count,forward.call_count,revoked.call_count


def test_positive_origin_precedes_first_forward():
    result,pre,mcp,fwd,revoked=call()
    assert pre==mcp==fwd==1 and revoked==0
    assert result['backend_lineage_independently_proven'] is True
    assert result['mcp_pid']==10492
    assert result['capsule_manifest_sha256']=='d'*64
    for key in ('live_worker_authorized','worker_result_accepted','terminal_ledger_written',
                'g1_g5_closed','copilot_process_tree_proven','copilot_egress_attested',
                'credential_isolation_attested','kernel_terminal_proven',
                'root_release_readback_proven','automatic_retry'):
        assert result[key] is False


def test_missing_proof_arguments_never_forward():
    inp=fixture_values();inp.pop('child_pin')
    with sockets() as pair:
        with mock.patch.object(api,'_serve_lab_one') as forward:
            with pytest.raises(TypeError):
                api.serve_one(listener=pair[0],trusted_mcp=pair[1],**inp)
            forward.assert_not_called()


@pytest.mark.parametrize('field,value',[
    ('frozen_source_commit','b'*40),('head','b'*40),
    ('bridge_pin',None),('child_pin',None),
    ('spec',None),('plan',{'identity':{'unit':'wrong'}}),
])
def test_wrong_origin_identity_denied_before_forward(field,value):
    inp=fixture_values();inp[field]=value
    result,_,_,fwd,revoked=call(inp)
    assert result is None and fwd==0 and revoked==1


@pytest.mark.parametrize('key,value',[
    ('source_commit','b'*40),('unit','wrong'),('bridge_pid',3),('mcp_pid',1),
    ('capsule_file_count',13),('mcp_process_transport_lineage_proven',False),
    ('git_object_source_verified_by_independent_caller',False),
    ('terminal_ledger_written',True),('copilot_egress_attested',True),
    ('g1_g5_closed',True),('capsule_manifest_sha256',None)
])
def test_forged_or_incomplete_child_report_denied(key,value):
    obj=proof();obj['origin'][key]=value
    result,pre,mcp,fwd,revoked=call(origin=obj)
    assert result is None and pre==1 and mcp==1 and fwd==0 and revoked==1


@pytest.mark.parametrize('key,value',[
    ('schema_version','wrong'),('state','WRONG'),('root_release_readback_proven',True),
    ('worker_result_accepted',True),('automatic_retry',True)
])
def test_post_review_authority_not_widened(key,value):
    obj=proof();obj[key]=value
    result,_,_,fwd,revoked=call(origin=obj)
    assert result is None and fwd==0 and revoked==1


def test_child_reviewer_exception_revokes_before_forward():
    inp=fixture_values()
    with sockets() as pair:
        with mock.patch.object(api,'_identity',return_value={'unit':UNIT}),\
             mock.patch.object(r141,'review_post_release_bridge',return_value={}),\
             mock.patch.object(r143,'review_post_release_git_child',side_effect=r143.CapsuleHold('tampered')),\
             mock.patch.object(api,'_serve_lab_one') as forward,\
             mock.patch.object(api,'_revoke_on_hold') as revoked:
            with pytest.raises(api.BrokerHold,match='ORIGIN_OR_SESSION_KERNEL_QUARANTINE'):
                api.serve_one(listener=pair[0],trusted_mcp=pair[1],**inp)
            forward.assert_not_called();revoked.assert_called_once()


def test_unproven_revoke_returns_explicit_unknown_kernel_hold():
    inp=fixture_values();inp['frozen_source_commit']='b'*40
    with sockets() as pair:
        with mock.patch.object(api,'_identity',return_value={'unit':UNIT}),\
             mock.patch.object(api,'_revoke_on_hold',side_effect=api.BrokerHold('cannot')):
            with pytest.raises(api.BrokerHold,match='REVOKE_UNKNOWN_KERNEL_QUARANTINE'):
                api.serve_one(listener=pair[0],trusted_mcp=pair[1],**inp)


@pytest.mark.parametrize('field,value',[
    ('lease_revoked',False),('session_read_only_calls',2),
    ('worker_result_accepted',True),('live_worker_authorized',True),
    ('terminal_ledger_written',True)
])
def test_unsealed_session_result_never_returned(field,value):
    r=relay();r[field]=value
    result,_,_,fwd,revoked=call(session=r)
    assert result is None and fwd==1 and revoked==1


def test_root_broker_old_lab_relay_is_private_and_no_second_launcher():
    assert callable(api._serve_lab_one)
    assert api.serve_one is not api._serve_lab_one
    s=Path(api.__file__).read_text()
    assert 'launch_after_owner_claim(' not in s
    assert 'append_record(' not in s
    assert 'systemctl start' not in s
