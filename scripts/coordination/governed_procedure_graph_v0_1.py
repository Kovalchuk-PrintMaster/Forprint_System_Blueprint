#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]

GRAPH_CONTRACT = (
    ROOT / "coordination/standards/automation/governed_procedure_graph_contract_v0_1.yaml"
)
REGISTRY_CONTRACT = (
    ROOT / "coordination/standards/automation/governed_procedure_registry_contract_v0_1.yaml"
)
MANIFEST_CONTRACT = (
    ROOT / "coordination/standards/automation/procedure_run_manifest_contract_v0_1.yaml"
)

NODE_KINDS = {
    "REQUIRED",
    "CONDITIONAL",
    "OPTIONAL",
    "NOT_APPLICABLE",
    "OPERATOR_GATE",
    "RETRY",
    "ABORT",
}
GATE_TYPES = {"NONE", "HARD_GATE", "OBSERVED_GATE"}
CLASSIFICATIONS = {"GRAPH_REQUIRED", "NOT_REQUIRED"}
OUTCOMES = {
    "PASS",
    "FAIL",
    "SKIPPED",
    "NOT_APPLICABLE",
    "WAIVED",
    "ABORTED",
    "RETRY",
}
RECOVERY_CLASSES = {"NONE", "CANONICAL_CONFLICT", "PROJECTION_STALE"}


