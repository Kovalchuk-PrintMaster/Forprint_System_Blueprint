#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.coordination.governed_procedure_graph_v0_1 import (  # noqa: E402
    validate_canonical_contracts,
    validate_runtime_surfaces,
)


def main() -> int:
    validate_canonical_contracts(ROOT)
    validate_runtime_surfaces(ROOT)
    print("GOVERNED_PROCEDURE_GRAPH_CONTRACT=PASS")
    print("NODE_KINDS=7")
    print("GATE_TYPES=HARD_GATE,OBSERVED_GATE,NONE")
    print("RUN_MANIFEST_REVISION_PINNING=true")
    print("LEGAL_WAIVER_CONTRACT=true")
    print("CAPABILITY_CLASSIFICATIONS=GRAPH_REQUIRED,NOT_REQUIRED")
    print("RECOVERY_CLASSES=CANONICAL_CONFLICT,PROJECTION_STALE")
    print("GRAPH_GRANTS_AUTHORITY=false")
    print("WORKER_DISPATCH_AUTHORITY=false")
    print("RUNTIME_PROCEDURE_REGISTRY=true")
    print("RUN_MANIFEST_EMITTER=true")
    print("CONFORMANCE_EXECUTION_ENTRYPOINT=true")
    print("ATTEMPT_LEDGER_EVIDENCE_BINDING=true")
    print("RUNTIME_GRANTS_AUTHORITY=false")
    print("CF08_IMPLEMENTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
