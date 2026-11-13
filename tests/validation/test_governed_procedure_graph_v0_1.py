from __future__ import annotations

from copy import deepcopy
from importlib import import_module

import pytest

procedure_graph = import_module("scripts.coordination.governed_procedure_graph_v0_1")
ProcedureValidationError = procedure_graph.ProcedureValidationError
canonical_sha256 = procedure_graph.canonical_sha256
validate_canonical_contracts = procedure_graph.validate_canonical_contracts
validate_procedure_graph = procedure_graph.validate_procedure_graph
validate_registry_instance = procedure_graph.validate_registry_instance
validate_run_manifest = procedure_graph.validate_run_manifest


def graph() -> dict:
    return {
        "schema_version": "forprint_governed_procedure_graph_v0_1",
        "procedure_id": "cf07_test_procedure",
        "procedure_revision": "0.1.0",
        "capability": {
            "capability_id": "governed_test_mutation",
            "classification": "GRAPH_REQUIRED",
            "reason": "Mutation requires ordered gates and evidence.",
        },
        "nodes": [
            {
                "node_id": "required",
                "kind": "REQUIRED",
                "gate": "NONE",
                "depends_on": [],
                "evidence_required": True,
                "waivable": False,
            },
            {
                "node_id": "conditional",
                "kind": "CONDITIONAL",
                "gate": "OBSERVED_GATE",
                "depends_on": ["required"],
                "evidence_required": True,
                "waivable": True,
                "condition": "when relevant",
            },
            {
                "node_id": "optional",
                "kind": "OPTIONAL",
                "gate": "NONE",
                "depends_on": ["conditional"],
                "evidence_required": False,
                "waivable": True,
            },
            {
                "node_id": "not_applicable",
                "kind": "NOT_APPLICABLE",
                "gate": "NONE",
                "depends_on": ["optional"],
                "evidence_required": False,
                "waivable": False,
            },
            {
                "node_id": "operator_gate",
                "kind": "OPERATOR_GATE",
                "gate": "HARD_GATE",
                "depends_on": ["not_applicable"],
                "evidence_required": True,
                "waivable": False,
                "operator_decision_class": "OPERATOR_APPROVAL",
            },
            {
                "node_id": "retry",
                "kind": "RETRY",
                "gate": "OBSERVED_GATE",
                "depends_on": ["operator_gate"],
                "evidence_required": True,
                "waivable": True,
                "retry_policy": {"max_attempts": 2},
            },
            {
                "node_id": "abort",
                "kind": "ABORT",
                "gate": "HARD_GATE",
                "depends_on": ["retry"],
                "evidence_required": True,
                "waivable": False,
                "abort_reason_class": "SAFETY_OR_CONTRACT_FAILURE",
            },
        ],
    }


def registry(g: dict) -> dict:
    return {
        "procedures": [
            {
                "procedure_id": g["procedure_id"],
                "procedure_revision": g["procedure_revision"],
                "graph_sha256": canonical_sha256(g),
                "status": "ACTIVE",
            }
        ],
        "capabilities": [
            deepcopy(g["capability"]),
            {
                "capability_id": "read_only_inventory",
                "classification": "NOT_REQUIRED",
                "reason": "Read-only non-authoritative inventory.",
            },
        ],
    }


def manifest(g: dict) -> dict:
    return {
        "schema_version": "forprint_procedure_run_manifest_v0_1",
        "run_id": "run-001",
        "procedure_id": g["procedure_id"],
        "procedure_revision": g["procedure_revision"],
        "graph_sha256": canonical_sha256(g),
        "capability_id": g["capability"]["capability_id"],
        "capability_classification": "GRAPH_REQUIRED",
        "contract_revisions": [
            {
                "contract_id": "work_front_contract",
                "revision": "0.1.0",
                "sha256": "a" * 64,
            }
        ],
        "node_results": [
            {"node_id": "required", "outcome": "PASS", "evidence": ["e1"]},
            {"node_id": "conditional", "outcome": "FAIL", "evidence": ["obs"]},
            {"node_id": "optional", "outcome": "PASS", "evidence": []},
            {
                "node_id": "not_applicable",
                "outcome": "NOT_APPLICABLE",
                "evidence": [],
            },
            {
                "node_id": "operator_gate",
                "outcome": "PASS",
                "evidence": ["operator"],
            },
            {"node_id": "retry", "outcome": "PASS", "evidence": ["retry"]},
            {"node_id": "abort", "outcome": "PASS", "evidence": ["safe"]},
        ],
        "waivers": [],
        "canonical_mutation_performed": True,
        "derived_refresh": {
            "status": "PASS",
            "evidence": ["continuity projections and indexes refreshed"],
        },
        "recovery_class": "NONE",
    }


def test_canonical_contract_surfaces() -> None:
    validate_canonical_contracts()


