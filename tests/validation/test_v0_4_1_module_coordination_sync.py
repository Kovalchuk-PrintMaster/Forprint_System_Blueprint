from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOL = (
    ROOT
    / "coordination/templates/"
    "module_coordination_sync_check_v0_1.py"
)
TEMPLATE = (
    ROOT
    / "coordination/templates/"
    "module_makefile_standard.template.mk"
)


def load_tool():
    spec = importlib.util.spec_from_file_location(
        "module_coordination_sync_check_v0_1",
        TOOL,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return result.stdout.strip()


def write_queue(
    root: Path,
    *,
    module_id: str = "demo",
    ready_count: int = 1,
) -> None:
    rows = []
    for index in range(ready_count):
        rows.append(
            {
                "prompt_id": f"demo_prompt_v0_{index + 1}",
                "sequence": index + 1,
                "target_module": module_id,
                "priority": "high",
                "file": f"approved/demo_{index + 1}.md",
                "module_execution": {
                    "status": "ready_for_module_pull",
                },
                "blueprint_review": {
                    "status": "not_started",
                },
            }
        )

    path = (
        root
        / "coordination/outgoing_prompts"
        / module_id
        / "index.yaml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "prompt_queue_v0_2",
                "module": module_id,
                "prompt_queue": rows,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def make_remote_fixture(
    tmp_path: Path,
) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    blueprint = tmp_path / "blueprint"

    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "init", "-b", "main", str(blueprint)],
        check=True,
        capture_output=True,
    )
    git(blueprint, "config", "user.email", "test@example.com")
    git(blueprint, "config", "user.name", "Test")
    git(blueprint, "remote", "add", "origin", str(remote))

    (blueprint / "README.md").write_text(
        "initial\n",
        encoding="utf-8",
    )
    git(blueprint, "add", "README.md")
    git(blueprint, "commit", "-m", "initial")
    git(blueprint, "push", "-u", "origin", "main")
    write_queue(blueprint)
    return blueprint, remote


def test_reference_sync_check_uses_remote_read_without_fetch(
    tmp_path: Path,
) -> None:
    module = load_tool()
    blueprint, _ = make_remote_fixture(tmp_path)

    before_refs = git(
        blueprint,
        "for-each-ref",
        "--format=%(refname) %(objectname)",
    )
    report = module.build_report(
        blueprint,
        "demo",
        remote="origin",
        branch=None,
        network=True,
    )
    after_refs = git(
        blueprint,
        "for-each-ref",
        "--format=%(refname) %(objectname)",
    )

    assert report["result_state"] == "READY"
    assert report["freshness"]["state"] == "CURRENT"
    assert report["prompt_notification"]["state"] == "READY_PROMPT"
    assert before_refs == after_refs
    assert report["boundaries"]["git_fetch_performed"] is False
    assert report["boundaries"]["git_pull_performed"] is False


def test_stale_blueprint_blocks_without_local_mutation(
    tmp_path: Path,
) -> None:
    module = load_tool()
    blueprint, remote = make_remote_fixture(tmp_path)

    other = tmp_path / "other"
    subprocess.run(
        ["git", "clone", str(remote), str(other)],
        check=True,
        capture_output=True,
    )
    git(other, "checkout", "main")
    git(other, "config", "user.email", "test@example.com")
    git(other, "config", "user.name", "Test")
    (other / "remote.txt").write_text("new\n", encoding="utf-8")
    git(other, "add", "remote.txt")
    git(other, "commit", "-m", "remote advance")
    git(other, "push", "origin", "main")

    before = git(blueprint, "rev-parse", "HEAD")
    report = module.build_report(
        blueprint,
        "demo",
        remote="origin",
        branch=None,
        network=True,
    )
    after = git(blueprint, "rev-parse", "HEAD")

    assert report["result_state"] == "BLOCKED"
    assert report["freshness"]["state"] == "STALE"
    assert "BLUEPRINT_CHECKOUT_STALE" in report["errors"]
    assert before == after


def test_prompt_notification_states_are_explicit(
    tmp_path: Path,
) -> None:
    module = load_tool()
    blueprint, _ = make_remote_fixture(tmp_path)

    write_queue(blueprint, ready_count=0)
    none_report = module.build_report(
        blueprint,
        "demo",
        remote="origin",
        branch=None,
        network=False,
    )
    assert none_report["result_state"] == "ADVISORY"
    assert (
        none_report["prompt_notification"]["state"]
        == "NO_READY_PROMPT"
    )

    write_queue(blueprint, ready_count=2)
    many_report = module.build_report(
        blueprint,
        "demo",
        remote="origin",
        branch=None,
        network=False,
    )
    assert many_report["result_state"] == "BLOCKED"
    assert (
        many_report["prompt_notification"]["state"]
        == "MULTIPLE_READY_PROMPTS"
    )


def _target_body(text: str, target: str) -> str:
    marker = f"{target}:\n"
    start = text.index(marker) + len(marker)
    rest = text[start:]
    lines = []
    for line in rest.splitlines():
        if line.startswith("\t"):
            lines.append(line)
            continue
        break
    return "\n".join(lines)


def test_template_has_canonical_h4_targets() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    assert ".PHONY: coordination-sync-check" in text
    assert ".PHONY: prompt-notify" in text
    assert "MODULE_COORDINATION_SYNC_CHECK_SCRIPT" in text

    start = _target_body(text, "module-start")
    assert "$(MAKE) coordination-sync-check" in start
    assert "$(MAKE) module-sync" in start
    assert "$(MAKE) prompt-notify" in start

    check = _target_body(text, "check")
    governance = _target_body(text, "governance-check")
    assert "coordination-sync-check" not in check
    assert "coordination-sync-check" not in governance


def test_blueprint_pull_is_fail_closed_only() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    body = _target_body(text, "blueprint-pull")
    assert "exit 2" in body
    assert "git pull" not in body
    assert "git fetch" not in body


def test_current_h4_standard_supersedes_module_side_pull() -> None:
    standard = (
        ROOT
        / "coordination/standards/governance/"
        "module_coordination_sync_protocol_v0_1.md"
    ).read_text(encoding="utf-8")

    assert "`blueprint-pull` is no longer a canonical" in standard
    assert "`git ls-remote`" in standard
    assert "Modules do not execute Blueprint Python code directly." in standard


def test_awareness_policy_uses_canonical_h4_startup() -> None:
    policy = (
        ROOT
        / "coordination/standards/governance/"
        "coordination_document_awareness_policy.md"
    ).read_text(encoding="utf-8")

    assert "coordination-sync-check" in policy
    assert "prompt-notify" in policy
    assert "module-sync" in policy
    assert "Module-side `blueprint-pull` is deprecated" in policy

    startup_section = policy.split(
        "After migration, a mature module `make module-start`",
        1,
    )[1]
    startup_section = startup_section.split(
        "Manual Delivery During Transition",
        1,
    )[0]
    assert "\nblueprint-pull\n" not in startup_section
