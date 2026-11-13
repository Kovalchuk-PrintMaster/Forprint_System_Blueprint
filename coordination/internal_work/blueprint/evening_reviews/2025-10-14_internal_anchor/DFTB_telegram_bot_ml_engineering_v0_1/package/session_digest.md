# Session Digest — Telegram DeBERTa ML engineering, October 2025

## Chronology

The filename `14.10.26` is not reliable.

The MHTML was exported on 15.09.2026, while the source itself contains:
- `confusion_matrix_2025-10-14_07-51.json`;
- `train_style_log_2025-10-14_11-30.json`;
- WSL/systemd boot evidence dated 2025-10-25.

This root is therefore treated as an **October 2025 Telegram ML/refactor phase**.

## Main technical focus

This is not primarily a bot-business-flow dialogue.

It is a technical engineering phase around:
- DeBERTa intent/style/sentiment classifiers;
- training datasets and label maps;
- train/classify/evaluate scripts;
- model revision archives;
- configuration/path standardization;
- evaluation/report readability;
- code/file documentation standards.

## Model quality

Owner reports a style classifier accuracy of **0.6394** and does not consider it good enough.

Historical work then focuses on:
- dataset review;
- conflicts/duplicates;
- class balance;
- train/validation/test split;
- confusion/evaluation reports;
- sentiment dataset gaps.

No historical metric is promoted to current model quality.

## Strong owner script standard

The most reusable contribution is the owner's file/script standard.

Important scripts should explain themselves:
- launch command;
- file/script name;
- detailed purpose;
- main result;
- direct dependencies;
- reverse/downstream dependencies;
- used paths;
- hidden/not-yet-configured paths;
- audit/recommendations;
- important parameters;
- input validation;
- side effects;
- created artifacts;
- logging.

Important blocks get Ukrainian comments/docstrings.

Scripts should fail clearly instead of continuing silently on invalid inputs.

## Path/config discipline

Repeated owner rule:
**do not hard-code paths throughout scripts.**

Use:
- existing `config.py` constants;
- `.env` for environment/settings;
- composed paths built from canonical path roots.

Existing config constants must not be deleted casually because other scripts may depend on them.

Later the owner detects a generic constant collision:
`DEBERTA_ARCHIVE_BASE_DIR`
being reused across classifier domains.

Direction becomes entity-specific path names for intent/style/sentiment.

## Structure-change discipline

Do not invent new directories or rename/move files without agreement.

Reuse existing project structure and inspect the tree first.

Owner repeatedly asks:
- which existing scripts already solve part of the problem?
- which are duplicates?
- what can be reused?

This motivates consolidation of evaluation/audit utilities.

## Encoding and human reports

All text/CSV:
- UTF-8.

For CSV intended for Excel:
- keep clean UTF-8 machine file;
- optionally create `_utf8_bom.csv` human-friendly copy.

Evaluation should also be understandable by a human, not only by tooling.

## Label-map contract

Existing maps should be read/preserved rather than silently overwritten.

Compatible shapes such as:
- `name → id`;
- `id → name`
should be supported/documented deliberately.

Historical decoder repair writes a canonical:
- `id2name`;
- `name2id`.

But the next classifier run still fails with `_MODEL` undefined.

Important lesson:
**one repaired artifact does not prove end-to-end health.**

## Intent path failure

A real historical run of `classify_intent` fails because `intent_fallback.py` cannot open the configured keyword file.

This is direct evidence that centralized config/path work was necessary.

## Unified pipeline direction

Style, sentiment and intent should share one structural discipline:
- training;
- label contract;
- classify;
- evaluate;
- reports;
- revision handling.

But outputs/paths must remain entity-specific to avoid collisions.

## Local revision management

Owner says Hugging Face version push is problematic.

Historical response is to formalize local revisions:
- `config_dynamic_intent.py`;
- `rev_manager_intent.py`;
- local model archives.

The intent pattern is planned to expand to style/sentiment.

Current model-registry authority still requires a live audit.

## Avoid unnecessary one-off scripts

Owner rejects adding another standalone utility just to produce evaluation TSV data when the function can safely belong in the main intent training pipeline.

Likewise, several evaluation/audit scripts are reviewed for duplication.

Stable principle:
**inventory and consolidate before adding another script.**

## Artifact layout correction

Owner explicitly corrects style/sentiment storage:
- revisions under `models/style/<rev>` / `models/sentiment/<rev>`;
- separate logs;
- separate checkpoints;
- separate reports;
- separate confusion-matrix locations.

This is historical module architecture, not current verified layout.

## Zone.Identifier

Windows→WSL/VS copying leaves `Zone.Identifier` sidecars.

Owner raises this twice because these files pollute project directories.

This belongs to developer/repository hygiene, not bot business logic.

## WSL environment

A local WSL user-session/systemd issue is diagnosed late in the source.

The owner later reports:
`journalctl --user -b -p err --no-pager`
→ `No entries`.

This is historical workstation evidence only.

## Relation to later Telegram histories

This source precedes the later Telegram behavior/runtime/governance root.

It explains the early ML/classifier engineering that later triggered a strategic owner correction:
first finalize the bot behavior model, then engineer production classifier/runtime around that model.

It also provides a detailed script standard that strongly resembles later Blueprint principles, but it remains Telegram module history until current Blueprint explicitly adopts/reconciles it.
