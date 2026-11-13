"""CF10 G2b-03C/02: separate non-authorizing successor Gate candidate.

Read-only live s01 observation using existing runtime inventory primitives, bounded
external coverage provenance, canonical source & dual pinned release checks.
Do NOT treat this as independent dynamic coverage attestation or permission to
execute: old signed activation/runtime v2 gates remain separate and quarantined.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import sys

SCHEMA = 'cf10_g2b03c02_successor_gate_candidate_v0_1'
SHA40 = re.compile(r'[0-9a-f]{40}\Z')
NEXT = 'G2B03C03_VERSIONED_RUNTIME_BINDING_AND_INDEPENDENT_ATTESTATION_DESIGN'

class GateBlocked(RuntimeError):
    pass


def directory_safety(status: dict, label: str) -> list[str]:
    """Never accept unknown, symlinked, non-root or writable-by-others paths."""
    if (status.get('state') != 'DIRECTORY' or status.get('uid') != 0 or
            status.get('group_writable') is not False or status.get('other_writable') is not False):
        return [label + '_DAC_UNSAFE_OR_NOT_OBSERVED']
    return []


def classify(*, source: dict, provenance: dict, live: dict, expected_head: str) -> dict:
    """Pure fail-closed result classifier for synthetic negative fixtures."""
    blockers: list[str] = []
    findings: list[str] = []
    if not SHA40.fullmatch(expected_head):
        blockers.append('EXPECTED_HEAD_INVALID')
    if (source.get('status') != 'DESIGN_REVIEW_READY_NON_AUTHORIZING' or
            source.get('blockers') != [] or source.get('source_head') != expected_head):
        blockers.append('SOURCE_READINESS_NOT_VERIFIED_FOR_HEAD')
    if (provenance.get('state') != 'PROVENANCE_CANDIDATE_VERIFIED_NON_AUTHORIZING' or
            provenance.get('blockers') != [] or provenance.get('authority_granted') is not False or
            provenance.get('successor_dynamic_coverage_verified') is not False):
        blockers.append('EXTERNAL_PROVENANCE_NOT_VERIFIED')
    candidate = provenance.get('external_candidate_check')
    if (not isinstance(candidate, dict) or candidate.get('status') != 'PASS' or
            candidate.get('path') != source.get('external_evidence_path') or
            candidate.get('sha256') != source.get('historical_coverage_sha256')):
        blockers.append('CANDIDATE_BYTES_PATH_OR_PINS_DRIFT')
    if live.get('host') != 's01' or live.get('deployment_root') != '/srv/software_development/forprint-project/forprint_system_blueprint':
        blockers.append('S01_DEPLOYMENT_IDENTITY_UNVERIFIED')
    if live.get('deployment_head') != expected_head:
        blockers.append('RUNTIME_DEPLOYMENT_HEAD_DRIFT')
    for key in ('canonical_ledger', 'canonical_parent', 'coordination_ancestor', 'continuity_ancestor'):
        blockers.extend(directory_safety(live.get(key, {}), key.upper()))
    mount = live.get('mount', {})
    if (mount.get('state') != 'OBSERVED' or mount.get('network_or_fuse_surface') is not False):
        blockers.append('LEDGER_MOUNT_UNSAFE_OR_UNKNOWN')
    processes = live.get('processes', {})
    if (processes.get('state') != 'OBSERVED' or processes.get('unreadable_count') != 0 or
            not isinstance(processes.get('observed'), list)):
        blockers.append('PROCESS_OBSERVATION_UNRELIABLE')
    # Preserve uncertainty: /proc scan cannot prove every indirect writer, no-process state
    # is not proof of absence, and a current scan does not attest restarts/drains.
    if processes.get('absence_of_processes_proven') is not False:
        blockers.append('PROCESS_PROOF_SEMANTICS_DRIFT')
    for kind in ('gate','writer'):
        if live.get('release_checks', {}).get(kind) != 'PASS':
            blockers.append('PINNED_RELEASE_NOT_VERIFIED:' + kind)
    compared = live.get('writer_source_comparison', {})
    if not isinstance(compared, dict) or set(compared) != set(live.get('tracked_writers', ())):
        blockers.append('TRACKED_WRITER_INVENTORY_INCOMPLETE')
    else:
        for rel, equal in compared.items():
            if equal is None:
                blockers.append('WRITER_SOURCE_UNREADABLE:' + rel)
            elif equal is False:
                findings.append('DEPLOYMENT_WRITER_DIFF_REQUIRES_REVIEW:' + rel)
    for key in ('signed_decision', 'writer_enrollment', 'independent_operator_review', 'runtime_binding'):
        if live.get('independent_authority', {}).get(key) != 'NOT_VERIFIED':
            blockers.append('AUTHORITY_SEMANTICS_DRIFT:' + key)
    if live.get('acl', {}).get('state') != 'OBSERVED':
        findings.append('LEDGER_ACL_NOT_INDEPENDENTLY_VERIFIED')
    # No branch can claim positive dynamic attestation. Only a safely observed state.
    state = 'BLOCKED_NON_AUTHORIZING' if blockers else 'LIVE_OBSERVATION_REVIEW_REQUIRED_NON_AUTHORIZING'
    return {
        'schema_version': SCHEMA,
        'status': state, 'blockers': sorted(set(blockers)), 'review_findings': sorted(set(findings)),
        'source_head': expected_head,
        'external_coverage_path': source.get('external_evidence_path'),
        'external_coverage_sha256': source.get('historical_coverage_sha256'),
        'observed_s01_runtime': live,
        'provenance_state': provenance.get('state'),
        'source_design_state': source.get('status'),
        'successor_gate_candidate_implemented': True,
        'live_runtime_observed': not blockers,
        'deployment_coverage_verified': False,
        'dynamic_coverage_verified': False,
        'independent_gate_accepted': False,
        'signed_operator_approval_verified': False,
        'signed_renewal_performed': False,
        'evidence_binding_changed': False,
        'make_launch_gate_unquarantined': False,
        'ledger_mutated': False,
        'worker_launched': False,
        'authority_granted': False,
        'backup_state': 'PENDING_EXTERNAL_INTEGRATION',
        'next_boundary': NEXT,
    }


def safely_compare_sources(runtime, stable, deployed: Path, writer: Path) -> dict[str, bool | None]:
    """Reuse published runtime's status/digest; compare only bounded known paths."""
    result: dict[str, bool | None] = {}
    for rel in runtime.TRACKED_WRITERS:
        a, b = deployed / rel, writer / rel
        sa, sb = runtime.path_status(a), runtime.path_status(b)
        if sa.get('state') != 'REGULAR_FILE' or sb.get('state') != 'REGULAR_FILE':
            result[rel] = None
            continue
        try:
            # Reuse G2a's nofollow source reader, not unguarded Path.read_bytes.
            source_a, source_b = stable.safe_file(a), stable.safe_file(b)
            if len(source_a) > 2_000_000 or len(source_b) > 2_000_000:
                raise GateBlocked('TRACKED_SOURCE_OVERSIZE:' + rel)
            result[rel] = runtime.digest(source_a) == runtime.digest(source_b)
        except (OSError, ValueError, GateBlocked, stable.ReviewBlocked):
            result[rel] = None
    return result


