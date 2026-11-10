"""R131 source-only test. A synthetic event is NEVER real kernel evidence."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import pytest
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r131_terminal_review_fence_v0_1 as r131,
    cf10_r129_canonical_lifecycle_convergence_v0_1 as r129,
)


def fixture():
    candidate, events = r129.synthetic_fixture()
    return deepcopy(candidate), deepcopy(events)


def test_readonly_source_review_never_becomes_runtime_attestation():
    c, e = fixture()
    result = r131.review_source(candidate=c, synthetic_events=e)
    assert result['stage'] == 'SOURCE_ONLY_NOT_TERMINAL_EVIDENCE'
    assert result['synthetic_unit_is_not_canonical'] is True
    assert result['runtime_evidence_verified'] is False
    assert result['terminal_ledger_written'] is False
    assert result['live_worker_authorized'] is False
    assert result['result_accepted'] is False
    assert all(value is False for value in result['authority'].values())
    assert result['report_sha256'] == r131._digest({k:v for k,v in result.items() if k!='report_sha256'})


def test_source_deterministic():
    c, e = fixture()
    assert r131.review_source(candidate=c, synthetic_events=e) == r131.review_source(candidate=c, synthetic_events=e)

@pytest.mark.parametrize('key', ['attempt_id','task_id','work_front_id','decision_id','epoch','source_head'])
def test_candidate_drift_holds(key):
    c, e = fixture()
    c[key] = 'bad'
    with pytest.raises(r131.R131Hold):r131.review_source(candidate=c, synthetic_events=e)

@pytest.mark.parametrize('position', list(range(11)))
def test_synthetic_transition_wrong_holds(position):
    c, e = fixture()
    e[position]['step'] = 'BYPASS'
    with pytest.raises(r131.R131Hold):r131.review_source(candidate=c, synthetic_events=e)


def test_live_attempt_is_never_authorized():
    c, e = fixture()
    with pytest.raises(r131.R131Hold):r131.review_source(candidate=c, synthetic_events=e, live_cutover_enabled=True)

@pytest.mark.parametrize('field', ['result_accepted', 'terminal_status'])
def test_terminal_event_drift_holds(field):
    c, e = fixture()
    e[9][field] = True
    with pytest.raises(r131.R131Hold):r131.review_source(candidate=c, synthetic_events=e)


def test_non_root_blocks_before_any_systemd_or_lease_readback():
    c,e = fixture()
    with patch.object(r131.os, 'geteuid', return_value=996):
        with pytest.raises(r131.R131Hold, match='ROOT_ONLY'):
            r131.witnessed_review_candidate(candidate=c, synthetic_events=e,
                attempt_root=Path('/invalid'),lease_path=Path('/invalid'),
                witness=None,runner=None,timeout_seconds=30)


def test_root_rejects_unscoped_attempt_and_bad_lease():
    c,e = fixture()
    with patch.object(r131.os, 'geteuid', return_value=0):
        with pytest.raises(r131.R131Hold,match='ATTEMPT_SCOPE'):
            r131.witnessed_review_candidate(candidate=c,synthetic_events=e,
                attempt_root=Path('/tmp/not-allowed'),lease_path=Path('/run/bad'),
                witness=None,runner=None,timeout_seconds=30)


def test_timeout_cannot_be_zero_or_boolean():
    c,e = fixture()
    with patch.object(r131.os, 'geteuid', return_value=0):
        for timeout in [0, True, -1, 7201, '100']:
            with pytest.raises(r131.R131Hold,match='TIMEOUT'):
                r131.witnessed_review_candidate(candidate=c,synthetic_events=e,
                    attempt_root=Path('/tmp/'),lease_path=Path('/tmp/'),
                    witness=None,runner=None,timeout_seconds=timeout)


def test_no_inline_runner_or_claim_or_ledger_append():
    text=Path(r131.__file__).read_text('utf8')
    assert 'subprocess.Popen' not in text
    assert 'systemd-run' not in text
    assert 'claim(' not in text
    assert '.append_observation(' not in text
    assert "'terminal_ledger_written': False" in text
    assert "'live_worker_authorized': False" in text
    assert 'witnessed_terminal(' in text
    assert 'inspect_lease(' in text


def test_terminal_source_only_does_not_trust_synthetic_unit():
    c,e=fixture()
    assert r131.review_source(candidate=c,synthetic_events=e)['synthetic_unit_is_not_canonical']


def _mock_real_readback_fixture(tmp_path, monkeypatch, *, revoked=True, wrong_unit=False, fail_kernel=False):
    """Pure test doubles. NOT an attestation or live systemd test."""
    from types import SimpleNamespace
    from scripts.coordination.control_plane import worker_runtime as pkg
    c, e = fixture()
    root = tmp_path/'worker-01'
    attempt = root/c['attempt_id']
    attempt.mkdir(parents=True)
    c['candidate_mcp_config']['mcpServers']['ForPrintValidation']['cwd'] = str(attempt/'workspace'/'repo')
    c['candidate_sha256'] = r129.sha({k:v for k,v in c.items() if k!='candidate_sha256'})
    class FakeWitness:
        unit = 'forprint-cf10-worker-'+'a'*24+'.service'
        invocation_id = 'b'*32
        closed = False
    lease = {'revoked': revoked}
    calls = []
    def inspect(path, **kwargs):
        calls.append('root-lease')
        assert kwargs['attempt'] == c['attempt_id']
        assert kwargs['source_head'] == c['source_head']
        return lease
    def witness_terminal(**kwargs):
        calls.append('canonical-terminal')
        if fail_kernel:
            raise TerminalBlocked('PINNED_KERNEL_READ_LOST')
        return {
            'systemd_unit': 'forprint-cf10-worker-'+'f'*24+'.service' if wrong_unit else FakeWitness.unit,
            'systemd_invocation_id': FakeWitness.invocation_id,
            'quiescence_observation': 'PINNED_KERNEL_1_TO_0_RETAINED_SYSTEMD_NON_AUTHORIZING',
            'return_code': 0,'timed_out':False,'worker_result_accepted':False,
            'release_allowed': False,'automatic_retry':False,
        }
    class TerminalBlocked(Exception):
        pass
    class KernelBlocked(Exception):
        pass
    monkeypatch.setattr(pkg,'cf10_r126_root_external_revoke_v0_1', SimpleNamespace(
        inspect_lease=inspect, ExternalRevokeHold=Exception),raising=False)
    monkeypatch.setattr(pkg,'cf10_systemd_terminal_bridge_v0_1', SimpleNamespace(
        witnessed_terminal=witness_terminal, TerminalReadbackBlocked=TerminalBlocked),raising=False)
    monkeypatch.setattr(pkg,'cf10_systemd_kernel_witness_v0_1', SimpleNamespace(
        KernelWitness=FakeWitness, WitnessBlocked=KernelBlocked),raising=False)
    monkeypatch.setattr(r131,'WORKER_ROOT',root)
    monkeypatch.setattr(r131.os,'geteuid',lambda:0)
    return c,e,attempt,FakeWitness(),calls


def test_root_and_typed_kernel_review_joins_only_after_both_readbacks(tmp_path,monkeypatch):
    c,e,attempt,witness,calls = _mock_real_readback_fixture(tmp_path,monkeypatch)
    result=r131.witnessed_review_candidate(candidate=c,synthetic_events=e,
        attempt_root=attempt,lease_path=Path('/run/forprint-cf10-r125-'+'f'*16+'/lease.json'),
        witness=witness,runner=lambda argv: None,timeout_seconds=30)
    assert calls == ['root-lease','canonical-terminal']
    assert result['root_lease_revoked'] is True
    assert result['pinned_kernel_transition'] == '1_TO_0'
    assert result['canonical_manifest_decision_join_attested'] is False
    assert result['terminal_ledger_written'] is False
    assert all(v is False for v in result['authority'].values())
    assert result['unit'] == witness.unit
    assert result['unit'] != e[0]['unit']  # synthetic unit has no authority


def test_open_lease_cannot_produce_terminal_candidate(tmp_path,monkeypatch):
    c,e,attempt,witness,calls = _mock_real_readback_fixture(tmp_path,monkeypatch,revoked=False)
    with pytest.raises(r131.R131Hold,match='ACTIVE_LEASE_NOT_TERMINAL'):
        r131.witnessed_review_candidate(candidate=c,synthetic_events=e,attempt_root=attempt,
          lease_path=Path('/run/forprint-cf10-r125-'+'f'*16+'/lease.json'),
          witness=witness,runner=lambda argv: None,timeout_seconds=30)
    assert calls == ['root-lease']


def test_kernel_witness_failure_is_hold_after_revoke(tmp_path,monkeypatch):
    c,e,attempt,witness,calls = _mock_real_readback_fixture(tmp_path,monkeypatch,fail_kernel=True)
    with pytest.raises(r131.R131Hold,match='CANONICAL_KERNEL_TERMINAL_NOT_PROVEN'):
        r131.witnessed_review_candidate(candidate=c,synthetic_events=e,attempt_root=attempt,
          lease_path=Path('/run/forprint-cf10-r125-'+'f'*16+'/lease.json'),
          witness=witness,runner=lambda argv: None,timeout_seconds=30)
    assert calls == ['root-lease','canonical-terminal']


def test_unit_drift_cannot_produce_terminal_candidate(tmp_path,monkeypatch):
    c,e,attempt,witness,calls = _mock_real_readback_fixture(tmp_path,monkeypatch,wrong_unit=True)
    with pytest.raises(r131.R131Hold,match='TERMINAL_EVIDENCE_DRIFT'):
        r131.witnessed_review_candidate(candidate=c,synthetic_events=e,attempt_root=attempt,
          lease_path=Path('/run/forprint-cf10-r125-'+'f'*16+'/lease.json'),
          witness=witness,runner=lambda argv: None,timeout_seconds=30)


def test_arbitrary_not_typed_witness_is_rejected(tmp_path,monkeypatch):
    c,e,attempt,witness,calls = _mock_real_readback_fixture(tmp_path,monkeypatch)
    with pytest.raises(r131.R131Hold,match='TYPED_KERNEL_WITNESS_REQUIRED'):
        r131.witnessed_review_candidate(candidate=c,synthetic_events=e,attempt_root=attempt,
          lease_path=Path('/run/forprint-cf10-r125-'+'f'*16+'/lease.json'),
          witness=object(),runner=lambda argv:None,timeout_seconds=30)
    assert not calls


def test_source_cli_does_not_claim_runtime_proof(monkeypatch,capsys):
    monkeypatch.setattr(r129,'verify_pinned_seams',lambda root:None)
    assert r131.main(['--mode','source-check']) == 0
    out=capsys.readouterr().out
    assert 'CF10_R131_RUNTIME_WITNESS=NOT_CLAIMED' in out
    assert 'CF10_R131_LIVE_CUTOVER=SEALED_FALSE' in out
