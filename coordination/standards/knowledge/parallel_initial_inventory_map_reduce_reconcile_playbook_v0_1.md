# ForPrint Parallel Initial Inventory — Map / Reduce / Reconcile Playbook v0.1

## Goal

Complete the first semantic inventory quickly without letting many reviewers mutate the repository.

## A — deterministic map

Collect tracked paths, types, Git hashes/history, Python AST symbols, imports/references where
available, document headings, Make targets and current knowledge records.

## B — semantic packages

Split by coherent responsibility, not equal file counts.

Examples: governance, prompt lifecycle, roadmaps, release machinery, evidence/reporting,
repository knowledge, validation, module coordination, tests, legacy/history.

Each package carries an exact manifest, known context, machine inventory, read-only instruction and
fixed machine-readable return schema.

## C — parallel review

Reviewers return purpose, authority, capability refs, dependencies, rationale evidence,
usage/status, duplicate candidates, unknowns and confidence. They do not mutate the repository.

## D — reducer

Merge reports and detect uncovered artifacts, contradictions, duplicate capability claims, invalid
refs and low-confidence results. Produce one unresolved queue.

## E — targeted second pass

Blind second review covers risky/conflicting/low-confidence material plus a control sample from
green results. Do not automatically double-review 100% if quality evidence does not justify it.

## F — canonicalization

Only after reconciliation update/publish indexes, propose target structure, and perform small
reversible validated migrations.

The first inventory is also calibration input for the future metadata schema, Inspector and
incremental-maintenance tooling.
