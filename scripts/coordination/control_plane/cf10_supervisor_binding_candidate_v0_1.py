"""CF-10 r013: fail-closed, NON-AUTHORIZING systemd supervisor plan + evidence contract.

Not a launcher. This module never invokes systemd, changes permissions, reads
credentials, issues an ACK/claim, or asserts production process quiescence.
Trusted owner/canonical lifecycle must authorize and independently bind all
inputs before any future wiring. Worker-controlled unit properties are unsafe.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

HEAD = re.compile(r"^[a-f0-9]{40}$")
HEX64 = re.compile(r"^[a-f0-9]{64}$")
TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{4,127}$")
ATTEMPT = re.compile(r"^cf10-[A-Za-z0-9_-]{3,80}-a[0-9]{3,5}$")
RUNNER = "forprint-runner"
UID = 996  # r004a / r012a server proof; MUST be revalidated on every host
GID = 992
UNIT_PREFIX = "forprint-cf10-worker-"
EXPECTED_PROPERTIES = {
    "User": RUNNER,
    "Group": RUNNER,
    "KillMode": "control-group",
    "Delegate": "no",
    "NoNewPrivileges": "yes",
    "ProtectControlGroups": "yes",
    "ProtectSystem": "strict",
    "ProtectHome": "yes",
    "PrivateTmp": "yes",
    "PrivateDevices": "yes",
    "RestrictNamespaces": "yes",
    "RestrictSUIDSGID": "yes",
    "CapabilityBoundingSet": "",
    "AmbientCapabilities": "",
    "SendSIGKILL": "yes",
    "UMask": "0077",
    "TasksMax": "32",
    "TimeoutStopSec": "10s",
}

class BoundaryBlocked(ValueError):
    pass


def deny(code: str) -> None:
    raise BoundaryBlocked("CF10_R013_" + code)


def _safe_string(value: str, pattern: re.Pattern, code: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        deny(code)
    return value


def _hash(value: Mapping) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def _clean_absolute(value: str, label: str) -> Path:
    if not isinstance(value, str) or not value.startswith('/') or any(c in value for c in ('\x00','\n','\r')):
        deny(label)
    path = Path(value)
    if '..' in path.parts or '.' in path.parts or str(path) != value or len(value) > 1024:
        deny(label)
    return path


def unit_for(attempt_id: str, source_head: str) -> str:
    _safe_string(attempt_id, ATTEMPT, 'ATTEMPT_INVALID')
    _safe_string(source_head, HEAD, 'HEAD_INVALID')
    suffix = hashlib.sha256((attempt_id + '\0' + source_head).encode()).hexdigest()[:24]
    return UNIT_PREFIX + suffix + '.service'


@dataclass(frozen=True)
class BoundedInput:
    task_prompt_id: str
    attempt_id: str
    source_head: str
    handoff_sha256: str
    baseline_sha256: str
    workspace: str
    runtime_root: str
    argv: tuple[str,...]
    timeout_seconds: int


def bind_plan(spec: BoundedInput) -> dict:
    """Compute a candidate plan ONLY, no authority; reject ambiguous scope."""
    if not isinstance(spec, BoundedInput): deny('SPEC_INVALID')
    _safe_string(spec.task_prompt_id, TOKEN, 'TASK_INVALID')
    _safe_string(spec.attempt_id, ATTEMPT, 'ATTEMPT_INVALID')
    _safe_string(spec.source_head, HEAD, 'HEAD_INVALID')
    _safe_string(spec.handoff_sha256, HEX64, 'HANDOFF_INVALID')
    _safe_string(spec.baseline_sha256, HEX64, 'BASELINE_INVALID')
    runtime = _clean_absolute(spec.runtime_root,'RUNTIME_INVALID')
    repo = _clean_absolute(spec.workspace,'WORKSPACE_INVALID')
    expected = runtime / 'forprint_system_blueprint' / 'worker-01' / spec.attempt_id / 'workspace' / 'repo'
    if repo != expected or repo == runtime: deny('WORKSPACE_OUTSIDE_ATTEMPT')
    if not isinstance(spec.argv, tuple) or not (1 <= len(spec.argv) <= 50):
        deny('COMMAND_INVALID')
    # R068: Copilot -p holds a bounded, multiline provider-owned prompt.
    # Preserve the strict nonprompt policy and bound total argv bytes as well.
    for index, item in enumerate(spec.argv):
        is_prompt = index > 0 and spec.argv[index - 1] in ('-p', '--prompt')
        is_mcp = index > 0 and spec.argv[index - 1] == '--additional-mcp-config'
        cap = 65536 if is_prompt else (8192 if is_mcp else 2000)
        forbidden = ('\x00', '\r') if is_prompt else ('\x00', '\r', '\n')
        if (not isinstance(item, str) or not item or
                len(item.encode('utf-8')) > cap or any(c in item for c in forbidden)):
            deny('COMMAND_INVALID')
    if sum(len(item.encode('utf-8')) + 1 for item in spec.argv) > 98304:
        deny('COMMAND_INVALID')
    executable = _clean_absolute(spec.argv[0], 'EXECUTABLE_INVALID')
    if not str(executable).startswith(('/usr/bin/', '/usr/local/bin/', '/bin/')):
        deny('EXECUTABLE_NOT_ALLOWLISTED')
    if (not isinstance(spec.timeout_seconds, int) or isinstance(spec.timeout_seconds,bool)
            or spec.timeout_seconds < 1 or spec.timeout_seconds > 7200):
        deny('TIMEOUT_INVALID')
    identity = {
        'attempt_id':spec.attempt_id,'task_prompt_id':spec.task_prompt_id,
        'source_head':spec.source_head,'handoff_sha256':spec.handoff_sha256,
        'baseline_sha256':spec.baseline_sha256,'workspace':spec.workspace,
        'runner_account':RUNNER,'runner_uid':UID,'runner_gid':GID,
        'unit':unit_for(spec.attempt_id,spec.source_head),
        'argv_sha256':hashlib.sha256('\0'.join(spec.argv).encode()).hexdigest(),
        'timeout_seconds':spec.timeout_seconds,
    }
    obj = {'schema_version':'cf10_supervisor_binding_candidate_v0_1',
           'identity':identity, 'properties':dict(EXPECTED_PROPERTIES),
           'flags': {'authorizing':False,'claim_issued':False,
                     'systemd_unit_started':False,'worker_result_accepted':False,
                     'production_quiescence_proven':False},
           'unresolved': ['CANONICAL_ACK_DISPATCH_LAUNCH_AUTHORITY',
                          'ROOT_OWNED_PROVENANCE_AND_ONE_TIME_CLAIM',
                          'CREDENTIAL_DELIVERY_AND_PROCESS_REAP',
                          'SYSTEMD_LIFECYCLE_AND_CRASH_RECOVERY',
                          'INDEPENDENT_RESULT_VERIFICATION']}
    obj['content_sha256'] = _hash(obj)
    return obj


def validate_plan(plan: Mapping, expected: BoundedInput) -> bool:
    if not isinstance(plan, dict) or plan != bind_plan(expected):
        deny('BOUND_PLAN_MISMATCH_OR_REPLAY')
    return True


def candidate_systemd_argv(plan: Mapping, spec: BoundedInput) -> list[str]:
    """Pure argv builder. MUST NOT BE CALLED by production without additional gates."""
    validate_plan(plan,spec)
    props=dict(plan['properties'])
    props['WorkingDirectory']=spec.workspace
    props['ReadWritePaths']=spec.workspace
    props['RuntimeMaxSec']=str(spec.timeout_seconds)+'s'
    return (['/usr/bin/systemd-run', '--unit='+plan['identity']['unit'],
             '--description=ForPrint CF10 bounded candidate', '--quiet']
            + ['--property='+k+'='+v for k,v in sorted(props.items())]
            + ['--'] + list(spec.argv))


def parse_systemd_show(raw: str) -> dict[str,str]:
    if not isinstance(raw,str) or len(raw)>32768: deny('SHOW_INVALID')
    result = {}
    for line in raw.splitlines():
        if '=' not in line: deny('SHOW_MALFORMED')
        k,v=line.split('=',1)
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,63}',k) or k in result or '\x00' in v:
            deny('SHOW_MALFORMED')
        result[k]=v
    return result


def assess_observation(*, plan: Mapping, spec: BoundedInput,
                       before: Mapping[str,str], after: Mapping[str,str],
                       sampled_pids: tuple[Mapping,...], cgroup_populated: str | None,
                       stop_rc: int) -> dict:
    """Evaluate untrusted observations; ALWAYS non-authorizing, even on PASS.

    Do not conflate sampled PID absence and cgroup vacancy with full production
    quiescence. Kernel-backed proof and recovery are separate future work.
    """
    validate_plan(plan,spec)
    unit=plan['identity']['unit']
    group='/system.slice/'+unit
    if (not isinstance(before,Mapping) or not isinstance(after,Mapping)
            or not isinstance(sampled_pids,tuple)):
        deny('OBSERVATION_INVALID')
    checks = {
        'unit_identity': before.get('Id') == unit and after.get('Id') == unit,
        'runner_identity': before.get('User') == RUNNER and before.get('Group') == RUNNER,
        'service_controls': all(before.get(k)==v for k,v in EXPECTED_PROPERTIES.items() if k in (
            'KillMode','Delegate','NoNewPrivileges','ProtectControlGroups','User','Group')),
        'parent_cgroup': before.get('ControlGroup') == group,
        'main_pid': before.get('MainPID','0').isdigit() and int(before.get('MainPID','0'))>1,
        'service_started': before.get('ActiveState') == 'active',
        'service_stopped': after.get('ActiveState') in ('inactive','failed') and after.get('MainPID') in ('0',''),
        'cgroup_empty': cgroup_populated in ('0', 'removed'),
        'stop_success': type(stop_rc) is int and stop_rc==0,
        'sampled_processes_gone': True,
    }
    for row in sampled_pids:
        if not isinstance(row,Mapping) or row.get('uid')!=UID or row.get('gid')!=GID or row.get('cgroup')!=group:
            checks['sampled_processes_gone']=False
        if not isinstance(row,Mapping) or row.get('alive_after_stop') is not False:
            checks['sampled_processes_gone']=False
    if not sampled_pids: checks['sampled_processes_gone']=False
    status='PASS_OBSERVATION_CANDIDATE_ONLY' if all(checks.values()) else 'BLOCKED_OBSERVATION_INCOMPLETE'
    return {
      'schema_version':'cf10_supervisor_observation_candidate_v0_1',
      'attempt_id':spec.attempt_id, 'source_head':spec.source_head,
      'unit':unit, 'checks':checks, 'status':status,
      'production_quiescence_proven':False,
      'authorization_granted':False,
      'worker_result_accepted':False,
      'promotion_allowed':False,
    }
