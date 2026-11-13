#!/usr/bin/env python3
"""CF10 R123: source-only crosswalk from canonical invocation to R122 capsule.

Non-authorizing. The current Copilot MCP child still comes from the attempt
workspace. This proof does NOT make it execute inside the R119 kernel sandbox;
no root broker, new launcher, claim, credential or live dispatch is created.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from collections.abc import Mapping

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r115_preclaim_executable_profile_v0_1 as preclaim,
    cf10_r122_durable_source_capsule_v0_1 as capsule,
)

SCHEMA = 'forprint_cf10_r123_source_capsule_invocation_crosswalk_v0_1'
CAPSULE_ID = 'git-12c668e0cc30-sha256-5877e4f4e16fefecf16a6e50ea9e9a712d288c7e35fb726b05950226ab416de9'
HEX64 = re.compile(r'^[0-9a-f]{64}$')
DENIALS = {
    'worker_authorized': False, 'claim_consumed': False,
    'live_dispatch_enabled': False, 'capsule_executed_as_mcp': False,
    'mcp_kernel_isolation_attested': False, 'inference_tool_egress_separated': False,
    'credential_broker_attested': False, 'release_receipt_attested': False,
    'g1_g5_closed': False, 'production_changed': False,
}

class BindingBlocked(RuntimeError):
    pass


def deny(label: str) -> None:
    raise BindingBlocked('CF10_R123_HOLD_' + label)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(doc: Mapping) -> bytes:
    return json.dumps(dict(doc), ensure_ascii=True, sort_keys=True,
                      separators=(',', ':')).encode('utf8')


def _pairs_unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out:deny('DUPLICATE_MCP_CONFIG_KEY')
        out[k] = v
    return out


def verify_capsule_readback(*, capsule_id: str = CAPSULE_ID,
                            store: Path = capsule.STORE,
                            owner: int = 0,
                            group: int = capsule.RUNNER_GID) -> dict:
    if capsule_id != CAPSULE_ID or not isinstance(capsule_id, str):
        deny('CAPSULE_ID_DRIFT')
    # R122 rejects added/symlinked/mutated files, wrong owner/group/mode and
    # changed manifest. Never accept only a claimed SHA from an invocation.
    try:
        check = capsule.verify_capsule(store / capsule_id, store=store,
                                       owner=owner, group=group)
    except (capsule.Hold, OSError, ValueError, TypeError):
        deny('R122_CAPSULE_READBACK')
    if (check.get('status') != 'PASS_NON_AUTHORIZING_DURABLE_SOURCE'
        or check.get('capsule_id') != capsule_id
        or check.get('git_head') != capsule.PINNED_HEAD
        or check.get('source_files') != 427
        or check.get('worker_authorized') is not False
        or check.get('runner_writable') is not False):
        deny('R122_READBACK_INCOMPLETE')
    path = store / capsule_id / 'MANIFEST.json'
    try:
        manifest = json.loads(path.read_bytes())
    except (OSError, ValueError, UnicodeError):
        deny('CAPSULE_MANIFEST_UNREADABLE')
    entries = {f['path']: f for f in manifest['files']}
    for key in (capsule.MCP, capsule.SUITE):
        if key not in entries or not HEX64.fullmatch(entries[key]['sha256']):
            deny('CAPSULE_CRITICAL_SOURCE_MISSING')
    return {
        'capsule_id': capsule_id,
        'capsule_head': check['git_head'],
        'capsule_files': check['source_files'],
        'mcp_source_sha256': entries[capsule.MCP]['sha256'],
        'validation_suite_sha256': entries[capsule.SUITE]['sha256'],
        'status': check['status'],
    }


def crosswalk_invocation(*, invocation: Mapping, capsule_id: str = CAPSULE_ID) -> dict:
    """Bind a *candidate* invocation to immutable MCP source, never authorize.

    Uses R118 for exact tool, flag, interpreter, workspace and argument checks.
    Workspace MCP code is compared with R122 entrypoint before returning a
    source-only proof. TOCTOU is not kernel-pinned; this is not an exec gate.
    """
    if capsule_id != CAPSULE_ID:
        deny('CAPSULE_ID_DRIFT')
    capsule_readback = verify_capsule_readback(capsule_id=capsule_id)
    if (not isinstance(invocation, Mapping)
        or invocation.get('schema_version') != 'forprint_worker_runtime_launch_invocation_v0_1'):
        deny('INVOCATION_SCHEMA')
    if (not isinstance(capsule_readback, Mapping)
        or set(capsule_readback) != {'capsule_id', 'capsule_head', 'capsule_files',
                                    'mcp_source_sha256', 'validation_suite_sha256', 'status'}
        or capsule_readback.get('capsule_id') != CAPSULE_ID
        or capsule_readback.get('capsule_head') != capsule.PINNED_HEAD
        or capsule_readback.get('status') != 'PASS_NON_AUTHORIZING_DURABLE_SOURCE'
        or capsule_readback.get('capsule_files') != 427
        or not all(type(capsule_readback.get(k)) is str and HEX64.fullmatch(capsule_readback[k])
                   for k in ('mcp_source_sha256', 'validation_suite_sha256'))):
        deny('UNTRUSTED_CAPSULE_READBACK')
    ws = invocation.get('workspace_repo')
    argv = invocation.get('argv')
    if (not isinstance(ws, str) or not isinstance(argv, list)
        or any(type(x) is not str for x in argv)):
        deny('INVOCATION_ARGUMENTS')
    authority = invocation.get('authority')
    effects = invocation.get('effects')
    if (not isinstance(authority, Mapping) or not isinstance(effects, Mapping)
        or invocation.get('provider_id') != 'github_copilot_cli'
        or invocation.get('command_representation') != 'ARGV_NO_SHELL'
        or authority.get('adapter_grants_authority') is not False
        or effects.get('worker_process_started') is not False):
        deny('INVOCATION_AUTHORITY')
    actual_argv_sha = digest('\0'.join(argv).encode('utf8'))
    if invocation.get('argv_sha256') != actual_argv_sha:
        deny('INVOCATION_ARGV_SHA')
    try:
        preclaim.assert_frozen_argv(argv, ws)
        preclaim.assert_static_tool_and_mcp_boundary(argv, ws)
    except preclaim.R115PreclaimBlocked:
        deny('R118_PRECLAIM_SOURCE_CONTRACT')
    try:
        config = json.loads(argv[7], object_pairs_hook=_pairs_unique)
    except (TypeError, UnicodeError, ValueError):
        deny('MCP_CONFIG_JSON')
    spec = config['mcpServers']['ForPrintValidation']
    args = spec['args']
    if (args[2] != invocation.get('attempt_id')
        or args[4] != invocation.get('task_id')
        or args[6] != invocation.get('work_front_id')
        or args[8] != invocation.get('decision_id')):
        deny('INVOCATION_FROZEN_CONTEXT_DRIFT')
    script = Path(args[0])
    if (script != Path(ws) / preclaim.PILOT_MCP_SCRIPT
        or script.is_symlink()):
        deny('WORKSPACE_MCP_SOURCE')
    try:
        # Non-authorizing, read-only comparison. Does not replace fd-pinning or
        # execution sandbox; must be revalidated at a later root gate.
        st = script.lstat()
        if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o022:
            deny('WORKSPACE_MCP_OWNER_MODE')
        with script.open('rb') as source:
            raw = source.read(2_000_001)
        if len(raw) > 2_000_000:
            deny('WORKSPACE_MCP_SIZE')
    except (OSError, ValueError):
        deny('WORKSPACE_MCP_UNREADABLE')
    if digest(raw) != capsule_readback['mcp_source_sha256']:
        deny('WORKSPACE_MCP_NOT_CAPSULE_SOURCE')
    record = {
        'schema_version': SCHEMA,
        'state': 'SOURCE_CROSSWALK_CANDIDATE_NON_AUTHORIZING',
        'capsule_id': CAPSULE_ID,
        'capsule_source_head': capsule.PINNED_HEAD,
        'mcp_source_sha256': capsule_readback['mcp_source_sha256'],
        'validation_suite_sha256': capsule_readback['validation_suite_sha256'],
        'workspace_repo': ws,
        'attempt_id': invocation['attempt_id'],
        'decision_id': invocation['decision_id'],
        'task_id': invocation['task_id'],
        'work_front_id': invocation['work_front_id'],
        'argv_sha256': actual_argv_sha,
        'mcp_config_sha256': digest(argv[7].encode('utf8')),
        'authority': dict(DENIALS),
    }
    return {**record, 'binding_sha256': digest(canonical(record))}


def verify_record(*, record: Mapping, invocation: Mapping) -> dict:
    expected = crosswalk_invocation(invocation=invocation)
    if not isinstance(record, Mapping) or dict(record) != expected:
        deny('RECORD_SOURCE_OR_INVOCATION_DRIFT')
    return expected


def main() -> int:
    p = argparse.ArgumentParser(description='R123 source-only capsule readback')
    p.add_argument('--mode', choices=['verify'], required=True)
    p.add_argument('--capsule-id', default=CAPSULE_ID)
    args = p.parse_args()
    if os.geteuid() != 0:deny('ROOT_REQUIRED_FOR_DURABLE_READBACK')
    result = verify_capsule_readback(capsule_id=args.capsule_id)
    print('CF10_R123_CAPSULE_READBACK='+result['status'])
    print('CF10_R123_CAPSULE_ID='+result['capsule_id'])
    print('CF10_R123_CAPSULE_FILES='+str(result['capsule_files']))
    print('CF10_R123_CANDIDATE=READY_SOURCE_ONLY_NO_LIVE_HOOK')
    print('CF10_R123_G1_G5=OPEN_NO_LIVE_ADMISSION')
    print('CF10_R123_NO_SYSTEMD_NO_WORKER_NO_CLAIM_NO_CREDENTIALS=true')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (BindingBlocked, ValueError, OSError, KeyError) as exc:
        print('CF10_R123_HOLD='+str(exc) if isinstance(exc, BindingBlocked)
              else 'CF10_R123_HOLD_'+type(exc).__name__)
        raise SystemExit(3)
