# Knowledge Foundation — Batch Validation Experiment v0.1

Status: PLANNED EXPERIMENT / AGREED DIRECTION / NOT ACTIVE EXECUTION AUTHORITY.

# Knowledge Inventory Acceleration Strategy

Status: `AGREED_WITH_OWNER` as an intended experimentation path.

## Problem

Structural scanning is not the only bottleneck.
Semantic validation consumes major time.

The owner does not want manual line-by-line validation of every generated inventory report.

## Proposed experiment

Process repository content in meaningful batches.

For each batch:
1. run automated inventory/analysis scripts;
2. preserve the script-generated report;
3. give raw scripts/documents to Assistant A;
4. give the script-generated analytical result to Assistant B;
5. compare independent raw-source interpretation with automated result;
6. classify disagreements;
7. manually investigate only disagreement/high-risk subsets;
8. strengthen scanners/parsers/semantic automation when scripts are wrong;
9. record cases where assistants are wrong or lack project context;
10. repeat on several batches before trusting broad automated conclusions.

## Validation philosophy

Use:
- batch evaluation;
- two independent review paths;
- disagreement-triggered deep review;
- risk-weighted sampling;
- periodic random control samples;
- measured script-vs-reviewer quality evidence.

## Inspector candidate role

Inspector can eventually:
- orchestrate structural/semantic checks;
- detect stale/drifting knowledge;
- report confidence/coverage;
- maintain finding queues;
- recheck after local repairs.

Inspector must not become semantic owner.

## Tomorrow's practical next step

Design one controlled experiment:
- select representative repository subset;
- define expected report schema;
- run automated inventory;
- prepare raw-source reviewer packet;
- prepare result-reviewer packet;
- define comparison/reconciliation rubric;
- classify disagreement causes;
- identify tooling improvements before scaling.

<!-- dual-path-knowledge-inventory-validation-v0-1:start -->
## Dual-path batch validation — owner reaffirmation 2026-08-28

For each meaningful Blueprint inventory batch run two independent paths.

**Path A — machine/scanner analysis:** deterministic structural facts, references, metadata, code/config/test relationships and machine findings with reproducible provenance.

**Path B — independent semantic review:** give a separate reviewer the raw thematic source batch and a precise prompt without first showing the machine conclusion. The reviewer assesses meaning, ownership, dependencies, contradictions, stale/legacy evidence, ambiguity and confidence.

Reconcile:
- agreement -> normal acceptance/sampling;
- disagreement -> focused discrepancy plan;
- high-risk ambiguity -> manual deep review;
- scanner error -> improve scanner/parser and rerun;
- reviewer/context error -> improve context/prompt packaging.

Scripts are not proof of semantic correctness for meaning-heavy governance/architecture documents. Their role is structural/deterministic evidence; semantic consistency requires independent reasoning and reconciliation.

Use relatively large thematic batches so operator participation is not required every few minutes.
<!-- dual-path-knowledge-inventory-validation-v0-1:end -->
