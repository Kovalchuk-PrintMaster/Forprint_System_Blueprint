from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scripts.coordination.control_plane.completion.human_gate import (
    project_human_acceptance_gate,
)
from scripts.coordination.control_plane.completion.inspector import (
    build_inspector_request,
    validate_inspector_result,
    write_inspector_request,
)
from scripts.coordination.control_plane.completion.intake import (
    normalize_completion_intake,
    write_normalized_completion,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    normalize = sub.add_parser("normalize")
    for flag in (
        "completion-capture",
        "completion-report",
        "dispatch-intent",
        "worker-invocation",
        "output-dir",
    ):
        normalize.add_argument(f"--{flag}", required=True)

    request = sub.add_parser("inspector-request")
    for flag in (
        "normalized-completion",
        "acceptance-oracle",
        "prompt-contract",
        "output-dir",
    ):
        request.add_argument(f"--{flag}", required=True)

    validate = sub.add_parser("inspector-result-validate")
    validate.add_argument("--request", required=True)
    validate.add_argument("--result", required=True)

    gate = sub.add_parser("human-gate-project")
    gate.add_argument("--request", required=True)
    gate.add_argument("--result", required=True)

    args = parser.parse_args()
    if args.command == "normalize":
        result = normalize_completion_intake(
            completion_capture_path=Path(args.completion_capture),
            completion_report_path=Path(args.completion_report),
            dispatch_intent_path=Path(args.dispatch_intent),
            worker_invocation_path=Path(args.worker_invocation),
        )
        path = write_normalized_completion(result=result, output_dir=Path(args.output_dir))
        print(f"NORMALIZED_COMPLETION_ID={result.normalized_id}")
        print(f"NORMALIZED_COMPLETION_PATH={path}")
        print("BLUEPRINT_ACCEPT_PERFORMED=false")
        return 0

    if args.command == "inspector-request":
        result = build_inspector_request(
            normalized_completion_path=Path(args.normalized_completion),
            acceptance_oracle_path=Path(args.acceptance_oracle),
            prompt_contract_path=Path(args.prompt_contract),
        )
        path = write_inspector_request(result=result, output_dir=Path(args.output_dir))
        print(f"INSPECTOR_REQUEST_ID={result.request_id}")
        print(f"INSPECTOR_REQUEST_PATH={path}")
        print("INSPECTOR_EXECUTED=false")
        return 0

    if args.command == "inspector-result-validate":
        result = validate_inspector_result(
            request_path=Path(args.request), result_path=Path(args.result)
        )
        print(yaml.safe_dump({"valid": result.valid, "errors": list(result.errors)}).rstrip())
        return 0 if result.valid else 2

    projection = project_human_acceptance_gate(
        inspector_request_path=Path(args.request),
        inspector_result_path=Path(args.result),
    )
    print(yaml.safe_dump(projection, sort_keys=False).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
