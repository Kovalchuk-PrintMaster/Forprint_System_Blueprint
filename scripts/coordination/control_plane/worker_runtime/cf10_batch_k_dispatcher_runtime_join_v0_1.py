"""CF10 Large Batch K: frozen R030 preclaim bound to disposable J-class sandbox observations.

The input is an independently frozen canonical R013 plan and R134 candidate. This
is a non-authorizing *fixture rehearsal*: neither the attempt nor the one-off
batchk unit is a production Worker. No credential, claim, process, filesystem,
ledger or network side effects. Lab controller owns those in its own disposable
one-shot namespace; this module merely checks the cross-layer evidence.
"""
from __future__ import annotations
import hashlib,json,re
from scripts.coordination.control_plane.worker_runtime import (
    cf10_batch_j_composed_copilot_proxy_contract_v0_1 as j,
    cf10_systemd_launcher_v0_1 as backend,
)
SCHEMA='cf10_batch_k_canonical_preclaim_runtime_join_v0_1'
STATUS='NON_AUTHORIZING_R030_FIXTURE_BINDING_WITH_ISOLATED_RUNTIME'
OPEN_GATES=('G1','G2','G3','G4','G5')
class JoinHold(RuntimeError):pass
def deny(reason):raise JoinHold('CF10_BATCH_K_HOLD_'+reason)
def _sha(doc):
    return hashlib.sha256(json.dumps(doc,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest()
def _hex(x):return type(x) is str and re.fullmatch('[0-9a-f]{64}',x) is not None

def review(*,spec,plan,invocation,candidate,reviewer=None):
    """Call the actual existing R030 review in server mode, never run_once."""
    if backend.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_CUTOVER_UNEXPECTED')
    if reviewer is None:
        from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
        reviewer=route.review_guarded_ipc_handoff
    try:
        checked=reviewer(spec=spec,plan=plan,invocation=invocation,candidate=candidate)
    except Exception as exc:
        deny('R030_PRECLAIM_'+type(exc).__name__)
    needed={'schema_version':'cf10_r030_guarded_ipc_handoff_review_v0_1',
            'state':'CANONICAL_R030_IPC_REVIEW_ONLY_BEFORE_CLAIM',
            'runtime_cutover_state':'SOURCE_BOUND_IPC_PRECLAIM_HOLD_EFFECTIVE_RUNTIME_UNPROVEN'}
    if type(checked) is not dict or any(checked.get(k)!=v for k,v in needed.items()):deny('R030_STATE')
    if (type(invocation) is not dict or type(candidate) is not dict or
        checked.get('attempt_id')!=invocation.get('attempt_id') or
        checked.get('source_head')!=candidate.get('source_head') or
        checked.get('candidate_sha256')!=candidate.get('candidate_sha256') or
        checked.get('canonical_argv_sha256')!=plan['identity']['argv_sha256'] or
        checked.get('unit')!=plan['identity']['unit']):deny('FROZEN_IDENTITY')
    for k in ('live_worker_authorized','claim_consumed','worker_started',
              'terminal_ledger_written','g1_g5_closed','automatic_retry'):
        if checked.get(k) is not False:deny('R030_AUTHORITY_'+k)
    if checked.get('whole_process_isolation_gates_open')!=list(__import__(
         'scripts.coordination.control_plane.worker_runtime.cf10_batch_e_runtime_cutover_contract_v0_1',
         fromlist=['EXPECTED_OPEN']).EXPECTED_OPEN):deny('CUTOVER_GATES')
    if (not _hex(checked.get('candidate_sha256')) or
        not _hex(checked.get('runtime_cutover_report_sha256')) or
        not _hex(checked.get('crosswalk_report_sha256'))):deny('DIGESTS')
    result={'schema':SCHEMA,'status':STATUS,
        'r030_review_sha256':_sha(checked),
        'attempt_id':checked['attempt_id'],
        'source_head':checked['source_head'],
        'canonical_unit':checked['unit'],
        'canonical_argv_sha256':checked['canonical_argv_sha256'],
        'candidate_sha256':checked['candidate_sha256'],
        'runtime_cutover_report_sha256':checked['runtime_cutover_report_sha256'],
        'model_tools':['ForPrintValidation-run_repo_head'],
        'gates_open':list(OPEN_GATES),'lab_only':True,'live_authority':False,
        'production_unit_started':False,'worker_claim_consumed':False,
        'provider_inference_executed':False,'worker_terminal_written':False,
        'disposable_lab_same_as_production_attempt':False}
    result['report_sha256']=_sha(result)
    return result

def attest(*,preclaim,lab):
    """Read-only join: same review digest crossed one disposable systemd unit.

    Does NOT equate a lab service to the R030 canonical Worker unit. It proves
    the digest traveled through the root-owned one-shot systemd child and back.
    """
    if (type(preclaim) is not dict or preclaim.get('schema')!=SCHEMA or
        preclaim.get('status')!=STATUS or preclaim.get('lab_only') is not True or
        preclaim.get('live_authority') is not False or
        preclaim.get('gates_open')!=list(OPEN_GATES) or
        preclaim.get('report_sha256')!=_sha({k:v for k,v in preclaim.items() if k!='report_sha256'})):
        deny('PRECLAIM_OR_REPORT_DRIFT')
    if type(lab) is not dict:deny('LAB_SHAPE')
    needed={'status':'PASS_COMPOSED_COPILOT_VERSION_AND_HTTPS_TLS_SANDBOX',
            'preclaim_review_sha256':preclaim['report_sha256'],
            'host_peercred_cgroup_verified':True,
            'effective_private_netns':True,
            'effective_ip_deny_all':True,
            'effective_ip_allow_localhost_only':True,
            'tls_over_unix_verified':True,
            'unauthorized_connect_denied':True,
            'copilot_offline_version_verified':True,
            'stop_readback_proven':True,
            'kernel_1_to_0_proven':False,
            'worker_claim_consumed':False,
            'copilot_inference_executed':False,
            'copilot_proxy_use_proven':False,
            'provider_credentials_used':False,
            'production_broker_used':False,
            'external_network_used':False}
    if any(lab.get(k)!=v for k,v in needed.items()):deny('LAB_BOUNDARY_OR_ORIGIN')
    if (lab.get('peer_uid')!=996 or lab.get('peer_gid')!=992 or
        type(lab.get('unit')) is not str or
        re.fullmatch(r'forprint-cf10-batchk-[a-f0-9]{16}\.service',lab['unit']) is None or
        lab.get('cgroup')!='/system.slice/'+lab['unit']):deny('LAB_IDENTITY')
    cli=lab.get('copilot_version_metadata')
    if (type(cli) is not dict or cli.get('result_status')!='PASS_OFFLINE_VERSION' or
        cli.get('pinned_argv')!='VERSION_ONLY' or cli.get('copilot_proxy_use_proven') is not False):
        deny('COPILOT_NOT_VERSION_ONLY')
    iso=lab.get('isolation')
    if type(iso) is not dict:deny('ISOLATION_MISSING')
    for key in ('direct_external_ipv4','direct_external_ipv6','fake_credential'):
        if type(iso.get(key)) is not dict or iso[key].get('denied') is not True:
            deny('ISOLATION_'+key)
    return {'schema':SCHEMA,'status':'PASS_FIXTURE_PRECLAIM_SHA_JOINED_TO_ONE_SANDBOX',
            'preclaim_report_sha256':preclaim['report_sha256'],
            'lab_unit':lab['unit'],'lab_peer_uid':996,'lab_peer_gid':992,
            'canonical_unit':preclaim['canonical_unit'],
            'same_production_attempt':False,'worker_started':False,
            'provider_inference_executed':False,'claim_consumed':False,
            'kernel_terminal_proven':False,'gates_open':list(OPEN_GATES)}

def source_check():
    if backend.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_SWITCH')
    jreport=j.source_check()
    if jreport.get('authority') is not False or jreport.get('copilot_proxy_use_proven') is not False:
        deny('J_AUTHORITY')
    return {'schema':SCHEMA,'status':'PASS_SOURCE_NON_AUTHORIZING_REHEARSAL',
            'gates_open':list(OPEN_GATES),'no_claim':True,'no_production_worker':True}

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=['source-check'],required=True)
    p.parse_args(argv)
    try:
        v=source_check()
        print('CF10_BATCH_K_SOURCE='+v['status'])
        print('CF10_BATCH_K_G1_G5=OPEN_NO_LIVE_AUTHORITY')
        return 0
    except (JoinHold,ValueError,ImportError,TypeError) as exc:
        print(str(exc) if isinstance(exc,JoinHold) else 'CF10_BATCH_K_HOLD_'+type(exc).__name__)
        return 3
if __name__=='__main__':raise SystemExit(main())
