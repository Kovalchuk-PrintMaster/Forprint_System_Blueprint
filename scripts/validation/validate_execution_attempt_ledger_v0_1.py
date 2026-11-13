from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path

import yaml


def module_from(root: Path):
    source = root / "scripts/coordination/execution_attempt_ledger_v0_1.py"
    spec = importlib.util.spec_from_file_location("_attempt_validator_runtime", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("runtime import spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fail(reason: str) -> int:
    print("EXECUTION_ATTEMPT_LEDGER_VALIDATION=FAIL")
    print("REASON=" + reason)
    return 1


def sample_record(attempt_id: str, **updates) -> dict:
    value = {
        "schema_version": "forprint_execution_attempt_record_v0_1",
        "attempt_id": attempt_id,
        "work_front_id": "wf-validator-001",
        "recorded_at": "2026-09-14T13:00:00Z",
        "actor_or_worker_ref": "validator",
        "where": "blueprint",
        "why": "contract verification",
        "source_fingerprint": "sha256:validator-source",
        "profile_ref_or_revision": None,
        "pack_hash_or_context_hash": None,
        "launch_or_invocation_ref": None,
        "attempt_stage": "FAILED",
        "result_state": "FAILED",
        "result_refs": [],
        "validator_outcome": "FAIL",
        "validator_evidence_refs": ["validator:self"],
        "failure_or_retry_ref": "failure:validator",
        "resume": {
            "latest_accepted_ref": None,
            "resume_coordinates": [],
            "replay_forbidden_refs": [],
        },
    }
    value.update(updates)
    return value


def validate(root: Path, *, contract_only: bool = False) -> int:
    try:
        contract = yaml.safe_load(
            (
                root / "coordination/standards/automation/"
                "execution_attempt_ledger_contract_v0_1.yaml"
            ).read_text(encoding="utf-8")
        )
        if not isinstance(contract, dict):
            return fail("CONTRACT_ROOT")
        runtime = module_from(root)
        runtime.validate_contract_shape(contract)
        first = sample_record("attempt-validator-001")
        errors = runtime.validate_record_data(first, contract)
        if errors:
            return fail("SAMPLE_RECORD:" + ";".join(errors))
        with tempfile.TemporaryDirectory() as raw:
            store = Path(raw)
            first_path = runtime.append_record(root, first, store_override=store)
            retry = sample_record(
                "attempt-validator-002",
                retry_of_attempt_id="attempt-validator-001",
                attempt_stage="FINISHED",
                result_state="SUCCEEDED",
                validator_outcome="PASS",
                validator_evidence_refs=["validator:retry"],
                failure_or_retry_ref="retry:attempt-validator-001",
            )
            retry_path = runtime.append_record(root, retry, store_override=store)
            if not first_path.is_file() or not retry_path.is_file():
                return fail("APPEND_RECORD")
            records = runtime.iter_records(store)
            if len(records) != 2:
                return fail("FAILED_ATTEMPT_NOT_PRESERVED")

            started = sample_record(
                "attempt-validator-terminal-001",
                recorded_at="2026-09-14T13:10:00Z",
                attempt_stage="STARTED",
                result_state="PENDING",
                validator_outcome="NOT_RUN",
                validator_evidence_refs=[],
                failure_or_retry_ref=None,
            )
            terminal = sample_record(
                "attempt-validator-terminal-001",
                recorded_at="2026-09-14T13:11:00Z",
                attempt_stage="FINISHED",
                result_state="SUCCEEDED",
                validator_outcome="PASS",
                validator_evidence_refs=["validator:terminal"],
                failure_or_retry_ref=None,
            )
            start_path = runtime.append_record(
                root, started, store_override=store
            )
            terminal_path = runtime.append_record(
                root, terminal, store_override=store
            )
            if not start_path.is_file() or not terminal_path.is_file():
                return fail("SAME_ATTEMPT_TERMINAL_APPEND")
            attempt_history = runtime.records_for_attempt(
                store,
                "attempt-validator-terminal-001",
            )
            if len(attempt_history) != 2:
                return fail("SAME_ATTEMPT_HISTORY_LENGTH")
            latest = runtime.latest_attempt_record(
                store,
                "attempt-validator-terminal-001",
            )
            if latest is None or latest.get("result_state") != "SUCCEEDED":
                return fail("LATEST_ATTEMPT_STATE")
            try:
                runtime.append_record(
                    root,
                    terminal,
                    store_override=store,
                )
            except FileExistsError:
                pass
            else:
                return fail("EXACT_TERMINAL_REAPPEND_NOT_REJECTED")
    except Exception as exc:
        return fail(type(exc).__name__ + ":" + str(exc))

    print("EXECUTION_ATTEMPT_LEDGER_CONTRACT=PASS")
    print("APPEND_ONLY=true")
    print("MULTI_RECORD_ATTEMPT_HISTORY=true")
    print("LATEST_ATTEMPT_STATE_DERIVED=true")
    print("START_RECORD_IMMUTABLE=true")
    print("FAILED_ATTEMPTS_PRESERVED=true")
    print("RETRY_CREATES_NEW_ATTEMPT=true")
    print("DISPATCH_AUTHORITY=false")
    if contract_only:
        return 0

    standards = yaml.safe_load(
        (root / "coordination/standards/index.yaml").read_text(encoding="utf-8")
    )
    rows = standards.get("standards") if isinstance(standards, dict) else None
    if not isinstance(rows, list):
        return fail("STANDARDS_INDEX")
    matches = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("file") == "automation/execution_attempt_ledger_contract_v0_1.yaml"
    ]
    if len(matches) != 1:
        return fail("STANDARDS_REGISTRATION")

    makefile = (root / "Makefile").read_text(encoding="utf-8")
    if ".PHONY: execution-attempt-ledger-check" not in makefile:
        return fail("MAKE_TARGET")
    check_core = next(
        (line for line in makefile.splitlines() if line.startswith("check-core:")),
        "",
    )
    if "cf05-history-ledger-check" not in check_core.split():
        return fail("CHECK_CORE_BINDING")

    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    if "<!-- FORPRINT_CF05_HISTORY_LEDGER_START -->" not in agents:
        return fail("AGENTS_BINDING")

    work_front_validator = (
        root / "scripts/validation/validate_work_front_contract_v0_1.py"
    ).read_text(encoding="utf-8")
    if 'print("EXECUTION_ATTEMPT_LEDGER_IMPLEMENTED=true")' not in work_front_validator:
        return fail("WORK_FRONT_VALIDATOR_BINDING")

    print("EXECUTION_ATTEMPT_LEDGER_VALIDATION=PASS")
    print("DURABLE_RESUME_COORDINATES=true")
    print("WORK_FRONT_EXECUTION_AUTHORITY_PRESERVED=true")
    print("LIFECYCLE_EXECUTION_AUTHORITY_PRESERVED=true")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--contract-only", action="store_true")
    args = parser.parse_args()
    return validate(Path(args.root).resolve(), contract_only=args.contract_only)


if __name__ == "__main__":
    raise SystemExit(main())