def test_graph_represents_all_cf07_node_kinds_and_gate_types() -> None:
    g = graph()
    validate_procedure_graph(g)
    assert {node["kind"] for node in g["nodes"]} == {
        "REQUIRED",
        "CONDITIONAL",
        "OPTIONAL",
        "NOT_APPLICABLE",
        "OPERATOR_GATE",
        "RETRY",
        "ABORT",
    }
    assert {node["gate"] for node in g["nodes"]} >= {
        "HARD_GATE",
        "OBSERVED_GATE",
    }


def test_registry_requires_graph_classification_reason() -> None:
    g = graph()
    r = registry(g)
    validate_registry_instance(r)
    broken = deepcopy(r)
    broken["capabilities"][0]["reason"] = ""
    with pytest.raises(ProcedureValidationError):
        validate_registry_instance(broken)


def test_valid_manifest_allows_failed_observed_gate() -> None:
    g = graph()
    validate_run_manifest(manifest(g), g, registry(g))


def test_required_node_skip_fails() -> None:
    g = graph()
    m = manifest(g)
    m["node_results"] = [row for row in m["node_results"] if row["node_id"] != "required"]
    with pytest.raises(ProcedureValidationError, match="SKIPPED_REQUIRED_NODE"):
        validate_run_manifest(m, g, registry(g))


def test_hard_gate_failure_blocks_downstream_execution() -> None:
    g = graph()
    m = manifest(g)
    for row in m["node_results"]:
        if row["node_id"] == "operator_gate":
            row["outcome"] = "FAIL"
    with pytest.raises(ProcedureValidationError, match="failed HARD_GATE"):
        validate_run_manifest(m, g, registry(g))


def test_valid_waiver_is_revision_bound_and_illegal_waiver_fails() -> None:
    g = graph()
    m = manifest(g)
    for row in m["node_results"]:
        if row["node_id"] == "conditional":
            row["outcome"] = "WAIVED"
    m["waivers"] = [
        {
            "waiver_id": "w-1",
            "node_id": "conditional",
            "procedure_revision": "0.1.0",
            "approved_by": "operator",
            "reason": "bounded test exception",
            "scope": "conditional node only",
        }
    ]
    validate_run_manifest(m, g, registry(g))

    bad = deepcopy(m)
    for row in bad["node_results"]:
        if row["node_id"] == "operator_gate":
            row["outcome"] = "WAIVED"
    bad["waivers"].append(
        {
            "waiver_id": "w-2",
            "node_id": "operator_gate",
            "procedure_revision": "0.1.0",
            "approved_by": "operator",
            "reason": "illegal",
            "scope": "operator gate",
        }
    )
    with pytest.raises(ProcedureValidationError, match="ILLEGAL_WAIVER"):
        validate_run_manifest(bad, g, registry(g))


def test_stale_revision_and_graph_drift_fail() -> None:
    g = graph()
    m = manifest(g)
    m["procedure_revision"] = "0.0.9"
    with pytest.raises(ProcedureValidationError, match="STALE_PROCEDURE_REVISION"):
        validate_run_manifest(m, g, registry(g))

    m = manifest(g)
    m["graph_sha256"] = "b" * 64
    with pytest.raises(ProcedureValidationError, match="GRAPH_DRIFT"):
        validate_run_manifest(m, g, registry(g))


def test_unregistered_graph_source_fails() -> None:
    g = graph()
    with pytest.raises(ProcedureValidationError, match="unregistered"):
        validate_procedure_graph(g, registry={"procedures": [], "capabilities": []})


def test_canonical_mutation_requires_derived_refresh() -> None:
    g = graph()
    m = manifest(g)
    m["derived_refresh"] = {
        "status": "FAIL",
        "evidence": ["projection stale"],
    }
    m["recovery_class"] = "PROJECTION_STALE"
    with pytest.raises(ProcedureValidationError, match="PROJECTION_STALE"):
        validate_run_manifest(m, g, registry(g))


def test_canonical_conflict_and_projection_stale_are_distinct() -> None:
    g = graph()
    m = manifest(g)
    for value in ("CANONICAL_CONFLICT", "PROJECTION_STALE"):
        current = deepcopy(m)
        current["recovery_class"] = value
        validate_run_manifest(current, g, registry(g))
    assert "CANONICAL_CONFLICT" != "PROJECTION_STALE"


# CF07_S2_RUNTIME_TESTS_START
ROOT = procedure_graph.ROOT

attempt_ledger = import_module("scripts.coordination.execution_attempt_ledger_v0_1")


