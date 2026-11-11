"""Batch E: one canonical, non-authorizing whole-process IPC cutover envelope.

The existing R013/R115/R134/R030 reviews validate an exact read-only MCP
candidate.  This join makes missing *whole process* isolation explicit and
machine checked. It never derives positive host/kernel/credential/egress
attestations from a static systemd plan; an IPC allowlist is not a firewall.

No file, process, kernel, network, credential, claim or Git effects.
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import re

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r115_preclaim_executable_profile_v0_1 as r115,
    cf10_r134_ipc_preclaim_crosswalk_v0_1 as r134,
)

SCHEMA = 'cf10_batch_e_whole_process_cutover_contract_v0_1'
STATE = 'SOURCE_BOUND_IPC_PRECLAIM_HOLD_EFFECTIVE_RUNTIME_UNPROVEN'
EXPECTED_OPEN = (
    'G1_DIRECT_INFERENCE_VS_TOOL_EGRESS_NOT_SEPARATED',
    'G2_CREDENTIAL_AND_PROVIDER_CACHE_ISOLATION_UNPROVEN',
    'G3_EFFECTIVE_COPILOT_WHOLE_PROCESS_SANDBOX_UNPROVEN',
    'G4_PRODUCTION_ROOT_BROKER_AND_RELEASE_NOT_ENABLED',
    'G5_KERNEL_1_TO_0_TERMINAL_LEDGER_JOIN_UNPROVEN',
)
MODELED_NEGATIVE = {
    'direct_inference_separate_from_tool_egress':False,
    'credential_namespace_attested':False,
    'effective_process_sandbox_attested':False,
    'production_root_ipc_listener_attested':False,
    'pinned_kernel_terminal_attested':False,
    'worker_admission_authorized':False,
    'owner_claim_consumed':False,
    'worker_started':False,
    'terminal_ledger_written':False,
    'automatic_retry':False,
}

class RuntimeCutoverHold(RuntimeError):
    pass


def deny(code: str) -> None:
    raise RuntimeCutoverHold('CF10_BATCH_E_HOLD_' + code)


def _canonical(doc:dict)->bytes:
    return json.dumps(doc,sort_keys=True,separators=(',', ':'),ensure_ascii=True).encode('ascii')


def _digest(doc:dict)->str:
    return hashlib.sha256(_canonical(doc)).hexdigest()


def _hex(value:str,size:int)->bool:
    return type(value) is str and re.fullmatch('[0-9a-f]{'+str(size)+'}',value) is not None


def _canonical_profile(plan:dict)->dict:
    """Exact current R013 plan, not an arbitrary planner-provided profile.

    Source-only assessment: PrivateNetwork, IPAddressDeny and AF_INET filters
    are not present in this direct-inference profile. Do not fabricate stronger
    isolation for a future Worker from a proposed/host-applied override.
    """
    if type(plan) is not dict or type(plan.get('properties')) is not dict:
        deny('PLAN_PROPERTIES')
    properties=plan['properties']
    # Report explicit network policy drift first for precise operator evidence.
    forbidden={'PrivateNetwork','IPAddressAllow','IPAddressDeny',
               'RestrictAddressFamilies','NetworkNamespacePath',
               'JoinsNamespaceOf','SocketBindAllow','SocketBindDeny'}
    if set(properties)&forbidden:
        deny('NETWORK_POLICY_UNREVIEWED_WITHOUT_INFERENCE_TRANSPORT')
    if properties != bound.EXPECTED_PROPERTIES:
        deny('R013_PROPERTIES_NOT_SOURCE_LOCKED')
    if (properties.get('User') != bound.RUNNER or
        properties.get('Group') != bound.RUNNER or
        properties.get('KillMode') != 'control-group' or
        properties.get('NoNewPrivileges') != 'yes' or
        properties.get('ProtectHome') != 'yes' or
        properties.get('ProtectSystem') != 'strict' or
        properties.get('StateDirectory') != 'forprint-runner'):
        deny('CURRENT_SANDBOX_BASELINE_CHANGED')
    return dict(properties)


def review(*,spec:bound.BoundedInput,plan:dict,invocation:dict,
           candidate:dict,preclaim:dict)->dict:
    """Bind R030-reviewed attempt, R134 crosswalk, and exact R013 base profile.

    This is a required extension of the R030 source review, NOT an alternate
    route, root permission check, production listener or launch consent.
    """
    if type(spec) is not bound.BoundedInput or type(plan) is not dict:
        deny('BOUND_INPUTS')
    try:bound.validate_plan(plan,spec)
    except (bound.BoundaryBlocked,ValueError,KeyError,TypeError):
        deny('FROZEN_R013_PLAN_DRIFT')
    properties=_canonical_profile(plan)
    if type(preclaim) is not dict or preclaim.get('schema_version')!='cf10_r030_guarded_ipc_handoff_review_v0_1':
        deny('R030_PRECLAIM_SCHEMA')
    if (preclaim.get('state')!='CANONICAL_R030_IPC_REVIEW_ONLY_BEFORE_CLAIM' or
        any(preclaim.get(k) is not False for k in (
            'live_worker_authorized','claim_consumed','worker_started',
            'terminal_ledger_written','g1_g5_closed','automatic_retry'))):
        deny('R030_REVIEW_PRETENDS_TO_AUTHORIZE')
    if (preclaim.get('attempt_id')!=spec.attempt_id or
        preclaim.get('source_head')!=spec.source_head or
        preclaim.get('unit')!=plan['identity']['unit'] or
        preclaim.get('canonical_argv_sha256')!=plan['identity']['argv_sha256'] or
        preclaim.get('model_tools')!=[r134.ALLOWED_MODEL_TOOL]):
        deny('R030_FROZEN_IDENTITY')
    if (type(invocation) is not dict or type(candidate) is not dict or
        candidate.get('attempt_id')!=spec.attempt_id or
        candidate.get('source_head')!=spec.source_head or
        invocation.get('argv')!=list(spec.argv) or
        invocation.get('workspace_repo')!=spec.workspace):
        deny('INVOKED_CANDIDATE_SCOPE')
    try:
        checked=r134.verify_source_only(invocation=invocation,candidate=candidate)
        preview=r115.assert_guarded_ipc_preview(
            [*invocation['argv'][:7],
             json.dumps(candidate['candidate_mcp_config'],sort_keys=True,
                        separators=(',', ':'),ensure_ascii=True),
             invocation['argv'][8],r134.ALLOWED_MODEL_TOOL,*invocation['argv'][-8:]],
            spec.workspace)
    except (r134.IPCPreclaimHold,r115.R115PreclaimBlocked,ValueError,KeyError,TypeError):
        deny('EXACT_READONLY_IPC_CROSSWALK')
    if (not _hex(checked.get('report_sha256'),64) or
        checked['report_sha256'] != preclaim.get('crosswalk_report_sha256') or
        checked['candidate_sha256']!=preclaim.get('candidate_sha256') or
        preview['argv_sha256']!=checked['review_only_argv_sha256'] or
        preview['mcp_config_sha256']!=checked['r115_guarded_ipc_mcp_config_sha256']):
        deny('CROSSWALK_DIGEST_DRIFT')
    report={
        'schema_version':SCHEMA,'status':STATE,
        'attempt_id':spec.attempt_id,'source_head':spec.source_head,
        'unit':plan['identity']['unit'],
        'canonical_argv_sha256':plan['identity']['argv_sha256'],
        'candidate_sha256':checked['candidate_sha256'],
        'crosswalk_report_sha256':checked['report_sha256'],
        'r013_properties_sha256':_digest(properties),
        'r030_preclaim_sha256':_digest(preclaim),
        'ipc_model_tools':[r134.ALLOWED_MODEL_TOOL],
        'static_ipc_tool_restriction_source_validated':True,
        'static_systemd_baseline_source_validated':True,
        'inference_transport':'DIRECT_COPILOT_NETWORK_NOT_EGRESS_ISOLATED',
        'credential_scope':'UNVERIFIED_PROVIDER_HOME_ENV_CACHE',
        'ipc_scope':'R140_LAB_ONLY_NO_PRODUCTION_LISTENER',
        'terminal_kernel_scope':'UNVERIFIED_NO_SOURCE_ONLY_KERNEL_PROOF',
        'open_gates':list(EXPECTED_OPEN),
        'authority':dict(MODELED_NEGATIVE),
    }
    report['report_sha256']=_digest(report)
    return report


def source_check() -> dict:
    """Deterministic zero-effects check; no server runtime assumptions."""
    properties=_canonical_profile({'properties':dict(bound.EXPECTED_PROPERTIES)})
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    if launcher.LIVE_CUTOVER_ENABLED is not False:
        deny('LIVE_SWITCH_ALREADY_ON')
    if not callable(r115.assert_guarded_ipc_preview) or not callable(r134.verify_source_only):
        deny('PRECLAIM_IMPLEMENTATION_MISSING')
    return {'schema_version':SCHEMA,'source_contract':'PASS_PRECLAIM_ONLY',
            'systemd_properties_sha256':_digest(properties),
            'open_gates':list(EXPECTED_OPEN),
            'live_worker_authorized':False}


def main(argv=None)->int:
    import argparse
    p=argparse.ArgumentParser(description='CF10 Batch E source-only runtime cutover boundary')
    p.add_argument('--mode',choices=['source-check'],required=True)
    p.parse_args(argv)
    try:
        report=source_check()
        print('CF10_BATCH_E_SOURCE=PASS_CANONICAL_IPC_RUNTIME_CONTRACT')
        print('CF10_BATCH_E_G1_G5=OPEN_NO_LIVE_ADMISSION')
        print('CF10_BATCH_E_PROFILE_SHA256='+report['systemd_properties_sha256'])
        return 0
    except (RuntimeCutoverHold,ValueError,KeyError,TypeError,ImportError) as exc:
        print(str(exc) if isinstance(exc,RuntimeCutoverHold) else
              'CF10_BATCH_E_HOLD_'+type(exc).__name__)
        return 3

if __name__=='__main__':
    raise SystemExit(main())
