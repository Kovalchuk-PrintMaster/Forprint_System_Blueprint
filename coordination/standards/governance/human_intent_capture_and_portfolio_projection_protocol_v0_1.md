# Human Intent Capture and Portfolio Projection Protocol v0.1

Status: active standard  
Adoption mode: gradual alignment  
Authority: governance process standard, not release authority

## Purpose

Preserve the human meaning of architecture and roadmap discussions so that technical normalization does not collapse dozens of concrete agreements into a few generic machine-oriented summaries.

## Required artifacts after a substantial architecture / evening review

The review is incomplete until all five outputs exist:

1. technical integration package or documented no-code decision;
2. Human Intent Delta grouped by module;
3. append-only human-intent ledger updates;
4. regenerated expanded human portfolio projection;
5. explicit unresolved GAP list.

## Entry contract

Each durable human-intent entry should provide:

- `intent_id`;
- `status`;
- `text` in short human language;
- `context`;
- related module;
- optional roadmap step reference;
- optional supersedes link;
- provenance / source note when available.

Statuses:

- `AGREED`;
- `RECOVERED`;
- `PROPOSED`;
- `GAP`.

## No silent loss

A generator must not reduce many active human-intent entries to one generic paragraph and then omit the entries from the expanded portfolio.

The expanded human portfolio must retain every active/relevant entry. It may paginate or group them, but it may not silently discard them.

## Supersession

Old human intent is not deleted merely because a newer decision exists.

A later entry may supersede an older entry. Both remain reconstructible.

## Exact resources and examples

If a conversation names a specific website, application, reference implementation, URL, physical example, formula, or measurement method, capture it explicitly when available.

If the exact detail cannot be recovered, create a `GAP` entry. Never invent a substitute and present it as the original agreement.

## Roadmap traceability

Roadmap steps should include `human_intent_refs` when human discussion materially defines design intent.

Target traceability:

business need -> human intent -> capability / architecture decision -> roadmap step -> contract / implementation -> evidence.

## Three portfolio projections

1. Narrow machine view: optimized for agent bootstrap and links to canonical project knowledge.
2. Balanced technical view: concise module capability / roadmap / dependency summary.
3. Expanded human view: Ukrainian human-language intent chain with all active/relevant intent entries.

Only the underlying structured project surfaces can be authority. Portfolio PDFs are review projections.

## Validation expectations

Repository checks should verify at minimum:

- unique intent IDs;
- referenced module IDs are known or explicitly proposed;
- no empty text;
- all module ledger files are indexed;
- expanded portfolio generation does not silently drop active intent IDs.

## Protected boundaries

This protocol does not by itself:

- change current release authority;
- enable autonomous business decisions;
- rewrite released prompts;
- activate proposed modules;
- authorize cross-repository writes;
- authorize commit or push.
