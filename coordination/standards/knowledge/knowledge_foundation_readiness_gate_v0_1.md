# ForPrint Knowledge Foundation Readiness Gate v0.1

## Purpose

Broad autonomous module execution must not start in a repository whose important knowledge is
unrecoverable, stale or invisible.

The gate does not require perfect documentation.

## Minimum readiness

Before broad autonomous execution a module should have:
- stable identity;
- Charter/mission and boundaries;
- explicit Target State;
- discoverable current roadmap authority;
- discoverable central standards;
- obvious zero-context entry path;
- discoverable high-level operational commands;
- indexed major capabilities/public contracts;
- critical dependencies/owners recorded;
- visible high-risk knowledge gaps;
- a local semantic knowledge owner;
- Inspector/collector ability to detect material drift.

## Risk-weighted states

`GREEN` — current authorized work has sufficient recoverable authority, standards, capability and
dependency knowledge. Non-critical debt may remain visible.

`YELLOW` — debt exists and needs scheduled reconciliation, but current work remains safe.

`RED` — a critical authority source, standard, contract, dependency or current execution fact is
unknown/stale/conflicting enough to make dependent autonomous work unsafe.

Blocking is stage-conditioned. A missing future dependency does not block unrelated current work.

Exact numerical thresholds are deferred until the first full Blueprint inventory provides real
calibration data.

## No hidden green

The system must never report healthy knowledge merely because an artifact was never indexed.
Unseen-change detection is part of readiness.

## Boundaries

This gate does not authorize autonomy, automatic ACCEPT/RETURN/HOLD, live SQLite, cross-repository
writes, or security/destructive exceptions.
