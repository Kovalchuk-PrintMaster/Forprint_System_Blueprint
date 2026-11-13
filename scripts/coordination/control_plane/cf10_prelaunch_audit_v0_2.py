#!/usr/bin/env python3
"""CF-10 project-owned non-authorizing prelaunch evidence collector. Never creates an attempt.

Executable source lives under scripts/, not tmp. Writes only a create-only
report directory under repository tmp. Never changes
Git, an attempt, signed decision, writer protocol, ledger or starts a worker.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

sys.dont_write_bytecode = True
TASK85 = 'cf10-project-change-impact-and-freshness-control-v0-1'
FRONT85 = 'coordination/work_fronts/cf10_project_change_impact_and_freshness_control_v0_1.yaml'
RUNTIME = '/srv/software_development/forprint-worker-runtime'
DECISION = '/etc/forprint/execution_attempt_writer_activation/signed_decision_v0_1.json'
SCHEMA = 'cf10_prelaunch_readiness_audit_v0_2'
SHA40 = re.compile(r'^[0-9a-f]{40}$')
SHA64 = re.compile(r'^[0-9a-f]{64}$')
ID = re.compile(r'^cf10-[a-z0-9-]+-a[0-9]{3}$')


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def cmd(args: list[str], cwd: Path, timeout: int = 15):
    try:
        p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True, timeout=timeout, check=False)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, '', type(exc).__name__


def result(name, status, details='', *, category='TECHNICAL'):
    assert status in ('PASS', 'BLOCKED', 'REVIEW', 'NOT_YET_TESTABLE', 'INFO')
    return {'id': name, 'status': status, 'category': category, 'detail': str(details)[:650]}


def load_json(path: Path):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError('missing or symlink file')
    return json.loads(path.read_text(encoding='utf-8'))


def load_yaml(path: Path):
    import yaml
    if path.is_symlink() or not path.is_file():
        raise RuntimeError('missing or symlink file')
    value = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise RuntimeError('expected YAML mapping')
    return value


def check_prior_accept(root: Path, runtime: Path, front_rel: str, new_attempt: str):
    """Reuse the real frozen-capsule zero-delta ACCEPT verifier, not a surrogate."""
    from scripts.coordination.control_plane.worker_runtime import invocation_adapter as inv
    front = load_yaml(root / front_rel)
    refs = front.get('provenance', {}).get('source_refs', [])
    if not isinstance(refs, list):
        raise RuntimeError('Work Front provenance source_refs invalid')
    op = [s.split(':', 1)[1] for s in refs if isinstance(s, str) and s.startswith('operator_decision:')]
    accepted = [s.split(':', 1)[1] for s in refs if isinstance(s, str) and s.startswith('accepted_attempt:')]
    if len(op) != 1 or len(accepted) != 1:
        raise RuntimeError('expected one prior operator decision and accepted attempt')
    relative = Path(op[0])
    if (not relative.as_posix().startswith('coordination/continuity/worker_result_decisions/')
        or relative.suffix != '.yaml' or '..' in relative.parts or relative.is_absolute()):
        raise RuntimeError('unsafe decision path')
    path = root / relative
    d = load_yaml(path)
    if d.get('schema_version') != 'cf10_zero_delta_operator_decision_v0_1':
        raise RuntimeError('different predecessor schema: needs dedicated review')
    attempt = runtime / 'forprint_system_blueprint' / 'worker-01' / new_attempt
    inv._verify_prior_zero_delta_accept(root=root, attempt=attempt,
        accepted=accepted[0], decision_path=path, decision=d,
        bindings=d.get('evidence_bindings'), source_refs=refs)
    return f'{accepted[0]} prior zero-delta ACCEPT evidence verified with canonical checker'


def check_frozen(root: Path, runtime: Path, front_rel: str, attempt_id: str):
    """Exact pre-worker frozen workspace/prior ACCEPT guard; never start Worker."""
    from scripts.coordination.control_plane.worker_runtime import invocation_adapter as inv
    attempt = runtime / 'forprint_system_blueprint' / 'worker-01' / attempt_id
    manifest = attempt / 'manifest.yaml'
    if not manifest.is_file():
        return result('frozen_capsule', 'NOT_YET_TESTABLE', 'Attempt has not been prepared; rerun after isolated prepare/ACK before authorization')
    if manifest.is_symlink():
        return result('frozen_capsule', 'BLOCKED', 'symlink manifest')
    data = load_yaml(manifest)
    workspace = data.get('workspace_repo')
    if not isinstance(workspace, str):
        return result('frozen_capsule', 'BLOCKED', 'workspace repo missing from manifest')
    ws = Path(workspace)
    # Work Front reference is rooted in immutable task selection, not CLI free-form.
    prompt = inv._verified_frozen_launch_context(root=root, attempt=attempt,
                                                 workspace=ws, binding={'work_front_ref': front_rel})
    if 'Prior operator zero-delta ACCEPT' not in prompt:
        return result('frozen_capsule', 'BLOCKED', 'Expected prior ACCEPT not present in frozen guard output')
    return result('frozen_capsule', 'PASS', 'Real frozen baseline, workspace delta and prior ACCEPT guard verified without Worker launch')


def inspect(root: Path, runtime: Path, task: str, attempt_id: str,
            expected_head: str, remote: bool):
    if str(root) not in sys.path: sys.path.insert(0, str(root))
    checks = []
    def add(*args, **kwargs): checks.append(result(*args, **kwargs))
    rc, head, msg = cmd(['git', 'rev-parse', 'HEAD'], root)
    add('canonical_head', 'PASS' if rc == 0 and head == expected_head else 'BLOCKED',
        f'actual={head or msg}; expected={expected_head}')
    rc, branch, _ = cmd(['git', 'branch', '--show-current'], root)
    add('branch', 'PASS' if rc == 0 and branch == 'audit/blueprint-inventory-refresh-2026-07-29' else 'BLOCKED', branch)
    rc, index, _ = cmd(['git', 'diff', '--cached', '--name-only'], root)
    add('index', 'PASS' if rc == 0 and not index else 'BLOCKED',
        'staged_paths=' + str(len(index.splitlines()) if index else 0))
    rc, status, _ = cmd(['git', 'status', '--porcelain=v1', '-uno'], root)
    add('protected_worktree', 'REVIEW' if rc == 0 and status else 'PASS' if rc == 0 else 'BLOCKED',
        'Tracked local changes count=' + str(len(status.splitlines()) if status else 0)
        + '; do not stage or clean automatically', category='NON_AUTHORITY')
    critical = ['scripts/coordination/control_plane/governed_worker_cycle.py',
       'scripts/coordination/control_plane/worker_runtime/invocation_adapter.py',
       'scripts/coordination/control_plane/dispatch_intent.py',
       'scripts/coordination/execution_attempt_ledger_v0_1.py', FRONT85]
    bad = []
    for rel in critical:
        p = root / rel
        rc, blob, _ = cmd(['git','hash-object',rel], root)
        rc2, tree, _ = cmd(['git','rev-parse','HEAD:'+rel],root)
        if rc != 0 or rc2 != 0 or blob != tree or not p.is_file() or p.is_symlink():
            bad.append(rel)
    add('critical_sources', 'BLOCKED' if bad else 'PASS',
        'tracked working-copy mismatches=' + ','.join(bad) if bad else '5 critical paths exactly match Git HEAD')
    if remote:
        rc, url, _ = cmd(['git','remote','get-url','origin'],root)
        if rc != 0 or url != 'git@github.com:Kovalchuk-PrintMaster/Forprint_System_Blueprint.git':
            add('remote_publication','BLOCKED','Origin mismatch/unavailable')
        else:
            rc, remote_ref, err = cmd(['git','ls-remote','--exit-code','origin',
                'refs/heads/audit/blueprint-inventory-refresh-2026-07-29'],root,timeout=25)
            sha = remote_ref.split()[0] if remote_ref else ''
            add('remote_publication', 'PASS' if rc == 0 and sha == expected_head else 'BLOCKED',
                'remote_sha='+sha if sha else 'unable to verify remote: '+err[:120])
    else:
        add('remote_publication','REVIEW','Not executed: --no-remote',category='NETWORK')
    if root.name != 'forprint_system_blueprint':
        add('repository_identity','BLOCKED','Repository basename mismatch')
    else:
        add('repository_identity','PASS','Expected repository')
    try:
        if task != TASK85: raise RuntimeError('this v0.1 profile handles Task85 only')
        front = load_yaml(root / FRONT85)
        add('work_front','PASS',str(front.get('work_front_id','unknown')))
    except Exception as exc:
        add('work_front','BLOCKED',type(exc).__name__+': '+str(exc))
    try:
        proof = check_prior_accept(root,runtime,FRONT85,attempt_id)
        add('prior_accept','PASS',proof)
    except Exception as exc:
        add('prior_accept','BLOCKED',type(exc).__name__+': '+str(exc))
    try:
        checks.append(check_frozen(root,runtime,FRONT85,attempt_id))
    except Exception as exc:
        add('frozen_capsule','BLOCKED',type(exc).__name__+': '+str(exc))
    attempt = runtime / 'forprint_system_blueprint' / 'worker-01' / attempt_id
    if attempt.exists():
        try:
            from scripts.coordination.control_plane import governed_worker_cycle as cycle
            proj = cycle.status(root=root,runtime_root=runtime,task_prompt_id=task,attempt_id=attempt_id)
            add('attempt_status','REVIEW',
                'state='+str(proj.get('state'))+'; a projection is NOT authorization',category='NON_AUTHORITY')
        except Exception as exc:
            add('attempt_status','BLOCKED',type(exc).__name__+': '+str(exc))
    else:
        add('attempt_status','NOT_YET_TESTABLE', 'No attempt created; this is intentional in analysis phase')
    # Full canonical invocation rehearsal only after explicit dispatch evidence exists.
    # Never synthesize authority or start a Worker; sanitized status enters the ZIP.
    from scripts.coordination.control_plane import cf10_invocation_rehearsal_v0_1 as rehearsal
    checks.append(rehearsal.inspect(root, runtime, task, attempt_id))
    decision_path = Path(DECISION)
    try:
        d = load_json(decision_path)
        binding = d.get('s01_runtime_binding_v0_2',{})
        bound = binding.get('deployment_git_head')
        expiry = datetime.fromisoformat(d['expires_at'].replace('Z','+00:00'))
        is_expired = datetime.now(timezone.utc)>=expiry
        add('signed_binding', 'PASS' if bound==expected_head and not is_expired else 'BLOCKED',
            'decision_sha256='+digest(decision_path.read_bytes())+
            '; signed_head='+str(bound)+'; expiry_utc='+d['expires_at']+
            '; expired='+str(is_expired)+'; signature not independently verified by this check')
    except Exception as exc:
        add('signed_binding','BLOCKED',type(exc).__name__+': '+str(exc))
    # Root-controlled renewal remains EXTERNAL to Blueprint. Never execute it
    # through an arbitrary tmp path or interpret an unsigned time/HEAD readback
    # as Ed25519 verification.
    add('operator_renewal', 'REVIEW',
        'External root-operator signature/coverage and expiry must be verified separately; '
        'no code in tmp is executed by this tool', category='HUMAN_GATE')
    makefile = root / 'Makefile'
    if not makefile.is_file() or makefile.is_symlink():
        add('legacy_tmp_tooling', 'BLOCKED', 'Makefile unavailable or symlink')
    else:
        data = makefile.read_text(encoding='utf-8')
        historical = [name for name in ('CF10_S01_GATE_ROOT', 'CF10_S01_WRITER_ROOT',
                      'CF10_S01_COVERAGE_EVIDENCE')
                      if re.search(r'^'+re.escape(name)+r'\s*\?=\s*.*tmp/', data, re.M)]
        add('legacy_tmp_tooling', 'REVIEW' if historical else 'PASS',
            'Legacy Gate/Writer/evidence Make variables relying on tmp: '
            + ','.join(historical) if historical else 'No known Gate/Writer tmp Make defaults',
            category='MIGRATION')
    # Automation can observe but cannot establish SSH exclusivity, full drain or operator consent.
    add('operator_coverage','REVIEW',
        'Requires human verification: all writer entrypoints, SSH/root, Docker, mounts, manual CLI, drained processes, maintenance freeze',
        category='HUMAN_GATE')
    add('worker_launch','INFO','Always forbidden by this tool; no attempt preparation, launch, ledger append or signed decision writes',category='AUTHORITY')
    return checks


def summarize(checks):
    counts={s:sum(x['status']==s for x in checks) for s in ('PASS','BLOCKED','REVIEW','NOT_YET_TESTABLE','INFO')}
    # Never call a static audit launch-ready.
    if counts['BLOCKED']: state='BLOCKED_NON_AUTHORIZING'
    elif counts['REVIEW'] or counts['NOT_YET_TESTABLE']: state='REVIEW_REQUIRED_NON_AUTHORIZING'
    else: state='EVIDENCE_COLLECTED_NON_AUTHORIZING'
    return state,counts


def save(root, parent, report, checks):
    base=(root/'generated').resolve()
    target=parent if parent.is_absolute() else root/parent
    # resolve(strict=False) and parent traversal fail closed
    if target.resolve() != base and base not in target.resolve().parents:
        raise RuntimeError('output must stay within repository generated area')
    if (root/'generated').is_symlink() or not (root/'generated').is_dir():
        raise RuntimeError('generated area unsafe or missing')
    relative = target.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RuntimeError('symlink output path ancestor')
    target.mkdir(mode=0o700,parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    dest=target/(f'cf10_prelaunch_{stamp}_{secrets.token_hex(3)}')
    dest.mkdir(mode=0o700)
    state,counts=summarize(checks)
    lines=[f'CF10_PRELAUNCH_STATE={state}',f'HEAD={report["expected_head"]}',
           f'ATTEMPT_ID={report["attempt_id"]}',
           f'CHECKS_PASS={counts["PASS"]}',f'CHECKS_BLOCKED={counts["BLOCKED"]}',
           f'CHECKS_REVIEW={counts["REVIEW"]}',f'CHECKS_NOT_YET_TESTABLE={counts["NOT_YET_TESTABLE"]}',
           'AUTHORITY_GRANTED=false','WORKER_LAUNCHED=false','SIGNED_DECISION_MUTATED=false',
           'REVIEW_OR_AUTHORIZE_SEPARATELY=true','', '=== CHECKS ===']
    for c in checks:lines.append(f'{c["status"]:18} {c["id"]:20} {c["detail"]}')
    summary='\n'.join(lines)+'\n'
    content={'summary.txt':summary.encode(),
      'report.json':(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode(),
      'checks.json':(json.dumps(checks,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()}
    content['SHA256SUMS']=''.join(digest(raw)+'  '+name+'\n' for name,raw in sorted(content.items())).encode()
    for name,raw in content.items():
        p=dest/name
        with p.open('xb') as f:f.write(raw)
        p.chmod(0o600)
    zpath=dest/'CF10_Prelaunch_Audit_Report.zip'
    with ZipFile(zpath,'x',ZIP_DEFLATED) as z:
        for name,raw in sorted(content.items()):
            info=ZipInfo(name,date_time=(2026,1,1,0,0,0));info.compress_type=ZIP_DEFLATED
            info.external_attr=0o600<<16
            z.writestr(info,raw)
    zpath.chmod(0o600)
    return zpath,summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--runtime-root',default=RUNTIME,type=Path)
    p.add_argument('--expected-head',required=True)
    p.add_argument('--task-id',default=TASK85)
    p.add_argument('--attempt-id',required=True)
    p.add_argument('--output-parent',default='generated/cf10_prelaunch_audits',type=Path)
    p.add_argument('--no-remote',action='store_true')
    a=p.parse_args()
    if not SHA40.fullmatch(a.expected_head) or not ID.fullmatch(a.attempt_id):p.error('invalid SHA/attempt')
    root=a.root.resolve()
    if root.is_symlink() or not (root/'.git').exists():p.error('canonical root unsafe')
    if Path(DECISION).is_symlink():p.error('authority file symlink unsafe')
    checks=inspect(root,a.runtime_root.resolve(),a.task_id,a.attempt_id,a.expected_head,
                   not a.no_remote)
    state,counts=summarize(checks)
    report={'schema_version':SCHEMA,'generated_utc':datetime.now(timezone.utc).isoformat(),
            'status':state,'counts':counts,'task_id':a.task_id,'attempt_id':a.attempt_id,
            'expected_head':a.expected_head,'checks':checks,
            'authority':{'granted':False,'operator_approval_performed':False,
                         'worker_launch_performed':False,'signed_renewal_performed':False,
                         'ledger_mutation_performed':False,'commit_performed':False,'push_performed':False}}
    archive,summary=save(root,a.output_parent,report,checks)
    print(summary,end='')
    print('REPORT_ZIP='+str(archive))
    print('REPORT_SHA256='+digest(archive.read_bytes()))
    print('CF10_PRELAUNCH_AUDIT=COMPLETE_NON_AUTHORIZING')
    return 0 if not counts['BLOCKED'] else 2

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('CF10_PRELAUNCH_AUDIT=BLOCKED:'+type(exc).__name__+':'+str(exc)[:350],file=sys.stderr)
        sys.exit(2)
