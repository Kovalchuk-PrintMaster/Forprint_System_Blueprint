"""Project-native non-authorizing Makefile source-policy audit (Q1).

No release approval, no writer-authority claims, no filesystem mutation.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

REQUIRED = (
 'cf10-s01-runtime-launch-preflight:',
 'CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND',
 'governed-worker-cycle-launch: cf10-s01-runtime-launch-preflight',
 'governed-worker-cycle-reconcile-result-return: cf10-s01-runtime-launch-preflight',
 'governed-worker-cycle-advance: cf10-s01-runtime-launch-preflight',
 'cf10-prelaunch-check:',
 'cf10-gate-writer-release-audit:',
 'CF10_ACCEPTANCE_REQUEST ?=',
 'CF10_ZERO_DELTA_PROOF ?=',
)


def inspect(text:str)->dict:
    findings=[]
    if re.search(r'(?i)(?<![\w])tmp(?![\w])|/tmp(/|\b)',text):
        findings.append('TRANSIENT_PATH_TOKEN_IN_MAKEFILE')
    for x in REQUIRED:
        if text.count(x)!=(2 if x.startswith('CF10_MAKE_RELEASE_BINDING=') else 1):findings.append('REQUIRED_WIRING_DRIFT:'+x)
    for target in ('cf10-s01-runtime-launch-preflight:', 'cf10-s01-runtime-binding-inspect:'):
        pos=text.find(target)
        if pos<0 or 'exit 2' not in text[pos:pos+180]:findings.append('QUARANTINE_MISSING:'+target)
    if 'generated/cf10_prelaunch_audits' not in text or 'generated/cf10_gate_writer_release_audits' not in text:
        findings.append('DERIVED_REPORT_OUTPUT_PATH_MISSING')
    return {'schema_version':'cf10_make_surface_policy_v0_1',
      'status':'BLOCKED' if findings else 'PASS_NON_AUTHORIZING',
      'findings':findings,'release_rebind_required':True,
      'worker_launch_allowed':False, 'writer_signature_authorized':False,
      'attempt_preparation_performed':False}


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'))
    a=p.parse_args(argv)
    path=a.root/'Makefile'
    if path.is_symlink() or not path.is_file():
        data={'status':'BLOCKED','findings':['UNSAFE_OR_MISSING_MAKEFILE']}
    else:data=inspect(path.read_text(encoding='utf-8'))
    print(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True))
    return 0 if data['status']=='PASS_NON_AUTHORIZING' else 2
if __name__=='__main__':sys.exit(main())
