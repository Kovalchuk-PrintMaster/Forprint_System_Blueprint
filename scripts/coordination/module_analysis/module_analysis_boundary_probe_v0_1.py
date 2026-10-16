#!/usr/bin/env python3
"""Non-invasive boundary probe. Reads Git, Makefile only; report is written to requested tmp/ path."""
from pathlib import Path
import argparse, json, subprocess, re

def cmd(root, *args):
    p=subprocess.run(args,cwd=root,text=True,capture_output=True,timeout=12)
    return p.stdout.strip() if p.returncode == 0 else None

def probe(root):
    head=cmd(root,'git','rev-parse','HEAD')
    stat=cmd(root,'git','status','--porcelain=v1','-uno')
    lines=(stat or '').splitlines()
    make=(root/'Makefile').read_text('utf-8') if (root/'Makefile').is_file() else ''
    names=set(re.findall(r'^([a-zA-Z0-9_.-]+):(?:\s|$)',make,flags=re.M))
    targets=('assistant-context-pack','roadmap-sync-check','coordination-pulse','oc01-session-projection-check','oc01-console-check','oc01-mini-closeout-check','cf10-worker-invocation-bridge-check')
    stat_counts={'blueprint_tracked_dirty': len(lines), 'cf10_related_dirty':0,'oc01_related_dirty':0,'analysis_target_dirty':0,'other_dirty':0}
    for l in lines:
        path=l[3:].lower()
        if 'cf10' in path or '/worker_runtime/' in path or 'work_front_closeout' in path: stat_counts['cf10_related_dirty']+=1
        elif 'oc01' in path: stat_counts['oc01_related_dirty']+=1
        elif 'module_roadmap_review_pilots' in path or 'module_analysis' in path: stat_counts['analysis_target_dirty']+=1
        else: stat_counts['other_dirty']+=1
    return {'schema_version':'module_boundary_readonly_probe_v0_1', 'source':'LIVE_LOCAL_REPO_METADATA_ONLY',
        'head':head,'tracked_dirty_summary':stat_counts,'make_target_presence':{t:t in names for t in targets},
        'oc01_runtime':'NOT_CHECKED','cf10_runtime':'NOT_CHECKED','module_inspector_conformance':'NOT_CHECKED',
        'production_runtime_inspector':'NOT_CHECKED','telegram_deployment':'NOT_CHECKED',
        'side_effects':'NO_MAKE_RUN_NO_SERVICE_RUN_NO_GIT_WRITES',
        'warning':'Do not treat presence of Make targets as passing tests or current readiness.'}

def main():
    pa=argparse.ArgumentParser();pa.add_argument('--repo',type=Path,required=True);pa.add_argument('--output',type=Path,required=True)
    a=pa.parse_args();root=a.repo.resolve();out=a.output.resolve()
    if root not in out.parents or 'tmp' not in out.relative_to(root).parts: raise SystemExit('DENY_OUTPUT_OUTSIDE_PROJECT_TMP')
    if out.exists(): raise SystemExit('DENY_OVERWRITE')
    d=probe(root)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print('BOUNDARY_METADATA_PROBE=PASS')
    print('OUTPUT='+str(out))
    print('RUNTIME_CHECKS=NOT_CHECKED')
if __name__=='__main__':main()
