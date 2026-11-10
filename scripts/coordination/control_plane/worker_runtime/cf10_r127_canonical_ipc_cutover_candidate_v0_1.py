"""CF10 R127: read-only crosswalk: canonical Copilot invocation -> IPC candidate.

The old R115/R118 invocation and live systemd release contract are NOT
modified. This API produces a REVIEW candidate only; it does not authorize a
worker, publish a capsule, open a lease, or change Copilot argv. A separate
source-reviewed release must integrate it into canonical preclaim + terminal
ledger. Explicitly not a second launcher.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from collections.abc import Mapping

CAPSULE_ID = 'git-12c668e0cc30-sha256-5877e4f4e16fefecf16a6e50ea9e9a712d288c7e35fb726b05950226ab416de9'
REL_PROXY = 'scripts/coordination/control_plane/worker_runtime/cf10_r127_mcp_stdio_ipc_proxy_v0_1.py'
LEASE_RE = re.compile(r'/run/forprint-cf10-r125-[0-9a-f]{16}/lease\.json\Z')
ID_RE = re.compile(r'[A-Za-z0-9_.:-]{1,160}\Z')
EPOCH_RE = re.compile(r'[A-Za-z0-9_.:-]{1,80}\Z')
HEAD_RE = re.compile(r'[a-f0-9]{40}\Z')
SHA256_RE = re.compile(r'[a-f0-9]{64}\Z')
SCHEMA = 'cf10_r127_review_only_ipc_cutover_candidate_v0_1'

class CandidateHold(RuntimeError):
    pass

def deny(code):
    raise CandidateHold('CF10_R127_CANDIDATE_HOLD_' + code)

def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode('ascii')

def validate_source_envelope(*, invocation: Mapping, binding_record: Mapping, proof: Mapping):
    if (not isinstance(invocation, Mapping) or not isinstance(binding_record, Mapping) or
        not isinstance(proof, Mapping) or invocation.get('schema_version') != 'forprint_worker_runtime_launch_invocation_v0_1'):
        deny('SOURCE_SHAPE')
    for key in ('attempt_id', 'decision_id', 'task_id', 'work_front_id'):
        if type(invocation.get(key)) is not str or not ID_RE.fullmatch(invocation[key]) or binding_record.get(key) != invocation[key]:
            deny('IDENTITY_'+key.upper())
    if (binding_record.get('schema_version') != 'forprint_cf10_r123_source_capsule_invocation_crosswalk_v0_1' or
        binding_record.get('capsule_id') != CAPSULE_ID or
        binding_record.get('state') != 'SOURCE_CROSSWALK_CANDIDATE_NON_AUTHORIZING' or
        binding_record.get('argv_sha256') != invocation.get('argv_sha256') or
        binding_record.get('workspace_repo') != invocation.get('workspace_repo')):
        deny('R123_BINDING_DRIFT')
    auth = binding_record.get('authority')
    if type(auth) is not dict or not auth or any(type(x) is not bool or x for x in auth.values()):
        deny('R123_AUTHORITY_WIDENED')
    if proof.get('binding_sha256') != binding_record.get('binding_sha256'):
        deny('R123_PROOF_DRIFT')
    for k in ('argv_sha256', 'binding_sha256'):
        v = invocation.get(k) if k == 'argv_sha256' else binding_record.get(k)
        if type(v) is not str or not SHA256_RE.fullmatch(v):
            deny('SOURCE_DIGEST')
    return True

def render_review_candidate(*, invocation: Mapping, binding_record: Mapping,
                            verified_binding: Mapping, verified_lease: Mapping,
                            source_head: str, epoch: str, socket_path: Path,
                            proxy_path: Path, interpreter: Path, live_cutover_enabled: bool) -> dict:
    """Pure canonical data composition AFTER independent R123/R126 readbacks.

    Actual readbacks happen in build_review_candidate() below. No authority
    can be gained by passing this pure helper a forged verified_* mapping.
    """
    validate_source_envelope(invocation=invocation, binding_record=binding_record, proof=verified_binding)
    if live_cutover_enabled is not False: deny('LIVE_CUTOVER_MUST_REMAIN_OFF')
    if type(source_head) is not str or not HEAD_RE.fullmatch(source_head): deny('SOURCE_HEAD')
    if type(epoch) is not str or not EPOCH_RE.fullmatch(epoch): deny('EPOCH')
    if not isinstance(socket_path, Path) or not isinstance(proxy_path, Path) or not isinstance(interpreter, Path):
        deny('PATH_TYPES')
    if (not socket_path.is_absolute() or not LEASE_RE.fullmatch(str(socket_path.with_name('lease.json')))
        or socket_path.name != 'mcp.sock'):
        deny('SOCKET_SCOPE')
    if (type(verified_lease) is not dict or set(verified_lease) !=
        {'schema', 'attempt_id', 'epoch', 'source_head', 'capsule_id', 'revoked'} or
        verified_lease['schema'] != 'cf10_r125_disposable_lease_v0_1' or
        verified_lease['attempt_id'] != invocation['attempt_id'] or
        verified_lease['epoch'] != epoch or verified_lease['source_head'] != source_head or
        verified_lease['capsule_id'] != CAPSULE_ID or verified_lease['revoked'] is not False):
        deny('R126_LEASE_DRIFT')
    if (not proxy_path.is_absolute() or not proxy_path.as_posix().endswith('/' + REL_PROXY)
        or not interpreter.is_absolute() or interpreter.name != 'python'):
        deny('PROXY_EXEC_SOURCE')
    # The prospective proxy is a source-only file. The existing R115 frozen
    # argv is intentionally unchanged; its reject-on-drift policy stands.
    manifest = {
      'schema_version': SCHEMA,
      'state': 'SOURCE_REVIEW_NOT_ADMITTED',
      'attempt_id': invocation['attempt_id'],
      'decision_id': invocation['decision_id'],
      'task_id': invocation['task_id'],
      'work_front_id': invocation['work_front_id'],
      'source_head': source_head,
      'epoch': epoch,
      'capsule_id': CAPSULE_ID,
      'canonical_invocation_sha256': invocation.get('invocation_sha256'),
      'canonical_argv_sha256': invocation['argv_sha256'],
      'r123_binding_sha256': binding_record['binding_sha256'],
      'candidate_mcp_config': {'mcpServers': {'ForPrintValidation': {
        'type': 'local',
        'command': str(interpreter),
        'args': [str(proxy_path), '--socket', str(socket_path),
                 '--attempt-id', invocation['attempt_id'], '--epoch', epoch,
                 '--source-head', source_head, '--capsule-id', CAPSULE_ID],
        'cwd': invocation['workspace_repo'],
        'tools': ['run_repo_head'],
      }}},
      'outstanding': ['R115_R118_NEW_PROXY_PRECLAIM', 'PROXY_ROOT_CGROUP_PEER_PIN',
                      'INFLIGHT_CANCELLATION_AND_TERMINAL_FENCE', 'CREDENTIAL_AND_EGRESS_ATTESTATION',
                      'NEW_ATTEMPT_CANONICAL_E2E_RELEASE'],
      'authority': {'live_worker': False, 'claim_consumed': False, 'release_granted': False,
                    'candidate_executable_in_current_R115': False,
                    'ipc_broker_launched': False, 'g1_g5_closed': False},
    }
    if (type(manifest['canonical_invocation_sha256']) is not str or
        not SHA256_RE.fullmatch(manifest['canonical_invocation_sha256'])):
        deny('INVOCATION_SHA')
    return {**manifest, 'candidate_sha256': hashlib.sha256(canonical(manifest)).hexdigest()}

def build_review_candidate(*, invocation: Mapping, binding_record: Mapping,
                           source_head: str, epoch: str, lease_path: Path,
                           proxy_path: Path, interpreter: Path) -> dict:
    """Root-only, read-only R123 + R126 readbacks, never a release check.

    The caller must separately provide an authoritative frozen source_head.
    This function is not connected to launch_after_owner_claim() or ledger.
    """
    if os.geteuid() != 0: deny('ROOT_ONLY_READBACK')
    from scripts.coordination.control_plane.worker_runtime import cf10_r123_capsule_invocation_binding_v0_1 as r123
    from scripts.coordination.control_plane.worker_runtime import cf10_r126_root_external_revoke_v0_1 as r126
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    if not isinstance(lease_path, Path) or not lease_path.is_absolute() or not LEASE_RE.fullmatch(str(lease_path)):
        deny('LEASE_PATH')
    if (not isinstance(proxy_path, Path) or proxy_path.is_symlink() or not proxy_path.is_file()
        or not stat.S_ISREG(proxy_path.stat().st_mode) or proxy_path.stat().st_mode & 0o022):
        deny('PROXY_SOURCE_UNTRUSTED')
    if not isinstance(interpreter, Path) or not interpreter.is_file():
        deny('INTERPRETER_MISSING')
    try:
        proof = r123.verify_record(record=binding_record, invocation=invocation)
        lease = r126.inspect_lease(lease_path, attempt=invocation['attempt_id'],
                                  epoch=epoch, source_head=source_head, capsule_id=CAPSULE_ID)
    except (r123.BindingBlocked, r126.ExternalRevokeHold, KeyError, ValueError, OSError, TypeError):
        deny('EXISTING_READBACK_REJECTED')
    socket_path = lease_path.with_name('mcp.sock')
    try:
        st = socket_path.lstat()
        gid = r126.runner_gid()
    except (OSError, KeyError):
        deny('SOCKET_MISSING')
    if not (stat.S_ISSOCK(st.st_mode) and st.st_uid == 0 and st.st_gid == gid
            and stat.S_IMODE(st.st_mode) == 0o660):
        deny('SOCKET_OWNER_MODE')
    candidate = render_review_candidate(invocation=invocation, binding_record=binding_record,
        verified_binding=proof, verified_lease=lease, source_head=source_head, epoch=epoch,
        socket_path=socket_path, proxy_path=proxy_path, interpreter=interpreter,
        live_cutover_enabled=launcher.LIVE_CUTOVER_ENABLED)
    # R134: independently cross-check the prospective read-only proxy argv
    # against the EXISTING R115 canonical invocation, before returning review.
    # R115's live preclaim remains unchanged and still REJECTS this argv.
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_r134_ipc_preclaim_crosswalk_v0_1 as r134,
    )
    try:
        r134.verify_source_only(invocation=invocation, candidate=candidate)
    except r134.IPCPreclaimHold:
        deny('R134_PRECLAIM_CROSSWALK')
    return candidate
