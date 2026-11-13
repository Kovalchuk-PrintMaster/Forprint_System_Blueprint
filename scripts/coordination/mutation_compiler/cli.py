from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import MutationCompiler
from .models import CompilerPolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forprint-mutation-compiler")
    parser.add_argument(
        "mode",
        choices=("check", "repair-check", "apply"),
    )
    parser.add_argument("--candidate-root", required=True)
    parser.add_argument("--target-root", default=".")
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        required=True,
        help="Repository-relative target path; repeat for each target.",
    )
    parser.add_argument("--mutation-id")
    parser.add_argument(
        "--pre-command",
        action="append",
        default=[],
        help="Baseline verification command run in isolated project copy before candidate overlay; shell=False.",
    )
    parser.add_argument(
        "--post-command",
        action="append",
        default=[],
        help="Candidate verification command run in isolated project copy after overlay and before durable apply; shell=False.",
    )
    parser.add_argument("--strict-unknown", action="store_true")
    parser.add_argument("--max-repair-passes", type=int, default=3)
    parser.add_argument("--command-timeout", type=int, default=300)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    policy = CompilerPolicy(
        max_repair_passes=args.max_repair_passes,
        strict_unknown=args.strict_unknown,
        command_timeout_seconds=args.command_timeout,
    )
    compiler = MutationCompiler(
        target_root=Path(args.target_root),
        candidate_root=Path(args.candidate_root),
        paths=args.paths,
        mode=args.mode,
        policy=policy,
        mutation_id=args.mutation_id,
        pre_commands=args.pre_command,
        post_commands=args.post_command,
    )
    report = compiler.compile()
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0 if report.result_state.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
