# Prompt: ForPrint Integration Gateway v0.6 — Contract Release Package, Consumer Acceptance Fixtures, and Backward Compatibility Gates

Generated: `__2026-06-12T16:00:59.641525+00:00__`

## Target module

`forprint_integration_gateway`

## Source

This prompt is issued by `forprint_system_blueprint`.

Read it through:

```bash
make blueprint-prompts-list
make blueprint-prompt
```
Purpose

Gateway v0.6 must turn the existing Gateway contract foundation into a structured contract release package that other modules can consume safely.

Gateway v0.3 created channel intake and handoff contracts.

Gateway v0.4 added adapter contracts, delivery policy, runtime status and error taxonomy.

Gateway v0.5 added compatibility matrix, replay fixtures and dry-run delivery planner.

Gateway v0.6 must package these into stable release artifacts with consumer acceptance fixtures and backward compatibility gates.

This checkpoint is still offline / dry-run / contract-only.

Do not enable live runtime delivery.

Accepted baseline

Gateway accepted baseline:

3a97012 Add Gateway adapter contracts and error taxonomy
3f51c41 Add Gateway v0.4 coordination report
1a7ed1d Add Gateway contract compatibility and replay dry-run
6e8626f Add Gateway v0.5 coordination report

Expected baseline:

make governance-check passes;
make check passes;
make check-report passes;
make channel-intake-preview passes;
make adapter-readiness-preview passes;
make compatibility-matrix-preview passes;
make replay-fixtures-preview passes;
no non-canonical module ids in source-controlled text files;
Gateway remains offline / contract-only.
Main goal

Create Gateway v0.6 foundations for:

contract release package;
consumer-specific contract bundles;
consumer acceptance fixtures;
backward compatibility gates;
contract deprecation policy;
contract changelog;
contract release manifest;
schema/descriptor consistency checks;
consumer acceptance preview;
contract release preview;
check-report integration;
updated coordination records and completion report.
Required contract release package

Add a stable release directory, for example:

contracts/gateway/v0_6/

or another existing project-consistent path.

The release package should include machine-readable and human-readable contract artifacts for:

channel_intake
adapter_contracts
error_taxonomy
delivery_policy
compatibility_matrix
dry_run_delivery_planner
replay_fixtures
consumer_acceptance

Keep artifacts offline.

No runtime transport.

No generated client SDK yet.

Required release manifest

Add a machine-readable release manifest, for example:

contracts/gateway/v0_6/release_manifest.yaml

It must include:

release id;
release version;
Gateway module id;
source commits;
supported consumer modules;
supported producer modules;
artifact list;
compatibility baseline;
boundary confirmation;
live delivery enabled false;
generated_at or updated_at;
contract status.

Supported consumer modules must include:

forprint_crm
forprint_operational_registry
calculator_engine
forprint_prepress_hub
forprint_accounting_registry
telegram_bot
website
mobile_app

Use canonical module ids only.

Forbidden non-canonical id:

forprint_calculator_engine
Required consumer-specific bundles

Create contract bundles for:

CRM bundle

Purpose:

order intake from Telegram/Website;
operator-facing workflow handoff;
client lookup requests;
no ownership of all operational truth.
Operational Registry bundle

Purpose:

client lookup candidates;
order handoff candidates;
operational truth ownership;
dry-run candidate acceptance only.
Calculator Engine bundle

Purpose:

quote preview request contracts;
no final price calculation inside Gateway;
calculator remains pricing owner.
Prepress Hub bundle

Purpose:

file/prepress job candidate contracts;
future Mobile App file request scenario;
no real file transfer.
Accounting Registry bundle

Purpose:

accounting reference candidate only;
no posting;
no 1C writes;
no automatic accounting mutation.
Telegram Bot bundle

Purpose:

channel intake producer contract;
no live Telegram API call from Gateway.
Website bundle

Purpose:

website form intake producer contract;
no live Website runtime call from Gateway.
Mobile App bundle

Purpose:

planned/future only;
must remain non-active runtime.
Required consumer acceptance fixtures

For every consumer bundle, add at least one acceptance fixture.

Fixtures must specify:

fixture id;
consumer module;
producer/source flow;
expected contract version;
expected compatibility state;
expected dry-run plan status;
required fields;
forbidden fields;
live enabled false;
expected boundary status.

Required acceptance fixture coverage:

CRM accepts order intake contract
Operational Registry accepts order handoff candidate contract
Operational Registry accepts client lookup candidate contract
Calculator accepts quote preview dry-run contract
Prepress accepts future prepress job candidate contract
Accounting rejects posting/write attempts
Telegram producer fixture is accepted as channel intake
Website producer fixture is accepted as channel intake
Mobile App fixture remains planned_future
Required backward compatibility gates

