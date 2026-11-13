#!/usr/bin/env python3
"""CF-10 S1 read-only attempt operator report integration candidate; NOT operator authority.

Runs in repository tmp/ and creates a derived, non-authoritative report only under
an explicitly configured tmp output directory. Canonical source/ledger are read-only.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from datetime import datetime, timezone

import yaml

SCHEMA = 'cf10_s1_attempt_operator_report_candidate_v0_2'
ATTEMPT_RE = re.compile(r'^cf10-[a-z0-9-]+$')
TOKEN_RE = re.compile(r'^[a-zA-Z0-9._-]+$')


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def load(path: Path):
    if not path.is_file():
        return None
    value = yaml.safe_load(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f'expected YAML mapping: {path}')
    return value


def bind(root: Path, path: Path):
    return {
        'path': str(path),
        'relative_path': str(path.relative_to(root)) if path.is_relative_to(root) else None,
        'exists': path.is_file(),
        'sha256': sha(path),
    }


def read_status(root: Path, runtime: Path, task: str, attempt: str):
    """Delegate lifecycle state to existing governed_worker_cycle status API."""
    from scripts.coordination.control_plane.governed_worker_cycle import status
    return status(root=root, runtime_root=runtime, task_prompt_id=task, attempt_id=attempt)


def collect(root: Path, runtime: Path, task: str, attempt: str, status_provider=read_status):
    if not ATTEMPT_RE.fullmatch(attempt) or not TOKEN_RE.fullmatch(task):
        raise ValueError('invalid attempt/task identifier')
    base = runtime / 'forprint_system_blueprint' / 'worker-01' / attempt
    ledger_dir = root / 'coordination/continuity/execution_attempts'
    decision_dir = root / 'coordination/continuity/worker_result_decisions'
    result_file = base / 'result/worker_result.yaml'
    return_file = base / 'evidence/governed_worker_cycle_result_return_v0_1.yaml'
    process_file = base / 'evidence/governed_worker_cycle_worker_process_result_v0_1.yaml'
    manifest_file = base / 'manifest.yaml'
    handoff_file = base / 'input/governed_worker_cycle_origin_handoff_manifest_v0_1.yaml'
    sources = {k: bind(root,p) for k,p in {
        'worker_result': result_file,
        'result_return': return_file,
        'worker_process_result': process_file,
        'worker_manifest': manifest_file,
        'origin_handoff': handoff_file,
    }.items()}
    blockers = []
    warnings = []
    parsed = {}
    for name, path in (('worker_result', result_file), ('result_return', return_file),
                       ('worker_process_result', process_file)):
        try:
            parsed[name] = load(path)
        except (OSError, yaml.YAMLError, ValueError) as exc:
            parsed[name] = None
            blockers.append('EVIDENCE_PARSE_FAILED:'+name+': '+str(exc))
    wr, rr, pr = (parsed[k] for k in ('worker_result', 'result_return', 'worker_process_result'))

    ledgers = []
    for p in sorted(ledger_dir.glob(f'{attempt}__*.yaml')):
        try:
            d = load(p)
            if d.get('attempt_id') != attempt:
                blockers.append('LEDGER_IDENTITY_CONFLICT: '+str(p))
            ledgers.append({'binding': bind(root,p), 'stage': d.get('attempt_stage'),
                            'result_state': d.get('result_state'),
                            'validator_outcome': d.get('validator_outcome'),
                            'work_front_id': d.get('work_front_id'),
                            'attempt_id': d.get('attempt_id'),
                            'source_fingerprint': d.get('source_fingerprint')})
        except (ValueError, OSError, yaml.YAMLError) as exc:
            blockers.append('LEDGER_PARSE_FAILED: '+str(exc))
    finished = [x for x in ledgers if x['stage'] == 'FINISHED']
    if len(finished) != 1:
        blockers.append(f'TERMINAL_LEDGER_COUNT={len(finished)}: expected exactly 1')
    terminal = finished[0] if len(finished) == 1 else None

    decisions = []
    for p in sorted(decision_dir.glob('*.yaml')) if decision_dir.is_dir() else []:
        try:
            d = load(p)
            if d.get('attempt_id') == attempt:
                decisions.append({'binding': bind(root,p), 'decision': d.get('decision'),
                                  'decision_id': d.get('decision_id')})
        except (OSError, ValueError, yaml.YAMLError) as exc:
            warnings.append('OTHER_DECISION_PARSE_FAILED: '+str(p))
    recorded = {d['decision'] for d in decisions}
    if len(recorded) > 1:
        blockers.append('CONFLICTING_OPERATOR_DECISIONS')
    if len(decisions) > 1:
        warnings.append('MULTIPLE_OPERATOR_DECISIONS_REVIEW_REQUIRED')
    decision_state = 'NOT_RECORDED' if not decisions else ('CONFLICT' if len(recorded) > 1 else str(decisions[-1]['decision']))

    try:
        projection = status_provider(root, runtime, task, attempt)
        if not isinstance(projection, dict):
            raise ValueError('status projection is not mapping')
    except Exception as exc:
        projection = {}
        blockers.append('GOVERNED_CYCLE_STATUS_UNAVAILABLE: '+str(exc))
    state = projection.get('state')
    boundary = projection.get('next_boundary')
    if wr is None: blockers.append('WORKER_RESULT_MISSING')
    if rr is None: blockers.append('RESULT_RETURN_MISSING')
    if pr is None: blockers.append('PROCESS_RESULT_MISSING')
    if not sources['worker_manifest']['exists']: blockers.append('WORKER_MANIFEST_MISSING')
    if not sources['origin_handoff']['exists']: blockers.append('ORIGIN_HANDOFF_MISSING')
    if wr:
        if wr.get('attempt_id') != attempt: blockers.append('WORKER_RESULT_ATTEMPT_MISMATCH')
        if wr.get('status') not in ('PASS', 'COMPLETED'): blockers.append('WORKER_RESULT_NOT_PASS')
        if not isinstance(wr.get('changed_paths'), list): blockers.append('WORKER_CHANGED_PATHS_INVALID')
        if wr.get('unresolved_findings') != []: blockers.append('WORKER_UNRESOLVED_FINDINGS')
        if wr.get('task_prompt_id') is not None and wr.get('task_prompt_id') != task:
            blockers.append('WORKER_TASK_MISMATCH')
        changes = wr.get('changed_paths')
        if isinstance(changes, list) and (len(changes) != len(set(map(str, changes))) or
            any(not isinstance(v, str) or v.startswith('/') or '..' in Path(v).parts for v in changes)):
            blockers.append('WORKER_CHANGED_PATHS_UNSAFE')
    if rr:
        if rr.get('attempt_id') != attempt or rr.get('result') != 'PASS' or rr.get('validation_passed') is not True or rr.get('blocked') is not False:
            blockers.append('RESULT_RETURN_NOT_VALIDATED')
        if rr.get('result_path') is not None and Path(str(rr['result_path'])).resolve() != result_file.resolve():
            blockers.append('RESULT_RETURN_PATH_MISMATCH')
        if rr.get('task_prompt_id') is not None and rr.get('task_prompt_id') != task:
            blockers.append('RESULT_RETURN_TASK_MISMATCH')
    if pr:
        process = pr.get('process')
        if pr.get('attempt_id') != attempt or not isinstance(process, dict) or process.get('return_code') != 0 or process.get('timed_out') is True:
            blockers.append('WORKER_PROCESS_NOT_SUCCESSFUL')
        if pr.get('task_prompt_id') is not None and pr.get('task_prompt_id') != task:
            blockers.append('PROCESS_TASK_MISMATCH')
    if terminal:
        if terminal['result_state'] != 'SUCCEEDED' or terminal['validator_outcome'] != 'PASS':
            blockers.append('TERMINAL_NOT_SUCCEEDED_PASS')
    suites = []
    for row in wr.get('validation_evidence', []) if isinstance(wr, dict) else []:
        if isinstance(row, dict) and row.get('kind') == 'validation_suite':
            suites.append({k: row.get(k) for k in ('suite_id', 'verification_tier', 'outcome', 'result', 'tests','evidence_digest','isolation_result')})
    if any(s['outcome'] != 'PASS' for s in suites): blockers.append('VALIDATION_SUITE_NOT_PASS')
    if wr and not suites: blockers.append('VALIDATION_SUITE_EVIDENCE_MISSING')
    if projection and projection.get('derived_non_authoritative') is not True:
        blockers.append('STATUS_PROJECTION_AUTHORITY_UNEXPECTED')
    if terminal and terminal.get('work_front_id') is None:
        blockers.append('TERMINAL_WORK_FRONT_MISSING')
    if not state or not boundary:
        blockers.append('GOVERNED_STATE_OR_BOUNDARY_MISSING')
    if decision_state == 'NOT_RECORDED' and state == 'AWAITING_OPERATOR_REVIEW' and boundary == 'OPERATOR_REVIEW' and not blockers:
        next_action = {'type': 'OPERATOR_REVIEW', 'required_authority': 'EXPLICIT_HUMAN_OPERATOR_DECISION',
                       'command': None, 'note': 'Do not use commit-only acceptance on zero-delta attempts.'}
    else:
        next_action = {'type':'INVESTIGATE_OR_FOLLOW_EXISTING_GOVERNED_PROJECTION',
                       'required_authority':'OPERATOR_INVESTIGATION', 'command':None}
    code = 'BLOCKED' if blockers else ('AWAITING_OPERATOR_REVIEW' if state == 'AWAITING_OPERATOR_REVIEW' and decision_state == 'NOT_RECORDED' else 'READ_ONLY_PROJECTION')
    head = subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,text=True)
    if head.returncode:
        blockers.append('GIT_HEAD_READ_FAILED')
        code = 'BLOCKED'
    if blockers:
        next_action = {'type': 'INVESTIGATE_EVIDENCE',
                       'required_authority': 'OPERATOR_INVESTIGATION',
                       'command': None}
        code = 'BLOCKED'
    report = {
      'schema_version':SCHEMA,
      'report_role':'DERIVED_NON_AUTHORITATIVE_NOT_OPERATOR_DECISION',
      'attempt_id':attempt,'task_prompt_id':task,
      'worker_id':'worker-01',
      'work_front_id':terminal['work_front_id'] if terminal else None,
      'canonical_git_head':head.stdout.strip() if not head.returncode else None,
      'worker_result_status':wr.get('status') if wr else None,
      'declared_changed_paths':wr.get('changed_paths') if wr else None,
      'unresolved_findings':wr.get('unresolved_findings') if wr else None,
      'result_return_status':rr.get('result') if rr else None,
      'validation_suites':suites,
      'validation_evidence_provenance':'WORKER_REPORTED_NOT_REEXECUTED_BY_THIS_REPORT',
      'attempt_ledgers':ledgers,
      'terminal_ledger':terminal,
      'operator_decision_state':decision_state,
      'operator_decisions':decisions,
      'governed_state':state,'next_boundary':boundary,
      'status_projection_derived_non_authoritative':projection.get('derived_non_authoritative'),
      'result_classification':code,
      'blockers':sorted(set(blockers)), 'warnings':sorted(set(warnings)),
      'next_action':next_action,
      'evidence':sources,
      'automatic_accept':False,'automatic_dispatch':False,'commit_performed':False,
      'push_performed':False,'promotion_performed':False,'publication_performed':False,
      'canonical_mutation_performed':False,
    }
    return report


def render_md(r):
    lines = [f"# CF-10 operator report candidate: {r['attempt_id']}", '',
      '**NON-AUTHORITATIVE / NOT AN OPERATOR DECISION**', '',
      '**Validation evidence is Worker-reported; S1 does not re-run tests.**', '',
      f"- Task: `{r['task_prompt_id']}`",
      f"- Worker Result: `{r['worker_result_status']}`",
      f"- Result return: `{r['result_return_status']}`",
      f"- Terminal: `{r['terminal_ledger']['result_state'] if r['terminal_ledger'] else 'NOT_FOUND'}`",
      f"- Operator decision: `{r['operator_decision_state']}`",
      f"- Governed status: `{r['governed_state']}` / `{r['next_boundary']}`",
      f"- Classification: `{r['result_classification']}`",
      f"- Changed paths: `{r['declared_changed_paths']}`",
      f"- Next: `{r['next_action']['type']}` / `{r['next_action']['required_authority']}`", '',
      '## Validation evidence', '']
    for item in r['validation_suites']:
        lines.append(f"- `{item.get('suite_id')}`: {item.get('outcome')} — {item.get('result')}")
    lines += ['', '## Blockers', '']
    lines += [f'- {x}' for x in r['blockers']] or ['- None']
    lines += ['', '## Evidence SHA256', '']
    for name,b in r['evidence'].items():
        lines.append(f"- {name}: `{b['sha256']}` ({b['path']})")
    if r['terminal_ledger']:
        t = r['terminal_ledger']['binding']
        lines.append(f"- terminal ledger: `{t['sha256']}` ({t['path']})")
    return '\n'.join(lines)+'\n'


# Small, precise source readback for project-native reuse review. Files are never
# executed, imported, or modified. Included in the result ZIP so the next
# engineering pass can assess actual function-level reuse, not just name matches.
SOURCE_PATHS = (
    'scripts/reporting/audit_consolidation.py',
    'scripts/coordination/modules/_shared/reporting.py',
    'scripts/coordination/modules/module_workflow_cli.py',
    'scripts/coordination/modules/forprint_system_blueprint/workflows/self_audit.py',
    'scripts/coordination/control_plane/governed_worker_cycle.py',
    'scripts/coordination/control_plane/post_commit_worker_acceptance.py',
    'scripts/coordination/control_plane/persist_worker_acceptance_evidence_v0_1.py',
    'scripts/coordination/control_plane/operator_console/mini_closeout.py',
)


def collect_reuse_sources(root: Path):
    manifest = []
    blobs = {}
    for rel in SOURCE_PATHS:
        path = root / rel
        if not path.exists() or path.is_symlink() or not path.is_file():
            manifest.append({'path': rel, 'exists': False})
            continue
        data = path.read_bytes()
        if len(data) > 300000:
            manifest.append({'path': rel, 'exists': True, 'skipped': 'size_limit', 'size': len(data)})
            continue
        entry = {'path': rel, 'exists': True, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
        try:
            tree = ast.parse(data.decode('utf-8'))
            entry['top_level_functions'] = [node.name for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))]
            entry['top_level_classes'] = [node.name for node in tree.body if isinstance(node,ast.ClassDef)]
        except (UnicodeDecodeError, SyntaxError) as exc:
            entry['parse_warning'] = str(exc)[:300]
        manifest.append(entry)
        blobs[rel] = data
    return {'role': 'NON_AUTHORITATIVE_SOURCE_REUSE_INVENTORY', 'files': manifest}, blobs


def write_preview(root: Path, report: dict, output_dir: Path, *, include_reuse: bool = False):
    """Write derived reports under isolated tmp only; never touch canonical or ledger."""
    temporary = (root / 'tmp').resolve()
    target = output_dir.resolve()
    if target == temporary or not target.is_relative_to(temporary):
        raise ValueError('output must be an isolated subdirectory under repository tmp/')
    if target.exists():
        raise FileExistsError(f'fail closed: output directory already exists: {target}')
    zpath = target.parent / (target.name + '.zip')
    if zpath.exists():
        raise FileExistsError('fail closed: report archive already exists: '+str(zpath))
    target.mkdir(parents=True)
    content = {
        'operator_report.json': json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n',
        'operator_report.yaml': yaml.safe_dump(report, sort_keys=True, allow_unicode=True),
        'operator_report.md': render_md(report),
    }
    for filename, text in content.items():
        (target / filename).write_text(text, encoding='utf-8')
    reuse_blobs = {}
    if include_reuse:
        reuse, reuse_blobs = collect_reuse_sources(root)
        (target / 'reuse_inventory.json').write_text(
            json.dumps(reuse, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')
    names = sorted(content) + (['reuse_inventory.json'] if include_reuse else [])
    checksums = ''.join(f'{sha(target / filename)}  {filename}\n' for filename in names)
    (target / 'SHA256SUMS').write_text(checksums, encoding='utf-8')
    # Stable zip member metadata: report bytes can be diffed across repeat runs.
    with zipfile.ZipFile(zpath, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for filename in ['SHA256SUMS', *names]:
            member = zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(member, (target / filename).read_bytes())
        for rel, data in sorted(reuse_blobs.items()):
            member = zipfile.ZipInfo('reuse_sources/'+rel, date_time=(1980, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(member, data)
    return zpath


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--runtime-root',type=Path,default=Path('/srv/software_development/forprint-worker-runtime'))
    p.add_argument('--attempt-id',required=True)
    p.add_argument('--task-prompt-id',required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--include-reuse-sources',action='store_true', help='optional source snapshot for engineering review')
    a=p.parse_args(argv)
    root=a.root.resolve()
    if root.name != 'forprint_system_blueprint' or not (root/'.git').is_dir():
        raise RuntimeError('expected live Blueprint repository root')
    report=collect(root,a.runtime_root.resolve(),a.task_prompt_id,a.attempt_id)
    archive=write_preview(root,report,a.output_dir,include_reuse=a.include_reuse_sources)
    print('CF10_S1_REPORT_CLASSIFICATION='+report['result_classification'])
    print('CF10_S1_GOVERNED_STATE='+str(report['governed_state']))
    print('CF10_S1_TERMINAL_COUNT='+str(sum(1 for x in report['attempt_ledgers'] if x['stage']=='FINISHED')))
    print('CF10_S1_OPERATOR_DECISION='+str(report['operator_decision_state']))
    print('CF10_S1_BLOCKERS='+str(len(report['blockers'])))
    print('CF10_S1_REPORT_ZIP='+str(archive))
    print('CF10_S1_NO_CANONICAL_MUTATION=true')
    print('CF10_S1_VALIDATION_EVIDENCE_PROVENANCE=WORKER_REPORTED_NOT_REEXECUTED')
    return 0 if not report['blockers'] else 2

if __name__ == '__main__':
    try: sys.exit(main())
    except (OSError, ValueError, RuntimeError, yaml.YAMLError) as exc:
        print('CF10_S1_REPORT_BLOCKED:',exc,file=sys.stderr)
        sys.exit(2)
