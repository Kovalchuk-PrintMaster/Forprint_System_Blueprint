from __future__ import annotations

import inspect
from pathlib import Path

from scripts.coordination import build_worker_invocation as adapter


def main() -> int:
    required = [
        "RuntimeValidation",
        "WorkerInvocationPlan",
        "validate_runtime_config",
        "build_worker_invocation",
        "write_invocation_plan",
        "render_summary",
    ]
    missing = [name for name in required if not hasattr(adapter, name)]
    if missing:
        print(
            "CONSOLE_WORKER_ADAPTER_CONTRACT=FAIL "
            f"missing={','.join(missing)}"
        )
        return 1

    signature = inspect.signature(adapter.build_worker_invocation)
    expected = {
        "root",
        "module_root",
        "launch_request_path",
        "runtime_path",
        "decision_path",
        "completion_root",
    }
    if set(signature.parameters) != expected:
        print(
            "CONSOLE_WORKER_ADAPTER_CONTRACT=FAIL "
            f"signature={','.join(signature.parameters)}"
        )
        return 1

    source = Path(adapter.__file__).read_text(encoding="utf-8")
    required_tokens = [
        "forprint_worker_runtime_v0_1",
        "forprint_worker_invocation_v0_1",
        "forprint_worker_completion_capture_v0_1",
        "CONSOLE_COMMAND",
        "DRY_RUN_READY",
        "APPROVAL_DECISION_NOT_PROVIDED",
        "LAUNCH_REQUEST_NOT_AWAITING_OPERATOR_APPROVAL",
        "validate_approval_for_dispatch",
        "worker_process_start_allowed",
        "worker_process_started",
        "secret_values_serialized",
        "unknown_telemetry",
        "not_observable",
        "--require-ready",
    ]
    absent = [token for token in required_tokens if token not in source]
    if absent:
        print(
            "CONSOLE_WORKER_ADAPTER_CONTRACT=FAIL "
            f"missing_tokens={','.join(absent)}"
        )
        return 1

    forbidden_tokens = [
        "subprocess.run(",
        "subprocess.Popen(",
        "os.system(",
        "shell=True",
    ]
    forbidden = [token for token in forbidden_tokens if token in source]
    if forbidden:
        print(
            "CONSOLE_WORKER_ADAPTER_CONTRACT=FAIL "
            f"execution_tokens={','.join(forbidden)}"
        )
        return 1

    print("CONSOLE_WORKER_ADAPTER_CONTRACT=PASS")
    print("PROVIDER_NEUTRAL=true")
    print("ADAPTER_MODE=DRY_RUN_ONLY_V0_1")
    print("WORKER_PROCESS_START_ALLOWED=false")
    print("PROMPT_CLAIM_ALLOWED=false")
    print("LOGISTICS_REPOSITORY_WRITE_ALLOWED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
