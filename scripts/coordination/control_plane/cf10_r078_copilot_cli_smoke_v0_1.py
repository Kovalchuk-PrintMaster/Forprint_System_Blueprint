"""R078: disposable, OFFLINE Copilot --version under the R077 systemd sandbox.

Never launches an actual Worker, runs prompts, accesses credentials, claims an
attempt, writes ledger/receipts, checks auth or proves production readiness.
The sole allowed executable is the published provider registry executable.
No user-provided argv, shell, credentials, or environment are ever forwarded.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import uuid

PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
HOME = Path('/var/lib/forprint-runner')
PROVIDER = 'github_copilot_cli'
SCHEMA = 'cf10_r078_copilot_version_smoke_v0_1'
CONFIRM = 'PROBE_COPILOT_VERSION_OFFLINE_DISPOSABLE_NO_WORKER'
VERSION_TIMEOUT = 25

class SmokeBlocked(RuntimeError):
    pass

def deny(code: str) -> None:
    raise SmokeBlocked('CF10_R078_' + code)


def executable_from_registry(root: Path) -> Path:
    """Read ONLY the source-controlled registry; no a054 manifest or argv."""
    from scripts.coordination.control_plane.worker_runtime import registry
    config = registry.load_module_runtime_config(root)
    selected = registry.resolve_default_runtime(root)
    command = config['command']
    exe = selected.get('executable')
    if (selected.get('provider_id') != PROVIDER or not isinstance(exe, str)
        or not exe.startswith(('/usr/bin/', '/usr/local/bin/', '/bin/'))
        or any(x in exe for x in ('\x00', '\r', '\n'))
        or '..' in Path(exe).parts or Path(exe).as_posix() != exe
        or command.get('provider_id') != PROVIDER
        or command.get('executable') != exe
        or not isinstance(command.get('base_argv'), list)
        or not command['base_argv'] or command['base_argv'][0] != exe):
        deny('PROVIDER_EXECUTABLE_REGISTRY_DRIFT')
    path = Path(exe)
    try:
        s = path.stat()
    except OSError:
        deny('EXECUTABLE_NOT_AVAILABLE')
    if not stat.S_ISREG(s.st_mode) or s.st_mode & 0o022 or not (s.st_mode & 0o111):
        deny('EXECUTABLE_PERMISSIONS')
    return path


def build_probe_argv(executable: Path, properties: dict[str, str], unit: str) -> list[str]:
    """Pure builder; accepts only one fixed CLI mode, no prompt or token args."""
    from scripts.coordination.control_plane import cf10_r077_runner_home_contract_v0_1 as home
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
    if not isinstance(executable, Path) or not executable.is_absolute():
        deny('EXECUTABLE_PATH')
    if not re.fullmatch(r'forprint-cf10-clismoke-[0-9a-f]{16}', unit):
        deny('DISPOSABLE_UNIT_ID')
    expected = {
        **bound.EXPECTED_PROPERTIES,
        'WorkingDirectory': str(HOME),
        'Environment': 'HOME=' + str(HOME),
        'Restart': 'no',
        'Type': 'exec',
        'RuntimeMaxSec': str(VERSION_TIMEOUT) + 's',
        'IPAddressDeny': 'any',
    }
    try:
        home.assert_systemd_properties(properties)
    except home.HomeBlocked:
        deny('SANDBOX_PROPERTY_SCOPE')
    if properties != expected or 'ReadWritePaths' in properties:
        deny('SANDBOX_PROPERTY_SCOPE')
    return [
        '/usr/bin/systemd-run', '--wait', '--pipe', '--collect', '--quiet',
        '--unit=' + unit,
        '--description=ForPrint CF10 R078 offline Copilot version smoke',
        *['--property=' + k + '=' + v for k, v in sorted(properties.items())],
        '--', str(executable), '--version',
    ]


def classify_output(stdout: bytes, stderr: bytes) -> str:
    """Return only a bounded category; never print raw provider responses."""
    raw = (stdout + b'\n' + stderr).lower()
    if b'enoent' in raw or b'failed to extract bundled package' in raw:
        return 'CLI_CACHE_OR_BUNDLE_INIT_ERROR'
    if b'permission denied' in raw or b'eacces' in raw or b'erofs' in raw:
        return 'CLI_SANDBOX_PERMISSION_ERROR'
    if b'not found' in raw or b'no such file' in raw:
        return 'CLI_DEPENDENCY_MISSING'
    if b'auth' in raw or b'token' in raw:
        return 'CLI_AUTH_OR_CREDENTIAL_MESSAGE_NOT_VERIFIED'
    return 'CLI_OTHER_FAILURE_OUTPUT_WITHHELD'


def prereq() -> Path:
    if os.geteuid() != 0 or Path.cwd() != PROJECT or PROJECT.is_symlink():
        deny('CANONICAL_ROOT_REQUIRED')
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_r077_runner_home_contract_v0_1 as home
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
    head = console.source_guard(PROJECT)
    if not re.fullmatch(r'[0-9a-f]{40}', head):
        deny('PUBLISHED_SOURCE_HEAD_INVALID')
    home.assert_runner_home()
    home.assert_systemd_properties(bound.EXPECTED_PROPERTIES)
    return executable_from_registry(PROJECT)


def probe() -> dict:
    if not (os.isatty(0) and os.isatty(1)):
        deny('INTERACTIVE_ROOT_TTY_REQUIRED')
    executable = prereq()
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
    properties = {
        **bound.EXPECTED_PROPERTIES,
        'WorkingDirectory': str(HOME),
        'Environment': 'HOME=' + str(HOME),
        'Restart': 'no',
        'Type': 'exec',
        'RuntimeMaxSec': str(VERSION_TIMEOUT) + 's',
        'IPAddressDeny': 'any',
    }
    unit = 'forprint-cf10-clismoke-' + uuid.uuid4().hex[:16]
    command = build_probe_argv(executable, properties, unit)
    # No Copilot auth environment, root credentials, prompt, MCP or Worker argv.
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C'}
    try:
        proc = subprocess.run(command, input=b'', stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env, timeout=45, check=False)
    except subprocess.TimeoutExpired:
        deny('DISPOSABLE_CLI_TIMEOUT_NO_RETRY_REVIEW_UNIT')
    except (OSError, subprocess.SubprocessError) as exc:
        deny('DISPOSABLE_SYSTEMD_UNAVAILABLE_' + type(exc).__name__)
    if proc.returncode != 0 or not proc.stdout.strip():
        deny('VERSION_SMOKE_FAILED_RC_' + str(proc.returncode) +
             '_' + classify_output(proc.stdout[:8192], proc.stderr[:8192]))
    if len(proc.stdout) > 8192 or len(proc.stderr) > 8192:
        deny('PROVIDER_OUTPUT_UNEXPECTEDLY_LARGE')
    return {
        'schema_version': SCHEMA,
        'status': 'PASS_OFFLINE_DISPOSABLE_COPILOT_VERSION_ONLY_NON_AUTHORIZING',
        'provider_id': PROVIDER,
        'cli_executable': str(executable),
        'systemd_transient_unit_collected': True,
        'runner_home_state_directory': True,
        'network_access_prohibited': True,
        'cli_version_output_nonempty': True,
        'stdout_bytes': len(proc.stdout), 'stderr_bytes': len(proc.stderr),
        'auth_tested': False, 'provider_request_sent': False,
        'mcp_invoked': False, 'worker_launched': False,
        'claim_consumed': False, 'ledger_written': False,
        'a054_modified': False, 'automatic_retry': False,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode', required=True, choices=('inspect', 'probe'))
    ap.add_argument('--confirm', default='')
    args = ap.parse_args(argv)
    try:
        exe = prereq()
        if args.mode == 'inspect':
            result = {
                'schema_version': SCHEMA,
                'status': 'PUBLISHED_PROVIDER_BINARY_VERIFIED_NO_EXECUTION',
                'provider_id': PROVIDER, 'cli_executable': str(exe),
                'auth_tested': False, 'worker_launched': False,
                'claim_consumed': False,
            }
        else:
            if args.confirm != CONFIRM:
                deny('EXPLICIT_OFFLINE_PROBE_CONFIRMATION_REQUIRED')
            result = probe()
        print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
        return 0
    except (SmokeBlocked, OSError, ValueError, TypeError, KeyError) as exc:
        print('CF10_R078_BLOCKED=' + type(exc).__name__ + ':' + str(exc)[:180])
        print('CF10_R078_NO_WORKER_NO_CLAIM=true')
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
