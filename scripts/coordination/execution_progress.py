#!/usr/bin/env python3
"""Shared ForPrint execution progress and streaming subprocess helper."""

from __future__ import annotations

import argparse
import io
import os
import queue
import subprocess
import sys
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

PROGRESS_ENV = "FORPRINT_PROGRESS"
HEARTBEAT_ENV = "FORPRINT_PROGRESS_HEARTBEAT_SECONDS"
CHILD_OUTPUT_ENV = "FORPRINT_PROGRESS_CHILD_OUTPUT"

PROGRESS_MODES = {"always", "auto", "never"}
CHILD_OUTPUT_MODES = {"live", "failures", "quiet"}

DEFAULT_PROGRESS_MODE = "always"
DEFAULT_HEARTBEAT_SECONDS = 15.0
DEFAULT_CHILD_OUTPUT = "failures"


class ProgressConfigurationError(ValueError):
    """Raised when progress configuration is invalid."""


@dataclass(frozen=True)
class ProgressConfig:
    mode: str = DEFAULT_PROGRESS_MODE
    heartbeat_seconds: float = DEFAULT_HEARTBEAT_SECONDS
    child_output: str = DEFAULT_CHILD_OUTPUT

    def __post_init__(self) -> None:
        if self.mode not in PROGRESS_MODES:
            raise ProgressConfigurationError(f"invalid progress mode: {self.mode}")
        if self.heartbeat_seconds <= 0:
            raise ProgressConfigurationError("heartbeat_seconds must be greater than zero")
        if self.child_output not in CHILD_OUTPUT_MODES:
            raise ProgressConfigurationError(f"invalid child output mode: {self.child_output}")


@dataclass(frozen=True)
class StreamingResult:
    command: tuple[str, ...]
    returncode: int
    output: str
    elapsed_seconds: float


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ProgressConfigurationError(f"{name} must be numeric, got {raw!r}") from exc
    if value <= 0:
        raise ProgressConfigurationError(f"{name} must be greater than zero")
    return value


def config_from_environment() -> ProgressConfig:
    return ProgressConfig(
        mode=os.environ.get(PROGRESS_ENV, DEFAULT_PROGRESS_MODE).strip().lower(),
        heartbeat_seconds=_float_env(
            HEARTBEAT_ENV,
            DEFAULT_HEARTBEAT_SECONDS,
        ),
        child_output=os.environ.get(
            CHILD_OUTPUT_ENV,
            DEFAULT_CHILD_OUTPUT,
        )
        .strip()
        .lower(),
    )


def add_progress_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--progress-mode",
        choices=sorted(PROGRESS_MODES),
        default=None,
    )
    parser.add_argument(
        "--heartbeat-seconds",
        type=float,
        default=None,
    )
    parser.add_argument(
        "--progress-child-output",
        choices=sorted(CHILD_OUTPUT_MODES),
        default=None,
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Explicitly suppress progress events for this invocation.",
    )


def config_from_args(args: argparse.Namespace) -> ProgressConfig:
    base = config_from_environment()
    mode = getattr(args, "progress_mode", None) or base.mode
    if getattr(args, "no_progress", False):
        mode = "never"
    return ProgressConfig(
        mode=mode,
        heartbeat_seconds=(getattr(args, "heartbeat_seconds", None) or base.heartbeat_seconds),
        child_output=(getattr(args, "progress_child_output", None) or base.child_output),
    )


