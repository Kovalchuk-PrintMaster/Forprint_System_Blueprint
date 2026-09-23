from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.indexing import build_blueprint_knowledge_index as builder

ROOT = Path(__file__).resolve().parents[2]


def test_reference_pattern_filter_rejects_recursive_runtime_caches(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(builder, "ROOT", tmp_path)

    allowed = tmp_path / "scripts" / "validation"
    allowed.mkdir(parents=True)

    cache_file = tmp_path / "scripts" / "validation" / "__pycache__" / "validator.cpython-311.pyc"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_bytes(b"cache")

    node_file = tmp_path / "tools" / "node_modules" / "pkg" / "index.js"
    node_file.parent.mkdir(parents=True)
    node_file.write_text("x", encoding="utf-8")

    assert builder._include_reference_pattern_match(allowed)
    assert not builder._include_reference_pattern_match(cache_file)
    assert not builder._include_reference_pattern_match(node_file)


def test_runtime_cache_filter_is_wired_into_glob_resolution() -> None:
    source = (ROOT / "scripts/indexing/build_blueprint_knowledge_index.py").read_text(
        encoding="utf-8"
    )

    assert "RECURSIVE_RUNTIME_CACHE_PARTS" in source
    assert "if _include_reference_pattern_match(item)" in source


def test_knowledge_index_is_current_after_runtime_cache_hardening() -> None:
    process = subprocess.run(
        [
            sys.executable,
            "scripts/indexing/build_blueprint_knowledge_index.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert process.returncode == 0, process.stdout
