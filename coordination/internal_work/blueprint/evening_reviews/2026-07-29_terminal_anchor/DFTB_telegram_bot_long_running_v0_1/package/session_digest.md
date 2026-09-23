# Session Digest — Telegram behavior model → runtime → governance closeout

## Source identity

This is a unique long-running Telegram module dialogue.

It is **not** the same source as the short `Telegram_bot_12.10.26` conversational-template/CSV dialogue.

The filename label `13.10.26` is impossible relative to the 15.09.2026 export. The terminal historical anchor is a **2026-07-29** governance completion packet.

## Early behavior architecture

The dialogue begins with a behavior-model approach:
- classify intent;
- select/use templates;
- generate human response;
- collect feedback;
- escalate low-confidence cases.

Historical assistant summary includes Mentor/AI escalation with conversation/order context, user transparency and logging.

The early stack mentions:
- Supabase;
- DeBERTa;
- Mistral.

These are historical dependencies, not current runtime authority.

## Qualification and delivery

The behavior registry expects the bot to enrich missing client information conversationally.

Examples include:
- phone;
- business/activity/product interests;
- preferred delivery method.

Important current interpretation:
Telegram can collect/communicate these facts, but it must not become canonical CRM/Operational Registry owner.

The early registry also goes too far toward delivery/provider execution. Later architecture gives shipment/provider execution to Logistics Service.

## Operator behavior registry

The owner requires the behavior registry to be easy to inspect:
- thematic blocks;
- light color coding;
- Excel for desktop editing;
- HTML for mobile reading.

Historical workbook iterations add:
- block/status dashboards;
- KPI schema;
- integrity/duplicate checks;
- technical notes;
- changelog.

These are useful design/operator projections, not automatically runtime truth.

## First major development correction

Implementation drifts into classifiers, template lookups, smoke tests and tooling.

The owner notices this and explicitly corrects the sequence:

**stage one = behavior-model table/scheme**  
**stage two = real classifier/runtime implementation**

Synthetic phrases should exercise the predefined behavior schemes, not become the source of architecture.

This is one of the strongest process decisions in the dialogue.

## Path/config discipline

Historical work suffers from references to nonexistent directories/scripts.

Owner then requires:
- move slowly;
- use real repository structure;
- correct package imports;
- consistent script metadata;
- no hard-coded paths/constants;
- settings through `config.py`, `.env` and explicit configuration.

## Wizard architecture

The behavior simulation evolves toward scenario-specific flows.

Owner rejects one enormous wizard and prefers:
- `head_wizard` dispatcher;
- ORDER runner;
- VENDORS runner;
- future scenario runners.

A historical ORDER flow successfully loads **113 nodes**.

VENDORS development shows real defects:
- SyntaxError;
- CLI argument mismatch;
- other interface/debug issues.

These failures are preserved as evidence, not cleaned out of history.

## Behavior artifacts vs production runtime

Later the owner makes another key boundary explicit:

the XLS/wizards under development/testing are for **describing and exercising behavior**.

The actual bot `app` should be real code using the project runtime/database and should no longer depend on XLS as its execution substrate.

This cleanly separates:
- specification/simulation;
- production runtime.

## Runtime modularity and code standard

Owner asks for domain/scenario folders such as delivery/vendors and a strong code-documentation standard:
- file name/purpose/result;
- inbound/outbound dependencies;
- paths;
- constants/variables;
- function explanations;
- terminal/log observability.

## Git and governance

Owner decides to connect GitHub so code is not stored in only one place.

Later Telegram adopts project-wide governance:
- canonical Make target contract;
- Blueprint prompt reading;
- rolling status;
- module-local completion/status writes;
- Blueprint-side acceptance.

## Governance baseline adoption

Historical prompt:
`telegram_bot_governance_baseline_adoption_v0_1`

runs on:
`feature/telegram-governance-baseline-adoption-v01`

The owner also explicitly retires `NO_COLOR=1`.

## External Blueprint blocker

During closeout, `blueprint-pull` cannot run because the Blueprint branch has no upstream.

Correct historical handling:
- do not modify Blueprint repo;
- do not repair its upstream from Telegram;
- classify `blueprint_pull` as **DEFERRED**;
- keep read-only/current module checks running;
- avoid both false green and false Telegram failure.

This is an important cross-module governance pattern.

## Historical final checkpoint

Terminal output creates and pushes:

`dcd2b01 docs: add governance baseline completion packet`

Branch:
`feature/telegram-governance-baseline-adoption-v01`

Remote divergence after push:
`0 0`.

Final historical report says:
- completion-packet apply is idempotent;
- governance/module/contract/packet validation passes;
- optional lint/format tools and blueprint pull remain documented warnings/deferred items;
- generated reports are not committed;
- no dialogue/business/runtime/provider/production behavior was changed;
- no Blueprint repo writes occurred.

Result:

**READY_FOR_BLUEPRINT_REVIEW**

Explicitly **not** `accepted_by_blueprint`.

## Current reconciliation required

Before any Telegram execution:
1. resolve current Blueprint release;
2. resolve current Telegram repo/branch/HEAD and fate of `dcd2b01`;
3. verify current CRM/client ownership contracts;
4. verify Logistics handoff for delivery;
5. classify behavior registry/wizards as spec/test/runtime;
6. verify current AI/model/privacy/escalation policy;
7. run current governance/coordination gates instead of trusting historical PASS.