def observe_s01(*, root: Path, expected_head: str) -> dict:
    """Observe live s01 using existing v0.1 sensors, never its gate_root/tmp binding."""
    from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_1 as runtime
    from scripts.coordination.control_plane import cf10_stable_release_roots_v0_1 as stable
    if root != runtime.DEPLOYMENT_PATH or root.is_symlink():
        raise GateBlocked('DEPLOYMENT_ROOT_NOT_APPROVED')
    if socket.gethostname().split('.')[0] != 's01':
        raise GateBlocked('WRONG_HOST')
    if runtime.git(root, 'rev-parse', 'HEAD') != expected_head:
        raise GateBlocked('DEPLOYMENT_HEAD_CHANGED')
    releases: dict[str,str] = {}
    for kind in ('gate','writer'):
        observed = stable.inspect_release(stable.stable_path(kind),kind)
        releases[kind] = observed.get('status','BLOCKED')
    writer = stable.stable_path('writer')
    canonical = root / runtime.CANONICAL_REL
    live = {
        'host': socket.gethostname().split('.')[0],
        'deployment_root': str(root),
        'deployment_head': runtime.git(root, 'rev-parse', 'HEAD'),
        'canonical_ledger': runtime.path_status(canonical),
        'canonical_parent': runtime.path_status(canonical.parent),
        'coordination_ancestor': runtime.path_status(root / 'coordination'),
        'continuity_ancestor': runtime.path_status(root / 'coordination/continuity'),
        'mount': runtime.mount_status(canonical),
        'acl': runtime.acl_status(canonical),
        'processes': runtime.scan_proc(),
        'tracked_writers': list(runtime.TRACKED_WRITERS),
        'writer_source_comparison': safely_compare_sources(runtime,stable,root,writer),
        'release_checks': releases,
        'independent_authority': {
            'signed_decision':'NOT_VERIFIED', 'writer_enrollment':'NOT_VERIFIED',
            'independent_operator_review':'NOT_VERIFIED', 'runtime_binding':'NOT_VERIFIED',
        },
    }
    if runtime.git(root, 'rev-parse','HEAD') != expected_head:
        raise GateBlocked('DEPLOYMENT_HEAD_CHANGED_DURING_SCAN')
    return live


