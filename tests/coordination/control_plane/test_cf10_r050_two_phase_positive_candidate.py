"""r050: exact two-phase contract, real canonical positive/negative fixture."""
from __future__ import annotations
import json
import os
from pathlib import Path
import pytest
from scripts.coordination.control_plane import cf10_r050_two_phase_pilot_v0_1 as phase
from scripts.coordination.control_plane import cf10_r050_positive_candidate_fixture_v0_1 as fixture

ROOT = Path(__file__).resolve().parents[3]
TASK = phase.TASK
ATT = 'cf10-u180j-a050'
HEAD = 'a' * 40


def good_report():
    return dict(schema_version='cf10_r045_bounded_owner_pilot_admission_v0_1',
                profile='SINGLE_OWNER_BOUNDED_TASK70_CANDIDATE',
                task_prompt_id=TASK, attempt_id=ATT,
                status='PRECLAIM_EVIDENCE_CANDIDATE_NON_AUTHORIZING',
                preclaim_evidence_complete=True, admission_authorized=False,
                launch_allowed=False, production_cutover=False,
                worker_launched=False, automatic_retry=False,
                automatic_acceptance=False, automatic_publication=False,
                owner_pam_authenticated=False, operator_claim_consumed=False,
                legacy_independent_release='UNCHANGED_NOT_SATISFIED_BY_OWNER_PILOT',
                blockers=[])


def good_release():
    return dict(schema_version='cf10_r046_pilot_cutover_review_v0_1',
                status='PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED',
                task_prompt_id=TASK, attempt_id=ATT,
                checks={'r047_source_lineage':'EXACT_RAW_BYTES_BOUND'},
                blockers=[], launch_allowed=False)


def good_live():
    return {name:True for name in phase.REQUIRED_LAUNCH_OBSERVATIONS}


def test_preclaim_snapshot_is_not_authority():
    out=phase.preclaim(report=good_report(),source_head=HEAD,task=TASK,attempt=ATT)
    assert out['status']=='PRECLAIM_SNAPSHOT_CANDIDATE_NON_AUTHORIZING'
    assert len(out['r045_report_sha256'])==64
    assert not out['launch_allowed'] and not out['root_owned_preclaim_receipt_written']
    assert not out['preclaim_root_receipt_verified']


def test_repeat_preclaim_is_deterministic_but_not_attested():
    a=phase.preclaim(report=good_report(),source_head=HEAD,task=TASK,attempt=ATT)
    b=phase.preclaim(report=good_report(),source_head=HEAD,task=TASK,attempt=ATT)
    assert a==b and a['root_owned_preclaim_receipt_written'] is False


@pytest.mark.parametrize('key,wrong',[
    ('status','BLOCKED_PRECLAIM_EVIDENCE_NON_AUTHORIZING'),
    ('preclaim_evidence_complete',False),
    ('launch_allowed',True),
    ('production_cutover',True),
    ('admission_authorized',True),
    ('automatic_retry',True),
    ('automatic_publication',True),
    ('owner_pam_authenticated',True),
    ('attempt_id','cf10-u180j-a049'),
    ('task_prompt_id','wrong'),
    ('blockers',['SOME_BLOCKER']),
])
def test_preclaim_rejects_false_report(key,wrong):
    report=good_report();report[key]=wrong
    out=phase.preclaim(report=report,source_head=HEAD,task=TASK,attempt=ATT)
    assert out['status']=='BLOCKED_PRECLAIM_SNAPSHOT'
    assert out['r045_report_sha256'] is None
    assert out['blockers']


@pytest.mark.parametrize('task,attempt,head',[
    ('wrong',ATT,HEAD), (TASK,'bad',HEAD), (TASK,ATT,'bad')])
def test_preclaim_rejects_invalid_identity(task,attempt,head):
    out=phase.preclaim(report=good_report(),source_head=head,task=task,attempt=attempt)
    assert out['blockers']


def test_second_phase_all_true_still_not_authority():
    snapshot=phase.preclaim(report=good_report(),source_head=HEAD,task=TASK,attempt=ATT)
    out=phase.launch_window(snapshot=snapshot,release=good_release(),observations=good_live(),
                            task=TASK,attempt=ATT,source_head=HEAD)
    assert out['status']=='PILOT_LAUNCH_CANDIDATE_NON_AUTHORIZING'
    assert out['r045_recollected_after_cutover'] is False
    for name in ('launch_allowed','production_cutover','worker_launched',
                 'release_authorized','automatic_retry','automatic_acceptance',
                 'automatic_publication','legacy_release_authority_reused'):
        assert out[name] is False


