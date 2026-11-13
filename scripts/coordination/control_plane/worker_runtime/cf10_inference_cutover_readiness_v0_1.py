#!/usr/bin/env python3
"""CF-10 U: fail-closed, non-authorizing real-inference cutover readiness review.

This module is a durable, source-only crosswalk. It does not run Copilot, route
HTTP, authenticate, launch a Worker, issue claims, or report G1-G5 success.
All historical evidence is treated as untrusted observational input, never as
permission to release or as an attestation of provider behaviour.

One bridge for the existing R079, R115, R134, R140 and Batch J components:
R140 is MCP IPC, NOT an inference egress proxy. The prior J proxy was fixture
only. A root-governed upstream/auth implementation remains separate work.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
import re

SCHEMA='cf10_inference_cutover_readiness_review_v0_1'
SNAPSHOT_SCHEMA='cf10_batch_t_consolidated_copilot_egress_readiness_v0_1'
PINNED_HEAD='8aa8fe76542b7556d8287fcdc28eec44ff50462c'
COPILOT_SHA='985f0e1b1b3e734bc996324651307a076ae3deae21e3fa9f9af917983ce309c4'
SHA40=re.compile(r'[a-f0-9]{40}\Z')
SHA64=re.compile(r'[a-f0-9]{64}\Z')
GATES={
 'G1': 'REAL_PROVIDER_EGRESS_AND_DESTINATION_POLICY_NOT_ATTESTED',
 'G2': 'PROVIDER_AUTH_DELEGATION_OUTSIDE_WORKER_NOT_ATTESTED',
 'G3': 'REAL_COPILOT_INFERENCE_RESULT_NOT_ATTESTED',
 'G4': 'CANONICAL_DISPATCHER_ROOT_EGRESS_INTEGRATION_NOT_ATTESTED',
 'G5': 'REAL_WORKER_KERNEL_TERMINAL_LEDGER_NOT_ATTESTED',
}
ARCHITECTURE={
 'selector':'R079_PROVIDER_NEUTRAL_SOURCE_ONLY',
 'frozen_preclaim':'R115_WITH_R134_REVIEW_ONLY',
 'root_ipc':'R140_MCP_BROKER_NOT_INFERENCE_PROXY',
 'network_fixture':'BATCH_J_SYNTHETIC_TLS_ONLY',
 'terminal_fixture':'BATCH_L_RETAINED_KERNEL_1_TO_0_LAB_ONLY',
 'production_egress':'NOT_IMPLEMENTED_OR_ATTESTED',
}
class ReadinessHold(ValueError):pass

def _deny(code):raise ReadinessHold('CF10_U_HOLD_'+code)
def _sha(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
def _typed_bool_false(v):return v is False

def review(snapshot: Mapping, *, expected_dirty_fingerprint: str) -> dict:
    """Strictly describe observable facts; never grant authority from an evidence file."""
    if not isinstance(snapshot,Mapping) or snapshot.get('schema')!=SNAPSHOT_SCHEMA:
        _deny('SNAPSHOT_SCHEMA')
    if snapshot.get('base_head')!=PINNED_HEAD or snapshot.get('status')!='CF10_BATCH_T_HOLD_KERNEL_PIN_READ_ERROR':
        _deny('SNAPSHOT_BASELINE_OR_STATUS')
    if type(expected_dirty_fingerprint) is not str or not SHA64.fullmatch(expected_dirty_fingerprint):
        _deny('DIRTY_HASH')
    pre=snapshot.get('preflight')
    if not isinstance(pre,Mapping) or pre.get('head')!=PINNED_HEAD or pre.get('copilot_sha256')!=COPILOT_SHA:
        _deny('PINNED_EXECUTABLE_OR_HEAD')
    if pre.get('dirty_fingerprint')!=expected_dirty_fingerprint or pre.get('dirty_tracked_count')!=18:
        _deny('SOURCE_FINGERPRINT')
    if pre.get('index_empty') is not True or pre.get('runner_uid')!=996 or pre.get('runner_gid')!=992:
        _deny('SOURCE_OR_RUNNER')
    reg=snapshot.get('regression');extended=snapshot.get('extended_regression')
    if not isinstance(reg,Mapping) or reg.get('exit_code')!=0 or not isinstance(extended,Mapping) or extended.get('exit_code')!=0:
        _deny('REGRESSION_HOLD')
    phases=snapshot.get('child_phases')
    if phases!=['STARTED','VERSION_DONE','HELP_DONE','PROMPT_BEGIN','PROMPT_END']:
        _deny('CHILD_PHASES')
    obs=snapshot.get('child_observations');cli=obs.get('copilot') if isinstance(obs,Mapping) else None
    if not isinstance(obs,Mapping) or obs.get('uid')!=996 or obs.get('gid')!=992 or not isinstance(cli,Mapping):
        _deny('COPILOT_OBSERVATION')
    version=obs.get('offline_version')
    if not isinstance(version,Mapping) or version.get('exit_code')!=0 or version.get('version_1_0_107_observed') is not True:
        _deny('COPILOT_VERSION')
    if cli.get('argv_mode')!='PINNED_REAL_COPILOT_P_WITHOUT_AUTH' or type(cli.get('exit_code')) is not int:
        _deny('CLI_MODE')
    if any(type(cli.get(k)) is not int or cli[k]<0 for k in ('proxy_http_requests','proxy_wellformed_connect_count','real_upstream_connections')):
        _deny('PROXY_COUNTS')
    if (cli['real_upstream_connections']!=0 or cli.get('external_egress_enabled') is not False or
        cli.get('provider_inference_proven') is not False or cli.get('timeout_or_forced_stop') is not False):
        _deny('AUTHORITY_OR_EGRESS_DRIFT')
    if cli.get('proxy_routing_evidence') is not (cli['proxy_wellformed_connect_count']>0):
        _deny('PROXY_COUNTER_CONTRADICTION')
    for k in ('direct_external_ipv4','direct_external_ipv6'):
        v=obs.get(k)
        if not isinstance(v,Mapping) or v.get('denied') is not True:_deny('EXTERNAL_NETWORK')
    if obs.get('fake_credentials_denied') is not True:_deny('CREDENTIALS')
    layout=snapshot.get('runtime_layout')
    if not isinstance(layout,Mapping) or layout.get('layout_readback')!='PASS' or layout.get('dir_mode')!='0750':
        _deny('SANDBOX_LAYOUT')
    kernel=snapshot.get('kernel')
    if not isinstance(kernel,Mapping) or kernel.get('pinned_fd_initial_populated')!='1' or kernel.get('pinned_fd_final_populated')=='0':
        _deny('KERNEL_OBSERVATION_MISMATCH')
    systemd=snapshot.get('systemd_postflight')
    if not isinstance(systemd,Mapping) or systemd.get('active')!='inactive' or systemd.get('main_pid')!='0' or systemd.get('unit_result')!='success':
        _deny('SYSTEMD_NOT_INACTIVE')
    authority=snapshot.get('authority')
    if not isinstance(authority,Mapping) or any(authority.get(key) is not False for key in ('external_egress','git_commit','live_worker','production_modified','provider_credentials_used','worker_claim','automatic_retry')):
        _deny('AUTHORITY_CLAIM')
    counts=cli['proxy_wellformed_connect_count']
    result={
      'schema':SCHEMA,'source_head':PINNED_HEAD,'source_fingerprint':expected_dirty_fingerprint,
      'provider_id':'github_copilot_cli','pinned_cli_sha256':COPILOT_SHA,
      'cli_executed_p':True,'cli_prompt_exit_code':cli['exit_code'],
      'cli_proxy_connect_count':counts,
      'cli_proxy_route_proven':counts>0,
      'no_proxy_routing_conclusion_permitted':False,
      'provider_authenticated':False,'inference_result_proven':False,
      'systemd_disposable_inactive':True,'kernel_initial_populated':'1',
      'kernel_final_zero_proven':False,'terminal_failure_kind':'PINNED_FD_READ_LOST_OR_ERROR',
      'r140_not_an_inference_proxy':True,'native_tool_sandbox_not_cli_egress_proof':True,
      'architectural_contracts':dict(ARCHITECTURE),
      'gates':dict(GATES),'all_gates_open':True,
      'next_frontier':'GOVERNED_PROVIDER_AUTH_EGRESS_AND_CANONICAL_ADAPTER_CUTOVER',
      'operator_authorization_granted':False,'live_dispatch_enabled':False,
      'claim_consumed':False,'production_modified':False,
      'terminal_ledger_written':False,'worker_result_accepted':False,'automatic_retry':False,
    }
    result['review_sha256']=_sha(result)
    return result


def synthetic_baseline():
    fingerprint='9e17680295581ff07bc2ae913a96fdc4cf86c88be60078ba03d1866ab3d9792d'
    return {'schema':SNAPSHOT_SCHEMA,'base_head':PINNED_HEAD,'status':'CF10_BATCH_T_HOLD_KERNEL_PIN_READ_ERROR',
     'preflight':{'head':PINNED_HEAD,'copilot_sha256':COPILOT_SHA,'dirty_fingerprint':fingerprint,
                  'dirty_tracked_count':18,'index_empty':True,'runner_uid':996,'runner_gid':992},
     'regression':{'exit_code':0},'extended_regression':{'exit_code':0},
     'child_phases':['STARTED','VERSION_DONE','HELP_DONE','PROMPT_BEGIN','PROMPT_END'],
     'child_observations':{'uid':996,'gid':992,'offline_version':{'exit_code':0,'version_1_0_107_observed':True},
      'copilot':{'argv_mode':'PINNED_REAL_COPILOT_P_WITHOUT_AUTH','exit_code':1,'proxy_http_requests':0,
       'proxy_wellformed_connect_count':0,'real_upstream_connections':0,'external_egress_enabled':False,
       'provider_inference_proven':False,'timeout_or_forced_stop':False,'proxy_routing_evidence':False},
      'direct_external_ipv4':{'denied':True},'direct_external_ipv6':{'denied':True},
      'fake_credentials_denied':True},
     'runtime_layout':{'layout_readback':'PASS','dir_mode':'0750'},
     'kernel':{'pinned_fd_initial_populated':'1'},
     'systemd_postflight':{'active':'inactive','main_pid':'0','unit_result':'success'},
     'authority':dict.fromkeys(('external_egress','git_commit','live_worker','production_modified',
                                 'provider_credentials_used','worker_claim','automatic_retry'),False)}

def source_check():
    snapshot=synthetic_baseline();result=review(snapshot,expected_dirty_fingerprint=snapshot['preflight']['dirty_fingerprint'])
    if result['live_dispatch_enabled'] or not result['all_gates_open'] or result['kernel_final_zero_proven']:
        _deny('AUTHORITY_DRIFT')
    return result

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--mode',required=True,choices=['source-check']);p.parse_args(argv)
    try:
        x=source_check()
        print('CF10_U=PASS_FAIL_CLOSED_CUTOVER_REVIEW_ONLY')
        print('CF10_U_REVIEW_SHA256='+x['review_sha256'])
        print('CF10_U_G1_G5=OPEN_NO_LIVE_AUTHORITY')
        return 0
    except (ReadinessHold,ValueError,TypeError,KeyError) as exc:
        print(str(exc) if isinstance(exc,ReadinessHold) else 'CF10_U_HOLD_'+type(exc).__name__)
        return 3
if __name__=='__main__':raise SystemExit(main())
