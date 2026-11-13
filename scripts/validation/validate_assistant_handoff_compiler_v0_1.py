#!/usr/bin/env python3
"""Validate Assistant Handoff Compiler v0.1 integration."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPILER = ROOT / "scripts/coordination/build_assistant_handoff_archive.py"
CONTRACT = ROOT / "coordination/standards/automation/continuity_contract_v0_1.yaml"
ROADMAP = (
    ROOT / "coordination/roadmaps/details/forprint_system_blueprint/continuity/"
    "2026-09-10__continuity_assistant_handoff_micro_roadmap_v0_1.yaml"
)
GENERATOR_REGISTRY = ROOT / "coordination/registry/generator_derivation_registry_v0_1.yaml"
DEPENDENCY_REGISTRY = ROOT / "coordination/registry/execution_dependency_registry_v0_1.yaml"
MAKEFILE = ROOT / "Makefile"
AGENTS = ROOT / "AGENTS.md"


def fail(message: str) -> int:
    print(f"ASSISTANT_HANDOFF_COMPILER_VALIDATION=FAIL {message}")
    return 1


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"mapping required: {path}")
    return value


def main() -> int:
    _validate_bootstrap_living_handoff_contract_v0_1()
    for path in (
        COMPILER,
        CONTRACT,
        ROADMAP,
        GENERATOR_REGISTRY,
        DEPENDENCY_REGISTRY,
        MAKEFILE,
        AGENTS,
        ROOT / "coordination/bootstrap/START_HERE.md",
        ROOT / "coordination/bootstrap/index_v0_1.yaml",
    ):
        if not path.is_file():
            return fail(f"missing={path.relative_to(ROOT)}")

    contract = load_yaml(CONTRACT)
    compiler = contract.get("handoff_compiler", {})
    if compiler.get("script") != "scripts/coordination/build_assistant_handoff_archive.py":
        return fail("contract_script")
    if compiler.get("make_target") != "assistant-pack":
        return fail("contract_make_target")
    if compiler.get("validation_target") != "assistant-handoff-check":
        return fail("contract_validation_target")
    if compiler.get("authority") != "none":
        return fail("contract_authority")
    if compiler.get("chat_transcript_included") is not False:
        return fail("contract_chat_boundary")
    if compiler.get("project_source_mutation_performed") is not False:
        return fail("contract_source_mutation_boundary")

    deterministic = compiler.get("deterministic_archive", {})
    if deterministic.get("entry_order") != "lexicographic":
        return fail("archive_order")
    if deterministic.get("zip_compression") != "stored":
        return fail("archive_compression")
    if deterministic.get("manifest_self_hash_excluded") is not True:
        return fail("manifest_self_hash")

    roadmap = load_yaml(ROADMAP)
    if any("state" in row for row in roadmap.get("steps", [])):
        return fail("roadmap_manual_execution_state_forbidden")
    historical = roadmap.get("historical_completion_evidence", {})
    if historical.get("schema_version") != "forprint_legacy_roadmap_completion_evidence_v0_1":
        return fail("roadmap_historical_evidence_schema")
    if historical.get("authority") != "HISTORICAL_ACCEPTANCE_EVIDENCE_NOT_EXECUTION_STATE":
        return fail("roadmap_historical_evidence_authority")
    if historical.get("step_state_fields_retired") is not True:
        return fail("roadmap_historical_state_retirement")
    if historical.get("completed_step_ids") != [row.get("id") for row in roadmap.get("steps", [])]:
        return fail("roadmap_historical_evidence_step_set")
    steps = {row["order"]: row for row in roadmap.get("steps", [])}
    if steps.get(9, {}).get("id") != "assistant_handoff_compiler":
        return fail("roadmap_step9_id")
    if steps.get(9, {}).get("work") != "u179e":
        return fail("roadmap_step9_work")
    if steps.get(10, {}).get("id") != "lifecycle_enforcement":
        return fail("roadmap_step10_id")
    if steps.get(10, {}).get("work") != "u179f":
        return fail("roadmap_step10_work")
    if steps.get(11, {}).get("id") != "zero_context_acceptance":
        return fail("roadmap_step11_id")
    if steps.get(11, {}).get("work") != "u179g":
        return fail("roadmap_step11_work")
    if steps.get(12, {}).get("id") != "module_transfer_reference_implementation":
        return fail("roadmap_step12_id")
    if steps.get(12, {}).get("work") != "u179h":
        return fail("roadmap_step12_work")
    next_action = roadmap.get("next_action", {})
    if next_action.get("id") != "control_foundation_near_horizon":
        return fail("roadmap_next_program")
    if next_action.get("activation_requires_operator") is not True:
        return fail("roadmap_next_program_operator_gate")

    generator_registry = load_yaml(GENERATOR_REGISTRY)
    generator_rows = [
        row
        for row in generator_registry.get("generators", [])
        if row.get("id") == "assistant_handoff_archive_compiler"
    ]
    if len(generator_rows) != 1:
        return fail("generator_registration")
    row = generator_rows[0]
    if row.get("authority") != "none":
        return fail("generator_authority")
    if row.get("output_state") != "untracked_runtime_artifact":
        return fail("generator_output_state")
    if row.get("make_check_allowed") is not False:
        return fail("generator_make_check")

    dependency_registry = load_yaml(DEPENDENCY_REGISTRY)
    targets = {
        row.get("target"): row
        for row in dependency_registry.get("targets", [])
        if isinstance(row, dict)
    }
    for target in ("assistant-handoff-check", "assistant-pack"):
        if target not in targets:
            return fail(f"dependency_target={target}")
        if "continuity_event_store" not in targets[target].get("requires", []):
            return fail(f"event_store_dependency={target}")
    if targets["assistant-handoff-check"].get("side_effect_scope") != []:
        return fail("handoff_check_side_effect")
    if targets["assistant-pack"].get("side_effect_scope") != ["tmp/assistant_handoff/*.zip"]:
        return fail("assistant_pack_side_effect")

    makefile = MAKEFILE.read_text(encoding="utf-8")
    if ".PHONY: assistant-pack" not in makefile:
        return fail("make_assistant_pack")
    if ".PHONY: assistant-handoff-check" not in makefile:
        return fail("make_assistant_handoff_check")
    check_core = next(
        (line for line in makefile.splitlines() if line.startswith("check-core:")),
        "",
    )
    if "assistant-handoff-check" not in check_core.split():
        return fail("check_core_binding")
    if "assistant-pack" in check_core.split():
        return fail("mutating_pack_in_check_core")

    agents = AGENTS.read_text(encoding="utf-8")
    if "<!-- FORPRINT_ASSISTANT_HANDOFF_COMPILER_START -->" not in agents:
        return fail("agents_binding")
    if "make assistant-pack" not in agents:
        return fail("agents_operator_surface")

    sterile_gate = os.environ.get("FORPRINT_MUTATION_COMPILER_STERILE_GATE") == "1"
    if not (ROOT / ".git").exists():
        if not sterile_gate:
            return fail("git_worktree_required_for_runtime_validation")
        print("RUNTIME_VALIDATE_ONLY=DEFERRED_STERILE_MUTATION_COMPILER_GATE")
    else:
        cp = subprocess.run(
            [
                sys.executable,
                "scripts/coordination/build_assistant_handoff_archive.py",
                "--root",
                ".",
                "--validate-only",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if cp.returncode:
            return fail("validate_only\n" + cp.stdout)
        if "ASSISTANT_HANDOFF_COMPILER=PASS" not in cp.stdout:
            return fail("validate_only_marker")
        if "MUTATION_PERFORMED=false" not in cp.stdout:
            return fail("validate_only_mutation_marker")

    print("ASSISTANT_HANDOFF_COMPILER_VALIDATION=PASS")
    print("MAKE_TARGET=assistant-pack")
    print("VALIDATION_TARGET=assistant-handoff-check")
    print("DETERMINISTIC_ARCHIVE=true")
    print("CHAT_TRANSCRIPT_INCLUDED=false")
    print("AUTHORITY=none")
    print("NEXT_PROGRAM=control_foundation_near_horizon")
    return 0



def _validate_bootstrap_living_handoff_contract_v0_1() -> None:
    import io
    import sys
    import zipfile
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]

    # Direct script execution sets sys.path[0] to scripts/validation.
    # Anchor imports to this repository root so the validator checks
    # the same sandbox/runtime sources as make assistant-pack.
    root_token = str(root)

    sys.path[:] = [
        entry
        for entry in sys.path
        if entry != root_token
    ]

    sys.path.insert(
        0,
        root_token,
    )

    from scripts.coordination import (
        blueprint_continuity_adapter_v0_1 as adapter,
    )

    expected_adapter_path = (
        root
        / "scripts/coordination/blueprint_continuity_adapter_v0_1.py"
    ).resolve()

    actual_adapter_path = Path(
        adapter.__file__
    ).resolve()

    if actual_adapter_path != expected_adapter_path:
        raise ValueError(
            "assistant handoff validator imported adapter from unexpected root: "
            + str(actual_adapter_path)
        )

    required = {
        'coordination/instruction_intake/assistant_reading_order.md', 'coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_2.yaml', 'coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml', 'coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md', 'coordination/repository_knowledge/roadmap_enrichment/README.md', 'coordination/repository_knowledge/roadmap_enrichment/source_map.yaml'
    }

    blob, _manifest, _name = adapter.expected_archive(root)

    with zipfile.ZipFile(io.BytesIO(blob), "r") as archive:
        names = set(archive.namelist())

        missing = required - names

        if missing:
            raise ValueError(
                "assistant handoff missing Bootstrap/Living surfaces: "
                + ", ".join(sorted(missing))
            )

        for rel in sorted(required):
            archive_bytes = archive.read(rel)
            canonical_bytes = (root / rel).read_bytes()

            if archive_bytes != canonical_bytes:
                raise ValueError(
                    "assistant handoff surface bytes mismatch: "
                    + rel
                )

        read_first = archive.read(
            "00_READ_FIRST.md"
        ).decode("utf-8")

        if "coordination/instruction_intake/assistant_reading_order.md" not in read_first:
            raise ValueError(
                "00_READ_FIRST does not route to assistant_reading_order"
            )

        reading_order = archive.read(
            "coordination/instruction_intake/assistant_reading_order.md"
        ).decode("utf-8")

        for rel in (
            "coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_2.yaml",
            "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml",
            "coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md",
            "coordination/repository_knowledge/roadmap_enrichment/README.md",
            "coordination/repository_knowledge/roadmap_enrichment/source_map.yaml",
        ):
            if rel not in reading_order:
                raise ValueError(
                    "assistant_reading_order missing route: "
                    + rel
                )


if __name__ == "__main__":
    raise SystemExit(main())
