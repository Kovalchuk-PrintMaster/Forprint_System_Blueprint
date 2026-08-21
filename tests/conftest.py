
# FORPRINT_LEGACY_COMPATIBILITY_COLLECTION_POLICY_V0_1
def pytest_collection_modifyitems(config, items):
    from pathlib import Path

    import pytest
    import yaml

    root = Path(str(config.rootpath))
    registry_path = (
        root / "coordination/legacy/compatibility_registry_v0_1.yaml"
    )
    if not registry_path.is_file():
        return

    data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return

    deprecated_modules = set()
    deprecated_nodeids = set()

    for component in data.get("components", []):
        if not isinstance(component, dict):
            continue
        if component.get("blocking_current_gates") is True:
            continue
        if component.get("status") not in {
            "deprecated_candidate",
            "historical_frozen",
        }:
            continue

        deprecated_modules.update(
            str(value).replace("\\\\", "/")
            for value in component.get("deprecated_test_modules", [])
        )
        deprecated_nodeids.update(
            str(value).replace("\\\\", "/")
            for value in component.get("deprecated_test_nodeids", [])
        )

    if not deprecated_modules and not deprecated_nodeids:
        return

    reason = (
        "deprecated compatibility test; excluded from current release gate; "
        "retained for historical/manual migration use"
    )
    skip_marker = pytest.mark.skip(reason=reason)

    for item in items:
        nodeid = item.nodeid.replace("\\\\", "/")
        module_path = nodeid.split("::", 1)[0]
        if module_path in deprecated_modules or nodeid in deprecated_nodeids:
            item.add_marker(skip_marker)
