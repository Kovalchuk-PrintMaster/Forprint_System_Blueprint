#!/usr/bin/env python3
"""CF10 O: pure source-only, provider-neutral root egress attachment candidate.

This is a NON-AUTHORIZING interface joining R079 provider selection, R115/R134
frozen preclaim, R140 root IPC boundary and J's loopback/Unix TLS transport.
No execution, credentials, external egress, claim or terminal success is possible
through this module. It explicitly forbids treating R140's MCP adapter as a
production inference proxy or treating vendor tool sandbox as CLI egress proof.
"""
from __future__ import annotations
from collections.abc import Mapping
import argparse
import hashlib
import json
from pathlib import Path
import re

SCHEMA = 'cf10_root_egress_attachment_candidate_v0_1'
SOURCE_SCHEMA = 'cf10_batch_o_source_pin_audit_v0_1'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
SHA64 = re.compile(r'[0-9a-f]{64}\Z')
ATTEMPT = re.compile(r'cf10-[a-zA-Z0-9_-]{3,80}-a[0-9]{3,5}\Z')
PROVIDER = re.compile(r'[a-z][a-z0-9_]{3,63}\Z')
PINNED_COPILOT_SHA256 = '985f0e1b1b3e734bc996324651307a076ae3deae21e3fa9f9af917983ce309c4'
CANONICAL_FILES = {
    'r079': 'scripts/coordination/control_plane/worker_runtime/cf10_provider_neutral_boundary_v0_1.py',
    'r115': 'scripts/coordination/control_plane/worker_runtime/cf10_r115_preclaim_executable_profile_v0_1.py',
    'r134': 'scripts/coordination/control_plane/worker_runtime/cf10_r134_ipc_preclaim_crosswalk_v0_1.py',
    'r140': 'scripts/coordination/control_plane/worker_runtime/cf10_r140_root_ipc_broker_adapter_v0_1.py',
    'batch_j': 'scripts/coordination/control_plane/worker_runtime/cf10_batch_j_composed_copilot_proxy_contract_v0_1.py',
}
# Explicitly OPEN; proof of a prior fixture is NOT proof of a real Worker.
GATES = (
    'G1_REAL_PROVIDER_EGRESS_NOT_ATTESTED',
    'G2_PROVIDER_AUTH_DELEGATION_NOT_ATTESTED',
    'G3_REAL_COPILOT_INFERENCE_NOT_ATTESTED',
    'G4_CANONICAL_DISPATCHER_EGRESS_ATTACHMENT_NOT_ATTESTED',
    'G5_REAL_WORKER_KERNEL_TERMINAL_NOT_ATTESTED',
)

class AttachmentHold(ValueError):
    pass

def _deny(code: str) -> None:
    raise AttachmentHold('CF10_O_HOLD_' + code)

def _exact(obj: object, fields: set[str], label: str) -> Mapping:
    if not isinstance(obj, Mapping) or set(obj) != fields:
        _deny(label + '_SHAPE')
    return obj

def _hash(value: object, label: str, length=64) -> str:
    pattern = SHA64 if length == 64 else SHA40
    if type(value) is not str or pattern.fullmatch(value) is None:
        _deny(label + '_HASH')
    return value

def _no_secret_material(obj: object) -> None:
    forbidden = {'token','access_token','refresh_token','password','secret',
                 'credential','credentials','authorization','api_key','private_key'}
    if isinstance(obj, Mapping):
        for k,v in obj.items():
            if type(k) is not str or k.lower() in forbidden:
                _deny('SECRET_FIELD_FORBIDDEN')
            _no_secret_material(v)
    elif isinstance(obj, (tuple,list)):
        for x in obj: _no_secret_material(x)
    elif not isinstance(obj, (str,int,bool,type(None))):
        _deny('SERIALIZATION_TYPE')

