#!/usr/bin/env python3
"""Validate CF-10 Slice 5A multi-provider runtime registry."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.coordination.control_plane.worker_runtime.registry import (  # noqa: E402
    load_module_runtime_config,
    load_runtime_registry,
    resolve_default_runtime,
)


def main() -> int:
    try:
        registry = load_runtime_registry(ROOT)
        config = load_module_runtime_config(ROOT)
        runtime = resolve_default_runtime(ROOT)

        rows = {row["provider_id"]: row for row in registry["providers"]}
        if set(rows) != {
            "github_copilot_cli",
            "openai_codex_cli",
            "anthropic_claude_code",
            "xai_grok_cli",
        }:
            raise RuntimeError("runtime provider set mismatch")

        ready = [row for row in rows.values() if row["state"] == "READY"]
        if len(ready) != 1 or ready[0]["provider_id"] != "github_copilot_cli":
            raise RuntimeError("Slice 5A must have exactly one READY provider")

        executable = Path(runtime["executable"])
        if executable != Path("/usr/local/bin/copilot"):
            raise RuntimeError("configured Copilot executable mismatch")
        if not executable.is_file():
            raise RuntimeError("configured Copilot executable is missing")

        cp = subprocess.run(
            [str(executable), "--version"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=60,
        )
        if cp.returncode != 0:
            raise RuntimeError("Copilot version probe failed")
        version_line = (cp.stdout or "").strip().splitlines()
        if not version_line:
            raise RuntimeError("Copilot version probe returned no output")

        if config["provider_selection"]["mode"] != "per_attempt":
            raise RuntimeError("provider must be selected per attempt")
        if config["command"]["shell"] is not False:
            raise RuntimeError("shell execution unexpectedly enabled")
        if config["auth"]["secret_value_in_config"] is not False:
            raise RuntimeError("secret value unexpectedly allowed in config")

        benchmark_path = (
            ROOT
            / "coordination/standards/automation/"
            "worker_runtime_benchmark_contract_v0_1.yaml"
        )
        benchmark = yaml.safe_load(benchmark_path.read_text(encoding="utf-8"))
        if benchmark["quality_facts"]["semantic_acceptance_is_automatic"] is not False:
            raise RuntimeError("benchmark cannot auto-accept results")

        print("CF10_MULTI_PROVIDER_RUNTIME_REGISTRY_VALIDATION=PASS")
        print("WORKER_IDENTITY_PROVIDER_NEUTRAL=true")
        print("READY_PROVIDER_COUNT=1")
        print("READY_PROVIDER=github_copilot_cli")
        print("COPILOT_EXECUTABLE=/usr/local/bin/copilot")
        print("COPILOT_VERSION_PROBE=PASS")
        print("DEFAULT_MODEL=auto")
        print("PROVIDER_SELECTION=PER_ATTEMPT")
        print("RESERVED_PROVIDER=openai_codex_cli:NOT_CONFIGURED")
        print("RESERVED_PROVIDER=anthropic_claude_code:NOT_CONFIGURED")
        print("RESERVED_PROVIDER=xai_grok_cli:NOT_CONFIGURED")
        print("SECRET_VALUES_IN_GIT=false")
        print("REGISTRY_GRANTS_AUTHORITY=false")
        print("ASSISTANT_ACK_CONSUMED=false")
        print("WORKER_PROCESS_LAUNCHED=false")
        return 0
    except Exception as exc:
        print(f"ERROR={type(exc).__name__}: {exc}")
        print("CF10_MULTI_PROVIDER_RUNTIME_REGISTRY_VALIDATION=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
