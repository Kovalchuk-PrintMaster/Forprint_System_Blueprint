#!/usr/bin/env python3
"""CF10 AA: bounded read-only repository Python AST/security inventory.

This is a triage inventory, NOT an automated security assessment, authorization
source, live execution check or acceptance oracle. No source bytes are emitted.
No network, credential read, git writes, caches or external tools beyond git.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

SCHEMA='cf10_repo_risk_inventory_v0_1'
MAX_FILE=2_000_000
MAX_FINDINGS=120
MAX_SOURCE=100_000_000
SHA40=re.compile(r'[0-9a-f]{40}\Z')

class InventoryHold(ValueError):pass

def deny(x):raise InventoryHold('CF10_AA_AUDIT_HOLD_'+x)

def _git(root:Path,*args)->bytes:
    try:
        cp=subprocess.run(['/usr/bin/git','-C',str(root),*args],stdin=subprocess.DEVNULL,
           stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=40,check=False,
           env={'PATH':'/usr/bin:/bin','LANG':'C','GIT_CONFIG_NOSYSTEM':'1'})
    except (OSError,subprocess.TimeoutExpired):deny('GIT_UNAVAILABLE')
    if cp.returncode!=0 or len(cp.stdout)>2_000_000:deny('GIT_ERROR_OR_OUTPUT_LIMIT')
    return cp.stdout

def _fqname(n:ast.AST)->str:
    if isinstance(n,ast.Name):return n.id
    if isinstance(n,ast.Attribute):return _fqname(n.value)+'.'+n.attr
    return ''

class Visitor(ast.NodeVisitor):
    def __init__(self): self.matches=[]
    def add(self,node,code,severity):self.matches.append((getattr(node,'lineno',0),code,severity))
    def visit_Call(self,node):
        name=_fqname(node.func)
        if name in ('eval','exec','os.system','pickle.loads','marshal.loads'):
            self.add(node,'DYNAMIC_EXECUTION_OR_UNSAFE_LOAD','REVIEW_HIGH')
        if name.startswith('subprocess.') and name in ('subprocess.run','subprocess.Popen','subprocess.call','subprocess.check_output'):
            if any(k.arg=='shell' and isinstance(k.value,ast.Constant) and k.value.value is True for k in node.keywords):
                self.add(node,'SUBPROCESS_SHELL_TRUE','REVIEW_HIGH')
        if name in ('yaml.load','ruamel.yaml.load'):
            self.add(node,'YAML_LOAD_CHECK_LOADER','REVIEW_MEDIUM')
        self.generic_visit(node)
    def visit_Assign(self,node):
        for target in node.targets:
            if isinstance(target,ast.Name) and target.id=='LIVE_CUTOVER_ENABLED' and (
                not isinstance(node.value,ast.Constant) or node.value.value is not False):
                self.add(node,'LIVE_CUTOVER_SOURCE_NOT_FALSE','REVIEW_CRITICAL')
        self.generic_visit(node)

def analyze_source(src:bytes,path:str)->tuple[list[dict],bool]:
    if b'\x00' in src:deny('PYTHON_NUL_BYTES')
    try:
        tree=ast.parse(src.decode('utf-8-sig'),filename=path)
    except (SyntaxError,UnicodeError):
        return [{'path':path,'line':0,'code':'PYTHON_PARSE_FAILED','severity':'REVIEW_HIGH'}],False
    v=Visitor();v.visit(tree)
    return [{'path':path,'line':line,'code':code,'severity':sev} for line,code,sev in v.matches],True

def inventory(root:Path, *, max_files:int=15000)->dict:
    root=Path(root)
    if root.is_symlink() or not root.is_dir() or not (root/'.git').exists():deny('REPOSITORY_SCOPE')
    raw=_git(root,'ls-files','-z')
    if not raw or not raw.endswith(b'\x00'):deny('TRACKED_FILES')
    try: names=[x.decode('utf-8','strict') for x in raw[:-1].split(b'\x00')]
    except UnicodeError:deny('TRACKED_PATH_ENCODING')
    if not 1<=len(names)<=max_files or len(names)!=len(set(names)):deny('TRACKED_COUNT')
    head=_git(root,'rev-parse','HEAD').decode('ascii','strict').strip()
    if SHA40.fullmatch(head) is None:deny('HEAD')
    risks=[]; types=Counter(); top_dirs=Counter(); total=0;parsed=0; read_bytes=0; errors=0
    for rel in names:
        p=Path(rel)
        if not rel or p.is_absolute() or any(x in ('.','..') for x in p.parts):deny('TRACKED_TRAVERSAL')
        types[p.suffix.lower() or '[no extension]']+=1
        top_dirs[p.parts[0]]+=1
        if p.suffix!='.py':continue
        total+=1
        f=root/p
        try:st=f.lstat()
        except OSError:
            risks.append({'path':rel,'line':0,'code':'TRACKED_PYTHON_MISSING','severity':'REVIEW_HIGH'});errors+=1;continue
        if not stat.S_ISREG(st.st_mode) or st.st_size>MAX_FILE or st.st_size<0:
            risks.append({'path':rel,'line':0,'code':'TRACKED_PYTHON_NOT_REGULAR_OR_OVERSIZE','severity':'REVIEW_HIGH'});errors+=1;continue
        read_bytes+=st.st_size
        if read_bytes>MAX_SOURCE:deny('TOTAL_SOURCE_BYTES_EXCEEDED')
        try: src=f.read_bytes()
        except OSError:
            risks.append({'path':rel,'line':0,'code':'TRACKED_PYTHON_UNREADABLE','severity':'REVIEW_HIGH'});errors+=1;continue
        found,ok=analyze_source(src,rel)
        risks.extend(found);parsed+=int(ok);errors+=int(not ok)
    priority={'REVIEW_CRITICAL':0,'REVIEW_HIGH':1,'REVIEW_MEDIUM':2}
    risks.sort(key=lambda v:(priority[v['severity']],v['path'],v['line'],v['code']))
    totals=Counter(x['code'] for x in risks)
    manifest={'schema':SCHEMA,'git_head':head,'tracked_files':len(names),
      'python_tracked':total,'python_ast_parsed':parsed,'python_unparsed':errors,
      'python_source_bytes_inspected':read_bytes,'file_types_top':dict(types.most_common(12)),
      'top_level_counts':dict(top_dirs.most_common(12)),
      'risk_counts':dict(sorted(totals.items())),
      'risk_findings_sample':risks[:MAX_FINDINGS],
      'risk_findings_truncated':max(0,len(risks)-MAX_FINDINGS),
      'full_python_tracked_scan_completed':parsed+errors==total,
      'review_needed_for_findings':True,'source_text_in_evidence':False,
      'credential_values_read':False,'git_mutated':False,
      'worker_launched':False,'live_authority':False,'g1_g5_open':True}
    encoded=json.dumps(manifest,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
    manifest['inventory_sha256']=hashlib.sha256(encoded).hexdigest()
    return manifest

def main(argv=None)->int:
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.');parser.add_argument('--output',default=None);parser.add_argument('--brief',action='store_true')
    args=parser.parse_args(argv)
    try: row=inventory(Path(args.root))
    except InventoryHold as e:
        print(str(e));return 3
    data=json.dumps(row,sort_keys=True,indent=2,ensure_ascii=False)+'\n'
    if args.output:
        out=Path(args.output)
        if out.is_symlink() or out.exists():
            print('CF10_AA_AUDIT_HOLD_OUTPUT_EXISTS');return 3
        fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
        try:
            os.write(fd,data.encode('utf8'));os.fsync(fd)
        finally:os.close(fd)
    elif args.brief:
        print('CF10_AA_AUDIT=PASS_TRACKED_'+str(row['tracked_files'])+'_PYTHON_'+str(row['python_tracked'])+'_PARSED_'+str(row['python_ast_parsed']))
        print('CF10_AA_AUDIT_FINDINGS_REQUIRE_REVIEW='+str(sum(row['risk_counts'].values())))
        print('CF10_AA_AUDIT_NO_LIVE_AUTHORITY=PASS')
    else:print(data)
    return 0
if __name__=='__main__':raise SystemExit(main())
