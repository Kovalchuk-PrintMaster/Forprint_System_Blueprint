import subprocess
import sys
import tarfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/module_bootstrap/build_module_bootstrap_commission.py"


def test_bootstrap_commission_generator_builds_expected_archive(tmp_path):
    request = {
        "schema_version": "forprint_module_bootstrap_commission_request_v0_1",
        "package_class": "MODULE_BOOTSTRAP_COMMISSION",
        "target": {
            "classification": "NEW_TOP_LEVEL_MODULE_CANDIDATE",
            "module_id": "synthetic_bootstrap_test",
            "module_name": "Synthetic Bootstrap Test",
            "purpose": "Validate the canonical cold-start package generator.",
            "must_not_own": ["foreign_business_truth"],
            "filesystem_path": None,
            "remote_url": None,
            "default_branch": "main",
            "registration_state": "bootstrap_unregistered",
        },
        "authority": {
            "operator_task_ref": "pytest-fixture",
            "allowed_scope": "bootstrap_only",
            "may_enter_module_specific_implementation": False,
        },
        "bootstrap": {
            "canonical_manifest_path": "coordination/module/manifest.yaml",
            "python_policy": "resolve_current",
            "hard_root_path_exceptions": [],
        },
        "optional_committed_blueprint_sources": {
            "authority_source_path": None,
            "additional_source_paths": [],
        },
    }
    request_path = tmp_path / "request.yaml"
    request_path.write_text(
        yaml.safe_dump(request, sort_keys=False),
        encoding="utf-8",
    )
    output = tmp_path / "out"

    cp = subprocess.run(
        [
            sys.executable,
            str(GENERATOR),
            "--root",
            str(ROOT),
            "--request",
            str(request_path),
            "--output-dir",
            str(output),
            "build",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "MODULE_BOOTSTRAP_COMMISSION_BUILD=PASS" in cp.stdout
    assert "AUTHORITY_CREATED=false" in cp.stdout

    archives = list(output.glob("*.tar.gz"))
    assert len(archives) == 1

    with tarfile.open(archives[0], "r:gz") as tf:
        names = set(tf.getnames())
        prefix = "synthetic_bootstrap_test_bootstrap_commission"
        required = {
            f"{prefix}/00_READ_FIRST.md",
            f"{prefix}/bootstrap_commission.yaml",
            f"{prefix}/PACKAGE_MANIFEST.yaml",
            f"{prefix}/evidence_index.yaml",
            f"{prefix}/acceptance/root_surface_review.yaml",
            f"{prefix}/acceptance/cold_start_acceptance.yaml",
            f"{prefix}/BLUEPRINT_COMMITTED_REFERENCE/coordination/standards/governance/clean_repository_root_policy_v0_1.yaml",
            f"{prefix}/BLUEPRINT_COMMITTED_REFERENCE/coordination/standards/governance/module_bootstrap_commission_contract_v0_1.yaml",
            f"{prefix}/BLUEPRINT_COMMITTED_REFERENCE/coordination/instruction_intake/bootstrap/forprint_roadmap_operating_contract_v0_1.yaml",
            f"{prefix}/TEMPLATES/module_bootstrap_manifest.template.yaml",
            f"{prefix}/TOOLS_REFERENCE/module_assistant_context.py",
        }
        assert required.issubset(names)

        manifest_fh = tf.extractfile(f"{prefix}/PACKAGE_MANIFEST.yaml")
        assert manifest_fh is not None
        manifest = yaml.safe_load(manifest_fh.read().decode("utf-8"))
        assert manifest["package_class"] == "MODULE_BOOTSTRAP_COMMISSION"
        assert manifest["authority"] == {
            "execution": False,
            "acceptance": False,
            "release": False,
            "blueprint_write": False,
            "cross_repository_write": False,
            "production": False,
        }
        assert manifest["source_blueprint"]["head_equals_upstream"] is True

        root_fh = tf.extractfile(f"{prefix}/acceptance/root_surface_review.yaml")
        assert root_fh is not None
        root_review = yaml.safe_load(root_fh.read().decode("utf-8"))
        assert root_review["canonical_manifest_default"] == "coordination/module/manifest.yaml"
        assert root_review["duplicate_root_manifest_for_compatibility"] == "FORBIDDEN"