Add a compatibility gate that checks v0.6 does not break accepted v0.3/v0.4/v0.5 concepts.

The gate must verify:

v0.3 channel intake examples still pass;
v0.4 adapter readiness still passes;
v0.5 compatibility matrix still passes;
v0.5 replay fixtures still pass;
existing route target module ids remain canonical;
no live delivery is enabled;
Accounting/1C/posting are blocked;
Mobile App remains future/planned.
Required deprecation policy

Add a document, for example:

docs/architecture/contract_deprecation_policy_v0_6.md

It must define:

when a contract can be deprecated;
how long old fixtures must stay readable;
how compatibility gates catch breaking changes;
how Blueprint approval is required for breaking changes;
how modules should report incompatible contract versions.
Required changelog

Add contract release changelog:

contracts/gateway/v0_6/changelog.md

It should summarize:

what was introduced in v0.3;
what was introduced in v0.4;
what was introduced in v0.5;
what v0.6 packages for consumers;
known non-live limitations;
next allowed evolution.
Required preview targets

Add:

make contract-release-preview
make consumer-acceptance-preview
make backward-compatibility-preview

contract-release-preview should show:

release id;
artifact count;
consumer bundles;
producer bundles;
live enabled false;
boundary status.

consumer-acceptance-preview should show:

consumer module;
fixture id;
expected result;
actual result;
compatibility state;
boundary status.

backward-compatibility-preview should show:

previous layer;
compatibility status;
protected concept;
result.
Required check-report integration

Extend make check-report so it validates:

release manifest exists and is valid;
consumer bundles exist;
consumer acceptance fixtures exist and pass;
backward compatibility gates pass;
v0.3/v0.4/v0.5 previews still pass;
no live delivery is enabled;
Accounting Registry cannot post or write to 1C;
Mobile App remains planned/future;
no queues/Redis/S3/DB ownership are introduced;
no non-canonical module ids exist in source-controlled text files;
coordination records remain machine-clean.
Cache hygiene

The canonical module id guard must ignore generated binary/cache files:

__pycache__
*.pyc
.pytest_cache

But source-controlled text files must still be checked strictly.

Required docs

Add architecture docs, for example:

docs/architecture/contract_release_package_v0_6.md
docs/architecture/consumer_acceptance_fixtures_v0_6.md
docs/architecture/backward_compatibility_gates_v0_6.md
docs/architecture/contract_deprecation_policy_v0_6.md

Use existing structure where possible.

Required coordination update

Update:

coordination/status/current_status.yaml
coordination/prompts/index.yaml
coordination/reports/index.yaml
coordination/status/next_questions_for_blueprint.md

Expected phase:

contract_release_consumer_acceptance_v0_6

Expected completed step:

gateway_contract_release_ready

Add completion report under:

coordination/reports/

The report must be tracked even if coordination/reports is ignored.

Use:

git add -f coordination/reports/index.yaml coordination/reports/<report-file>.md
Required validation before commit

Run:

find app tests scripts examples docs coordination reports contracts -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +

make governance-check
make check
make check-report
make channel-intake-preview
make adapter-readiness-preview
make compatibility-matrix-preview
make replay-fixtures-preview
make contract-release-preview
make consumer-acceptance-preview
make backward-compatibility-preview

grep -R --exclude-dir="__pycache__" --exclude="*.pyc" "forprint_calculator_engine" -n app tests scripts examples docs coordination reports contracts || true

git ls-files coordination/reports/index.yaml
git status --short

Expected:

all checks OK;
pytest passes;
channel intake preview OK;
adapter readiness preview OK;
compatibility matrix preview OK;
replay fixtures preview OK;
contract release preview OK;
consumer acceptance preview OK;
backward compatibility preview OK;
grep returns nothing from source-controlled text;
coordination reports index is tracked;
no live integration introduced.
Commit expectation

After checks are green:

git commit -m "Add Gateway contract release and consumer acceptance"
git push

Use staged commits if needed.

Boundary

Do not implement:

live API;
database;
queues;
Redis;
S3;
Telegram runtime calls;
Website runtime calls;
CRM runtime calls;
Operational Registry runtime calls;
Calculator runtime calls;
Library runtime calls;
Prepress runtime calls;
Accounting runtime calls;
1C writes;
automatic posting;
final price calculation;
generated production SDKs.

Gateway remains a validation, normalization, routing, idempotency, correlation, audit, adapter-contract, compatibility, replay, dry-run planning and contract-release boundary.
