#!/usr/bin/env python3
"""CF10 Y: one governed first-live-Copilot-Worker critical-path admission REVIEW.

This is an operational, machine-readable PRE-LAUNCH decision surface.
It reuses canonical R079/R115/R134/R140 plus W/X; it cannot invoke them with
launch authority. Input evidence is untrusted. An evidence ZIP, matching SHA,
provider token file metadata or CLI help text never grants worker release.

No external egress, credential reads, Worker claims, systemd mutation,
launch retries, terminal ledger writes or historical-attempt rebinds.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
import re

SCHEMA = 'cf10_first_worker_critical_path_v0_1'
REVIEW = 'cf10_first_worker_prelaunch_review_v0_1'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
SHA64 = re.compile(r'[0-9a-f]{64}\Z')
PROVIDER = 'github_copilot_cli'
BIN_SHA = '985f0e1b1b3e734bc996324651307a076ae3deae21e3fa9f9af917983ce309c4'
GATES = {
 'G1': 'PROVIDER_HOST_POLICY_AND_REAL_EXTERNAL_EGRESS_UNVERIFIED',
 'G2': 'CREDENTIAL_NONEXPOSURE_AND_PROVIDER_AUTH_UNVERIFIED',
 'G3': 'REAL_MODEL_INFERENCE_RESULT_UNVERIFIED',
 'G4': 'CANONICAL_DISPATCHER_WORKER_RELEASE_UNVERIFIED',
 'G5': 'REAL_WORKER_KERNEL_TERMINAL_AND_LEDGER_UNVERIFIED',
}
SEQUENCE = (
 'RECONCILE_CANONICAL_SOURCE_AND_DIRTY_WORKTREE',
 'ATTEST_PROVIDER_AUTH_OUTSIDE_WORKER_WITHOUT_TOKEN_IN_CHILD',
 'PIN_REAL_PROVIDER_DESTINATIONS_AND_ROOT_ONLY_EGRESS',
 'ATTEST_PINNED_COPILOT_WITH_CONTROLLED_PROVIDER_EXCHANGE',
 'BIND_R115_R134_TO_EXISTING_DISPATCHER_NO_ALTERNATE_LAUNCHER',
 'ISSUE_FRESH_OWNER_AUTHORIZED_CLAIM_ONCE',
 'KERNEL_1_TO_0_TERMINAL_LEDGER_AND_INDEPENDENT_RESULT_REVIEW',
 'PREPARE_NEXT_WORKER_ONLY_AFTER_FINAL_REVIEW',
)
SECRET_KEYS=frozenset((
 'COPILOT_GITHUB_TOKEN','GH_TOKEN','GITHUB_TOKEN','GITHUB_PERSONAL_ACCESS_TOKEN',
 'COPILOT_PROVIDER_API_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY',
))

class AdmissionHold(ValueError):
    pass

def deny(code: str) -> None:
    raise AdmissionHold('CF10_Y_HOLD_'+code)

def digest(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest()

def _exact(obj: object, keys: set[str], name: str) -> Mapping:
    if not isinstance(obj,Mapping) or set(obj)!=keys:
        deny(name+'_SCHEMA')
    return obj

def no_secret_fields(obj: object, *, depth: int=0) -> None:
    """Reject credential-shaped material; never inspect or serialize secret values."""
    if depth>10:deny('NESTING')
    forbidden=frozenset((
        'token','password','secret','authorization','api_key','access_token',
        'refresh_token','credential','credentials','env','environment','private_key',
        'copilot_github_token','gh_token','github_token','cookie','headers',
    ))
    if isinstance(obj, Mapping):
        for k,v in obj.items():
            if type(k) is not str or k.lower() in forbidden:
                deny('SECRET_FIELD')
            no_secret_fields(v,depth=depth+1)
    elif isinstance(obj,(list,tuple)):
        for v in obj:no_secret_fields(v,depth=depth+1)
    elif type(obj) not in (bool,int,str,type(None)):
        deny('UNSAFE_VALUE')

def check_credential_boundary(row: Mapping) -> dict:
    """Presence/permissions NEVER prove usable auth or non-exposure to tools."""
    keys={'source','root_owns_material','group_or_world_access','material_read',
          'passed_to_cli_env','passed_to_child_tools','credential_exchange_attested'}
    _exact(row,keys,'CREDENTIAL_BOUNDARY')
    if row['source'] not in ('UNCONFIGURED','ROOT_EXTERNAL_HANDLE_REVIEW_ONLY'):
        deny('CREDENTIAL_SOURCE')
    for k in keys-{'source'}:
        if type(row[k]) is not bool:deny('CREDENTIAL_BOOLEAN_'+k)
    if row['material_read'] or row['passed_to_cli_env'] or row['passed_to_child_tools']:
        deny('CREDENTIAL_EXPOSURE')
    if row['group_or_world_access'] or row['credential_exchange_attested']:
        deny('UNTRUSTED_CREDENTIAL_ASSERTION')
    if row['source']=='UNCONFIGURED' and row['root_owns_material']:
        deny('CREDENTIAL_CONTRADICTION')
    return {'candidate':'ROOT_EXTERNAL_HANDLE_NOT_PROOF',
            'root_only_file_metadata_seen':row['root_owns_material'],
            'provider_auth_proven':False,
            'child_credential_isolation_proven':False,
            'credential_material_read':False,
            'live_credential_delegation_authorized':False}

def check_egress_boundary(row: Mapping) -> dict:
    """Treat W/X as a fixture, not an upstream transport for real provider."""
    _exact(row,{'transport','real_provider_hosts','root_upstream_enabled',
                'direct_worker_ipv4_ipv6_blocked','live_provider_tls_proven',
                'provider_network_auth_attested'},'EGRESS')
    if row['transport']!='W_X_LOCAL_SYNTHETIC_TLS_ONLY':deny('EGRESS_TRANSPORT')
    if row['real_provider_hosts']!=[]:deny('EGRESS_HOSTS_NOT_REVIEWED')
    for k in ('root_upstream_enabled','direct_worker_ipv4_ipv6_blocked',
              'live_provider_tls_proven','provider_network_auth_attested'):
        if type(row[k]) is not bool:deny('EGRESS_BOOLEAN')
    if (row['root_upstream_enabled'] or row['live_provider_tls_proven'] or
            row['provider_network_auth_attested']):deny('EGRESS_LIVE_ASSERTION')
    if row['direct_worker_ipv4_ipv6_blocked'] is not True:
        deny('WORKER_NETWORK_ISOLATION_NOT_ATTESTED')
    return {'fixture_tls_proven':True,'real_provider_network_proven':False,
            'real_destinations_approved':False,'worker_direct_network_denied':True,
            'production_egress_authorized':False}

def plan(*, source_head: str, identity: Mapping, credential: Mapping,
         egress: Mapping, dispatcher: Mapping, terminal: Mapping) -> dict:
    """No route here can ever turn OPEN into authorized; only canonical issuer can."""
    if type(source_head) is not str or not SHA40.fullmatch(source_head):deny('SOURCE_HEAD')
    _exact(identity,{'provider','binary_sha256','cli_offline_executed',
                     'model_response_attested'},'IDENTITY')
    if (identity['provider']!=PROVIDER or identity['binary_sha256']!=BIN_SHA or
        identity['cli_offline_executed'] is not True or
        identity['model_response_attested'] is not False):deny('PROVIDER_PIN_OR_MODEL')
    auth=check_credential_boundary(credential)
    net=check_egress_boundary(egress)
    _exact(dispatcher,{'r115_frozen','r134_review_only','r140_mcp_only',
                       'canonical_worker_dispatched','claim_consumed',
                       'live_cutover_enabled'},'DISPATCHER')
    if any(type(x) is not bool for x in dispatcher.values()):deny('DISPATCHER_TYPES')
    if (dispatcher['r115_frozen'] is not True or dispatcher['r134_review_only'] is not True
        or dispatcher['r140_mcp_only'] is not True or
        dispatcher['canonical_worker_dispatched'] is not False or
        dispatcher['claim_consumed'] is not False or
        dispatcher['live_cutover_enabled'] is not False):deny('CANONICAL_AUTHORITY')
    _exact(terminal,{'lab_kernel_1_to_0','real_worker_kernel_1_to_0',
                     'durable_terminal_ledger','independent_result_review'},'TERMINAL')
    if any(type(x) is not bool for x in terminal.values()):deny('TERMINAL_TYPES')
    if (terminal['lab_kernel_1_to_0'] is not True or
        any(terminal[k] is not False for k in ('real_worker_kernel_1_to_0',
                 'durable_terminal_ledger','independent_result_review'))):
        deny('TERMINAL_AUTHORITY')
    no_secret_fields(identity)
    no_secret_fields(credential)
    no_secret_fields(egress)
    no_secret_fields(dispatcher)
    no_secret_fields(terminal)
    result={'schema':REVIEW,'source_head':source_head,'provider_id':PROVIDER,
       'pinned_binary_sha256':BIN_SHA,'credential_boundary':auth,'egress_boundary':net,
       'dispatcher_canonical_R115_R134_R140_observed':True,
       'lab_kernel_terminal_observed':True,'real_worker_terminal_proven':False,
       'gates':dict(GATES),'all_gates_open':True,'required_sequence':list(SEQUENCE),
       'owner_authority_granted':False,'source_only':True,
       'worker_claim_consumed':False,'provider_inference_executed':False,
       'worker_launched':False,'terminal_ledger_written':False,'result_accepted':False,
       'automatic_retry':False,'next_attempt_prepared':False,
       'network_policy_modified':False,'hestia_or_sudoers_modified':False}
    result['review_sha256']=digest(result)
    return result

def fixture():
    return {'source_head':'d9911cb24f03ee443cad6adea945dcab826b8293',
      'identity':{'provider':PROVIDER,'binary_sha256':BIN_SHA,
                  'cli_offline_executed':True,'model_response_attested':False},
      'credential':{'source':'UNCONFIGURED','root_owns_material':False,
        'group_or_world_access':False,'material_read':False,
        'passed_to_cli_env':False,'passed_to_child_tools':False,
        'credential_exchange_attested':False},
      'egress':{'transport':'W_X_LOCAL_SYNTHETIC_TLS_ONLY','real_provider_hosts':[],
        'root_upstream_enabled':False,'direct_worker_ipv4_ipv6_blocked':True,
        'live_provider_tls_proven':False,'provider_network_auth_attested':False},
      'dispatcher':{'r115_frozen':True,'r134_review_only':True,'r140_mcp_only':True,
        'canonical_worker_dispatched':False,'claim_consumed':False,
        'live_cutover_enabled':False},
      'terminal':{'lab_kernel_1_to_0':True,
        'real_worker_kernel_1_to_0':False,'durable_terminal_ledger':False,
        'independent_result_review':False}}

def source_check() -> dict:
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_provider_neutral_boundary_v0_1 as r079,
        cf10_r115_preclaim_executable_profile_v0_1 as r115,
        cf10_r134_ipc_preclaim_crosswalk_v0_1 as r134,
        cf10_r140_root_ipc_broker_adapter_v0_1 as r140,
        cf10_inference_egress_session_v0_1 as w,
        cf10_egress_transport_join_v0_1 as x,
        cf10_systemd_launcher_v0_1 as launcher)
    for candidate in (r079,r115,r134,r140,w,x):
        if candidate is None:deny('CANONICAL_IMPORT')
    if launcher.LIVE_CUTOVER_ENABLED is not False:
        deny('LIVE_SWITCH_NOT_CLOSED')
    w.source_check()
    x.source_check()
    result=plan(**fixture())
    if (result['worker_launched'] or result['owner_authority_granted'] or
            result['terminal_ledger_written'] or not result['all_gates_open']):
        deny('SOURCE_OPEN_AUTHORITY')
    return result

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('source-check','print-gates'),required=True)
    args=p.parse_args(argv)
    try:
        record=source_check()
    except (AdmissionHold,ValueError,TypeError,KeyError,AssertionError,
            ImportError,AttributeError) as exc:
        print('CF10_Y=HOLD_'+type(exc).__name__)
        return 3
    print('CF10_Y=PASS_FIRST_WORKER_GOVERNED_PRELAUNCH_REVIEW_ONLY')
    print('CF10_Y_REVIEW_SHA256='+record['review_sha256'])
    print('CF10_Y_G1_G5=OPEN_NO_RELEASE')
    if args.mode=='print-gates':
        for gate,reason in record['gates'].items():print(gate+'='+reason)
    return 0
if __name__=='__main__':raise SystemExit(main())
