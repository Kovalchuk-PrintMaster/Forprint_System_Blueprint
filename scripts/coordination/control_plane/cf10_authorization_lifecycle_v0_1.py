"""CF-10 authorization lifecycle: one diagnostic/request/resume entrypoint.

Never signs, provisions trust roots, extends validity, updates Git/ledger/Make,
or launches workers. A signed approval must come from independent authorities.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SCHEMA = 'cf10_authorization_lifecycle_v0_1'
MAX_SECONDS = {'writer_activation': 86400, 'worker_release': 28800}
ROOT_REQUEST = Path('tmp/cf10_authorization_requests')
MAKE_QUARANTINE_MARKER = 'CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(data: dict) -> bytes:
    return (json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def _git_head(root: Path) -> str:
    p = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
    value = p.stdout.decode('ascii').strip()
    if not SHA40.fullmatch(value):
        raise ValueError('git head format')
    return value


def _dt(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError('datetime not a string')
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('timezone required')
    return d.astimezone(timezone.utc)


def classify_window(kind: str, doc: dict | None, *, head: str,
                    now: datetime) -> dict:
    """Independent clock diagnostics, explicitly NOT signature verification."""
    result = {'kind': kind, 'state': 'UNAVAILABLE', 'head_binding': 'UNKNOWN',
              'expiry_utc': None, 'time_remaining_seconds': None,
              'cryptographic_signature_checked_here': False,
              'renewal_not_authority': True}
    if doc is None:
        return result
    if not isinstance(doc, dict):
        return {**result, 'state': 'MALFORMED'}
    commit = doc.get('publication_commit')
    result['head_binding'] = 'MATCH' if commit == head else 'MISMATCH'
    try:
        issued, expires = _dt(doc.get('issued_at')), _dt(doc.get('expires_at'))
        result['expiry_utc'] = expires.isoformat().replace('+00:00', 'Z')
        result['time_remaining_seconds'] = int((expires - now).total_seconds())
        elapsed = (expires - issued).total_seconds()
        if elapsed <= 0 or elapsed > MAX_SECONDS[kind]:
            result['state'] = 'INVALID_WINDOW'
        elif issued > now:
            result['state'] = 'NOT_YET_VALID'
        elif expires <= now:
            result['state'] = 'EXPIRED'
        else:
            result['state'] = 'WITHIN_WINDOW_NOT_AUTHORIZED'
    except (ValueError, TypeError, OverflowError, KeyError):
        result['state'] = 'INVALID_WINDOW'
    return result


def decide(activation: dict, release: dict, *, gate: dict,
           release_gate: dict, make_quarantined: bool) -> dict:
    """Explicit, bounded next-action classifier. Never authorizes launch."""
    a, r = activation['state'], release['state']
    mismatched = any(x['head_binding'] == 'MISMATCH' for x in (activation, release))
    if mismatched:
        code = 'SOURCE_REVIEW_AND_NEW_SIGNED_DECISIONS_REQUIRED'
        action = 'Source publication HEAD changed: review proof freshness and request new bound signatures, not just a new expiry.'
    elif a in ('EXPIRED', 'NOT_YET_VALID', 'INVALID_WINDOW', 'UNAVAILABLE', 'MALFORMED'):
        code = 'WRITER_ACTIVATION_RENEWAL_REVIEW_REQUIRED'
        action = 'Independent operator: verify unchanged source, coverage, protocol and provenance; issue a fresh signed activation decision if justified.'
    elif r in ('EXPIRED', 'NOT_YET_VALID', 'INVALID_WINDOW', 'UNAVAILABLE', 'MALFORMED'):
        code = 'WORKER_RELEASE_RENEWAL_REVIEW_REQUIRED'
        action = 'Independent release reviewer: verify exact worker/task/attempt, proofs and current HEAD; issue a new bounded signed release receipt.'
    elif gate.get('status') != 'PASS' or release_gate.get('candidate_preconditions_pass') is not True:
        code = 'CANONICAL_GATES_BLOCKED_REVIEW_REQUIRED'
        action = 'Read canonical gate blockers; signed artifacts are never approved by this wrapper.'
    elif make_quarantined:
        code = 'INDEPENDENT_MAKE_REBIND_REQUIRED'
        action = 'Do not override Make quarantine. Independently approve and implement a reviewed guarded release binding.'
    else:
        code = 'EXPLICIT_RELEASE_REVIEW_REQUIRED'
        action = 'Signed preconditions appear ready; independently verify governed Make wiring and Task/Attempt authority. This tool never authorizes launch.'
    return {'state': code, 'operator_next_action': action,
            'worker_launch_allowed_by_this_tool': False,
            'authority_granted_by_this_tool': False,
            'auto_signature_or_expiry_extension_performed': False}


def _gate_view(data: dict | None) -> dict:
    if not isinstance(data, dict):
        return {'status': 'UNAVAILABLE', 'blockers': ['EVALUATOR_UNAVAILABLE']}
    return {'status': data.get('status', 'UNKNOWN'),
            'candidate_preconditions_pass': data.get('candidate_preconditions_pass') is True,
            'blockers': [str(x)[:200] for x in data.get('blockers', []) if isinstance(x, str)][:30],
            'checks': {k: v for k, v in data.get('checks', {}).items()
                       if isinstance(k, str) and isinstance(v, (str, int, bool))}}


def _canonical(root: Path) -> tuple[dict, dict, dict | None, dict | None]:
    """Use existing root-controlled canonical readers, never export decisions."""
    from scripts.coordination import execution_attempt_writer_activation_v0_1 as activation
    from scripts.coordination.control_plane import cf10_s01_release_gate_candidate_v0_1 as release
    a_doc = r_doc = None
    try:
        a_doc, _ = activation.trusted_json(activation.DECISION_FILE)
    except Exception:
        pass
    try:
        r_doc, _ = activation.trusted_json(release.RELEASE_DECISION)
    except Exception:
        pass
    try:
        ga = _gate_view(activation.evaluate(root, stage='verify'))
    except Exception:
        ga = {'status': 'UNAVAILABLE', 'blockers': ['CANONICAL_ACTIVATION_EVALUATOR_UNAVAILABLE']}
    try:
        gr = _gate_view(release.evaluate(root, mode='inspect'))
    except Exception:
        gr = {'status': 'UNAVAILABLE', 'blockers': ['CANONICAL_RELEASE_EVALUATOR_UNAVAILABLE']}
    return ga, gr, a_doc, r_doc


def _make_quarantine(root: Path) -> bool:
    path = root / 'Makefile'
    if not path.is_file() or path.is_symlink():
        return True
    # A missing marker is not evidence that all launch paths are guarded.
    text = path.read_text('utf-8')
    return ('cf10-s01-runtime-launch-preflight:' not in text
            or MAKE_QUARANTINE_MARKER in text)


def build(root: Path, *, now: datetime | None = None,
          reader=None, gate_reader=None) -> dict:
    now = now or datetime.now(timezone.utc)
    head = _git_head(root)
    if reader is None or gate_reader is None:
        ga, gr, a_doc, r_doc = _canonical(root)
    else:
        a_doc, r_doc = reader()
        ga, gr = gate_reader()
    activation = classify_window('writer_activation', a_doc, head=head, now=now)
    release = classify_window('worker_release', r_doc, head=head, now=now)
    quarantined = _make_quarantine(root)
    choice = decide(activation, release, gate=ga, release_gate=gr, make_quarantined=quarantined)
    if _git_head(root) != head:
        choice = {'state': 'SOURCE_CHANGED_DURING_DIAGNOSTIC',
                  'operator_next_action': 'Re-run after freezing a stable HEAD.',
                  'worker_launch_allowed_by_this_tool': False,
                  'authority_granted_by_this_tool': False,
                  'auto_signature_or_expiry_extension_performed': False}
    return {'schema_version': SCHEMA, 'time_checked_utc': now.isoformat(),
            'source_head': head, 'writer_activation_window': activation,
            'worker_release_window': release, 'canonical_activation_gate': ga,
            'canonical_release_gate': gr, 'make_quarantine_observed': quarantined,
            'next_step': choice, 'historical_proofs_automatically_reaccepted': False,
            'signed_artifacts_exported': False, 'worker_launched': False,
            'git_mutated': False, 'ledger_mutated': False}


def _store(root: Path, report: dict) -> Path:
    """Idempotent, bounded private request snapshot; NO authoritative material."""
    basis = {'source_head': report['source_head'],
             'writer_activation_window': report['writer_activation_window'].copy(),
             'worker_release_window': report['worker_release_window'].copy(),
             'state': report['next_step']['state']}
    # A source/head/window change gets a new key. Time of inspection does not.
    for window in (basis['writer_activation_window'], basis['worker_release_window']):
        window.pop('time_remaining_seconds', None)
    key = _sha(_json(basis))[:24]
    parent = root / ROOT_REQUEST
    if (root / 'tmp').is_symlink() or parent.is_symlink():
        raise ValueError('unsafe request parent')
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    folder = parent / ('request_' + key)
    if folder.is_symlink():
        raise ValueError('unsafe request directory')
    folder.mkdir(mode=0o700, exist_ok=True)
    request = {'schema_version': 'cf10_authorization_operator_request_v0_1',
               'request_digest': key, 'source_head': report['source_head'],
               'issue_classification': report['next_step']['state'],
               'next_action': report['next_step']['operator_next_action'],
               'windows': [basis['writer_activation_window'], basis['worker_release_window']],
               'independent_operator_review_required': True,
               'review_must_confirm': [
                   'Fresh source/protocol/coverage binding and independent proof provenance',
                   'Correct Ed25519 signer, purpose, nonce and clock limits',
                   'Current publication head and exact worker/task/attempt release scope',
                   'Separate positive runtime binding and governed Make release acceptance'],
               'request_is_not_a_signed_decision': True,
               'permission_or_launch_granted': False}
    msg = ('CF10 renewal request (NOT AUTHORITY)\n'
           + 'Issue: ' + request['issue_classification'] + '\n'
           + 'Source: ' + request['source_head'] + '\n'
           + 'Operator next: ' + request['next_action'] + '\n'
           + 'After independently installing approved signed artifacts, rerun: '
           + 'make -f Makefile -f coordination/continuity/cf10_authorization_lifecycle_v0_1.mk cf10-auth-resume-check\n')
    files = {'request.json': _json(request), 'OPERATOR_NEXT.txt': msg.encode('utf-8')}
    sums = ''.join(_sha(v) + '  ' + k + '\n' for k, v in files.items()).encode('ascii')
    files['SHA256SUMS'] = sums
    for name, body in files.items():
        target = folder / name
        if target.is_symlink():
            raise ValueError('unsafe request artifact')
        if target.exists():
            if not target.is_file() or target.read_bytes() != body:
                raise ValueError('existing request artifact differs')
        else:
            fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, 'O_NOFOLLOW', 0), 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(body)
    return folder


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['run', 'status', 'request', 'resume-check'])
    p.add_argument('--root', type=Path, default=Path('.'))
    args = p.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        report = build(root)
        if args.mode in ('run', 'request') and report['next_step']['state'] != 'EXPLICIT_RELEASE_REVIEW_REQUIRED':
            report['request_directory'] = str(_store(root, report))
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        print('CF10_AUTH_STATUS=' + report['next_step']['state'])
        print('WORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false\nMAKE_QUARANTINE_RETAINED=' + str(report['make_quarantine_observed']).lower())
        return 0 if args.mode in ('status','run','request') else 2
    except Exception as exc:
        print('CF10_AUTH_STATUS=BLOCKED_DIAGNOSTIC_ERROR:' + type(exc).__name__, file=sys.stderr)
        print('WORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
