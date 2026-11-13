"""R073: verify archived experiment bytes and provenance; no production authority.

Historical R060/a050 and R065/a051 evidence is NOT a production a053 run.
This module never authenticates a server evidence producer or attests cryptographic
origin. A separately authenticated operator must review that limitation before
any bounded, non-authorizing R046/R047 candidate issuance.
"""
from __future__ import annotations
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

HEAD = 'e790ed596758c9ebfe101c6d5892d64901a95134'
ATT = 'cf10-u180j-a053'
TASK = 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
OLD_HEAD = '74a81f77e59c54522d95822bb662804bb573e296'
OLD_ATT = 'cf10-r060fixture-288dca72af2ae5d1ff706110-a060'
SRC = {
 'R065_ORIGINAL.zip':'ddc42277626320cd53d7cade4296d51c35df6b203f88474780e959bd7175a187',
 'R071_PARTIAL_DIAG_ORIGINAL.zip':'b8f4d83550ed71212235bcef7b45cd96d36ce007f2c1b7c0b13babdf44ec9f92',
 'R071B_ORIGINAL.zip':'9853f7e99dee3ef3b7900ea5fa104ee4ff48ec9111f8fdb93874c4cb2172a174',
 'R072C_ORIGINAL.zip':'be132aa6b50535aa2e656571fbb69ff9231c0bb8f82c4c4ddd7c6646729c9868',
}
KINDS = (
 'DISPOSABLE_SYSTEMD_CONTROLLER_LOSS_RECOVERY',
 'TMP_UNAVAILABLE_END_TO_END',
 'INDEPENDENT_FINALIZER_GATE_FIXTURE',
 'SOURCE_AND_WRITER_BOUNDARY',
)
FIELDS = {
 KINDS[0]: ('real_systemd_controller_sigkill_observed','service_survived_controller_death',
            'recovery_without_terminal_witness_fail_closed','automatic_retry_absent',
            'unit_retired_after_proof','fixture_cleanup_verified'),
 KINDS[1]: ('project_tmp_unavailable_during_disposable_execution','disposable_execution_completed',
            'recovery_completed_without_project_tmp','canonical_durable_state_independent_of_project_tmp',
            'project_tmp_unavailability_isolated_from_live_server'),
 KINDS[2]: ('preterminal_root_claim_crosschecked','kernel_systemd_readback_crosschecked',
            'candidate_result_independently_validated','invalid_result_did_not_append_success_terminal',
            'immutable_terminal_replay_not_refinalized'),
 KINDS[3]: ('canonical_task70_and_work_front_bound','published_head_and_frozen_source_equal',
            'writer_protocol_enforced','one_shot_claim_unconsumed',
            'canonical_ledger_has_no_started_record_for_attempt','cf10_systemd_quiescence_observed'),
}
class EvidenceBlocked(ValueError): pass

def require(cond, code):
    if not cond: raise EvidenceBlocked('R073_'+code)

def sha(b):return hashlib.sha256(b).hexdigest()

