"""R074 operator workflow regression: pure decision and Make-root integration."""
from __future__ import annotations
import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'scripts/coordination/control_plane/cf10_pilot_operator_workflow_v0_1.py'
spec = importlib.util.spec_from_file_location('cf10_r074_doctor', SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def ready():
    return {'attempt_id':'cf10-u180j-a053','state':'READY_FOR_WORKER_LAUNCH',
      'claim':'UNCONSUMED','ledger_records':0,'frozen_source_current':True,
      'root_receipt_store':'PASS','logs':'PASS',
      'preclaim':'PRECLAIM_ROOT_RECEIPT_VERIFIED_NON_AUTHORIZING',
      'preclaim_blockers':[], 'proof':'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED',
      'proof_lineage':'EXACT_RAW_BYTES_BOUND','proof_blockers':[]}


def test_complete_is_separate_one_shot_not_launch():
    result=mod.next_route(ready())
    assert result['route']=='READY_FOR_EXPLICIT_ONE_SHOT_OWNER_PAM'
    assert result['automatic_retry'] is False
    assert result['worker_launch_invoked'] is False
    assert result['operator_authority_granted'] is False


def test_missing_proof_fail_closed():
    d=ready();d['proof_blockers']=['MISSING']
    assert mod.next_route(d)['route']=='PROOF_LINEAGE_BLOCKED'


def test_unknown_claim_never_retried():
    d=ready();d['claim']='UNKNOWN'
    assert mod.next_route(d)['route']=='CLAIM_NOT_FREE_FAIL_CLOSED'


def test_consumed_claim_and_observe_are_not_relaunch():
    d=ready();d['state']='OBSERVE_WORKER';d['claim']='CONSUMED_NO_RETRY';d['ledger_records']=1
    assert mod.next_route(d)['route']=='WORKER_IN_PROGRESS_OR_RESULT_PENDING'
    d['state']='AWAITING_OPERATOR_REVIEW'
    assert mod.next_route(d)['route']=='S3_POSTWORKER_REVIEW_ONLY'


def test_stale_head_precedes_all_actions():
    d=ready();d['frozen_source_current']=False
    assert mod.next_route(d)['route']=='FROZEN_HEAD_MISMATCH_NO_REBIND'


def test_no_side_effects_or_new_launcher():
    source=SRC.read_text('utf8')
    tree=ast.parse(source)
    # Prevent accidental introduction of a second mutation channel.
    assert 'subprocess' not in source
    assert 'cf10-s01-pilot-owner-run' not in source
    assert 'launch_once(' not in source
    assert 'os.system' not in source
    assert 'cf10-r051-preclaim-issue' not in source
    assert all(not isinstance(node,ast.Import) or all(x.name!='subprocess' for x in node.names)
               for node in ast.walk(tree))


def test_make_absolute_root_is_durable_fix():
    text=(ROOT/'Makefile').read_text('utf8')
    assert 'CF10_PILOT_ARGS = --root "$(CURDIR)"' in text
    assert 'cf10-pilot-launch-once:' in text
    assert 'resume $(CF10_PILOT_ARGS) --launch-once' in text
    assert 'cf10-pilot-operator-doctor:' in text


def test_machine_passport_exists():
    import json
    path=ROOT/'coordination/continuity/cf10_pilot_operator_chain_v0_1.json'
    doc=json.loads(path.read_text('utf8'))
    assert doc['schema_version']=='cf10_pilot_operator_chain_v0_1'
    assert doc['source_change_requires_new_attempt_if_frozen'] is True
    assert doc['automatic_retry'] is False
    assert doc['worker_launch_auto'] is False
    assert doc['temporary_directory_is_runtime_dependency'] is False


def test_doctor_includes_actual_manifest_preclaim_before_ready_pam():
    source=SRC.read_text('utf8')
    assert 'pilot.assert_owner_preclaim_runtime(' in source
    assert source.index('pilot.assert_owner_preclaim_runtime(') > source.index('all(facts.values())')
