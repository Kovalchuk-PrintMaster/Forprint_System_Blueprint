"""CF10 G2b-03C/04A: metadata-only attestation boundary inventory.

Reuses v0.3's observed, unsigned runtime binding review; external trust files
are lstat'ed but NEVER opened or parsed. No Ed25519 verification, dynamic writer
enrollment proof, deployment change, quarantine removal or Worker execution.
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
import sys

SCHEMA = 'cf10_g2b03c04a_attestation_boundary_v0_1'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
SHA64 = re.compile(r'[0-9a-f]{64}\Z')
SELF_REL = 'scripts/coordination/control_plane/cf10_g2b03c04a_attestation_boundary_v0_1.py'
EXPECTED_B3_SHA = '74d069eae81fea583375fede6d320b3ba23fbc337b73b03b788236a2e3dc3a3b'
EXPECTED_B3 = 'tmp/cf10_g2b03c03b_review_20261028T135332890726Z/report.json'
DEPLOYMENT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
TRUST_ROOT = Path('/etc/forprint/execution_attempt_writer_activation')
TRUST_FILES = (
    'trust_root_v0_1.json',
    'writer_coverage_v0_1.json',
    'signed_decision_v0_1.json',
    'protocol_candidate_v0_1.yaml',
)
NEXT = 'G2B03C04B_INDEPENDENT_DYNAMIC_COVERAGE_ATTESTATION_PROOF_CONTRACT'
GAPS = (
    'CURRENT_WRITER_ENTRYPOINT_COMPLETENESS_NOT_PROVEN',
    'ALL_WRITER_PROCESSES_ENROLLED_NOT_PROVEN',
    'RUNNING_WRITER_DRAIN_OR_RESTART_NOT_PROVEN',
    'CURRENT_DYNAMIC_COVERAGE_INDEPENDENTLY_VERIFIED_FALSE',
    'SUCCESSOR_GATE_INDEPENDENT_PUBLISHED_RELEASE_NOT_ACCEPTED',
    'SIGNED_OPERATOR_DECISION_CURRENT_HEAD_SOURCE_HASH_EXPIRY_NOT_VERIFIED',
    'VERSIONED_RUNTIME_BINDING_NOT_INDEPENDENTLY_ATTESTED',
    'MAKE_LAUNCH_QUARANTINE_STILL_ACTIVE',
)

class BoundaryBlocked(RuntimeError):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def path_metadata(path: Path, *, expect_directory: bool = False) -> dict:
    """Only stat metadata, never read external authority bytes; no symlink fallback.

    Missing components are distinguished from unsafe components. Walk all
    ancestors to prevent symlinked /etc or group-writable trust roots.
    """
    if not path.is_absolute() or '..' in path.parts:
        return {'status': 'UNSAFE', 'reason': 'PATH_NOT_CANONICAL_ABSOLUTE'}
    chain = [path, *path.parents]
    for pos, node in enumerate(reversed(chain)):
        try:
            s = node.lstat()
        except FileNotFoundError:
            return {'status': 'MISSING', 'reason': 'PATH_COMPONENT_MISSING'}
        except OSError:
            return {'status': 'UNSAFE', 'reason': 'PATH_COMPONENT_UNREADABLE'}
        is_final = pos == len(chain) - 1
        if stat.S_ISLNK(s.st_mode):
            return {'status': 'UNSAFE', 'reason': 'SYMLINK_COMPONENT'}
        if (not is_final or expect_directory) and not stat.S_ISDIR(s.st_mode):
            return {'status': 'UNSAFE', 'reason': 'DIRECTORY_COMPONENT_INVALID'}
        if is_final and not expect_directory and not stat.S_ISREG(s.st_mode):
            return {'status': 'UNSAFE', 'reason': 'EXTERNAL_FILE_NOT_REGULAR'}
        if s.st_uid != 0 or s.st_mode & 0o022:
            return {'status': 'UNSAFE', 'reason': 'NON_ROOT_OR_BROAD_WRITE'}
        if is_final and not expect_directory:
            if s.st_size <= 0 or s.st_size > 1_048_576 or s.st_nlink != 1:
                return {'status': 'UNSAFE', 'reason': 'FILE_SIZE_OR_LINK_COUNT_UNSAFE'}
            return {'status': 'METADATA_PRESENT_NON_ATTESTING',
                    'mode': format(stat.S_IMODE(s.st_mode), '04o'), 'size_bytes': s.st_size}
    return {'status': 'METADATA_PRESENT_NON_ATTESTING',
            'mode': format(stat.S_IMODE(s.st_mode), '04o')}


def authority_metadata(root: Path = TRUST_ROOT) -> dict:
    directory = path_metadata(root, expect_directory=True)
    files = {}
    # Do not traverse children if a parent path is missing or unsafe.
    if directory['status'] == 'METADATA_PRESENT_NON_ATTESTING':
        for name in TRUST_FILES:
            files[name] = path_metadata(root / name)
    else:
        files = {name: {'status': 'NOT_INSPECTED_PARENT_' + directory['status']} for name in TRUST_FILES}
    return {'directory': directory, 'files': files, 'external_file_content_read': False,
            'signature_verified': False, 'coverage_attested': False}


def classify(*, prior: dict, head: str, metadata: dict, source_published: bool) -> dict:
    blockers = []
    if not SHA40.fullmatch(head) or prior.get('source_head') != head:
        blockers.append('CANONICAL_HEAD_OR_BINDING_DRIFT')
    if (prior.get('status') != 'VERSIONED_BINDING_CANDIDATE_REVIEW_REQUIRED_NON_AUTHORIZING'
            or prior.get('blockers') != [] or prior.get('mode') != 'inspect'
            or prior.get('b3_regression_passed_count') != 62
            or prior.get('launch_allowed') is not False
            or prior.get('independent_dynamic_coverage_verified') is not False
            or prior.get('runtime_binding_authorized') is not False
            or prior.get('authority_granted') is not False):
        blockers.append('VERSIONED_BINDING_CANDIDATE_NOT_VERIFIED')
    if source_published is not True:
        blockers.append('SELF_SOURCE_NOT_PUBLISHED')
    if not isinstance(metadata, dict) or not isinstance(metadata.get('files'),dict):
        blockers.append('AUTHORITY_METADATA_UNAVAILABLE')
        metadata = {'directory': {'status': 'UNSAFE'}, 'files': {}}
    items = [metadata.get('directory', {})] + list(metadata.get('files', {}).values())
    if any(not isinstance(x, dict) or x.get('status') == 'UNSAFE' for x in items):
        blockers.append('EXTERNAL_AUTHORITY_PATH_UNSAFE')
    if set(metadata.get('files',{})) != set(TRUST_FILES):
        blockers.append('EXTERNAL_TRUST_FILE_INVENTORY_INCOMPLETE')
    if metadata.get('external_file_content_read') is not False or metadata.get('signature_verified') is not False or metadata.get('coverage_attested') is not False:
        blockers.append('FALSE_EXTERNAL_ATTESTATION_CLAIM')
    result_state = 'BLOCKED_NON_AUTHORIZING' if blockers else 'ATTESTATION_BOUNDARY_GAPS_RECORDED_NON_AUTHORIZING'
    return {
        'schema_version': SCHEMA, 'status': result_state, 'blockers': sorted(set(blockers)),
        'canonical_head': head, 'predecessor_binding_status': prior.get('status'),
        'external_authority_metadata_only': metadata,
        'required_evidence_gaps': list(GAPS),
        'next_boundary': NEXT,
        'historical_coverage_is_not_dynamic_proof': True,
        'b3_synthetic_tests_are_not_production_proof': True,
        'external_signature_payload_read': False,
        'signature_cryptographically_verified': False,
        'independent_dynamic_coverage_verified': False,
        'writer_enrollment_verified': False,
        'worker_drain_or_restart_verified': False,
        'current_signed_head_approved': False,
        'successor_gate_release_accepted': False,
        'make_quarantine_removed': False,
        'launch_allowed': False,
        'ledger_mutated': False,
        'worker_launched': False,
        'authority_granted': False,
    }


def report_locator_allowed(root: Path, report: Path, expected_sha: str) -> bool:
    """Admit historical exact report OR current project-native B3 envelope.

    The successor binding *separately* verifies exact bytes, manifest, source
    set, current HEAD and S01 lock. A pathname is never proof of authority.
    """
    old = (report == root / EXPECTED_B3 and expected_sha == EXPECTED_B3_SHA)
    current = (report != root / EXPECTED_B3
               and report.parent.parent == root / 'tmp'
               and re.fullmatch(r'cf10_g2b03c03b_review_[0-9]{8}T[0-9]{6,12}Z', report.parent.name) is not None
               and report.name == 'report.json'
               and SHA64.fullmatch(expected_sha) is not None)
    return old or current


def review(root: Path, expected_head: str, *, b3_report: Path, b3_sha256: str) -> dict:
    from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inventory
    from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_3 as binding
    if root != DEPLOYMENT or root.is_symlink():
        raise BoundaryBlocked('CANONICAL_DEPLOYMENT_ROOT_NOT_PINNED')
    if not SHA40.fullmatch(expected_head):
        raise BoundaryBlocked('EXPECTED_HEAD_INVALID')
    if not report_locator_allowed(root, b3_report, b3_sha256):
        raise BoundaryBlocked('PROJECT_NATIVE_B3_REPORT_LOCATOR_NOT_ACCEPTED')
    # Source code is exact published content; no newly introduced source shadowing.
    inventory.exact_published_file(root, expected_head, SELF_REL)
    prior = binding.review(root, expected_head, report=b3_report,
                           report_sha=b3_sha256, mode='inspect')
    metadata = authority_metadata()
    inventory.exact_published_file(root, expected_head, SELF_REL)
    return classify(prior=prior, head=expected_head, metadata=metadata, source_published=True)


def save_report(root: Path, doc: dict) -> tuple[Path,str]:
    scratch = root / 'tmp'
    if not scratch.is_dir() or any(p.is_symlink() for p in (scratch,*scratch.parents)):
        raise BoundaryBlocked('PROJECT_SCRATCH_UNSAFE')
    folder = scratch / ('cf10_g2b03c04a_boundary_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(mode=0o700)
    report = (json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')
    summary = ('CF10_G2B03C04A_STATUS=' + doc['status'] + '\n'
               + ''.join('BLOCKER='+x+'\n' for x in doc['blockers'])
               + ''.join('GAP='+x+'\n' for x in doc['required_evidence_gaps'])
               + 'DYNAMIC_COVERAGE_VERIFIED=false\nAUTHORITY_GRANTED=false\n'
               + 'WORKER_LAUNCHED=false\n').encode('utf-8')
    contents = {'report.json': report, 'summary.txt': summary}
    contents['SHA256SUMS'] = ''.join(digest(raw) + '  ' + name + '\n' for name,raw in sorted(contents.items())).encode()
    for name, raw in sorted(contents.items()):
        fd = os.open(folder / name, os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return folder, digest(report)


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--expected-head',required=True)
    p.add_argument('--b3-report',required=True,type=Path)
    p.add_argument('--b3-sha256',required=True)
    args=p.parse_args(argv)
    try:
        root=args.root.absolute()
        result=review(root,args.expected_head,b3_report=args.b3_report,b3_sha256=args.b3_sha256)
        out, report_sha=save_report(root,result)
        print('CF10_G2B03C04A_STATUS='+result['status'])
        print('EXTERNAL_TRUST_DIR='+result['external_authority_metadata_only']['directory']['status'])
        for name,row in result['external_authority_metadata_only']['files'].items():
            print('EXTERNAL_METADATA_'+name.upper().replace('.','_')+'='+row['status'])
        for blocker in result['blockers']:
            print('BLOCKER='+blocker)
        print('REPORT_DIR='+str(out))
        print('REPORT_SHA256='+report_sha)
        print('DYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\n'
              'WORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        return 2 if result['blockers'] else 0
    except (BoundaryBlocked,OSError,ValueError,RuntimeError) as exc:
        print('CF10_G2B03C04A_STATUS=BLOCKED_NON_AUTHORIZING',file=sys.stderr)
        print('BLOCKER='+type(exc).__name__+':'+str(exc)[:180],file=sys.stderr)
        print('AUTHORITY_GRANTED=false',file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
