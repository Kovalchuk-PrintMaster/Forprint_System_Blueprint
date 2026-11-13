"""CF10 R089: exact-release Codex binary intake with explicit, one-shot install.

The source/Make installer never invokes this install path. Only the operator can
invoke a pinned, independently SHA-256 checked, official GitHub Release asset.
No npm lifecycle scripts, curl|sh, user-supplied URL, shell, credentials, Worker,
PAM, root claim, source repo write, registry READY, or retry/fallback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile

SCHEMA = 'cf10_r089_pinned_codex_binary_install_v0_1'
RELEASE = '0.166.0'
TAG = 'rust-v0.166.0'
PUBLISHED = '2026-10-29'
PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
DESTINATION = Path('/usr/local/bin/codex')
OTHER = Path('/usr/bin/codex')
RECEIPT_ROOT = Path('/var/lib/forprint-provider-provenance')
RECEIPT = RECEIPT_ROOT / 'codex_r089_v0_166_0_install.json'
CONFIRM = 'INSTALL_PINNED_CODEX_0_166_0_NO_WORKER'
ASSETS = {
    'x86_64': {
        'name': 'codex-x86_64-unknown-linux-musl.tar.gz',
        'member': 'codex-x86_64-unknown-linux-musl',
        'sha256': 'a0bf572d2f93f056c6712a6da348e96078dc84f3885fd7be67807ef389cb3978',
        'bytes': 121764138,
        'elf_machine': 62,
    },
    'aarch64': {
        'name': 'codex-aarch64-unknown-linux-musl.tar.gz',
        'member': 'codex-aarch64-unknown-linux-musl',
        'sha256': '94eb707605ec2646b2e05b7edf7c4e7b3ccf02b16237c34ae9beb8cfb7f810a9',
        'bytes': 113382496,
        'elf_machine': 183,
    },
}
MAX_ARCHIVE_BYTES = 170_000_000
MAX_BINARY_BYTES = 550_000_000
HEX64 = re.compile(r'[a-f0-9]{64}\Z')


class InstallBlocked(RuntimeError):
    pass


def deny(code: str) -> None:
    raise InstallBlocked('CF10_R089_' + code)


def selected_asset(machine: str | None = None) -> dict:
    machine = platform.machine() if machine is None else machine
    if machine not in ASSETS:
        deny('HOST_ARCH_NOT_SUPPORTED')
    return {**ASSETS[machine], 'arch': machine,
            'url': 'https://github.com/openai/codex/releases/download/' + TAG + '/' + ASSETS[machine]['name']}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            part = stream.read(1024 * 1024)
            if not part:
                break
            digest.update(part)
    return digest.hexdigest()


def _root_directory(path: Path) -> None:
    """Reject writable/symlink path ancestors, including the destination parent."""
    if not path.is_absolute() or '..' in path.parts:
        deny('DIRECTORY_NOT_ABSOLUTE')
    for parent in (Path('/'), *reversed(path.parents), path):
        try:
            item = parent.lstat()
        except (OSError, ValueError):
            deny('TRUSTED_DIRECTORY_NOT_AVAILABLE')
        if not stat.S_ISDIR(item.st_mode) or item.st_uid != 0 or item.st_mode & 0o022:
            deny('UNTRUSTED_DIRECTORY_PARENT')


def _must_not_exist(path: Path, reason: str) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError:
        deny('TARGET_STAT_UNAVAILABLE')
    deny(reason)


def preflight_for_install() -> dict:
    if (os.geteuid() != 0 or not os.isatty(0) or not os.isatty(1)
        or Path.cwd() != PROJECT or PROJECT.is_symlink()):
        deny('EXPLICIT_ROOT_INTERACTIVE_PROJECT_REQUIRED')
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane.worker_runtime import cf10_r088_codex_offline_attestation_v0_1 as r088
    head = console.source_guard(PROJECT)
    if not isinstance(head, str) or not re.fullmatch(r'[a-f0-9]{40}', head):
        deny('PUBLISHED_SOURCE_GUARD_FAILED')
    asset = selected_asset()
    _root_directory(DESTINATION.parent)
    _root_directory(OTHER.parent)
    inventory = r088.inspect_candidates()
    if inventory.get('status') != 'CODEX_CLI_NOT_INSTALLED_IN_ALLOWED_PATHS':
        deny('EXISTING_CODEX_OR_UNTRUSTED_BINARY_REVIEW_NO_REPLACE')
    _must_not_exist(DESTINATION, 'TARGET_ALREADY_PRESENT_NO_REPLACE')
    _must_not_exist(OTHER, 'OTHER_CODEX_ALREADY_PRESENT_NO_REPLACE')
    _must_not_exist(RECEIPT, 'DURABLE_INSTALL_RECEIPT_ALREADY_PRESENT')
    _root_directory(Path('/var'))
    temp = Path('/var/tmp').lstat()
    if (not stat.S_ISDIR(temp.st_mode) or temp.st_uid != 0
        or not (temp.st_mode & stat.S_ISVTX)):
        deny('DISPOSABLE_ROOT_TMP_NOT_STICKY')
    if shutil.disk_usage('/var/tmp').free < 250_000_000:
        deny('DOWNLOAD_VOLUME_INSUFFICIENT')
    if shutil.disk_usage(DESTINATION.parent).free < 650_000_000:
        deny('DESTINATION_VOLUME_INSUFFICIENT')
    return {'head': head, 'asset': asset}


def _download_pinned(asset: dict, destination: Path) -> None:
    """No shell, installer script, package manager, inherited auth, or raw output."""
    argv = [
        '/usr/bin/curl', '--disable', '--fail', '--location', '--silent',
        '--show-error', '--proto', '=https', '--proto-redir', '=https',
        '--connect-timeout', '20', '--max-time', '720',
        '--max-filesize', str(MAX_ARCHIVE_BYTES),
        '--output', str(destination), asset['url'],
    ]
    try:
        result = subprocess.run(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=750, check=False,
            env={'PATH': '/usr/bin:/bin', 'LANG': 'C'},
        )
    except subprocess.TimeoutExpired:
        deny('PINNED_DOWNLOAD_TIMEOUT_NO_RETRY')
    except (OSError, subprocess.SubprocessError) as exc:
        deny('PINNED_DOWNLOAD_UNAVAILABLE_' + type(exc).__name__)
    if result.returncode != 0:
        deny('PINNED_DOWNLOAD_FAILED_NO_RETRY_RC_' + str(result.returncode))
    st = destination.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_size != asset['bytes'] or st.st_size > MAX_ARCHIVE_BYTES:
        deny('PINNED_RELEASE_ARCHIVE_SIZE_MISMATCH')
    if sha_file(destination) != asset['sha256']:
        deny('OFFICIAL_RELEASE_ARCHIVE_SHA256_MISMATCH')


def _extract_checked(archive: Path, destination: Path, asset: dict) -> str:
    """Exact one regular tar member, bounded unpack, ELF arch, no links/traversal."""
    try:
        with tarfile.open(archive, mode='r:gz') as tar:
            members = tar.getmembers()
            if (len(members) != 1 or members[0].name != asset['member']
                or not members[0].isfile() or members[0].size < 1_000_000
                or members[0].size > MAX_BINARY_BYTES):
                deny('OFFICIAL_RELEASE_TAR_MEMBER_SCOPE_UNEXPECTED')
            member = members[0]
            source = tar.extractfile(member)
            if source is None:
                deny('OFFICIAL_RELEASE_MEMBER_UNREADABLE')
            copied = 0
            with source, destination.open('xb') as target:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    copied += len(chunk)
                    if copied > member.size:
                        deny('BINARY_LENGTH_EXCEEDED')
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
            if copied != member.size:
                deny('BINARY_LENGTH_UNEXPECTED')
    except (tarfile.TarError, EOFError, OSError, ValueError) as exc:
        deny('PINNED_ARCHIVE_EXTRACTION_FAILED_' + type(exc).__name__)
    with destination.open('rb') as stream:
        header = stream.read(64)
    if (len(header) < 20 or header[:4] != b'\x7fELF' or header[4] != 2
        or header[5] != 1 or int.from_bytes(header[18:20], 'little') != asset['elf_machine']):
        deny('CODEX_BINARY_NOT_EXPECTED_ELF_ARCH')
    return sha_file(destination)


def _receipt_directory() -> None:
    if not RECEIPT_ROOT.exists():
        # No tmp dependency; this is a permanent root-owned, private state dir.
        RECEIPT_ROOT.mkdir(mode=0o700)
    _root_directory(RECEIPT_ROOT)
    st = RECEIPT_ROOT.lstat()
    if stat.S_IMODE(st.st_mode) != 0o700:
        deny('DURABLE_RECEIPT_DIRECTORY_NOT_PRIVATE')


def _receipt_body(*, pinned: dict, binary_sha256: str, source_head: str) -> dict:
    return {
        'schema_version': SCHEMA, 'provider_id': 'openai_codex_cli',
        'release': RELEASE, 'release_tag': TAG, 'release_date': PUBLISHED,
        'source_head_at_install': source_head,
        'asset_name': pinned['name'], 'asset_url': pinned['url'],
        'asset_sha256': pinned['sha256'], 'binary_sha256': binary_sha256,
        'binary_path': str(DESTINATION), 'installed_as_direct_regular_file': True,
        'registry_ready': False, 'provider_auth_verified': False,
        'network_used_only_to_fetch_pinned_archive': True,
        'worker_launched': False, 'owner_claim_consumed': False,
        'ledger_written': False, 'automatic_fallback': False,
        'automatic_retry': False,
    }


def _record_receipt_once(body: dict) -> None:
    content = (json.dumps(body, sort_keys=True, indent=2) + '\n').encode('utf-8')
    fd = os.open(RECEIPT, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb', closefd=True) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        # Never silently allow an incomplete receipt to attest provenance.
        deny('DURABLE_RECEIPT_WRITE_INCOMPLETE_REVIEW_NO_RETRY')


def install_once() -> dict:
    facts = preflight_for_install()
    asset = facts['asset']
    _receipt_directory()
    # The only mutable objects before publish are private disposable staging.
    with tempfile.TemporaryDirectory(prefix='cf10-r089-codex-', dir='/var/tmp') as scratch:
        archive = Path(scratch) / 'official-release.tar.gz'
        _download_pinned(asset, archive)
        with tempfile.TemporaryDirectory(prefix='.cf10-r089-stage-', dir=DESTINATION.parent) as stage:
            executable = Path(stage) / 'codex'
            binary_sha = _extract_checked(archive, executable, asset)
            os.chown(executable, 0, 0)
            os.chmod(executable, 0o755)
            # Recheck no preexisting Codex *after* the network operation.
            _must_not_exist(DESTINATION, 'CONCURRENT_INSTALL_TARGET_EXISTS_NO_REPLACE')
            _must_not_exist(OTHER, 'CONCURRENT_OTHER_CODEX_EXISTS_NO_REPLACE')
            try:
                # Atomic no-replace hardlink, unlike os.replace / rename overwrite.
                os.link(executable, DESTINATION, follow_symlinks=False)
            except FileExistsError:
                deny('CONCURRENT_INSTALL_TARGET_EXISTS_NO_REPLACE')
            except OSError as exc:
                deny('ATOMIC_BINARY_PUBLICATION_FAILED_' + type(exc).__name__)
            if sha_file(DESTINATION) != binary_sha:
                deny('INSTALLED_BINARY_HASH_DRIFT_REVIEW_NO_RETRY')
    body = _receipt_body(pinned=asset, binary_sha256=binary_sha, source_head=facts['head'])
    _record_receipt_once(body)
    from scripts.coordination.control_plane.worker_runtime import cf10_r088_codex_offline_attestation_v0_1 as r088
    inventory = r088.inspect_candidates()
    if inventory.get('selected_executable') != str(DESTINATION):
        deny('POSTINSTALL_R088_INVENTORY_NOT_EXACT_REVIEW_NO_RETRY')
    return {
        'schema_version': SCHEMA,
        'status': 'PINNED_OFFICIAL_CODEX_BINARY_INSTALLED_NONAUTHORIZING',
        'provider_id': 'openai_codex_cli', 'release': RELEASE,
        'executable': str(DESTINATION), 'binary_sha256': binary_sha,
        'durable_receipt': str(RECEIPT),
        'offline_version_probe_executed': False,
        'provider_auth_verified': False, 'provider_ready': False,
        'worker_launched': False, 'claim_consumed': False,
        'ledger_written': False, 'automatic_fallback': False,
        'automatic_retry': False,
    }


def inspect() -> dict:
    from scripts.coordination.control_plane.worker_runtime import cf10_r088_codex_offline_attestation_v0_1 as r088
    asset = selected_asset()
    inventory = r088.inspect_candidates()
    return {
        'schema_version': SCHEMA,
        'status': 'PINNED_RELEASE_INSTALL_AVAILABLE_EXPLICIT_OPT_IN_REQUIRED',
        'release': RELEASE, 'release_tag': TAG,
        'selected_architecture': asset['arch'],
        'official_asset_sha256': asset['sha256'],
        'installed_candidate': inventory['selected_executable'],
        'inventory_state': inventory['status'],
        'durable_receipt_present': RECEIPT.exists(),
        'install_executed': False, 'cli_version_executed': False,
        'provider_ready': False, 'worker_launched': False,
        'claim_consumed': False, 'ledger_written': False,
        'provider_auth_verified': False, 'automatic_retry': False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', required=True, choices=('inspect', 'install'))
    args = parser.parse_args(argv)
    try:
        if args.mode == 'inspect':
            result = inspect()
        else:
            if os.environ.get('CF10_CONFIRM_CODEX_INSTALL') != CONFIRM:
                deny('EXPLICIT_PINNED_INSTALL_CONFIRMATION_REQUIRED')
            result = install_once()
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (InstallBlocked, OSError, ValueError, RuntimeError, TypeError, KeyError) as exc:
        print('CF10_R089_BLOCKED=' + type(exc).__name__)
        print('CF10_R089_NO_WORKER_NO_CLAIM=true')
        print('CF10_R089_IF_INSTALL_PARTIAL_REVIEW_NO_AUTOMATIC_RETRY=true')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
