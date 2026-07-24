from pathlib import Path

import pytest
import yaml

from scripts.coordination.modules._shared.external_input import (
    build_input_template,
    validate_provided_input,
)
from scripts.coordination.modules._shared.io import WorkflowError


def test_external_input_requires_exact_identity(tmp_path: Path) -> None:
    path = tmp_path / "bsa.yaml"
    data = build_input_template(
        request_id="bsa-test",
        bundle_path="tmp/bundle.tar.gz",
        bundle_sha256="abc123",
    )
    data["status"] = "provided"
    data["analysis"]["summary"] = "Current state assessed."
    data["analysis"]["confidence"] = "high"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    result = validate_provided_input(
        path,
        expected_request_id="bsa-test",
        expected_bundle_sha256="abc123",
    )

    assert result["analysis"]["summary"] == "Current state assessed."
    assert result["input_sha256"]


def test_external_input_rejects_empty_summary(tmp_path: Path) -> None:
    path = tmp_path / "bsa.yaml"
    data = build_input_template(
        request_id="bsa-test",
        bundle_path="tmp/bundle.tar.gz",
        bundle_sha256="abc123",
    )
    data["status"] = "provided"
    data["analysis"]["confidence"] = "medium"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    with pytest.raises(WorkflowError, match="analysis.summary"):
        validate_provided_input(
            path,
            expected_request_id="bsa-test",
            expected_bundle_sha256="abc123",
        )
