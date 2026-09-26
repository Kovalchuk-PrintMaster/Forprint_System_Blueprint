from pathlib import Path

import yaml

from scripts.coordination.control_plane.worker_runtime.bootstrap_profile import validate_profile

STANDARD = Path(
    "coordination/standards/automation/control_plane/bootstrap_worker_runtime_profile_v0_1.yaml"
)


def main() -> int:
    data = yaml.safe_load(STANDARD.read_text(encoding="utf-8"))
    validate_profile(data)
    print("BOOTSTRAP_WORKER_RUNTIME_PROFILE=PASS")
    print("MODULE_BOOTSTRAP_ONLY=true")
    print("MODULE_RUNTIME_PROFILE_REQUIRED_FOR_BOOTSTRAP=false")
    print("MODULE_RUNTIME_PROFILE_REQUIRED_FOR_ROADMAP_DEVELOPMENT=true")
    print("PROVIDER_SECRET_IN_GIT=false")
    print("WORKER_PROCESS_STARTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
