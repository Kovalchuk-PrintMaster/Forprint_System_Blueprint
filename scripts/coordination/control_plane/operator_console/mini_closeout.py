from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

import yaml

MILESTONES = {
    "STAGE0": "8f220bd125da7c16d0ba97ad7fb569dd3cf3a448",
    "OC01-MINI-1": "ef4ec7a482b75f9a2e1317a9d09afc5bb5e5d355",
    "OC01-MINI-2": "a7ade7fa797e554e994658a73e3f662c31b7cf91",
    "OC01-MINI-3": "c5d9cf0e68136f681af27fbc946ec6a466cd1c78",
    "OC01-MINI-4": "e50bdc08af0ee634f0f8d51693de465f060ec713",
    "OC01-MINI-5": "f6612467eaa047e3b2558120f594edd133e6209e",
    "OC01-MINI-6": "e4873e5fcf09c1bacc9fabfe235131dae22c761c",
    "OC01-MINI-7": "9247d2a8750afec0fa30c7320056d9202e0a8cc5",
    "OC01-MINI-8": "89afbb3b4f3f06c664979de788bfd9bb117c789a",
}

MINI7_PROOF_SHA = "69a4ba9935725070699dc04bf8f535d03437fa9935ecfe42d8143dc23d176c85"
MINI8_PROOF_SHA = "f8b517dcd5d7c2be9b5ee16c8a0a572f24050c7274058d49052da82c08554efb"
MINI8_SEALED_SHA = "a28218f58b5bbfac788e17b244ce0c3ac30c6ff9d23f3928773fdd6aa16972dc"
MINI8_PREVIEW_SHA = "ea3d56596034897f68950392c13ae7765bc9c4c36fb89ae3e9ff8c3fda49f85b"
COMPLETION = "USEFUL_MINIMUM_PROVEN_PARTIAL_OC01"

OPERATOR_ROADMAP = Path(
    "coordination/roadmaps/details/forprint_system_blueprint/"
    "operator_console/operator_console_program_v0_1.yaml"
)
ECP_ROADMAP = Path(
    "coordination/roadmaps/details/forprint_system_blueprint/"
    "execution_control_plane/execution_control_plane_program_v0_1.yaml"
)
DESIGN_FREEZE = Path(
    "coordination/internal_work/blueprint/operator_console/"
    "2026-10-01__oc01_mini_design_freeze_v0_1.yaml"
)
CLOSEOUT = Path(
    "coordination/internal_work/blueprint/operator_console/"
    "2026-10-02__oc01_mini_closeout_v0_1.md"
)
PROBE = Path(
    "coordination/internal_work/blueprint/operator_console/proofs/"
    "oc01_mini8_real_promotion_probe_v0_1.txt"
)

REQUIRED_MAKE_TARGETS = (
    "oc01-session-projection-check:",
    "oc01-protected-terminal-check:",
    "oc01-assistant-sandbox-check:",
    "oc01-sealed-result-check:",
    "oc01-promotion-surface-check:",
    "oc01-console-check:",
    "oc01-protected-terminal-real-proof-check:",
    "oc01-sandbox-to-canonical-real-proof-check:",
    "oc01-mini-closeout-check:",
)


