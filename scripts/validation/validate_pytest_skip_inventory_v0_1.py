#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = (
    ROOT
    / "coordination/internal_work/blueprint/testing/"
    "2026-09-02__pytest_skip_inventory_v0_1.yaml"
)


class SkipCollector:
    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []

    @pytest.hookimpl
    def pytest_collection_finish(self, session: pytest.Session) -> None:
        for item in session.items:
            for marker in item.iter_markers(name="skip"):
                reason = str(marker.kwargs.get("reason", "")).strip()
                self.items.append((item.nodeid, reason))
                break


def fail(message: str) -> None:
    print("PYTEST_SKIP_INVENTORY_VALIDATION=FAIL")
    print("ERROR=" + message)
    raise SystemExit(1)


def main() -> None:
    inventory = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    if not isinstance(inventory, dict):
        fail("INVENTORY_NOT_MAPPING")

    collector = SkipCollector()
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
        result = pytest.main(["--collect-only", "-q"], plugins=[collector])

    if result != pytest.ExitCode.OK:
        fail("PYTEST_COLLECTION_FAILED")

    actual_by_path: dict[str, list[str]] = {}
    for nodeid, reason in collector.items:
        path = nodeid.split("::", 1)[0]
        actual_by_path.setdefault(path, []).append(reason)

    groups = inventory.get("groups", [])
    expected_by_path = {group["path"]: group for group in groups}

    if set(actual_by_path) != set(expected_by_path):
        fail(
            "SKIP_PATH_SET_DRIFT:"
            f"actual={sorted(actual_by_path)}:"
            f"expected={sorted(expected_by_path)}"
        )

    actual_total = 0
    for path, group in expected_by_path.items():
        reasons = actual_by_path[path]
        expected_count = int(group["expected_skipped_test_count"])
        if len(reasons) != expected_count:
            fail(
                f"SKIP_COUNT_DRIFT:{path}:actual={len(reasons)}:"
                f"expected={expected_count}"
            )

        expected_reason = str(group["reason"])
        if any(reason != expected_reason for reason in reasons):
            fail(
                f"SKIP_REASON_DRIFT:{path}:"
                f"actual={sorted(set(reasons))}:expected={expected_reason}"
            )

        actual_total += len(reasons)

    expected_total = int(inventory["expected_total_skipped_tests"])
    if actual_total != expected_total:
        fail(
            f"TOTAL_SKIP_COUNT_DRIFT:actual={actual_total}:expected={expected_total}"
        )

    summary = inventory.get("summary", {})
    if int(summary.get("registered_skipped_test_count", -1)) != expected_total:
        fail("INVENTORY_SUMMARY_COUNT_DRIFT")
    if int(summary.get("unexplained_skip_count", -1)) != 0:
        fail("INVENTORY_UNEXPLAINED_SKIP_COUNT_NOT_ZERO")

    print("PYTEST_SKIP_INVENTORY_VALIDATION=PASS")
    print(f"REGISTERED_SKIP_GROUP_COUNT={len(groups)}")
    print(f"REGISTERED_SKIPPED_TEST_COUNT={actual_total}")
    print("UNEXPLAINED_SKIP_COUNT=0")
    print("SKIP_DELETION_RECOMMENDED=false")


if __name__ == "__main__":
    main()
