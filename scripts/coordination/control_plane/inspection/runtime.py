from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scripts.coordination.control_plane.inspection.reviewer_registry import (
    load_registry,
    resolve_completion_reviewer,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--reviewer-id")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = resolve_completion_reviewer(
        registry=load_registry(Path(args.registry)),
        reviewer_id=args.reviewer_id,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(result, sort_keys=False, allow_unicode=True, width=112),
        encoding="utf-8",
    )

    print(f"INSPECTOR_BINDING_STATE={result['binding_state']}")
    print(f"INSPECTOR_REVIEWER_ID={result['reviewer_id']}")
    print(f"INSPECTOR_REVIEWER_ROLE={result['reviewer_role']}")
    print("INSPECTOR_READ_ONLY=true")
    print("HUMAN_ACCEPTANCE_AUTHORITY_PRESERVED=true")
    print("INSPECTOR_PROCESS_STARTED=false")
    print(f"INSPECTOR_BINDING_RESOLUTION_PATH={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
