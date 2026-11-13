from __future__ import annotations

import inspect
from pathlib import Path

from scripts.coordination import build_context_bundle as compiler


def main() -> int:
    required = [
        "TaskContextResult",
        "build_task_context",
        "write_task_context_archive",
    ]
    missing = [name for name in required if not hasattr(compiler, name)]
    if missing:
        print(f"TASK_CONTEXT_COMPILER_CONTRACT=FAIL missing={','.join(missing)}")
        return 1

    signature = inspect.signature(compiler.build_task_context)
    expected = {"root", "module", "prompt_id", "module_root"}
    if set(signature.parameters) != expected:
        print(
            "TASK_CONTEXT_COMPILER_CONTRACT=FAIL "
            f"signature={','.join(signature.parameters)}"
        )
        return 1

    source = Path(compiler.__file__).read_text(encoding="utf-8")
    required_tokens = [
        "--task-context",
        "--prompt-id",
        "--module-root",
        "forprint_task_context_manifest_v0_1",
        "PAUSED_BY_OPERATOR",
        "worker_dispatch_allowed",
        "prompt_claim_allowed",
        "TASK_CONTEXT_ARCHIVE_SHA256",
    ]
    absent = [token for token in required_tokens if token not in source]
    if absent:
        print(
            "TASK_CONTEXT_COMPILER_CONTRACT=FAIL "
            f"missing_tokens={','.join(absent)}"
        )
        return 1

    print("TASK_CONTEXT_COMPILER_CONTRACT=PASS")
    print("EXISTING_CONTEXT_BUNDLE_COMPATIBILITY=REQUIRED")
    print("WORKER_DISPATCH_ALLOWED=false")
    print("PROMPT_CLAIM_ALLOWED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
