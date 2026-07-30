#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return data


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Missing YAML frontmatter: {path}")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"Unclosed YAML frontmatter: {path}")
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML frontmatter: {path}")
    return data


def validate_package(
    root: Path,
    roadmap_path: Path,
    queue_path: Path,
    completion_path: Path,
    module_plan_paths: list[Path],
) -> dict[str, Any]:
    errors: list[str] = []
    roadmap = load_yaml(roadmap_path)
    queue = load_yaml(queue_path)
    completion = load_yaml(completion_path)

    if roadmap.get("schema_version") != "blueprint_self_coordination_roadmap_v0_1":
        errors.append("roadmap schema mismatch")

    metadata = roadmap.get("metadata")
    steps = roadmap.get("steps")
    if not isinstance(metadata, dict):
        errors.append("roadmap metadata missing")
        metadata = {}
    if not isinstance(steps, list):
        errors.append("roadmap steps missing")
        steps = []

    ordered = sorted(
        [step for step in steps if isinstance(step, dict)],
        key=lambda step: (
            step.get("sequence", 10000),
            str(step.get("step_id", "")),
        ),
    )
    active = [step for step in ordered if step.get("status") == "active"]

    if len(active) != 1:
        errors.append("roadmap needs exactly one active step")
        actionable = []
    else:
        if active[0].get("step_id") != metadata.get("current_step_id"):
            errors.append("roadmap current_step_id mismatch")
        index = ordered.index(active[0])
        actionable = [
            step
            for step in ordered[index + 1 :]
            if step.get("status") in {"active", "planned", "ready"}
        ]
        if not 8 <= len(actionable) <= 10:
            errors.append("roadmap needs 8-10 actionable steps after current")

    if queue.get("schema_version") != "blueprint_self_prompt_queue_v0_1":
        errors.append("queue schema mismatch")

    queue_metadata = queue.get("metadata")
    prompts = queue.get("prompts")
    if not isinstance(queue_metadata, dict):
        errors.append("queue metadata missing")
        queue_metadata = {}
    if not isinstance(prompts, list):
        errors.append("queue prompts missing")
        prompts = []

    approved = [
        prompt
        for prompt in prompts
        if isinstance(prompt, dict) and prompt.get("status") == "approved"
    ]
    drafts = [
        prompt for prompt in prompts if isinstance(prompt, dict) and prompt.get("status") == "draft"
    ]
    completed = [
        prompt
        for prompt in prompts
        if isinstance(prompt, dict) and prompt.get("status") == "completed"
    ]

    if len(approved) != 1:
        errors.append("queue needs exactly one approved prompt")
    elif approved[0].get("prompt_id") != queue_metadata.get("active_prompt_id"):
        errors.append("queue active_prompt_id mismatch")

    if len(drafts) < 2:
        errors.append("queue needs at least two drafts")
    if not completed:
        errors.append("queue needs a completed baseline prompt")

    prompt_failures = 0
    for prompt in prompts:
        if not isinstance(prompt, dict):
            prompt_failures += 1
            continue
        relative = prompt.get("path")
        if not isinstance(relative, str):
            prompt_failures += 1
            continue
        path = root / relative
        if not path.is_file():
            prompt_failures += 1
            continue
        try:
            frontmatter = parse_frontmatter(path)
        except ValueError:
            prompt_failures += 1
            continue
        if frontmatter.get("prompt_id") != prompt.get("prompt_id") or frontmatter.get(
            "status"
        ) != prompt.get("status"):
            prompt_failures += 1

    if completion.get("schema_version") != "blueprint_self_completion_packet_v0_1":
        errors.append("completion schema mismatch")
    if completion.get("result") != "ACCEPTED":
        errors.append("completion result mismatch")
    ownership = completion.get("ownership")
    if not isinstance(ownership, dict):
        errors.append("completion ownership missing")
    elif not ownership.get("implementer") or not ownership.get("reviewer"):
        errors.append("completion ownership incomplete")

    module_failures = 0
    module_ids: set[str] = set()
    for path in module_plan_paths:
        plan = load_yaml(path)
        metadata = plan.get("metadata")
        horizon = plan.get("planned_horizon")
        safety = plan.get("safety")
        if plan.get("schema_version") != "blueprint_module_advancement_plan_v0_1":
            module_failures += 1
        if isinstance(metadata, dict) and isinstance(metadata.get("module_id"), str):
            module_ids.add(metadata["module_id"])
        else:
            module_failures += 1
        if not isinstance(horizon, list) or len(horizon) < 3:
            module_failures += 1
        if (
            not isinstance(safety, dict)
            or safety.get("external_rollout_state") != "gated"
            or safety.get("module_repository_writes") is not False
        ):
            module_failures += 1

    if module_ids != {"forprint_library", "logistics_service", "telegram_bot"}:
        errors.append("managed-module coverage mismatch")

    passed = not errors and prompt_failures == 0 and module_failures == 0
    return {
        "schema_version": "blueprint_self_coordination_validation_report_v0_1",
        "metadata": {"result": "PASSED" if passed else "FAILED"},
        "summary": {
            "roadmap_steps": len(ordered),
            "actionable_after_current": len(actionable),
            "approved_prompts": len(approved),
            "draft_prompts": len(drafts),
            "completed_prompts": len(completed),
            "prompt_failures": prompt_failures,
            "module_plans": len(module_plan_paths),
            "module_failures": module_failures,
            "policy_errors": len(errors),
        },
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--roadmap", required=True)
    parser.add_argument("--queue", required=True)
    parser.add_argument("--completion", required=True)
    parser.add_argument("--module-plan", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = validate_package(
        Path(args.repo_root).resolve(),
        Path(args.roadmap),
        Path(args.queue),
        Path(args.completion),
        [Path(value) for value in args.module_plan],
    )
    Path(args.output).write_text(
        yaml.safe_dump(report, sort_keys=False, allow_unicode=True, width=112),
        encoding="utf-8",
    )
    return 0 if report["metadata"]["result"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
