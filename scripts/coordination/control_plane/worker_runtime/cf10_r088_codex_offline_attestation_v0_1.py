"""CF10 R088: read-only Codex CLI inventory; opt-in offline --version sandbox.

NO installer, auth, network, prompts, Worker, attempt, ledger, claim, or READY.
Version-probe is an EXPLICIT, disposable SYSTEMD transient service only and
never runs during package installation or inspection. Output remains redacted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import uuid

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r087_codex_cli_candidate_v0_1 as codex_candidate,
)

SCHEMA = 'cf10_r088_codex_offline_attestation_v0_1'
PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
PROVIDER = 'openai_codex_cli'
HOME = Path('/var/lib/forprint-runner')
CONFIRM = 'PROBE_CODEX_VERSION_OFFLINE_DISPOSABLE_NO_WORKER'
TIMEOUT_SECONDS = 25
VERSION_CAP = 8192
# No PATH search and no executable supplied by operator or Worker.
CANDIDATES = (Path('/usr/local/bin/codex'), Path('/usr/bin/codex'))
UNIT = re.compile(r'forprint-cf10-codexprobe-[0-9a-f]{16}\Z')


class CodexOfflineBlocked(RuntimeError):
    pass


def deny(code: str) -> None:
    raise CodexOfflineBlocked('CF10_R088_' + code)


def _candidate_state(path: Path) -> str:
    """Pure observation; symlinks require separately reviewed target lineage."""
    if path not in CANDIDATES:
        deny('EXECUTABLE_NOT_ALLOWLISTED')
    for parent in (path.parent, path.parent.parent):
        try:
            st = parent.lstat()
        except FileNotFoundError:
            return 'DIRECTORY_MISSING'
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != 0 or st.st_mode & 0o022:
            return 'UNTRUSTED_EXECUTABLE_PARENT'
    try:
        st = path.lstat()
    except FileNotFoundError:
        return 'NOT_INSTALLED'
    if stat.S_ISLNK(st.st_mode):
        return 'SYMLINK_NEEDS_INDEPENDENT_PROVENANCE'
    if not stat.S_ISREG(st.st_mode):
        return 'NOT_REGULAR_EXECUTABLE'
    if st.st_uid != 0 or st.st_mode & 0o022 or not (st.st_mode & 0o111):
        return 'EXECUTABLE_OWNERSHIP_OR_MODE_UNTRUSTED'
    return 'EXACT_ROOT_OWNED_BINARY_CANDIDATE'


def inspect_candidates() -> dict:
    states = {str(path): _candidate_state(path) for path in CANDIDATES}
    verified = [path for path in CANDIDATES if states[str(path)] == 'EXACT_ROOT_OWNED_BINARY_CANDIDATE']
    if len(verified) == 1 and all(
        states[str(p)] == 'NOT_INSTALLED' for p in CANDIDATES if p != verified[0]
    ):
        state = 'ONE_ROOT_OWNED_EXECUTABLE_CANDIDATE_NO_AUTH_ATTESTATION'
        selected = str(verified[0])
    elif all(x == 'NOT_INSTALLED' for x in states.values()):
        state = 'CODEX_CLI_NOT_INSTALLED_IN_ALLOWED_PATHS'
        selected = None
    else:
        state = 'REVIEW_EXECUTABLE_PATH_OR_SYMLINK_NO_PROBE'
        selected = None
    return {
        'schema_version': SCHEMA,
        'status': state,
        'provider_id': PROVIDER,
        'candidate_paths': states,
        'selected_executable': selected,
        'source_adapter_exists': callable(codex_candidate.build_invocation),
        'provider_registry_ready': False,
        'executable_verified_for_worker': False,
        'cli_version_executed': False,
        'provider_auth_verified': False,
        'network_request_sent': False,
        'worker_launched': False,
        'claim_consumed': False,
        'ledger_written': False,
        'automatic_fallback': False,
        'automatic_retry': False,
        'live_dispatch_enabled': False,
    }


def probe_properties(unit: str) -> dict[str, str]:
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
    if not isinstance(unit, str) or UNIT.fullmatch(unit) is None:
        deny('UNIT_NAME_NOT_DISPOSABLE')
    # Isolated CODEX_HOME lives in the private ephemeral transient-unit
    # RuntimeDirectory; the runner's ordinary HOME is not used for Codex auth.
    return {
        **bound.EXPECTED_PROPERTIES,
        'WorkingDirectory': str(HOME),
        'Environment': 'HOME=' + str(HOME) + ' CODEX_HOME=/run/' + unit,
        'RuntimeDirectory': unit,
        'RuntimeDirectoryMode': '0700',
        'Restart': 'no',
        'Type': 'exec',
        'RuntimeMaxSec': str(TIMEOUT_SECONDS) + 's',
        'IPAddressDeny': 'any',
    }


def build_version_argv(executable: Path, properties: dict[str, str], unit: str) -> list[str]:
    """Pure builder: pinned --version ONLY, no prompt, auth, updater or shell."""
    from scripts.coordination.control_plane import cf10_r077_runner_home_contract_v0_1 as home
    if executable not in CANDIDATES or properties != probe_properties(unit):
        deny('DISPOSABLE_SANDBOX_DRIFT')
    if 'ReadWritePaths' in properties:
        deny('BROAD_RW_PATHS_FORBIDDEN')
    try:
        home.assert_systemd_properties(properties)
    except home.HomeBlocked:
        deny('R077_SANDBOX_POLICY_DRIFT')
    return [
        '/usr/bin/systemd-run', '--wait', '--pipe', '--collect', '--quiet',
        '--unit=' + unit,
        '--description=ForPrint CF10 R088 offline Codex version probe',
        *['--property=' + key + '=' + value for key, value in sorted(properties.items())],
        '--', str(executable), '--version',
    ]


def _safe_version_output(stdout: bytes, stderr: bytes, return_code: int) -> dict:
    if type(return_code) is not int or return_code != 0:
        deny('VERSION_PROBE_PROCESS_NOT_SUCCESSFUL')
    if (not isinstance(stdout, bytes) or not isinstance(stderr, bytes)
        or len(stdout) > VERSION_CAP or len(stderr) > VERSION_CAP
        or not stdout.strip()):
        deny('VERSION_PROBE_OUTPUT_INVALID')
    # No raw stdout/stderr echoed; may include sensitive executable details.
    return {
        'version_stdout_sha256': hashlib.sha256(stdout).hexdigest(),
        'version_stdout_length': len(stdout),
        'version_stderr_length': len(stderr),
        'version_output_nonempty': True,
    }


def _source_and_home() -> None:
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_r077_runner_home_contract_v0_1 as home
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
    # Published source and private runner identity required before any process.
    head = console.source_guard(PROJECT)
    if not isinstance(head, str) or not re.fullmatch(r'[a-f0-9]{40}', head):
        deny('PUBLISHED_SOURCE_HEAD_INVALID')
    home.assert_runner_home()
    home.assert_systemd_properties(bound.EXPECTED_PROPERTIES)


def probe_version() -> dict:
    """Explicit standalone offline version probe. Never a Worker invocation."""
    if (os.geteuid() != 0 or not os.isatty(0) or not os.isatty(1)
        or PROJECT.is_symlink() or Path.cwd() != PROJECT):
        deny('ROOT_INTERACTIVE_CANONICAL_PROJECT_REQUIRED')
    inventory = inspect_candidates()
    if inventory['selected_executable'] is None:
        deny('EXACT_EXECUTABLE_NOT_ATTESTABLE')
    _source_and_home()
    unit = 'forprint-cf10-codexprobe-' + uuid.uuid4().hex[:16]
    exe = Path(inventory['selected_executable'])
    argv = build_version_argv(exe, probe_properties(unit), unit)
    # Only these fixed environment scalars; no inherited auth/session tokens.
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C'}
    try:
        process = subprocess.run(
            argv, input=b'', stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, timeout=45, check=False,
        )
    except subprocess.TimeoutExpired:
        deny('PROBE_TIMEOUT_REVIEW_TRANSIENT_UNIT_NO_RETRY')
    except (OSError, subprocess.SubprocessError) as exc:
        deny('PROBE_SYSTEMD_ERROR_' + type(exc).__name__)
    observed = _safe_version_output(process.stdout, process.stderr, process.returncode)
    return {
        'schema_version': SCHEMA,
        'status': 'OFFLINE_DISPOSABLE_CODEX_VERSION_ONLY_PASS_NONAUTHORIZING',
        'provider_id': PROVIDER,
        'executable': str(exe),
        'runtime_unit_collected': True,
        'network_access_prohibited': True,
        'codex_home_disposable': True,
        'auth_tested': False,
        'model_executed': False,
        'prompt_sent': False,
        'provider_registry_ready': False,
        'worker_launched': False,
        'claim_consumed': False,
        'ledger_written': False,
        'automatic_retry': False,
        'live_dispatch_enabled': False,
        **observed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('inspect', 'probe'), required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == 'inspect':
            data = inspect_candidates()
        else:
            if os.environ.get('CF10_CONFIRM_CODEX_VERSION_PROBE') != CONFIRM:
                deny('EXPLICIT_VERSION_PROBE_CONFIRMATION_REQUIRED')
            data = probe_version()
        print(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (CodexOfflineBlocked, OSError, ValueError, TypeError, KeyError) as exc:
        print('CF10_R088_BLOCKED=' + type(exc).__name__)
        print('CF10_R088_NO_WORKER_NO_CLAIM=true')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
