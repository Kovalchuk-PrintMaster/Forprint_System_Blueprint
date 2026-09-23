#!/usr/bin/env python3
"""Validate the canonical Blueprint validation-suite registry."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from scripts.validation.run_validation_suite_v0_1 import (
        ALLOWED_STEP_KINDS,
        REGISTRY,
        SCHEMA,
        SuiteError,
        load_registry,
    )
except ModuleNotFoundError:
    from run_validation_suite_v0_1 import (
        ALLOWED_STEP_KINDS,
        REGISTRY,
        SCHEMA,
        SuiteError,
        load_registry,
    )


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    try:
        registry = load_registry(root)
    except SuiteError as exc:
        print(f"VALIDATION_SUITE_REGISTRY_VALIDATION=FAIL {exc}", file=sys.stderr)
        return 2

    suites = registry["suites"]
    print("VALIDATION_SUITE_REGISTRY_VALIDATION=PASS")
    print(f"SCHEMA={SCHEMA}")
    print(f"REGISTRY={REGISTRY.as_posix()}")
    print(f"SUITE_COUNT={len(suites)}")
    for suite_id in sorted(suites):
        print(f"SUITE={suite_id}")
        print(f"SUITE_STEP_COUNT={len(suites[suite_id]['steps'])}")
    print("ALLOWED_STEP_KINDS=" + ",".join(sorted(ALLOWED_STEP_KINDS)))
    print("ARBITRARY_SHELL_COMMANDS_ALLOWED=false")
    print("PATHS_REPOSITORY_RELATIVE=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
