from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scripts.coordination.control_plane.worker_runtime.bootstrap_profile import (
    resolve_bootstrap_runtime,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--module-root", required=True)
    parser.add_argument("--execution-class", default="MODULE_BOOTSTRAP")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = resolve_bootstrap_runtime(
        blueprint_root=Path(args.root),
        module_root=Path(args.module_root),
        execution_class=args.execution_class,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(result, sort_keys=False, allow_unicode=True, width=112),
        encoding="utf-8",
    )
    print(f"BOOTSTRAP_RUNTIME_SOURCE={result['source']}")
    print(
        "BLUEPRINT_BOOTSTRAP_RUNTIME_FALLBACK_USED="
        + str(result["blueprint_fallback_used"]).lower()
    )
    print("WORKER_PROCESS_STARTED=false")
    print("OPERATOR_APPROVAL_CREATED=false")
    print(f"BOOTSTRAP_RUNTIME_RESOLUTION_PATH={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
