from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(".")
CANDIDATE_ROOT = Path(
    "coordination/internal_work/blueprint/prompt_candidates/logistics_service/"
    "logistics_service_authority_lineage_and_module_bootstrap_v0_2"
)
MANIFEST = CANDIDATE_ROOT / "replacement_candidate_manifest_v0_1.yaml"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    if data["candidate_state"] != "READY_FOR_EXPLICIT_RELEASE_AUTHORIZATION":
        print("LOGISTICS_BOOTSTRAP_PROMPT_V0_2_CANDIDATE=FAIL state")
        return 1
    if data["released"] is not False:
        print("LOGISTICS_BOOTSTRAP_PROMPT_V0_2_CANDIDATE=FAIL released")
        return 1
    if data["old_release_authorization_inherited"] is not False:
        print("LOGISTICS_BOOTSTRAP_PROMPT_V0_2_CANDIDATE=FAIL authority inheritance")
        return 1
    if data["active_queue_mutated"] is not False:
        print("LOGISTICS_BOOTSTRAP_PROMPT_V0_2_CANDIDATE=FAIL queue")
        return 1

    for key in ("prompt", "contract", "acceptance_oracle"):
        row = data["candidate_artifacts"][key]
        path = ROOT / row["path"]
        if not path.is_file() or _sha(path) != row["sha256"]:
            print(f"LOGISTICS_BOOTSTRAP_PROMPT_V0_2_CANDIDATE=FAIL {key}")
            return 1

    print("LOGISTICS_BOOTSTRAP_PROMPT_V0_2_CANDIDATE=PASS")
    print("RELEASED=false")
    print("OLD_RELEASE_AUTHORIZATION_INHERITED=false")
    print("ACTIVE_QUEUE_MUTATED=false")
    print("NEXT_GATE=EXPLICIT_RELEASE_AUTHORIZATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
