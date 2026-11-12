#!/usr/bin/env python3
"""First-live Copilot pre-admission; observational evidence NEVER confers authority.

Provider-neutral contract shape. The root survey is allowed to test a fixed,
unauthenticated TLS _ping against official GitHub hosts, but this must not be
confused with provider inference routing, credentials isolation, or G1 closure.
No Worker, claim, production writes, provider tokens or user-supplied prompts.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections.abc import Mapping

SCHEMA='cf10_ai_pre_admission_contract_v0_1'
GATES=['G1','G2','G3','G4','G5']
ENDPOINTS=('copilot-proxy.githubusercontent.com','api.githubcopilot.com')
BINARY_SHA='985f0e1b1b3e734bc996324651307a076ae3deae21e3fa9f9af917983ce309c4'
CLI_FLAGS=('--no-auto-update','--no-ask-user','--deny-tool','--no-custom-instructions','--output-format')
SHA40=re.compile(r'[0-9a-f]{40}\Z')
SHA64=re.compile(r'[0-9a-f]{64}\Z')
PROMPT='Reply with exactly FORPRINT_CF10_FIRST_INFERENCE_OK. Do not use tools or access files.'
DENY_TOOLS=('read','write','shell','url','memory')
class AdmissionHold(ValueError):pass

def deny(code):raise AdmissionHold('CF10_AI_HOLD_'+code)
def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest()
def exact(obj,fields,tag):
    if not isinstance(obj,Mapping) or set(obj)!=set(fields):deny(tag+'_SHAPE')
    return obj

def one_ping(row,host):
    exact(row,{'host','path','state','http_status','tls_certificate_verified','response_bytes'},'TLS_ROW')
    if row['host']!=host or row['path']!='/_ping':deny('TLS_HOST_OR_PATH')
    if row['state'] not in ('PASS_TLS_200','HOLD_NETWORK','HOLD_TLS_OR_CERT','HOLD_HTTP_STATUS','HOLD_RESPONSE_SIZE'):
        deny('TLS_STATE')
    if type(row['response_bytes']) is not int or not 0<=row['response_bytes']<=1024:deny('TLS_BYTES')
    if row['state']=='PASS_TLS_200':
        if row['tls_certificate_verified'] is not True or type(row['http_status']) is not int or row['http_status']!=200:
            deny('TLS_PASS_UNVERIFIED')
    elif row['tls_certificate_verified'] is not False or (row['http_status'] is not None and (type(row['http_status']) is not int or not 100<=row['http_status']<=599)):
        deny('TLS_FAILURE_SHAPE')
    return dict(row)

def one_cli(row):
    exact(row,{'pinned_sha256','binary_verified_by_r115','help_exit_code','help_flag_matches',
               'offline_no_auto_update','credential_env_passed','provider_inference'},'CLI')
    if (row['pinned_sha256']!=BINARY_SHA or type(row['binary_verified_by_r115']) is not bool or
        row['offline_no_auto_update'] is not True or row['credential_env_passed'] is not False or
        row['provider_inference'] is not False):deny('CLI_PIN_OR_AUTH')
    if row['help_exit_code'] is not None and (type(row['help_exit_code']) is not int or not -255<=row['help_exit_code']<=255):deny('CLI_RC')
    flags=exact(row['help_flag_matches'],set(CLI_FLAGS),'FLAGS')
    if any(type(x) is not bool for x in flags.values()):deny('CLI_FLAGS_BOOLEAN')
    if row['binary_verified_by_r115'] is False and row['help_exit_code'] is not None:deny('CLI_UNPINNED_EXEC')
    return dict(row)

def one_credential(row):
    expected={'source','root_owns_material','group_or_world_access','material_read','passed_to_cli_env',
              'passed_to_child_tools','credential_exchange_attested','metadata_status'}
    exact(row,expected,'CREDENTIAL')
    if row['source'] not in ('UNCONFIGURED','ROOT_EXTERNAL_HANDLE_REVIEW_ONLY'):
        deny('CREDENTIAL_SOURCE')
    for k in expected-{'source','metadata_status'}:
        if type(row[k]) is not bool:deny('CREDENTIAL_BOOLEAN')
    if (row['material_read'] is not False or row['passed_to_cli_env'] is not False or
        row['passed_to_child_tools'] is not False or row['credential_exchange_attested'] is not False or
        row['group_or_world_access'] is not False):deny('CREDENTIAL_AUTHORITY')
    if row['metadata_status'] not in ('UNCONFIGURED','ROOT_METADATA_ONLY','HOLD_PATH_OR_OWNERSHIP'):
        deny('CREDENTIAL_METADATA_STATUS')
    if row['source']=='UNCONFIGURED' and row['root_owns_material']:deny('CREDENTIAL_CONTRADICTION')
    if row['metadata_status']=='ROOT_METADATA_ONLY' and not row['root_owns_material']:
        deny('CREDENTIAL_NOT_ROOT_ONLY')
    return dict(row)

def plan(*,source_head:str,network:Mapping,cli:Mapping,credential:Mapping,canonical:Mapping):
    if type(source_head) is not str or SHA40.fullmatch(source_head) is None:deny('HEAD')
    exact(network,set(ENDPOINTS),'NETWORK_ENDPOINTS')
    ordered=[one_ping(network[h],h) for h in ENDPOINTS]
    cli=one_cli(cli)
    credential=one_credential(credential)
    exact(canonical,{'live_cutover_enabled','canonical_claim_consumed','production_ledger_written',
                     'independent_owner_ack','production_dispatcher_authorized'},'CANONICAL')
    if any(canonical[k] is not False for k in canonical):deny('CANONICAL_AUTHORITY')
    # Root access to a public /_ping endpoint is NOT a governed Worker egress route.
    root_ping_count=sum(p['state']=='PASS_TLS_200' for p in ordered)
    all_help=cli['help_exit_code']==0 and all(cli['help_flag_matches'].values())
    blockers=['G1_REAL_WORKER_EGRESS_POLICY_AND_ROOT_BROKER_NOT_ATTESTED',
              'G2_PROVIDER_AUTH_AND_SECRET_NONEXPOSURE_NOT_ATTESTED',
              'G3_REAL_MODEL_INFERENCE_RESULT_NOT_ATTESTED',
              'G4_CANONICAL_DISPATCHER_RELEASE_NOT_ATTESTED',
              'G5_REAL_AUTHENTICATED_WORKER_TERMINAL_LEDGER_NOT_ATTESTED']
    if not cli['binary_verified_by_r115'] or not all_help:
        blockers.append('OFFLINE_CLI_HELP_PIN_OR_FLAGS_UNVERIFIED')
    if root_ping_count!=len(ENDPOINTS):blockers.append('ROOT_DIRECT_TLS_PING_PARTIAL_OR_BLOCKED')
    if credential['metadata_status']!='ROOT_METADATA_ONLY':blockers.append('CREDENTIAL_HANDLE_METADATA_UNCONFIGURED_OR_BLOCKED')
    result={'schema':SCHEMA,'status':'PASS_COMPLETED_OBSERVATIONAL_PRE_ADMISSION_ONLY',
      'source_head':source_head,'provider_id':'github_copilot_cli',
      'pinned_executable_sha256':BINARY_SHA,'root_direct_tls_probe':ordered,
      'root_tls_ping_pass_count':root_ping_count,'direct_tls_not_worker_egress_attestation':True,
      'cli_source_and_help':cli,'credential_metadata':credential,
      'first_inference_candidate':{'prompt_sha256':hashlib.sha256(PROMPT.encode()).hexdigest(),
          'prompt_bytes':len(PROMPT.encode()),'fixed_task':'FIRST_READ_ONLY_NO_TOOLS_MODEL_PING',
          'tool_kinds_denied':list(DENY_TOOLS),'request_executed':False,
          'candidate_authorizes_network':False},
      'canonical':dict(canonical),'gates_open':list(GATES), 'blockers':blockers,
      'g1_real_worker_egress_attested':False,'g2_authenticated_nonexposure_attested':False,
      'g3_inference_attested':False,'g4_production_dispatch_attested':False,
      'g5_live_terminal_ledger_attested':False,'live_worker_authorized':False,
      'production_claim_consumed':False,'provider_token_read':False,
      'provider_inference_executed':False,'external_provider_request_executed':False,
      'worker_launched':False,'automatic_retry':False,
      'next_boundary':'ROOT_AUTH_EGRESS_BROKER_AND_GOVERNED_ONE_SHOT_INFERENCE_NOT_YET_AUTHORIZED'}
    result['report_sha256']=digest(result)
    return result

def source_check():
    empty={h:{'host':h,'path':'/_ping','state':'HOLD_NETWORK','http_status':None,
         'tls_certificate_verified':False,'response_bytes':0} for h in ENDPOINTS}
    flags={f:False for f in CLI_FLAGS}
    row=plan(source_head='a'*40,network=empty,
      cli={'pinned_sha256':BINARY_SHA,'binary_verified_by_r115':False,'help_exit_code':None,
           'help_flag_matches':flags,'offline_no_auto_update':True,
           'credential_env_passed':False,'provider_inference':False},
      credential={'source':'UNCONFIGURED','root_owns_material':False,'group_or_world_access':False,
                  'material_read':False,'passed_to_cli_env':False,'passed_to_child_tools':False,
                  'credential_exchange_attested':False,'metadata_status':'UNCONFIGURED'},
      canonical=dict.fromkeys(('live_cutover_enabled','canonical_claim_consumed','production_ledger_written',
                                'independent_owner_ack','production_dispatcher_authorized'),False))
    if row['gates_open']!=GATES or row['provider_inference_executed'] is not False:deny('FIXTURE_AUTHORITY')
    return row
