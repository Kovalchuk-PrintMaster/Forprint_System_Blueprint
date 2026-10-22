from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination import execution_attempt_ledger_v0_1 as attempt_ledger
from scripts.coordination.control_plane import dispatch_intent as dispatch

TRAINING_QUEUE = Path(
    "coordination/internal_work/blueprint/worker_training/"
    "cf10_worker_training_queue_v0_1.yaml"
)
WORKER_TASK_INDEX = Path(
    "coordination/internal_work/blueprint/worker_tasks/index.yaml"
)
WORKER_TASK_ROOT = Path(
    "coordination/internal_work/blueprint/worker_tasks"
)
WORK_FRONT_ROOT = Path("coordination/work_fronts")

ATTEMPT_RE = re.compile(r"^cf10-u180j-a([0-9]{3,})$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# CF10_STAGE4CP0_RESULT_TRANSPORT_AUTHORITY_V0_1
RESULT_TRANSPORT_POLICY_REF = (
    "coordination/registry/cf10_worker_result_transport_policy_v0_1.yaml"
)
RESULT_TRANSPORT_POLICY_SCHEMA = (
    "forprint_cf10_worker_result_transport_policy_v0_1"
)
RESULT_TRANSPORT_SELECTION_SCHEMA = (
    "forprint_cf10_result_transport_selection_v0_1"
)
LEGACY_RESULT_TRANSPORT = "handoff-v2-full"
DRAFT_RESULT_TRANSPORT = "worker-completion-draft-v0-1"
_RESULT_TRANSPORTS = [LEGACY_RESULT_TRANSPORT, DRAFT_RESULT_TRANSPORT]


class CF10TrainingDispatchError(RuntimeError):
    pass


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise CF10TrainingDispatchError(f"{label} missing: {path}")
    if path.is_symlink():
        raise CF10TrainingDispatchError(f"{label} must not be a symlink: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CF10TrainingDispatchError(f"{label} must be a mapping")
    return value


def _sha256_file(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise CF10TrainingDispatchError(f"hash input missing or unsafe: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validated_governed_worker_context_digest(
    ready_execution: dict[str, Any],
) -> str:
    context = ready_execution.get("governed_worker_context")
    if not isinstance(context, dict):
        raise CF10TrainingDispatchError(
            "governed Worker context missing from ready execution"
        )
    if context.get("schema_version") != (
        "forprint_governed_worker_context_projection_v0_1"
    ):
        raise CF10TrainingDispatchError(
            "governed Worker context schema invalid"
        )

    declared = ready_execution.get("governed_worker_context_sha256")
    if not isinstance(declared, str) or not SHA256_RE.fullmatch(declared):
        raise CF10TrainingDispatchError(
            "governed Worker context digest missing or invalid"
        )
    recomputed = dispatch.governed_worker_context_sha256(context)
    if recomputed != declared:
        raise CF10TrainingDispatchError(
            "governed Worker context digest drift"
        )

    handoff = ready_execution.get("handoff_manifest_sha256")
    if context.get("handoff_manifest_sha256") != handoff:
        raise CF10TrainingDispatchError(
            "governed Worker context Handoff binding drift"
        )

    authority = context.get("authority")
    if not isinstance(authority, dict):
        raise CF10TrainingDispatchError(
            "governed Worker context authority missing"
        )
    required_false = (
        "context_grants_authority",
        "dispatch_authority_granted",
        "release_authority_granted",
        "cross_repository_write_authority_granted",
    )
    widened = [
        key for key in required_false
        if authority.get(key) is not False
    ]
    if widened:
        raise CF10TrainingDispatchError(
            "governed Worker context authority widened: "
            + ",".join(widened)
        )
    return declared


def _safe_repo_file(root: Path, base: Path, raw: str, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise CF10TrainingDispatchError(f"{label} must be a non-empty string")
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts:
        raise CF10TrainingDispatchError(f"{label} escapes repository scope")
    path = (root / base / relative).resolve()
    expected = (root / base).resolve()
    try:
        path.relative_to(expected)
    except ValueError as exc:
        raise CF10TrainingDispatchError(f"{label} escapes expected root") from exc
    if not path.is_file() or path.is_symlink():
        raise CF10TrainingDispatchError(f"{label} missing or unsafe: {path}")
    return path


def _find_work_front(root: Path, work_front_id: str) -> tuple[Path, dict[str, Any]]:
    matches: list[tuple[Path, dict[str, Any]]] = []
    front_root = (root / WORK_FRONT_ROOT).resolve()
    for path in sorted(front_root.glob("*.yaml")):
        if path.is_symlink():
            continue
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(value, dict) and value.get("work_front_id") == work_front_id:
            matches.append((path, value))
    if len(matches) != 1:
        raise CF10TrainingDispatchError(
            f"expected exactly one Work Front for {work_front_id}, found {len(matches)}"
        )
    return matches[0]


def _training_task_ref(front: dict[str, Any]) -> str:
    provenance = front.get("provenance")
    refs = provenance.get("source_refs") if isinstance(provenance, dict) else None
    if not isinstance(refs, list):
        raise CF10TrainingDispatchError("Work Front provenance.source_refs missing")
    values = [
        item.split(":", 1)[1]
        for item in refs
        if isinstance(item, str) and item.startswith("training_task:")
    ]
    if len(values) != 1 or not values[0]:
        raise CF10TrainingDispatchError(
            "Work Front must bind exactly one training_task provenance ref"
        )
    return values[0]


def _profile_ref(task: dict[str, Any]) -> tuple[str, str]:
    profile = task.get("execution_profile")
    if not isinstance(profile, dict):
        raise CF10TrainingDispatchError("Worker Task execution_profile missing")
    profile_id = profile.get("profile_id")
    revision = profile.get("revision")
    if not isinstance(profile_id, str) or not profile_id:
        raise CF10TrainingDispatchError("Worker Task profile_id invalid")
    if not isinstance(revision, str) or not revision:
        raise CF10TrainingDispatchError("Worker Task profile revision invalid")
    return profile_id, f"{profile_id}@{revision}"


def _procedure_id(task: dict[str, Any]) -> str:
    procedure = task.get("procedure")
    if not isinstance(procedure, dict):
        raise CF10TrainingDispatchError("Worker Task procedure missing")
    procedure_id = procedure.get("procedure_id")
    if not isinstance(procedure_id, str) or not procedure_id:
        raise CF10TrainingDispatchError("Worker Task procedure_id invalid")
    return procedure_id


def _validate_task_boundaries(task: dict[str, Any]) -> None:
    workspace = task.get("workspace")
    authority = task.get("authority")
    if not isinstance(workspace, dict) or not isinstance(authority, dict):
        raise CF10TrainingDispatchError("Worker Task boundary blocks missing")
    if workspace.get("isolated_workspace_required") is not True:
        raise CF10TrainingDispatchError("isolated workspace must be required")
    if workspace.get("candidate_only") is not True:
        raise CF10TrainingDispatchError("training task must remain candidate-only")
    if workspace.get("canonical_write_allowed") is not False:
        raise CF10TrainingDispatchError("canonical worker writes must remain forbidden")
    forbidden = (
        "task_artifact_grants_authority",
        "dispatch_authority",
        "release_authority",
        "push_authority",
        "merge_authority",
        "foreign_write_authority",
        "automatic_accept",
        "widening_requested",
    )
    widened = [key for key in forbidden if authority.get(key) is not False]
    if widened:
        raise CF10TrainingDispatchError(
            "Worker Task authority widened: " + ",".join(widened)
        )
    if authority.get("execution_authority_source") != "WORK_FRONT":
        raise CF10TrainingDispatchError("Work Front must remain execution authority")


def resolve_training_task(*, root: Path, task_prompt_id: str) -> dict[str, Any]:
    root = Path(root).resolve()
    index = _load_yaml(root / WORKER_TASK_INDEX, "Worker Task index")
    entries = index.get("tasks")
    if not isinstance(entries, list):
        raise CF10TrainingDispatchError("Worker Task index tasks missing")
    matches = [
        item
        for item in entries
        if isinstance(item, dict) and item.get("task_id") == task_prompt_id
    ]
    if len(matches) != 1:
        raise CF10TrainingDispatchError(
            f"task must be materialized exactly once: {task_prompt_id}"
        )
    entry = matches[0]
    if entry.get("work_id") != "u180j":
        raise CF10TrainingDispatchError("training task must belong to u180j")
    if entry.get("status") != "READY_FOR_CONTEXT":
        raise CF10TrainingDispatchError("training task is not READY_FOR_CONTEXT")

    task_path = _safe_repo_file(
        root,
        WORKER_TASK_ROOT,
        str(entry.get("file", "")),
        "Worker Task file",
    )
    task = _load_yaml(task_path, "Worker Task")
    if task.get("task_id") != task_prompt_id:
        raise CF10TrainingDispatchError("Worker Task identity mismatch")
    if task.get("module_id") != "forprint_system_blueprint":
        raise CF10TrainingDispatchError("training task module mismatch")
    work = task.get("work")
    if not isinstance(work, dict) or work.get("work_id") != "u180j":
        raise CF10TrainingDispatchError("Worker Task work binding invalid")
    work_front_id = work.get("work_front_id")
    if work_front_id != entry.get("work_front_id"):
        raise CF10TrainingDispatchError("Worker Task index Work Front mismatch")
    if not isinstance(work_front_id, str) or not work_front_id:
        raise CF10TrainingDispatchError("Worker Task Work Front missing")

    _validate_task_boundaries(task)
    profile_id, profile_ref = _profile_ref(task)
    procedure_id = _procedure_id(task)

    front_path, front = _find_work_front(root, work_front_id)
    training_task_id = _training_task_ref(front)

    queue = _load_yaml(root / TRAINING_QUEUE, "CF-10 training queue")
    if queue.get("work_id") != "u180j" or queue.get("step_id") != "CF-10":
        raise CF10TrainingDispatchError("training queue CF-10 binding invalid")
    queue_tasks = queue.get("tasks")
    if not isinstance(queue_tasks, list):
        raise CF10TrainingDispatchError("training queue tasks missing")
    queue_matches = [
        item
        for item in queue_tasks
        if isinstance(item, dict) and item.get("task_id") == training_task_id
    ]
    if len(queue_matches) != 1:
        raise CF10TrainingDispatchError(
            f"training task missing/duplicated in queue: {training_task_id}"
        )
    queue_task = queue_matches[0]
    order = queue_task.get("order")
    if not isinstance(order, int) or isinstance(order, bool) or order < 30:
        raise CF10TrainingDispatchError(
            "reusable training adapter is limited to queue task order >= 30"
        )

    return {
        "work_id": "u180j",
        "module": "forprint_system_blueprint",
        "task_prompt_id": task_prompt_id,
        "training_task_id": training_task_id,
        "training_order": order,
        "work_front_id": work_front_id,
        "work_front_ref": str(front_path.relative_to(root)),
        "task_ref": str(task_path.relative_to(root)),
        "execution_profile": profile_id,
        "profile_ref": profile_ref,
        "procedure_id": procedure_id,
        "candidate_only": True,
    }


def _validate_attempt_id(attempt_id: str) -> None:
    match = ATTEMPT_RE.fullmatch(attempt_id)
    if not match:
        raise CF10TrainingDispatchError("invalid CF-10 training attempt_id")
    if int(match.group(1)) < 4:
        raise CF10TrainingDispatchError(
            "reusable training adapter starts at cf10-u180j-a004"
        )


def assert_attempt_unused(
    *,
    root: Path,
    attempt_id: str,
    store_override: Path | None = None,
) -> None:
    _validate_attempt_id(attempt_id)
    root = Path(root).resolve()
    if store_override is None:
        contract = attempt_ledger.load_contract(root)
        store = attempt_ledger.store_root(root, contract, None)
    else:
        store = Path(store_override).resolve()
    if attempt_ledger.records_for_attempt(store, attempt_id):
        raise CF10TrainingDispatchError(
            f"attempt_id already exists in immutable ledger history: {attempt_id}"
        )


# CF10_STAGE4CP0_POLICY_AND_SELECTION_PROOF_V0_1_START

def _transport_exact_string(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(c) < 32 for c in value)
        or "*" in value
        or "?" in value
    ):
        raise CF10TrainingDispatchError(f"invalid result transport {label}")
    return value


def _transport_task_identity(binding: dict[str, Any]) -> dict[str, str]:
    if not isinstance(binding, dict):
        raise CF10TrainingDispatchError("result transport task binding must be a mapping")
    task = _transport_exact_string(binding.get("task_prompt_id"), "task_prompt_id")
    front_id = _transport_exact_string(binding.get("work_front_id"), "work_front_id")
    front_ref = _transport_exact_string(binding.get("work_front_ref"), "work_front_ref")
    relative = Path(front_ref)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or relative.as_posix() != front_ref
        or not front_ref.startswith("coordination/work_fronts/")
        or not front_ref.endswith(".yaml")
    ):
        raise CF10TrainingDispatchError("result transport Work Front reference invalid")
    return {
        "task_prompt_id": task,
        "work_front_id": front_id,
        "work_front_ref": front_ref,
    }


def validate_result_transport_policy_data(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CF10TrainingDispatchError("transport policy must be a mapping")
    keys = {
        "schema_version", "status", "revision", "grants_authority",
        "default_transport", "allowed_transports", "opt_in_bindings",
    }
    if set(value) != keys:
        raise CF10TrainingDispatchError("transport policy fields drift")
    if value["schema_version"] != RESULT_TRANSPORT_POLICY_SCHEMA:
        raise CF10TrainingDispatchError("transport policy schema mismatch")
    if value["status"] != "current_standard":
        raise CF10TrainingDispatchError("transport policy not current")
    if value["revision"] != "0.1.0":
        raise CF10TrainingDispatchError("transport policy revision mismatch")
    if value["grants_authority"] is not False:
        raise CF10TrainingDispatchError("transport policy grants forbidden authority")
    if value["default_transport"] != LEGACY_RESULT_TRANSPORT:
        raise CF10TrainingDispatchError("transport policy default must remain legacy")
    if value["allowed_transports"] != _RESULT_TRANSPORTS:
        raise CF10TrainingDispatchError("transport policy allowed values drift")
    bindings = value["opt_in_bindings"]
    if not isinstance(bindings, list):
        raise CF10TrainingDispatchError("transport policy opt-in must be a list")
    seen: set[tuple[str, str, str]] = set()
    for entry in bindings:
        if not isinstance(entry, dict) or set(entry) != {
            "task_prompt_id", "work_front_id", "work_front_ref", "transport"
        }:
            raise CF10TrainingDispatchError("transport opt-in fields invalid")
        identity = _transport_task_identity(entry)
        if entry["transport"] != DRAFT_RESULT_TRANSPORT:
            raise CF10TrainingDispatchError("transport opt-in must select known draft")
        identifier = tuple(identity[k] for k in (
            "task_prompt_id", "work_front_id", "work_front_ref"
        ))
        if identifier in seen:
            raise CF10TrainingDispatchError("transport opt-in duplicate binding")
        seen.add(identifier)
    return value


def _load_result_transport_policy(root: Path) -> tuple[dict[str, Any], str]:
    path = Path(root).resolve() / RESULT_TRANSPORT_POLICY_REF
    if not path.is_file() or path.is_symlink():
        raise CF10TrainingDispatchError("transport policy missing or unsafe")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        class NoDuplicateKeysLoader(yaml.SafeLoader):
            pass

        def no_duplicates(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode) -> dict:
            pairs: dict[Any, Any] = {}
            for key_node, value_node in node.value:
                key = loader.construct_object(key_node, deep=True)
                if not isinstance(key, str) or key in pairs:
                    raise CF10TrainingDispatchError("transport policy duplicate/invalid key")
                pairs[key] = loader.construct_object(value_node, deep=True)
            return pairs

        NoDuplicateKeysLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, no_duplicates,
        )
        value = yaml.load(raw.decode("utf-8"), Loader=NoDuplicateKeysLoader)
    except (yaml.YAMLError, UnicodeDecodeError) as exc:
        raise CF10TrainingDispatchError("transport policy YAML invalid") from exc
    return validate_result_transport_policy_data(value), digest


def resolve_result_transport_selection(
    *, root: Path, task_binding: dict[str, Any],
) -> dict[str, Any]:
    identity = _transport_task_identity(task_binding)
    policy, digest = _load_result_transport_policy(root)
    selected = LEGACY_RESULT_TRANSPORT
    for entry in policy["opt_in_bindings"]:
        ref = {k: entry[k] for k in identity}
        overlap = [key for key in identity if identity[key] == ref[key]]
        if len(overlap) == len(identity):
            selected = DRAFT_RESULT_TRANSPORT
        elif overlap:
            raise CF10TrainingDispatchError("partial transport opt-in identity drift")
    return {
        "schema_version": RESULT_TRANSPORT_SELECTION_SCHEMA,
        "transport": selected,
        "policy_ref": RESULT_TRANSPORT_POLICY_REF,
        "policy_sha256": digest,
        "policy_revision": policy["revision"],
        **identity,
    }


def _verify_execution_transport_selection(
    *, root: Path, execution: dict[str, Any], binding: dict[str, Any],
) -> dict[str, Any] | None:
    marker = execution.get("result_transport_policy_sha256")
    selection = execution.get("result_transport_selection")
    marker_present = "result_transport_policy_sha256" in execution
    selection_present = "result_transport_selection" in execution
    if not marker_present and not selection_present:
        # Historical legacy prepared records contain no selector or provenance.
        return None
    if not marker_present or not selection_present:
        raise CF10TrainingDispatchError("declared result transport selection incomplete")
    expected = resolve_result_transport_selection(root=root, task_binding=binding)
    if not isinstance(selection, dict) or selection != expected:
        raise CF10TrainingDispatchError("result transport selection binding drift")
    if marker != expected["policy_sha256"]:
        raise CF10TrainingDispatchError("result transport policy provenance drift")
    return expected

# CF10_STAGE4CP0_POLICY_AND_SELECTION_PROOF_V0_1_END


def prepare_training_pre_dispatch(
    *,
    root: Path,
    task_prompt_id: str,
    worker_id: str,
    attempt_id: str,
    blueprint_ai_trial_ready: bool = False,
    ledger_store_override: Path | None = None,
    runner=None,
) -> dict[str, Any]:
    if blueprint_ai_trial_ready is not False:
        raise CF10TrainingDispatchError(
            "CF-10 training adapter requires BLUEPRINT_AI_TRIAL_READY=false"
        )
    if worker_id != "worker-01":
        raise CF10TrainingDispatchError("CF-10 training worker must be worker-01")

    root = Path(root).resolve()
    binding = resolve_training_task(root=root, task_prompt_id=task_prompt_id)
    assert_attempt_unused(
        root=root,
        attempt_id=attempt_id,
        store_override=ledger_store_override,
    )

    prepared = dispatch.prepare_cf09_task_execution(
        root=root,
        work_front=binding["work_front_ref"],
        execution_profile=binding["execution_profile"],
        task_prompt_id=binding["task_prompt_id"],
        task_module_root=".",
        module=binding["module"],
        procedure_id=binding["procedure_id"],
        runner=runner,
    )
    if prepared.get("state") != "AWAITING_ASSISTANT_ACK":
        raise CF10TrainingDispatchError(
            "training preparation must stop at AWAITING_ASSISTANT_ACK"
        )
    if prepared.get("assistant_ack_validated") is not False:
        raise CF10TrainingDispatchError("training preparation cannot consume ACK")

    authority = prepared.get("authority")
    if not isinstance(authority, dict):
        raise CF10TrainingDispatchError("prepared authority block missing")
    forbidden = (
        "execution_authority_granted",
        "dispatch_authority_granted",
        "worker_dispatch_performed",
        "external_dispatch_allowed",
        "release_allowed",
        "push_allowed",
        "merge_allowed",
    )
    widened = [key for key in forbidden if authority.get(key) is not False]
    if widened:
        raise CF10TrainingDispatchError(
            "pre-dispatch authority widened: " + ",".join(widened)
        )

    result = dict(prepared)
    result["cf10_training_binding"] = binding
    # Preserve selected transport and raw policy byte digest across ACK and dispatch.
    selection = resolve_result_transport_selection(root=root, task_binding=binding)
    result["result_transport_selection"] = copy.deepcopy(selection)
    result["result_transport_policy_sha256"] = selection["policy_sha256"]
    result["worker_id"] = worker_id
    result["attempt_id"] = attempt_id
    result["workspace_required_before_dispatch"] = True
    result["worker_process_launch_allowed"] = False
    result["canonical_attempt_ledger_append_allowed"] = False
    return result


def build_training_canonical_ack(
    *,
    root: Path,
    prepared_execution: dict[str, Any],
    source_state_fingerprint: str,
    worker_id: str,
    attempt_id: str,
) -> dict[str, Any]:
    root = Path(root).resolve()
    if worker_id != "worker-01":
        raise CF10TrainingDispatchError("CF-10 training worker must be worker-01")
    _validate_attempt_id(attempt_id)
    if prepared_execution.get("mode") != "TASK_EXECUTION":
        raise CF10TrainingDispatchError("canonical ACK requires TASK_EXECUTION")
    if prepared_execution.get("state") != "AWAITING_ASSISTANT_ACK":
        raise CF10TrainingDispatchError(
            "canonical ACK requires AWAITING_ASSISTANT_ACK"
        )
    if prepared_execution.get("assistant_ack_validated") is not False:
        raise CF10TrainingDispatchError("canonical ACK cannot rebuild consumed ACK")
    if prepared_execution.get("attempt_id") != attempt_id:
        raise CF10TrainingDispatchError("canonical ACK attempt binding mismatch")
    if prepared_execution.get("worker_id") != worker_id:
        raise CF10TrainingDispatchError("canonical ACK worker binding mismatch")
    if not SHA256_RE.fullmatch(source_state_fingerprint):
        raise CF10TrainingDispatchError(
            "source_state_fingerprint must be sha256 hex"
        )

    binding = prepared_execution.get("cf10_training_binding")
    if not isinstance(binding, dict):
        raise CF10TrainingDispatchError("training binding missing")
    resolved = resolve_training_task(
        root=root,
        task_prompt_id=str(binding.get("task_prompt_id", "")),
    )
    if binding != resolved:
        raise CF10TrainingDispatchError("prepared training binding is stale")

    manifest = prepared_execution.get("handoff_manifest_sha256")
    if not isinstance(manifest, str) or not SHA256_RE.fullmatch(manifest):
        raise CF10TrainingDispatchError("prepared Handoff manifest hash invalid")

    constitution = (
        root / "coordination/standards/governance/project_constitution_v0_1.yaml"
    )
    module_policy = (
        root
        / "coordination/module_policy/forprint_system_blueprint/module_policy.md"
    )
    work_front = root / binding["work_front_ref"]
    profiles = root / "coordination/registry/execution_profiles_v0_1.yaml"
    procedure = (
        root
        / "coordination/registry/governed_canonical_mutation_procedure_v0_1.yaml"
    )

    return {
        "schema_version": "forprint_assistant_handoff_v2_ack_v0_1",
        "handoff_manifest_sha256": manifest,
        "launch_mode": "TASK_EXECUTION",
        "context_fingerprint": source_state_fingerprint,
        "authority_ack": {
            "scope": "CF10_U180J_MATERIALIZED_TRAINING_TASK_ONLY",
            "project_constitution_sha256": _sha256_file(constitution),
            "module_policy_sha256": _sha256_file(module_policy),
            "authority_widening": False,
        },
        "work_front_ack": {
            "work_front_id": binding["work_front_id"],
            "work_front_ref": binding["work_front_ref"],
            "sha256": _sha256_file(work_front),
        },
        "profile_ack": {
            "profile_ref": binding["profile_ref"],
            "registry_sha256": _sha256_file(profiles),
        },
        "procedure_ack": {
            "procedure_id": binding["procedure_id"],
            "sha256": _sha256_file(procedure),
        },
        "freshness_ack": {
            "source_state_fingerprint": source_state_fingerprint,
            "worker_id": worker_id,
            "attempt_id": attempt_id,
            "workspace_equivalence_required": True,
        },
    }


def validate_training_assistant_ack(
    *,
    root: Path,
    prepared_execution: dict[str, Any],
    assistant_ack: dict[str, Any],
    expected_ack: dict[str, Any],
) -> dict[str, Any]:
    # The existing ACK validator remains the authority gate; transport is
    # checked against the exact prepared binding before and after that gate.
    binding = prepared_execution.get("cf10_training_binding")
    if not isinstance(binding, dict):
        raise CF10TrainingDispatchError("prepared training binding missing")
    frozen_selection = _verify_execution_transport_selection(
        root=root, execution=prepared_execution, binding=binding,
    )
    ready = dispatch.validate_cf09_assistant_ack(
        root=root,
        prepared_execution=prepared_execution,
        assistant_ack=assistant_ack,
        expected_ack=expected_ack,
        expected_ack_source="DISPATCHER_CANONICAL_BINDING",
    )
    if frozen_selection is None:
        if "result_transport_selection" in ready or "result_transport_policy_sha256" in ready:
            raise CF10TrainingDispatchError("unbound result transport introduced by ACK")
    else:
        if ready.get("result_transport_selection") != frozen_selection:
            raise CF10TrainingDispatchError("ACK result transport selection drift")
        if ready.get("result_transport_policy_sha256") != frozen_selection["policy_sha256"]:
            raise CF10TrainingDispatchError("ACK result transport policy digest drift")
        ready["result_transport_selection"] = copy.deepcopy(frozen_selection)
    if ready.get("state") != "READY_FOR_EXPLICIT_DISPATCH":
        raise CF10TrainingDispatchError(
            "validated training ACK did not reach READY_FOR_EXPLICIT_DISPATCH"
        )
    if ready.get("assistant_ack_validated") is not True:
        raise CF10TrainingDispatchError("training ACK validation marker missing")
    return ready


def authorize_training_explicit_dispatch(
    *,
    root: Path,
    ready_execution: dict[str, Any],
    worker_id: str,
    attempt_id: str,
    source_state_fingerprint: str,
    workspace_repo: Path,
    runtime_provider: str,
    runtime_model: str,
    ledger_store_override: Path | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    if ready_execution.get("state") != "READY_FOR_EXPLICIT_DISPATCH":
        raise CF10TrainingDispatchError(
            "execution must be READY_FOR_EXPLICIT_DISPATCH"
        )
    if ready_execution.get("assistant_ack_validated") is not True:
        raise CF10TrainingDispatchError(
            "Assistant ACK must be validated before explicit dispatch"
        )
    if worker_id != "worker-01":
        raise CF10TrainingDispatchError("CF-10 training worker must be worker-01")
    _validate_attempt_id(attempt_id)
    if ready_execution.get("attempt_id") != attempt_id:
        raise CF10TrainingDispatchError("explicit dispatch attempt mismatch")
    if ready_execution.get("worker_id") != worker_id:
        raise CF10TrainingDispatchError("explicit dispatch worker mismatch")
    if not SHA256_RE.fullmatch(source_state_fingerprint):
        raise CF10TrainingDispatchError(
            "source_state_fingerprint must be sha256 hex"
        )
    if runtime_provider != "github_copilot_cli":
        raise CF10TrainingDispatchError(
            "current CF-10 training provider must be github_copilot_cli"
        )
    if runtime_model != "auto":
        raise CF10TrainingDispatchError(
            "current CF-10 training model selection must be auto"
        )

    assert_attempt_unused(
        root=root,
        attempt_id=attempt_id,
        store_override=ledger_store_override,
    )

    binding = ready_execution.get("cf10_training_binding")
    if not isinstance(binding, dict):
        raise CF10TrainingDispatchError("training binding missing")
    resolved = resolve_training_task(
        root=root,
        task_prompt_id=str(binding.get("task_prompt_id", "")),
    )
    if binding != resolved:
        raise CF10TrainingDispatchError("ready training binding is stale")

    required = {
        "module": binding["module"],
        "work_front_id": binding["work_front_ref"],
        "task_prompt_id": binding["task_prompt_id"],
        "procedure_id": binding["procedure_id"],
    }
    drift = [
        key
        for key, expected in required.items()
        if ready_execution.get(key) != expected
    ]
    if drift:
        raise CF10TrainingDispatchError(
            "ready execution binding drift: " + ",".join(drift)
        )
    profile = ready_execution.get("execution_profile_ref")
    if profile not in {
        binding["execution_profile"],
        binding["profile_ref"],
    }:
        raise CF10TrainingDispatchError("ready execution profile mismatch")

    gate = ready_execution.get("work_front_gate")
    if not isinstance(gate, dict) or gate.get("validated") is not True:
        raise CF10TrainingDispatchError("ready Work Front gate invalid")
    if gate.get("work_front_id") != binding["work_front_id"]:
        raise CF10TrainingDispatchError("ready Work Front ID mismatch")

    authority = ready_execution.get("authority")
    if not isinstance(authority, dict):
        raise CF10TrainingDispatchError("ready authority block missing")
    forbidden = (
        "execution_authority_granted",
        "dispatch_authority_granted",
        "worker_dispatch_performed",
        "external_dispatch_allowed",
        "release_allowed",
        "push_allowed",
        "merge_allowed",
    )
    widened = [key for key in forbidden if authority.get(key) is not False]
    if widened:
        raise CF10TrainingDispatchError(
            "forbidden pre-dispatch authority widening: " + ",".join(widened)
        )

    # The explicit decision hash must cover the exact transport and policy
    # source selected during the prepared stage; never use Worker stdout/env.
    frozen_transport_selection = _verify_execution_transport_selection(
        root=root, execution=ready_execution, binding=binding,
    )
    governed_context_sha = _validated_governed_worker_context_digest(
        ready_execution
    )

    workspace = Path(workspace_repo).expanduser().resolve()
    suffix = Path(
        "forprint_system_blueprint/worker-01/"
        f"{attempt_id}/workspace/repo"
    )
    if not workspace.is_dir():
        raise CF10TrainingDispatchError("isolated workspace repo is missing")
    if tuple(workspace.parts[-len(suffix.parts):]) != suffix.parts:
        raise CF10TrainingDispatchError(
            "workspace repo is outside exact CF-10 attempt layout"
        )

    decision_binding = {
        "work_id": "u180j",
        "worker_id": worker_id,
        "attempt_id": attempt_id,
        "task_prompt_id": binding["task_prompt_id"],
        "training_task_id": binding["training_task_id"],
        "training_order": binding["training_order"],
        "source_state_fingerprint": source_state_fingerprint,
        "work_front_id": binding["work_front_id"],
        "work_front_ref": binding["work_front_ref"],
        "profile_ref": binding["profile_ref"],
        "procedure_id": binding["procedure_id"],
        "runtime_provider": runtime_provider,
        "runtime_model": runtime_model,
        "workspace_repo": str(workspace),
        "governed_worker_context_sha256": governed_context_sha,
    }
    if frozen_transport_selection is not None:
        decision_binding["result_transport_selection"] = copy.deepcopy(
            frozen_transport_selection
        )
    decision_id = hashlib.sha256(
        json.dumps(
            decision_binding,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return {
        "schema_version": "forprint_cf10_internal_explicit_dispatch_decision_v0_1",
        "decision_id": decision_id,
        "decision": "ALLOW_EXACT_CF10_TRAINING_WORKER_LAUNCH",
        "binding": decision_binding,
        "assistant_ack_validated": True,
        "explicit_dispatch_decision_recorded": True,
        "worker_process_launch_allowed": True,
        "canonical_attempt_ledger_append_allowed": True,
        "external_dispatch_allowed": False,
        "release_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "foreign_repository_write_allowed": False,
        "automatic_accept_allowed": False,
        "grants_broad_dispatch_authority": False,
    }
