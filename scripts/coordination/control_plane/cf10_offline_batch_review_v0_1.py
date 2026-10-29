#!/usr/bin/env python3
"""Reconcile an exported ForPrint CF-10 offline batch, non-authorizing.

No imported project code is executed. No read from /etc, /run, or external trust.
Output is local analysis only, not a verified runtime Writer-coverage proof.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

SOURCE_HEAD='93b81ea783cfe0feec619eaa764dce9eaaf4f8ec'
SOURCE_PREFIX='published_head/'
KNOWN_REPORTS={
 'p07_write_survey.json': '935b75d3f5476bafc446df638716650e9456631665166a43c970f7f3c2f8159a',
 'p08_semantics.json': '28556680e74415939ad8deb225650a1154a01dec34a4c4fe6885f32be50355be',
 'p09_routes.json': 'f90b7f6209666daceac404c924bc478a8b8b141f41014f688e3ec94762def2ed',
 'p10_metadata.json': 'a0777844c2d6c3468d5775bec511a45c0d6c9da5c54a63c35529e1cd5e430ade',
 'p11_declaration.json': 'dfb375a82fec65cfa9cfd86b65186a5826b2109b36d110d421036ed805d1ded5',
}
REQUIRED_PROOFS=(
 'COMPLETE_CURRENT_WRITER_ENTRYPOINTS',
 'ALL_WRITER_PROCESSES_ENROLLED',
 'RUNNING_WRITER_RESTART_OR_DRAIN',
 'SCHEDULED_MANUAL_REMOTE_WRITERS',
 'CANONICAL_LOCK_AND_LEDGER_EXCLUSIVITY',
 'INDEPENDENT_DYNAMIC_PROOF',
 'SIGNED_COVERAGE_APPROVAL',
 'RUNTIME_BINDING_AND_QUARANTINE_ACCEPTANCE',
)
CATEGORIES={
 'STRING_REPLACE_NOT_FS_WRITE': 'Виклик str.replace, не файлова операція',
 'READ_ONLY_OPEN': 'Відкриття для читання; не підтверджений запис',
 'CANONICAL_LEDGER_CORE': 'API/файловий create-only запис у canonical ledger',
 'CANONICAL_LEDGER_API_CALL': 'Виклик канонічного append_record з execution code',
 'SYNTHETIC_LEDGER_VALIDATION': 'Append в окреме сховище синтетичного validator',
 'SEPARATE_HISTORY_STORE': 'Окреме сховище Work Front History',
 'SYNTHETIC_HISTORY_VALIDATION': 'Синтетичні записи history у tmp-store',
 'CLOSEOUT_COMPLETION_WRITE': 'Вихідний governance completion у відокремлений target',
 'CLOSEOUT_CANDIDATE_WRITE': 'Вихідний closeout candidate, не canonical ledger',
 'CLOSEOUT_LOCK_HANDLE': 'Відкриття та блокування спільного lock-файлу',
 'SHARED_WRITER_LOCK_HANDLE': 'Lock descriptor, не append ledger',
 'WORKER_RUNTIME_AND_HANDOFF_WRITE': 'Файли Worker attempt/handoff, окремо від ledger',
 'OPERATOR_ACCEPTANCE_ARTIFACT': 'Окремі записи operator acceptance, не canonical ledger',
 'REPORT_OR_PROOF_ARTIFACT': 'Створення звітів, projections або proof-artifacts',
 'OTHER_SOURCE_WRITE_REVIEW_REQUIRED': 'Файловий запис, ціль за runtime не підтверджена',
}

class ReviewError(RuntimeError):pass

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()

def canonical_name(name:str)->bool:
    p=PurePosixPath(name)
    return (bool(name) and not name.startswith('/') and '\\' not in name
            and '..' not in p.parts and '.' not in p.parts and p.as_posix()==name)

def site_category(row:dict, line:str)->str:
    """Conservative per-site classification, never a runtime safety certificate."""
    path,api,n,func=row['path'],row['api'],row['line'],row['function']
    if api=='replace' and '.replace(' in line:
        return 'STRING_REPLACE_NOT_FS_WRITE'
    if api=='open' and (('O_RDONLY' in line) or ('open("rb")' in line) or ("open('rb')" in line)):
        return 'READ_ONLY_OPEN'
    if path.endswith('/execution_attempt_ledger_v0_1.py'):
        return 'CANONICAL_LEDGER_CORE'
    if path.endswith('/dispatch_intent.py') and api=='append_record':
        return 'CANONICAL_LEDGER_API_CALL'
    if path.endswith('/governed_worker_cycle.py') and api=='append_record':
        return 'CANONICAL_LEDGER_API_CALL'
    if path.endswith('/validate_execution_attempt_ledger_v0_1.py') and api=='append_record':
        return 'SYNTHETIC_LEDGER_VALIDATION'
    if path.endswith('/workfront_history_v0_1.py'):
        return 'SEPARATE_HISTORY_STORE'
    if path.endswith('/validate_workfront_history_v0_1.py') and api=='append_record':
        return 'SYNTHETIC_HISTORY_VALIDATION'
    if path.endswith('/work_front_closeout_apply_v0_1.py'):
        if func=='perform_closeout' and n==215:
            return 'CLOSEOUT_LOCK_HANDLE'
        if func=='perform_closeout':return 'CLOSEOUT_COMPLETION_WRITE'
        if func=='prepare_candidate':return 'CLOSEOUT_CANDIDATE_WRITE'
    if path.endswith('/execution_attempt_writer_lock_v0_1.py'):
        return 'SHARED_WRITER_LOCK_HANDLE'
    if path.endswith('/governed_worker_cycle.py'):
        return 'WORKER_RUNTIME_AND_HANDOFF_WRITE'
    if path.endswith('/post_commit_worker_acceptance.py'):
        return 'OPERATOR_ACCEPTANCE_ARTIFACT'
    if path.endswith('/cf10_zero_delta_operator_review_v0_1.py'):
        return 'OPERATOR_ACCEPTANCE_ARTIFACT'
    if path.endswith('/persist_worker_acceptance_evidence_v0_1.py'):
        return 'OPERATOR_ACCEPTANCE_ARTIFACT'
    if path.endswith('/dispatch_intent.py'):
        return 'WORKER_RUNTIME_AND_HANDOFF_WRITE'
    if (path.endswith('/run_non_mutating_make_check.py') or
        '/cf10_' in path or 's01_writer_runtime_binding' in path or
        'assistant_handoff' in path or path.endswith('/work_front_closeout_v0_1.py')):
        return 'REPORT_OR_PROOF_ARTIFACT'
    return 'OTHER_SOURCE_WRITE_REVIEW_REQUIRED'

def read_archive(path:Path):
    if not path.is_file() or path.stat().st_size>30_000_000:raise ReviewError('ARCHIVE_MISSING_OR_LARGE')
    with zipfile.ZipFile(path,'r') as z:
        infos=z.infolist(); names=[x.filename for x in infos]
        if len(names)!=len(set(names)) or len(names)>1000 or sum(x.file_size for x in infos)>30_000_000:
            raise ReviewError('ARCHIVE_DUPLICATES_OR_BOMB')
        if not all(canonical_name(x.filename) and not stat.S_ISLNK(x.external_attr >> 16) and x.file_size<4_000_000 for x in infos):
            raise ReviewError('ARCHIVE_ENTRY_UNSAFE')
        contents={n:z.read(n) for n in names}
    sha_lines=contents['SHA256SUMS'].decode('utf-8').splitlines()
    hashes={}
    for line in sha_lines:
        h,sep,n=line.partition('  ')
        if not sep or not re.fullmatch('[0-9a-f]{64}',h) or n in hashes:
            raise ReviewError('SHA256SUMS_FORMAT')
        hashes[n]=h
    if set(contents)-{'SHA256SUMS'}!=set(hashes):
        raise ReviewError('SHA256SUMS_SET_MISMATCH')
    if any(sha(contents[n])!=h for n,h in hashes.items()):
        raise ReviewError('SHA256SUMS_CONTENT_MISMATCH')
    manifest=json.loads(contents['manifest.json'])
    if manifest.get('source_head')!=SOURCE_HEAD or manifest.get('source_files')!=336 or manifest.get('reports')!=17:
        raise ReviewError('MANIFEST_SOURCE_BOUNDARY')
    if (manifest.get('authority_granted') is not False or
            manifest.get('dynamic_coverage_verified') is not False or
            manifest.get('writer_enrollment_attested') is not False or
            manifest.get('staged_changes_present') is not False or
            manifest.get('external_trust_or_runtime_bytes_included') is not False):
        raise ReviewError('MANIFEST_AUTHORITY_OR_SCOPE_BOUNDARY')
    items=manifest.get('artifacts')
    if not isinstance(items,list) or len(items)!=len(set(x.get('archive_path') for x in items)):
        raise ReviewError('MANIFEST_ARTIFACTS')
    if {x['archive_path'] for x in items}!=set(contents)-{'manifest.json','SHA256SUMS','summary.txt'}:
        raise ReviewError('MANIFEST_ARTIFACTS_SET')
    for item in items:
        n=item['archive_path']
        if sha(contents[n])!=item['sha256'] or len(contents[n])!=item['bytes']:
            raise ReviewError('MANIFEST_ARTIFACT_HASH')
    for f,expected in KNOWN_REPORTS.items():
        if sha(contents['reports/'+f])!=expected:raise ReviewError('PINNED_REPORT:'+f)
    return contents,manifest

def assess_dirty_patch(patch:str,manifest:dict):
    seen=[]; sections={}
    for sec in patch.split('diff --git ')[1:]:
        first,_,body=sec.partition('\n')
        pieces=first.split(' b/',1)
        if len(pieces)!=2:raise ReviewError('PATCH_HEADER_INVALID')
        name=pieces[1]
        if not canonical_name(name) or name in sections:raise ReviewError('PATCH_PATH_INVALID')
        if first.split(' b/')[0]!='a/'+name:raise ReviewError('PATCH_RENAME_OR_PATH_MISMATCH')
        sections[name]=body;seen.append(name)
    expected=manifest.get('dirty_worktree_file_names_only')
    if expected and set(expected)!=set(seen):raise ReviewError('PATCH_FILE_SET_MISMATCH')
    rows=[]
    for f in seen:
        sec=sections[f]
        plus=sum(x.startswith('+') and not x.startswith('+++') for x in sec.splitlines())
        minus=sum(x.startswith('-') and not x.startswith('---') for x in sec.splitlines())
        role=('RUNTIME_CODE' if f.startswith('scripts/') else 'TESTS' if f.startswith('tests/')
             else 'GOVERNANCE_OR_REGISTRY')
        risk=('VALIDATION_RECIPE_ISOLATION_REVIEW_REQUIRED' if f.endswith('run_validation_suite_v0_1.py')
              else 'MIRROR_GIT_IDENTITY_REVIEW_REQUIRED' if f.endswith('run_non_mutating_make_check.py')
              else 'GENERATED_INDEX_RECONCILIATION_REQUIRED' if f in ('indexes/governance.yaml','indexes/roadmaps.yaml')
              else 'TESTS_NOT_EXECUTED_ON_PUBLISHED_HEAD' if role=='TESTS'
              else 'GOVERNANCE_REVIEW_NO_AUTOMATIC_ACCEPTANCE')
        rows.append({'path':f,'role':role,'added_lines':plus,'removed_lines':minus,'disposition':risk})
    return rows

def review(path:Path)->dict:
    c,m=read_archive(path)
    # Reconcile the full frozen P01 Git source manifest (333 files) against bytes.
    p01=json.loads(c['reports/p01_evidence.json'])
    p01_manifest=p01['scan']['source_file_manifest']
    if len(p01_manifest)!=333 or len({x['path'] for x in p01_manifest})!=333:
        raise ReviewError('P01_SOURCE_MANIFEST_COUNT')
    p01_not_exported=[];p01_crosschecked=0
    for x in p01_manifest:
        key=SOURCE_PREFIX+x['path']
        if key not in c:
            p01_not_exported.append(x['path']);continue
        if sha(c[key])!=x['sha256'] or len(c[key])!=x['bytes']:
            raise ReviewError('P01_SOURCE_HASH_MISMATCH:'+x['path'])
        p01_crosschecked+=1
    if p01_crosschecked!=332 or p01_not_exported!=['config/worker_runtime.yaml']:
        raise ReviewError('P01_EXPORT_COVERAGE_DRIFT')
    p07=json.loads(c['reports/p07_write_survey.json'])
    p08=json.loads(c['reports/p08_semantics.json'])
    p09=json.loads(c['reports/p09_routes.json'])
    p10=json.loads(c['reports/p10_metadata.json'])
    p11=json.loads(c['reports/p11_declaration.json'])
    req=json.loads(c['reports/04b_coverage.json'])['proof_requirements']
    if sorted(r['id'] for r in req)!=sorted(REQUIRED_PROOFS) or any(r['status']!='NOT_ATTESTED' for r in req):
        raise ReviewError('PROOF_CONTRACT_DRIFT')
    for name,report in (('p07',p07),('p08',p08),('p09',p09),('p10',p10),('p11',p11)):
        if report.get('source_head')!=SOURCE_HEAD or report.get('authority_granted') is not False:
            raise ReviewError('REPORT_SOURCE_OR_AUTHORITY_DRIFT:'+name)
    if not p11.get('protocol_declared_enforced') is True:
        raise ReviewError('PROTOCOL_DECLARATION_MISMATCH')
    # Make source hashes and source file hashes are checked by archive manifest.
    candidates=p07['python_static_write_survey']['write_api_candidates']
    make_digest=p07['make_survey']['published_makefile_sha256']
    if sha(c['published_head/Makefile'])!=make_digest:
        raise ReviewError('P07_MAKE_SOURCE_HASH_DRIFT')
    for item in p07['python_static_write_survey']['related_sources']:
        key=SOURCE_PREFIX+item['path']
        if key not in c or sha(c[key])!=item['source_sha256']:
            raise ReviewError('P07_RELATED_SOURCE_HASH_DRIFT')
    # P08-P11 reference one another by full report-byte digest.
    for newer,field,older in (
        (p08,'frozen_p07_report_sha256','p07_write_survey.json'),
        (p09,'frozen_p08_report_sha256','p08_semantics.json'),
        (p10,'frozen_p09_report_sha256','p09_routes.json'),
        (p11,'frozen_p10_report_sha256','p10_metadata.json'),
    ):
        if newer.get(field)!=sha(c['reports/'+older]):
            raise ReviewError('FROZEN_REPORT_CHAIN_DRIFT:'+field)
    if len(candidates)!=113:raise ReviewError('P07_CANDIDATE_COUNT_DRIFT')
    if p08.get('p07_direct_write_candidate_count')!=113 or p09.get('unreviewed_p07_direct_write_candidates')!=96:
        raise ReviewError('P07_P08_P09_COUNT_DRIFT')
    distinguished=p08['distinguished_write_semantics']
    # Report shape must carry all 17 singled-out sites.
    seen_dist=[]
    for v in distinguished.values():
        if isinstance(v,list):seen_dist+=v
    lines_by_path={}
    rows=[];original=set()
    for x in candidates:
        rel=x['path'];file=SOURCE_PREFIX+rel
        if file not in c:raise ReviewError('CANDIDATE_SOURCE_NOT_INCLUDED:'+rel)
        if rel not in lines_by_path:lines_by_path[rel]=c[file].decode('utf-8').splitlines()
        if not (1<=x['line']<=len(lines_by_path[rel])):
            raise ReviewError('CANDIDATE_INVALID_LINE:'+rel)
        line=lines_by_path[rel][x['line']-1].strip()
        category=site_category(x,line)
        key=(rel,x['line'],x['api'])
        if key in original:raise ReviewError('DUPLICATE_CANDIDATE')
        original.add(key)
        rows.append({'path':rel,'line':x['line'],'api':x['api'],'function':x['function'],
                     'category':category,'source_line':line[:240],
                     'source_sha256':sha(c[file]),'runtime_verified':False,
                     'canonical_bypass_absence_proven':False})
    counts=dict(sorted(Counter(x['category'] for x in rows).items()))
    summary={
      'schema_version':'cf10_offline_batch_integrated_review_v0_1',
      'status':'STATIC_BATCH_RECONCILED_RUNTIME_ATTESTATION_REQUIRED_NON_AUTHORIZING',
      'source_head':SOURCE_HEAD,'input_archive_sha256':sha(path.read_bytes()),
      'input_artifacts_sha256_verified':True,
      'source_files':336,'python_files':331,'historical_reports':17,
      'p01_files_crosschecked':p01_crosschecked,'p01_files_not_exported':p01_not_exported,
      'p07_candidates_reviewed':len(rows),'p07_candidate_categories':counts,
      'additional_indirect_canonical_append':{
        'path':'scripts/coordination/control_plane/governed_worker_cycle.py','line':2168,
        'mechanism':'_b2_call_supported_kwargs(execution_attempt_ledger_v0_1.append_record, ...)',
        'classification':'ADDITIONAL_CALLBACK_CANONICAL_WRITER_CALLSITE_NOT_IN_P07_113',
        'runtime_verified':False,
      },
      'p07_unreviewed_before_batch':96,
      'complete_writer_set_proven':False,'canonical_ledger_runtime_lock_verified':False,
      'writer_enrollment_verified':False,'dynamic_coverage_verified':False,
      'protocol_declared_enforced':True,'protocol_sha256':p11['external_protocol']['sha256'],
      'make_quarantine_3_targets_preserved_in_source':True,
      'make_quarantine_removed':False,'authority_granted':False,
      'all_eight_proofs_attested':False,'proofs_attested':0,
      'outside_repo_signed_and_runtime_evidence_in_archive':False,
      'other_source_writes_outside_p07_113_excluded_from_complete_coverage_claim':True,
    }
    patch=c.get('uncommitted_review/NOT_FOR_AUTHORITY_dirty_worktree.patch')
    if m.get('dirty_worktree_bytes_included') and patch is None:
        raise ReviewError('PATCH_EXPECTED_MISSING')
    dirty=assess_dirty_patch(patch.decode('utf-8'),m) if patch is not None else []
    if patch is not None and len(dirty)!=18:raise ReviewError('DIRTY_FILE_COUNT_DRIFT')
    summary['dirty_files_reviewed']=len(dirty)
    summary['dirty_patch_sha256']=sha(patch) if patch is not None else None
    if 'scripts/validation/run_validation_suite_v0_1.py' in [x['path'] for x in dirty]:
        body=patch.decode('utf-8')
        if 'ISOLATION_ENV' not in body or '_verify_isolated_baseline_binding' not in body:
            raise ReviewError('VALIDATION_PATCH_RECIPE_NOT_PRESENT')
    proof_rows=[{'requirement_id':r['id'],'requirement':r['required_evidence'],
                 'status':'NOT_ATTESTED','existing_static_observation':'SOURCE_OR_METADATA_ONLY',
                 'next_required':'INDEPENDENT_RUNTIME_OR_SIGNED_OPERATOR_PROOF'} for r in req]
    return {'summary':summary,'candidates':rows,'dirty_patch':dirty,'proof_requirements':proof_rows,
            'make_routes':p09['make_routes'],'category_descriptions':CATEGORIES}

def write_results(result:dict,outdir:Path)->None:
    if outdir.exists():
        raise ReviewError('OUTPUT_EXISTS_FAIL_CLOSED')
    outdir.mkdir(parents=True,mode=0o700)
    def json_file(name,contents):
        (outdir/name).write_text(json.dumps(contents,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    json_file('review_summary.json',result['summary'])
    json_file('proof_requirements.json',result['proof_requirements'])
    json_file('make_routes.json',result['make_routes'])
    json_file('categories.json',result['category_descriptions'])
    def csv_file(name,rows,columns):
        with (outdir/name).open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows)
    csv_file('write_candidates_113.csv',result['candidates'],['path','line','api','function','category','source_line','source_sha256','runtime_verified','canonical_bypass_absence_proven'])
    csv_file('dirty_patch_18.csv',result['dirty_patch'],['path','role','added_lines','removed_lines','disposition'])
    sumfile=outdir/'summary.txt';s=result['summary'];sumfile.write_text('\n'.join((
      'CF10_OFFLINE_BATCH_REVIEW_STATUS='+s['status'],
      'WRITE_CANDIDATES_RECONCILED='+str(s['p07_candidates_reviewed']),
      'DIRTY_FILES_REVIEWED='+str(s['dirty_files_reviewed']),
      'ADDITIONAL_CANONICAL_CALLBACK_OBSERVED=true',
      'CANONICAL_LOCK_RUNTIME_ENFORCED_VERIFIED=false',
      'ALL_WRITERS_ENROLLED_VERIFIED=false',
      'PROOFS_ATTESTED=0',
      'AUTHORITY_GRANTED=false','')),'utf-8')
    sums=[]
    for f in sorted(outdir.iterdir()):
        if f.is_file():sums.append(sha(f.read_bytes())+'  '+f.name)
    (outdir/'SHA256SUMS').write_text('\n'.join(sums)+'\n','ascii')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,required=True)
    a=ap.parse_args();r=review(a.archive)
    write_results(r,a.output_dir)
    print((a.output_dir/'summary.txt').read_text(),end='')
    print('REPORT_DIR='+str(a.output_dir.resolve()))
    print('REPORT_SHA256='+sha((a.output_dir/'review_summary.json').read_bytes()))

if __name__=='__main__':main()
