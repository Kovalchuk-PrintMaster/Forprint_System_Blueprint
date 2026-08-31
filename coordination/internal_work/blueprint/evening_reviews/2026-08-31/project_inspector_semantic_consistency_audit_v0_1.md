# Project Inspector Semantic Consistency Audit v0.1

Status: agreed target capability
Module: forprint_project_inspector
Date: 2026-08-31

## Decision

Do not create a separate ForPrint semantic-audit module.

Semantic consistency becomes an independent capability/worker inside ForPrint Project Inspector.
The Inspector remains an observer/auditor and does not become semantic owner of audited domains.

## Change boundary

Incremental inspection must compare the last inspected Git checkpoint/commit with the current
target commit. `git status` alone is insufficient because already committed daytime changes
would disappear from the working-tree view.

## Two audit layers

### Deterministic layer

Use scripts whenever a claim can be proven mechanically:

- repository/schema structure;
- standards/revision registration;
- contract versions;
- indexes;
- tests/checks;
- required evidence;
- known authority/adoption metadata;
- declared new entity/token availability.

Deterministic checks should be frequent and cheap.

### Semantic LLM layer

When changed content contains interpretive/business/policy/legal/customer-facing semantics,
Inspector builds a bounded context package for an LLM worker.

Package inputs may include:

- changed documents/diff;
- relevant module charter/roadmap;
- applicable standards;
- canonical authority documents;
- contracts;
- Human Intent;
- dependency context;
- cross-module invariants;
- explicit review questions.

The LLM may ask Inspector for additional bounded context. It must not invent missing authority.

## Risk-based triggers

Do not decide semantic review from diff size alone. A one-line policy change can be high impact.

Suggested semantic risk classes include:

- POLICY_CHANGE;
- BUSINESS_RULE_CHANGE;
- CONTRACT_CHANGE;
- CUSTOMER_FACING_TEXT;
- LEGAL_OR_COMPLIANCE;
- IDENTITY_CHANGE;
- PAYMENT_CHANGE;
- PRODUCTION_SAFETY_CHANGE;
- CROSS_MODULE_AUTHORITY_CHANGE;
- HUMAN_INTENT_CHANGE.

Low-risk code-only/refactor changes may stop after deterministic verification when the contract
surface demonstrably did not change.

## Periodic sweep

In addition to event-driven incremental review, run a wider cross-module semantic sweep.

Initial cadence target: approximately monthly while the architecture changes quickly.

With increasing maturity and lower architectural change rate, cadence may move toward quarterly
and later semiannual review. High-risk event-driven checks remain active regardless of maturity.

## Finding taxonomy

Semantic audit should be able to report at least:

- SEMANTIC_CONTRADICTION;
- AMBIGUOUS_RULE;
- OWNERSHIP_VIOLATION;
- CONTRACT_DIVERGENCE;
- TERM_DRIFT;
- STALE_AUTHORITY_REFERENCE;
- HUMAN_INTENT_DIVERGENCE;
- HIDDEN_DEFAULT;
- ORPHAN_RULE;
- CROSS_MODULE_BEHAVIOR_CONFLICT.

Findings should contain severity, confidence, evidence, affected modules and recommended owner.

## Legal boundary

LLM review may perform issue spotting, internal-policy comparison, missing-clause detection and
comparison against supplied legal requirements.

It must not label a material legal question `LEGAL_COMPLIANCE_CONFIRMED` merely from model
analysis. Material legal certainty remains a human/legal-review boundary.

## Decision boundary

Inspector and its LLM worker may:

DETECT → VERIFY → COMPARE → CLASSIFY → REPORT → ROUTE.

They may not:

- invent a business rule;
- change semantic authority;
- accept/reject a domain decision;
- silently rewrite another module's semantics.

A potential defect in an authority document is reported as a finding against that owner rather
than silently "fixed" by Inspector.

## Future cross-module invariant registry

Blueprint should later formalize a machine-readable registry of cross-module invariants, for
example:

- phone is not immutable person identity;
- QR is identifier, not permission;
- filename is projection, not source of truth;
- search finds candidates; domain owner decides truth;
- actual data does not silently rewrite norms;
- breaking contract revisions require adoption before activation.

Inspector consumes these invariants; it does not own their domain semantics.