class MiniCloseoutError(RuntimeError):
    pass


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def _load_yaml(root: Path, relative: Path) -> dict[str, Any]:
    path = root / relative
    if not path.is_file():
        raise MiniCloseoutError(f"required YAML missing: {relative}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise MiniCloseoutError(f"required YAML is not a mapping: {relative}")
    return value


def _require_ancestor(root: Path, label: str, commit: str) -> None:
    exists = _git(root, "cat-file", "-e", f"{commit}^{{commit}}")
    if exists.returncode != 0:
        raise MiniCloseoutError(f"milestone commit missing: {label}={commit}")
    ancestor = _git(root, "merge-base", "--is-ancestor", commit, "HEAD")
    if ancestor.returncode != 0:
        raise MiniCloseoutError(
            f"milestone is not ancestor of HEAD: {label}={commit}"
        )


def validate_closeout(root: Path | str) -> dict[str, Any]:
    repo = Path(root).expanduser().resolve()
    if not (repo / ".git").exists():
        raise MiniCloseoutError("root must be the Blueprint Git checkout")

    for label, commit in MILESTONES.items():
        _require_ancestor(repo, label, commit)

    design = _load_yaml(repo, DESIGN_FREEZE)
    acceptance = design.get("acceptance_boundary")
    if not isinstance(acceptance, dict):
        raise MiniCloseoutError("design freeze acceptance boundary missing")
    if acceptance.get("completion_meaning") != COMPLETION:
        raise MiniCloseoutError("design freeze completion meaning drift")
    if acceptance.get("must_not_claim") != "OC01_FULL_COMPLETE":
        raise MiniCloseoutError("design freeze full-complete boundary drift")

    operator = _load_yaml(repo, OPERATOR_ROADMAP)
    state = operator.get("oc01_current_implementation_state_2026_10_02")
    if not isinstance(state, dict):
        raise MiniCloseoutError("Operator Console current state missing")
    if state.get("status") != COMPLETION:
        raise MiniCloseoutError("Operator Console MINI completion state mismatch")

    implemented = state.get("implemented")
    if not isinstance(implemented, dict):
        raise MiniCloseoutError("Operator Console implemented map missing")

    for mini in range(1, 9):
        key = f"OC01-MINI-{mini}"
        row = implemented.get(key)
        if not isinstance(row, dict):
            raise MiniCloseoutError(f"Operator Console row missing: {key}")
        if row.get("state") != "PUBLISHED":
            raise MiniCloseoutError(f"{key} is not PUBLISHED")
        if row.get("commit") != MILESTONES[key]:
            raise MiniCloseoutError(f"{key} publication commit mismatch")

    if implemented["OC01-MINI-7"].get("evidence_sha256") != MINI7_PROOF_SHA:
        raise MiniCloseoutError("MINI-7 proof SHA mismatch")
    mini8 = implemented["OC01-MINI-8"]
    if mini8.get("evidence_sha256") != MINI8_PROOF_SHA:
        raise MiniCloseoutError("MINI-8 proof SHA mismatch")
    if mini8.get("preview_sha256") != MINI8_PREVIEW_SHA:
        raise MiniCloseoutError("MINI-8 preview SHA mismatch")
    if mini8.get("completion_candidate_after_publication") != COMPLETION:
        raise MiniCloseoutError("MINI-8 completion candidate mismatch")
    if mini8.get("must_not_claim") != "OC01_FULL_COMPLETE":
        raise MiniCloseoutError("MINI-8 full-complete boundary mismatch")

    completion = state.get("mini_closeout")
    if not isinstance(completion, dict):
        raise MiniCloseoutError("Operator Console mini_closeout block missing")
    if completion.get("mini_sequence_complete") is not True:
        raise MiniCloseoutError("MINI sequence is not marked complete")
    if completion.get("completion_state") != COMPLETION:
        raise MiniCloseoutError("MINI closeout completion state mismatch")
    if completion.get("oc01_full_complete") is not False:
        raise MiniCloseoutError("OC01 full completion widened")
    if completion.get("oc01_full_activated") is not False:
        raise MiniCloseoutError("OC01-FULL unexpectedly activated")

    ecp = _load_yaml(repo, ECP_ROADMAP)
    mini8_contract = ecp.get(
        "oc01_mini8_sandbox_to_canonical_real_proof_contract_2026_10_02"
    )
    if not isinstance(mini8_contract, dict):
        raise MiniCloseoutError("ECP MINI-8 contract missing")
    if mini8_contract.get("status") != "PUBLISHED":
        raise MiniCloseoutError("ECP MINI-8 contract is not PUBLISHED")
    if mini8_contract.get("publication_commit") != MILESTONES["OC01-MINI-8"]:
        raise MiniCloseoutError("ECP MINI-8 publication commit mismatch")
    proof = mini8_contract.get("proof")
    if not isinstance(proof, dict):
        raise MiniCloseoutError("ECP MINI-8 proof block missing")
    if proof.get("evidence_sha256") != MINI8_PROOF_SHA:
        raise MiniCloseoutError("ECP MINI-8 proof SHA mismatch")
    if proof.get("preview_sha256") != MINI8_PREVIEW_SHA:
        raise MiniCloseoutError("ECP MINI-8 preview SHA mismatch")

    ecp_closeout = ecp.get("oc01_mini_closeout_2026_10_02")
    if not isinstance(ecp_closeout, dict):
        raise MiniCloseoutError("ECP MINI closeout block missing")
    if ecp_closeout.get("completion_state") != COMPLETION:
        raise MiniCloseoutError("ECP MINI completion state mismatch")
    if ecp_closeout.get("mini_sequence_complete") is not True:
        raise MiniCloseoutError("ECP MINI sequence not complete")
    if ecp_closeout.get("oc01_full_complete") is not False:
        raise MiniCloseoutError("ECP widened OC01 full completion")
    if ecp_closeout.get("oc01_full_activated") is not False:
        raise MiniCloseoutError("ECP activated OC01-FULL")
    handoff = ecp_closeout.get("handoff")
    if not isinstance(handoff, dict):
        raise MiniCloseoutError("ECP MINI closeout handoff block missing")
    if handoff.get("cf10_canonical_write_reentry_allowed") is not True:
        raise MiniCloseoutError("CF10 re-entry not recorded")
    if handoff.get("cf10_must_reconcile_from_closeout_head") is not True:
        raise MiniCloseoutError("CF10 re-entry reconciliation requirement missing")

    closeout_path = repo / CLOSEOUT
    if not closeout_path.is_file():
        raise MiniCloseoutError("closeout Markdown record missing")
    closeout_text = closeout_path.read_text(encoding="utf-8")
    for token in (
        "OC01_MINI_SEQUENCE_COMPLETE=true",
        "OC01_COMPLETION_STATE=USEFUL_MINIMUM_PROVEN_PARTIAL_OC01",
        "OC01_FULL_COMPLETE=false",
        MINI7_PROOF_SHA,
        MINI8_PROOF_SHA,
        MINI8_SEALED_SHA,
        MINI8_PREVIEW_SHA,
        MILESTONES["OC01-MINI-8"],
    ):
        if token not in closeout_text:
            raise MiniCloseoutError(
                f"closeout Markdown missing required token: {token}"
            )

    probe_path = repo / PROBE
    if not probe_path.is_file():
        raise MiniCloseoutError("MINI-8 promoted proof probe missing")
    probe_text = probe_path.read_text(encoding="utf-8")
    if f"source_head={MILESTONES['OC01-MINI-7']}" not in probe_text:
        raise MiniCloseoutError("MINI-8 probe source-head binding mismatch")
    if "promotion_authority=OPERATOR_CONTROLLED_CF10" not in probe_text:
        raise MiniCloseoutError("MINI-8 probe promotion authority mismatch")

    makefile = (repo / "Makefile").read_text(encoding="utf-8")
    missing_targets = [
        target for target in REQUIRED_MAKE_TARGETS if target not in makefile
    ]
    if missing_targets:
        raise MiniCloseoutError(
            "Makefile coverage missing: " + ", ".join(missing_targets)
        )

    return {
        "schema_version": "forprint_oc01_mini_closeout_validation_v0_1",
        "result": "PASS",
        "milestone_count": len(MILESTONES),
        "mini_slice_count": 8,
        "mini_sequence_complete": True,
        "completion_state": COMPLETION,
        "oc01_full_complete": False,
        "oc01_full_activated": False,
        "protected_terminal_real_proof": "PASS",
        "sandbox_to_canonical_real_proof": "PASS",
        "stable_operator_entrypoint_coverage": "PASS",
        "cf10_canonical_write_reentry_allowed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate OC-01-MINI closeout and publication chain"
    )
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    result = validate_closeout(args.root)
    for key, value in result.items():
        if isinstance(value, bool):
            rendered = str(value).lower()
        else:
            rendered = str(value)
        print(f"{key.upper()}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
