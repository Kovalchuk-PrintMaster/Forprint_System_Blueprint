from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path

import yaml


def module_from(root: Path):
    source = root / "scripts/coordination/workfront_history_v0_1.py"
    spec = importlib.util.spec_from_file_location("_wfh_validator_runtime", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("runtime import spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fail(reason: str) -> int:
    print("WORKFRONT_HISTORY_VALIDATION=FAIL")
    print("REASON=" + reason)
    return 1


def sample_record() -> dict:
    return {
        "schema_version": "forprint_workfront_history_record_v0_1",
        "history_record_id": "wfh-validator-001",
        "work_front_id": "wf-validator-001",
        "recorded_at": "2026-09-14T13:00:00Z",
        "actor": "validator",
        "reason": "contract verification",
        "source_fingerprint": "sha256:validator-source",
        "work_front_snapshot_or_hash": "sha256:validator-front",
        "provenance_refs": ["roadmap:CF-05"],
    }


def validate(root: Path, *, contract_only: bool = False) -> int:
    try:
        contract = yaml.safe_load(
            (
                root / "coordination/standards/automation/workfront_history_contract_v0_1.yaml"
            ).read_text(encoding="utf-8")
        )
        if not isinstance(contract, dict):
            return fail("CONTRACT_ROOT")
        runtime = module_from(root)
        runtime.validate_contract_shape(contract)
        errors = runtime.validate_record_data(sample_record(), contract)
        if errors:
            return fail("SAMPLE_RECORD:" + ";".join(errors))
        with tempfile.TemporaryDirectory() as raw:
            store = Path(raw)
            path = runtime.append_record(root, sample_record(), store_override=store)
            if not path.is_file():
                return fail("APPEND_RECORD")
            try:
                runtime.append_record(root, sample_record(), store_override=store)
            except FileExistsError:
                pass
            else:
                return fail("DUPLICATE_ID_NOT_REJECTED")
    except Exception as exc:
        return fail(type(exc).__name__ + ":" + str(exc))

    print("WORKFRONT_HISTORY_CONTRACT=PASS")
    print("APPEND_ONLY=true")
    print("FACT_HISTORY_ONLY=true")
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
        and row.get("file") == "automation/workfront_history_contract_v0_1.yaml"
    ]
    if len(matches) != 1:
        return fail("STANDARDS_REGISTRATION")

    makefile = (root / "Makefile").read_text(encoding="utf-8")
    if ".PHONY: workfront-history-check" not in makefile:
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
    if 'print("CF05_HISTORY_IMPLEMENTED=true")' not in work_front_validator:
        return fail("WORK_FRONT_VALIDATOR_BINDING")

    print("WORKFRONT_HISTORY_VALIDATION=PASS")
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
