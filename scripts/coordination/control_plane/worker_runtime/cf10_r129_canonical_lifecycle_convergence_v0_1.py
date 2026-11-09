#!/usr/bin/env python3
"""CF10 R129: deterministic, source-only candidate lifecycle convergence gate.

This module does NOT issue or validate real release authority. It only verifies
that a proposed *synthetic* event sequence and R127 source-only transport
candidate do not contradict existing frozen launch and terminal contracts.
A caller-supplied event is NEVER kernel or root evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from collections.abc import Mapping, Sequence

SCHEMA = 'cf10_r129_synthetic_lifecycle_convergence_v0_1'
R127_SCHEMA = 'cf10_r127_review_only_ipc_cutover_candidate_v0_1'
CAPSULE = 'git-12c668e0cc30-sha256-5877e4f4e16fefecf16a6e50ea9e9a712d288c7e35fb726b05950226ab416de9'
REPO = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
BRANCH = 'audit/blueprint-inventory-refresh-2026-07-29'
HEX40 = re.compile('[0-9a-f]{40}\\Z')
HEX64 = re.compile('[0-9a-f]{64}\\Z')
ID = re.compile('[A-Za-z0-9_.:-]{1,160}\\Z')
EPOCH = re.compile('[A-Za-z0-9_.:-]{1,80}\\Z')
SOCKET = re.compile(r'/run/forprint-cf10-r125-[a-f0-9]{16}/mcp\.sock\Z')
PROXY = 'scripts/coordination/control_plane/worker_runtime/cf10_r127_mcp_stdio_ipc_proxy_v0_1.py'
STEPS = (
    'PREPARED', 'EXPLICIT_ACK', 'OWNER_ADMISSION', 'LAUNCH_REQUESTED',
    'CANONICAL_STARTED', 'ROOT_RELEASE', 'READONLY_TOOLCALL',
    'EXTERNAL_ROOT_REVOKE', 'KERNEL_CGROUP_QUIESCENT',
    'TERMINAL_LEDGER_JOIN', 'OPERATOR_REVIEW',
)
ORIGINS = (
    'dispatcher', 'assistant', 'owner_pam', 'root_control', 'canonical_ledger',
    'root_control', 'isolated_mcp', 'external_root', 'kernel_witness',
    'canonical_ledger', 'operator',
)
SOURCE_BLOBS = {
    'scripts/coordination/control_plane/worker_runtime/invocation_adapter.py': '0668123ac0098126db1df76622f60feb4a890b78',
    'scripts/coordination/control_plane/worker_runtime/cf10_r115_preclaim_executable_profile_v0_1.py': '0c65b0832c59fc9606d5731b99d3d86b0c48f83c',
    'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py': '29f2ac02f801f842591318b4207d7e8e9fe8f28a',
    'scripts/coordination/control_plane/worker_runtime/cf10_systemd_terminal_bridge_v0_1.py': '2e4eef5c69cfa91d79e5da40784dcd6324f54a9a',
    'scripts/coordination/control_plane/worker_runtime/cf10_r123_capsule_invocation_binding_v0_1.py': '705708d648d95167cecf55f98a4284fff14ec827',
    'scripts/coordination/control_plane/worker_runtime/cf10_r125_attempt_ipc_contract_v0_1.py': 'c1b687c033a3b047d3b4b9dd2b1c0ab12ee7b626',
    'scripts/coordination/control_plane/worker_runtime/cf10_r126_root_external_revoke_v0_1.py': 'f7710a600fc3e288149a9acbf1b40dab74460b01',
    PROXY: '2dddb8f189a4fd7fb1547aeec1e191e06d5d07a3',
}

class ConvergenceHold(RuntimeError):
    pass

def deny(reason: str) -> None:
    raise ConvergenceHold('CF10_R129_HOLD_' + reason)

def canonical(doc: Mapping) -> bytes:
    return json.dumps(doc, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')

def sha(doc: Mapping) -> str:
    return hashlib.sha256(canonical(doc)).hexdigest()

def _text(obj, pattern, label):
    if type(obj) is not str or not pattern.fullmatch(obj):
        deny(label)
    return obj

def _dict(obj, label):
    if type(obj) is not dict:
        deny(label)
    return obj

def _bool_off(doc, required, label):
    if _dict(doc, label) != {name: False for name in required}:
        deny(label)

def validate_r127_candidate(candidate: Mapping) -> dict:
    """Verify an exact non-authorizing R127 preview, not a live invocation."""
    c = _dict(candidate, 'CANDIDATE_OBJECT')
    expected_keys = {'schema_version','state','attempt_id','task_id','work_front_id','decision_id',
                     'source_head','epoch','capsule_id','canonical_invocation_sha256',
                     'canonical_argv_sha256','r123_binding_sha256','candidate_mcp_config',
                     'outstanding','authority','candidate_sha256'}
    if set(c) != expected_keys:
        deny('CANDIDATE_FIELDS')
    if c.get('schema_version') != R127_SCHEMA or c.get('state') != 'SOURCE_REVIEW_NOT_ADMITTED':
        deny('CANDIDATE_STATE')
    keys = ('attempt_id', 'task_id', 'work_front_id', 'decision_id')
    for key in keys:
        _text(c.get(key), ID, 'IDENTITY_' + key.upper())
    _text(c.get('epoch'), EPOCH, 'EPOCH')
    _text(c.get('source_head'), HEX40, 'SOURCE_HEAD')
    for key in ('canonical_invocation_sha256', 'canonical_argv_sha256', 'r123_binding_sha256'):
        _text(c.get(key), HEX64, 'HASH_' + key.upper())
    if c.get('capsule_id') != CAPSULE:
        deny('CAPSULE_ID')
    authority = ('live_worker', 'claim_consumed', 'release_granted',
                 'candidate_executable_in_current_R115', 'ipc_broker_launched', 'g1_g5_closed')
    _bool_off(c.get('authority'), authority, 'CANDIDATE_AUTHORITY')
    config = _dict(c.get('candidate_mcp_config'), 'CONFIG')
    if set(config) != {'mcpServers'}:
        deny('CONFIG_KEYS')
    servers = _dict(config['mcpServers'], 'SERVERS')
    if set(servers) != {'ForPrintValidation'}:
        deny('SERVERS_KEYS')
    spec = _dict(servers['ForPrintValidation'], 'SERVER_SPEC')
    if set(spec) != {'type', 'command', 'args', 'cwd', 'tools'} or spec['type'] != 'local':
        deny('SERVER_SPEC_KEYS')
    if spec['tools'] != ['run_repo_head']:
        deny('MODEL_TOOL_ALLOWLIST')
    cwd = spec['cwd']
    if type(cwd) is not str or not cwd.startswith('/') or '/..' in cwd or not cwd.endswith('/workspace/repo'):
        deny('WORKSPACE_CWD')
    command = spec['command']
    if type(command) is not str or not command.startswith('/') or not Path(command).name == 'python':
        deny('INTERPRETER')
    args = spec['args']
    if type(args) is not list or len(args) != 11 or any(type(x) is not str for x in args):
        deny('PROXY_ARG_SHAPE')
    if not args[0].startswith('/') or not args[0].endswith('/' + PROXY):
        deny('PROXY_SOURCE')
    if args[1::2] != ['--socket', '--attempt-id', '--epoch', '--source-head', '--capsule-id']:
        deny('PROXY_FLAGS')
    if not SOCKET.fullmatch(args[2]) or args[4] != c['attempt_id'] or args[6] != c['epoch'] or args[8] != c['source_head'] or args[10] != CAPSULE:
        deny('PROXY_BINDING')
    expected_outstanding = ['R115_R118_NEW_PROXY_PRECLAIM', 'PROXY_ROOT_CGROUP_PEER_PIN',
       'INFLIGHT_CANCELLATION_AND_TERMINAL_FENCE', 'CREDENTIAL_AND_EGRESS_ATTESTATION',
       'NEW_ATTEMPT_CANONICAL_E2E_RELEASE']
    if c.get('outstanding') != expected_outstanding:
        deny('OUTSTANDING')
    actual = c.get('candidate_sha256')
    _text(actual, HEX64, 'CANDIDATE_SHA_TYPE')
    if actual != sha({k: v for k, v in c.items() if k != 'candidate_sha256'}):
        deny('CANDIDATE_DIGEST')
    return c

def convergence(candidate: Mapping, events: Sequence[Mapping], *, live_cutover_enabled: bool = False) -> dict:
    """Validate a *synthetic* canonical event trace without granting authority.

    This deliberately cannot validate real signed decisions or kernel witnesses;
    those must be verified by their separate existing root-owned components.
    """
    c = validate_r127_candidate(candidate)
    if live_cutover_enabled is not False:
        deny('LIVE_CUTOVER_NOT_SEALED')
    if type(events) not in (list, tuple) or len(events) != len(STEPS):
        deny('TRACE_LENGTH')
    identity = {key: c[key] for key in ('attempt_id', 'task_id', 'work_front_id', 'decision_id', 'source_head', 'epoch')}
    unit = 'forprint-cf10-worker-' + hashlib.sha256((c['attempt_id'] + '\0' + c['epoch']).encode()).hexdigest()[:24] + '.service'
    for n, (step, origin) in enumerate(zip(STEPS, ORIGINS)):
        ev = _dict(events[n], 'EVENT_OBJECT')
        base_keys = {'step', 'origin', 'attempt_id', 'task_id', 'work_front_id', 'decision_id', 'epoch', 'source_head', 'unit', 'synthetic'}
        extra = ({'evidence_digest'} if step == 'READONLY_TOOLCALL' else
                 {'kernel_transition', 'cgroup_populated'} if step == 'KERNEL_CGROUP_QUIESCENT' else
                 {'terminal_status', 'result_accepted'} if step == 'TERMINAL_LEDGER_JOIN' else set())
        if set(ev) != base_keys | extra:
            deny('EVENT_KEYS_' + str(n))
        if ev['step'] != step or ev['origin'] != origin or ev['synthetic'] is not True:
            deny('EVENT_SEQUENCE_' + str(n))
        if any(ev[k] != v for k, v in identity.items()) or ev['unit'] != unit:
            deny('EVENT_BINDING_' + str(n))
        if step == 'READONLY_TOOLCALL':
            _text(ev['evidence_digest'], HEX64, 'READONLY_TOOLCALL_DIGEST')
        if step == 'KERNEL_CGROUP_QUIESCENT' and (ev['kernel_transition'] != '1_TO_0' or ev['cgroup_populated'] != '0'):
            deny('KERNEL_QUIESCENCE')
        if step == 'TERMINAL_LEDGER_JOIN' and (ev['terminal_status'] != 'REVIEW_REQUIRED' or ev['result_accepted'] is not False):
            deny('TERMINAL_IS_NOT_ACCEPTANCE')
    report = {
      'schema_version': SCHEMA,
      'mode': 'SYNTHETIC_ONLY_NON_AUTHORIZING',
      'candidate_sha256': c['candidate_sha256'],
      'attempt_id': c['attempt_id'],
      'source_head': c['source_head'],
      'epoch': c['epoch'],
      'unit': unit,
      'synthetic_event_count': len(events),
      'sequence': list(STEPS),
      'source_only_trace_valid': True,
      'open_boundaries': [
         'R115_EXACT_PROXY_PRECLAIM_NOT_IN_LIVE_PATH',
         'OWNER_SIGNED_RELEASE_AND_ROOT_LEASE_EPOCH_JOIN_UNPROVEN',
         'INFLIGHT_TOOL_CANCELLATION_NOT_PROVEN',
         'G1_PROVIDER_TOOL_EGRESS_AND_G2_CREDENTIAL_ISOLATION_NOT_PROVEN',
         'G3_COPILOT_PROCESS_SANDBOX_NOT_PROVEN',
         'G5_KERNEL_WITNESS_TO_DURABLE_LEDGER_NOT_PROVEN',
      ],
      'authority': {'live_worker_allowed': False, 'claim_consumed': False,
                    'root_release_granted': False, 'automatic_retry': False,
                    'tool_cancellation_attested': False, 'g1_g5_closed': False},
    }
    report['report_sha256'] = sha(report)
    return report

def synthetic_fixture() -> tuple[dict, list[dict]]:
    """Deterministic fixture for negative suite; NOT a claimed real attempt."""
    h = 'a' * 40
    ident = 'cf10-r129-synthetic-a999'
    epoch = 'r129-synthetic-epoch'
    candidate = {
       'schema_version': R127_SCHEMA, 'state': 'SOURCE_REVIEW_NOT_ADMITTED',
       'attempt_id': ident, 'task_id': 'cf10-r129-contract',
       'work_front_id': 'cf10-contract', 'decision_id': 'cf10-r129-none',
       'source_head': h, 'epoch': epoch, 'capsule_id': CAPSULE,
       'canonical_invocation_sha256': '1'*64,
       'canonical_argv_sha256': '2'*64,
       'r123_binding_sha256': '3'*64,
       'candidate_mcp_config': {'mcpServers': {'ForPrintValidation': {
          'type': 'local', 'command': '/usr/bin/python',
          'args': [str(REPO / PROXY), '--socket', '/run/forprint-cf10-r125-0123456789abcdef/mcp.sock',
                   '--attempt-id', ident, '--epoch', epoch, '--source-head', h,
                   '--capsule-id', CAPSULE],
          'cwd': '/srv/software_development/forprint-worker-runtime/synthetic/workspace/repo',
          'tools': ['run_repo_head'],
       }}},
       'outstanding': ['R115_R118_NEW_PROXY_PRECLAIM', 'PROXY_ROOT_CGROUP_PEER_PIN',
                       'INFLIGHT_CANCELLATION_AND_TERMINAL_FENCE',
                       'CREDENTIAL_AND_EGRESS_ATTESTATION', 'NEW_ATTEMPT_CANONICAL_E2E_RELEASE'],
       'authority': {'live_worker': False, 'claim_consumed': False,
                     'release_granted': False, 'candidate_executable_in_current_R115': False,
                     'ipc_broker_launched': False, 'g1_g5_closed': False},
    }
    candidate['candidate_sha256'] = sha(candidate)
    unit = 'forprint-cf10-worker-' + hashlib.sha256((ident + '\0' + epoch).encode()).hexdigest()[:24] + '.service'
    events = []
    for step, origin in zip(STEPS, ORIGINS):
        ev = {'step': step, 'origin': origin, 'attempt_id': ident, 'task_id': candidate['task_id'],
              'work_front_id': candidate['work_front_id'], 'decision_id': candidate['decision_id'], 'source_head': h,
              'epoch': epoch, 'unit': unit, 'synthetic': True}
        if step == 'READONLY_TOOLCALL': ev['evidence_digest'] = '4'*64
        if step == 'KERNEL_CGROUP_QUIESCENT': ev.update(kernel_transition='1_TO_0', cgroup_populated='0')
        if step == 'TERMINAL_LEDGER_JOIN': ev.update(terminal_status='REVIEW_REQUIRED', result_accepted=False)
        events.append(ev)
    return candidate, events

def verify_pinned_seams(root: Path) -> None:
    """Read-only exact Git blob check; rejects worktree edits to canonical seams."""
    if root != REPO or root.is_symlink() or not root.is_dir():
        deny('CANONICAL_PROJECT_ROOT')
    def git(*args: str) -> str:
        try:
            cp = subprocess.run(['/usr/bin/git', '-C', str(root), *args], stdin=subprocess.DEVNULL,
                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=12, check=False,
                 env={'PATH': '/usr/bin:/bin', 'GIT_TERMINAL_PROMPT': '0', 'LANG': 'C'})
        except (OSError, subprocess.TimeoutExpired):
            deny('SOURCE_GIT_UNAVAILABLE')
        if cp.returncode:
            deny('SOURCE_GIT_' + args[0].replace('-', '_'))
        return cp.stdout.decode('ascii', 'strict').strip()
    if git('symbolic-ref', '--short', 'HEAD') != BRANCH:
        deny('SOURCE_BRANCH')
    for path, expected in SOURCE_BLOBS.items():
        p = root / path
        if p.is_symlink() or not p.is_file() or git('rev-parse', 'HEAD:' + path) != expected or git('hash-object', '--', path) != expected:
            deny('SOURCE_SEAM_' + Path(path).stem)
    if 'LIVE_CUTOVER_ENABLED=False' not in (root/'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py').read_text('utf8'):
        deny('LIVE_CUTOVER_TAMPER')

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Non-authorizing CF10 source-only convergence gate')
    parser.add_argument('--mode', choices=['source-check', 'synthetic-check'], required=True)
    args = parser.parse_args(argv)
    try:
        verify_pinned_seams(REPO)
        print('CF10_R129_CANONICAL_SEAMS=PASS_PINNED_UNCHANGED')
        if args.mode == 'synthetic-check':
            candidate, events = synthetic_fixture()
            report = convergence(candidate, events)
            if report['authority']['live_worker_allowed'] is not False:
                deny('AUTHORITY')
            print('CF10_R129_SYNTHETIC_LIFECYCLE=PASS_ORDER_IDENTITY_REVOCATION_TERMINAL_REVIEW')
            print('CF10_R129_OPEN_BOUNDARIES=' + str(len(report['open_boundaries'])))
        print('CF10_R129_NO_CLAIM_NO_COPILOT_NO_SYSTEMD_NO_LIVE_RELEASE=true')
        return 0
    except (ConvergenceHold, ValueError, KeyError, TypeError) as exc:
        print(str(exc) if isinstance(exc, ConvergenceHold) else 'CF10_R129_HOLD_' + type(exc).__name__)
        return 3

if __name__ == '__main__':
    raise SystemExit(main())
