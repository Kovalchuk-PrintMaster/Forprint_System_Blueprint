from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validation/run_non_mutating_make_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "run_non_mutating_make_check_under_test",
        SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_module_root_none_remains_none(tmp_path):
    module = _load_module()
    root = tmp_path / "blueprint"
    root.mkdir()
    assert module._resolve_module_root(root, None) is None


def test_resolve_module_root_relative_self_becomes_none(tmp_path):
    module = _load_module()
    root = tmp_path / "blueprint"
    root.mkdir()
    assert module._resolve_module_root(root, ".") is None


def test_resolve_module_root_absolute_self_becomes_none(tmp_path):
    module = _load_module()
    root = tmp_path / "blueprint"
    root.mkdir()
    assert module._resolve_module_root(root, str(root)) is None


def test_resolve_module_root_real_sibling_is_preserved(tmp_path):
    module = _load_module()
    root = tmp_path / "blueprint"
    sibling = tmp_path / "forprint_library"
    root.mkdir()
    sibling.mkdir()
    assert module._resolve_module_root(root, "../forprint_library") == sibling.resolve()


def test_main_does_not_forward_self_as_sibling_module(tmp_path, monkeypatch):
    module = _load_module()
    root = tmp_path / "blueprint"
    root.mkdir()
    captured = {}

    def fake_run_isolated_check(*, root, target, module_root, keep_workspace):
        captured["root"] = root
        captured["target"] = target
        captured["module_root"] = module_root
        captured["keep_workspace"] = keep_workspace
        return 0

    monkeypatch.setattr(module, "run_isolated_check", fake_run_isolated_check)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--root",
            str(root),
            "--target",
            "check-core",
            "--module-root",
            ".",
        ],
    )

    assert module.main() == 0
    assert captured["root"] == root.resolve()
    assert captured["target"] == "check-core"
    assert captured["module_root"] is None
    assert captured["keep_workspace"] is False

