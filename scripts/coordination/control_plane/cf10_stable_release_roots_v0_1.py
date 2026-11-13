"""CF10 G2a stable historical Gate/Writer release-root migration.

Project-native SOURCE, externally provisioned release checkouts. This never
changes signed decisions, evidence, ledger, worker runtime, or Make launch gate.
`inspect` is read-only except an optional derived report under generated/.
`provision` is an explicit root-operator filesystem action, not authorization.
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
import sys
from datetime import datetime, timezone
from typing import Any
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

BRANCH = 'audit/blueprint-inventory-refresh-2026-07-29'
ORIGIN = 'git@github.com:Kovalchuk-PrintMaster/Forprint_System_Blueprint.git'
BASE = Path('/srv/software_development/forprint-releases/cf10')
Q1_MARKER = 'CF10 MAKE SURFACE Q1: INDEPENDENT RELEASE REBIND REQUIRED'
RELEASES = {
    'gate': {
        'head': '3d90143a240439d33833463d38ab0fb3497eac8f',
        'ref': 'refs/heads/cf10/writer-coverage-indirect-append-v0-4',
        'source': 'scripts/coordination/execution_attempt_writer_coverage_v0_1.py',
        'git_blob_oid': '06a7b4eeb757254c0f098be393780f950a266407',
    },
    'writer': {
        'head': 'd5d1495c0a1ab25367c146b0f5379b015e03dd85',
        'ref': 'refs/heads/cf10/closeout-writer-activation-v0-1',
        'source': 'scripts/coordination/execution_attempt_writer_activation_v0_1.py',
        'git_blob_oid': 'e098c6dc8c15192d33b3c0560830b2bb37a0f338',
    },
}
SCHEMA = 'cf10_g2a_stable_release_roots_review_v0_1'
SHA40 = re.compile('[0-9a-f]{40}\\Z')

class ReviewBlocked(RuntimeError):
    pass

def git(root: Path, *args: str, timeout: int = 45) -> bytes:
    try:
        result = subprocess.run(['git', *args], cwd=root, capture_output=True,
                                check=False, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ReviewBlocked('GIT_UNAVAILABLE:' + args[0]) from exc
    if result.returncode:
        raise ReviewBlocked('GIT_BLOCKED:' + args[0] + ':RC=' + str(result.returncode))
    if len(result.stdout) > 12_000_000:
        raise ReviewBlocked('GIT_OUTPUT_OVERSIZE')
    return result.stdout

def utf(raw: bytes) -> str:
    return raw.decode('utf-8', 'strict').strip()

def blob_oid(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\x00' + raw).hexdigest()

def safe_file(path: Path) -> bytes:
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or (st.st_mode & 0o022):
        raise ReviewBlocked('SOURCE_NOT_REGULAR_OR_WRITABLE_BY_OTHERS')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0))
    try:
        cur = os.fstat(fd)
        if (cur.st_ino, cur.st_dev) != (st.st_ino, st.st_dev):
            raise ReviewBlocked('SOURCE_REPLACED')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(12_000_001)
        if len(data) > 12_000_000:
            raise ReviewBlocked('SOURCE_OVERSIZE')
        return data
    finally:
        os.close(fd)

def assert_no_symlinks(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ReviewBlocked('SYMLINK_IN_PATH:' + str(part))

def stable_path(kind: str, base: Path = BASE) -> Path:
    if kind not in RELEASES:
        raise ReviewBlocked('UNKNOWN_RELEASE_KIND')
    return base / kind / RELEASES[kind]['head']

def root_identity(canonical: Path, expected: str, *, network: bool = True,
                  allow_missing_local_pins: bool = False) -> dict[str, Any]:
    if not SHA40.fullmatch(expected) or canonical.is_symlink() or not canonical.is_dir():
        raise ReviewBlocked('CANONICAL_ROOT_OR_HEAD_UNSAFE')
    if utf(git(canonical, 'rev-parse', '--show-toplevel')) != str(canonical.resolve()):
        raise ReviewBlocked('CANONICAL_NOT_GIT_TOP')
    head = utf(git(canonical, 'rev-parse', 'HEAD'))
    if head != expected:
        raise ReviewBlocked('CANONICAL_HEAD_DRIFT')
    if utf(git(canonical, 'branch', '--show-current')) != BRANCH:
        raise ReviewBlocked('CANONICAL_BRANCH_DRIFT')
    if utf(git(canonical, 'remote', 'get-url', 'origin')) != ORIGIN:
        raise ReviewBlocked('CANONICAL_ORIGIN_DRIFT')
    if utf(git(canonical, 'diff', '--cached', '--name-only')):
        raise ReviewBlocked('CANONICAL_STAGED_INDEX_NOT_EMPTY')
    marker_bytes = safe_file(canonical / 'Makefile')
    if marker_bytes != git(canonical, 'show', expected + ':Makefile'):
        raise ReviewBlocked('CANONICAL_MAKEFILE_NOT_PUBLISHED_BYTES')
    marker = marker_bytes.decode('utf-8')
    if Q1_MARKER not in marker or 'QUARANTINED_NEEDS_INDEPENDENT_REBIND' not in marker:
        raise ReviewBlocked('Q1_QUARANTINE_NOT_INSTALLED')
    if 'cf10-make-surface-policy-check:' not in marker:
        raise ReviewBlocked('Q1_POLICY_TARGET_MISSING')
    if network:
        remote = utf(git(canonical, 'ls-remote', '--exit-code', 'origin', 'refs/heads/' + BRANCH))
        if remote != expected + '\trefs/heads/' + BRANCH:
            raise ReviewBlocked('CANONICAL_REMOTE_HEAD_DRIFT')
    missing = []
    # Validate the publication ref first. A remote ref is provenance, not authority.
    for kind, pin in RELEASES.items():
        if network:
            remote = utf(git(canonical, 'ls-remote', '--exit-code', 'origin', pin['ref']))
            if remote != pin['head'] + '\t' + pin['ref']:
                raise ReviewBlocked('RELEASE_REMOTE_REF_DRIFT:' + kind)
        try:
            git(canonical, 'cat-file', '-e', pin['head'] + '^{commit}')
        except ReviewBlocked as exc:
            if allow_missing_local_pins and 'GIT_BLOCKED:cat-file:RC=128' in str(exc):
                missing.append(kind)
                continue
            raise ReviewBlocked('PINNED_RELEASE_OBJECT_MISSING_OR_INVALID:' + kind) from exc
        raw = git(canonical, 'show', pin['head'] + ':' + pin['source'])
        if blob_oid(raw) != pin['git_blob_oid']:
            raise ReviewBlocked('PINNED_GIT_BLOB_DRIFT:' + kind)
    if missing and not allow_missing_local_pins:
        raise ReviewBlocked('PINNED_RELEASE_OBJECTS_MISSING:' + ','.join(missing))
    return {'canonical_head': head, 'branch': BRANCH, 'remote_verified': network,
            'pinned_git_objects_verified': not missing,
            'pinned_git_objects_missing': missing}


PINNED_REF_PREFIX = 'refs/forprint/cf10/pinned/'


def pinned_ref(kind: str) -> str:
    if kind not in RELEASES:
        raise ReviewBlocked('UNKNOWN_RELEASE_KIND')
    return PINNED_REF_PREFIX + kind


def optional_git_ref(root: Path, ref: str) -> str | None:
    p = subprocess.run(['git', 'rev-parse', '--verify', '--quiet', ref],
                       cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=30, check=False)
    if p.returncode == 1 and not p.stdout:
        return None
    if p.returncode != 0:
        raise ReviewBlocked('PINNED_LOCAL_REF_UNREADABLE')
    return utf(p.stdout)


def recover_pinned_source_objects(canonical: Path, expected_head: str) -> list[str]:
    """Operator-only .git hydration: exact remote refs -> immutable local pin refs.

    Does not alter HEAD, branch, index, tracked files or signed authority.
    Called only within explicitly confirmed G2a provisioning.
    """
    before = root_identity(canonical, expected_head, network=True,
                           allow_missing_local_pins=True)
    # All remote publication refs have already been compared with pinned SHAs.
    refs = {kind: optional_git_ref(canonical, pinned_ref(kind)) for kind in RELEASES}
    for kind, existing in refs.items():
        if existing is not None and existing != RELEASES[kind]['head']:
            raise ReviewBlocked('PINNED_LOCAL_REF_DRIFT:' + kind)
    imported = []
    for kind, pin in RELEASES.items():
        if refs[kind] is None:
            git(canonical, 'fetch', '--no-tags', '--no-write-fetch-head',
                '--no-recurse-submodules', 'origin', pin['ref'] + ':' + pinned_ref(kind),
                timeout=180)
            imported.append(kind)
        if optional_git_ref(canonical, pinned_ref(kind)) != pin['head']:
            raise ReviewBlocked('PINNED_LOCAL_REF_POSTFETCH_DRIFT:' + kind)
        git(canonical, 'cat-file', '-e', pin['head'] + '^{commit}')
        raw = git(canonical, 'show', pin['head'] + ':' + pin['source'])
        if blob_oid(raw) != pin['git_blob_oid']:
            raise ReviewBlocked('PINNED_LOCAL_BLOB_POSTFETCH_DRIFT:' + kind)
    # Ensure source frozen state did not change while importing objects.
    after = root_identity(canonical, expected_head, network=True)
    if before['canonical_head'] != after['canonical_head']:
        raise ReviewBlocked('CANONICAL_HEAD_CHANGED_DURING_HYDRATION')
    return imported


def inspect_release(path: Path, kind: str, *, base: Path = BASE) -> dict[str, Any]:
    pin = RELEASES[kind]
    expected = stable_path(kind, base)
    if path != expected:
        return {'kind': kind, 'status': 'BLOCKED', 'reason': 'UNAPPROVED_RELEASE_LOCATION'}
    try:
        assert_no_symlinks(path)
        if not path.exists():
            return {'kind': kind, 'status': 'MISSING', 'reason': 'PERMANENT_CHECKOUT_NOT_PROVISIONED',
                    'head': pin['head']}
        if not path.is_dir():
            raise ReviewBlocked('ROOT_NOT_DIRECTORY')
        st = path.stat()
        if st.st_uid != 0 or st.st_mode & 0o022:
            raise ReviewBlocked('RELEASE_ROOT_NOT_ROOT_CONTROLLED')
        if utf(git(path, 'rev-parse', '--show-toplevel')) != str(path.resolve()):
            raise ReviewBlocked('RELEASE_NOT_GIT_TOP')
        if utf(git(path, 'rev-parse', 'HEAD')) != pin['head']:
            raise ReviewBlocked('RELEASE_CHECKOUT_HEAD_DRIFT')
        if utf(git(path, 'remote', 'get-url', 'origin')) != ORIGIN:
            raise ReviewBlocked('RELEASE_CHECKOUT_REMOTE_DRIFT')
        if utf(git(path, 'status', '--porcelain=v1', '--untracked-files=all')):
            raise ReviewBlocked('RELEASE_CHECKOUT_DIRTY')
        assert_no_symlinks(path / pin['source'])
        raw = safe_file(path / pin['source'])
        if blob_oid(raw) != pin['git_blob_oid']:
            raise ReviewBlocked('CHECKOUT_BLOB_DRIFT')
        if raw != git(path, 'show', pin['head'] + ':' + pin['source']):
            raise ReviewBlocked('WORKTREE_NOT_EXACT_PINNED_BLOB')
        return {'kind': kind, 'status': 'PASS', 'reason': 'EXACT_ROOT_OWNED_PINNED_RELEASE',
                'head': pin['head'], 'source_blob_oid': pin['git_blob_oid']}
    except (OSError, ValueError, ReviewBlocked, UnicodeError) as exc:
        return {'kind': kind, 'status': 'BLOCKED', 'reason': str(exc)[:200]}

def review(canonical: Path, expected_head: str, *, network: bool = True,
           base: Path = BASE) -> dict[str, Any]:
    checks = {}
    try:
        checks['canonical'] = {'status': 'PASS', **root_identity(canonical, expected_head, network=network)}
    except (OSError, ValueError, ReviewBlocked, UnicodeError) as exc:
        checks['canonical'] = {'status': 'BLOCKED', 'reason': str(exc)[:200]}
    for kind in RELEASES:
        checks[kind] = inspect_release(stable_path(kind, base), kind, base=base)
    statuses = {v['status'] for v in checks.values()}
    state = ('BLOCKED_NON_AUTHORIZING' if 'BLOCKED' in statuses else
             'RELEASE_ROOTS_NOT_PROVISIONED_NON_AUTHORIZING' if 'MISSING' in statuses else
             'STABLE_RELEASES_READY_FOR_INDEPENDENT_REBIND_NON_AUTHORIZING')
    return {'schema_version': SCHEMA, 'state': state, 'checks': checks,
            'historical_technical_coverage_evidence_migrated': False,
            'historical_gate_coverage_binding_reauthorized': False,
            'root_signed_activation_renewed': False,
            'make_launch_gate_unquarantined': False,
            'worker_launched': False,
            'authority_granted': False,
            'next_boundary': 'INDEPENDENT_COVERAGE_EVIDENCE_AND_SIGNED_HEAD_REBIND'}

def ensure_base_dirs(base: Path) -> None:
    if base != BASE:
        raise ReviewBlocked('ROOT_PROVISION_BASE_NOT_EXACTLY_APPROVED')
    assert_no_symlinks(base)
    for path in (base.parent.parent, base.parent, base):
        if path.exists():
            s = path.stat()
            if not stat.S_ISDIR(s.st_mode) or s.st_uid != 0 or s.st_mode & 0o022:
                raise ReviewBlocked('PROVISION_PARENT_UNSAFE:' + str(path))
        else:
            path.mkdir(mode=0o750)
            os.chmod(path, 0o750)

def provision(canonical: Path, expected_head: str, *, confirm: bool,
              hostname: str, base: Path = BASE) -> dict[str, Any]:
    if not confirm:
        raise ReviewBlocked('EXPLICIT_RELEASE_PROVISION_CONFIRMATION_REQUIRED')
    if os.geteuid() != 0 or hostname != 's01':
        raise ReviewBlocked('ROOT_OPERATOR_ON_S01_REQUIRED')
    imported = recover_pinned_source_objects(canonical, expected_head)
    before = review(canonical, expected_head, network=True, base=base)
    if before['checks']['canonical']['status'] != 'PASS' or any(
       r['status'] == 'BLOCKED' for r in before['checks'].values()):
        raise ReviewBlocked('PREPROVISION_REVIEW_BLOCKED')
    created = []
    for kind in ('gate', 'writer'):
        target = stable_path(kind, base)
        if target.exists():
            if inspect_release(target, kind, base=base)['status'] != 'PASS':
                raise ReviewBlocked('EXISTING_RELEASE_NOT_VERIFIED:' + kind)
            continue
        ensure_base_dirs(base)
        kindparent = target.parent
        if kindparent.exists():
            assert_no_symlinks(kindparent)
            st = kindparent.stat()
            if st.st_uid != 0 or st.st_mode & 0o022:
                raise ReviewBlocked('RELEASE_KIND_PARENT_UNSAFE')
        else:
            kindparent.mkdir(mode=0o750)
        # A completed existing checkout is NEVER removed or overwritten.
        # Partial Git clone remains quarantined for manual recovery.
        proc = subprocess.run(['git', 'clone', '--no-checkout', '--no-hardlinks',
             str(canonical), str(target)], capture_output=True, timeout=180, check=False)
        if proc.returncode:
            raise ReviewBlocked('PINNED_CLONE_FAILED:' + kind)
        git(target, 'remote', 'set-url', 'origin', ORIGIN)
        # Clone-from-canonical copies heads but not arbitrary pinned refs.
        # Transfer the verified historical commit explicitly from canonical.
        git(target, 'fetch', '--no-tags', '--no-write-fetch-head',
            '--no-recurse-submodules', str(canonical), pinned_ref(kind), timeout=180)
        git(target, 'cat-file', '-e', RELEASES[kind]['head'] + '^{commit}')
        raw = git(target, 'show', RELEASES[kind]['head'] + ':' + RELEASES[kind]['source'])
        if blob_oid(raw) != RELEASES[kind]['git_blob_oid']:
            raise ReviewBlocked('PINNED_TRANSFER_BLOB_DRIFT:' + kind)
        git(target, 'checkout', '--detach', RELEASES[kind]['head'])
        os.chmod(target, 0o750)
        if inspect_release(target, kind, base=base)['status'] != 'PASS':
            raise ReviewBlocked('POSTPROVISION_RELEASE_VERIFICATION_FAILED:' + kind)
        created.append(kind)
    after = review(canonical, expected_head, network=True, base=base)
    if after['state'] != 'STABLE_RELEASES_READY_FOR_INDEPENDENT_REBIND_NON_AUTHORIZING':
        raise ReviewBlocked('POSTPROVISION_REVIEW_NOT_READY')
    after['operator_provisioned_release_kinds'] = created
    after['operator_imported_pinned_sources'] = imported
    after['provisioning_only_no_authority'] = True
    return after

def report_zip(root: Path, report: dict[str, Any]) -> Path:
    generated = root / 'generated'
    if generated.is_symlink() or not generated.is_dir():
        raise ReviewBlocked('GENERATED_REPORT_ROOT_UNAVAILABLE')
    assert_no_symlinks(generated)
    path = generated / 'cf10_stable_release_reviews'
    path.mkdir(mode=0o700, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest = path / ('g2a_' + stamp)
    dest.mkdir(mode=0o700)
    brief = [
        'CF10_G2A_STATUS=' + report['state'],
        *[f'{name.upper()}={row["status"]}: {row.get("reason", "")}'
          for name, row in report['checks'].items()],
        'SIGNED_RENEWAL_PERFORMED=false',
        'WORKER_LAUNCHED=false',
        'AUTHORITY_GRANTED=false',
        'MAKE_LAUNCH_GATE_UNQUARANTINED=false',
    ]
    payloads = {'summary.txt': ('\n'.join(brief) + '\n').encode(),
        'report.json': (json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()}
    payloads['SHA256SUMS'] = ''.join(hashlib.sha256(v).hexdigest()+'  '+k+'\n'
                                    for k,v in sorted(payloads.items())).encode()
    archive = dest / 'CF10_G2A_Stable_Release_Review.zip'
    with ZipFile(archive, 'x', ZIP_DEFLATED) as z:
        for name, body in sorted(payloads.items()):
            zi = ZipInfo(name, date_time=(2026,1,1,0,0,0))
            zi.compress_type = ZIP_DEFLATED
            zi.external_attr = (0o600 << 16)
            z.writestr(zi, body)
    archive.chmod(0o600)
    return archive

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=('inspect', 'provision'))
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--expected-head', required=True)
    p.add_argument('--no-remote', action='store_true')
    p.add_argument('--confirm-provision', action='store_true')
    p.add_argument('--no-report', action='store_true')
    a = p.parse_args(argv)
    if a.mode == 'provision' and (a.no_remote or a.no_report):
        p.error('provision requires remote and durable review report')
    canonical = a.root.resolve()
    if a.mode == 'provision':
        result = provision(canonical, a.expected_head, confirm=a.confirm_provision,
                           hostname=os.uname().nodename.split('.')[0])
    else:
        result = review(canonical, a.expected_head, network=not a.no_remote)
    for key, item in result['checks'].items():
        print(f'{key.upper()}={item["status"]}:{item.get("reason", "VERIFIED")}', flush=True)
    print('CF10_G2A_STATUS=' + result['state'], flush=True)
    if not a.no_report:
        archive = report_zip(canonical, result)
        print('REPORT_ZIP=' + str(archive), flush=True)
        print('REPORT_SHA256=' + hashlib.sha256(archive.read_bytes()).hexdigest(), flush=True)
    print('SIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false', flush=True)
    return 2 if result['state'] == 'BLOCKED_NON_AUTHORIZING' else 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('CF10_G2A=BLOCKED:' + type(exc).__name__ + ':' + str(exc)[:220], file=sys.stderr)
        sys.exit(2)
