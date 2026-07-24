from __future__ import annotations

from pathlib import Path
from subprocess import run

ROOT = Path(__file__).resolve().parents[4]


def test_module_workflow_make_target_is_parseable() -> None:
    result = run(
        ["make", "-n", "module-workflow-check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        "-m scripts.coordination.modules.module_workflow_cli"
        in result.stdout
    )
