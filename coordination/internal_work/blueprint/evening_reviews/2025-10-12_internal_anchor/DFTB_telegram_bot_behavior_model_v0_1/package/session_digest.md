# Session Digest — Telegram behavior model, AI escalation and recurring ML evaluation

## Source identity and duplicate handling

This is a new Telegram history root, not a re-export.

It shares some literal text with the later long-running Telegram source because **turn 1 contains a pasted/embedded earlier conversation and scaffold**. Shared message IDs are zero and sequence similarity is negligible.

That embedded material is preserved as secondary provenance and is not double-counted as fresh owner acceptance.

## Chronology

The filename says `12.10.26`, but the MHTML was exported in September 2026.

Inside the embedded scaffold:
`updated: "2025-10-12"`.

This provides a strong internal anchor for a **12 October 2025 behavior-model phase**.

It precedes the separately recovered Telegram ML engineering root internally dated 14–25 October 2025.

## Behavior-model-first direction

The owner asks to start from a behavior-model scaffold and then add concrete behavior criteria.

The stable objective is not a dry FAQ bot. It should behave like an attentive human manager and cover likely behavior modes beyond only the examples explicitly supplied.

## Voice/chat synchronization as project-memory problem

The conversation repeatedly demonstrates a product/process problem:
voice instructions are not reliably reflected back in text.

The owner defines a precise reporting rule:
- after a voice conversation, provide a compact text summary/checklist;
- summarize **only the latest exact voice dialogue**;
- do not merge several hours of previous voice conversations.

This is historical UX/process evidence for durable project memory and operator handoff.

## Order dialogue detail

One concrete behavior requirement:
the bot must not confuse quantity/packaging semantics.

Example:
distinguish one pack/unit from a larger package containing multiple packs and ask clarifying questions rather than assume.

## Ambiguity escalation

A major owner requirement:

When Telegram cannot make a correct, unambiguous decision, it should not bluff.

Historical escalation paths:
1. Mentor/human helper;
2. AI assistant.

The helper should receive sufficient context:
- conversation;
- order context;
- approved relevant data.

Current implementation must add least-privilege/privacy/approval boundaries around that context.

## Deterministic bot vs AI layer

The owner develops a useful architectural distinction:

**deterministic bot logic** handles known procedures and explicit rules;  
**AI** is invoked for analysis, ambiguity or cases not safely covered by deterministic behavior.

This is stronger than “AI answers everything”.

## Tool-enabled personal assistant

The owner also explores a broader Telegram assistant role:
- check email;
- summarize correspondence;
- draft/respond under defined rules;
- manipulate files;
- use AI when routine logic is insufficient.

This is an automation ambition, not blanket authority.

Current system needs explicit tool permissions, credential boundaries, audit and approval levels.

## 1C automation

The owner wants routine 1C/accounting tasks automated, e.g. order creation or material operations.

The assistant historically suggests API/library integration.

Later ForPrint architecture is stronger:
Telegram should not own accounting truth or direct unrestricted 1C writes.

Current path must be:
Telegram/operator intent → governed contract → Accounting/1C adapter → result/audit.

## Repository-memory failure

A long late segment shows the assistant repeatedly claiming it can find the previously supplied bot skeleton/file structure, while failing to name the file and eventually admitting that it cannot directly retrieve the history.

This is valuable negative evidence:
**chat memory is not repository knowledge**.

Project structure, current authority and file identity must come from durable artifacts/indexes/live repo.

## Three-layer historical Telegram stack

Owner summarizes the design as:
1. **DeBERTa** — classify intent/style/sentiment;
2. **Mistral** — richer dialogue generation;
3. **AI assistant** — difficult ambiguous decisions.

This is historical architecture and must still be reconciled with the live implementation.

## Sales behavior

The bot-manager should have sales skills, not only accept requests.

Owner wants semantics for:
- sales opportunity;
- refusal;
- objection handling;
- suggesting an offer/service.

These semantics should drive downstream behavior rather than be mixed into one unstructured phrase pool.

## Modular training datasets

Owner rejects one giant training table.

Preferred historical direction:
specialized datasets/tables for domains such as:
- general client dialogues;
- sales;
- objections;
- order handling;
- other weak/problem domains.

Training can combine these sets while each domain remains maintainable independently.

When one domain performs badly, improve that dataset rather than rewriting unrelated data.

## Recurring ML evaluation

Owner asks for professional automated recurring quality checks:
- periodic evaluation;
- error reports;
- identify confused intents/domains;
- retrain when quality falls below a threshold.

## Test-set memorization risk

The owner correctly identifies a major ML-governance problem:

If the same evaluation dataset is repeatedly used and leaks into tuning/training decisions, the model can simply adapt to that set while true generalization stagnates.

Therefore a static recurring test set is not sufficient long-term evidence.

## Fresh evaluation cases

Owner prefers fresh, unseen evaluation examples and rejects simple rotation-only sets as the preferred autonomous strategy.

Historical assistant suggestion:
use an external LLM/API to generate fresh test queries on a schedule.

Important current refinement:
fresh prompts alone are insufficient.

A professional evaluation pipeline also needs:
- expected labels / evaluation oracle;
- provenance;
- hidden holdout policy;
- leakage checks;
- versioned test pools;
- promotion/retraining thresholds.

## Current reconciliation priorities

This source strengthens existing Telegram audits around:
- behavior source of truth;
- voice/project-memory continuity;
- AI/Mentor escalation;
- tool permissions;
- Accounting/1C integration;
- sales taxonomy;
- modular ML datasets;
- recurring evaluation/oracle design.

No historical PASS, provider claim or embedded scaffold is current implementation proof.