class ProgressReporter:
    """Stable stderr progress events plus streaming child execution."""

    def __init__(
        self,
        config: ProgressConfig | None = None,
        *,
        stream: TextIO | None = None,
    ) -> None:
        self.config = config or config_from_environment()
        self.stream = stream or sys.stderr

    def visible(self) -> bool:
        if self.config.mode == "never":
            return False
        if self.config.mode == "always":
            return True
        isatty = getattr(self.stream, "isatty", None)
        return bool(isatty and isatty())

    def emit(
        self,
        status: str,
        message: str,
        *,
        step: int | None = None,
        total: int | None = None,
        elapsed_seconds: float | None = None,
    ) -> None:
        if not self.visible():
            return

        timestamp = time.strftime("%H:%M:%S")
        step_token = ""
        if step is not None and total is not None:
            width = max(2, len(str(total)))
            step_token = f"[{step:0{width}d}/{total:0{width}d}]"

        elapsed_token = ""
        if elapsed_seconds is not None:
            elapsed_token = f"[{elapsed_seconds:.1f}s]"

        print(
            f"[FORPRINT][{timestamp}]{step_token}[{status.upper()}]{elapsed_token} {message}",
            file=self.stream,
            flush=True,
        )

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        label: str,
        step: int | None = None,
        total: int | None = None,
        log_path: Path | None = None,
        env: dict[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> StreamingResult:
        argv = tuple(str(item) for item in command)
        started = time.monotonic()
        last_visible_activity = started
        self.emit("START", label, step=step, total=total)

        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)

        process = subprocess.Popen(
            argv,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            env=env,
        )
        if process.stdout is None:
            process.kill()
            raise RuntimeError("subprocess stdout pipe was not created")

        output_queue: queue.Queue[str | None] = queue.Queue()

        def reader() -> None:
            try:
                for line in process.stdout:
                    output_queue.put(line)
            finally:
                output_queue.put(None)

        thread = threading.Thread(
            target=reader,
            name="forprint-progress-reader",
            daemon=True,
        )
        thread.start()

        chunks: list[str] = []
        reader_done = False
        heartbeat = self.config.heartbeat_seconds

        with (
            log_path.open("w", encoding="utf-8") if log_path is not None else io.StringIO()
        ) as log_handle:
            while True:
                now = time.monotonic()
                if timeout_seconds is not None and now - started > timeout_seconds:
                    process.kill()
                    process.wait()
                    elapsed = time.monotonic() - started
                    self.emit(
                        "FAIL",
                        f"{label} — timeout",
                        step=step,
                        total=total,
                        elapsed_seconds=elapsed,
                    )
                    raise subprocess.TimeoutExpired(
                        argv,
                        timeout_seconds,
                        output="".join(chunks),
                    )

                wait_for = min(
                    0.25,
                    max(0.01, heartbeat - (now - last_visible_activity)),
                )
                try:
                    item = output_queue.get(timeout=wait_for)
                except queue.Empty:
                    item = "__FORPRINT_QUEUE_EMPTY__"

                if item is None:
                    reader_done = True
                elif item != "__FORPRINT_QUEUE_EMPTY__":
                    chunks.append(item)
                    log_handle.write(item)
                    log_handle.flush()
                    last_visible_activity = time.monotonic()
                    if self.config.child_output == "live" and self.visible():
                        print(
                            item,
                            end="",
                            file=self.stream,
                            flush=True,
                        )

                now = time.monotonic()
                if process.poll() is None and now - last_visible_activity >= heartbeat:
                    self.emit(
                        "HEARTBEAT",
                        f"{label} still running",
                        step=step,
                        total=total,
                        elapsed_seconds=now - started,
                    )
                    last_visible_activity = now

                if reader_done and process.poll() is not None:
                    break

        thread.join(timeout=1.0)
        returncode = process.wait()
        elapsed = time.monotonic() - started
        output = "".join(chunks)

        if returncode == 0:
            self.emit(
                "PASS",
                label,
                step=step,
                total=total,
                elapsed_seconds=elapsed,
            )
        else:
            self.emit(
                "FAIL",
                f"{label} rc={returncode}",
                step=step,
                total=total,
                elapsed_seconds=elapsed,
            )
            if self.config.child_output == "failures" and self.visible():
                tail = output.splitlines()[-120:]
                if tail:
                    print(
                        "\n".join(tail),
                        file=self.stream,
                        flush=True,
                    )

        return StreamingResult(
            command=argv,
            returncode=returncode,
            output=output,
            elapsed_seconds=elapsed,
        )


def _demo(args: argparse.Namespace) -> int:
    config = config_from_args(args)
    reporter = ProgressReporter(config)
    result = reporter.run(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(0.15); print('demo child complete')",
        ],
        cwd=Path.cwd(),
        label="Execution progress demo",
        step=1,
        total=1,
    )
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    add_progress_arguments(parser)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    if args.demo:
        return _demo(args)

    config = config_from_args(args)
    print(
        "FORPRINT_PROGRESS_CONFIG="
        f"mode={config.mode},"
        f"heartbeat_seconds={config.heartbeat_seconds:g},"
        f"child_output={config.child_output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
