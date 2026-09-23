# Verification & Adversarial Testing Policy v0.1

Status: PROPOSED

## Independent purpose

Verification Lab is separate from:
- Project Inspector, which audits architecture/governance/conformance;
- Runtime Inspector, which observes actual execution;
- domain modules, which own business behavior.

Verification Lab intentionally generates scenarios intended to expose incorrect behavior.

## Test modes

### BLACK BOX
Tester sees only what a realistic actor/channel could know.

Purpose:
- unbiased external behavior;
- authorization/security boundary;
- realistic language/input behavior.

### GRAY BOX
Tester sees declared contracts/capabilities and expected invariants.

Purpose:
- contract/business-rule coverage;
- systematic combinatorial generation.

### WHITE BOX
Read-only diagnosis using code/contracts/traces.

Purpose:
- explain failure;
- create minimal reproducible case;
- identify missing deterministic test.

## Test taxonomy

- normal/valid;
- invalid;
- boundary;
- malformed;
- combinatorial;
- multilingual;
- out-of-domain/noise;
- authorization;
- data isolation;
- prompt/adversarial;
- tool misuse;
- state-machine;
- concurrency;
- duplicate/replay/idempotency;
- fault injection;
- provider outage;
- recovery;
- stale cache;
- schema/contract fuzz;
- performance/load/soak;
- AI routing;
- token/cost regression.

## Test Plane rule

Default:
`NO_LIVE_EXTERNAL_SIDE_EFFECTS`

Use:
- fake taxi;
- fake payment;
- fake printer;
- fake email/SMS;
- fake cloud;
- synthetic Telegram events;
- test DB/filesystem.

Provider sandbox/live canary requires explicit separate policy.

## Regression learning loop

`AI exploratory case → interesting failure → owner/contract confirmation → deterministic regression test`

Verification Lab may propose a test candidate.
It may not unilaterally turn an invented business assumption into canonical truth.

## Trace-aware evaluation

Do not evaluate only final text.

Capture:
- ingress classification;
- routing path;
- deterministic handlers;
- AI calls;
- tool calls;
- owner lookups;
- policy decisions;
- external adapter requests;
- retries;
- latency;
- tokens/cost;
- result.

A correct-looking answer reached through an unsafe path may still be a failure.

## Campaigns

Support:
- CHANGE_TRIGGERED
- DAILY/NIGHTLY
- WEEKLY_DEEP
- MANUAL_CAMPAIGN
- PRE_RELEASE
- POST_RELEASE_CANARY

Dependency graph should select relevant suites instead of always running the entire corpus.

## Example Calculator adversarial classes

For a business-card capability:
- valid paper combinations;
- incompatible roll/banner material;
- unsupported duplex/4+4 for one-sided media;
- zero/negative/huge quantity;
- missing/ambiguous material;
- stale material ID;
- invalid color mode;
- duplicate quote/order submission;
- inconsistent dimensions;
- unexpected language/encoding.

Expected behavior must come from approved product/material capability truth.

## Example Telegram campaign

Measure:
- correct language response;
- in-domain vs out-of-domain classification;
- deterministic resolution rate;
- AI escalation rate;
- unsafe action attempts;
- authorization failures;
- unnecessary tool calls;
- cost per resolved request.

## Security boundary

The Lab must not receive production mutation credentials merely because its job is adversarial.

Adversarial power belongs inside Test Plane.
