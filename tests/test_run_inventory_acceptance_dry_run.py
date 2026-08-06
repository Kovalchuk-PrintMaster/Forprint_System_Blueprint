from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "coordination" / "run_inventory_acceptance_dry_run.py"
INDEX = (
    ROOT
    / "coordination"
    / "internal_work"
    / "blueprint"
    / "inventory_refresh"
    / "2026-07-30__blueprint__"
    "inventory_acceptance_evidence_index_v0_1.yaml"
)
INDEX_VALIDATION = ROOT / "reports" / "inventory_acceptance_evidence_index_validation_report.yaml"
RCI = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "inventory"
    / "2026-07-30__forprint_system_blueprint__"
    "repository_capability_inventory_v0_4.yaml"
)
REDM = (
    ROOT
    / "coordination"
    / "repository_knowledge"
    / "flows"
    / "2026-07-30__forprint_system_blueprint__"
    "repository_execution_dependency_map_v0_4.yaml"
)
CLOSURE = ROOT / "reports" / "semantic_coverage_closure_report.yaml"
RECONCILIATION = ROOT / "reports" / "repository_knowledge_reconciliation_report.yaml"
AUTHORITY_POLICY = (
    ROOT / "coordination" / "repository_knowledge" / "artifact_authority_policy_v0_1.yaml"
)
PLAN = (
    ROOT
    / "coordination"
    / "internal_work"
    / "blueprint"
    / "inventory_refresh"
    / "2026-07-29__blueprint__inventory_refresh_plan_v0_1.yaml"
)
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
QUEUE = ROOT / "coordination" / "self_coordination" / "prompt_queue" / "index.yaml"

