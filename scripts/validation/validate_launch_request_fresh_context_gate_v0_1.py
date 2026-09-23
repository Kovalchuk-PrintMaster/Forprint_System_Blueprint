from __future__ import annotations

import inspect
from pathlib import Path

from scripts.coordination import build_launch_request as gate


def main() -> int:
    required = [
        "LaunchRequestResult",
        "build_launch_request",
        "write_launch_request",
        "render_summary",
    ]
    missing = [name for name in required if not hasattr(gate, name)]
    if missing:
        print(
            "LAUNCH_REQUEST_FRESH_CONTEXT_GATE_CONTRACT=FAIL "
            f"missing={','.join(missing)}"
        )
        return 1

    signature = inspect.signature(gate.build_launch_request)
    expected = {
        "root",
        "module_root",
        "task_context_archive",
        "dependency_readiness_path",
    }
    if set(signature.parameters) != expected:
        print(
            "LAUNCH_REQUEST_FRESH_CONTEXT_GATE_CONTRACT=FAIL "
            f"signature={','.join(signature.parameters)}"
        )
        return 1

    source = Path(gate.__file__).read_text(encoding="utf-8")
    required_tokens = [
        "forprint_launch_request_v0_1",
        "forprint_dependency_readiness_snapshot_v0_1",
        "AWAITING_OPERATOR_APPROVAL",
        "TASK_CONTEXT_FINGERPRINT_DRIFT",
        "DEPENDENCY_READINESS_NOT_PROVIDED",
        "worker_dispatch_allowed",
        "prompt_claim_allowed",
        "approval_gateway_implemented",
        "--require-eligible",
        "sys.modules[spec.name] = module",
    ]
    absent = [token for token in required_tokens if token not in source]
    if absent:
        print(
            "LAUNCH_REQUEST_FRESH_CONTEXT_GATE_CONTRACT=FAIL "
            f"missing_tokens={','.join(absent)}"
        )
        return 1

    print("LAUNCH_REQUEST_FRESH_CONTEXT_GATE_CONTRACT=PASS")
    print("OPERATOR_APPROVAL_PERFORMED=false")
    print("WORKER_DISPATCH_ALLOWED=false")
    print("PROMPT_CLAIM_ALLOWED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
