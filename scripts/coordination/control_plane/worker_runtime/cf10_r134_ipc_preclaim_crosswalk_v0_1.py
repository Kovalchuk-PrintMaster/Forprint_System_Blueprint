"""CF10 R134: non-authorizing IPC candidate versus frozen canonical preclaim.

This is NOT an alternate live preclaim. The existing R115 production function,
R030, launcher, root claim and root release remain the only authoritative path.
It reads only in-memory invocation/candidate and returns digest-only review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r115_preclaim_executable_profile_v0_1 as r115,
    cf10_r129_canonical_lifecycle_convergence_v0_1 as r129,
)

SCHEMA = 'cf10_r134_ipc_preclaim_crosswalk_v0_1'
REVIEW_ONLY = 'SOURCE_IPC_PRECLAIM_COMPATIBILITY_NOT_AUTHORIZED'
ALLOWED_MODEL_TOOL = 'ForPrintValidation-run_repo_head'
EXACT_PROXY = str(r129.REPO / r129.PROXY)

class IPCPreclaimHold(RuntimeError):
    pass


def deny(reason: str):
    raise IPCPreclaimHold('CF10_R134_HOLD_' + reason)


def _sha_argv(argv: list[str]) -> str:
    return hashlib.sha256('\0'.join(argv).encode('utf-8')).hexdigest()


def _sha_doc(data: dict) -> str:
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',', ':'),ensure_ascii=True).encode('ascii')).hexdigest()


def verify_source_only(*, invocation: Mapping, candidate: Mapping) -> dict:
    """Read-only R115 (current) to R127 (prospective) exact compatibility.

    Input candidate is never a root attestation. No filesystem/kernel evidence,
    claim, permitted socket, credential, process or ledger write is inferred.
    This function cannot approve IPC execution: the old R115 MUST reject the
    prospective argv until a separately governed live cutover is implemented.
    """
    if type(invocation) is not dict or type(candidate) is not dict:
        deny('INPUT_SHAPE')
    try:
        c = r129.validate_r127_candidate(candidate)
    except (r129.ConvergenceHold, KeyError, ValueError, TypeError):
        deny('R127_VALIDATION')
    if (invocation.get('schema_version') != 'forprint_worker_runtime_launch_invocation_v0_1'
        or invocation.get('provider_id') != 'github_copilot_cli'
        or invocation.get('command_representation') != 'ARGV_NO_SHELL'):
        deny('CANONICAL_INVOCATION_SCHEMA')
    if (not isinstance(invocation.get('authority'), dict)
        or invocation['authority'].get('adapter_grants_authority') is not False
        or not isinstance(invocation.get('effects'), dict)
        or invocation['effects'].get('worker_process_started') is not False):
        deny('INVOCATION_AUTHORITY')
    if any(invocation.get(k) != c.get(k) for k in ('attempt_id','task_id','work_front_id','decision_id')):
        deny('CANONICAL_IDENTITY')
    if invocation.get('invocation_sha256') != c['canonical_invocation_sha256']:
        deny('INVOCATION_DIGEST')
    workspace = str(r115.PILOT_MCP_BASE_WORKSPACE / c['attempt_id'] / 'workspace' / 'repo')
    spec = c['candidate_mcp_config']['mcpServers']['ForPrintValidation']
    if (invocation.get('workspace_repo') != workspace or spec['cwd'] != workspace):
        deny('WORKSPACE')
    argv = invocation.get('argv')
    if type(argv) is not list or any(type(x) is not str for x in argv):
        deny('ARGV_TYPE')
    if (invocation.get('argv_sha256') != c['canonical_argv_sha256']
        or _sha_argv(argv) != c['canonical_argv_sha256']):
        deny('CANONICAL_ARGV_DIGEST')
    try:
        r115.assert_frozen_argv(argv, workspace)
        r115.assert_static_tool_and_mcp_boundary(argv, workspace)
    except (r115.R115PreclaimBlocked, ValueError, TypeError):
        deny('EXISTING_R115_PRECLAIM_DRIFT')
    if (spec['command'] not in r115.PILOT_MCP_ALLOWED_PYTHON
        or spec['args'][0] != EXACT_PROXY
        or spec['tools'] != ['run_repo_head']):
        deny('IPC_PROXY_NOT_SOURCE_BOUND')
    # Preserve the ONLY existing approved Copilot shape (prompt/model/sandbox,
    # provider binary/credits and all other flags). Alter just source-reviewed
    # MCP config and narrow the entire model tool set to one read-only MCP.
    preview_argv = [*argv[:7],
        json.dumps(c['candidate_mcp_config'],sort_keys=True,separators=(',', ':'),ensure_ascii=True),
        argv[8], ALLOWED_MODEL_TOOL, *argv[-8:]]
    if (preview_argv[0] != str(r115.COPILOT_PILOT_PATH)
        or preview_argv[8] != '--available-tools'
        or preview_argv[-8:] != argv[-8:]
        or preview_argv[9:-8] != [ALLOWED_MODEL_TOOL]):
        deny('PREVIEW_TOOL_OR_PROVIDER_DRIFT')
    try:
        r115.assert_frozen_argv(preview_argv, workspace)
        inspected=r115.assert_guarded_ipc_preview(preview_argv, workspace)
    except (r115.R115PreclaimBlocked, ValueError, TypeError):
        deny('PREVIEW_R115_EXACT_IPC_SHAPE')
    if (inspected['attempt_id'] != c['attempt_id'] or
            inspected['source_head'] != c['source_head'] or
            inspected['epoch'] != c['epoch'] or
            inspected['argv_sha256'] != _sha_argv(preview_argv)):
        deny('PREVIEW_R115_IDENTITY')
    # Mandatory hold: changing the future candidate MUST NOT silently bypass
    # the current production R115 reject-on-drift policy.
    try:
        r115.assert_static_tool_and_mcp_boundary(preview_argv, workspace)
    except r115.R115PreclaimBlocked:
        pass
    else:
        deny('LIVE_R115_UNEXPECTEDLY_ACCEPTS_IPC_PREVIEW')
    report = {
        'schema_version': SCHEMA,
        'status': REVIEW_ONLY,
        'attempt_id': c['attempt_id'],
        'source_head': c['source_head'],
        'epoch': c['epoch'],
        'capsule_id': c['capsule_id'],
        'candidate_sha256': c['candidate_sha256'],
        'original_argv_sha256': c['canonical_argv_sha256'],
        'review_only_argv_sha256': _sha_argv(preview_argv),
        'model_tools': [ALLOWED_MODEL_TOOL],
        'legacy_r115_rejects_prospective_argv': True,
        'r115_guarded_ipc_preview_exact':True,
        'r115_guarded_ipc_mcp_config_sha256':inspected['mcp_config_sha256'],
        'root_lease_attested': False,
        'credential_egress_attested': False,
        'copilot_sandbox_attested': False,
        'kernel_witness_attested': False,
        'terminal_ledger_attested': False,
        'live_cutover_authorized': False,
        'claim_consumed': False,
        'worker_started': False,
        'automatic_retry': False,
    }
    report['report_sha256'] = _sha_doc(report)
    return report


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description='CF10 R134 non-authorizing IPC preclaim crosswalk')
    p.add_argument('--mode',choices=['source-check'],required=True)
    p.parse_args(argv)
    try:
        r129.verify_pinned_seams(r129.REPO)
        if r115.PILOT_MCP_SERVER != 'ForPrintValidation' or not r115.PILOT_TOOL_UNIVERSE:
            deny('R115_SOURCE_DRIFT')
        from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
        if launcher.LIVE_CUTOVER_ENABLED is not False:
            deny('LIVE_CUTOVER_ENABLED')
        print('CF10_R134_R115_R127_SOURCE=PASS_SEALED_CROSSWALK')
        print('CF10_R134_IPC_LIVE_PRECLAIM=NOT_MODIFIED')
        print('CF10_R134_G1_G5=OPEN_NO_LIVE_ADMISSION')
        return 0
    except (IPCPreclaimHold, r129.ConvergenceHold, OSError, KeyError, ValueError, TypeError) as exc:
        print(str(exc) if isinstance(exc,IPCPreclaimHold) else 'CF10_R134_HOLD_'+type(exc).__name__)
        return 3

if __name__=='__main__':
    raise SystemExit(main())