def audit(root: Path, head: str) -> dict:
    from scripts.coordination.control_plane import cf10_g2b03c_successor_readiness_v0_1 as readiness
    from scripts.coordination.control_plane import cf10_g2b03_successor_provenance_v0_1 as provenance
    from scripts.coordination.control_plane import cf10_g2b01_inventory_v0_1 as inv
    source_rel = 'scripts/coordination/control_plane/cf10_g2b03c02_successor_gate_v0_1.py'
    if not SHA40.fullmatch(head):
        raise GateBlocked('EXPECTED_HEAD_INVALID')
    source = readiness.audit(root, head)
    if source.get('status') != 'DESIGN_REVIEW_READY_NON_AUTHORIZING':
        raise GateBlocked('SOURCE_READINESS_BLOCKED')
    # The very Gate candidate being executed must match the current published tree.
    inv.exact_published_file(root, head, source_rel)
    prior = provenance.audit(root, head, root / inv.HISTORICAL_COVERAGE_REL)
    if prior.get('state') != 'PROVENANCE_CANDIDATE_VERIFIED_NON_AUTHORIZING':
        raise GateBlocked('PROVENANCE_NOT_VERIFIED')
    live = observe_s01(root=root,expected_head=head)
    inv.exact_published_file(root, head, source_rel)
    return classify(source=source,provenance=prior,live=live,expected_head=head)


def save_report(root: Path, doc: dict) -> tuple[Path,str]:
    scratch = root/'tmp'
    if not scratch.is_dir() or any(p.is_symlink() for p in (scratch,*scratch.parents)):
        raise GateBlocked('PROJECT_SCRATCH_UNSAFE')
    folder = scratch / ('cf10_g2b03c02_runtime_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    folder.mkdir(mode=0o700)
    payload = (json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
    summary = ('CF10_G2B03C02_STATUS='+doc['status']+'\n' +
               ''.join('BLOCKER='+b+'\n' for b in doc['blockers'])+
               ''.join('FINDING='+b+'\n' for b in doc['review_findings'])+
               'DYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\n'
               'WORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false\n').encode()
    files = {'report.json':payload,'summary.txt':summary}
    files['SHA256SUMS']=''.join(hashlib.sha256(blob).hexdigest()+'  '+name+'\n'
                                for name,blob in sorted(files.items())).encode()
    for name,blob in sorted(files.items()):
        fd=os.open(folder/name,os.O_WRONLY|os.O_EXCL|os.O_CREAT|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:
            f.write(blob);f.flush();os.fsync(f.fileno())
    return folder,hashlib.sha256(payload).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('.'))
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--no-report',action='store_true')
    args=parser.parse_args(argv)
    try:
        root=args.root.absolute()
        result=audit(root,args.expected_head)
        print('CF10_G2B03C02_STATUS='+result['status'])
        print('SOURCE_DESIGN='+str(result['source_design_state']))
        print('EXTERNAL_PROVENANCE='+str(result['provenance_state']))
        for b in result['blockers']:print('BLOCKER='+b)
        for b in result['review_findings']:print('FINDING='+b)
        if not args.no_report:
            target,digest=save_report(root,result)
            print('REPORT_DIR='+str(target))
            print('REPORT_SHA256='+digest)
        print('DYNAMIC_COVERAGE_VERIFIED=false\nSIGNED_RENEWAL_PERFORMED=false\nWORKER_LAUNCHED=false\nAUTHORITY_GRANTED=false')
        return 2 if result['blockers'] else 0
    except (GateBlocked,OSError,ValueError,RuntimeError) as e:
        print('CF10_G2B03C02_STATUS=BLOCKED_NON_AUTHORIZING',file=sys.stderr)
        print('BLOCKER='+type(e).__name__+':'+str(e)[:180],file=sys.stderr)
        print('AUTHORITY_GRANTED=false',file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
