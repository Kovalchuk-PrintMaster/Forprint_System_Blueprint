"""Project-native, NON-AUTHORIZING CF-10 immutable Gate/Writer release audit.

Never runs external release code, changes services, signs, dispatches or launches.
Reads pinned Git commit objects from canonical .git, and optionally *observes*
independent stable release roots. Historical evidence is not rewritten.
A PASS here is source-provenance evidence, NEVER Writer Activation authority.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

SCHEMA = 'cf10_gate_writer_release_audit_v0_1'
REPO = 'git@github.com:Kovalchuk-PrintMaster/Forprint_System_Blueprint.git'
BRANCH = 'audit/blueprint-inventory-refresh-2026-07-29'
EXPECTED_BASE = 'dc194b4c46846bdc5a767cdd499bfd05ba99a40b'
RELEASES = {
    'gate': {
        'commit': '3d90143a240439d33833463d38ab0fb3497eac8f',
        'ref': 'refs/heads/cf10/writer-coverage-indirect-append-v0-4',
        'module_path': 'scripts/coordination/execution_attempt_writer_coverage_v0_1.py',
        'blob_oid': '06a7b4eeb757254c0f098be393780f950a266407',
    },
    'writer': {
        'commit': 'd5d1495c0a1ab25367c146b0f5379b015e03dd85',
        'ref': 'refs/heads/cf10/closeout-writer-activation-v0-1',
        'module_path': 'scripts/coordination/execution_attempt_writer_activation_v0_1.py',
        'blob_oid': 'e098c6dc8c15192d33b3c0560830b2bb37a0f338',
    },
}
OLD_DEFAULTS = ('CF10_S01_GATE_ROOT ?= $(CURDIR)/tmp/',
                'CF10_S01_WRITER_ROOT ?= $(CURDIR)/tmp/',
                'CF10_S01_COVERAGE_EVIDENCE ?= $(CF10_S01_GATE_ROOT)/tmp/')
SHA40 = re.compile(r'[0-9a-f]{40}\Z')


def run(root: Path, argv: list[str], *, limit: int = 15_000_000) -> bytes:
    try:
        p = subprocess.run(argv, cwd=root, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=35, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError('GIT_EXECUTION_FAILED:' + argv[1]) from exc
    if p.returncode:
        raise ValueError('GIT_COMMAND_FAILED:' + argv[1])
    if len(p.stdout) > limit:
        raise ValueError('GIT_OUTPUT_TOO_LARGE')
    return p.stdout


def git(root: Path, *args: str) -> str:
    return run(root, ['git', *args], limit=200_000).decode('utf-8').strip()


def check(state: str, name: str, detail: str, *, category: str = 'PROVENANCE') -> dict[str,str]:
    return {'id': name, 'state': state, 'detail': detail, 'category': category}


def blob_oid(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\x00' + raw).hexdigest()


def read_regular(path: Path) -> bytes:
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o022:
        raise ValueError('FILE_NOT_REGULAR_OR_WRITABLE_BY_OTHERS')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(path, flags), 'rb') as f:
        current = os.fstat(f.fileno())
        if (current.st_ino, current.st_dev) != (st.st_ino, st.st_dev):
            raise ValueError('FILE_REPLACED_DURING_READ')
        return f.read(10_000_001)


def stable_root_check(root: Path | None, release: dict[str,str]) -> dict[str,str]:
    name = 'stable_' + ('gate' if release['module_path'].endswith('coverage_v0_1.py') else 'writer')
    if root is None:
        return check('NOT_YET_TESTABLE', name, 'STABLE_RELEASE_ROOT_NOT_CONFIGURED', category='STABLE_RELEASE')
    if not root.is_absolute() or any(part == 'tmp' for part in root.parts):
        return check('BLOCKED', name, 'RELEASE_ROOT_UNSAFE_OR_INSIDE_TMP', category='STABLE_RELEASE')
    if root.is_symlink() or not root.is_dir():
        return check('NOT_YET_TESTABLE', name, 'STABLE_RELEASE_ROOT_NOT_PROVISIONED', category='STABLE_RELEASE')
    if any(p.is_symlink() for p in (root, *root.parents)):
        return check('BLOCKED', name, 'STABLE_RELEASE_PATH_ANCESTOR_SYMLINK', category='STABLE_RELEASE')
    try:
        if git(root, 'rev-parse', '--show-toplevel') != str(root.resolve()):
            raise ValueError('NESTED_REPO')
        if git(root, 'rev-parse', 'HEAD') != release['commit']:
            raise ValueError('HEAD_DRIFT')
        if git(root, 'remote', 'get-url', 'origin') != REPO:
            raise ValueError('REMOTE_DRIFT')
        if git(root, 'status', '--porcelain=v1', '--untracked-files=no'):
            raise ValueError('TRACKED_RELEASE_DIRTY')
        raw = read_regular(root / release['module_path'])
        if blob_oid(raw) != release['blob_oid']:
            raise ValueError('RELEASE_MODULE_BLOB_DRIFT')
        return check('PASS', name, 'PINNED_RELEASE_SOURCE_OBSERVED_NON_AUTHORIZING', category='STABLE_RELEASE')
    except (ValueError, OSError, UnicodeError) as exc:
        return check('BLOCKED', name, type(exc).__name__ + ':' + str(exc)[:100], category='STABLE_RELEASE')


def audit(root: Path, expected_head: str, gate_root: Path | None = None,
          writer_root: Path | None = None, *, probe_remote: bool = True) -> list[dict[str,str]]:
    rows: list[dict[str,str]] = []
    def add(state: str, name: str, detail: str, category: str = 'PROVENANCE') -> None:
        rows.append(check(state, name, detail, category=category))

    try:
        if root.is_symlink() or not (root / '.git').exists() or not SHA40.fullmatch(expected_head):
            raise ValueError('UNSAFE_ROOT_OR_EXPECTED_HEAD')
        actual = git(root, 'rev-parse', 'HEAD')
        top = git(root, 'rev-parse', '--show-toplevel')
        branch = git(root, 'branch', '--show-current')
        origin = git(root, 'remote', 'get-url', 'origin')
        staged = git(root, 'diff', '--cached', '--name-only')
        add('PASS' if actual == expected_head and top == str(root.resolve()) and branch == BRANCH
            and origin == REPO and not staged else 'BLOCKED', 'canonical_identity',
            f'HEAD={actual}; branch={branch}; staged_count={len(staged.splitlines())}')
    except (ValueError, OSError, UnicodeError) as exc:
        add('BLOCKED', 'canonical_identity', type(exc).__name__ + ':' + str(exc)[:160])

    for kind, rel in RELEASES.items():
        try:
            # Both provenance anchors are mandatory: pinned commit AND exact blob.
            git(root, 'cat-file', '-e', rel['commit'] + '^{commit}')
            raw = run(root, ['git','show',rel['commit'] + ':' + rel['module_path']])
            oid = blob_oid(raw)
            if oid != rel['blob_oid']:
                raise ValueError('HISTORICAL_RELEASE_BLOB_SHA_MISMATCH')
            add('PASS', kind + '_git_object', 'COMMIT_AND_SOURCE_BLOB_PIN_MATCH; git_blob=' + oid)
        except (OSError, ValueError, UnicodeError) as exc:
            add('BLOCKED', kind + '_git_object', type(exc).__name__ + ':' + str(exc)[:120])
        if probe_remote:
            try:
                line = git(root, 'ls-remote', '--exit-code', 'origin', rel['ref']).splitlines()
                if line != [rel['commit'] + '\t' + rel['ref']]:
                    raise ValueError('RELEASE_PUBLICATION_REF_DRIFT')
                add('PASS', kind + '_remote_ref', 'EXACT_REMOTE_REF_MATCH')
            except (OSError, ValueError) as exc:
                add('BLOCKED', kind + '_remote_ref', type(exc).__name__ + ':' + str(exc)[:120], 'NETWORK')
        else:
            add('REVIEW', kind + '_remote_ref', 'NETWORK_NOT_PROBED_NO_PUBLICATION_CLAIM', 'NETWORK')

    rows.append(stable_root_check(gate_root, RELEASES['gate']))
    rows.append(stable_root_check(writer_root, RELEASES['writer']))
    try:
        data = read_regular(root / 'Makefile').decode('utf-8')
        old = all(item in data for item in OLD_DEFAULTS)
        add('REVIEW' if old else 'REVIEW', 'make_launch_wiring',
            'LEGACY_TMP_DEFAULTS_PRESENT_MIGRATION_PENDING' if old else
            'MAKEFILE_NO_LONGER_MATCHES_PINNED_OLD_DEFAULTS_MANUAL_REVIEW_REQUIRED',
            'MIGRATION')
    except (OSError, UnicodeError, ValueError) as exc:
        add('BLOCKED', 'make_launch_wiring', type(exc).__name__ + ':' + str(exc)[:120], 'MIGRATION')

    add('REVIEW','independent_operator_rebind',
        'STABLE_RELEASES_REQUIRE_INDEPENDENT_COVERAGE_REATTESTATION_AND_NEW_SIGNED_HEAD; NO_AUTHORITY', 'AUTHORITY')
    add('REVIEW','coverage_evidence_migration',
        'HISTORICAL_SHA_BOUND_EVIDENCE_IMMUTABLE; FUTURE_EXTERNAL_REBIND_REQUIRED', 'AUTHORITY')
    return rows


def summary(rows: list[dict[str,str]]) -> tuple[str, dict[str,int]]:
    counts = {s: sum(row['state'] == s for row in rows)
              for s in ('PASS','BLOCKED','REVIEW','NOT_YET_TESTABLE')}
    # Passing immutable Git objects never amounts to release migration completion.
    state = 'BLOCKED_NON_AUTHORIZING' if counts['BLOCKED'] else 'REVIEW_REQUIRED_NON_AUTHORIZING'
    return state, counts


def save(root: Path, output_dir: Path, report: dict[str,Any]) -> Path:
    base = root / 'generated'
    if base.is_symlink() or not base.is_dir():
        raise ValueError('PROJECT_GENERATED_AREA_NOT_AVAILABLE')
    dest_parent = output_dir if output_dir.is_absolute() else root / output_dir
    # resolve before writing; prevent a report from escaping project-controlled tmp.
    dest_parent = dest_parent.resolve()
    if base.resolve() not in dest_parent.parents:
        raise ValueError('REPORT_PARENT_OUTSIDE_GENERATED_AREA')
    for node in [dest_parent, *dest_parent.parents]:
        if node == root or node == base:
            break
        if node.is_symlink():
            raise ValueError('REPORT_PARENT_SYMLINK')
    dest_parent.mkdir(parents=True, exist_ok=True)
    nonce = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest = dest_parent / ('cf10_gate_writer_release_audit_' + nonce)
    dest.mkdir(mode=0o700)
    txt = '\n'.join([
        'CF10_GATE_WRITER_RELEASE_AUDIT=' + report['status'],
        'AUTHORITY_GRANTED=false','WORKER_LAUNCHED=false','SIGNED_RENEWAL_PERFORMED=false',
        *[f"{r['state']:17} {r['id']:33} {r['detail']}" for r in report['checks']]
    ]) + '\n'
    files = {'summary.txt': txt.encode('utf-8'),
             'report.json': (json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)+'\n').encode()}
    files['SHA256SUMS'] = ''.join(hashlib.sha256(raw).hexdigest()+'  '+name+'\n'
                                 for name,raw in sorted(files.items())).encode('utf-8')
    with ZipFile(dest / 'CF10_Gate_Writer_Release_Audit.zip', 'x', ZIP_DEFLATED) as z:
        for name, raw in sorted(files.items()):
            info = ZipInfo(name,date_time=(2026,1,1,0,0,0));info.compress_type=ZIP_DEFLATED
            info.external_attr=0o600<<16; z.writestr(info,raw)
    os.chmod(dest / 'CF10_Gate_Writer_Release_Audit.zip',0o600)
    return dest / 'CF10_Gate_Writer_Release_Audit.zip'


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--expected-head', required=True)
    p.add_argument('--stable-gate-root',type=Path)
    p.add_argument('--stable-writer-root',type=Path)
    p.add_argument('--no-remote',action='store_true')
    p.add_argument('--output-parent',default='generated/cf10_gate_writer_release_audits',type=Path)
    a = p.parse_args(argv)
    root = a.root.absolute()
    rows = audit(root, a.expected_head, a.stable_gate_root, a.stable_writer_root,
                 probe_remote=not a.no_remote)
    state, counts = summary(rows)
    report = {'schema_version':SCHEMA,'status':state,'expected_head':a.expected_head,
              'counts':counts,'checks':rows,
              'authority':{'granted':False,'worker_launch_performed':False,
                           'signing_performed':False,'ledger_mutation_performed':False,
                           'operator_rebind_performed':False,'git_mutation_performed':False}}
    archive = save(root,a.output_parent,report)
    print('CF10_GATE_WRITER_RELEASE_AUDIT='+state)
    print('CHECKS_PASS='+str(counts['PASS']))
    print('CHECKS_BLOCKED='+str(counts['BLOCKED']))
    print('CHECKS_REVIEW='+str(counts['REVIEW']))
    print('CHECKS_NOT_YET_TESTABLE='+str(counts['NOT_YET_TESTABLE']))
    for row in rows: print(f"{row['state']:17} {row['id']:33} {row['detail']}")
    print('REPORT_ZIP='+str(archive))
    print('REPORT_SHA256='+hashlib.sha256(archive.read_bytes()).hexdigest())
    print('AUTHORITY_GRANTED=false\nWORKER_LAUNCHED=false\nSIGNED_RENEWAL_PERFORMED=false')
    return 2 if counts['BLOCKED'] else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('CF10_GATE_WRITER_RELEASE_AUDIT=BLOCKED:'+type(e).__name__+':'+str(e)[:200],file=sys.stderr)
        sys.exit(2)
