"""All tests are fake filesystem-only; never inspect or change real s01."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_1 as m


def fixture_roots(tmp_path, monkeypatch):
    d = tmp_path / "deployment"
    gate = tmp_path / "gate"
    writer = tmp_path / "writer"
    for path in (d, gate, writer):
        path.mkdir()
    (d / "tmp").mkdir()
    (d / m.CANONICAL_REL).mkdir(parents=True)
    for rel in m.TRACKED_WRITERS:
        for root in (d, writer):
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"# fake: {rel}\n")
    evidence = gate / "tmp" / "coverage.json"
    evidence.parent.mkdir()
    evidence.write_text(json.dumps({
        "schema_version": "forprint_execution_attempt_writer_deployment_evidence_v0_2",
        "status": "READY_FOR_INDEPENDENT_REVIEW", "technical_blockers": [],
        "deployment_coverage_verified": False,
        "gate_publication": {"commit": m.GATE_COMMIT, "ref": m.GATE_REF, "remote": m.REMOTE},
        "writer_publication": {"commit": m.WRITER_COMMIT, "ref": m.WRITER_REF, "remote": m.REMOTE},
    }))
    monkeypatch.setattr(m, "configured_paths", lambda: {})
    monkeypatch.setattr(m, "scan_proc", lambda *_a, **_kw: {"state": "OBSERVED", "observed": [], "unreadable_count": 0, "absence_of_processes_proven": False})
    monkeypatch.setattr(m, "acl_status", lambda *_a, **_kw: {"state": "FIXTURE"})
    monkeypatch.setattr(m, "mount_status", lambda *_a, **_kw: {"state": "FIXTURE", "network_or_fuse_surface": False})
    return d, gate, writer, evidence


def call(d, gate, writer, evidence, **kwargs):
    return m.build_review(deployment_root=d, gate_root=gate, writer_root=writer,
                          coverage_path=evidence, expected_evidence_sha=m.digest(evidence.read_bytes()),
                          hostname="s01", check_git=False, **kwargs)


def test_s01_boundary_declaration_never_self_certifies(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    doc = call(d, g, w, e)
    assert doc["status"] == "OPERATOR_REVIEW_REQUIRED"
    assert doc["verified"] is False
    assert doc["operator_declared_boundary"]["other_hosts_onboarded"] is False
    assert doc["operator_declared_boundary"]["remote_hosts_technically_excluded"] is False
    assert doc["independent_operator_approval_performed"] is False
    assert doc["findings_requiring_operator_action"] == []


def test_wrong_host_fail_closed(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    with pytest.raises(m.InventoryBlocked, match="WRONG_HOST"):
        m.build_review(deployment_root=d, gate_root=g, writer_root=w, coverage_path=e,
                       expected_evidence_sha=m.digest(e.read_bytes()), hostname="host-other", check_git=False)


def test_evidence_mismatch_fails(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    with pytest.raises(m.InventoryBlocked, match="SHA_MISMATCH"):
        m.build_review(deployment_root=d, gate_root=g, writer_root=w, coverage_path=e,
                       expected_evidence_sha="a" * 64, hostname="s01", check_git=False)


def test_modified_deployed_writer_requires_action(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    (d / m.TRACKED_WRITERS[0]).write_text("# changed deployment file\n")
    doc = call(d, g, w, e)
    assert "DEPLOYMENT_WRITER_SOURCE_NOT_EQUAL_PINNED_RELEASE" in doc["findings_requiring_operator_action"]
    assert doc["writer_source_comparison"][m.TRACKED_WRITERS[0]]["exact_writer_release_sha256_match"] is False


def test_symlinked_deployment_file_is_not_trusted(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    f = d / m.TRACKED_WRITERS[0]
    f.unlink()
    f.symlink_to(w / m.TRACKED_WRITERS[0])
    doc = call(d, g, w, e)
    assert "DEPLOYMENT_WRITER_SOURCE_NOT_EQUAL_PINNED_RELEASE" in doc["findings_requiring_operator_action"]
    assert doc["writer_source_comparison"][m.TRACKED_WRITERS[0]]["deployment_file"]["state"] == "SYMLINK"


def test_report_is_create_only_and_outside_tmp_rejected(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    doc = call(d, g, w, e)
    name = Path("tmp/cf10_s01_test.json")
    initial = m.write_report(name, d, doc)
    assert m.digest((d / name).read_bytes()) == initial
    with pytest.raises(m.InventoryBlocked, match="CREATE_ONLY"):
        m.write_report(name, d, doc)
    with pytest.raises(m.InventoryBlocked, match="DIRECT_CHILD"):
        m.write_report(Path("elsewhere/file.json"), d, doc)


def test_network_mount_remains_operator_finding(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "mount_status", lambda *_a, **_kw: {"state": "OBSERVED", "network_or_fuse_surface": True})
    doc = call(d, g, w, e)
    assert "CANONICAL_LEDGER_NETWORK_OR_FUSE_MOUNT_REVIEW" in doc["findings_requiring_operator_action"]


def test_proc_scan_minimizes_sensitive_command_lines(tmp_path):
    p = tmp_path / "100"
    p.mkdir()
    (p / "cmdline").write_bytes(b"python\x00-m\x00scripts.coordination.control_plane.governed_worker_cycle\x00--password\x00secret\x00")
    result = m.scan_proc(tmp_path)
    assert result["state"] == "OBSERVED"
    assert result["observed"][0]["pid"] == 100
    assert "secret" not in json.dumps(result)
    assert result["absence_of_processes_proven"] is False


def test_protocol_presence_is_not_activation(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    doc = call(d, g, w, e)
    assert doc["external_provisioning_performed"] is False
    assert doc["writer_process_drain_performed"] is False
    assert doc["ledger_mutation_performed"] is False
    assert doc["git_mutation_performed"] is False


def test_matching_sources_do_not_self_authorize(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    doc = call(d, g, w, e)
    result = m.launch_preflight(doc)
    assert result['status'] == 'BLOCKED'
    assert result['launch_allowed'] is False
    assert result['runtime_binding_authorized'] is False
    assert 'INDEPENDENT_RUNTIME_BINDING_AND_ACTIVATION_READBACK_NOT_INTEGRATED' in result['blockers']


def test_active_worktree_source_drift_blocks_launch(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    (d / m.TRACKED_WRITERS[0]).write_text('# actively developed dispatcher\n')
    result = m.launch_preflight(call(d, g, w, e))
    assert 'ACTIVE_WORKTREE_WRITER_SOURCE_DRIFT' in result['blockers']


def test_not_root_owned_ledger_blocks_launch(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    doc = call(d, g, w, e)
    doc['canonical_ledger']['status']['uid'] = 1000
    result = m.launch_preflight(doc)
    assert 'CANONICAL_LEDGER_NOT_ROOT_OWNED' in result['blockers']


def test_inspection_is_non_authorizing(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    result = m.binding_summary(call(d, g, w, e))
    assert result['status'] == 'OPERATOR_REVIEW_REQUIRED'
    assert result['runtime_binding_authorized'] is False
    assert result['independent_attestation_verified'] is False
    assert result['all_writer_sources_pinned'] is True


def test_missing_writer_source_never_accepted(monkeypatch, tmp_path):
    d, g, w, e = fixture_roots(tmp_path, monkeypatch)
    (d / m.TRACKED_WRITERS[0]).unlink()
    assert 'ACTIVE_WORKTREE_WRITER_SOURCE_DRIFT' in m.launch_preflight(call(d, g, w, e))['blockers']


def test_current_published_release_pins():
    assert m.GATE_COMMIT == '3d90143a240439d33833463d38ab0fb3497eac8f'
    assert m.WRITER_COMMIT == 'd5d1495c0a1ab25367c146b0f5379b015e03dd85'
