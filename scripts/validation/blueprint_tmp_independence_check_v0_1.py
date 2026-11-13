"""Read-only, non-authorizing global Blueprint tmp-dependency policy gate."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

# Executed as a project-native script; canonical imports, no zip/staging imports.
from scripts.coordination.control_plane import blueprint_durable_storage_v0_1 as storage

POLICY = Path('coordination/global_policy/blueprint_tmp_independence_v0_1.yaml')

class CheckFailure(RuntimeError): pass

def check(root: Path) -> dict:
    root = root.resolve()
    if not (root / '.git').exists():
        raise CheckFailure('ROOT_NOT_GIT_CHECKOUT')
    policy = (root / POLICY).read_text('utf-8')
    for token in ('OWNER_APPROVED_GLOBAL_RULE', 'TMP_IS_DISPOSABLE_NOT_A_RUNTIME_DEPENDENCY',
                  '/srv/software_development/forprint-worker-runtime', 'hestia_out_of_scope: true',
                  'authorizes_launch: false', 'authorizes_release: false'):
        if token not in policy: raise CheckFailure('POLICY_CONTRACT_MISSING')
    makefile = (root / 'Makefile').read_text('utf-8')
    m = re.search(r'^GOVERNED_WORKER_RUNTIME_ROOT\s*\?=\s*(\S+)\s*$', makefile, re.M)
    if m is None: raise CheckFailure('WORKER_RUNTIME_MAKE_DEFAULT_MISSING')
    storage.require_runtime_root(m.group(1), blueprint_root=root)
    target = 'blueprint-tmp-independence-check'
    if not re.search(r'^'+target+r':\s*$', makefile, re.M):
        raise CheckFailure('MAKE_GATE_NOT_REGISTERED')
    if not re.search(r'^check-core:.*\b'+target+r'\b', makefile, re.M):
        raise CheckFailure('CORE_GATE_NOT_ATTACHED')
    if 'BLUEPRINT_TMP_INDEPENDENCE_GLOBAL' not in (root / 'AGENTS.md').read_text('utf-8'):
        raise CheckFailure('AGENTS_INVARIANT_MISSING')
    # Negative controls prove a runtime root cannot be redirected to a temporary path.
    for value in ('/tmp/runtime', '/var/tmp/runtime', str(root / 'tmp' / 'runtime'),
                  str(root / 'scripts' / 'runtime')):
        try: storage.require_runtime_root(value, blueprint_root=root)
        except storage.StorageBoundaryBlocked: pass
        else: raise CheckFailure('TEMP_OR_SOURCE_ROOT_ACCEPTED')
    storage.require_runtime_root(storage.RUNTIME_ROOT, blueprint_root=root)
    return {'status':'PASS_POLICY_AND_CRITICAL_RUNTIME_ROOT_NON_AUTHORIZING',
            'runtime_root':str(storage.RUNTIME_ROOT),
            'global_scope':True,'tmp_disposable':True,
            'production_wiring_tested':False,'full_repository_dependency_audit_complete':False,
            'worker_launch_authorized':False,'release_authorized':False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=Path.cwd())
    args=p.parse_args()
    try: result=check(args.root)
    except (OSError,ValueError,CheckFailure) as e:
        print('BLUEPRINT_TMP_INDEPENDENCE=BLOCKED:'+str(e), file=sys.stderr)
        return 2
    print('BLUEPRINT_TMP_INDEPENDENCE='+result['status'])
    print('RUNTIME_ROOT='+result['runtime_root'])
    print('RELEASE_GATE=BLOCKED_PENDING_END_TO_END_TMP_UNAVAILABLE_PROOF')
    return 0
if __name__ == '__main__': raise SystemExit(main())
