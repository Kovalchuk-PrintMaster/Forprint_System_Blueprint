"""CF-10 G2b-03C: read-only successor Gate design readiness review.

NO runtime Gate verification, source changes, signature reads, promotion, or authority.
Reuses the G2b01/G2b02/G2b03A checks and pins already owned by Blueprint.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

SCHEMA = 'cf10_g2b03c_successor_readiness_v0_1'
EXPECTED_CANDIDATE_STATE = 'PROVENANCE_CANDIDATE_VERIFIED_NON_AUTHORIZING'
EXPECTED_PLAN_STATE = 'SUCCESSOR_GATE_DESIGN_REVIEW_REQUIRED_NON_AUTHORIZING'
NEXT = 'G2B03C02_SUCCESSOR_GATE_IMPLEMENTATION_AND_NEGATIVE_FIXTURES'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')

# Anchors are reviewed invariants of OLD published source, not a proposed new API.
GATE_ANCHORS = (
    'PLAN_MUST_BE_REGULAR_PROJECT_TMP_FILE',
    'expected_parent = (root / "tmp").resolve()',
    'file.parent.resolve() != expected_parent',
    'def verify_coverage(',
    'gate.validate_coverage(doc)',
)
RUNTIME_V1_ANCHORS = (
    'COVERAGE_EVIDENCE_NOT_FROM_GATE_TMP',
    'coverage_path.parent.resolve() != (gate_root / "tmp").resolve()',
)
RUNTIME_V2_ANCHORS = (
    'from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_1 as inventory',
    'SIGNED_RUNTIME_EXTENSION_MISSING',
    'def independent_readback(',
    'def attested_runtime_binding(',
)
WRITER_ANCHORS = (
    'def verify_signed_decision(',
    'def validate_coverage(',
    'coverage_sha256',
    'signed_decision_v0_1.json',
)

class ReadinessBlocked(RuntimeError):
    pass


def anchors(source: str, expected: tuple[str, ...]) -> dict:
    missing = [name for name in expected if name not in source]
    return {'status': 'BLOCKED' if missing else 'PASS', 'missing': missing}


def classify(prior: dict, checks: dict, *, head: str, candidate_path: str, candidate_sha: str) -> dict:
    """Pure and fail-closed: PASS means design prerequisite only, never authority."""
    blockers = []
    if not SHA40.fullmatch(head):
        blockers.append('EXPECTED_HEAD_INVALID')
    if prior.get('state') != EXPECTED_CANDIDATE_STATE or prior.get('blockers') != []:
        blockers.append('G2B03A_PROVENANCE_NOT_PASS')
    if prior.get('g2b02_planning_state') != EXPECTED_PLAN_STATE:
        blockers.append('G2B02_PLAN_NOT_PASS')
    ext = prior.get('external_candidate_check', {})
    hist = prior.get('original_historical_check', {})
    if not isinstance(ext, dict) or ext.get('status') != 'PASS' or ext.get('sha256') != candidate_sha or ext.get('path') != candidate_path:
        blockers.append('EXTERNAL_COVERAGE_PIN_NOT_VERIFIED')
    if not isinstance(hist, dict) or hist.get('status') != 'PASS' or hist.get('sha256') != candidate_sha:
        blockers.append('HISTORICAL_COVERAGE_PIN_NOT_VERIFIED')
    if prior.get('authority_granted') is not False or prior.get('successor_dynamic_coverage_verified') is not False:
        blockers.append('PRIOR_FALSE_AUTHORITY_OR_DYNAMIC_CLAIM')
    for name in ('gate', 'writer', 'runtime_v1', 'runtime_v2', 'quarantine'):
        if checks.get(name, {}).get('status') != 'PASS':
            blockers.append('SOURCE_ANCHOR_NOT_VERIFIED:' + name)
    return {
        'schema_version': SCHEMA,
        'status': 'DESIGN_REVIEW_READY_NON_AUTHORIZING' if not blockers else 'BLOCKED_NON_AUTHORIZING',
        'blockers': sorted(set(blockers)),
        'source_head': head,
        'historical_coverage_sha256': candidate_sha,
        'external_evidence_path': candidate_path,
        'reused_prior': {'g2b03a_state': prior.get('state'), 'g2b02_state': prior.get('g2b02_planning_state')},
        'source_anchor_checks': checks,
        'technical_gap_matrix': {
            'historical_provenance': 'EXACT_BYTES_AND_PINS_VERIFIED' if not blockers else 'REVIEW',
            'legacy_gate_tmp_dependency': 'REQUIRES_SUCCESSOR_GATE',
            'legacy_runtime_v01_dependency': 'REQUIRES_NEW_VERSIONED_BINDING',
            'runtime_v02_delegate_dependency': 'REQUIRES_NEW_VERSIONED_BINDING',
            'current_s01_runtime_inventory': 'NOT_EXECUTED',
            'independent_dynamic_coverage': 'NOT_VERIFIED',
            'independent_signed_operator_approval': 'NOT_VERIFIED',
            'make_launch_quarantine': 'RETAIN',
            'evidence_vault_backup': 'PENDING_EXTERNAL_INTEGRATION',
        },
        'architecture_decision': 'NEW_SEPARATELY_PUBLISHED_SUCCESSOR_GATE_AND_VERSIONED_RUNTIME_BINDING',
        'read_only_design_review': True,
        'pinned_gate_or_writer_executed': False,
        'current_runtime_probed': False,
        'external_signed_payload_read': False,
        'signature_verified': False,
        'dynamic_coverage_verified': False,
        'coverage_rebound': False,
        'writer_gate_unquarantined': False,
        'writer_or_ledger_mutated': False,
        'worker_launched': False,
        'authority_granted': False,
        'next_boundary': NEXT,
    }


def audit(root: Path, head: str) -> dict:
    from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inv
    from scripts.coordination.control_plane import cf10_g2b02_binding_plan_v0_1 as plan
    from scripts.coordination.control_plane import cf10_g2b03_successor_provenance_v0_1 as provenance
    # Existing checks are re-used; their audit function is read-only and non-authorizing.
    canonical, published = inv.canonical_probe(root, head)
    prior = provenance.audit(root, head, root / inv.HISTORICAL_COVERAGE_REL)
    checks = {}
    checks['quarantine'] = {'status': 'PASS' if canonical.get('status') == 'PASS' and
        any(x.get('id') == 'make_launch_boundary' and x.get('status') == 'PASS'
            for x in inv.make_boundary_probe(published)) else 'BLOCKED'}
    for kind, keys in (('gate', GATE_ANCHORS), ('writer', WRITER_ANCHORS)):
        try:
            source = plan.verified_git_blob(root, kind)
            checks[kind] = anchors(source, keys)
        except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
            checks[kind] = {'status': 'BLOCKED', 'reason': type(exc).__name__ + ':' + str(exc)[:100]}
    for name, rel, keys in (
        ('runtime_v1', plan.RUNTIME_V1, RUNTIME_V1_ANCHORS),
        ('runtime_v2', plan.RUNTIME_V2, RUNTIME_V2_ANCHORS)):
        try:
            source = inv.exact_published_file(root, head, rel)
            checks[name] = anchors(source, keys)
        except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
            checks[name] = {'status': 'BLOCKED', 'reason': type(exc).__name__ + ':' + str(exc)[:100]}
    return classify(prior, checks, head=head, candidate_path=str(inv.STABLE_COVERAGE),
                    candidate_sha=inv.EXPECTED_COVERAGE_SHA256)


def write_report(root: Path, result: dict) -> tuple[Path, str]:
    scratch = root / 'tmp'
    if scratch.is_symlink() or not scratch.is_dir() or any(p.is_symlink() for p in (scratch, *scratch.parents)):
        raise ReadinessBlocked('PROJECT_TMP_UNSAFE')
    folder = scratch / ('cf10_g2b03c_design_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(mode=0o700)
    report = (json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + '\n').encode()
    summary = ('CF10_G2B03C_STATUS=' + result['status'] + '\n' +
               ''.join('BLOCKER=' + x + '\n' for x in result['blockers']) +
               'DYNAMIC_COVERAGE_VERIFIED=false\nAUTHORITY_GRANTED=false\nWORKER_LAUNCHED=false\n' +
               'NEXT_BOUNDARY=' + NEXT + '\n').encode()
    contents = {'report.json': report, 'summary.txt': summary}
    contents['SHA256SUMS'] = ''.join(hashlib.sha256(blob).hexdigest() + '  ' + name + '\n'
                                   for name, blob in sorted(contents.items())).encode()
    for name, blob in sorted(contents.items()):
        fd = os.open(folder / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
    return folder, hashlib.sha256(report).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--no-report', action='store_true')
    args = parser.parse_args(argv)
    try:
        root = args.root.absolute()
        if not SHA40.fullmatch(args.expected_head):
            raise ReadinessBlocked('EXPECTED_HEAD_INVALID')
        result = audit(root, args.expected_head)
        print('CF10_G2B03C_STATUS=' + result['status'])
        for key, item in result['source_anchor_checks'].items():
            print('SOURCE_' + key.upper() + '=' + item['status'])
        for blocker in result['blockers']:
            print('BLOCKER=' + blocker)
        if not args.no_report:
            target, digest = write_report(root, result)
            print('REPORT_DIR=' + str(target))
            print('REPORT_SHA256=' + digest)
        print('DYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        return 2 if result['blockers'] else 0
    except (ReadinessBlocked, OSError, ValueError) as exc:
        print('CF10_G2B03C_STATUS=BLOCKED_NON_AUTHORIZING', file=sys.stderr)
        print('BLOCKER=' + type(exc).__name__ + ':' + str(exc)[:180], file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