SPEC = importlib.util.spec_from_file_location(
    "run_inventory_acceptance_dry_run",
    MODULE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load inventory acceptance dry-run module")

MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class InventoryAcceptanceDryRunTests(unittest.TestCase):
    def execute_dry_run(
        self,
        *,
        index_path: Path = INDEX,
        rci_path: Path = RCI,
    ) -> dict:
        return MODULE.run_dry_run(
            index_path=index_path,
            index_validation_path=INDEX_VALIDATION,
            rci_path=rci_path,
            redm_path=REDM,
            closure_path=CLOSURE,
            reconciliation_path=RECONCILIATION,
            authority_policy_path=AUTHORITY_POLICY,
            plan_path=PLAN,
            roadmap_path=ROADMAP,
            queue_path=QUEUE,
            module_id="forprint_system_blueprint",
        )

    def write_yaml(
        self,
        directory: Path,
        name: str,
        data: dict,
    ) -> Path:
        path = directory / name
        path.write_text(
            yaml.safe_dump(
                data,
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        return path

    def test_canonical_dry_run_passes(self) -> None:
        report = self.execute_dry_run()

        self.assertEqual(
            report["metadata"]["result"],
            "PASSED",
            report["errors"],
        )

        phase = report["summary"]["coordination_phase"]

        self.assertIn(
            phase,
            {
                "PRE_TRANSITION",
                "POST_TRANSITION",
                "DEPENDENCY_REMEDIATION",
            },
        )

        next_prompt_required = report["summary"][
            "next_prompt_required"
        ]

        if phase == "POST_TRANSITION":
            self.assertTrue(next_prompt_required)
        else:
            self.assertFalse(next_prompt_required)
            self.assertTrue(report["summary"]["next_prompt_present"])

        if phase == "DEPENDENCY_REMEDIATION":
            self.assertEqual(
                report["summary"]["release_decision"],
                (
                    "BLOCK_INVENTORY_ACCEPTANCE_PACKET_INTEGRITY_GATE_"
                    "PENDING_DEPENDENCY_REMEDIATION"
                ),
            )
        else:
            self.assertEqual(
                report["summary"]["release_decision"],
                (
                    "PROCEED_TO_INVENTORY_ACCEPTANCE_"
                    "PACKET_INTEGRITY_GATE"
                ),
            )
        self.assertFalse(report["summary"]["candidate_acceptance_performed"])
        self.assertFalse(report["summary"]["dry_run_effects_applied"])
        self.assertEqual(
            report["summary"]["failed_scenario_count"],
            0,
        )

    def test_canonical_phase_matches_repository_state(
        self,
    ) -> None:
        report = self.execute_dry_run()
        plan = MODULE.load_yaml(PLAN)
        current = plan["metadata"]["current_step_id"]

        expected_phase = {
            MODULE.CURRENT_ID: "PRE_TRANSITION",
            MODULE.NEXT_ID: "POST_TRANSITION",
            MODULE.REMEDIATION_ID: "DEPENDENCY_REMEDIATION",
        }[current]

        self.assertEqual(
            report["summary"]["coordination_phase"],
            expected_phase,
        )

    def test_pre_transition_allows_next_prompt_absent(
        self,
    ) -> None:
        alignment = MODULE.coordination_alignment(
            {
                "metadata": {
                    "current_step_id": MODULE.CURRENT_ID,
                },
                "steps": [
                    {"step_id": MODULE.CURRENT_ID},
                    {"step_id": MODULE.NEXT_ID},
                ],
            },
            {
                "metadata": {
                    "current_step_id": MODULE.CURRENT_ID,
                },
                "steps": [
                    {"step_id": MODULE.CURRENT_ID},
                    {"step_id": MODULE.NEXT_ID},
                ],
            },
            {
                "metadata": {
                    "active_prompt_id": MODULE.CURRENT_ID,
                },
                "prompts": [
                    {"prompt_id": MODULE.CURRENT_ID},
                ],
            },
        )

        self.assertTrue(
            alignment["passed"],
            alignment["reasons"],
        )
        self.assertEqual(
            alignment["phase"],
            "PRE_TRANSITION",
        )
        self.assertFalse(alignment["next_prompt_required"])

    def test_post_transition_requires_next_prompt(
        self,
    ) -> None:
        plan = {
            "metadata": {
                "current_step_id": MODULE.NEXT_ID,
            },
            "steps": [
                {"step_id": MODULE.CURRENT_ID},
                {"step_id": MODULE.NEXT_ID},
            ],
        }
        roadmap = copy.deepcopy(plan)
        queue = {
            "metadata": {
                "active_prompt_id": MODULE.NEXT_ID,
            },
            "prompts": [
                {"prompt_id": MODULE.CURRENT_ID},
            ],
        }

        alignment = MODULE.coordination_alignment(
            plan,
            roadmap,
            queue,
        )

        self.assertFalse(alignment["passed"])
        self.assertEqual(
            alignment["phase"],
            "POST_TRANSITION",
        )
        self.assertTrue(alignment["next_prompt_required"])

        queue["prompts"].append({"prompt_id": MODULE.NEXT_ID})
        repaired = MODULE.coordination_alignment(
            plan,
            roadmap,
            queue,
        )

        self.assertTrue(
            repaired["passed"],
            repaired["reasons"],
        )

    def test_dependency_remediation_phase_is_aligned_and_gated(
        self,
    ) -> None:
        plan = {
            "metadata": {
                "current_step_id": MODULE.REMEDIATION_ID,
            },
            "steps": [
                {"step_id": MODULE.REMEDIATION_ID},
                {"step_id": MODULE.CURRENT_ID},
                {"step_id": MODULE.NEXT_ID},
            ],
        }
        roadmap = copy.deepcopy(plan)
        queue = {
            "metadata": {
                "active_prompt_id": MODULE.REMEDIATION_ID,
            },
            "prompts": [
                {"prompt_id": MODULE.REMEDIATION_ID},
                {"prompt_id": MODULE.CURRENT_ID},
                {"prompt_id": MODULE.NEXT_ID},
            ],
        }

        alignment = MODULE.coordination_alignment(
            plan,
            roadmap,
            queue,
        )

        self.assertTrue(
            alignment["passed"],
            alignment["reasons"],
        )
        self.assertEqual(
            alignment["phase"],
            "DEPENDENCY_REMEDIATION",
        )
        self.assertFalse(alignment["next_prompt_required"])
        self.assertTrue(alignment["remediation_prompt_required"])
        self.assertTrue(alignment["remediation_prompt_present"])

        queue["prompts"] = [
            {"prompt_id": MODULE.CURRENT_ID},
            {"prompt_id": MODULE.NEXT_ID},
        ]
        blocked = MODULE.coordination_alignment(
            plan,
            roadmap,
            queue,
        )

        self.assertFalse(blocked["passed"])
        self.assertIn(
            (
                "dependency-remediation prompt queue "
                "lacks the active prompt"
            ),
            blocked["reasons"],
        )

    def test_accepted_candidate_is_red(self) -> None:
        rci = MODULE.load_yaml(RCI)
        mutated = copy.deepcopy(rci)
        mutated[MODULE.RCI_SECTION]["status"] = "ACCEPTED"

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_yaml(
                Path(temporary),
                "rci.yaml",
                mutated,
            )
            report = self.execute_dry_run(rci_path=path)

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )

    def test_hidden_deferrals_is_red(self) -> None:
        index = MODULE.load_yaml(INDEX)
        mutated = copy.deepcopy(index)
        mutated["explicit_deferrals"] = []

        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_yaml(
                Path(temporary),
                "index.yaml",
                mutated,
            )
            report = self.execute_dry_run(index_path=path)

        self.assertEqual(
            report["metadata"]["result"],
            "FAILED",
        )

    def test_simulated_actions_are_non_mutating(self) -> None:
        report = self.execute_dry_run()

        self.assertTrue(
            all(
                item["status"] == "SIMULATED" and item["effect_applied"] is False
                for item in report["simulated_actions"]
            )
        )


if __name__ == "__main__":
    unittest.main()
