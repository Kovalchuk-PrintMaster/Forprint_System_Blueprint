#!/usr/bin/env python3
"""Validate Markdown fenced-code structure against a ratcheted baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASELINE = Path(
    "machine/validation/markdown_fence_baseline.json"
)
SCHEMA_VERSION = "markdown_fence_baseline_v0_1"


@dataclass(frozen=True)
class FenceIssue:
    """One unmatched Markdown opening fence."""

    path: str
    opening_line: int
    fence_char: str
    fence_length: int
    info: str
    content_sha256: str

    def structural_signature(self) -> tuple[object, ...]:
        """Return fields that identify the known structural defect."""

        return (
            self.path,
            self.opening_line,
            self.fence_char,
            self.fence_length,
            self.info,
        )


def parse_fence_line(line: str) -> tuple[str, int, str] | None:
    """Parse a CommonMark-style fence line indented by at most 3 spaces."""

    raw = line.rstrip("\r\n")
    leading_spaces = len(raw) - len(raw.lstrip(" "))

    if leading_spaces > 3:
        return None

    content = raw[leading_spaces:]

    if not content or content[0] not in ("`", "~"):
        return None

    fence_char = content[0]
    fence_length = 0

    while (
        fence_length < len(content)
        and content[fence_length] == fence_char
    ):
        fence_length += 1

    if fence_length < 3:
        return None

    return (
        fence_char,
        fence_length,
        content[fence_length:].strip(),
    )


def audit_markdown_file(root: Path, relative: Path) -> FenceIssue | None:
    """Return the unmatched opening fence for one Markdown file."""

    path = root / relative
    data = path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    opening: tuple[str, int, int, str] | None = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        parsed = parse_fence_line(line)

        if parsed is None:
            continue

        fence_char, fence_length, info = parsed

        if opening is None:
            opening = (
                fence_char,
                fence_length,
                line_number,
                info,
            )
            continue

        open_char, open_length, _open_line, _open_info = opening

        if (
            fence_char == open_char
            and fence_length >= open_length
            and not info
        ):
            opening = None

    if opening is None:
        return None

    open_char, open_length, open_line, open_info = opening

    return FenceIssue(
        path=relative.as_posix(),
        opening_line=open_line,
        fence_char=open_char,
        fence_length=open_length,
        info=open_info,
        content_sha256=hashlib.sha256(data).hexdigest(),
    )


def tracked_markdown_paths(root: Path) -> list[Path]:
    """Return deterministic Git-tracked Markdown paths."""

    result = subprocess.run(
        ["git", "ls-files", "--", "*.md"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    return sorted(
        {
            Path(line.strip())
            for line in result.stdout.splitlines()
            if line.strip() and (root / line.strip()).is_file()
        },
        key=lambda path: path.as_posix(),
    )


def resolve_requested_paths(
    root: Path,
    requested: list[str],
) -> list[Path]:
    """Resolve an explicit focused path list inside the selected root."""

    paths: list[Path] = []

    for raw in requested:
        candidate = Path(raw)

        if candidate.is_absolute():
            try:
                relative = candidate.resolve().relative_to(root)
            except ValueError as error:
                raise ValueError(
                    f"path is outside root: {candidate}"
                ) from error
        else:
            relative = candidate

        path = root / relative

        if not path.is_file():
            raise ValueError(f"Markdown file not found: {relative}")

        if path.suffix.lower() != ".md":
            raise ValueError(f"Not a Markdown file: {relative}")

        paths.append(relative)

    return sorted(set(paths), key=lambda path: path.as_posix())


def load_baseline(path: Path) -> dict[str, FenceIssue]:
    """Load and validate the ratcheted known-defect baseline."""

    raw: dict[str, Any] = json.loads(
        path.read_text(encoding="utf-8")
    )

    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            "unsupported Markdown fence baseline schema"
        )

    entries = raw.get("known_issues")

    if not isinstance(entries, list):
        raise ValueError("baseline known_issues must be a list")

    baseline: dict[str, FenceIssue] = {}

    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(
                f"baseline entry {index} must be an object"
            )

        issue = FenceIssue(
            path=str(entry["path"]),
            opening_line=int(entry["opening_line"]),
            fence_char=str(entry["fence_char"]),
            fence_length=int(entry["fence_length"]),
            info=str(entry.get("info", "")),
            content_sha256=str(entry["content_sha256"]),
        )

        if issue.path in baseline:
            raise ValueError(
                f"duplicate baseline path: {issue.path}"
            )

        baseline[issue.path] = issue

    return baseline


def validate(
    *,
    root: Path,
    baseline_path: Path,
    requested_paths: list[str],
) -> int:
    """Validate current fence defects against the baseline."""

    paths = (
        resolve_requested_paths(root, requested_paths)
        if requested_paths
        else tracked_markdown_paths(root)
    )

    baseline = load_baseline(baseline_path)
    selected = {path.as_posix() for path in paths}

    if requested_paths:
        baseline = {
            path: issue
            for path, issue in baseline.items()
            if path in selected
        }

    current = {
        issue.path: issue
        for relative in paths
        if (issue := audit_markdown_file(root, relative))
        is not None
    }

    new_paths = sorted(set(current) - set(baseline))
    stale_paths = sorted(set(baseline) - set(current))
    changed_paths: list[str] = []

    for path in sorted(set(current) & set(baseline)):
        observed = current[path]
        expected = baseline[path]

        if (
            observed.structural_signature()
            != expected.structural_signature()
            or observed.content_sha256
            != expected.content_sha256
        ):
            changed_paths.append(path)

    print("Blueprint Markdown fence validation")
    print(f"Root: {root}")
    print(f"Files scanned: {len(paths)}")
    print(f"Current issues: {len(current)}")
    print(f"Baseline issues in scope: {len(baseline)}")
    print(f"New issues: {len(new_paths)}")
    print(f"Changed known issues: {len(changed_paths)}")
    print(f"Resolved but still baselined: {len(stale_paths)}")

    if new_paths:
        print("\nNEW ISSUES")
        for path in new_paths:
            issue = current[path]
            print(
                f"- {path}:{issue.opening_line}: "
                f"unclosed {issue.fence_char * issue.fence_length}"
                f"{issue.info}"
            )

    if changed_paths:
        print("\nCHANGED BASELINE FILES")
        for path in changed_paths:
            print(
                f"- {path}: known defective file changed; "
                "repair the fence or update the baseline deliberately"
            )

    if stale_paths:
        print("\nSTALE BASELINE ENTRIES")
        for path in stale_paths:
            print(
                f"- {path}: defect is resolved; remove its baseline entry"
            )

    if new_paths or changed_paths or stale_paths:
        print("\nFAILED: Markdown fence baseline mismatch")
        return 1

    print(
        "\nOK: no new Markdown fence defects beyond "
        "the ratcheted baseline."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the read-only validator CLI."""

    parser = argparse.ArgumentParser(
        description=(
            "Validate tracked Markdown fences against a "
            "ratcheted known-defect baseline."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root. Defaults to the Blueprint repository.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="Baseline JSON path, relative to root unless absolute.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional focused Markdown paths.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the read-only Markdown fence validator."""

    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    baseline_path = args.baseline

    if not baseline_path.is_absolute():
        baseline_path = root / baseline_path

    try:
        return validate(
            root=root,
            baseline_path=baseline_path,
            requested_paths=args.paths,
        )
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"ERROR: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
