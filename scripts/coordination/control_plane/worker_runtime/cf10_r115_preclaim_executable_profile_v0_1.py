"""R115: read-only feasibility checks before a single-use systemd Worker claim.

This module is a *negative* boundary, not sandbox, broker, auth, production
release, endpoint inventory or evidence of effective policy. Copilot-only pilot
pin intentionally lives here rather than in provider-neutral task contracts.

No side effects except reading a root-controlled executable. No subprocess.
"""
from __future__ import annotations

import hashlib
import os
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
    properties = parse_systemd_properties(systemd_command)
    assert_inference_network_not_impossible(properties)
    assert_pinned_binary()
    return {
        'schema_version': 'cf10_r115_preclaim_executable_profile_v0_1',
        'status': 'PASS_NEGATIVE_PRECLAIM_FEASIBILITY_ONLY_NOT_AUTHORIZING',
        'pinned_copilot_binary_sha256': COPILOT_PILOT_SHA256,
        'live_worker_authorized': False,
        'effective_sandbox_policy_attested': False,
        'provider_vs_tool_egress_enforced': False,
        'root_broker_epoch_revocation_attested': False,
        'release_to_terminal_ledger_join_attested': False,
        'claim_consumed': False,
        'worker_launched': False,
    }
