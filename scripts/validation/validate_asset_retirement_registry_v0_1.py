#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "asset_lifecycle_retirement_policy_v0_1.yaml"
)
REGISTRY = (
    ROOT
    / "coordination/internal_work/blueprint/cleanliness/"
    "asset_retirement_registry_v0_1.yaml"
)
SKIP_INVENTORY = (
    ROOT
    / "coordination/internal_work/blueprint/testing/"
    "2026-09-02__pytest_skip_inventory_v0_1.yaml"
)

STATUSES = {
    "ACTIVE",
    "DEPRECATED",
    "RETIREMENT_CANDIDATE",
    "NEEDS_OWNER_REVIEW",
    "ARCHIVE_APPROVED",
    "REMOVE_APPROVED",
    "HISTORICAL_ONLY",
    "RETIRED",
}
DISPOSITIONS = {
    "KEEP",
    "MOVE",
    "MERGE",
    "REWRITE",
    "DEPRECATE",
    "REMOVE",
    "NEEDS_OWNER_REVIEW",
}


def fail(message: str) -> None:
    print("ASSET_RETIREMENT_REGISTRY_VALIDATION=FAIL")
    print("ERROR=" + message)
    raise SystemExit(1)


def main() -> None:
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    skip_inventory = yaml.safe_load(SKIP_INVENTORY.read_text(encoding="utf-8"))

    if policy.get("status") != "ACTIVE":
        fail("POLICY_NOT_ACTIVE")
    if policy.get("approval_rules", {}).get("automatic_deletion_allowed") is not False:
        fail("AUTOMATIC_DELETION_NOT_FALSE")
    if policy.get("approval_rules", {}).get("age_only_removal_allowed") is not False:
        fail("AGE_ONLY_REMOVAL_NOT_FALSE")
    if registry.get("automatic_deletion_allowed") is not False:
        fail("REGISTRY_AUTOMATIC_DELETION_NOT_FALSE")
    if registry.get("automatic_archive_allowed") is not False:
        fail("REGISTRY_AUTOMATIC_ARCHIVE_NOT_FALSE")

    assets = registry.get("assets", [])
    if not isinstance(assets, list):
        fail("ASSETS_NOT_LIST")

    ids: set[str] = set()
    paths: set[str] = set()
    for item in assets:
        required = {
            "asset_id",
            "path",
            "asset_type",
            "owner",
            "lifecycle_status",
            "disposition",
            "reason",
            "evidence",
            "review_after",
            "removal_or_archive_condition",
        }
        missing = required - set(item)
        if missing:
            fail("MISSING_FIELDS:" + str(sorted(missing)))

        asset_id = item["asset_id"]
        path = item["path"]
        if asset_id in ids:
            fail("DUPLICATE_ASSET_ID:" + asset_id)
        if path in paths:
            fail("DUPLICATE_ASSET_PATH:" + path)
        ids.add(asset_id)
        paths.add(path)

        if item["lifecycle_status"] not in STATUSES:
            fail("UNKNOWN_STATUS:" + str(item["lifecycle_status"]))
        if item["disposition"] not in DISPOSITIONS:
            fail("UNKNOWN_DISPOSITION:" + str(item["disposition"]))
        if not (ROOT / path).is_file():
            fail("REGISTERED_ASSET_MISSING:" + path)
        if not item["evidence"]:
            fail("ASSET_WITHOUT_EVIDENCE:" + path)

        if item["lifecycle_status"] in {"REMOVE_APPROVED", "ARCHIVE_APPROVED"}:
            if item["disposition"] not in {"REMOVE", "MOVE"}:
                fail("APPROVED_STATUS_WITHOUT_ACTION_DISPOSITION:" + path)
            if not item.get("approval_evidence"):
                fail("APPROVED_STATUS_WITHOUT_APPROVAL_EVIDENCE:" + path)

    # Deprecated compatibility skips must be visible in the lifecycle registry.
    skip_paths = {
        group["path"]
        for group in skip_inventory.get("groups", [])
        if group.get("classification") == "PRESERVED_DEPRECATED_COMPATIBILITY"
    }
    if not skip_paths.issubset(paths):
        fail(
            "DEPRECATED_SKIP_ASSET_NOT_REGISTERED:"
            + ",".join(sorted(skip_paths - paths))
        )

    summary = registry.get("summary", {})
    if summary.get("registered_asset_count") != len(assets):
        fail("SUMMARY_REGISTERED_COUNT_DRIFT")

    computed = {
        "retirement_candidate_count": sum(
            item["lifecycle_status"] == "RETIREMENT_CANDIDATE"
            for item in assets
        ),
        "needs_owner_review_count": sum(
            item["lifecycle_status"] == "NEEDS_OWNER_REVIEW"
            for item in assets
        ),
        "remove_approved_count": sum(
            item["lifecycle_status"] == "REMOVE_APPROVED"
            for item in assets
        ),
        "archive_approved_count": sum(
            item["lifecycle_status"] == "ARCHIVE_APPROVED"
            for item in assets
        ),
    }
    for key, value in computed.items():
        if summary.get(key) != value:
            fail(f"SUMMARY_COUNT_DRIFT:{key}:actual={value}:stored={summary.get(key)}")

    print("ASSET_RETIREMENT_REGISTRY_VALIDATION=PASS")
    print(f"REGISTERED_ASSET_COUNT={len(assets)}")
    print(f"RETIREMENT_CANDIDATE_COUNT={computed['retirement_candidate_count']}")
    print(f"NEEDS_OWNER_REVIEW_COUNT={computed['needs_owner_review_count']}")
    print(f"REMOVE_APPROVED_COUNT={computed['remove_approved_count']}")
    print(f"ARCHIVE_APPROVED_COUNT={computed['archive_approved_count']}")
    print("AUTOMATIC_DELETION_ALLOWED=false")
    print("AUTOMATIC_ARCHIVE_ALLOWED=false")
    print("DEPRECATED_SKIP_COVERAGE=PASS")


if __name__ == "__main__":
    main()