def test_isolated_runner_materializes_generated_prerequisites_only_in_mirror(
    tmp_path,
):
    module = _load_module()
    repo = tmp_path / "source"
    repo.mkdir()

    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "tests@forprint.local"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "ForPrint Tests"],
        cwd=repo,
        check=True,
    )

    scripts = repo / "scripts" / "indexing"
    scripts.mkdir(parents=True)

    (scripts / "build_generator_inventory.py").write_text(
        "from pathlib import Path\n"
        "p = Path('indexes/generator_inventory.yaml')\n"
        "p.parent.mkdir(parents=True, exist_ok=True)\n"
        "p.write_text('generated: true\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (scripts / "build_execution_dependency_graph.py").write_text(
        "from pathlib import Path\n"
        "p = Path('indexes/execution_dependency_graph.yaml')\n"
        "p.parent.mkdir(parents=True, exist_ok=True)\n"
        "p.write_text('generated: true\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )

    (repo / "Makefile").write_text(
        "check-core:\n"
        "\t@test -f indexes/generator_inventory.yaml\n"
        "\t@test -f indexes/execution_dependency_graph.yaml\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "fixture"],
        cwd=repo,
        check=True,
    )

    assert not (repo / "indexes/generator_inventory.yaml").exists()
    assert not (repo / "indexes/execution_dependency_graph.yaml").exists()

    rc = module.run_isolated_check(
        root=repo,
        target="check-core",
        module_root=None,
        keep_workspace=False,
    )

    assert rc == 0
    assert not (repo / "indexes/generator_inventory.yaml").exists()
    assert not (repo / "indexes/execution_dependency_graph.yaml").exists()

def test_isolated_runner_refreshes_roadmap_projection_only_in_mirror(tmp_path):
    module = _load_module()
    repo = tmp_path / "source"
    repo.mkdir()

    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "tests@forprint.local"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "ForPrint Tests"], cwd=repo, check=True)

    controller = repo / "scripts/coordination/roadmap_execution_reconciliation.py"
    controller.parent.mkdir(parents=True)
    controller.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "if sys.argv[-1] != 'sync':\n"
        "    raise SystemExit(2)\n"
        "base = Path('coordination/roadmap_execution/projections')\n"
        "base.mkdir(parents=True, exist_ok=True)\n"
        "(base / 'ROADMAP_EXECUTION_STATUS.yaml').write_text('sync: current\\n', encoding='utf-8')\n"
        "(base / 'ROADMAP_RECONCILIATION_STATUS.yaml').write_text('sync: current\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )

    (repo / "Makefile").write_text(
        "check-core:\n"
        "\t@test -f coordination/roadmap_execution/projections/ROADMAP_EXECUTION_STATUS.yaml\n"
        "\t@test -f coordination/roadmap_execution/projections/ROADMAP_RECONCILIATION_STATUS.yaml\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)

    source_exec = repo / "coordination/roadmap_execution/projections/ROADMAP_EXECUTION_STATUS.yaml"
    source_recon = repo / "coordination/roadmap_execution/projections/ROADMAP_RECONCILIATION_STATUS.yaml"
    assert not source_exec.exists()
    assert not source_recon.exists()

    rc = module.run_isolated_check(
        root=repo,
        target="check-core",
        module_root=None,
        keep_workspace=False,
    )

    assert rc == 0
    assert not source_exec.exists()
    assert not source_recon.exists()

def test_isolated_runner_converges_all_known_derived_prerequisites_only_in_mirror(
    tmp_path,
):
    module = _load_module()
    repo = tmp_path / "source"
    repo.mkdir()

    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "tests@forprint.local"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "ForPrint Tests"], cwd=repo, check=True)

    indexing = repo / "scripts/indexing"
    coordination = repo / "scripts/coordination"
    indexing.mkdir(parents=True)
    coordination.mkdir(parents=True)

    builders = {
        "build_generator_inventory.py": "indexes/generator_inventory.yaml",
        "build_execution_dependency_graph.py": "indexes/execution_dependency_graph.yaml",
        "build_blueprint_index.py": "indexes/blueprint_index.generated",
        "build_blueprint_knowledge_index.py": "indexes/blueprint_knowledge.generated",
        "build_blueprint_specialized_indexes.py": "indexes/blueprint_specialized.generated",
    }
    for script_name, output_rel in builders.items():
        (indexing / script_name).write_text(
            "from pathlib import Path\n"
            f"p = Path({output_rel!r})\n"
            "p.parent.mkdir(parents=True, exist_ok=True)\n"
            "p.write_text('generated: true\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )

    (coordination / "roadmap_execution_reconciliation.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "if sys.argv[-1] != 'sync':\n"
        "    raise SystemExit(2)\n"
        "p = Path('coordination/roadmap_execution/projections/ROADMAP_EXECUTION_STATUS.yaml')\n"
        "p.parent.mkdir(parents=True, exist_ok=True)\n"
        "p.write_text('sync: current\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )

    (coordination / "blueprint_continuity_adapter_v0_1.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "if '--refresh' not in sys.argv:\n"
        "    raise SystemExit(2)\n"
        "p = Path('coordination/continuity/projections/CURRENT_WORKFRONT.yaml')\n"
        "p.parent.mkdir(parents=True, exist_ok=True)\n"
        "p.write_text('fresh: true\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )

    required = [
        *builders.values(),
        "coordination/roadmap_execution/projections/ROADMAP_EXECUTION_STATUS.yaml",
        "coordination/continuity/projections/CURRENT_WORKFRONT.yaml",
    ]
    make_lines = ["check-core:"]
    make_lines.extend(f"\t@test -f {rel}" for rel in required)
    (repo / "Makefile").write_text("\n".join(make_lines) + "\n", encoding="utf-8")

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)

    for rel in required:
        assert not (repo / rel).exists()

    rc = module.run_isolated_check(
        root=repo,
        target="check-core",
        module_root=None,
        keep_workspace=False,
    )

    assert rc == 0
    for rel in required:
        assert not (repo / rel).exists()

def test_isolated_runner_reconciles_roadmap_again_after_continuity_refresh(
    tmp_path,
):
    module = _load_module()
    repo = tmp_path / "source"
    repo.mkdir()

    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "tests@forprint.local"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "ForPrint Tests"], cwd=repo, check=True)

    coordination = repo / "scripts/coordination"
    coordination.mkdir(parents=True)

    (coordination / "roadmap_execution_reconciliation.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "if sys.argv[-1] != 'sync':\n"
        "    raise SystemExit(2)\n"
        "continuity = Path('coordination/continuity/projections/CURRENT_WORKFRONT.yaml')\n"
        "out = Path('coordination/roadmap_execution/projections/ROADMAP_EXECUTION_STATUS.yaml')\n"
        "out.parent.mkdir(parents=True, exist_ok=True)\n"
        "state = 'after_continuity' if continuity.exists() else 'before_continuity'\n"
        "out.write_text('state: ' + state + '\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )

    (coordination / "blueprint_continuity_adapter_v0_1.py").write_text(
        "from pathlib import Path\n"
        "import sys\n"
        "if '--refresh' not in sys.argv:\n"
        "    raise SystemExit(2)\n"
        "p = Path('coordination/continuity/projections/CURRENT_WORKFRONT.yaml')\n"
        "p.parent.mkdir(parents=True, exist_ok=True)\n"
        "p.write_text('fresh: true\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )

    (repo / "Makefile").write_text(
        "check-core:\n"
        "\t@grep -q 'state: after_continuity' "
        "coordination/roadmap_execution/projections/ROADMAP_EXECUTION_STATUS.yaml\n"
        "\t@test -f coordination/continuity/projections/CURRENT_WORKFRONT.yaml\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)

    rc = module.run_isolated_check(
        root=repo,
        target="check-core",
        module_root=None,
        keep_workspace=False,
    )

    assert rc == 0
    assert not (
        repo
        / "coordination/roadmap_execution/projections/ROADMAP_EXECUTION_STATUS.yaml"
    ).exists()
    assert not (
        repo / "coordination/continuity/projections/CURRENT_WORKFRONT.yaml"
    ).exists()

