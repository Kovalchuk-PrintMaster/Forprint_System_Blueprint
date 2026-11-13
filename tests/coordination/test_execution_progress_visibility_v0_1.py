from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from scripts.coordination.execution_progress import (
    ProgressConfig,
    ProgressReporter,
    add_progress_arguments,
    config_from_args,
)

ROOT = Path(__file__).resolve().parents[2]


def test_default_progress_is_visible_and_compact() -> None:
    config = ProgressConfig()
    assert config.mode == "always"
    assert config.heartbeat_seconds == 15.0
    assert config.child_output == "failures"


def test_progress_reporter_emits_phase_events() -> None:
    stream = io.StringIO()
    reporter = ProgressReporter(
        ProgressConfig(mode="always", heartbeat_seconds=1),
        stream=stream,
    )
    reporter.emit("START", "Example", step=2, total=4)
    reporter.emit(
        "PASS",
        "Example",
        step=2,
        total=4,
        elapsed_seconds=1.25,
    )
    text = stream.getvalue()
    assert "[02/04][START]" in text
    assert "[02/04][PASS]" in text
    assert "Example" in text


def test_silent_child_gets_heartbeat(tmp_path: Path) -> None:
    stream = io.StringIO()
    reporter = ProgressReporter(
        ProgressConfig(
            mode="always",
            heartbeat_seconds=0.05,
            child_output="quiet",
        ),
        stream=stream,
    )
    result = reporter.run(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(0.16)",
        ],
        cwd=ROOT,
        label="Silent child",
        log_path=tmp_path / "silent.log",
    )
    assert result.returncode == 0
    text = stream.getvalue()
    assert "[HEARTBEAT]" in text
    assert "[PASS]" in text


def test_failure_mode_surfaces_child_tail(tmp_path: Path) -> None:
    stream = io.StringIO()
    reporter = ProgressReporter(
        ProgressConfig(
            mode="always",
            heartbeat_seconds=1,
            child_output="failures",
        ),
        stream=stream,
    )
    result = reporter.run(
        [
            sys.executable,
            "-c",
            "print('VISIBLE_FAILURE_SENTINEL'); raise SystemExit(7)",
        ],
        cwd=ROOT,
        label="Failing child",
        log_path=tmp_path / "failure.log",
    )
    assert result.returncode == 7
    text = stream.getvalue()
    assert "[FAIL]" in text
    assert "VISIBLE_FAILURE_SENTINEL" in text
    assert "VISIBLE_FAILURE_SENTINEL" in (tmp_path / "failure.log").read_text(encoding="utf-8")


def test_no_progress_is_explicit_opt_out(monkeypatch) -> None:
    monkeypatch.setenv("FORPRINT_PROGRESS", "always")
    parser = argparse.ArgumentParser()
    add_progress_arguments(parser)
    args = parser.parse_args(["--no-progress"])
    config = config_from_args(args)
    assert config.mode == "never"

    stream = io.StringIO()
    ProgressReporter(config, stream=stream).emit("START", "Hidden")
    assert stream.getvalue() == ""


def test_agents_binds_future_assistants_to_progress_contract() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "<!-- FORPRINT_EXECUTION_PROGRESS_VISIBILITY_START -->" in text
    assert "execution_progress_visibility_contract_v0_1.yaml" in text
    assert "must not remain silent" in text


def test_make_exports_progress_defaults() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "FORPRINT_PROGRESS ?= always" in text
    assert "FORPRINT_PROGRESS_HEARTBEAT_SECONDS ?= 15" in text
    assert "FORPRINT_PROGRESS_CHILD_OUTPUT ?= failures" in text
    assert "export FORPRINT_PROGRESS" in text
    assert "execution-progress-check:" in text
