from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scripts.coordination.control_plane.readiness.module_readiness import (
    DevelopmentSignals,
    evaluate_module_readiness,
)


def _bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate bootstrap and development readiness separately."
    )
    parser.add_argument("--bootstrap-context", required=True)
    parser.add_argument("--bootstrap-accepted", type=_bool, default=False)
    parser.add_argument("--strict-task-context-ready", type=_bool, default=False)
    parser.add_argument("--inspector-binding-ready", type=_bool, default=False)
    parser.add_argument("--dependency-readiness-ready", type=_bool, default=False)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    context_path = Path(args.bootstrap_context)
    context = yaml.safe_load(context_path.read_text(encoding="utf-8"))
    if not isinstance(context, dict):
        raise SystemExit("bootstrap context must be a YAML mapping")

    result = evaluate_module_readiness(
        bootstrap_context=context,
        signals=DevelopmentSignals(
            bootstrap_accepted=args.bootstrap_accepted,
            strict_task_context_ready=args.strict_task_context_ready,
            inspector_binding_ready=args.inspector_binding_ready,
            dependency_readiness_ready=args.dependency_readiness_ready,
        ),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(
            result,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )

    print("BOOTSTRAP_READINESS_STATE=" + result["bootstrap_readiness"]["state"])
    print("DEVELOPMENT_READINESS_STATE=" + result["development_readiness"]["state"])
    print("DEVELOPMENT_BLOCKERS=" + ",".join(result["development_readiness"]["blockers"]))
    print(f"PORTFOLIO_STATE={result['portfolio_state']}")
    print(f"READINESS_PATH={output}")
    print("OPERATOR_APPROVAL_CREATED=false")
    print("WORKER_PROCESS_STARTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
