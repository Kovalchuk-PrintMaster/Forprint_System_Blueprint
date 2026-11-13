#!/usr/bin/env python3
"""CF-10 S2B candidate: independent zero-delta operator review, fail-closed.

READ-ONLY preview. Explicit decide writes exactly one append-only record; does NOT
change governed_worker_cycle status, promote, stage, commit, push or publish.
Current-workspace proof is NOT an historical worker-exit attestation.
Not authorized for canonical deployment until operator approves the contract.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable

import yaml

SCHEMA = 'cf10_zero_delta_operator_review_preview_v0_1'
DECISION_SCHEMA = 'cf10_zero_delta_operator_decision_v0_1'
DIR = Path('coordination/continuity/worker_result_decisions')
ID = re.compile(r'^[a-z0-9][a-z0-9-]{2,110}$')
HEX = re.compile(r'^[0-9a-f]{64}$')
ALLOWED = {'ACCEPT', 'HOLD', 'RETURN'}
BINDING_FILES = {
    'worker_manifest': 'manifest.yaml',
    'worker_baseline': 'evidence/worker_baseline_v0_1.yaml',
    'worker_result': 'result/worker_result.yaml',
    'result_return': 'evidence/governed_worker_cycle_result_return_v0_1.yaml',
    'process_result': 'evidence/governed_worker_cycle_worker_process_result_v0_1.yaml',
    'origin_handoff': 'input/governed_worker_cycle_origin_handoff_manifest_v0_1.yaml',
}


class Blocked(RuntimeError):
    pass


def require(test: bool, code: str) -> None:
    if not test:
        raise Blocked(code)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def yaml_map(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink(), 'MISSING_OR_SYMLINK:'+str(path))
    obj = yaml.safe_load(path.read_bytes())
    require(isinstance(obj, dict), 'INVALID_MAPPING:'+str(path))
    return obj


def safe_dir(root: Path, sub: Path) -> Path:
    require(not sub.is_symlink(), 'SYMLINK_DIRECTORY')
    resolved = sub.resolve(strict=True)
    require(resolved.is_relative_to(root.resolve(strict=True)), 'PATH_OUTSIDE_ROOT')
    return resolved


def decision_rows(root: Path, attempt: str) -> list[dict[str, Any]]:
    folder = root / DIR
    require(folder.is_dir() and not folder.is_symlink(), 'DECISION_DIRECTORY_MISSING_OR_SYMLINK')
    rows = []
    for path in sorted(folder.glob('*.yaml')):
        require(not path.is_symlink(), 'DECISION_SYMLINK_PRESENT')
        doc = yaml_map(path)
        if doc.get('attempt_id') == attempt:
            rows.append({'path': str(path.relative_to(root)), 'record': doc, 'sha256': sha(path)})
    return rows


def evaluate(root: Path, runtime: Path, proof_file: Path, task: str, attempt: str,
             *, collect_fn: Callable | None = None, derive_fn: Callable | None = None,
             allow_existing: bool = True) -> dict:
    root = root.resolve(strict=True)
    runtime = runtime.resolve(strict=True)
    require(bool(ID.fullmatch(attempt)) and bool(ID.fullmatch(task)), 'INVALID_IDS')
    require((root / '.git').exists(), 'NOT_GIT_REPOSITORY')
    p = proof_file.absolute()
    require(not p.is_symlink() and p.is_file(), 'PROOF_FILE_MISSING_OR_SYMLINK')
    require(p.resolve().is_relative_to((root / 'tmp').resolve(strict=True)), 'PROOF_NOT_UNDER_REPO_TMP')
    proof = yaml_map(p)
    require(proof.get('schema_version') == 'cf10_s2_independent_workspace_proof_v0_1', 'PROOF_SCHEMA')
    require(proof.get('attempt_id') == attempt and proof.get('task_prompt_id') == task, 'PROOF_IDENTITY')
    require(proof.get('result_role') == 'DERIVED_READ_ONLY_NON_AUTHORITATIVE_NOT_ACCEPT', 'PROOF_ROLE')
    disp = proof.get('disposition') or {}
    require(disp.get('state') == 'INDEPENDENT_CURRENT_WORKSPACE_ZERO_DELTA_PASS', 'PROOF_NOT_PASS')
    require(disp.get('blockers') == [], 'PROOF_BLOCKERS')
    require(disp.get('independent_current_workspace_zero_delta_proven') is True, 'PROOF_NOT_INDEPENDENT')
    require(disp.get('historical_end_of_process_snapshot_attested') is False, 'HISTORIC_CLAIM_UNEXPECTED')
    require(disp.get('operator_decision_allowed_by_this_tool') is False, 'PROOF_AUTHORITY_WIDENED')
    require(proof.get('time_scope') == 'CURRENT_WORKSPACE_AT_PROOF_EXECUTION_NOT_AT_WORKER_EXIT', 'PROOF_TIME_SCOPE')
    require(proof.get('operator_decision_written') is False and proof.get('canonical_mutation_performed') is False, 'PROOF_MUTATION_CLAIM')
    base = runtime / 'forprint_system_blueprint' / 'worker-01' / attempt
    require(base.is_dir() and not base.is_symlink(), 'ATTEMPT_RUNTIME_MISSING')
    paths = {key: base / rel for key, rel in BINDING_FILES.items()}
    ledgers = list((root / 'coordination/continuity/execution_attempts').glob(attempt+'__*.yaml'))
    finished = [f for f in ledgers if yaml_map(f).get('attempt_stage') == 'FINISHED']
    require(len(finished) == 1, 'EXPECTED_ONE_FINISHED_LEDGER')
    paths['terminal_ledger'] = finished[0]
    bindings = proof.get('evidence_bindings') or {}
    for key, path in paths.items():
        expected = bindings.get(key) or {}
        require(path.is_file() and not path.is_symlink(), 'SOURCE_MISSING_OR_SYMLINK:'+key)
        require(expected.get('path') == str(path), 'EVIDENCE_PATH_MISMATCH:'+key)
        require(expected.get('sha256') == sha(path), 'EVIDENCE_SHA_CHANGED:'+key)
        require(expected.get('bytes') == path.stat().st_size, 'EVIDENCE_SIZE_CHANGED:'+key)
    if collect_fn is None:
        from scripts.coordination.control_plane.cf10_attempt_operator_report_v0_2 import collect as collect_fn
    if derive_fn is None:
        from scripts.coordination.control_plane.workspace import derive_worker_delta_from_manifest as derive_fn
    report = collect_fn(root, runtime, task, attempt)
    require(report.get('blockers') == [], 'S1_BLOCKERS')
    require(report.get('attempt_id') == attempt and report.get('task_prompt_id') == task, 'S1_IDENTITY')
    require(report.get('report_role') == 'DERIVED_NON_AUTHORITATIVE_NOT_OPERATOR_DECISION', 'S1_ROLE')
    require(report.get('worker_result_status') == 'PASS' and report.get('result_return_status') == 'PASS', 'S1_RESULT_NOT_PASS')
    require(report.get('declared_changed_paths') == [], 'S1_CHANGED_PATHS')
    terminal = report.get('terminal_ledger') or {}
    require(terminal.get('stage') == 'FINISHED' and terminal.get('result_state') == 'SUCCEEDED' and terminal.get('validator_outcome') == 'PASS', 'S1_TERMINAL')
    require((terminal.get('binding') or {}).get('sha256') == sha(finished[0]), 'S1_TERMINAL_SHA')
    # Work Front owner and scope re-check, no broad recursive policy changes.
    wf_id = terminal.get('work_front_id')
    require(isinstance(wf_id,str) and wf_id, 'WORK_FRONT_ID_MISSING')
    wfs = [(f,yaml_map(f)) for f in (root/'coordination/work_fronts').glob('*.yaml')]
    matched = [(f,obj) for f,obj in wfs if obj.get('work_front_id') == wf_id]
    require(len(matched) == 1, 'WORK_FRONT_NOT_UNIQUE')
    wf_file,wf = matched[0]
    scope=wf.get('scope')
    require(isinstance(scope,list) and bool(scope) and all(isinstance(v,str) and v and not v.startswith('/') and '..' not in Path(v).parts for v in scope) and len(set(scope))==len(scope), 'WORK_FRONT_SCOPE_INVALID')
    require(wf.get('authority',{}).get('layer') == 'WORK_FRONT', 'WORK_FRONT_AUTHORITY_INVALID')
    result = yaml_map(paths['worker_result'])
    manifest = yaml_map(paths['worker_manifest'])
    ledger = yaml_map(paths['terminal_ledger'])
    return_evidence = yaml_map(paths['result_return'])
    require(result.get('attempt_id') == attempt and result.get('status') == 'PASS', 'WORKER_RESULT_INVALID')
    require(result.get('changed_paths') == [] and result.get('unresolved_findings') == [], 'WORKER_RESULT_DELTA_OR_FINDINGS')
    require((result.get('resume_coordinates') or {}).get('attempt_id') == attempt, 'WORKER_S4_RESUME_ATTEMPT_MISMATCH')
    require(ledger.get('work_front_id') == wf_id, 'TERMINAL_WORK_FRONT_MISMATCH')
    require(result.get('handoff_manifest_sha256') == ledger.get('pack_hash_or_context_hash'), 'HANDOFF_BINDING_MISMATCH')
    require(manifest.get('source_head') == proof.get('source_head'), 'MANIFEST_SOURCE_HEAD_MISMATCH')
    require(return_evidence.get('validation_passed') is True and return_evidence.get('blocked') is False, 'RESULT_RETURN_INVALID')
    require(return_evidence.get('result_path') == str(paths['worker_result']), 'RESULT_RETURN_PATH_MISMATCH')
    native = derive_fn(paths['worker_manifest'])
    old = proof.get('independent_delta') or {}
    # S2A stores workspace_repo at the top level, not inside independent_delta.
    require(proof.get('workspace_repo') == manifest.get('workspace_repo') == native.get('workspace_repo'),
            'LIVE_DELTA_CHANGED:workspace_repo')
    for key in ('attempt_id','source_head','baseline_fingerprint_sha256','changed_paths','post_worker_dirty_paths','inherited_dirty_paths'):
        require(native.get(key) == old.get(key), 'LIVE_DELTA_CHANGED:'+key)
    require(native.get('changed_paths') == [] and native.get('worker_delta_exact') is True, 'LIVE_ZERO_DELTA_INVALID')
    require(native.get('authority_granted') is False and native.get('candidate_promoted') is False and native.get('canonical_write_performed') is False, 'LIVE_AUTHORITY_WIDENED')
    require(report.get('governed_state') == 'AWAITING_OPERATOR_REVIEW' and report.get('next_boundary') == 'OPERATOR_REVIEW', 'GOVERNED_STATE_UNEXPECTED')
    rows = decision_rows(root,attempt)
    require(all(x['record'].get('schema_version') == DECISION_SCHEMA for x in rows), 'MIXED_OPERATOR_DECISION_CONTRACT')
    require(len(rows) <= 1, 'MORE_THAN_ONE_ZERO_DELTA_DECISION')
    if not allow_existing:
        require(not rows, 'ALREADY_DECIDED')
    bound = {'attempt_id':attempt,'task_prompt_id':task,'work_front_id':wf_id,
             'proof_sha256':sha(p),'terminal_sha256':sha(paths['terminal_ledger']),
             'worker_result_sha256':sha(paths['worker_result']),
             'manifest_sha256':sha(paths['worker_manifest']),
             'baseline_sha256':sha(paths['worker_baseline']),
             'origin_handoff_sha256':sha(paths['origin_handoff']),
             'result_return_sha256':sha(paths['result_return']),
             'work_front_sha256':sha(wf_file),'source_head':manifest.get('source_head'),
             'temporal_scope':'CURRENT_WORKSPACE_AT_REVIEW_NOT_HISTORICAL_EXIT'}
    digest = hashlib.sha256(json.dumps(bound,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'schema_version':SCHEMA,'status':'EXISTING_OPERATOR_DECISION' if rows else 'READY_FOR_EXPLICIT_OPERATOR_DECISION',
            'attempt_id':attempt,'task_prompt_id':task,'work_front_id':wf_id,
            'decision_binding_sha256':digest,'bound_evidence':bound,
            'existing_decisions':rows,
            'operator_decision_recorded':bool(rows),
            'historical_exit_attestation':False,
            'governed_state':report.get('governed_state'),
            'governed_status_changed_by_this_tool':False,
            'zero_delta_promotion_required':False,
            'automatic_accept':False,'automatic_commit':False,'automatic_push':False,'automatic_publication':False,
            'next_action':'EXPLICIT_HUMAN_REVIEW' if not rows else 'ZERO_DELTA_STATUS_POLICY_RECONCILIATION'}


def decide(root:Path,preview:dict,decision:str,decision_id:str,operator_ref:str,confirm:str,temporal_ack:str) -> dict:
    require(preview.get('status') in ('READY_FOR_EXPLICIT_OPERATOR_DECISION','EXISTING_OPERATOR_DECISION'), 'PREVIEW_NOT_READY')
    require(decision in ALLOWED and bool(ID.fullmatch(decision_id)) and bool(ID.fullmatch(operator_ref)), 'BAD_DECISION_ARGUMENTS')
    digest=preview['decision_binding_sha256']
    require(confirm == f'{decision}:{preview["attempt_id"]}:{digest[:12]}', 'CONFIRMATION_MISMATCH')
    require(temporal_ack == 'CURRENT_WORKSPACE_ONLY_NOT_HISTORICAL_EXIT', 'TEMPORAL_LIMIT_ACK_REQUIRED')
    folder=root/DIR
    record = {
      'schema_version':DECISION_SCHEMA,
      'record_role':'zero_delta_operator_decision_not_promotion_or_publication',
      'decision_id':decision_id,'decision':decision,'attempt_id':preview['attempt_id'],
      'task_prompt_id':preview['task_prompt_id'],'work_front_id':preview['work_front_id'],
      'operator_ref':operator_ref,'review_binding_sha256':digest,
      'evidence_bindings':preview['bound_evidence'],
      'zero_delta_confirmed_current_workspace':True,
      'historical_exit_attestation':False,
      'canonical_promotion_performed':False,'commit_performed':False,'push_performed':False,
      'publication_state':'NOT_ATTESTED',
      'governed_status_projection_updated':False,
      'next_boundary':'ZERO_DELTA_STATUS_POLICY_RECONCILIATION',
    }
    target=folder/f'{preview["attempt_id"]}__zero_delta_operator_decision_v0_1.yaml'
    old=preview.get('existing_decisions') or []
    if old:
        require(len(old) == 1 and old[0]['path'] == str(target.relative_to(root)), 'DECISION_ALREADY_EXISTS')
        observed=old[0]['record']
        check_keys=set(record)
        require(all(observed.get(k) == record[k] for k in check_keys), 'DECISION_REPLAY_CONFLICT')
        return {'decision_record':str(target),'action':'IDENTICAL_REPLAY_NO_WRITE','decision':decision}
    # Exclusive create: never overwrite, truncate, or mutate previous records.
    record['recorded_at']=datetime.now(timezone.utc).isoformat()
    raw=yaml.safe_dump(record,sort_keys=False,allow_unicode=True)
    try:
        with target.open('x',encoding='utf-8') as f:
            f.write(raw)
            f.flush()
    except FileExistsError as exc:
        raise Blocked('DECISION_FILE_ALREADY_CREATED_CONCURRENTLY') from exc
    return {'decision_record':str(target),'action':'APPEND_ONLY_DECISION_WRITTEN','decision':decision}


def main(argv:list[str]|None=None) -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=('preview','decide'))
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--runtime-root',type=Path,default=Path('/srv/software_development/forprint-worker-runtime'))
    ap.add_argument('--proof-file',type=Path,required=True)
    ap.add_argument('--task',required=True)
    ap.add_argument('--attempt-id',required=True)
    ap.add_argument('--decision',choices=sorted(ALLOWED))
    ap.add_argument('--decision-id')
    ap.add_argument('--operator-ref')
    ap.add_argument('--confirm')
    ap.add_argument('--temporal-ack')
    args=ap.parse_args(argv)
    try:
        sys.path.insert(0,str(args.root.resolve(strict=True)))
        preview=evaluate(args.root,args.runtime_root,args.proof_file,args.task,args.attempt_id)
        if args.action=='preview':
            print(yaml.safe_dump(preview,allow_unicode=True,sort_keys=False))
        else:
            result=decide(args.root.resolve(strict=True),preview,args.decision,args.decision_id,args.operator_ref,args.confirm,args.temporal_ack)
            print(yaml.safe_dump(result,sort_keys=False,allow_unicode=True))
        return 0
    except (Blocked,ValueError,OSError,TypeError,yaml.YAMLError) as exc:
        print('CF10_S2B_BLOCKED='+str(exc),file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