@pytest.mark.parametrize('name',sorted(phase.REQUIRED_LAUNCH_OBSERVATIONS))
def test_second_phase_missing_one_observation_fails_closed(name):
    snapshot=phase.preclaim(report=good_report(),source_head=HEAD,task=TASK,attempt=ATT)
    live=good_live();live[name]=False
    out=phase.launch_window(snapshot=snapshot,release=good_release(),observations=live,
                            task=TASK,attempt=ATT,source_head=HEAD)
    assert out['status']=='BLOCKED_LAUNCH_WINDOW'
    assert 'LAUNCH_'+name.upper()+'_UNVERIFIED' in out['blockers']


def test_second_phase_requires_exact_observation_keys():
    snapshot=phase.preclaim(report=good_report(),source_head=HEAD,task=TASK,attempt=ATT)
    live=good_live();live['extra']=True
    out=phase.launch_window(snapshot=snapshot,release=good_release(),observations=live,
                            task=TASK,attempt=ATT,source_head=HEAD)
    assert 'LAUNCH_OBSERVATIONS_EXACT_FIELDS_REQUIRED' in out['blockers']


@pytest.mark.parametrize('field,wrong',[
    ('status','BLOCKED_PENDING_PILOT_RELEASE_EVIDENCE'),
    ('blockers',['no']),
    ('attempt_id','cf10-u180j-a049'),
    ('launch_allowed',True),
    ('checks',{'r047_source_lineage':'UNPROVEN_OR_BLOCKED'}),
    ('checks','untrusted'),
])
def test_second_phase_rejects_fake_release(field,wrong):
    snapshot=phase.preclaim(report=good_report(),source_head=HEAD,task=TASK,attempt=ATT)
    release=good_release();release[field]=wrong
    out=phase.launch_window(snapshot=snapshot,release=release,observations=good_live(),
                            task=TASK,attempt=ATT,source_head=HEAD)
    assert 'EXACT_R046_R047_PROOFS_NOT_VERIFIED' in out['blockers']


def test_second_phase_rejects_preclaim_source_drift():
    snapshot=phase.preclaim(report=good_report(),source_head=HEAD,task=TASK,attempt=ATT)
    out=phase.launch_window(snapshot=snapshot,release=good_release(),observations=good_live(),
                            task=TASK,attempt=ATT,source_head='b'*40)
    assert 'PRECLAIM_SOURCE_OR_IDENTITY_DRIFT' in out['blockers']


def test_second_phase_rejects_untrusted_snapshot():
    out=phase.launch_window(snapshot={},release=good_release(),observations=good_live(),
                            task=TASK,attempt=ATT,source_head=HEAD)
    assert 'PRECLAIM_SNAPSHOT_INVALID' in out['blockers']


def test_requirements_advertises_unimplemented_activation():
    x=phase.requirements()
    assert x['preclaim_root_receipt_writer_implemented'] is False
    assert x['source_bound_pilot_make_backend_activation_implemented'] is False
    assert x['launch_allowed'] is False


@pytest.mark.parametrize('variant,expected',[
    ('positive','PASS_POSITIVE_DISPOSABLE_CANDIDATE_NON_AUTHORIZING'),
    ('missing_terminal','PASS_NEGATIVE_TERMINAL_ABSENCE_BLOCKED'),
    ('drifted_result','PASS_NEGATIVE_RESULT_DRIFT_BLOCKED')])
def test_disposable_fixture_real_canonical_validators(variant,expected):
    if os.geteuid()!=0:pytest.skip('root-only fixture, run on s01 as root')
    out=fixture.run(root=ROOT,variant=variant)
    assert out['status']==expected
    assert out['real_envelope_and_resume_validators_used'] is True
    assert out['create_only_result_replay_blocked'] is True
    assert out['production_cutover'] is False
    assert out['worker_result_accepted'] is False
    assert out['root_pilot_proof_issued'] is False
    assert out['actual_worker_end_to_end_proven'] is False


def test_disposable_fixture_invalid_variant_fails_before_mutation():
    with pytest.raises(fixture.FixtureBlocked,match='UNKNOWN_FIXTURE_VARIANT'):
        fixture.run(root=ROOT,variant='launch-real-worker')


def test_fixture_code_has_no_live_launcher_or_release_writer():
    code=Path(fixture.__file__).read_text()
    assert 'launch_after_owner_claim(' not in code
    assert 'systemctl start' not in code
    assert "dir='/var/tmp'" in code
    assert 'recovery.identity_from_source' in code
    assert 'durable.record_terminal' in code
    assert 'independent._assess' in code


def test_makefile_legacy_gate_remains_quarantined():
    make=(ROOT/'Makefile').read_text()
    assert 'CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND' in make
    assert 'governed-worker-cycle-advance: cf10-s01-runtime-launch-preflight' in make
    backend=(ROOT/'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py').read_text()
    assert 'LIVE_CUTOVER_ENABLED=False' in backend