def canonical(obj):return (json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()

def strict_json(blob):
    def unique(pairs):
        d={}
        for k,v in pairs:
            require(k not in d,'DUPLICATE_JSON_KEY');d[k]=v
        return d
    return json.loads(blob,object_pairs_hook=unique,parse_constant=lambda x:require(False,'JSON_CONSTANT'))

def unzip(raw, max_files=100, max_total=20_000_000):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos=z.infolist()
        require(0<len(infos)<=max_files,'ZIP_ENTRIES')
        require(z.testzip() is None,'ZIP_CRC')
        names=[e.filename for e in infos]
        require(len(names)==len(set(names)),'ZIP_DUPLICATE')
        require(sum(e.file_size for e in infos)<=max_total,'ZIP_UNCOMPRESSED_SIZE')
        for e in infos:
            require(not e.is_dir() and not e.filename.startswith('/') and '..' not in Path(e.filename).parts and '\\' not in e.filename and not e.filename.startswith('.'),'ZIP_PATH')
            require(((e.external_attr>>16)&0o170000)!=0o120000,'ZIP_SYMLINK')
        return {i.filename:z.read(i) for i in infos}

def verify_shas(items, name):
    manifest=items[name].decode('ascii','strict')
    listed={}
    for line in manifest.splitlines():
        require('  ' in line,'HASH_MANIFEST_FORMAT')
        digest,path=line.split('  ',1)
        require(re.fullmatch('[0-9a-f]{64}',digest) is not None and path not in listed,'HASH_MANIFEST_NAME')
        listed[path]=digest
    require(set(listed)==set(items)-{name},'HASH_MANIFEST_COMPLETE')
    for file,h in listed.items(): require(sha(items[file])==h,'HASH_MISMATCH_'+file)

def proof_evidence(folder:Path):
    blobs={}
    for name,h in SRC.items():
        p=folder/name
        require(p.is_file() and not p.is_symlink() and p.stat().st_size<2_000_000,'MISSING_OR_UNSAFE_'+name)
        blob=p.read_bytes();require(sha(blob)==h,'PIN_MISMATCH_'+name)
        blobs[name]=blob
    hist=unzip(blobs['R065_ORIGINAL.zip'])
    part=unzip(blobs['R071_PARTIAL_DIAG_ORIGINAL.zip'])
    prior=unzip(blobs['R071B_ORIGINAL.zip'])
    final=unzip(blobs['R072C_ORIGINAL.zip'])
    verify_shas(prior,'CAPSULE_SHA256SUMS.txt')
    verify_shas(final,'CAPSULE_SHA256SUMS.txt')
    part_m=strict_json(part['DIAGNOSTIC_MANIFEST.json'])
    require(part_m['files_sha256']=={k:sha(v) for k,v in part.items() if k!='DIAGNOSTIC_MANIFEST.json'},'PARTIAL_SHA')
    require(part_m['status']=='PARTIAL_NON_AUTHORIZING_DIAGNOSTIC','PARTIAL_SCOPE')
    require(part_m['attempt_id']==ATT and part_m['source_head']==HEAD,'PARTIAL_IDENTITY')
    require(prior['r071_systemd_original_verified.json']==part['systemd_controller_loss.json'],'SYSTEMD_BYTES_NOT_ORIGINAL')
    require(final['r071b_original_review.json']==prior['r071b_review.json'],'R071B_BYTES_NOT_ORIGINAL')
    r071b=strict_json(prior['r071b_review.json']);r072=strict_json(final['r072_report.json'])
    sysd=strict_json(part['systemd_controller_loss.json'])
    tmp=strict_json(final['tmp_e2e_report.json']);rec=strict_json(final['lifecycle_recovery.json'])
    fin=strict_json(final['finalizer_report.json']);started=strict_json(final['lifecycle_started.json'])
    terminal=strict_json(final['lifecycle_terminal.json']);replay=r071b['ledger_replay']
    # Traceable provenance checks; no trust in an unbound all-true observations dict.
    with zipfile.ZipFile(io.BytesIO(hist['R062_INTAKE_RESULT.zip'])) as z:
        cover=strict_json(z.read('COVERAGE.json'))
    require(cover['schema_version'].startswith('cf10_r062_') and not cover['producer_identity_authenticated'],'R062_SCOPE')
    require(cover['counts'][KINDS[0]]['observed']==6,'HISTORICAL_SYSTEMD_COVERAGE')
    for field in FIELDS[KINDS[0]]:
        require(cover['observations'][KINDS[0]][field]['status']=='OBSERVED_NOT_ISSUER_AUTHENTICATED','HISTORICAL_SYSTEMD_UNSUPPORTED_'+field)
    require(sysd['status']=='PASS_ACTUAL_DISPOSABLE_SYSTEMD_CONTROLLER_LOSS','SYSTEMD_STATUS')
    require(sysd['schema']=='cf10_r071_fresh_real_systemd_controller_loss_v0_1','SYSTEMD_SCHEMA')
    require(sysd['controller_sigkill_observed'] is True and sysd['service_survived_controller_death'] is True
       and sysd['service_main_pid_before_after_equal'] is True and sysd['unit_cleanup_verified'] is True,'SYSTEMD_CORE')
    require(sysd['automatic_retry'] is False and sysd['production_worker_launched'] is False and sysd['not_canonical_worker_service'] is True,'SYSTEMD_BOUNDARY')
    require(sysd['before']['MainPID']==sysd['after_controller_sigkill']['MainPID']==str(sysd['probe_started']['pid'])
            and sysd['retired']['LoadState']=='not-found' and sysd['retired']['ActiveState']=='inactive','SYSTEMD_LIFECYCLE')
    require(sysd['probe_finished']['pid']==sysd['probe_started']['pid'] and sysd['probe_finished']['monotonic_ns']>sysd['probe_started']['monotonic_ns'],'SYSTEMD_PROBE')
    require(tmp['schema']=='cf10_r072_tmp_full_disposable_e2e_v1' and tmp['status']=='PASS_REAL_DISPOSABLE_EXECUTE_RECOVER_WITH_TMP_UNAVAILABLE','TMP_STATUS')
    for field in ('separate_exec_and_recovery_processes','project_tmp_readonly_masked_in_private_namespace','current_a053_preclaim_readback','r025_claim_readback','r035_terminal_readback'):
        require(tmp[field] is True,'TMP_'+field)
    require(r071b['tmp_namespace']['root_durable_paths_outside_project_tmp'] is True,'TMP_DURABLE_OUTSIDE_PROJECT_TMP')
    require(tmp['namespace_host']!=tmp['namespace_private'] and rec['namespace']==tmp['namespace_private'],'TMP_NAMESPACE')
    require(rec['status']=='PASS_SEPARATE_PROCESS_RECOVERY_WITH_TMP_MASK' and rec['execution_pid']!=rec['recovery_pid']
            and rec['recovery_read_only'] is True and rec['tampered_copy_rejected'] is True
            and rec['terminal_replay_rejected'] is True,'TMP_RECOVERY')
    for name in ('seed','result','started','terminal'):
        require(sha(final['lifecycle_'+name+'.json'])==rec['durable_files_sha256'][name+'.json']
                ==tmp['durable_recovery_files_sha256'][name+'.json'],'TMP_DURABLE_HASH_'+name)
    require(started['attempt_id']==ATT and started['head']==HEAD and terminal['attempt_id']==ATT and terminal['head']==HEAD,'TMP_IDENTITY')
    require(terminal['started_sha256']==sha(final['lifecycle_started.json']) and terminal['result_sha256']==sha(final['lifecycle_result.json']),'TMP_TERMINAL_LINKS')
    require(tmp['production_worker_launched'] is False and not tmp['actual_production_worker_lifecycle_run'],'TMP_NONWORKER')
    require(fin['schema']=='cf10_r072_independent_finalizer_fixture_v1' and fin['status']=='PASS_R036_R037_REAL_CODE_DISPOSABLE_FIXTURE','FINALIZER_STATUS')
    for field in ('current_r036_and_r037_code_executed','current_canonical_s4_validators_executed',
                  'current_r026_systemctl_and_kernel_readback_not_mocked','positive_candidate_verified',
                  'negative_missing_started_rejected','negative_tampered_result_rejected'):
        require(fin[field] is True,'FINALIZER_'+field)
    require(fin['current_attempt_id']==ATT and fin['current_source_head']==HEAD and fin['historical_head']==OLD_HEAD
            and fin['historical_attempt_id']==OLD_ATT,'FINALIZER_IDENTITY')
    require(fin['canonical_finalizer_append_executed'] is False and fin['independent_producer_authenticated'] is False
            and fin['full_production_end_to_end_attested'] is False,'FINALIZER_LIMITS')
    require(fin['r035_pre_sha256']==strict_json(final['old_fixture_identity.json'])['pre_sha']
            and fin['r035_post_sha256']==strict_json(final['old_fixture_identity.json'])['post_sha'],'FINALIZER_RECEIPT_BIND')
    require(replay['status']=='PASS_CURRENT_CANONICAL_LEDGER_REPLAY_FIXTURE' and replay['replay_identical_blocked'] is True
            and replay['replay_altered_blocked'] is True and replay['bytes_unchanged'] is True
            and replay['production_ledger_modified'] is False,'FINALIZER_REPLAY')
    require(r072['status']=='PASS_DISPOSABLE_EVIDENCE_NOT_RELEASE' and r072['head']==HEAD
            and r072['attempt']==ATT and r072['owner_claim_consumed'] is False
            and r072['release_issued'] is False,'R072_SCOPE')
    require(r072['historical_r065_sha256']==SRC['R065_ORIGINAL.zip'] and r072['historical_r071b_sha256']==SRC['R071B_ORIGINAL.zip'],'R072_ARCHIVE_BIND')
    require(r072['new_tmp_e2e'] is True and r072['current_r036_r037_fixture'] is True,'R072_COMPONENTS')
    require(r071b['attempt_id']==ATT and r071b['source_head']==HEAD and r071b['owner_claim_consumed'] is False,'R071B_SCOPE')
    for marker in ('before','after'):
        s=r072[marker]
        require(s['head']==HEAD and s['attempt']==ATT and s['state']=='READY_FOR_WORKER_LAUNCH'
                and s['claim']=='UNCONSUMED' and s['ledger_records']==0
                and s['preclaim']=='PRECLAIM_ROOT_RECEIPT_VERIFIED_NON_AUTHORIZING'
                and s['nine_release_files_missing'] is True and s['worker_started'] is False,'R072_'+marker)
        require(sum(v is True for v in s['gates'].values())==13 and s['gates']['release_candidate_raw_lineage_verified'] is False,'R072_GATES')
    # Full historical coverage is not used to assert success for current HEAD.
    return {'schema':'cf10_r073_disposable_evidence_byte_review_v0_1','status':'PASS_ARCHIVED_BYTES_AND_REPORTED_OUTCOMES_NOT_PRODUCER_AUTHENTICATED',
       'attempt_id':ATT,'source_head':HEAD,'historical_source_head':OLD_HEAD,
       'archive_sha256':dict(SRC),'observation_sources':{
          KINDS[0]:['R071_PARTIAL_DIAG_ORIGINAL.zip:systemd_controller_loss.json','R065_ORIGINAL.zip:R062/COVERAGE.json (historical fail-closed recovery)'],
          KINDS[1]:['R072C_ORIGINAL.zip:tmp_e2e_report.json','R072C_ORIGINAL.zip:lifecycle_*','R072C_ORIGINAL.zip:lifecycle_recovery.json'],
          KINDS[2]:['R072C_ORIGINAL.zip:finalizer_report.json (historical R035 receipts, injected disposable dependencies)','R071B_ORIGINAL.zip:r071b_review.json:ledger_replay'],
          KINDS[3]:['FRESH_SERVER_R052_OBSERVERS_REQUIRED'],
       },
       'producer_cryptographically_authenticated':False,
       'historical_fixture_promoted_to_live_worker_proof':False,
       'canonical_production_finalizer_executed':False,
       'release_issued':False,
       'worker_launched':False}
