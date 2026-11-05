"""CF10 R090: read-only Codex binary/receipt lineage; opt-in offline exec --help.

The source ZIP never invokes Codex. Help probe is a separate root/TTY Make
command; the command is hardcoded, network denied, no task, no auth, no claim.
Help text is untrusted and only a bounded public option-presence observation.
Nothing here promotes Registry READY, authorizes Worker or accepts a result.
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
from collections.abc import Mapping

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r088_codex_offline_attestation_v0_1 as r088,
    cf10_r089_codex_pinned_install_v0_1 as r089,
)

SCHEMA = 'cf10_r090_codex_binary_lineage_and_offline_help_v0_1'
PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
HEAD_AT_INSTALL = 'c951bef0e2238ea3322a4779ced3e6d546e7be89'
BINARY = Path('/usr/local/bin/codex')
RECEIPT_ROOT = Path('/var/lib/forprint-provider-provenance')
RECEIPT = RECEIPT_ROOT / 'codex_r089_v0_166_0_install.json'
EXPECTED_BINARY_SHA_X86_64 = 'b8a11fedf24b2dfb59a70c9e52b030f9a508dcd49cd2dd0d41956f4c785156b8'
CONFIRM = 'PROBE_CODEX_EXEC_HELP_OFFLINE_NO_WORKER'
ROOT_UID = 0
ROOT_GID = 0
MAX_RECEIPT_BYTES = 8192
MAX_HELP_BYTES = 65536
PROBE_TIMEOUT = 45
HELP_FLAGS = (
    '--json', '--ephemeral', '--ignore-user-config', '--ignore-rules',
    '--sandbox', '--model', '--cd',
)
HEX40 = re.compile(r'[0-9a-f]{40}\Z')


class LineageBlocked(RuntimeError):
    pass


def deny(code: str) -> None:
    raise LineageBlocked('CF10_R090_' + code)


def _trusted_regular(path: Path, *, mode: int | None = None) -> os.stat_result:
    """Inspect the inode, rejecting symlinks and unexpected ownership/modes."""
    try:
        s = path.lstat()
    except (OSError, ValueError):
        deny('FILE_UNAVAILABLE_OR_UNTRUSTED')
    if (not stat.S_ISREG(s.st_mode) or s.st_uid != ROOT_UID
        or s.st_gid != ROOT_GID or s.st_mode & 0o022 or s.st_nlink != 1):
        deny('FILE_OWNER_MODE_LINK_COUNT_DRIFT')
    if mode is not None and stat.S_IMODE(s.st_mode) != mode:
        deny('FILE_EXACT_MODE_DRIFT')
    return s


def _private_receipt_root() -> None:
    # The durable path may not be redirected through a symlinked ancestor.
    if RECEIPT_ROOT.is_symlink():
        deny('DURABLE_RECEIPT_ROOT_SYMLINK')
    if RECEIPT_ROOT == Path('/var/lib/forprint-provider-provenance'):
        for ancestor in (Path('/var'), Path('/var/lib')):
            try:
                st = ancestor.lstat()
            except OSError:
                deny('DURABLE_RECEIPT_ANCESTOR_MISSING')
            if not stat.S_ISDIR(st.st_mode) or st.st_uid != ROOT_UID or st.st_mode & 0o022:
                deny('DURABLE_RECEIPT_ANCESTOR_UNTRUSTED')
    try:
        s = RECEIPT_ROOT.lstat()
    except (OSError, ValueError):
        deny('DURABLE_RECEIPT_ROOT_UNAVAILABLE')
    if (not stat.S_ISDIR(s.st_mode) or s.st_uid != ROOT_UID or s.st_gid != ROOT_GID
        or stat.S_IMODE(s.st_mode) != 0o700):
        deny('DURABLE_RECEIPT_ROOT_NOT_PRIVATE')


def _read_receipt() -> Mapping:
    _private_receipt_root()
    before = _trusted_regular(RECEIPT, mode=0o600)
    if before.st_size <= 0 or before.st_size > MAX_RECEIPT_BYTES:
        deny('DURABLE_RECEIPT_SIZE_INVALID')
    fd = None
    try:
        fd = os.open(RECEIPT, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            deny('DURABLE_RECEIPT_RACED')
        with os.fdopen(fd, 'rb') as handle:
            fd = None
            raw = handle.read(MAX_RECEIPT_BYTES + 1)
        after = _trusted_regular(RECEIPT, mode=0o600)
    except OSError:
        deny('DURABLE_RECEIPT_NOFOLLOW_OPEN_FAILED')
    finally:
        if fd is not None:
            os.close(fd)
    if (len(raw) != before.st_size or
        (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) !=
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)):
        deny('DURABLE_RECEIPT_CHANGED_DURING_READ')
    try:
        data = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, ValueError, TypeError):
        deny('DURABLE_RECEIPT_JSON_INVALID')
    if not isinstance(data, dict):
        deny('DURABLE_RECEIPT_SCHEMA_INVALID')
    return data


def _hash_binary() -> str:
    before = _trusted_regular(BINARY, mode=0o755)
    if before.st_size < 1_000_000 or before.st_size > r089.MAX_BINARY_BYTES:
        deny('INSTALLED_BINARY_SIZE_INVALID')
    fd = None
    try:
        fd = os.open(BINARY, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            deny('INSTALLED_BINARY_RACED')
        digest = hashlib.sha256()
        with os.fdopen(fd, 'rb') as stream:
            fd = None
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        after = _trusted_regular(BINARY, mode=0o755)
    except OSError:
        deny('INSTALLED_BINARY_NOFOLLOW_READ_FAILED')
    finally:
        if fd is not None:
            os.close(fd)
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) != (
        before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns
    ):
        deny('INSTALLED_BINARY_CHANGED_DURING_HASH')
    return digest.hexdigest()


def _git(*args: str) -> bool:
    try:
        result = subprocess.run(['git', '-C', str(PROJECT), *args],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            check=False, timeout=15)
    except (OSError, subprocess.SubprocessError):
        deny('GIT_LINEAGE_UNAVAILABLE')
    return result.returncode == 0


def _check_install_head(source_head: str) -> None:
    if source_head != HEAD_AT_INSTALL or HEX40.fullmatch(source_head) is None:
        deny('INSTALL_SOURCE_HEAD_NOT_PINNED')
    if not _git('cat-file', '-e', HEAD_AT_INSTALL + '^{commit}'):
        deny('PINNED_INSTALL_COMMIT_UNAVAILABLE')
    if not _git('merge-base', '--is-ancestor', HEAD_AT_INSTALL, 'HEAD'):
        deny('INSTALLED_SOURCE_NOT_ANCESTOR_OF_CURRENT_HEAD')


def attest() -> dict:
    """Read-only positive attestation. Does not access Codex, auth or network."""
    inventory = r088.inspect_candidates()
    if (inventory.get('selected_executable') != str(BINARY)
        or inventory.get('status') != 'ONE_ROOT_OWNED_EXECUTABLE_CANDIDATE_NO_AUTH_ATTESTATION'):
        deny('R088_INSTALLED_EXECUTABLE_NOT_UNAMBIGUOUS')
    receipt = _read_receipt()
    source_head = receipt.get('source_head_at_install')
    if not isinstance(source_head, str):
        deny('RECEIPT_SOURCE_HEAD_MISSING')
    _check_install_head(source_head)
    selected = r089.selected_asset()
    if (selected['arch'] != 'x86_64' or r089.RELEASE != '0.166.0'
        or r089.TAG != 'rust-v0.166.0' or r089.DESTINATION != BINARY
        or r089.RECEIPT != RECEIPT or selected['sha256'] !=
        'a0bf572d2f93f056c6712a6da348e96078dc84f3885fd7be67807ef389cb3978'):
        deny('R089_PINNED_DISTRIBUTION_DRIFT')
    binary_sha = _hash_binary()
    if binary_sha != EXPECTED_BINARY_SHA_X86_64:
        deny('INSTALLED_BINARY_SHA_NOT_REVIEWED_PIN')
    expected_receipt = r089._receipt_body(
        pinned=selected, binary_sha256=binary_sha, source_head=HEAD_AT_INSTALL)
    if receipt != expected_receipt:
        deny('DURABLE_INSTALL_RECEIPT_NOT_EXACT')
    return {
        'schema_version': SCHEMA,
        'status': 'PINNED_CODEX_BINARY_AND_RECEIPT_EXACT_READONLY_NONAUTHORIZING',
        'provider_id': 'openai_codex_cli',
        'release': r089.RELEASE,
        'binary_path': str(BINARY),
        'binary_sha256': binary_sha,
        'receipt_path': str(RECEIPT),
        'receipt_canonical_sha256': hashlib.sha256(json.dumps(receipt, sort_keys=True,
             separators=(',', ':'), ensure_ascii=True).encode()).hexdigest(),
        'source_head_at_install': source_head,
        'r088_version_probe_not_reexecuted': True,
        'cli_exec_help_probe_executed': False,
        'provider_ready': False,
        'provider_auth_verified': False,
        'model_invoked': False,
        'worker_launched': False,
        'claim_consumed': False,
        'ledger_written': False,
        'automatic_retry': False,
        'live_dispatch_enabled': False,
    }


def build_help_argv(unit: str) -> list[str]:
    """No caller-controlled executable or command; only codex exec --help."""
    properties = r088.probe_properties(unit)
    if ('ReadWritePaths' in properties or properties.get('IPAddressDeny') != 'any'
        or properties.get('Restart') != 'no' or properties.get('User') != 'forprint-runner'):
        deny('R088_SANDBOX_CONTRACT_DRIFT')
    from scripts.coordination.control_plane import cf10_r077_runner_home_contract_v0_1 as home
    home.assert_systemd_properties(properties)
    return [
        '/usr/bin/systemd-run', '--wait', '--pipe', '--collect', '--quiet',
        '--unit=' + unit,
        '--description=ForPrint CF10 R090 offline Codex exec help probe',
        *['--property=' + key + '=' + value for key, value in sorted(properties.items())],
        '--', str(BINARY), 'exec', '--help',
    ]


def inspect_help_text(stdout: bytes, stderr: bytes, returncode: int) -> dict:
    """Report only public switch-presence booleans; no provider raw output."""
    if (type(returncode) is not int or returncode != 0 or not isinstance(stdout, bytes)
        or not isinstance(stderr, bytes) or not stdout or len(stdout) > MAX_HELP_BYTES
        or len(stderr) > MAX_HELP_BYTES):
        deny('CLI_HELP_OUTPUT_OR_EXIT_INVALID')
    try:
        decoded = stdout.decode('utf-8')
    except UnicodeDecodeError:
        deny('CLI_HELP_NOT_UTF8')
    observed = {flag: bool(re.search(re.escape(flag) + r'(?=[=\s,]|$)', decoded))
                for flag in HELP_FLAGS}
    missing = [flag for flag, present in observed.items() if not present]
    return {
        'status': 'HELP_SWITCHES_ADVERTISED_NOT_EXECUTION_AUTHORITY' if not missing else
                  'R087_ARGUMENTS_NOT_ALL_ADVERTISED_REQUIRES_REVIEW',
        'advertised_switches': observed,
        'unconfirmed_switches': missing,
        'stdout_sha256': hashlib.sha256(stdout).hexdigest(),
        'stdout_bytes': len(stdout),
        'stderr_bytes': len(stderr),
        'all_r087_switches_advertised': not missing,
        'actual_task_command_executed': False,
        'version_output_not_a_runtime_proof': True,
        'worker_launched': False,
        'result_accepted': False,
    }


def probe_help() -> dict:
    """Explicit read-only CLI help through disposable offline systemd unit."""
    if (os.geteuid() != 0 or not os.isatty(0) or not os.isatty(1)
        or Path.cwd() != PROJECT or PROJECT.is_symlink()):
        deny('ROOT_INTERACTIVE_CANONICAL_PROJECT_REQUIRED')
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    head = console.source_guard(PROJECT)
    if not isinstance(head, str) or HEX40.fullmatch(head) is None:
        deny('PUBLISHED_SOURCE_HEAD_INVALID')
    audit = attest()
    from scripts.coordination.control_plane import cf10_r077_runner_home_contract_v0_1 as home
    home.assert_runner_home()
    unit = 'forprint-cf10-codexprobe-' + uuid.uuid4().hex[:16]
    command = build_help_argv(unit)
    try:
        process = subprocess.run(command, input=b'', stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False, timeout=PROBE_TIMEOUT,
            env={'PATH': '/usr/bin:/bin', 'LANG': 'C'})
    except subprocess.TimeoutExpired:
        deny('OFFLINE_HELP_TIMEOUT_NO_RETRY_REVIEW_UNIT')
    except (OSError, subprocess.SubprocessError) as exc:
        deny('OFFLINE_HELP_UNAVAILABLE_' + type(exc).__name__)
    facts = inspect_help_text(process.stdout, process.stderr, process.returncode)
    return {
        **facts,
        'schema_version': SCHEMA,
        'provider_id': 'openai_codex_cli',
        'binary_sha256': audit['binary_sha256'],
        'offline_systemd_unit_collected': True,
        'network_access_prohibited': True,
        'codex_home_disposable': True,
        'provider_ready': False,
        'provider_auth_verified': False,
        'claim_consumed': False,
        'ledger_written': False,
        'live_dispatch_enabled': False,
        'automatic_retry': False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('attest', 'help-probe'), required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == 'attest':
            result = attest()
        else:
            if os.environ.get('CF10_CONFIRM_CODEX_HELP_PROBE') != CONFIRM:
                deny('EXPLICIT_OFFLINE_HELP_CONFIRMATION_REQUIRED')
            result = probe_help()
        print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
        return 0
    except (LineageBlocked, OSError, ValueError, TypeError, KeyError) as exc:
        print('CF10_R090_BLOCKED=' + type(exc).__name__)
        print('CF10_R090_NO_WORKER_NO_CLAIM=true')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
