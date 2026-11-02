"""CF10 r025: exact canonical seam inventory, no live launch or modification.

This module checks code shape AND exact Git object provenance before subsequent
cutover work. Inventory both frozen legacy mode and sealed systemd mode; no release authority.
"""
from __future__ import annotations
import ast
import hashlib
from pathlib import Path
import subprocess

CRITICAL=(
'scripts/coordination/control_plane/governed_worker_cycle.py',
'scripts/coordination/control_plane/cf10_owner_pam_launch_v0_1.py',
'scripts/coordination/control_plane/worker_runtime/launcher.py',
'scripts/coordination/control_plane/worker_runtime/invocation_adapter.py',
'scripts/coordination/control_plane/cf10_r024_disposable_supervisor_v0_1.py',
'scripts/coordination/control_plane/cf10_root_lifecycle_receipt_v0_1.py',
'scripts/coordination/control_plane/cf10_receipt_ledger_join_review_v0_1.py',
)

class SeamBlocked(RuntimeError):pass

def deny(reason):raise SeamBlocked('CF10_R025_SEAM_'+reason)

def _call_name(node):
    if isinstance(node,ast.Name):return node.id
    if isinstance(node,ast.Attribute):return _call_name(node.value)+'.'+node.attr
    return '<dynamic>'

def _fn(tree,name):
    funcs=[node for node in ast.walk(tree) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name]
    if len(funcs)!=1:deny('FUNCTION_COUNT:'+name)
    return funcs[0]

def _calls(func,name):
    return [x for x in ast.walk(func) if isinstance(x,ast.Call) and _call_name(x.func)==name]

def review_source_shapes(sources:dict[str,bytes])->dict:
    if set(sources)!=set(CRITICAL):deny('SOURCE_SET')
    try:trees={p:ast.parse(b,filename=p) for p,b in sources.items()}
    except (SyntaxError,UnicodeError) as exc:deny('SYNTAX:'+type(exc).__name__)
    base='scripts/coordination/control_plane/'
    cycle=trees[base+'governed_worker_cycle.py']
    auth=_fn(cycle,'launch_authorized_worker_cycle')
    owner=_fn(trees[base+'cf10_owner_pam_launch_v0_1.py'],'launch_once')
    launcher=_fn(trees[base+'worker_runtime/launcher.py'],'launch_process')
    adapter=trees[base+'worker_runtime/invocation_adapter.py']
    spawn_calls=_calls(launcher,'subprocess.Popen')
    callback_calls=_calls(launcher,'on_started')
    legacy_calls=_calls(auth,'launcher.launch_process')
    modern_calls=_calls(auth,'modern_route.run_once')
    if (len(spawn_calls)!=1 or len(callback_calls)!=1
            or spawn_calls[0].lineno>=callback_calls[0].lineno):
        deny('LEGACY_UTILITY_LAUNCHER_CONTRACT')
    if len(legacy_calls)==1 and len(modern_calls)==0:
        mode='LEGACY_ROOT_INHERITED_POPEN'
    elif len(legacy_calls)==0 and len(modern_calls)==1:
        gate_calls=_calls(owner,'modern_route.assert_cutover_ready')
        claim_calls=_calls(owner,'_owner_claim')
        if (len(gate_calls)!=1 or len(claim_calls)!=1
                or gate_calls[0].lineno>=claim_calls[0].lineno):
            deny('MODERN_OWNER_PRECLAIM_GATE')
        mode='SEALED_CANONICAL_SYSTEMD'
    else:
        deny('DUAL_LAUNCH_OR_UNKNOWN_BACKEND')
    claim=_calls(owner,'_owner_claim')
    enter=_calls(owner,'cycle.launch_cycle')
    if len(claim)!=1 or len(enter)!=1 or claim[0].lineno>=enter[0].lineno:deny('OWNER_CLAIM_ORDER')
    if not _calls(auth,'require_bounded_s01_launch_authority'):deny('OWNER_AUTHORITY_NOT_PRESENT')
    if not _calls(auth,'_b2_build_started_record'):deny('STARTED_CONTRACT_NOT_PRESENT')
    if not any(isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name=='build_launch_invocation' for x in ast.walk(adapter)):
        deny('INVOCATION_BUILDER_MISSING')
    return {'schema_version':'cf10_r025_canonical_seam_inventory_v0_1',
        'owner_claim_before_launch':True,'legacy_popen_present':mode=='LEGACY_ROOT_INHERITED_POPEN',
        'legacy_launch_callback_after_spawn':True,
        'legacy_canonical_launch_unchanged':mode=='LEGACY_ROOT_INHERITED_POPEN',
        'launch_mode':mode,'modern_systemd_canonical':mode=='SEALED_CANONICAL_SYSTEMD',
        'worker_cutover_authorized':False,'production_launch_allowed':False,
        'recovery_release_allowed':False,
        'source_sha256':{p:hashlib.sha256(sources[p]).hexdigest() for p in sorted(sources)}}

def inspect_committed(repo:Path,head:str)->dict:
    repo=Path(repo)
    if not repo.is_absolute() or not (repo/'.git').exists():deny('REPO')
    current=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    if current!=head:deny('HEAD_DRIFT')
    sources={}
    for path in CRITICAL:
        source=repo/path
        if not source.is_file() or source.is_symlink():deny('SOURCE_NOT_FILE:'+path)
        committed=subprocess.check_output(['git','-C',str(repo),'show',f'{head}:{path}'])
        if source.read_bytes()!=committed:deny('SOURCE_WORKTREE_DRIFT:'+path)
        sources[path]=committed
    return review_source_shapes(sources)
