from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

EXPECTED_IDS = {
    "forprint_accounting_registry_service",
    "forprint_integration_gateway",
    "forprint_library",
    "logistics_service",
    "forprint_operations_control_registry",
    "forprint_system_blueprint",
    "website",
    "telegram_bot",
}
OUTBOX = "coordination/completion_outbox/records"


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("registry root must be mapping")
    return data


def origin(repo: Path) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), "remote", "get-url", "origin"],
        text=True,
        capture_output=True,
        check=False,
    )
    return cp.stdout.strip() if cp.returncode == 0 else ""


def validate(path: Path) -> list[str]:
    data = load(path)
    errors: list[str] = []
    if data.get("schema_version") != "coordination_source_registry_v0_1":
        errors.append("SCHEMA_VERSION")
    if data.get("metadata", {}).get("owner") != "forprint_system_blueprint":
        errors.append("OWNER")
    modules = data.get("modules")
    if not isinstance(modules, list):
        return errors + ["MODULES_MISSING"]
    ids = [str(x.get("module_id")) for x in modules if isinstance(x, dict)]
    if len(ids) != len(set(ids)):
        errors.append("DUPLICATE_MODULE_ID")
    if set(ids) != EXPECTED_IDS:
        errors.append("MODULE_SET")
    repo_ids: list[str] = []
    local_paths: list[str] = []
    for item in modules:
        if not isinstance(item, dict):
            errors.append("MODULE_RECORD")
            continue
        mid = str(item.get("module_id", ""))
        repo = item.get("repository", {})
        sources = item.get("sources", {})
        bounds = item.get("boundaries", {})
        rid = str(repo.get("repository_id", ""))
        lp = str(repo.get("local_path", ""))
        repo_ids.append(rid)
        local_paths.append(lp)
        p = Path(lp)
        if not p.is_absolute() or not (p / ".git").exists():
            errors.append(f"REPO_MISSING:{mid}")
        elif origin(p) != repo.get("origin"):
            errors.append(f"ORIGIN_MISMATCH:{mid}")
        if repo.get("remote_name") != "origin":
            errors.append(f"REMOTE_NAME:{mid}")
        if "head" in repo or "branch" in repo:
            errors.append(f"VOLATILE_PIN:{mid}")
        module_source = sources.get("module_source", {})
        roadmap = sources.get("roadmap", {})
        queue = sources.get("prompt_queue", {})
        outbox = sources.get("completion_outbox", {})
        if module_source.get("owner") != mid or module_source.get("path") != ".":
            errors.append(f"MODULE_SOURCE:{mid}")
        if outbox.get("owner") != mid or outbox.get("path") != OUTBOX:
            errors.append(f"OUTBOX:{mid}")
        if outbox.get("availability") not in {"present", "not_present_yet"}:
            errors.append(f"OUTBOX_AVAILABILITY:{mid}")
        for name, src in (("roadmap", roadmap), ("prompt_queue", queue)):
            if src.get("availability") not in {"present", "not_registered"}:
                errors.append(f"{name.upper()}_AVAILABILITY:{mid}")
            if not isinstance(src.get("path"), str) or str(src.get("path")).startswith("/"):
                errors.append(f"{name.upper()}_PATH:{mid}")
        if bounds.get("blueprint_lookup_mode") != "read_only":
            errors.append(f"LOOKUP_MODE:{mid}")
        expected_write = mid == "forprint_system_blueprint"
        if bounds.get("blueprint_may_write_repository") is not expected_write:
            errors.append(f"WRITE_BOUNDARY:{mid}")
    if len(repo_ids) != len(set(repo_ids)):
        errors.append("DUPLICATE_REPOSITORY_ID")
    if len(local_paths) != len(set(local_paths)):
        errors.append("DUPLICATE_LOCAL_PATH")
    policy = data.get("lookup_policy", {})
    if policy.get("module_id_is_repository_name") is not False:
        errors.append("ID_DERIVATION")
    if policy.get("module_repository_access") != "read_only_from_blueprint":
        errors.append("ACCESS_POLICY")
    if policy.get("completion_outbox_future_path") != OUTBOX:
        errors.append("OUTBOX_POLICY")
    self_entry = next(
        (x for x in modules if x.get("module_id") == "forprint_system_blueprint"), None
    )
    if self_entry:
        if (
            self_entry["sources"]["roadmap"]["path"]
            != "coordination/self_coordination/roadmap.yaml"
        ):
            errors.append("SELF_ROADMAP")
        if (
            self_entry["sources"]["prompt_queue"]["path"]
            != "coordination/self_coordination/prompt_queue/index.yaml"
        ):
            errors.append("SELF_QUEUE")
    return errors


def main() -> int:
    path = Path("coordination/registry/coordination_source_registry_v0_1.yaml")
    errors = validate(path)
    if errors:
        for error in errors:
            print("ERROR:", error)
        print(f"RESULT: COORDINATION_SOURCE_REGISTRY_INVALID ({len(errors)})")
        return 1
    print("modules: 8")
    print("RESULT: COORDINATION_SOURCE_REGISTRY_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
