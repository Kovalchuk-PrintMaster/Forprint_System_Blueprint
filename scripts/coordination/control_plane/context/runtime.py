from __future__ import annotations

import argparse
from pathlib import Path

from scripts.coordination.control_plane.context.bootstrap_task_context import (
    build_bootstrap_task_context,
    write_bootstrap_task_context,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a MODULE_BOOTSTRAP context envelope. "
            "This mode may carry explicit bootstrap debt but never permits roadmap "
            "development before Stage 0 and strict task-context rebuild."
        )
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--module-root", required=True)
    parser.add_argument("--module-id", required=True)
    parser.add_argument("--prompt-id", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--prompt-contract", required=True)
    parser.add_argument("--release-authorization", required=True)
    parser.add_argument("--acceptance-oracle", required=True)
    parser.add_argument("--bootstrap-policy", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    envelope = build_bootstrap_task_context(
        blueprint_root=Path(args.root),
        module_root=Path(args.module_root),
        module_id=args.module_id,
        prompt_id=args.prompt_id,
        prompt_path=Path(args.prompt),
        prompt_contract_path=Path(args.prompt_contract),
        release_authorization_path=Path(args.release_authorization),
        acceptance_oracle_path=Path(args.acceptance_oracle),
        stage_0_policy_path=Path(args.bootstrap_policy),
    )
    path = write_bootstrap_task_context(
        envelope=envelope,
        output_dir=Path(args.output_dir),
    )

    print(f"BOOTSTRAP_CONTEXT_STATE={envelope['state']}")
    print(f"BOOTSTRAP_DEBT_COUNT={envelope['bootstrap_debt_count']}")
    print(
        "STRICT_DEVELOPMENT_CONTEXT_READY="
        + str(envelope["strict_development_context_ready"]).lower()
    )
    print("STAGE_0_REQUIRED=true")
    print("ROADMAP_DEVELOPMENT_ALLOWED=false")
    print(f"BOOTSTRAP_CONTEXT_PATH={path}")
    print("WORKER_PROCESS_STARTED=false")
    print("OPERATOR_APPROVAL_CREATED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
