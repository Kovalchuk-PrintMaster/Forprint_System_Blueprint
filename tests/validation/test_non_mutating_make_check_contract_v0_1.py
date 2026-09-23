from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.generate_mermaid import check_generated as check_mermaid_generated
from scripts.generate_mermaid import generate as generate_mermaid
from scripts.generate_module_guides import check_generated as check_guides_generated
from scripts.generate_module_guides import generate as generate_guides
from scripts.run_blueprint_checks import build_checks
from scripts.validation.run_non_mutating_make_check import run_isolated_check

ROOT = Path(__file__).resolve().parents[2]


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "tests@forprint.local")
    _git(path, "config", "user.name", "ForPrint Tests")


def test_blueprint_check_catalog_uses_non_mutating_generator_modes() -> None:
    by_id = {check.check_id: check for check in build_checks()}
    assert by_id["mermaid_generation"].command[-1] == "--check"
    assert by_id["module_guides_generation"].command[-1] == "--check"


def test_mermaid_check_detects_drift_without_repairing(tmp_path: Path) -> None:
    machine = tmp_path / "machine"
    diagrams = tmp_path / "diagrams"
    machine.mkdir()
    diagrams.mkdir()
    (machine / "data_flows.yaml").write_text("data_flows: []\n", encoding="utf-8")
    (machine / "ownership.yaml").write_text("ownership: {}\n", encoding="utf-8")

    generate_mermaid(tmp_path)
    assert check_mermaid_generated(tmp_path)

    graph = diagrams / "module_graph.mmd"
    graph.write_text("drift\n", encoding="utf-8")
    assert not check_mermaid_generated(tmp_path)
    assert graph.read_text(encoding="utf-8") == "drift\n"


def test_module_guides_check_detects_drift_without_repairing(tmp_path: Path) -> None:
    machine = tmp_path / "machine"
    guides = tmp_path / "module_guides"
    machine.mkdir()
    guides.mkdir()
    (machine / "modules.yaml").write_text(
        """
modules:
  - id: demo
    title: Demo
    type: test
    status: planned
    role: Demo role
    owns: []
    consumes: []
    provides: []
    must_not_own: []
""".lstrip(),
        encoding="utf-8",
    )
    (machine / "data_flows.yaml").write_text("data_flows: []\n", encoding="utf-8")
    (machine / "contracts.yaml").write_text("contracts: []\n", encoding="utf-8")

    generate_guides(tmp_path)
    assert check_guides_generated(tmp_path)

    guide = guides / "demo.md"
    guide.write_text("drift\n", encoding="utf-8")
    assert not check_guides_generated(tmp_path)
    assert guide.read_text(encoding="utf-8") == "drift\n"


def test_isolated_runner_allows_inner_mutation_but_preserves_source(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "source"
    _init_repo(repo)
    tracked = repo / "tracked.txt"
    tracked.write_text("original\n", encoding="utf-8")
    (repo / "Makefile").write_text(
        "check-core:\n\t@printf 'changed\\\\n' >> tracked.txt\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture")

    rc = run_isolated_check(
        root=repo,
        target="check-core",
        module_root=None,
        keep_workspace=False,
    )

    assert rc == 0
    assert tracked.read_text(encoding="utf-8") == "original\n"


def test_isolated_runner_preserves_untracked_dirty_state(tmp_path: Path) -> None:
    repo = tmp_path / "source"
    _init_repo(repo)
    tracked = repo / "tracked.txt"
    tracked.write_text("committed\n", encoding="utf-8")
    (repo / "Makefile").write_text(
        "check-core:\n\t@test -f untracked.txt\n\t@grep -q dirty tracked.txt\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture")

    tracked.write_text("dirty\n", encoding="utf-8")
    untracked = repo / "untracked.txt"
    untracked.write_text("working tree\n", encoding="utf-8")

    rc = run_isolated_check(
        root=repo,
        target="check-core",
        module_root=None,
        keep_workspace=False,
    )

    assert rc == 0
    assert tracked.read_text(encoding="utf-8") == "dirty\n"
    assert untracked.read_text(encoding="utf-8") == "working tree\n"


def test_make_check_routes_through_isolation_wrapper() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert ".PHONY: check-core" in makefile
    assert "run_non_mutating_make_check.py --target check-core" in makefile


def test_isolated_runner_mirrors_reports_but_keeps_report_writes_disposable(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "source"
    _init_repo(repo)
    nested = repo / "coordination" / "reports" / "completion" / "required.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("durable evidence\n", encoding="utf-8")

    top_report = repo / "reports" / "runtime.txt"
    top_report.parent.mkdir(parents=True)
    top_report.write_text("source report\n", encoding="utf-8")

    (repo / "Makefile").write_text(
        "check-core:\n"
        "\t@test -f coordination/reports/completion/required.md\n"
        "\t@grep -q 'source report' reports/runtime.txt\n"
        "\t@printf 'isolated write\\n' >> reports/runtime.txt\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture")

    rc = run_isolated_check(
        root=repo,
        target="check-core",
        module_root=None,
        keep_workspace=False,
    )

    assert rc == 0
    assert nested.read_text(encoding="utf-8") == "durable evidence\n"
    assert top_report.read_text(encoding="utf-8") == "source report\n"


def test_check_core_builds_freshness_report_it_consumes() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "--output reports/repository_knowledge_freshness_report.yaml" in makefile
    assert "--freshness reports/repository_knowledge_freshness_report.yaml" in makefile
    assert (
        "check-repository-knowledge-freshness"
        in makefile.split("check-core:", 1)[1].splitlines()[0]
    )

def test_continuity_baseline_freeze_precedes_disposable_mirror_creation():
    """Preserve source Git-index semantics for isolated continuity checks."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    runner = (
        root
        / "scripts"
        / "validation"
        / "run_non_mutating_make_check.py"
    )
    source = runner.read_text(encoding="utf-8")

    function_start = source.index("def run_isolated_check(")
    function_end = source.index("\ndef main()", function_start)
    function_source = source[function_start:function_end]

    baseline_call = (
        'baseline_cp = _run(\n'
        '                root,'
    )
    mirror_call = "prepare_repository_mirror(root, workspace)"

    assert baseline_call in function_source
    assert mirror_call in function_source

    assert (
        function_source.index(baseline_call)
        < function_source.index(mirror_call)
    )

    assert (
        'FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE_ROOT'
        in function_source
    )
    assert "str(workspace.resolve())" in function_source

