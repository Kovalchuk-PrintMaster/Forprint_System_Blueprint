# Portfolio Execution Dashboard — concept v0.1

## Role

The dashboard is a projection of the governance/data model, not the source of truth.

Do not build a sophisticated dashboard before roadmap/dependency/execution records exist.

## Core module view

Potential fields:

- module;
- current phase/roadmap step;
- total weighted scope;
- accepted completed weight;
- progress percentage;
- confidence;
- blockers;
- dependencies waiting for this module;
- dependencies this module waits for;
- portfolio priority;
- blocking class;
- current executor/provider/model;
- spend;
- weighted work delivered;
- cost per weighted unit;
- lead time;
- rework rate;
- acceptance/quality rate;
- report quality;
- monthly velocity;
- 30/90-day trend.

## Historical comparison

Create an initial baseline representing approximately the first year of mostly manual owner-driven
development.

Then preserve periodic snapshots so the project can compare:

- manual-era progress;
- automated/agent-assisted progress;
- budget efficiency;
- executor/model changes;
- module velocity over time.

## Caution

Early percentage values are approximate. Display confidence/assessment notes to avoid false
precision.

## Priority view

Dashboard should help answer:

- who is blocking whom;
- which dependency is needed soonest;
- where budget should be concentrated;
- which module can safely remain paused;
- whether a faster/more expensive executor is economically justified;
- whether automation is producing measurable improvement.

## Step placement

The owner identified the portfolio dashboard foundation as the planned **second program step after
the current Q-series stage 0**, while the first post-Q step will be defined in the next working
session.
