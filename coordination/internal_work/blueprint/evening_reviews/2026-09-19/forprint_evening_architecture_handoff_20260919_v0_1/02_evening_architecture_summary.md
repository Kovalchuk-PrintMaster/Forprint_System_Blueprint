# Evening Architecture Summary

## Telegram Bot mission

Telegram Bot is a **personalized communication orchestration layer**.

It should:
- receive human messages and normalize/route them;
- preserve conversation state;
- maintain communication preferences;
- render structured domain facts as natural context-aware communication;
- ask clarifying questions;
- route structured answers back to the responsible domain.

It should **not** own:
- pricing truth;
- financial calculations;
- credit decisions;
- logistics truth;
- production truth;
- historical asset storage;
- customer economic analytics;
- durable fulfilment workflow state.

Core principle:

> Business modules determine **what is true / what must happen**.  
> Telegram Bot determines **how to communicate it naturally and contextually**.

## Communication Intent

Domain modules should ideally emit structured communication intents rather than pre-written customer prose.

Telegram Bot combines that intent with:
- conversation context;
- communication profile;
- preferred language;
- formality;
- preferred name/addressing;
- verbosity;
- sentiment/context;
- previous messages.

It must not alter factual values such as price, deadline, delivery status or guarantee.

## Customer-specific understanding

The system should learn **how each individual customer communicates and behaves**:
- customer-specific terminology;
- recurring order patterns;
- exceptions;
- corrections;
- preferred communication style;
- typical ambiguity;
- typical response latency;
- historical production patterns.

Customer-specific semantics must not silently become global semantics.

## Baseline, exception and pattern shift

Preference learning should distinguish:
- `BASELINE`
- `EXCEPTION`
- `POSSIBLE_SHIFT`
- `PROBABLE_SHIFT`
- `NEW_BASELINE`

A single exceptional order must not silently redefine a stable preference.

A persistent recent pattern must be able to supersede a large stale historical pattern without requiring lifetime numerical majority.

Concepts to evaluate later:
- recency weighting;
- recent-window analysis;
- drift/change detection;
- minimum evidence;
- hysteresis;
- contextual segmentation;
- provenance/audit.

## Customer profile architecture

Suggested logical layers:

### Seed Profile
Chosen quickly by a manager using a small set of simple presets/buttons.

### Observed Customer Model
Machine-derived evidence from real interactions and transactions.

### Effective Policy
The currently allowed handling rules for this customer.

Also separate:
- descriptive knowledge;
- preferences;
- control policy.

## Profile maturity and coverage

Profile quality should depend on evidence, not only elapsed time.

Possible evidence:
- confirmed orders;
- confirmed corrections;
- distinct product families;
- clarification outcomes;
- payment outcomes;
- delivery outcomes;
- repeated patterns.

Coverage can be domain-specific.

## Continuous customer movement

Customers and ForPrint both change over time.

Support continuously updated customer state/trajectory rather than quarterly/static categories.

Potential dimensions:
- payment health;
- commercial value;
- growth momentum;
- margin quality;
- service burden;
- order clarity;
- dispute risk;
- relationship stability;
- strategic potential.

Prefer event-driven reaction plus periodic reconciliation.

## Historical Asset Index

Existing client file archives are raw material, not a runtime search surface for Telegram Bot.

A worker/pipeline should preprocess historical assets into a searchable machine-readable index.

Potential metadata:
- customer_id;
- order_id;
- asset_id;
- archive reference/path;
- original filename;
- type/size;
- page count;
- dimensions;
- color/resolution;
- exact hash;
- visual fingerprint;
- OCR/text signature;
- semantic descriptors;
- representative page fingerprints;
- revision family;
- production recipe links;
- printed/approved/superseded status.

Runtime search:
1. cheap candidate retrieval from the index;
2. deep comparison only for a small candidate set;
3. if multiple candidates remain, show them to the customer for explicit selection.

## Revision families

Similar files should be able to form revision families:

```text
BOOK-041
├── R01
├── R02
└── R03
```

Useful status:
- draft;
- printed;
- customer_rejected;
- customer_approved;
- superseded.

## Clarification workspace

For ambiguous or multi-file orders, avoid endless Telegram message chains.

Possible modes:
- short high-confidence confirmation;
- editable single-item card;
- batch/grouping workspace;
- explicit unresolved group.

The UI should call canonical services such as Library/Calculator rather than implement pricing/product truth itself.

Final output should be a structured `Order Draft`, not free text.

## AI position

AI is a fallback/helper, not primary authority.

Preferred sequence:

```text
rules
→ history
→ classifiers
→ customer model
→ clarification
→ AI helper
→ human
```

Escalation should be driven by unresolved ambiguity / lack of progress / contradictory evidence, not only a fixed retry count.

## Long-running Process Manager

Long fulfilment chains are not a Telegram responsibility.

A durable business Process Manager should own:
- process state;
- current step;
- waiting condition;
- timers;
- deadlines;
- retries;
- escalations;
- expected events;
- process transitions;
- operator-attention conditions.

Telegram Bot is a communication participant.

## Hosted / incubated capability

Do not create a standalone Process Manager module yet.

First locate the best existing host.

The capability should be independently extractable:
- own namespace;
- own contracts;
- own state model;
- own tests;
- explicit adapters/ports;
- minimal direct host internals;
- explicit extraction readiness.