def plan_attachment(*, frozen: Mapping, provider: Mapping, root_ipc: Mapping,
                    egress: Mapping, runtime: Mapping) -> dict:
    """Return an inert, SHA-bound candidate, never a launchable invocation."""
    fields = {'attempt_id','source_head','frozen_preclaim_sha256','crosswalk_sha256'}
    _exact(frozen,fields,'FROZEN')
    attempt=frozen['attempt_id']
    if type(attempt) is not str or ATTEMPT.fullmatch(attempt) is None:
        _deny('ATTEMPT')
    head=_hash(frozen['source_head'],'SOURCE_HEAD',40)
    _hash(frozen['frozen_preclaim_sha256'],'PRECLAIM')
    _hash(frozen['crosswalk_sha256'],'R134_CROSSWALK')

    _exact(provider,{'provider_id','adapter_route','provider_selection_sha256'},'PROVIDER')
    provider_id=provider['provider_id']
    if type(provider_id) is not str or PROVIDER.fullmatch(provider_id) is None:
        _deny('PROVIDER_ID')
    if provider['adapter_route']!='R079_EXPLICIT_SELECTION':
        _deny('R079_ROUTE')
    _hash(provider['provider_selection_sha256'],'PROVIDER_SELECTION')

    _exact(root_ipc,{'adapter','lease','external_revoke','session_fence',
                     'lineage_independently_proven'},'ROOT_IPC')
    if (root_ipc['adapter']!='R140_EXISTING_ROOT_IPC' or
        root_ipc['lease']!='R125_DISPOSABLE_ONLY' or
        root_ipc['external_revoke']!='R126' or
        root_ipc['session_fence']!='R135' or
        root_ipc['lineage_independently_proven'] is not False):
        _deny('CANONICAL_ROOT_IPC_CONTRACT')

    _exact(egress,{'route','upstream_policy','approved_hosts','egress_tested',
                   'credentials_delegated'},'EGRESS')
    if (egress['route']!='J_LOOPBACK_TO_UNIX_CONNECT_CANDIDATE' or
        egress['upstream_policy']!='DENY_ALL_UNTIL_SEPARATELY_ATTESTED' or
        type(egress['approved_hosts']) is not list or egress['approved_hosts'] or
        egress['egress_tested'] is not False or egress['credentials_delegated'] is not False):
        _deny('EGRESS_FAIL_CLOSED')

    _exact(runtime,{'runner_uid','runner_gid','binary_sha256','private_network',
                    'direct_external_ip_blocked','inference_enabled','worker_claim_used',
                    'live_dispatch_enabled'},'RUNTIME')
    if (type(runtime['runner_uid']) is not int or runtime['runner_uid']!=996 or
        type(runtime['runner_gid']) is not int or runtime['runner_gid']!=992 or
        runtime['private_network'] is not True or
        runtime['direct_external_ip_blocked'] is not True or
        runtime['inference_enabled'] is not False or
        runtime['worker_claim_used'] is not False or
        runtime['live_dispatch_enabled'] is not False):
        _deny('RUNTIME_FAIL_CLOSED')
    _hash(runtime['binary_sha256'],'BINARY')
    if provider_id == 'github_copilot_cli':
        if runtime['binary_sha256'] != PINNED_COPILOT_SHA256:
            _deny('COPILOT_PIN')
    else:
        # Do not infer readiness of Claude/Codex/other providers from Copilot proof.
        _deny('PROVIDER_NOT_AUDITED')

    for obj in (frozen,provider,root_ipc,egress,runtime):
        _no_secret_material(obj)
    payload={
        'schema':SCHEMA,
        'attempt_id':attempt,'source_head':head,
        'frozen_preclaim_sha256':frozen['frozen_preclaim_sha256'],
        'crosswalk_sha256':frozen['crosswalk_sha256'],
        'provider_selection_sha256':provider['provider_selection_sha256'],
        'provider_id':provider_id,'root_ipc_adapter':root_ipc['adapter'],
        'egress_route':egress['route'],'approved_hosts':[],
        'open_gates':list(GATES),
        'source_only':True,'authority':False,
        'live_worker_authorized':False,'inference_enabled':False,
        'credentials_delegated':False,'external_egress_enabled':False,
        'dispatcher_integrated':False,'terminal_proven':False,
        'provider_native_sandbox_counts_as_isolation':False,
        'kernel_fixture_counts_as_live_worker_proof':False,
        'automatic_retry':False,'git_mutation_authorized_by_contract':False,
    }
    body=json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
    payload['candidate_sha256']=hashlib.sha256(body).hexdigest()
    return payload


def test_vector() -> dict:
    a='a'*64; b='b'*64; c='c'*64; d='d'*64
    return {
      'frozen':{'attempt_id':'cf10-u180j-a054','source_head':'f6938f6db956b4b645133a07b07daf1cc413a914',
                'frozen_preclaim_sha256':a,'crosswalk_sha256':b},
      'provider':{'provider_id':'github_copilot_cli','adapter_route':'R079_EXPLICIT_SELECTION',
                  'provider_selection_sha256':c},
      'root_ipc':{'adapter':'R140_EXISTING_ROOT_IPC','lease':'R125_DISPOSABLE_ONLY',
                  'external_revoke':'R126','session_fence':'R135','lineage_independently_proven':False},
      'egress':{'route':'J_LOOPBACK_TO_UNIX_CONNECT_CANDIDATE',
                'upstream_policy':'DENY_ALL_UNTIL_SEPARATELY_ATTESTED','approved_hosts':[],
                'egress_tested':False,'credentials_delegated':False},
      'runtime':{'runner_uid':996,'runner_gid':992,'binary_sha256':PINNED_COPILOT_SHA256,
                 'private_network':True,'direct_external_ip_blocked':True,
                 'inference_enabled':False,'worker_claim_used':False,
                 'live_dispatch_enabled':False},
    }


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=['source-check','candidate-demo'],required=True)
    a=p.parse_args(argv)
    try:
        result=plan_attachment(**test_vector())
        assert len(result['open_gates']) == 5 and result['authority'] is False
        print('CF10_O=PASS_INERT_EGRESS_ATTACHMENT_CONTRACT')
        print('CF10_O_CANDIDATE_SHA256='+result['candidate_sha256'])
        print('CF10_O_G1_G5=OPEN_NO_LIVE_ADMISSION')
        return 0
    except (AttachmentHold, AssertionError, ValueError,TypeError,KeyError) as exc:
        print('CF10_O=HOLD_'+type(exc).__name__)
        return 3

if __name__=='__main__':raise SystemExit(main())
