"""R115: read-only feasibility checks before a single-use systemd Worker claim.

This module is a *negative* boundary, not sandbox, broker, auth, production
release, endpoint inventory or evidence of effective policy. Copilot-only pilot
pin intentionally lives here rather than in provider-neutral task contracts.

No side effects except reading a root-controlled executable. No subprocess.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
import stat
from collections.abc import Mapping, Sequence


COPILOT_PILOT_PATH = Path('/usr/local/bin/forprint-copilot-1.0.107')
COPILOT_PILOT_SHA256 = '985f0e1b1b3e734bc996324651307a076ae3deae21e3fa9f9af917983ce309c4'
COPILOT_PILOT_BYTES = 205458240


class R115PreclaimBlocked(RuntimeError):
    pass


def deny(code: str) -> None:
    raise R115PreclaimBlocked('CF10_R115_PRECLAIM_' + code)


def assert_frozen_argv(argv: Sequence[str], workspace: str) -> None:
    """Check fixed, source-reviewed Copilot pilot argv, not arbitrary CLI flags.

    Prefix enforcement also prevents accidental reuse of the unpinned legacy
    /usr/local/bin/copilot executable. This is a provisional one-provider
    policy; never use it to select future Workers or remote executors.
    """
    if (not isinstance(argv, (tuple, list)) or len(argv) < 18
        or any(not isinstance(x, str) or not x or '\x00' in x for x in argv)
        or not isinstance(workspace, str) or not workspace.startswith('/')
        or argv[0] != str(COPILOT_PILOT_PATH)):
        deny('FROZEN_PROVIDER_BINARY_PATH_NOT_PINNED')
    if list(argv[-4:]) != ['--no-auto-update', '--sandbox', '-C', workspace]:
        deny('SANDBOX_ARGV_TAIL_NOT_FROZEN')
    for flag in ('--no-sandbox', '--allow-all-paths', '--allow-all-urls', '--allow-all', '--yolo'):
        if flag in argv:
            deny('EXPLICIT_UNSAFE_CLI_FLAG')
    for required in ('-p', '--model', '--available-tools',
                     '--additional-mcp-config', '--disable-builtin-mcps', '--max-ai-credits'):
        if argv.count(required) != 1:
            deny('FROZEN_ARGV_OPTION_MISSING_OR_DUPLICATE')
    if argv.count('--sandbox') != 1 or argv.count('-C') != 1:
        deny('FROZEN_ARGV_SANDBOX_AMBIGUOUS')



# R117 S02 is deliberately a STATIC preclaim narrowing, not kernel isolation.
# New providers and new tools require a reviewed source change, not prompt text.
PILOT_TOOL_UNIVERSE = frozenset({
    'view', 'edit', 'apply_patch',
    'ForPrintValidation-run_validation_suite',
    'ForPrintValidation-run_repo_diff_check',
    'ForPrintValidation-run_repo_head',
    'ForPrintValidation-run_repo_status',
    'ForPrintValidation-read_completed_validation_evidence',
})
PILOT_MCP_SERVER = 'ForPrintValidation'


def _unique_json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            deny('MCP_DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def assert_static_tool_and_mcp_boundary(argv: Sequence[str], workspace: str) -> None:
    """Close the prompt/argv tool-widening gap BEFORE owner claim.

    This never authorizes a Worker. It cannot attest the effective native
    sandbox, protect Copilot in-process tools from credentials, or control the
    inference network. Existing ForPrintValidation remains the only MCP.
    """
    if (not isinstance(argv, (tuple, list)) or len(argv) < 19
        or argv[0] != str(COPILOT_PILOT_PATH)
        or argv[1] != '-p' or list(argv[3:5]) != ['--silent', '--model']
        or argv[6] != '--additional-mcp-config'
        or argv[8] != '--available-tools'
        or not isinstance(argv[2], str) or not argv[2]
        or not isinstance(argv[5], str) or not argv[5]
        or not isinstance(argv[7], str)
        or list(argv[-8:-6]) != ['--allow-all-tools', '--disable-builtin-mcps']
        or argv[-6] != '--max-ai-credits'
        or list(argv[-4:]) != ['--no-auto-update', '--sandbox', '-C', workspace]):
        deny('EXACT_COPILOT_PILOT_ARGV_SHAPE_REQUIRED')
    credits = argv[-5]
    if not isinstance(credits, str) or not credits.isdecimal() or not 30 <= int(credits) <= 10000:
        deny('COPILOT_PILOT_CREDIT_BOUND')
    tools = argv[9:-8]
    if (not tools or len(tools) > len(PILOT_TOOL_UNIVERSE)
        or any(not isinstance(x, str) for x in tools)
        or len(tools) != len(set(tools))
        or any(x not in PILOT_TOOL_UNIVERSE for x in tools)):
        deny('COPILOT_TOOL_UNIVERSE_WIDENED')
    # The non-empty selected tool list may only contain the reviewed built-ins
    # and the bounded local MCP; no Bash/Web/remote/new provider tools.
    try:
        config = json.loads(argv[7], object_pairs_hook=_unique_json_pairs)
    except (ValueError, TypeError, UnicodeError):
        deny('COPILOT_MCP_CONFIG_JSON_INVALID')
    if not isinstance(config, dict) or set(config) != {'mcpServers'}:
        deny('COPILOT_MCP_CONFIG_ROOT_UNREVIEWED')
    servers = config['mcpServers']
    if not isinstance(servers, dict) or set(servers) != {PILOT_MCP_SERVER}:
        deny('COPILOT_REMOTE_OR_EXTRA_MCP_SERVER')
    spec = servers[PILOT_MCP_SERVER]
    if not isinstance(spec, dict):
        deny('COPILOT_MCP_SERVER_INVALID')
    assert_local_mcp_execution_identity(spec, workspace, tools)


# R118 S01: canonical invocation_adapter.py uses type=local, not type=stdio.
# Bound both the MODEL-facing MCP identity and the actual local executable,
# argv, cwd and tools before owner claim. No worker-provided env/overrides.
PILOT_MCP_SCRIPT = 'scripts/coordination/control_plane/worker_runtime/worker_validation_mcp.py'
PILOT_MCP_BASE_TOOLS = (
    'run_validation_suite', 'run_repo_diff_check', 'run_repo_head', 'run_repo_status',
)
PILOT_MCP_OPTIONAL_READBACK = 'read_completed_validation_evidence'
PILOT_MCP_BASE_WORKSPACE = Path(
    '/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01')
PILOT_MCP_ALLOWED_PYTHON = frozenset({
    '/srv/software_development/forprint-project/forprint_system_blueprint/.venv_blueprint/bin/python',
    '/srv/software_development/forprint-project/forprint_system_blueprint/.venv_blueprint/bin/python3',
    '/srv/software_development/forprint-project/forprint_system_blueprint/.venv_blueprint/bin/python3.11',
    '/usr/bin/python3', '/usr/bin/python3.11',
})


def assert_local_mcp_execution_identity(spec: Mapping, workspace: str,
                                        selected_tools: Sequence[str]) -> None:
    """Single canonical STDIO-local ForPrintValidation subprocess identity.

    This is a negative source contract, not proof that Copilot executes the
    same command, nor OS/isolation or protected credential attestation.
    """
    if not isinstance(spec, Mapping) or (set(spec) not in (
            {'type','command','args','tools','cwd'},
            {'type','command','args','tools','cwd','timeout'})):
        deny('MCP_SPEC_KEYS_UNREVIEWED')
    if spec['type'] != 'local':
        deny('MCP_CANONICAL_LOCAL_TYPE_REQUIRED')
    if not isinstance(spec['command'], str) or spec['command'] not in PILOT_MCP_ALLOWED_PYTHON:
        deny('MCP_INTERPRETER_NOT_SOURCE_BOUND')
    if not isinstance(workspace, str) or not workspace.startswith('/') or '..' in Path(workspace).parts:
        deny('MCP_WORKSPACE_SCOPE')
    try:
        relative=Path(workspace).relative_to(PILOT_MCP_BASE_WORKSPACE)
    except ValueError:
        deny('MCP_WORKSPACE_SCOPE')
    parts=relative.parts
    if len(parts)!=3 or parts[1:]!=('workspace','repo') or not re.fullmatch(
            r'cf10-[A-Za-z0-9_-]{3,80}-a[0-9]{3,5}',parts[0]):
        deny('MCP_WORKSPACE_ATTEMPT_SCOPE')
    attempt=parts[0]
    if spec['cwd']!=workspace:
        deny('MCP_CWD_NOT_FROZEN')
    tools=spec['tools']
    if not isinstance(tools,list) or tools not in (
            list(PILOT_MCP_BASE_TOOLS),
            [*PILOT_MCP_BASE_TOOLS,PILOT_MCP_OPTIONAL_READBACK]):
        deny('MCP_TOOLS_NOT_CANONICAL')
    selected=list(selected_tools)
    expected=['view','edit','apply_patch',
              *[PILOT_MCP_SERVER+'-'+x for x in tools]]
    if selected != expected:
        deny('MCP_MODEL_TOOL_LIST_DRIFT')
    args=spec['args']
    if not isinstance(args,list) or any(not isinstance(v,str) or not v for v in args):
        deny('MCP_ARGS_INVALID')
    fixed=13+(1 if len(tools)==5 else 0)
    if len(args)!=fixed:
        deny('MCP_ARGS_SHAPE')
    if args[0]!=str(Path(workspace)/PILOT_MCP_SCRIPT):
        deny('MCP_SCRIPT_PATH_NOT_FROZEN')
    names=['--attempt-id','--task-id','--work-front-id','--decision-id','--workspace-repo','--evidence-root']
    for i,name in enumerate(names):
        if args[1+i*2]!=name:
            deny('MCP_ARGS_FLAGS_NOT_FROZEN')
    vals={k:args[2+i*2] for i,k in enumerate(names)}
    if vals['--attempt-id']!=attempt:
        deny('MCP_ATTEMPT_ID_DRIFT')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}',vals['--task-id']):
        deny('MCP_TASK_ID_FORMAT')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}',vals['--work-front-id']):
        deny('MCP_WORK_FRONT_ID_FORMAT')
    if not re.fullmatch(r'[0-9a-f]{64}',vals['--decision-id']):
        deny('MCP_DISPATCH_DECISION_ID_FORMAT')
    if vals['--workspace-repo']!=workspace:
        deny('MCP_WORKSPACE_ARG_DRIFT')
    if vals['--evidence-root']!=str(PILOT_MCP_BASE_WORKSPACE/attempt/'evidence'/'structured_command'):
        deny('MCP_EVIDENCE_ROOT_DRIFT')
    if len(tools)==5 and args[-1]!='--enable-completed-readback':
        deny('MCP_READBACK_FLAG_DRIFT')
    if 'timeout' in spec and (type(spec['timeout']) is not int or not 900_000<spec['timeout']<=1_200_000):
        deny('MCP_TIMEOUT_POLICY_DRIFT')
    # Deliberately no env, envFile, transport, HTTP, extra flags, cwd
    # override or configurable executable command. Any requires new review.


def _require_root_owned_parent(path: Path) -> None:
    # Directories are root-controlled to prevent swap-out between pin and exec.
    for p in (Path('/usr'), Path('/usr/local'), Path('/usr/local/bin')):
        try:
            info = p.lstat()
        except OSError:
            deny('EXECUTABLE_PARENT_UNAVAILABLE')
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != 0
            or stat.S_IMODE(info.st_mode) & 0o022):
            deny('EXECUTABLE_PARENT_NOT_ROOT_CONTROLLED')


def assert_pinned_binary() -> None:
    """Read the exact executable without following a final-component symlink.

    The gate-entry's independent exec-time pin and root broker remain required
    work, so passing this *preclaim* check does not attest kernel enforcement.
    """
    path = COPILOT_PILOT_PATH
    _require_root_owned_parent(path)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError:
        deny('DURABLE_COPILOT_BINARY_MISSING_OR_LINKED')
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0
            or stat.S_IMODE(info.st_mode) & 0o022
            or not stat.S_IMODE(info.st_mode) & 0o100
            or info.st_size != COPILOT_PILOT_BYTES):
            deny('DURABLE_COPILOT_INODE_OR_SIZE_DRIFT')
        sha = hashlib.sha256()
        with os.fdopen(os.dup(fd), 'rb') as source:
            while chunk := source.read(1024 * 1024):
                sha.update(chunk)
        after = os.fstat(fd)
        if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
            info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns
        ):
            deny('DURABLE_COPILOT_INODE_CHANGED_DURING_READ')
        if sha.hexdigest() != COPILOT_PILOT_SHA256:
            deny('DURABLE_COPILOT_SHA256_MISMATCH')
    finally:
        os.close(fd)


def parse_systemd_properties(argv: Sequence[str]) -> dict[str, str]:
    """Reject duplicate properties; do not accept spoofed strings in manifest."""
    if not isinstance(argv, (list, tuple)) or not argv or any(not isinstance(v, str) for v in argv):
        deny('SYSTEMD_COMMAND_INVALID')
    values: dict[str, str] = {}
    for part in argv:
        if not part.startswith('--property='):
            continue
        body = part[len('--property='):]
        if '=' not in body:
            deny('SYSTEMD_PROPERTY_MALFORMED')
        key, value = body.split('=', 1)
        if not key or key in values:
            deny('SYSTEMD_PROPERTY_DUPLICATE')
        values[key] = value
    return values


def assert_inference_network_not_impossible(properties: Mapping[str, str]) -> None:
    """Only negative feasibility: does NOT prove tool-versus-inference egress.

    The current pilot uses DIRECT network inference and has no verified local
    broker; a future brokered AF_UNIX design needs its own source-controlled
    mode with independent epoch/revocation and endpoint proofs.
    """
    if not isinstance(properties, Mapping):
        deny('SYSTEMD_PROFILE_MISSING')
    if properties.get('PrivateNetwork', '').lower() in ('yes', 'true', '1'):
        deny('DIRECT_PROVIDER_NETWORK_NAMESPACE_BLOCKED')
    if properties.get('IPAddressDeny', '').strip().lower() == 'any':
        deny('DIRECT_PROVIDER_NETWORK_DENIED_BY_SYSTEMD')
    families = properties.get('RestrictAddressFamilies', '').split()
    if families:
        negated = families[0].startswith('~')
        if negated:
            denied = {f.lstrip('~') for f in families}
            if {'AF_INET', 'AF_INET6'}.issubset(denied):
                deny('DIRECT_PROVIDER_AF_INET_UNAVAILABLE')
        elif not any(f in families for f in ('AF_INET', 'AF_INET6')):
            deny('DIRECT_PROVIDER_AF_INET_UNAVAILABLE')
    # Absence of blocks is not positive authorization. A root broker, egress
    # policy, HOME privacy, sandbox effectiveness and Ledger join are unproven.


def assert_pilot_preclaim(*, argv: Sequence[str], workspace: str,
                          systemd_command: Sequence[str]) -> dict:
    assert_frozen_argv(argv, workspace)
    assert_static_tool_and_mcp_boundary(argv, workspace)
    properties = parse_systemd_properties(systemd_command)
    assert_inference_network_not_impossible(properties)
    assert_pinned_binary()
    return {
        'schema_version': 'cf10_r115_preclaim_executable_profile_v0_1',
        'status': 'PASS_NEGATIVE_PRECLAIM_FEASIBILITY_ONLY_NOT_AUTHORIZING',
        'pinned_copilot_binary_sha256': COPILOT_PILOT_SHA256,
        'live_worker_authorized': False,
        'effective_sandbox_policy_attested': False,
        'static_tool_universe_source_bound': True,
        'local_mcp_single_server_source_bound': True,
        'credential_cache_kernel_isolated': False,
        'provider_vs_tool_egress_enforced': False,
        'root_broker_epoch_revocation_attested': False,
        'release_to_terminal_ledger_join_attested': False,
        'claim_consumed': False,
        'worker_launched': False,
    }
