from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SOURCE = (
    ROOT
    / "scripts/coordination/control_plane/worker_runtime/launcher.py"
)
spec = importlib.util.spec_from_file_location("_cf10_launcher_test", SOURCE)
assert spec is not None and spec.loader is not None
launcher = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = launcher
spec.loader.exec_module(launcher)


def test_launcher_starts_argv_without_shell_and_captures_output(
    tmp_path: Path,
) -> None:
    events = []
    result = launcher.launch_process(
        argv=[
            sys.executable,
            "-c",
            "import sys; print('ok'); print('err', file=sys.stderr)",
        ],
        cwd=tmp_path,
        stdout_path=tmp_path / "stdout.txt",
        stderr_path=tmp_path / "stderr.txt",
        timeout_seconds=10,
        on_started=lambda row: events.append(row),
        heartbeat_seconds=1,
    )
    assert result["process_started"] is True
    assert result["shell"] is False
    assert result["return_code"] == 0
    assert result["timed_out"] is False
    assert len(events) == 1
    assert events[0]["pid"] > 0
    assert (tmp_path / "stdout.txt").read_text().strip() == "ok"
    assert (tmp_path / "stderr.txt").read_text().strip() == "err"


def test_launcher_callback_failure_terminates_started_process(
    tmp_path: Path,
) -> None:
    def broken(_row):
        raise RuntimeError("ledger append failed")

    with pytest.raises(RuntimeError, match="ledger append failed"):
        launcher.launch_process(
            argv=[
                sys.executable,
                "-c",
                "import time; time.sleep(30)",
            ],
            cwd=tmp_path,
            stdout_path=tmp_path / "stdout.txt",
            stderr_path=tmp_path / "stderr.txt",
            timeout_seconds=40,
            on_started=broken,
            heartbeat_seconds=1,
        )


def test_launcher_times_out_and_returns_evidence(tmp_path: Path) -> None:
    result = launcher.launch_process(
        argv=[
            sys.executable,
            "-c",
            "import time; time.sleep(2)",
        ],
        cwd=tmp_path,
        stdout_path=tmp_path / "stdout.txt",
        stderr_path=tmp_path / "stderr.txt",
        timeout_seconds=1,
        heartbeat_seconds=1,
    )
    assert result["process_started"] is True
    assert result["timed_out"] is True
    assert result["return_code"] != 0


def test_launcher_rejects_non_list_argv(tmp_path: Path) -> None:
    with pytest.raises(
        launcher.WorkerProcessLaunchError,
        match="argv must be a non-empty list",
    ):
        launcher.launch_process(
            argv="echo bad",
            cwd=tmp_path,
            stdout_path=tmp_path / "stdout.txt",
            stderr_path=tmp_path / "stderr.txt",
            timeout_seconds=1,
        )
