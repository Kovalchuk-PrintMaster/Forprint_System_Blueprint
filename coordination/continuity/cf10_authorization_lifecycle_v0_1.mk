# CF-10 authorization lifecycle / project-native operator commands.
# Append with -f; intentionally does not override quarantined live Make targets.
.PHONY: cf10-auth-status cf10-auth-request cf10-auth-resume-check
cf10-auth-status:
	@PYTHONDONTWRITEBYTECODE=1 $(if $(BLUEPRINT_PYTHON),$(BLUEPRINT_PYTHON),python3) -B -m scripts.coordination.control_plane.cf10_authorization_lifecycle_v0_1 status --root .
cf10-auth-request:
	@PYTHONDONTWRITEBYTECODE=1 $(if $(BLUEPRINT_PYTHON),$(BLUEPRINT_PYTHON),python3) -B -m scripts.coordination.control_plane.cf10_authorization_lifecycle_v0_1 run --root .
cf10-auth-resume-check:
	@PYTHONDONTWRITEBYTECODE=1 $(if $(BLUEPRINT_PYTHON),$(BLUEPRINT_PYTHON),python3) -B -m scripts.coordination.control_plane.cf10_authorization_lifecycle_v0_1 resume-check --root .
