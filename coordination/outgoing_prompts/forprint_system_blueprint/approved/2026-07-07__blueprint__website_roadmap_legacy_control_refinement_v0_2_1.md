# Prompt: Refine Website Roadmap with Legacy Base Control and Risk Register v0.2.1

## Target module

`forprint_system_blueprint`

## Related module

`website`

## Assistant working name

`ForPrint_Web_Site_Base`

## Purpose

Update the Blueprint-controlled `website` roadmap after the v0.1, v0.2 and v0.3 Website Base reports.

The current website roadmap is structurally correct, but it must be expanded with stronger legacy PHP base controls before public launch or broad repository tracking.

The website must remain a public channel / lead-capture surface, not a canonical owner of ForPrint products, clients, orders, payments, stock, accounting or 1C data.

## Current known state

Website repository root:

```text
/srv/software_development/forprint-project/forprint_website
```

Website base directory:

```text
/srv/software_development/forprint-project/forprint_website/base
```

Completed checkpoints:

website_initial_read_only_inspection_v0_1
website_repository_control_deep_inspection_v0_2
website_secret_cleanup_php82_v0_3

v0.3 completed:

SMTP config cleanup;
mail.local.php local-only approach;
mail.example.php placeholder-only example;
PHP 8.2 fatal syntax blocker fixed;
make php-syntax passed;
make check passed;
broad git add base/ remains forbidden.
Required changes
1. Update coordination/roadmaps/website.yaml

Update or create:

coordination/roadmaps/website.yaml

Use schema:

module_development_roadmap_v0_1

The roadmap must include the complete path:

legacy PHP base -> controlled repository -> source/runtime split -> config split -> schema recovery -> web-root hardening -> smoke tests -> admin/upload/SQL hardening -> lead-capture-only launch profile -> limited launch gate -> future next version
Required roadmap sequencing

Use this sequence or an equivalent sequence with the same meaning:

Completed
website_initial_read_only_inspection_v0_1
website_repository_control_deep_inspection_v0_2
website_secret_cleanup_php82_v0_3
Next / ready / planned
website_scaffolding_first_safe_commit_v0_4
website_legacy_base_inventory_v0_4_1
website_safe_tracking_policy_v0_4_2
website_config_split_and_secret_policy_v0_4_3
website_database_schema_recovery_v0_4_4
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
Required step details
website_scaffolding_first_safe_commit_v0_4

Purpose:

Create a safe repository checkpoint without broadly committing inherited base/.

Expected outputs:

.gitignore;
README.md;
Makefile;
coordination/status/current_status.md;
v0.3 report;
safe first commit.

Explicit rule:

Do not run `git add base/`.
website_legacy_base_inventory_v0_4_1

Purpose:

Preserve knowledge of inherited PHP base state without committing unsafe runtime/secrets/media/vendor/log/temp content.

Expected outputs:

file inventory of base/;
source/runtime/vendor/media/log/temp classification;
statement that base/ is inherited legacy PHP code;
no secrets committed;
no runtime logs committed;
no production config committed.

The inventory must classify paths into:

source_code
tracked_seed_assets
local_config
runtime_uploads
runtime_logs
generated_files
vendor_dependencies
temporary_scratch
unknown_needs_review
website_safe_tracking_policy_v0_4_2

Purpose:

Define exactly what from base/ may be tracked and what must remain ignored.

Expected outputs:

source_files_to_track
files_to_ignore
files_to_replace_with_examples
runtime_dirs_to_keep_untracked
vendor_policy
userfiles_policy
log_temp_policy
composer_policy

Required rule:

Broad git add base/ remains forbidden until owner/Blueprint explicitly approves the tracking policy.

website_config_split_and_secret_policy_v0_4_3

Purpose:

Make config tracking safe before any broad base/ commit.

Expected outputs:

decide whether base/config.php can be tracked;
create or plan config.example.php;
keep config.local.php ignored;
ensure DB credentials are never committed;
ensure SMTP credentials stay only in mail.local.php;
run grep-based secret scan.

Acceptance:

tracked config files contain fake/example values only;
local config files are ignored;
no real DB/SMTP/API credentials are present in git.
website_database_schema_recovery_v0_4_4

Purpose:

Recover or document the inherited website database schema.

Expected outputs:

confirm MySQL/MariaDB schema source or confirm missing;
create schema-only dump if local DB exists;
no production data dump;
table inventory;
table ownership map;
all local website order/client/product tables marked as legacy_website_local_non_canonical.

Strategic rule:

Website DB tables are channel-local legacy tables only. They are not ForPrint canonical clients, products, orders, stock, payments or accounting.

website_webroot_exposure_hardening_v0_5

Purpose:

Harden public exposure risks.

Expected outputs:

document-root decision;
.htaccess or server config hardening;
direct access blocked for:
config.php
config.local.php
mail.local.php
core/
vendor/
log/
temp/
composer.json
composer.lock
vendor/phpmailer/phpmailer/get_oauth_token.php
suspicious rewrite rule reviewed:
RewriteCond %(REQUEST_FILENAME) !-f

and corrected if needed to:

RewriteCond %{REQUEST_FILENAME} !-f
PHP execution blocked in userfiles/.
website_public_exposure_smoke_tests_v0_5_1

Purpose:

Add small curl-based smoke tests after web-root hardening.

Required checks:

/config.php -> 403 or 404
/core/ -> 403 or 404
/vendor/ -> 403 or 404
/log/ -> 403 or 404
/temp/ -> 403 or 404
/vendor/phpmailer/phpmailer/get_oauth_token.php -> 403 or 404
/userfiles/test.php -> must not execute PHP

Expected outputs:

smoke test script or documented manual command set;
result report;
HTTPS behavior documented;
production error display disabled or flagged.
website_admin_auth_session_lockdown_v0_6

