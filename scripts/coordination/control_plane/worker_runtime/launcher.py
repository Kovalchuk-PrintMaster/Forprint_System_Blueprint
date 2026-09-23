from __future__ import annotations

import hashlib
import subprocess
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path


class WorkerProcessLaunchError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _argv_digest(argv: list[str]) -> str:
    return hashlib.sha256("\0".join(argv).encode("utf-8")).hexdigest()


def launch_process(
    *,
    argv: list[str],
    cwd: Path | str,
    stdout_path: Path | str,
    stderr_path: Path | str,
    timeout_seconds: int,
    on_started: Callable[[dict], None] | None = None,
    on_heartbeat: Callable[[dict], None] | None = None,
    heartbeat_seconds: int = 15,
) -> dict:
    if not isinstance(argv, list) or not argv:
        raise WorkerProcessLaunchError("argv must be a non-empty list")
    if not all(isinstance(item, str) and item for item in argv):
        raise WorkerProcessLaunchError("argv items must be non-empty strings")
    if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
        raise WorkerProcessLaunchError("timeout_seconds must be positive")
    if not isinstance(heartbeat_seconds, int) or heartbeat_seconds <= 0:
        raise WorkerProcessLaunchError("heartbeat_seconds must be positive")

    working = Path(cwd).expanduser().resolve()
    if not working.is_dir():
        raise WorkerProcessLaunchError("cwd must be an existing directory")

    out = Path(stdout_path).expanduser().resolve()
    err = Path(stderr_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    err.parent.mkdir(parents=True, exist_ok=True)

    started_at = _now()
    started_monotonic = time.monotonic()

    with out.open("wb") as stdout_handle, err.open("wb") as stderr_handle:
        try:
            process = subprocess.Popen(
                argv,
                cwd=working,
                stdout=stdout_handle,
                stderr=stderr_handle,
                shell=False,
            )
        except Exception as exc:
            raise WorkerProcessLaunchError(
                f"process start failed: {type(exc).__name__}: {exc}"
            ) from exc

        started = {
            "pid": process.pid,
            "started_at": started_at,
            "cwd": str(working),
            "argv_sha256": _argv_digest(argv),
            "shell": False,
        }

        try:
            if on_started is not None:
                on_started(dict(started))
        except Exception:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            raise

        deadline = started_monotonic + timeout_seconds
        next_heartbeat = started_monotonic + heartbeat_seconds
        timed_out = False

        while process.poll() is None:
            current = time.monotonic()
            if current >= deadline:
                timed_out = True
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                break

            if current >= next_heartbeat:
                if on_heartbeat is not None:
                    on_heartbeat(
                        {
                            "pid": process.pid,
                            "elapsed_seconds": round(
                                current - started_monotonic,
                                3,
                            ),
                        }
                    )
                next_heartbeat = current + heartbeat_seconds

            time.sleep(0.25)

        return_code = process.returncode
        if return_code is None:
            return_code = process.wait()

    return {
        **started,
        "finished_at": _now(),
        "elapsed_seconds": round(
            time.monotonic() - started_monotonic,
            3,
        ),
        "return_code": int(return_code),
        "timed_out": timed_out,
        "stdout_path": str(out),
        "stderr_path": str(err),
        "process_started": True,
    }