class ProcedureValidationError(ValueError):
    pass


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def canonical_sha256(value: Any) -> str:
    payload = yaml.safe_dump(
        value,
        sort_keys=True,
        allow_unicode=True,
        width=120,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _need(mapping: dict[str, Any], key: str, where: str) -> Any:
    if key not in mapping:
        raise ProcedureValidationError(f"{where}: missing required field {key}")
    return mapping[key]


def _nonempty_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProcedureValidationError(f"{where}: expected non-empty string")
    return value


def validate_contract_surfaces(root: Path = ROOT) -> None:
    graph = load_yaml(root / GRAPH_CONTRACT.relative_to(ROOT))
    registry = load_yaml(root / REGISTRY_CONTRACT.relative_to(ROOT))
    manifest = load_yaml(root / MANIFEST_CONTRACT.relative_to(ROOT))

    if set(graph["node_kinds"]) != NODE_KINDS:
        raise ProcedureValidationError("graph contract node kinds drift")
    if set(graph["gate_types"]) != GATE_TYPES:
        raise ProcedureValidationError("graph contract gate types drift")

    recoveries = set(graph["canonical_mutation_rule"]["recovery_classes"])
    if recoveries != {"CANONICAL_CONFLICT", "PROJECTION_STALE"}:
        raise ProcedureValidationError("graph recovery class contract drift")

    allowed = set(registry["capability_classification"]["allowed_classifications"])
    if allowed != CLASSIFICATIONS:
        raise ProcedureValidationError("registry classification drift")

    manifest_recoveries = set(manifest["recovery_classes"])
    if manifest_recoveries != RECOVERY_CLASSES:
        raise ProcedureValidationError("manifest recovery class drift")

    if graph["authority_semantics"]["graph_grants_authority"] is not False:
        raise ProcedureValidationError("graph must not grant authority")
    if manifest["immutability"]["execution_authority"] is not False:
        raise ProcedureValidationError("manifest must not grant execution authority")
    if manifest["immutability"]["lifecycle_authority"] is not False:
        raise ProcedureValidationError("manifest must not grant lifecycle authority")


def validate_capability_classification(item: dict[str, Any]) -> None:
    where = "capability classification"
    capability_id = _nonempty_string(_need(item, "capability_id", where), where)
    classification = _need(item, "classification", where)
    if classification not in CLASSIFICATIONS:
        raise ProcedureValidationError(
            f"{capability_id}: invalid classification {classification!r}"
        )
    _nonempty_string(_need(item, "reason", where), where)


def validate_registry_instance(registry: dict[str, Any]) -> None:
    capabilities = registry.get("capabilities", [])
    if not isinstance(capabilities, list):
        raise ProcedureValidationError("registry capabilities must be a list")
    seen_capabilities: set[str] = set()
    for item in capabilities:
        if not isinstance(item, dict):
            raise ProcedureValidationError("capability entry must be mapping")
        validate_capability_classification(item)
        capability_id = item["capability_id"]
        if capability_id in seen_capabilities:
            raise ProcedureValidationError(f"duplicate capability_id {capability_id}")
        seen_capabilities.add(capability_id)

    procedures = registry.get("procedures", [])
    if not isinstance(procedures, list):
        raise ProcedureValidationError("registry procedures must be a list")
    seen: set[tuple[str, str]] = set()
    for item in procedures:
        if not isinstance(item, dict):
            raise ProcedureValidationError("procedure entry must be mapping")
        procedure_id = _nonempty_string(
            _need(item, "procedure_id", "procedure"),
            "procedure_id",
        )
        revision = _nonempty_string(
            _need(item, "procedure_revision", "procedure"),
            "procedure_revision",
        )
        digest = _nonempty_string(
            _need(item, "graph_sha256", "procedure"),
            "graph_sha256",
        )
        if len(digest) != 64:
            raise ProcedureValidationError("graph_sha256 must be sha256 hex")
        key = (procedure_id, revision)
        if key in seen:
            raise ProcedureValidationError(
                f"duplicate procedure revision {procedure_id}@{revision}"
            )
        seen.add(key)


def validate_procedure_graph(
    graph: dict[str, Any],
    *,
    registry: dict[str, Any] | None = None,
) -> None:
    if graph.get("schema_version") != "forprint_governed_procedure_graph_v0_1":
        raise ProcedureValidationError("invalid graph schema_version")

    procedure_id = _nonempty_string(
        _need(graph, "procedure_id", "graph"),
        "procedure_id",
    )
    revision = _nonempty_string(
        _need(graph, "procedure_revision", "graph"),
        "procedure_revision",
    )
    capability = graph.get("capability")
    if not isinstance(capability, dict):
        raise ProcedureValidationError("graph capability must be mapping")
    validate_capability_classification(capability)

    nodes = graph.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise ProcedureValidationError("graph nodes must be non-empty list")

    seen: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ProcedureValidationError("graph node must be mapping")
        node_id = _nonempty_string(
            _need(node, "node_id", f"node[{index}]"),
            f"node[{index}].node_id",
        )
        if node_id in seen:
            raise ProcedureValidationError(f"duplicate node_id {node_id}")
        kind = _need(node, "kind", node_id)
        gate = _need(node, "gate", node_id)
        deps = _need(node, "depends_on", node_id)
        if kind not in NODE_KINDS:
            raise ProcedureValidationError(f"{node_id}: invalid kind {kind}")
        if gate not in GATE_TYPES:
            raise ProcedureValidationError(f"{node_id}: invalid gate {gate}")
        if not isinstance(deps, list):
            raise ProcedureValidationError(f"{node_id}: depends_on must be list")
        unknown = [dep for dep in deps if dep not in seen]
        if unknown:
            raise ProcedureValidationError(
                f"{node_id}: dependency references non-earlier nodes {unknown}"
            )
        if not isinstance(node.get("evidence_required"), bool):
            raise ProcedureValidationError(f"{node_id}: evidence_required must be bool")
        if not isinstance(node.get("waivable"), bool):
            raise ProcedureValidationError(f"{node_id}: waivable must be bool")
        if kind == "CONDITIONAL" and not node.get("condition"):
            raise ProcedureValidationError(f"{node_id}: CONDITIONAL requires condition")
        if kind == "RETRY" and not isinstance(node.get("retry_policy"), dict):
            raise ProcedureValidationError(f"{node_id}: RETRY requires retry_policy")
        if kind == "OPERATOR_GATE" and not node.get("operator_decision_class"):
            raise ProcedureValidationError(
                f"{node_id}: OPERATOR_GATE requires operator_decision_class"
            )
        if kind == "ABORT" and not node.get("abort_reason_class"):
            raise ProcedureValidationError(f"{node_id}: ABORT requires abort_reason_class")
        seen.add(node_id)

    if registry is not None:
        validate_registry_instance(registry)
        matches = [
            item
            for item in registry.get("procedures", [])
            if item.get("procedure_id") == procedure_id
            and item.get("procedure_revision") == revision
        ]
        if len(matches) != 1:
            raise ProcedureValidationError(f"procedure {procedure_id}@{revision} is unregistered")
        if matches[0]["graph_sha256"] != canonical_sha256(graph):
            raise ProcedureValidationError(f"procedure {procedure_id}@{revision} graph drift")


def _waiver_map(
    waivers: list[dict[str, Any]],
    revision: str,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for waiver in waivers:
        if not isinstance(waiver, dict):
            raise ProcedureValidationError("waiver must be mapping")
        for field in (
            "waiver_id",
            "node_id",
            "procedure_revision",
            "approved_by",
            "reason",
            "scope",
        ):
            _nonempty_string(_need(waiver, field, "waiver"), f"waiver.{field}")
        if waiver["procedure_revision"] != revision:
            raise ProcedureValidationError(
                f"waiver {waiver['waiver_id']} is bound to stale revision"
            )
        node_id = waiver["node_id"]
        if node_id in result:
            raise ProcedureValidationError(f"multiple waivers for node {node_id}")
        result[node_id] = waiver
    return result


def validate_run_manifest(
    manifest: dict[str, Any],
    graph: dict[str, Any],
    registry: dict[str, Any],
) -> None:
    validate_procedure_graph(graph, registry=registry)

    if manifest.get("schema_version") != "forprint_procedure_run_manifest_v0_1":
        raise ProcedureValidationError("invalid manifest schema_version")

    for field in (
        "run_id",
        "procedure_id",
        "procedure_revision",
        "graph_sha256",
        "capability_id",
        "capability_classification",
        "contract_revisions",
        "node_results",
        "waivers",
        "canonical_mutation_performed",
        "derived_refresh",
        "recovery_class",
    ):
        _need(manifest, field, "manifest")

    if manifest["procedure_id"] != graph["procedure_id"]:
        raise ProcedureValidationError("manifest procedure_id mismatch")
    if manifest["procedure_revision"] != graph["procedure_revision"]:
        raise ProcedureValidationError("STALE_PROCEDURE_REVISION")
    if manifest["graph_sha256"] != canonical_sha256(graph):
        raise ProcedureValidationError("GRAPH_DRIFT")
    if manifest["capability_id"] != graph["capability"]["capability_id"]:
        raise ProcedureValidationError("manifest capability_id mismatch")
    if manifest["capability_classification"] != graph["capability"]["classification"]:
        raise ProcedureValidationError("manifest capability classification mismatch")

    if manifest["recovery_class"] not in RECOVERY_CLASSES:
        raise ProcedureValidationError("invalid recovery_class")

    revisions = manifest["contract_revisions"]
    if not isinstance(revisions, list):
        raise ProcedureValidationError("contract_revisions must be list")
    for item in revisions:
        if not isinstance(item, dict):
            raise ProcedureValidationError("contract revision must be mapping")
        for field in ("contract_id", "revision", "sha256"):
            _nonempty_string(
                _need(item, field, "contract_revision"),
                f"contract_revision.{field}",
            )
        if len(item["sha256"]) != 64:
            raise ProcedureValidationError("contract revision sha256 must be 64 hex chars")

    node_by_id = {node["node_id"]: node for node in graph["nodes"]}
    results = manifest["node_results"]
    if not isinstance(results, list):
        raise ProcedureValidationError("node_results must be list")

    result_by_id: dict[str, dict[str, Any]] = {}
    for result in results:
        if not isinstance(result, dict):
            raise ProcedureValidationError("node result must be mapping")
        node_id = _nonempty_string(
            _need(result, "node_id", "node_result"),
            "node_result.node_id",
        )
        if node_id not in node_by_id:
            raise ProcedureValidationError(f"UNREGISTERED_NODE_SOURCE:{node_id}")
        if node_id in result_by_id:
            raise ProcedureValidationError(f"duplicate node result {node_id}")
        outcome = _need(result, "outcome", node_id)
        if outcome not in OUTCOMES:
            raise ProcedureValidationError(f"{node_id}: invalid outcome {outcome}")
        evidence = _need(result, "evidence", node_id)
        if not isinstance(evidence, list):
            raise ProcedureValidationError(f"{node_id}: evidence must be list")
        result_by_id[node_id] = result

    waiver_map = _waiver_map(
        manifest["waivers"],
        graph["procedure_revision"],
    )

    blocked_by_hard_gate: set[str] = set()
    for node in graph["nodes"]:
        node_id = node["node_id"]
        result = result_by_id.get(node_id)

        if node["kind"] == "NOT_APPLICABLE":
            if result is None or result["outcome"] != "NOT_APPLICABLE":
                raise ProcedureValidationError(
                    f"{node_id}: NOT_APPLICABLE node requires explicit disposition"
                )
            continue

        if result is None:
            if node["kind"] in {"REQUIRED", "OPERATOR_GATE", "ABORT"}:
                raise ProcedureValidationError(f"SKIPPED_REQUIRED_NODE:{node_id}")
            continue

        outcome = result["outcome"]
        if node["evidence_required"] and not result["evidence"]:
            raise ProcedureValidationError(f"{node_id}: required evidence missing")

        if outcome == "WAIVED":
            waiver = waiver_map.get(node_id)
            if waiver is None:
                raise ProcedureValidationError(f"{node_id}: WAIVED without waiver")
            if not node["waivable"]:
                raise ProcedureValidationError(f"ILLEGAL_WAIVER:{node_id}")

        if any(dep in blocked_by_hard_gate for dep in node["depends_on"]):
            if outcome not in {"SKIPPED", "ABORTED"}:
                raise ProcedureValidationError(f"{node_id}: executed after failed HARD_GATE")

        if node["gate"] == "HARD_GATE" and outcome not in {"PASS", "WAIVED"}:
            blocked_by_hard_gate.add(node_id)

    if manifest["canonical_mutation_performed"] is True:
        refresh = manifest["derived_refresh"]
        if not isinstance(refresh, dict):
            raise ProcedureValidationError(
                "derived_refresh must be mapping after canonical mutation"
            )
        if refresh.get("status") != "PASS":
            raise ProcedureValidationError("PROJECTION_STALE")
        evidence = refresh.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ProcedureValidationError("derived refresh PASS requires evidence")


def validate_canonical_contracts(root: Path = ROOT) -> None:
    validate_contract_surfaces(root)
    registry_contract = load_yaml(root / REGISTRY_CONTRACT.relative_to(ROOT))
    initial = registry_contract.get("initial_registry")
    if not isinstance(initial, dict):
        raise ProcedureValidationError("initial_registry missing")
    validate_registry_instance(initial)


# CF07_S2_RUNTIME_START
RUNTIME_REGISTRY_REL = Path("coordination/registry/governed_procedure_registry_v0_1.yaml")
DEFAULT_RUN_STORE_REL = Path("coordination/continuity/procedure_runs")


def load_procedure_registry(
    root: Path = ROOT,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    path = registry_path if registry_path is not None else root / RUNTIME_REGISTRY_REL
    registry = load_yaml(path)
    if not isinstance(registry, dict):
        raise ProcedureValidationError("runtime procedure registry must be mapping")
    if registry.get("schema_version") != "forprint_governed_procedure_registry_v0_1":
        raise ProcedureValidationError("invalid runtime registry schema_version")
    authority = registry.get("authority")
    if not isinstance(authority, dict):
        raise ProcedureValidationError("runtime registry authority must be mapping")
    for field in (
        "execution_authority",
        "dispatch_authority",
        "release_authority",
    ):
        if authority.get(field) is not False:
            raise ProcedureValidationError(f"runtime registry must not grant {field}")
    validate_registry_instance(registry)
    return registry


def resolve_procedure(
    registry: dict[str, Any],
    procedure_id: str,
    *,
    revision: str | None = None,
    root: Path = ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _nonempty_string(procedure_id, "procedure_id")
    candidates = [
        item
        for item in registry.get("procedures", [])
        if item.get("procedure_id") == procedure_id
        and (revision is None or item.get("procedure_revision") == revision)
        and item.get("status") == "ACTIVE"
    ]
    if len(candidates) != 1:
        requested = revision or "ACTIVE"
        raise ProcedureValidationError(
            f"procedure resolution ambiguous/missing: {procedure_id}@{requested}"
        )
    entry = candidates[0]
    graph_path_raw = _nonempty_string(
        _need(entry, "graph_path", "procedure registry entry"),
        "graph_path",
    )
    graph_path = (root / graph_path_raw).resolve()
    try:
        graph_path.relative_to(root.resolve())
    except ValueError as exc:
        raise ProcedureValidationError("procedure graph_path escapes project root") from exc
    if not graph_path.is_file():
        raise ProcedureValidationError(f"registered procedure graph missing: {graph_path_raw}")
    graph = load_yaml(graph_path)
    if not isinstance(graph, dict):
        raise ProcedureValidationError("registered procedure graph must be mapping")
    validate_procedure_graph(graph, registry=registry)
    return entry, graph


def contract_revision_refs(root: Path = ROOT) -> list[dict[str, str]]:
    refs = []
    for rel in (
        GRAPH_CONTRACT.relative_to(ROOT),
        REGISTRY_CONTRACT.relative_to(ROOT),
        MANIFEST_CONTRACT.relative_to(ROOT),
    ):
        path = root / rel
        value = load_yaml(path)
        if not isinstance(value, dict):
            raise ProcedureValidationError(f"contract surface must be mapping: {rel}")
        contract_id = _nonempty_string(
            value.get("contract_id"),
            f"{rel}.contract_id",
        )
        revision = _nonempty_string(
            value.get("revision"),
            f"{rel}.revision",
        )
        refs.append(
            {
                "contract_id": contract_id,
                "revision": revision,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return refs


def build_run_manifest(
    *,
    run_id: str,
    procedure_id: str,
    node_results: list[dict[str, Any]],
    canonical_mutation_performed: bool,
    derived_refresh: dict[str, Any],
    waivers: list[dict[str, Any]] | None = None,
    recovery_class: str = "NONE",
    revision: str | None = None,
    root: Path = ROOT,
    registry_path: Path | None = None,
) -> dict[str, Any]:
    _nonempty_string(run_id, "run_id")
    registry = load_procedure_registry(root, registry_path)
    _entry, graph = resolve_procedure(
        registry,
        procedure_id,
        revision=revision,
        root=root,
    )
    manifest = {
        "schema_version": "forprint_procedure_run_manifest_v0_1",
        "run_id": run_id,
        "procedure_id": graph["procedure_id"],
        "procedure_revision": graph["procedure_revision"],
        "graph_sha256": canonical_sha256(graph),
        "capability_id": graph["capability"]["capability_id"],
        "capability_classification": graph["capability"]["classification"],
        "contract_revisions": contract_revision_refs(root),
        "node_results": node_results,
        "waivers": list(waivers or []),
        "canonical_mutation_performed": canonical_mutation_performed,
        "derived_refresh": derived_refresh,
        "recovery_class": recovery_class,
    }
    validate_run_manifest(manifest, graph, registry)
    return manifest


def run_manifest_digest(manifest: dict[str, Any]) -> str:
    return canonical_sha256(manifest)


def iter_run_manifests(store: Path) -> list[dict[str, Any]]:
    if not store.exists():
        return []
    records = []
    for path in sorted(store.glob("*.yaml")):
        value = load_yaml(path)
        if isinstance(value, dict):
            records.append(value)
    return records


def append_run_manifest(
    root: Path,
    manifest: dict[str, Any],
    *,
    store_override: Path | None = None,
    registry_path: Path | None = None,
) -> Path:
    registry = load_procedure_registry(root, registry_path)
    _entry, graph = resolve_procedure(
        registry,
        manifest.get("procedure_id", ""),
        revision=manifest.get("procedure_revision"),
        root=root,
    )
    validate_run_manifest(manifest, graph, registry)
    store = store_override if store_override is not None else root / DEFAULT_RUN_STORE_REL
    store.mkdir(parents=True, exist_ok=True)
    run_id = _nonempty_string(manifest.get("run_id"), "run_id")
    for existing in iter_run_manifests(store):
        if existing.get("run_id") == run_id:
            raise FileExistsError(f"run_id already exists: {run_id}")
    digest = run_manifest_digest(manifest)
    path = store / f"{run_id}__{digest[:12]}.yaml"
    payload = yaml.safe_dump(
        manifest,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
    return path


def evaluate_procedure_run(
    *,
    run_id: str,
    procedure_id: str,
    node_results: list[dict[str, Any]],
    canonical_mutation_performed: bool,
    derived_refresh: dict[str, Any],
    waivers: list[dict[str, Any]] | None = None,
    recovery_class: str = "NONE",
    revision: str | None = None,
    persist: bool = False,
    root: Path = ROOT,
    store_override: Path | None = None,
    registry_path: Path | None = None,
) -> tuple[dict[str, Any], Path | None]:
    manifest = build_run_manifest(
        run_id=run_id,
        procedure_id=procedure_id,
        revision=revision,
        node_results=node_results,
        waivers=waivers,
        canonical_mutation_performed=canonical_mutation_performed,
        derived_refresh=derived_refresh,
        recovery_class=recovery_class,
        root=root,
        registry_path=registry_path,
    )
    path = None
    if persist:
        path = append_run_manifest(
            root,
            manifest,
            store_override=store_override,
            registry_path=registry_path,
        )
    return manifest, path


def procedure_run_attempt_evidence(manifest_path: Path) -> str:
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = load_yaml(manifest_path)
    if not isinstance(manifest, dict):
        raise ProcedureValidationError("procedure run manifest file must be mapping")
    run_id = _nonempty_string(manifest.get("run_id"), "run_id")
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    return f"procedure_run:{run_id}:sha256:{digest}:path:{manifest_path.as_posix()}"


def bind_procedure_run_to_attempt_record(
    attempt_record: dict[str, Any],
    manifest_path: Path,
) -> dict[str, Any]:
    bound = dict(attempt_record)
    existing = bound.get("validator_evidence_refs", [])
    if not isinstance(existing, list) or not all(isinstance(item, str) for item in existing):
        raise ProcedureValidationError("attempt validator_evidence_refs must be string list")
    bound["validator_evidence_refs"] = [
        *existing,
        procedure_run_attempt_evidence(manifest_path),
    ]
    return bound


def validate_runtime_surfaces(root: Path = ROOT) -> None:
    registry = load_procedure_registry(root)
    procedures = registry.get("procedures", [])
    if not procedures:
        raise ProcedureValidationError(
            "runtime procedure registry must register at least one procedure"
        )
    for item in procedures:
        resolve_procedure(
            registry,
            item["procedure_id"],
            revision=item["procedure_revision"],
            root=root,
        )
    canonical = [
        item
        for item in procedures
        if item.get("procedure_id") == "governed_canonical_mutation"
        and item.get("status") == "ACTIVE"
    ]
    if len(canonical) != 1:
        raise ProcedureValidationError(
            "governed_canonical_mutation must have one ACTIVE registration"
        )


# CF07_S2_RUNTIME_END
