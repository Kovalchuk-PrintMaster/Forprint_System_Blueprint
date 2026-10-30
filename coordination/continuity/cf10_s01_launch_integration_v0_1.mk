# Read-only pilot corridor integration review; intentionally NOT live launch wiring.
# Explicit additional -f avoids overwriting quarantined Makefile prerequisites.
.PHONY: cf10-s01-integration-status cf10-s01-integration-report cf10-s01-integration-launch-preflight
cf10-s01-integration-status:
	@PYTHONDONTWRITEBYTECODE=1 .venv_blueprint/bin/python -B -m scripts.coordination.control_plane.cf10_s01_launch_integration_review_v0_1 status --root .
cf10-s01-integration-report:
	@PYTHONDONTWRITEBYTECODE=1 .venv_blueprint/bin/python -B -m scripts.coordination.control_plane.cf10_s01_launch_integration_review_v0_1 report --root .
cf10-s01-integration-launch-preflight:
	@PYTHONDONTWRITEBYTECODE=1 .venv_blueprint/bin/python -B -m scripts.coordination.control_plane.cf10_s01_launch_integration_review_v0_1 launch-preflight --root .