Purpose:

Review and harden admin authentication/session internals.

Expected outputs:

md5 password risk handled or patch plan;
default admin seed reviewed/removed/disabled;
cookie/session flags reviewed;
CSRF posture reviewed;
brute-force behavior reviewed.
website_admin_access_policy_v0_6_1

Purpose:

Define how admin is reachable before deeper auth rewrite.

Policy:

admin disabled publicly by default;
admin only via VPN/internal IP/temporary maintenance window;
no public admin exposure before auth/session/CSRF hardening;
default admin seed removed or disabled before launch.

Expected outputs:

admin route policy;
public admin exposure blocked;
weak legacy auth not internet-facing.
website_upload_safety_lockdown_v0_7

Purpose:

Restrict uploads and media directory risks.

Expected outputs:

upload paths inventory;
extension allowlist decision;
MIME validation decision;
max size recommendation;
randomized filename policy if needed;
PHP execution blocked in upload/media directories;
launch blocker status.
website_sql_user_input_review_v0_8

Purpose:

Map dynamic SQL and request input risk.

Expected outputs:

dynamic SQL map;
user input map;
high-risk query list;
prepared statement / allowlist patch plan;
launch blocker status.
website_launch_mode_restriction_v0_9

Purpose:

Decide which inherited shop features are allowed for first public use.

Expected outputs:

early public mode recommendation;
cart/order/user account disable or hide plan if needed;
clear statement that website data is not canonical ForPrint data.
website_public_launch_profile_v0_9_1

Purpose:

Define the first allowed public launch profile.

Recommended launch profile:

launch_profile:
  mode: lead_capture_only
  enabled:
    - public pages
    - service/product presentation
    - contact information
    - request form
    - local SEO pages
  disabled_or_blocked:
    - admin public access
    - user login
    - cart checkout
    - canonical order creation
    - payment flow
    - stock display
    - accounting flow
    - 1C integration

Acceptance:

first launch mode is explicitly limited;
cart/order/account behavior disabled, hidden, or marked non-canonical;
lead capture does not directly write to ForPrint core modules.
website_dependency_backup_environment_v0_10

Purpose:

Normalize PHP/Composer/runtime/deployment support.

Expected outputs:

PHP version target;
Composer workflow decision;
vendor tracking decision;
backup/restore procedure;
environment documentation;
Makefile/check updates.
website_seo_lead_capture_readiness_v0_11

Purpose:

Prepare local SEO and lead-capture only after security blockers are controlled.

Expected outputs:

contacts/address review;
robots.txt/sitemap decision;
Search Console/analytics checklist;
local landing page checklist;
spam/rate-limit recommendation.
website_limited_public_launch_gate_v0_12

Purpose:

Final explicit launch approval gate.

Expected outputs:

final blocker review;
public launch checklist;
rollback plan;
backup confirmation;
approved launch scope;
explicit owner approval required.
website_future_next_version_planning_v0_13

Purpose:

Plan future clean website implementation beside base/.

Expected outputs:

next/ or modern/ directory decision;
migration strategy;
future Integration Gateway boundary;
Library/Calculator/Operational Registry integration plan.
website_future_gateway_handoff_gate_v0_14

Purpose:

Define future integration gate.

Strategic rule:

Website must not connect directly to Operational Registry, Calculator Engine, Library, Accounting Registry or 1C.

Future flow must be:

Website request -> Integration Gateway -> approved downstream module

Acceptance for future integration:

Gateway contract approved;
idempotency/correlation defined;
website request payload is channel-level;
no direct canonical writes from website.
Add legacy risk register

Create or update a risk register for the website module.

Preferred path:

coordination/risk_registers/website.yaml

If the Blueprint already has another risk-register location or standard, follow the existing standard instead.

Use a simple YAML structure if no existing schema exists.

Required fields per risk:

risk_id:
area:
severity:
current_status:
launch_blocker: true
mitigation:
owner_module:
target_step:

Initial risks must include:

hardcoded/local config risk;
dynamic SQL risk;
md5 password risk;
upload execution risk;
public web-root exposure risk;
inherited vendor exposure risk;
local order/client/product table ownership confusion risk;
missing DB schema risk;
missing backup/restore procedure risk;
public admin exposure risk;
secret/config tracking risk.
Documentation update

Update relevant status/report files if they exist.

At minimum, ensure the roadmap points to current v0.1/v0.2/v0.3 reports and marks v0.3 completed.

Do not edit PHP website code in this Blueprint prompt.

Checks

Run:

make roadmap-dashboard MODULE=website
make check
git diff --check

If make check fails because of an unrelated telegram_bot prompt index issue, do not hide it.

Report:

the website roadmap validation result;
the unrelated failure;
exact failing file/check;
whether the website roadmap itself is valid.
Completion report

Create a short Blueprint completion report:

coordination/reports/completion/2026-07-07__blueprint__website_roadmap_legacy_control_refinement_v0_2_1.md

The report must include:

roadmap changes;
risk register changes;
new steps added;
current website step;
dashboard result;
check result;
known unrelated blockers;
next recommended Website prompt.
Non-goals

Do not edit /srv/software_development/forprint-project/forprint_website/base.

Do not deploy.

Do not connect production services.

Do not commit secrets.

Do not approve broad git add base/.

Do not make website canonical owner of clients, products, orders, payments, stock, accounting or 1C data.

Do not bypass Integration Gateway in future integration planning.

Expected final state

At the end:

website roadmap is refined and visible in the module roadmap dashboard;
v0.3 is marked completed;
v0.4+ path is explicit and conservative;
legacy base inventory/tracking/config/schema steps exist;
launch profile and exposure smoke tests are planned;
risk register exists;
public launch remains blocked until launch gate approval.
