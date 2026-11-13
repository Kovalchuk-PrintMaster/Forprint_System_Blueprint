"""r051: exact root-owned PRECLAIM storage and phase-separated readback."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat

import pytest
from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as r
from scripts.coordination.control_plane import cf10_r050_two_phase_pilot_v0_1 as phase
from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as release

TASK = phase.TASK
ATT = 'cf10-u180j-a051'
HEAD = 'a' * 40


def good_report():
    return {'schema_version':'cf10_r045_bounded_owner_pilot_admission_v0_1',
            'profile':'SINGLE_OWNER_BOUNDED_TASK70_CANDIDATE',
            'task_prompt_id':TASK,'attempt_id':ATT,
            'status':'PRECLAIM_EVIDENCE_CANDIDATE_NON_AUTHORIZING',
            'preclaim_evidence_complete':True,'admission_authorized':False,
            'launch_allowed':False,'production_cutover':False,
            'worker_launched':False,'automatic_retry':False,
            'automatic_acceptance':False,'automatic_publication':False,
            'owner_pam_authenticated':False,'operator_claim_consumed':False,
            'legacy_independent_release':'UNCHANGED_NOT_SATISFIED_BY_OWNER_PILOT',
            'blockers':[]}


@pytest.fixture
def harness(tmp_path, monkeypatch):
    if os.geteuid() != 0:
        pytest.skip('Root-owned record requires root, as on s01')
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as r045
    monkeypatch.setattr(r, 'PROJECT', tmp_path)
    monkeypatch.setattr(r, '_exact_source_bytes', lambda root, head: None)
    monkeypatch.setattr(console, 'source_guard', lambda _: HEAD)
    monkeypatch.setattr(r045, 'collect', lambda *a, **kw: good_report())
    monkeypatch.setattr(r, '_state_fd', lambda: os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY))
    return tmp_path


def _sealed(harness):
    return r.issue(root=harness,task=TASK,attempt=ATT,confirm=r.ISSUE_CONFIRM)


def _file(harness):
    return harness/r._name(ATT)


def test_seal_readback_create_only_and_not_authority(harness):
    out=_sealed(harness)
    assert out['status']=='SEALED_ROOT_PRECLAIM_NON_AUTHORIZING'
    assert out['launch_allowed'] is False and out['permission_consumed'] is False
    path=_file(harness)
    assert path.is_file() and stat.S_IMODE(path.stat().st_mode)==0o600
    doc=r._decode(path.read_bytes())
    assert doc['root_receipt_is_launch_authority'] is False
    assert r._canonical(doc)==path.read_bytes()
    verified=r.inspect(root=harness,task=TASK,attempt=ATT,head=HEAD)
    assert verified['status']=='PRECLAIM_ROOT_RECEIPT_VERIFIED_NON_AUTHORIZING'
    assert verified['preclaim_root_receipt_verified'] is True
    assert verified['r045_recollected_after_cutover'] is False
    original=path.read_bytes()
    with pytest.raises(r.PreclaimBlocked,match='PRECLAIM_ALREADY_EXISTS_NO_REWRITE'):
        _sealed(harness)
    assert path.read_bytes()==original


def test_source_bytes_must_match_published_git_before_write(harness, monkeypatch):
    monkeypatch.setattr(r, '_exact_source_bytes',
                        lambda root, head: (_ for _ in ()).throw(r.PreclaimBlocked('PRECLAIM_CRITICAL_SOURCE_DRIFT')))
    with pytest.raises(r.PreclaimBlocked, match='PRECLAIM_CRITICAL_SOURCE_DRIFT'):
        _sealed(harness)
    assert not _file(harness).exists()


def test_no_report_or_unready_never_creates_record(harness,monkeypatch):
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as r045
    report=good_report();report['status']='BLOCKED_PRECLAIM_EVIDENCE_NON_AUTHORIZING'
    monkeypatch.setattr(r045,'collect',lambda *a,**kw:report)
    with pytest.raises(r.PreclaimBlocked, match='R045_PRECLAIM_NOT_READY'):
        _sealed(harness)
    assert not _file(harness).exists()


def test_invalid_confirm_never_calls_r045(harness,monkeypatch):
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as r045
    monkeypatch.setattr(r045,'collect',lambda *a,**kw:pytest.fail('r045 should not run'))
    with pytest.raises(r.PreclaimBlocked,match='ROOT_CANONICAL_EXPLICIT_CONFIRM_REQUIRED'):
        r.issue(root=harness,task=TASK,attempt=ATT,confirm='')
    assert not _file(harness).exists()


def test_source_drift_during_capture_blocks_before_write(harness,monkeypatch):
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    heads=iter([HEAD,'b'*40])
    monkeypatch.setattr(console,'source_guard',lambda _:next(heads))
    with pytest.raises(r.PreclaimBlocked,match='SOURCE_DRIFT_DURING_PRECLAIM'):
        _sealed(harness)
    assert not _file(harness).exists()


@pytest.mark.parametrize('change',[
    lambda doc: doc.__setitem__('attempt_id','cf10-u180j-a052'),
    lambda doc: doc.__setitem__('source_head','b'*40),
    lambda doc: doc.__setitem__('permission_consumed',True),
    lambda doc: doc.__setitem__('root_receipt_is_launch_authority',True),
    lambda doc: doc.__setitem__('automatic_retry',True),
    lambda doc: doc.__setitem__('production_cutover',True),
    lambda doc: doc.__setitem__('worker_launched',True),
    lambda doc: doc['r045_report'].__setitem__('blockers',['BAD']),
    lambda doc: doc['snapshot'].__setitem__('r045_report_sha256','0'*64),
    lambda doc: doc.__setitem__('profile','OTHER'),
    lambda doc: doc.__setitem__('unexpected_authority','YES'),
])
def test_tampered_receipt_refused(harness,change):
    _sealed(harness)
    path=_file(harness)
    doc=r._decode(path.read_bytes())
    change(doc)
    path.write_bytes(r._canonical(doc))
    result=r.inspect(root=harness,task=TASK,attempt=ATT,head=HEAD)
    assert result['preclaim_root_receipt_verified'] is False
    assert result['launch_allowed'] is False


@pytest.mark.parametrize('raw',[
    b'{"schema_version":1,"schema_version":2}\n',
    b'{"bad":true}\n',
    b'{"bad":true}',
    b'{"bad":NaN}\n',
    b'not json\n',
])
def test_noncanonical_or_duplicate_json_fails(harness,raw):
    _sealed(harness)
    _file(harness).write_bytes(raw)
    assert r.inspect(root=harness,task=TASK,attempt=ATT,head=HEAD)['blockers']


def test_wrong_mode_or_symlink_untrusted(harness):
    _sealed(harness)
    path=_file(harness)
    path.chmod(0o644)
    assert r.inspect(root=harness,task=TASK,attempt=ATT,head=HEAD)['blockers']
    path.unlink();path.symlink_to('/etc/passwd')
    assert r.inspect(root=harness,task=TASK,attempt=ATT,head=HEAD)['blockers']


def test_hardlink_and_oversized_refused(harness):
    _sealed(harness)
    path=_file(harness)
    os.link(path,harness/'alias.json')
    assert r.inspect(root=harness,task=TASK,attempt=ATT,head=HEAD)['blockers']
    (harness/'alias.json').unlink()
    path.write_bytes(b'A'*(r.MAX_BYTES+1))
    assert r.inspect(root=harness,task=TASK,attempt=ATT,head=HEAD)['blockers']


def test_stale_head_or_wrong_attempt_blocked(harness):
    _sealed(harness)
    assert r.inspect(root=harness,task=TASK,attempt=ATT,head='b'*40)['blockers']
    assert r.inspect(root=harness,task=TASK,attempt='cf10-u180j-a052',head=HEAD)['blockers']
    assert r.inspect(root=harness,task='not-task70',attempt=ATT,head=HEAD)['blockers']


def test_write_failure_leaves_create_once_file_to_block_retry(harness,monkeypatch):
    original=r._write_create_once
    def fail_after_create(folder,name,raw):
        original(folder,name,raw)
        raise r.PreclaimBlocked('SIMULATED_FAILURE_AFTER_DURABLE_WRITE')
    monkeypatch.setattr(r,'_write_create_once',fail_after_create)
    with pytest.raises(r.PreclaimBlocked,match='SIMULATED_FAILURE'):
        _sealed(harness)
    assert _file(harness).exists()
    monkeypatch.setattr(r,'_write_create_once',original)
    with pytest.raises(r.PreclaimBlocked,match='PRECLAIM_ALREADY_EXISTS_NO_REWRITE'):
        _sealed(harness)


def test_r046_launch_window_does_not_recollect_r045(harness,monkeypatch):
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as r045
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_r047_pilot_proof_lineage_v0_1 as lineage
    _sealed(harness)
    monkeypatch.setattr(r045,'collect',lambda *a,**kw:pytest.fail('RECOLLECT_R045_FORBIDDEN'))
    monkeypatch.setattr(release,'_trusted_folder',lambda _:os.open('/dev/null',os.O_RDONLY))
    monkeypatch.setattr(release,'_trusted_file',lambda fd,n:json.dumps({'proofs': {k:{'relative_file':'placeholder'} for k in release.PROOF_TYPES}}).encode() if n.startswith('owner_pilot_release') else b'{}')
    monkeypatch.setattr(lineage,'verify_sources',lambda **kw:[])
    monkeypatch.setattr(release,'validate_candidate',lambda *args,**kw:[])
    result=release.inspect(root=Path('/srv/software_development/forprint-project/forprint_system_blueprint'),
                           task=TASK,attempt=ATT,phase='LAUNCH_WINDOW')
    # r051 receives canonical project root from r046; on isolated temp store
    # it must block rather than trust fixture solely by passed flags.
    assert result['launch_allowed'] is False
    assert result['production_cutover'] is False
    assert 'r045' not in result['checks']
    assert result['checks'].get('r051') == 'BLOCKED_PRECLAIM_ROOT_RECEIPT'


def test_r046_launch_window_with_verified_root_seal(monkeypatch):
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as r045
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    monkeypatch.setattr(console,'source_guard',lambda _:HEAD)
    monkeypatch.setattr(r045,'collect',lambda *a,**kw:pytest.fail('RECOLLECT_R045_FORBIDDEN'))
    monkeypatch.setattr(r,'inspect',lambda **kw:{'status':'PRECLAIM_ROOT_RECEIPT_VERIFIED_NON_AUTHORIZING','preclaim_root_receipt_verified':True})
    monkeypatch.setattr(release,'_trusted_folder',lambda _:os.open('/dev/null',os.O_RDONLY))
    monkeypatch.setattr(release,'_trusted_file',lambda fd,n:json.dumps({'proofs': {k:{'relative_file':'proof'} for k in release.PROOF_TYPES}}).encode() if n.startswith('owner_pilot_release') else b'{}')
    from scripts.coordination.control_plane import cf10_r047_pilot_proof_lineage_v0_1 as lineage
    monkeypatch.setattr(lineage,'verify_sources',lambda **kw:[])
    monkeypatch.setattr(release,'validate_candidate',lambda *a,**kw:[])
    out=release.inspect(root=Path('/srv/software_development/forprint-project/forprint_system_blueprint'),
                        task=TASK,attempt=ATT,phase='LAUNCH_WINDOW')
    assert out['checks']['r051']=='PRECLAIM_ROOT_RECEIPT_VERIFIED_NON_AUTHORIZING'
    # A synthetic proof map cannot supply release authority. The r051 branch
    # is verified while the incomplete fake proof remains correctly blocked.
    assert out['status'] in ('PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED',
                             'BLOCKED_PENDING_PILOT_RELEASE_EVIDENCE')
    assert out['launch_allowed'] is False


def test_legacy_preclaim_r046_still_calls_r045(monkeypatch):
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as r045
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    monkeypatch.setattr(console,'source_guard',lambda _:HEAD)
    calls=[]
    monkeypatch.setattr(r045,'collect',lambda *a,**kw:calls.append(True) or {'preclaim_evidence_complete':False,'status':'BLOCKED'})
    monkeypatch.setattr(release,'_trusted_folder',lambda _: (_ for _ in ()).throw(FileNotFoundError()))
    out=release.inspect(root=Path('/srv/software_development/forprint-project/forprint_system_blueprint'),task=TASK,attempt=ATT)
    assert calls==[True]
    assert 'R045_PRECLAIM_UNVERIFIED' in out['blockers']


def test_phase_cli_cannot_authorize_and_unknown_phase_fails_closed():
    x=release.inspect(root=Path('/nonexistent'),task=TASK,attempt=ATT,phase='WRONG')
    assert x['launch_allowed'] is False
    assert x['blockers']


def test_makefile_still_has_original_quarantine():
    make=(Path(__file__).resolve().parents[3]/'Makefile').read_text()
    assert 'CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND' in make
    assert 'governed-worker-cycle-advance: cf10-s01-runtime-launch-preflight' in make
    assert 'LIVE_CUTOVER_ENABLED=False' in (Path(__file__).resolve().parents[3]/'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py').read_text()
