"""Strict canonical Writer proof — isolated fixture only, never production ledger."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import yaml
import pytest
from scripts.coordination import execution_attempt_writer_lock_v0_1 as guard
from scripts.coordination import execution_attempt_ledger_v0_1 as ledger

CONTRACT = Path(__file__).resolve().parents[2] / 'coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml'


def record():
    return {
        'schema_version':'forprint_execution_attempt_record_v0_1',
        'attempt_id':'cf10-fixture-direct-cli', 'work_front_id':'wf-fixture',
        'recorded_at':datetime(2026,10,29,tzinfo=timezone.utc).isoformat(),
        'actor_or_worker_ref':'fixture', 'where':'isolated-test','why':'strict-guard-proof',
        'source_fingerprint':'fixture','profile_ref_or_revision':None,
        'pack_hash_or_context_hash':None,'launch_or_invocation_ref':None,
        'attempt_stage':'STARTED','result_state':'PENDING','result_refs':[],
        'validator_outcome':'NOT_RUN','validator_evidence_refs':[],
        'failure_or_retry_ref':None,
        'resume':{'latest_accepted_ref':None,'resume_coordinates':[],'replay_forbidden_refs':[]}}


@pytest.fixture
def case(tmp_path, monkeypatch):
    root=tmp_path/'repo';root.mkdir()
    contract=root/'coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml'
    contract.parent.mkdir(parents=True)
    contract.write_bytes(CONTRACT.read_bytes())
    missing=tmp_path/'no-protocol.yaml'
    monkeypatch.setattr(guard,'PROTOCOL_PATH',missing)
    record_path=root/'case.yaml';record_path.write_text(yaml.safe_dump(record()))
    return root,missing,record_path


def test_canonical_append_missing_protocol_blocks_before_create(case):
    root,_,_=case
    with pytest.raises(guard.WriterProtocolError,match='SHARED_WRITER_PROTOCOL_NOT_PROVISIONED'):
        ledger.append_record(root,record())
    assert not (root/'coordination/continuity/execution_attempts').exists()


def test_direct_cli_missing_protocol_blocks(case):
    root,missing,record_path=case
    # Fresh Python process exercises the actual CLI entrypoint, only fixture paths.
    code = ("from pathlib import Path\nimport sys\n"
      "from scripts.coordination import execution_attempt_writer_lock_v0_1 as w\n"
      "from scripts.coordination import execution_attempt_ledger_v0_1 as l\n"
      "w.PROTOCOL_PATH=Path(sys.argv[1])\n"
      "sys.argv=['ledger','--root',sys.argv[2],'append','--record','case.yaml']\n"
      "raise SystemExit(l.main())\n")
    p=subprocess.run([sys.executable,'-B','-c',code,str(missing),str(root)],
       cwd=root, capture_output=True,text=True,
       env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    assert p.returncode!=0
    assert 'SHARED_WRITER_PROTOCOL_NOT_PROVISIONED' in p.stderr
    assert not (root/'coordination/continuity/execution_attempts').exists()


def test_noncanonical_store_override_is_not_blocked(case):
    root,missing,_=case
    alternative=root/'tmp/fixture-ledger'
    assert not missing.exists()
    out=ledger.append_record(root,record(),store_override=alternative)
    assert out.parent==alternative
    assert not (root/'coordination/continuity/execution_attempts').exists()


def test_canonical_override_alias_still_fails_closed(case):
    root,_,_=case
    canonical=root/'coordination/continuity/execution_attempts'
    with pytest.raises(guard.WriterProtocolError,match='SHARED_WRITER_PROTOCOL_NOT_PROVISIONED'):
        ledger.append_record(root,record(),store_override=canonical)
    assert not canonical.exists()


def test_release_gate_ast_accepts_strict_direct_canonical_writer():
    from scripts.coordination.control_plane import cf10_s01_release_gate_candidate_v0_1 as release
    root=Path(__file__).resolve().parents[2]
    source=(root/release.SOURCE_GUARD).read_text()
    ledger_source=(root/release.SOURCE_LEDGER).read_text()
    assert release.strict_direct_writer_guard(source,ledger_source) is True
