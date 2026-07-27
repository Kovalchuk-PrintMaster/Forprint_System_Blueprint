# Blueprint Completion Report — Website Roadmap Legacy Control Refinement v0.2.1

## Module

`forprint_system_blueprint`

## Related module

`website`

## Working name

`ForPrint_Web_Site_Base`

## Source prompt

`coordination/outgoing_prompts/forprint_system_blueprint/approved/2026-07-07__blueprint__website_roadmap_legacy_control_refinement_v0_2_1.md`

## Status

`website_roadmap_legacy_control_refinement_v0_2_1_prepared`

## Roadmap changes

Updated:

```text
coordination/roadmaps/website.yaml
```

The website roadmap now explicitly tracks the conservative path:

legacy PHP base -> controlled repository -> source/runtime split -> config split -> schema recovery -> web-root hardening -> smoke tests -> admin/upload/SQL hardening -> lead-capture-only launch profile -> limited launch gate -> future next version
New / refined steps

The roadmap now includes:

website_scaffolding_first_safe_commit_v0_4
website_legacy_base_inventory_v0_4_1
website_safe_tracking_policy_v0_4_2
website_config_split_and_secret_policy_v0_4_3
website_database_schema_recovery_v0_4_4
website_selected_base_source_checkpoint_v0_4_5
website_webroot_exposure_hardening_v0_5
website_public_exposure_smoke_tests_v0_5_1
website_admin_auth_session_lockdown_v0_6
website_admin_access_policy_v0_6_1
website_upload_safety_lockdown_v0_7
website_sql_user_input_review_v0_8
website_launch_mode_restriction_v0_9
website_public_launch_profile_v0_9_1
website_dependency_backup_environment_v0_10
website_seo_lead_capture_readiness_v0_11
website_limited_public_launch_gate_v0_12
website_future_next_version_planning_v0_13
website_future_gateway_handoff_gate_v0_14
Risk register changes

Created or updated:

coordination/risk_registers/website.yaml

The risk register tracks:

hardcoded/local config risk
dynamic SQL risk
md5 password risk
upload execution risk
public web-root exposure risk
inherited vendor exposure risk
local order/client/product table ownership confusion risk
missing DB schema risk
missing backup/restore procedure risk
public admin exposure risk
secret/config tracking risk
Current website step

Current roadmap step:

website_scaffolding_first_safe_commit_v0_4

Next conservative Website prompt after the scaffold checkpoint:

ForPrint_Web_Site_Base — Legacy Base Inventory and Safe Tracking Policy v0.4.1
Boundary confirmation

The website remains a public channel / lead-capture surface only.

It must not become canonical owner of:

products
clients
orders
payments
stock
accounting
1C data
Calculator pricing rules

Future integration must go through:

Website request -> Integration Gateway -> approved downstream module
Known check note

If global make check fails because of the unrelated Telegram Bot outgoing prompt index issue, report it without hiding it.

Expected wording:

Website roadmap/dashboard validation passed.
Global make check failed due to unrelated telegram_bot outgoing prompt index issue.
No website roadmap regression detected.
Public launch status

Public launch remains blocked until website_limited_public_launch_gate_v0_12 is explicitly approved.