def _runtime_results() -> list[dict]:
    return [
        {
            "node_id": "inspect_current_state",
            "outcome": "PASS",
            "evidence": ["source state inspected"],
        },
        {
            "node_id": "verify_authority_and_scope",
            "outcome": "PASS",
            "evidence": ["authority and scope constrained"],
        },
        {
            "node_id": "apply_canonical_mutation",
            "outcome": "PASS",
            "evidence": ["accepted canonical mutation ref"],
        },
        {
            "node_id": "refresh_affected_derived",
            "outcome": "PASS",
            "evidence": ["derived projections refreshed"],
        },
        {
            "node_id": "validate_conformance",
            "outcome": "PASS",
            "evidence": ["targeted and public validation passed"],
        },
    ]


def _attempt_record(attempt_id: str = "attempt-cf07-s2-001") -> dict:
    return {
        "schema_version": "forprint_execution_attempt_record_v0_1",
        "attempt_id": attempt_id,
        "work_front_id": "wf-cf07-s2-test",
        "recorded_at": "2026-09-15T16:00:00Z",
        "actor_or_worker_ref": "cf07-runtime-test",
        "where": "blueprint",
        "why": "prove Procedure Run evidence can bind to attempt history",
        "source_fingerprint": "sha256:cf07-runtime-test",
        "profile_ref_or_revision": None,
        "pack_hash_or_context_hash": None,
        "launch_or_invocation_ref": None,
        "attempt_stage": "FINISHED",
        "result_state": "SUCCEEDED",
        "result_refs": [],
        "validator_outcome": "PASS",
        "validator_evidence_refs": ["pytest:cf07-runtime"],
        "failure_or_retry_ref": None,
        "resume": {
            "latest_accepted_ref": None,
            "resume_coordinates": [],
            "replay_forbidden_refs": [],
        },
    }


def test_runtime_registry_resolves_hash_bound_real_procedure() -> None:
    registry = procedure_graph.load_procedure_registry(ROOT)
    entry, resolved = procedure_graph.resolve_procedure(
        registry,
        "governed_canonical_mutation",
        revision="0.1.0",
        root=ROOT,
    )
    assert entry["graph_sha256"] == canonical_sha256(resolved)
    assert entry["status"] == "ACTIVE"
    assert registry["authority"]["execution_authority"] is False
    assert registry["authority"]["dispatch_authority"] is False


def test_evaluate_and_append_run_manifest_is_immutable(tmp_path) -> None:
    manifest, path = procedure_graph.evaluate_procedure_run(
        run_id="run-cf07-s2-001",
        procedure_id="governed_canonical_mutation",
        node_results=_runtime_results(),
        canonical_mutation_performed=True,
        derived_refresh={
            "status": "PASS",
            "evidence": ["derived surfaces refreshed"],
        },
        persist=True,
        root=ROOT,
        store_override=tmp_path,
    )
    assert path is not None and path.is_file()
    assert manifest["contract_revisions"]
    assert manifest["graph_sha256"]
    assert procedure_graph.run_manifest_digest(manifest)[:12] in path.name
    with pytest.raises(FileExistsError, match="run_id already exists"):
        procedure_graph.append_run_manifest(
            ROOT,
            manifest,
            store_override=tmp_path,
        )


def test_stale_or_drifted_runtime_registry_fails_closed() -> None:
    registry = procedure_graph.load_procedure_registry(ROOT)
    broken = deepcopy(registry)
    broken["procedures"][0]["graph_sha256"] = "b" * 64
    with pytest.raises(ProcedureValidationError, match="graph drift"):
        procedure_graph.resolve_procedure(
            broken,
            "governed_canonical_mutation",
            revision="0.1.0",
            root=ROOT,
        )
    with pytest.raises(
        ProcedureValidationError,
        match="resolution ambiguous/missing",
    ):
        procedure_graph.resolve_procedure(
            registry,
            "governed_canonical_mutation",
            revision="9.9.9",
            root=ROOT,
        )


def test_procedure_run_evidence_binds_to_attempt_ledger_without_authority(
    tmp_path,
) -> None:
    _manifest, path = procedure_graph.evaluate_procedure_run(
        run_id="run-cf07-attempt-binding-001",
        procedure_id="governed_canonical_mutation",
        node_results=_runtime_results(),
        canonical_mutation_performed=True,
        derived_refresh={
            "status": "PASS",
            "evidence": ["derived refresh accepted"],
        },
        persist=True,
        root=ROOT,
        store_override=tmp_path,
    )
    assert path is not None
    record = procedure_graph.bind_procedure_run_to_attempt_record(
        _attempt_record(),
        path,
    )
    assert any(
        ref.startswith("procedure_run:run-cf07-attempt-binding-001:")
        for ref in record["validator_evidence_refs"]
    )
    assert (
        attempt_ledger.validate_record_data(
            record,
            attempt_ledger.load_contract(ROOT),
        )
        == []
    )
    assert "dispatch_authority" not in record
    assert "release_authority" not in record


def test_runtime_surface_validator_passes() -> None:
    procedure_graph.validate_runtime_surfaces(ROOT)


# CF07_S2_RUNTIME_TESTS_END
